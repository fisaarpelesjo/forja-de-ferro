import gc
import json
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from forja_de_ferro import db_ops
from forja_de_ferro import ods_ops
from forja_de_ferro import telegram_poller


def _assert_progressao():
    assert ods_ops.suggest_next_weight(40, 7) == 44
    assert ods_ops.suggest_next_weight(40, 6) == 44
    assert ods_ops.suggest_next_weight(40, 8) == 42
    assert ods_ops.suggest_next_weight(40, 9) == 40
    assert ods_ops.suggest_next_weight(40, 10) == 38
    assert ods_ops.suggest_next_weight(40, 11) == 38
    assert ods_ops.suggest_next_weight(40, None) == 40
    assert ods_ops.suggest_next_weight(None, 8) is None


def _assert_equipamento_e_descanso():
    assert ods_ops.get_initial_target_weight("Rosca martelo (barra H)") == 16
    assert ods_ops.get_initial_target_weight("Supino reto (barra)") is None
    assert ods_ops.get_rest_interval("Agachamento Zercher") == "4 min"
    assert ods_ops.get_rest_interval("Remada curvada (barra)") == "3 min"
    assert ods_ops.get_rest_interval("Tríceps testa") == "2 min"
    assert ods_ops.get_rest_interval("Exercicio desconhecido") == "2 min"
    assert (
        ods_ops.format_loading_note("Tríceps testa", 18)
        == "barra W 6kg + 12kg de anilhas"
    )
    assert (
        ods_ops.format_loading_note("Pullover (barra)", 16)
        == "barra W 6kg + 10kg de anilhas"
    )
    assert (
        ods_ops.format_loading_note("Rosca martelo (barra H)", 18)
        == "barra H 9kg + 9kg de anilhas"
    )
    assert ods_ops.format_loading_note("Supino reto (barra)", 40) is None


def main():
    _assert_progressao()
    _assert_equipamento_e_descanso()

    original_db_path = db_ops.DB_PATH
    original_data_dir = db_ops.DATA_DIR
    original_ods_session = ods_ops.SESSION_FILE
    original_poller_session = telegram_poller.SESSION_FILE
    original_send = telegram_poller.send
    mensagens = []

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-regras-") as temp_dir:
        temp_path = Path(temp_dir)
        test_db = temp_path / "forja_de_ferro.db"
        test_session = temp_path / "session.json"

        try:
            db_ops.DATA_DIR = temp_path
            db_ops.DB_PATH = test_db
            ods_ops.SESSION_FILE = test_session
            telegram_poller.SESSION_FILE = test_session
            telegram_poller.send = mensagens.append

            telegram_poller.handle_preview()
            assert not test_session.exists()
            assert db_ops.count_filled([]) == 0

            telegram_poller.handle_exercises()
            assert "Lista de exercicios" in mensagens[-1]
            assert "Agachamento Zercher" in mensagens[-1]

            telegram_poller.handle_volume()
            assert "Volume por musculo" in mensagens[-1]
            assert "Quadriceps" in mensagens[-1]

            session_id = db_ops.create_session("2026-06-09")
            log_id = db_ops.log_exercise(session_id, "Agachamento Zercher", 3, 5, 0)
            session = {
                "session_id": session_id,
                "exercises": [
                    {
                        "log_id": log_id,
                        "name": "Agachamento Zercher",
                        "sets": 3,
                        "reps": 5,
                        "target_weight": None,
                        "rest_interval": "4 min",
                    }
                ],
            }
            test_session.write_text(json.dumps(session), encoding="utf-8")

            telegram_poller.handle("/desfazer", session)
            assert mensagens[-1] == "Nada para desfazer."

            telegram_poller.handle("carga invalida", session)
            assert "Formato:" in mensagens[-1]

            telegram_poller.handle("40 9", session)
            assert "Treino completo." in mensagens[-1]

            telegram_poller.handle("42 8", session)
            assert mensagens[-1] == "O treino ja esta completo. Use /status."

            telegram_poller.handle("/status", session)
            assert "Treino completo. 1/1" in mensagens[-1]

            telegram_poller.handle("/desfazer", session)
            assert "Desfeito" in mensagens[-1]
            assert db_ops.count_filled([log_id]) == 0

            print("Teste das regras de treino passou.")
        finally:
            db_ops.DB_PATH = original_db_path
            db_ops.DATA_DIR = original_data_dir
            ods_ops.SESSION_FILE = original_ods_session
            telegram_poller.SESSION_FILE = original_poller_session
            telegram_poller.send = original_send
            gc.collect()


if __name__ == "__main__":
    main()
