import requests
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from . import dashboard
from . import db_ops
from . import ods_ops

BASE_DIR = Path(__file__).resolve().parents[1]
SESSION_FILE = BASE_DIR / "session.json"
CHAT_ID = "6575275306"
DASHBOARD_OUTPUT = dashboard.DEFAULT_OUTPUT
LOGGER = logging.getLogger("forja_de_ferro.telegram")
SEND_RETRY_DELAYS = (1, 2)
POLL_RETRY_INITIAL = 3
POLL_RETRY_MAX = 60


class TelegramTemporaryError(RuntimeError):
    pass


class TelegramConfigurationError(RuntimeError):
    pass


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def read_token():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return None
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and line.split("=", 1)[0].upper() == "TELEGRAM_TOKEN":
                return line.split("=", 1)[1]
    return None


TOKEN = read_token()
API = f"https://api.telegram.org/bot{TOKEN}"


def send(text):
    attempts = len(SEND_RETRY_DELAYS) + 1
    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                f"{API}/sendMessage",
                json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            if response.status_code in (401, 404):
                LOGGER.error("Falha permanente ao enviar mensagem: token invalido.")
                return False
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            if attempt >= attempts:
                LOGGER.error(
                    "Falha temporaria ao enviar mensagem tentativa=%s tipo=%s",
                    attempt,
                    type(exc).__name__,
                )
                return False
            delay = SEND_RETRY_DELAYS[attempt - 1]
            LOGGER.warning(
                "Falha temporaria ao enviar mensagem tentativa=%s tipo=%s espera=%ss",
                attempt,
                type(exc).__name__,
                delay,
            )
            time.sleep(delay)


def load_session():
    session = None
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                session = json.load(f)
        except (OSError, json.JSONDecodeError):
            session = None

    if session:
        exercises = session.get("exercises", [])
        log_ids = [ex.get("log_id") for ex in exercises]
        if all(log_ids) and db_ops.is_session_incomplete(
            session.get("session_id"),
            log_ids,
        ):
            return session

    return ods_ops.recover_active_session()


def get_updates(offset=0):
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": 3},
            timeout=10,
        )
        if r.status_code in (401, 404):
            raise TelegramConfigurationError(
                "Token do Telegram invalido ou bot nao encontrado."
            )
        r.raise_for_status()
        payload = r.json()
        result = payload.get("result", [])
        if not isinstance(result, list):
            raise ValueError("Resposta sem lista de atualizacoes.")
        return result
    except TelegramConfigurationError:
        raise
    except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
        raise TelegramTemporaryError(type(exc).__name__) from None


def _command_name(text):
    normalized = text.strip().lower()
    if normalized.startswith("/"):
        return normalized.split(maxsplit=1)[0]
    if normalized in {
        "ajuda",
        "exercicios",
        "volume",
        "dashboard",
        "planos",
        "plano",
        "aquecimento",
        "gerar",
        "prever",
        "previa",
        "status",
        "desfazer",
    }:
        return normalized
    return "registro_carga"


def _format_weight(weight):
    if weight is None:
        return "-"
    return str(int(weight) if weight == int(weight) else weight)


def _format_target_suffix(ex):
    target_weight = ex.get("target_weight")
    if target_weight is None:
        return ""
    return f" - alvo {_format_weight(target_weight)}kg"


def _format_current_exercise(ex):
    msg = (
        f"▶ <b>{ex['name']}</b> ({ex['sets']}x{ex['reps']})"
        f"{_format_target_suffix(ex)} - descanso {ex.get('rest_interval', '2 min')}"
    )
    loading_note = ex.get("loading_note") or ods_ops.format_loading_note(
        ex["name"],
        ex.get("target_weight"),
    )
    if loading_note:
        msg += f"\n   {loading_note}"
    return msg


def _format_exercise_line(idx, ex):
    target = _format_weight(ex.get("target_weight"))
    rest = ex.get("rest_interval", "2 min")
    return (
        f"{idx}. <b>{ex['name']}</b>\n"
            f"   {ex['sets']}x{ex['reps']} | alvo: {target}kg | descanso: {rest}"
    )


def _format_training_msg(exercises):
    lines = ["<b>Treino</b>\n"]
    lines.extend(_format_exercise_line(idx, ex) for idx, ex in enumerate(exercises, start=1))
    return "\n\n".join(lines)


