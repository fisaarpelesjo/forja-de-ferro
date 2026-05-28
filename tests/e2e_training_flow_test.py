import gc
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from forja_de_ferro import db_ops
from forja_de_ferro import ods_ops
from forja_de_ferro import telegram_poller


def _fetch_log(db_path, log_id):
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT exercise_name, weight, rpe
            FROM training_logs
            WHERE id = ?
            """,
            (log_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def main():
    original_db_path = db_ops.DB_PATH
    original_data_dir = db_ops.DATA_DIR
    original_ods_session = ods_ops.SESSION_FILE
    original_poller_session = telegram_poller.SESSION_FILE
    original_send = telegram_poller.send

    sent_messages = []

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-e2e-") as temp_dir:
        temp_path = Path(temp_dir)
        test_db = temp_path / "forja_de_ferro.db"
        test_session = temp_path / "session.json"

        try:
            db_ops.DATA_DIR = temp_path
            db_ops.DB_PATH = test_db
            ods_ops.SESSION_FILE = test_session
            telegram_poller.SESSION_FILE = test_session
            telegram_poller.send = sent_messages.append

            telegram_poller.handle_preview()
            assert test_db.exists(), "Preview should initialize the database for exercise lookup."
            assert not test_session.exists(), "Preview should not create a session file."
            assert "Previa do treino. Nada foi salvo." in sent_messages[-1]

            conn = sqlite3.connect(test_db)
            try:
                session_count = conn.execute("SELECT COUNT(*) FROM training_sessions").fetchone()[0]
                log_count = conn.execute("SELECT COUNT(*) FROM training_logs").fetchone()[0]
            finally:
                conn.close()
            assert session_count == 0
            assert log_count == 0

            telegram_poller.handle_generate()
            assert test_db.exists(), "E2E database was not created."
            assert test_session.exists(), "E2E session file was not created."

            session = json.loads(test_session.read_text(encoding="utf-8"))
            exercises = session["exercises"]
            total_exercises = len(list(ods_ops.TRAINING_EXERCISES))
            assert len(exercises) == total_exercises
            assert exercises[0]["target_weight"] is None
            assert exercises[0]["rest_interval"] == "4 min"
            assert "descanso: 4 min" in sent_messages[-2]
            assert "<pre>" not in sent_messages[-2]
            assert "Sessao de treino gerada." in sent_messages[-1]

            first_log_id = exercises[0]["log_id"]

            telegram_poller.handle("80 8", session)
            first_log = _fetch_log(test_db, first_log_id)
            assert first_log["weight"] == 80.0
            assert first_log["rpe"] == 8.0
            assert "80.0kg RPE 8" in sent_messages[-1]

            telegram_poller.handle_generate()
            progressed_session = json.loads(test_session.read_text(encoding="utf-8"))
            progressed_first = progressed_session["exercises"][0]
            assert progressed_first["target_weight"] == 82.0
            assert "82" in sent_messages[-2]
            assert "descanso: 4 min" in sent_messages[-2]

            telegram_poller.handle("/status", session)
            assert "Treino" in sent_messages[-1]
            assert f"1/{total_exercises}" in sent_messages[-1]

            telegram_poller.handle("/desfazer", session)
            undone_log = _fetch_log(test_db, first_log_id)
            assert undone_log["weight"] is None
            assert undone_log["rpe"] is None
            assert "Desfeito" in sent_messages[-1]

            telegram_poller.handle("80,5", session)
            relogged = _fetch_log(test_db, first_log_id)
            assert relogged["weight"] == 80.5
            assert relogged["rpe"] is None

            telegram_poller.handle_generate()
            maintained_session = json.loads(test_session.read_text(encoding="utf-8"))
            maintained_first = maintained_session["exercises"][0]
            assert maintained_first["target_weight"] == 80.5
            assert ods_ops.format_loading_note("Tríceps testa", 18.0) == "barra W 6kg + 12kg de anilhas"
            assert ods_ops.format_loading_note("Pullover (barra)", 16.0) == "barra W 6kg + 10kg de anilhas"
            triceps = {"name": "Tríceps testa", "sets": 3, "reps": 8, "target_weight": 18.0}
            assert "barra W 6kg + 12kg de anilhas" in telegram_poller._format_current_exercise(triceps)
            assert "barra W" not in telegram_poller._format_training_msg([triceps])

            telegram_poller.handle("80.5 10", maintained_session)
            telegram_poller.handle_generate()
            reduced_session = json.loads(test_session.read_text(encoding="utf-8"))
            reduced_first = reduced_session["exercises"][0]
            assert reduced_first["target_weight"] == 78.5

            print("Teste ponta a ponta do fluxo de treino passou.")
        finally:
            db_ops.DB_PATH = original_db_path
            db_ops.DATA_DIR = original_data_dir
            ods_ops.SESSION_FILE = original_ods_session
            telegram_poller.SESSION_FILE = original_poller_session
            telegram_poller.send = original_send
            gc.collect()


if __name__ == "__main__":
    main()
