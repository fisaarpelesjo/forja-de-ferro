import requests
import json
import time
from pathlib import Path

from . import db_ops
from . import ods_ops

BASE_DIR = Path(__file__).resolve().parents[1]
SESSION_FILE = BASE_DIR / "session.json"
CHAT_ID = "6575275306"


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
    try:
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")


def load_session():
    if not SESSION_FILE.exists():
        return None
    with open(SESSION_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_updates(offset=0):
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": 3},
            timeout=10,
        )
        return r.json().get("result", [])
    except Exception:
        return []


def _format_weight(weight):
    if weight is None:
        return "-"
    return str(int(weight) if weight == int(weight) else weight)


def _format_target_suffix(ex):
    target_weight = ex.get("target_weight")
    if target_weight is None:
        return ""
    return f" - alvo {_format_weight(target_weight)}kg"


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
        send(f"Erro ao gerar previa do treino: {e}")
        return

    msg = _format_training_msg(exercises)
    send(msg)
    send("Previa do treino. Nada foi salvo. Use /gerar para iniciar uma sessao real.")


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
            msg += (
                f"▶ <b>{ex['name']}</b> ({ex['sets']}x{ex['reps']})"
                f"{_format_target_suffix(ex)} - descanso {ex.get('rest_interval', '2 min')}"
            )
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
        send(
            f"<b>{ex['name']}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n\n"
            f"Treino completo."
        )
    else:
        nxt = exercises[new_filled]
        send(
            f"<b>{ex['name']}</b> ✓ {weight}kg{rpe_str} ({new_filled}/{total})\n"
            f"▶ {nxt['name']} ({nxt['sets']}x{nxt['reps']})"
            f"{_format_target_suffix(nxt)} - descanso {nxt.get('rest_interval', '2 min')}"
        )


def main():
    if not TOKEN:
        print("TELEGRAM_TOKEN nao encontrado no .env")
        return

    offset = 0
    print("Bot Forja de Ferro em polling... (Ctrl+C para parar)")

    try:
        while True:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = msg.get("text", "")

                if chat_id != CHAT_ID or not text:
                    continue

                lower = text.strip().lower()

                if lower in ("/ajuda", "ajuda", "/help", "help"):
                    send(
                        "<b>Forja de Ferro — Comandos</b>\n\n"
                        "/gerar — cria uma sessao de treino\n"
                        "/prever — mostra uma previa sem salvar\n"
                        "/exercicios — lista os exercicios atuais\n"
                        "/aquecimento — mostra o aquecimento\n"
                        "/volume — volume por grupo muscular\n"
                        "/status — exercicio atual e progresso\n"
                        "/desfazer — apaga o ultimo registro\n"
                        "/ajuda — esta mensagem\n\n"
                        "<b>Registrar carga:</b>\n"
                        "<code>80</code> — somente carga\n"
                        "<code>80 8</code> — carga + RPE"
                    )
                    continue

                if lower in ("/exercicios", "exercicios", "/exercises", "exercises"):
                    exercises = ods_ops.read_exercises()
                    send(_format_exercises_msg(exercises))
                    continue

                if lower in ("/volume", "volume"):
                    exercises = ods_ops.read_exercises()
                    muscle_sets = {}
                    for ex in exercises:
                        muscles = ods_ops.MUSCLE_MAP.get(ex["name"], ["Other"])
                        for m in muscles:
                            muscle_sets[m] = muscle_sets.get(m, 0) + ex["sets"]
                    lines = ["<b>Volume por musculo</b>\n", "<i>series/sessao → series/semana (~3.5x)</i>\n"]
                    for muscle, sets in sorted(muscle_sets.items()):
                        weekly = round(sets * 3.5, 1)
                        lines.append(f"{muscle}: <b>{sets}</b> → ~{weekly:.0f}/sem")
                    send("\n".join(lines))
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

                session = load_session()
                if session is None:
                    send("Nenhuma sessao ativa. Use /gerar.")
                    continue

                handle(text, session)

            time.sleep(3)
    except KeyboardInterrupt:
        print("\nBot encerrado.")


if __name__ == "__main__":
    main()