def _format_summary_names(items, limit=4):
    names = [item["name"] for item in items[:limit]]
    suffix = f" e mais {len(items) - limit}" if len(items) > limit else ""
    return ", ".join(names) + suffix


def _format_training_summary(session_id):
    summary = db_ops.get_session_summary(session_id)
    if summary is None:
        return "Resumo indisponivel."

    lines = [
        "<b>Resumo da sessao</b>",
        f"Volume: <b>{summary['volume']:,.0f} kg</b>".replace(",", "."),
    ]
    if summary["rpe_average"] is not None:
        lines.append(f"RPE medio: <b>{summary['rpe_average']:.1f}</b>".replace(".", ","))
    if summary["volume_delta"] is not None:
        delta = summary["volume_delta"]
        signal = "+" if delta > 0 else ""
        lines.append(
            f"Volume vs. sessao anterior: <b>{signal}{delta:,.0f} kg</b>".replace(
                ",", "."
            )
        )
    if summary["increases"]:
        lines.append(f"Aumentos: {_format_summary_names(summary['increases'])}")
    if summary["reductions"]:
        lines.append(f"Reducoes: {_format_summary_names(summary['reductions'])}")
    if summary["consolidations"]:
        lines.append(
            f"Consolidacoes: {_format_summary_names(summary['consolidations'])}"
        )
    if summary["maintained_rpe9"]:
        lines.append(
            f"Cargas mantidas em RPE 9: "
            f"{_format_summary_names(summary['maintained_rpe9'])}"
        )
    if summary["records"]:
        lines.append(f"Recordes: {_format_summary_names(summary['records'])}")
    return "\n".join(lines)


def _format_exercises_msg(exercises):
    lines = ["<pre>Lista de exercicios\n"]
    lines.append(f"{'#':>2} {'Exercicio':<22} {'S':>2} {'R':>3}\n")
    lines.append("-" * 34 + "\n")
    for idx, ex in enumerate(exercises, start=1):
        lines.append(f"{idx:>2} {ex['name'][:22]:<22} {ex['sets']:>2} {ex['reps']:>3}\n")
    lines.append("</pre>")
    return "".join(lines)


def handle_generate():
    try:
        exercises, session_id = ods_ops.generate_training()
    except Exception as e:
        LOGGER.error(
            "Falha ao gerar sessao tipo=%s",
            type(e).__name__,
        )
        send(f"Erro ao gerar sessao de treino: {e}")
        return

    ods_ops.write_session(exercises, session_id)

    msg = _format_training_msg(exercises)
    send(msg)
    send("Sessao de treino gerada. Envie <code>carga rpe</code> para cada exercicio.")


def handle_preview():
    try:
        exercises = ods_ops.preview_training()
    except Exception as e:
        LOGGER.error(
            "Falha ao gerar previa tipo=%s",
            type(e).__name__,
        )
        send(f"Erro ao gerar previa do treino: {e}")
        return

    msg = _format_training_msg(exercises)
    send(msg)
    send("Previa do treino. Nada foi salvo. Use /gerar para iniciar uma sessao real.")


def handle_exercises():
    try:
        exercises = ods_ops.read_exercises()
        send(_format_exercises_msg(exercises))
    except Exception as exc:
        LOGGER.error("Falha ao listar exercicios tipo=%s", type(exc).__name__)
        send("Erro ao listar exercicios. Consulte o terminal.")


def handle_volume():
    try:
        exercises = ods_ops.read_exercises()
        muscle_groups = ods_ops.read_muscle_groups()
        muscle_sets = {}
        for ex in exercises:
            groups = muscle_groups.get(ex["name"], [])
            muscles = [group["muscle_group"] for group in groups] or ["Outros"]
            for muscle in muscles:
                muscle_sets[muscle] = muscle_sets.get(muscle, 0) + ex["sets"]
        lines = [
            "<b>Volume por musculo</b>\n",
            "<i>series/sessao → series/semana (~3.5x)</i>\n",
        ]
        for muscle, sets in sorted(muscle_sets.items()):
            weekly = round(sets * 3.5, 1)
            lines.append(f"{muscle}: <b>{sets}</b> → ~{weekly:.0f}/sem")
        send("\n".join(lines))
    except Exception as exc:
        LOGGER.error("Falha ao calcular volume tipo=%s", type(exc).__name__)
        send("Erro ao calcular volume. Consulte o terminal.")


