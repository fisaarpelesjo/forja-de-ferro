import gc
import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from forja_de_ferro import backup_ops
from forja_de_ferro import db_ops


def _session_count(database_path):
    conn = sqlite3.connect(database_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM training_sessions").fetchone()[0]
    finally:
        conn.close()


def main():
    original_db_path = db_ops.DB_PATH
    original_data_dir = db_ops.DATA_DIR

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-backup-") as temp_dir:
        temp_path = Path(temp_dir)
        source_db = temp_path / "origem.db"
        restored_db = temp_path / "restaurado.db"

        try:
            db_ops.DATA_DIR = temp_path
            db_ops.DB_PATH = source_db
            db_ops.get_or_seed_exercises()
            session_id = db_ops.create_session("2026-06-09")
            log_id = db_ops.log_exercise(
                session_id,
                "Agachamento Zercher",
                3,
                5,
                0,
            )
            db_ops.update_log_weight(log_id, 48, 9)
            db_ops.add_body_weight(118, source="teste")

            backup = backup_ops.criar_backup(
                temp_path / "backups",
                source_db,
            )
            assert backup.is_file()
            assert _session_count(backup) == 1

            export = backup_ops.exportar_dados(
                temp_path / "exportacoes",
                source_db,
            )
            payload = json.loads(export.read_text(encoding="utf-8"))
            assert payload["schema_version"] == db_ops.SCHEMA_VERSION
            assert len(payload["tables"]["training_sessions"]) == 1
            assert payload["tables"]["training_logs"][0]["weight"] == 48
            assert payload["tables"]["exercise_muscle_groups"]
            assert payload["tables"]["training_plans"]
            assert payload["tables"]["training_plan_exercises"]
            assert payload["tables"]["body_weights"][0]["weight_kg"] == 118

            restored, safety = backup_ops.restaurar_backup(
                backup,
                restored_db,
                create_safety_backup=False,
            )
            assert restored == restored_db
            assert safety is None
            assert _session_count(restored_db) == 1
            assert backup_ops.validar_banco(restored_db)

            print("Teste de backup e exportacao passou.")
        finally:
            db_ops.DB_PATH = original_db_path
            db_ops.DATA_DIR = original_data_dir
            gc.collect()


if __name__ == "__main__":
    main()
