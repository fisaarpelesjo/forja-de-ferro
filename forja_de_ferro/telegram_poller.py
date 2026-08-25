import requests
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from . import dashboard
from . import db_ops
from . import muaythai
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
    return "registro_carga"


def _is_session_input(text):
    normalized = text.strip().lower()
    if normalized in {"/status", "/desfazer"}:
        return True
    try:
        float(normalized.replace(",", ".").split()[0])
        return True
    except (ValueError, IndexError):
        return False


def _format_weight(weight):
    if weight is None:
        return "-"
    return str(int(weight) if weight == int(weight) else weight)


def _format_body_weight(weight):
    return f"{float(weight):.1f}".replace(".", ",")


def _format_weight_date(recorded_at):
    return datetime.fromisoformat(recorded_at).strftime("%d/%m/%Y %H:%M")


def _format_target_suffix(ex):
    target_weight = ex.get("target_weight")
    if target_weight is None:
        return ""
    return f" - alvo {_format_weight(target_weight)}kg"


def _display_exercise_name(name):
    return ods_ops.get_display_name(name)


def _format_current_exercise(ex):
    display_name = _display_exercise_name(ex["name"])
    msg = (
        f"▶ <b>{display_name}</b> ({ex['sets']}x{ex['reps']})"
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
    display_name = _display_exercise_name(ex["name"])
    return (
        f"{idx}. <b>{display_name}</b>\n"
            f"   {ex['sets']}x{ex['reps']} | alvo: {target}kg | descanso: {rest}"
    )


def _format_training_msg(exercises):
    lines = ["<b>Treino</b>\n"]
    lines.extend(_format_exercise_line(idx, ex) for idx, ex in enumerate(exercises, start=1))
    return "\n\n".join(lines)


def _format_training_b_msg(exercises):
    lines = ["10 voltas | descanso 60s no fim da volta"]
    for idx, ex in enumerate(exercises, start=1):
        target = ex.get("target_weight")
        weight_line = (
            "peso corporal"
            if target is None
            else f"peso: {_format_weight(target)}kg"
        )
        lines.append(
            f"{idx}. <b>{ex['name']}</b>\n"
            f"   {ex['work']} | {weight_line}"
        )
        if ex.get("loading_note"):
            lines.append(f"   {ex['loading_note']}")
    return "\n\n".join(lines)


def _format_summary_names(items, limit=4):
    names = [_display_exercise_name(item["name"]) for item in items[:limit]]
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
    display_names = [_display_exercise_name(ex["name"]) for ex in exercises]
    name_width = max([22, *(len(name) for name in display_names)])
    lines = ["<pre>Lista de exercicios\n"]
    lines.append(f"{'#':>2} {'Exercicio':<{name_width}} {'S':>2} {'R':>3}\n")
    lines.append("-" * (name_width + 12) + "\n")
    for idx, (ex, display_name) in enumerate(
        zip(exercises, display_names),
        start=1,
    ):
        lines.append(
            f"{idx:>2} {display_name:<{name_width}} {ex['sets']:>2} {ex['reps']:>3}\n"
        )
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
    if exercises:
        send(f"<b>Agora faca:</b>\n{_format_current_exercise(exercises[0])}")


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


def _mt_semana_do_texto(text, padrao=1):
    """Semana opcional no comando: /mtterca 3. Fora de 1-8, o modulo ajusta."""
    partes = text.strip().split()
    if len(partes) > 1:
        try:
            return int(partes[1])
        except ValueError:
            pass
    return padrao


def handle_mt_iniciar(chave, text):
    semana = _mt_semana_do_texto(text)
    try:
        muaythai.iniciar(chave, semana)
    except Exception as exc:
        LOGGER.error("Falha ao iniciar roteiro MT chave=%s tipo=%s", chave, type(exc).__name__)
        send("Erro ao iniciar o roteiro. Consulte o terminal.")
        return
    send(muaythai.formatar_resumo(chave, semana))


def handle_mt_hoje(text):
    chave = muaythai.roteiro_do_dia()
    if chave is None:
        send(
            "Hoje nao e dia de saco.\n\n"
            "Segunda, quarta e sexta sao musculacao. Domingo e descanso completo.\n"
            "Use /mtterca, /mtquinta ou /mtsabado para ver outro treino."
        )
        return
    handle_mt_iniciar(chave, text)


def handle_mt_proximo():
    estado = muaythai.carregar_estado()
    if estado is None:
        send("Nenhum roteiro de Muay Thai ativo. Use /mt, /mtterca, /mtquinta ou /mtsabado.")
        return
    # O primeiro /proximo apos iniciar mostra o bloco 0; os seguintes avancam.
    if estado.get("mostrou_primeiro"):
        estado = muaythai.avancar()
        if estado is None:
            send("Roteiro concluido. Bom treino.\n\nUse /mtregras para revisar as regras do ciclo.")
            return
    else:
        estado["mostrou_primeiro"] = True
        muaythai.salvar_estado(estado)
    send(muaythai.formatar_bloco(estado))


def handle_mt_parar():
    if muaythai.carregar_estado() is None:
        send("Nenhum roteiro ativo.")
        return
    muaythai.limpar_estado()
    send("Roteiro encerrado.")


def handle_fundamentos(text):
    """/fundamentos [a|b|c]. Sem argumento mostra o indice da fase, com a sessao
    de hoje marcada -- e a primeira coisa que alguem digita, entao nao pode ser
    erro."""
    termo = text.strip()[len("/fundamentos"):].strip()
    if not termo:
        send(muaythai.formatar_indice_fundamentos())
        return
    chave = muaythai.resolver_fundamentos(termo)
    if chave is None:
        send("Sessao nao reconhecida. Use /fundamentos a, b ou c.\n\n"
             "Sem argumento, /fundamentos mostra a fase inteira.")
        return
    try:
        muaythai.iniciar(chave)
    except Exception as exc:
        LOGGER.error("Falha ao iniciar fundamentos chave=%s tipo=%s", chave, type(exc).__name__)
        send("Erro ao iniciar a sessao. Consulte o terminal.")
        return
    send(muaythai.formatar_resumo(chave))


def handle_como(text):
    """/como <tecnica>. Sem argumento, mostra o indice em vez de erro -- o
    operador que digita so /como esta pedindo para ver o que existe."""
    termo = text.strip()[len("/como"):].strip()
    if not termo:
        send(muaythai.formatar_indice_tecnicas())
        return
    chave = muaythai.buscar_tecnica(termo)
    if chave is None:
        send(muaythai.formatar_tecnica_nao_encontrada(termo))
        return
    send(muaythai.formatar_tecnica(chave))


def handle_training_b():
    try:
        exercises = ods_ops.build_training_b()
    except Exception as e:
        LOGGER.error(
            "Falha ao gerar treino B tipo=%s",
            type(e).__name__,
        )
        send(f"Erro ao gerar treino B: {e}")
        return

    send(_format_training_b_msg(exercises))


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


def handle_weight(text):
    parts = text.strip().split(maxsplit=1)
    if len(parts) == 2:
        try:
            weight = float(parts[1].strip().replace(",", "."))
            entry = db_ops.add_body_weight(weight)
        except ValueError as exc:
            send(f"{exc}\nUse <code>/peso 118,5</code>.")
            return
        send(
            f"Peso registrado: <b>{_format_body_weight(entry['weight_kg'])} kg</b>."
        )
        return

    history = db_ops.list_body_weights(limit=5)
    if not history:
        send("Nenhum peso registrado. Use <code>/peso 118,5</code>.")
        return

    latest = history[0]
    lines = [
        "<b>Peso corporal</b>",
        f"Atual: <b>{_format_body_weight(latest['weight_kg'])} kg</b>",
        f"Registrado em: {_format_weight_date(latest['recorded_at'])}",
    ]
    if len(history) > 1:
        delta = latest["weight_kg"] - history[1]["weight_kg"]
        signal = "+" if delta > 0 else ""
        lines.append(
            f"Desde a medicao anterior: "
            f"<b>{signal}{_format_body_weight(delta)} kg</b>"
        )
    lines.append("\n<b>Ultimas medicoes</b>")
    lines.extend(
        f"{_format_weight_date(item['recorded_at'])}: "
        f"{_format_body_weight(item['weight_kg'])} kg"
        for item in history
    )
    send("\n".join(lines))


def handle_waist(text):
    parts = text.strip().split(maxsplit=1)
    if len(parts) == 2:
        try:
            circumference = float(parts[1].strip().replace(",", "."))
            entry = db_ops.add_waist_measurement(circumference)
        except ValueError as exc:
            send(f"{exc}\nUse <code>/cintura 110,5</code>.")
            return
        send(
            "Cintura registrada: "
            f"<b>{_format_body_weight(entry['circumference_cm'])} cm</b>."
        )
        return

    history = db_ops.list_waist_measurements(limit=5)
    if not history:
        send("Nenhuma medida de cintura registrada. Use <code>/cintura 110,5</code>.")
        return

    latest = history[0]
    lines = [
        "<b>Circunferencia da cintura</b>",
        f"Atual: <b>{_format_body_weight(latest['circumference_cm'])} cm</b>",
        f"Registrada em: {_format_weight_date(latest['recorded_at'])}",
    ]
    if len(history) > 1:
        delta = latest["circumference_cm"] - history[1]["circumference_cm"]
        signal = "+" if delta > 0 else ""
        lines.append(
            f"Desde a medicao anterior: "
            f"<b>{signal}{_format_body_weight(delta)} cm</b>"
        )
    lines.append("\n<b>Ultimas medicoes</b>")
    lines.extend(
        f"{_format_weight_date(item['recorded_at'])}: "
        f"{_format_body_weight(item['circumference_cm'])} cm"
        for item in history
    )
    send("\n".join(lines))


def handle(text, session):
    text = text.strip()
    exercises = session.get("exercises", [])

    if not exercises or "log_id" not in exercises[0]:
        send("Formato de sessao antigo. Use /gerar para iniciar uma nova sessao de treino.")
        return

    log_ids = [ex["log_id"] for ex in exercises]
    total = len(exercises)
    filled = db_ops.count_filled(log_ids)

    if text.lower() == "/status":
        latest_weight = db_ops.get_latest_body_weight()
        weight_line = (
            f"\nPeso atual: {_format_body_weight(latest_weight['weight_kg'])} kg"
            if latest_weight
            else ""
        )
        if filled >= total:
            send(f"Treino completo. {total}/{total} ✓{weight_line}")
        else:
            ex = exercises[filled]
            done = "\n".join(
                f"✓ {_display_exercise_name(exercises[i]['name'])}"
                for i in range(filled)
            )
            msg = f"Treino — {filled}/{total}\n"
            if done:
                msg += done + "\n"
            msg += _format_current_exercise(ex)
            msg += weight_line
            send(msg)
        return

    if text.lower() == "/desfazer":
        if filled == 0:
            send("Nada para desfazer.")
            return
        last_ex = exercises[filled - 1]
        db_ops.update_log_weight(last_ex["log_id"], None, None)
        send(f"↩ Desfeito: <b>{_display_exercise_name(last_ex['name'])}</b>")
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
            f"<b>{_display_exercise_name(ex['name'])}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n\n"
            f"Treino completo.\n\n{summary}"
        )
    else:
        nxt = exercises[new_filled]
        send(
            f"<b>{_display_exercise_name(ex['name'])}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n"
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

                if lower == "/ajuda":
                    send(
                        "<b>Forja de Ferro — Comandos</b>\n\n"
                        "/gerar — cria uma sessao de treino\n"
                        "/prever — mostra uma previa sem salvar\n"
                        "/treinob — mostra o treino B de garagem\n"
                        "/exercicios — lista os exercicios atuais\n"
                        "/aquecimento — mostra o aquecimento\n"
                        "/volume — volume por grupo muscular\n"
                        "/dashboard — atualiza o dashboard local\n"
                        "/planos — lista planos de treino\n"
                        "/plano NOME — seleciona o plano ativo\n"
                        "/peso VALOR — registra o peso corporal\n"
                        "/peso — mostra o peso atual e o historico\n"
                        "/cintura VALOR — registra a circunferencia em cm\n"
                        "/cintura — mostra a cintura atual e o historico\n"
                        "/status — exercicio atual e progresso\n"
                        "/desfazer — apaga o ultimo registro\n"
                        "/ajuda — esta mensagem\n\n"
                        "<b>Muay Thai</b>\n"
                        "/fundamentos — fase sem saco, um movimento por vez\n"
                        "/fundamentos a|b|c — sessao de fundamentos\n"
                        "/mt — treino de hoje (ter/qui/sab)\n"
                        "/mtterca, /mtquinta, /mtsabado — treino especifico\n"
                        "/proximo — proximo bloco do roteiro\n"
                        "/mtparar — encerra o roteiro\n"
                        "/mtregras — regras do ciclo\n"
                        "/tecnicas — todas as tecnicas\n"
                        "/como &lt;tecnica&gt; — passo a passo (ex: /como chute baixo)\n"
                        "<i>semana opcional: /mtterca 3</i>\n\n"
                        "<b>Registrar carga:</b>\n"
                        "<code>80</code> — somente carga\n"
                        "<code>80 8</code> — carga + RPE"
                    )
                    continue

                if lower == "/exercicios":
                    handle_exercises()
                    continue

                if lower == "/volume":
                    handle_volume()
                    continue

                if lower == "/dashboard":
                    handle_dashboard()
                    continue

                if lower == "/planos":
                    handle_plans()
                    continue

                if lower == "/plano" or lower.startswith("/plano "):
                    handle_select_plan(text)
                    continue

                if lower == "/peso" or lower.startswith("/peso "):
                    handle_weight(text)
                    continue

                if lower == "/cintura" or lower.startswith("/cintura "):
                    handle_waist(text)
                    continue

                if lower == "/aquecimento":
                    send(
                        "<b>Aquecimento</b>\n\n"
                        "5 minutos, sem transformar em outro treino:\n\n"
                        "1. Marcha rapida ou polichinelo leve — 60s\n"
                        "2. Circulos de braco e abrir/fechar bracos — 30s\n"
                        "3. Rotacao de tronco — 30s\n"
                        "4. Agachamento livre — 1x10\n"
                        "5. Afundo alternado ou passada para tras — 1x6 por perna\n"
                        "6. Bom dia sem peso ou com barra vazia — 1x10\n"
                        "7. Flexao facil — 1x5-8\n"
                        "8. Prancha com toque no ombro — 10 toques"
                    )
                    continue

                if lower == "/mt" or lower.startswith("/mt "):
                    handle_mt_hoje(text)
                    continue

                if lower.startswith("/mtterca"):
                    handle_mt_iniciar("terca", text)
                    continue

                if lower.startswith("/mtquinta"):
                    handle_mt_iniciar("quinta", text)
                    continue

                if lower.startswith("/mtsabado"):
                    handle_mt_iniciar("sabado", text)
                    continue

                if lower == "/proximo":
                    handle_mt_proximo()
                    continue

                if lower == "/mtparar":
                    handle_mt_parar()
                    continue

                if lower == "/mtregras":
                    send(muaythai.formatar_regras())
                    continue

                if lower == "/fundamentos" or lower.startswith("/fundamentos "):
                    handle_fundamentos(text)
                    continue

                if lower == "/tecnicas":
                    send(muaythai.formatar_indice_tecnicas())
                    continue

                if lower == "/como" or lower.startswith("/como "):
                    handle_como(text)
                    continue

                if lower == "/gerar":
                    handle_generate()
                    continue

                if lower == "/prever":
                    handle_preview()
                    continue

                if lower == "/treinob":
                    handle_training_b()
                    continue

                if not _is_session_input(text):
                    send("Comando invalido. Use /ajuda.")
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