def handle_plans():
    plans = db_ops.list_training_plans()
    if not plans:
        send("Nenhum plano de treino cadastrado.")
        return
    lines = ["<b>Planos de treino</b>"]
    for plan in plans:
        marker = " ✓ ativo" if plan["active"] else ""
        lines.append(
            f"{plan['name']}: {plan['exercise_count']} exercicios{marker}"
        )
    lines.append("\nUse <code>/plano NOME</code> para selecionar.")
    send("\n".join(lines))


def handle_select_plan(text):
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        handle_plans()
        return
    name = parts[1].strip()
    if db_ops.set_active_training_plan(name):
        send(f"Plano ativo: <b>{name}</b>.")
    else:
        send(f"Plano nao encontrado ou vazio: <b>{name}</b>.")


def handle_dashboard():
    try:
        dashboard.salvar_dashboard(DASHBOARD_OUTPUT)
        data = dashboard.carregar_dados()
        summary = data["resumo"]
        updated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
        lines = [f"Dashboard atualizado em <b>{updated_at}</b>."]
        if summary["sessoes"]:
            lines.extend(
                [
                    f"Ultima sessao: <b>{summary['ultima_data']}</b>",
                    f"Volume: <b>{summary['ultimo_volume']:,.0f} kg</b>".replace(
                        ",", "."
                    ),
                ]
            )
            if summary["rpe_medio"] is not None:
                lines.append(
                    f"RPE medio geral: <b>{summary['rpe_medio']:.1f}</b>".replace(
                        ".", ","
                    )
                )
        else:
            lines.append("Ainda nao existem sessoes preenchidas.")
        send("\n".join(lines))
    except Exception as exc:
        LOGGER.error("Falha ao atualizar dashboard tipo=%s", type(exc).__name__)
        send("Erro ao atualizar o dashboard. Consulte o terminal.")


def handle(text, session):
    text = text.strip()
    exercises = session.get("exercises", [])

    if not exercises or "log_id" not in exercises[0]:
        send("Formato de sessao antigo. Use /gerar para iniciar uma nova sessao de treino.")
        return

    log_ids = [ex["log_id"] for ex in exercises]
    total = len(exercises)
    filled = db_ops.count_filled(log_ids)

    if text.lower() in ("/status", "status"):
        if filled >= total:
            send(f"Treino completo. {total}/{total} ✓")
        else:
            ex = exercises[filled]
            done = "\n".join(f"✓ {exercises[i]['name']}" for i in range(filled))
            msg = f"Treino — {filled}/{total}\n"
            if done:
                msg += done + "\n"
            msg += _format_current_exercise(ex)
            send(msg)
        return

    if text.lower() in ("/desfazer", "desfazer", "/undo", "undo"):
        if filled == 0:
            send("Nada para desfazer.")
            return
        last_ex = exercises[filled - 1]
        db_ops.update_log_weight(last_ex["log_id"], None, None)
        send(f"↩ Desfeito: <b>{last_ex['name']}</b>")
        return

    if filled >= total:
        send("O treino ja esta completo. Use /status.")
        return

    parts = text.replace(",", ".").split()
    try:
        weight = float(parts[0])
        rpe = int(parts[1]) if len(parts) > 1 else None
    except (ValueError, IndexError):
        send("Formato: <code>80 8</code> (carga + RPE) ou <code>80</code> (somente carga)")
        return

    ex = exercises[filled]
    db_ops.update_log_weight(ex["log_id"], weight, rpe)
    new_filled = filled + 1

    rpe_str = f" RPE {rpe}" if rpe is not None else ""
    if new_filled >= total:
        try:
            summary = _format_training_summary(session.get("session_id"))
        except Exception as exc:
            LOGGER.error(
                "Falha ao gerar resumo session_id=%s tipo=%s",
                session.get("session_id"),
                type(exc).__name__,
            )
            summary = "Resumo indisponivel. Consulte o terminal."
        send(
            f"<b>{ex['name']}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n\n"
            f"Treino completo.\n\n{summary}"
        )
    else:
        nxt = exercises[new_filled]
        send(
            f"<b>{ex['name']}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n"
            f"{_format_current_exercise(nxt)}"
        )


def main():
    configure_logging()
    if not TOKEN:
        LOGGER.error("TELEGRAM_TOKEN nao encontrado no .env")
        return

    offset = 0
    retry_delay = POLL_RETRY_INITIAL
    LOGGER.info("Bot Forja de Ferro em polling. Use Ctrl+C para parar.")

    try:
        while True:
            try:
                updates = get_updates(offset)
                retry_delay = POLL_RETRY_INITIAL
            except TelegramConfigurationError as exc:
                LOGGER.error("Polling encerrado: %s", exc)
                return
            except TelegramTemporaryError as exc:
                LOGGER.warning(
                    "Falha temporaria no polling tipo=%s espera=%ss",
                    exc,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, POLL_RETRY_MAX)
                continue

            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")

                if chat_id != CHAT_ID or not text:
                    continue

                lower = text.strip().lower()
                command = _command_name(text)
                LOGGER.info("Comando recebido comando=%s", command)

                if lower in ("/ajuda", "ajuda", "/help", "help"):
                    send(
                        "<b>Forja de Ferro — Comandos</b>\n\n"
                        "/gerar — cria uma sessao de treino\n"
                        "/prever — mostra uma previa sem salvar\n"
                        "/exercicios — lista os exercicios atuais\n"
                        "/aquecimento — mostra o aquecimento\n"
                        "/volume — volume por grupo muscular\n"
                        "/dashboard — atualiza o dashboard local\n"
                        "/planos — lista planos de treino\n"
                        "/plano NOME — seleciona o plano ativo\n"
                        "/status — exercicio atual e progresso\n"
                        "/desfazer — apaga o ultimo registro\n"
                        "/ajuda — esta mensagem\n\n"
                        "<b>Registrar carga:</b>\n"
                        "<code>80</code> — somente carga\n"
                        "<code>80 8</code> — carga + RPE"
                    )
                    continue

                if lower in ("/exercicios", "exercicios", "/exercises", "exercises"):
                    handle_exercises()
                    continue

                if lower in ("/volume", "volume"):
                    handle_volume()
                    continue

                if lower in ("/dashboard", "dashboard"):
                    handle_dashboard()
                    continue

                if lower in ("/planos", "planos"):
                    handle_plans()
                    continue

                if lower == "/plano" or lower == "plano" or lower.startswith(
                    ("/plano ", "plano ")
                ):
                    handle_select_plan(text)
                    continue

                if lower in ("/aquecimento", "aquecimento", "/warmup", "warmup"):
                    send(
                        "<b>Aquecimento</b>\n\n"
                        "1. Agachamento livre — 1x10\n"
                        "2. Dobradiça de quadril — 1x10\n"
                        "3. Sustentação Zercher com barra vazia — 1x15s\n"
                        "4. Agachamento Zercher com barra vazia — 1x5\n"
                        "5. Agachamento Zercher leve — 1x3\n"
                        "6. Supino reto com barra vazia — 1x8\n"
                        "7. Supino reto leve — 1x3"
                    )
                    continue

                if lower.startswith("/gerar") or lower.startswith("/generate"):
                    handle_generate()
                    continue

                if lower in ("/prever", "prever", "/previa", "previa", "/preview", "preview"):
                    handle_preview()
                    continue

                try:
                    session = load_session()
                except Exception as exc:
                    LOGGER.error(
                        "Falha ao carregar sessao comando=%s tipo=%s",
                        command,
                        type(exc).__name__,
                    )
                    send("Erro ao carregar a sessao. Consulte o terminal.")
                    continue
                if session is None:
                    LOGGER.info("Comando sem sessao ativa comando=%s", command)
                    send("Nenhuma sessao ativa. Use /gerar.")
                    continue

                LOGGER.info(
                    "Comando associado a sessao comando=%s session_id=%s",
                    command,
                    session.get("session_id"),
                )
                try:
                    handle(text, session)
                except Exception as exc:
                    LOGGER.error(
                        "Falha ao processar comando=%s session_id=%s tipo=%s",
                        command,
                        session.get("session_id"),
                        type(exc).__name__,
                    )
                    send("Erro ao processar o comando. Consulte o terminal.")

            time.sleep(3)
    except KeyboardInterrupt:
        LOGGER.info("Bot encerrado pelo usuario.")


if __name__ == "__main__":
    main()
