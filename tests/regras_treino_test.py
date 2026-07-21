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
    assert ods_ops.get_initial_target_weight("Supino inclinado (barra)") == 41
    assert ods_ops.get_initial_target_weight("Supino fechado (barra)") == 35
    assert ods_ops.get_display_name("Supino fechado (barra)") == "Supino fechado"
    assert ods_ops.get_display_name("Rosca martelo (barra H)") == "Rosca martelo"
    assert ods_ops.get_initial_target_weight("Supino reto (barra)") is None
    assert ods_ops.get_rest_interval("Agachamento com barra nas costas") == "4 min"
    assert ods_ops.get_rest_interval("Remada curvada (barra)") == "3 min"
    assert ods_ops.get_rest_interval("Desenvolvimento (barra em pé)") == "4 min"
    assert ods_ops.get_rest_interval("Supino reto back-off") == "4 min"
    assert ods_ops.get_rest_interval("Supino inclinado (barra)") == "4 min"
    assert ods_ops.get_rest_interval("Supino fechado (barra)") == "3 min"
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
        ods_ops.format_loading_note("Remada alta (barra)", 18)
        == "barra W 6kg + 12kg de anilhas"
    )
    assert (
        ods_ops.format_loading_note("Rosca martelo (barra H)", 18)
        == "barra H 9kg + 9kg de anilhas"
    )
    assert (
        ods_ops.format_loading_note("Agachamento sumô com barra à frente", 40)
        == "barra oca 1,50 m 1kg + 39kg de anilhas"
    )
    for exercise_name in (
        "Agachamento com barra nas costas",
        "Supino reto (barra)",
        "Supino reto back-off",
        "Supino inclinado (barra)",
        "Supino fechado (barra)",
        "Remada curvada (barra)",
        "Desenvolvimento (barra em pé)",
        "Levantamento Terra Romeno",
        "Remada curvada alta no peito (barra)",
    ):
        assert (
            ods_ops.format_loading_note(exercise_name, 40)
            == "barra reta 2,20 m 11kg + 29kg de anilhas"
        )


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

            db_ops.init_db()
            conn = sqlite3.connect(test_db)
            try:
                versions = [
                    row[0]
                    for row in conn.execute(
                        "SELECT version FROM schema_migrations ORDER BY version"
                    )
                ]
                indexes = {
                    row[0]
                    for row in conn.execute(
                        """
                        SELECT name FROM sqlite_master
                        WHERE type = 'index' AND name LIKE 'idx_training_logs_%'
                        """
                    )
                }
            finally:
                conn.close()
            assert versions == list(range(1, db_ops.SCHEMA_VERSION + 1))
            assert "idx_training_logs_session_pending" in indexes
            assert "idx_training_logs_exercise_history" in indexes
            assert db_ops.get_body_profile() is None
            perfil = db_ops.set_body_profile(183, 30)
            assert perfil["height_cm"] == 183.0
            assert perfil["age_years"] == 30
            assert db_ops.get_body_profile()["height_cm"] == 183.0
            try:
                db_ops.set_body_profile(80, 30)
                raise AssertionError("Altura abaixo do limite deveria falhar.")
            except ValueError:
                pass
            assert db_ops.get_latest_body_weight() is None
            first_weight = db_ops.add_body_weight(
                118,
                source="teste",
                recorded_at="2026-06-13 08:00:00",
            )
            second_weight = db_ops.add_body_weight(
                117.5,
                source="teste",
                recorded_at="2026-06-14 08:00:00",
            )
            assert first_weight["weight_kg"] == 118.0
            assert db_ops.get_latest_body_weight()["id"] == second_weight["id"]
            assert len(db_ops.list_body_weights()) == 2
            try:
                db_ops.add_body_weight(20)
                raise AssertionError("Peso abaixo do limite deveria falhar.")
            except ValueError:
                pass
            assert db_ops.get_latest_waist_measurement() is None
            first_waist = db_ops.add_waist_measurement(
                112,
                source="teste",
                recorded_at="2026-06-13 08:00:00",
            )
            second_waist = db_ops.add_waist_measurement(
                110.5,
                source="teste",
                recorded_at="2026-06-14 08:00:00",
            )
            assert first_waist["circumference_cm"] == 112.0
            assert (
                db_ops.get_latest_waist_measurement()["id"]
                == second_waist["id"]
            )
            assert len(db_ops.list_waist_measurements()) == 2
            try:
                db_ops.add_waist_measurement(20)
                raise AssertionError("Cintura abaixo do limite deveria falhar.")
            except ValueError:
                pass
            active_exercises = db_ops.get_or_seed_exercises()
            muscle_groups = db_ops.list_muscle_groups()
            assert all(ex["name"] in muscle_groups for ex in active_exercises)
            agachamento_groups = db_ops.get_muscle_groups(
                "Agachamento com barra nas costas"
            )
            assert agachamento_groups[0] == {
                "muscle_group": "Quadriceps",
                "role": "principal",
            }
            assert any(
                group["role"] == "secundario" for group in agachamento_groups
            )
            sumo_groups = db_ops.get_muscle_groups(
                "Agachamento sumô com barra à frente"
            )
            assert sumo_groups[0] == {
                "muscle_group": "Adutores",
                "role": "principal",
            }
            assert db_ops.get_muscle_groups("Exercicio desconhecido") == []
            plan_a = db_ops.get_active_training_plan()
            assert plan_a["name"] == "A"
            assert len(plan_a["exercises"]) == len(active_exercises)
            assert plan_a["exercises"][1] == {
                "name": "Agachamento sumô com barra à frente",
                "sets": 3,
                "reps": 10,
            }

            db_ops.replace_training_plan(
                "B",
                [
                    {"name": "Supino reto (barra)", "sets": 3, "reps": 5},
                    {"name": "Remada curvada (barra)", "sets": 3, "reps": 8},
                ],
                active=True,
            )
            plan_b = db_ops.get_active_training_plan()
            assert plan_b["name"] == "B"
            assert len(plan_b["exercises"]) == 2

            telegram_poller.handle_plans()
            assert "B: 2 exercicios ✓ ativo" in mensagens[-1]
            telegram_poller.handle_select_plan("/plano A")
            assert "Plano ativo: <b>A</b>" in mensagens[-1]
            assert db_ops.get_active_training_plan()["name"] == "A"

            treino_a = db_ops.create_session("2026-06-08", "A")
            for sort_order, (name, weight, rpe) in enumerate(
                [
                    ("Agachamento com barra nas costas", 67, 8),
                    ("Levantamento Terra Romeno", 73, 9),
                    ("Remada curvada (barra)", 61, 9),
                ]
            ):
                treino_a_log = db_ops.log_exercise(treino_a, name, 3, 8, sort_order)
                db_ops.update_log_weight(treino_a_log, weight, rpe)

            treino_b = ods_ops.build_training_b()
            treino_b_pesos = {
                item["name"]: item["target_weight"]
                for item in treino_b
            }
            assert treino_b_pesos["Farmer walk ida e volta"] == 34
            assert treino_b_pesos["Marcha forte no lugar com joelho alto"] is None
            assert treino_b_pesos["Agachamento com pausa"] is None
            assert treino_b_pesos["Remada leve com barra"] == 38
            assert treino_b_pesos["Flexão"] is None
            assert (
                treino_b[0]["loading_note"]
                == "2 barras de 40 cm + 17kg por mao"
            )
            assert (
                treino_b[1]["loading_note"]
                is None
            )
            assert (
                treino_b[2]["loading_note"]
                is None
            )
            assert (
                treino_b[3]["loading_note"]
                == "barra reta 2,50 m 9kg + 29kg de anilhas"
            )
            telegram_poller.handle_training_b()
            assert "10 voltas | descanso 60s" in mensagens[-1]
            assert "Treino B - garagem" not in mensagens[-1]
            assert "Farmer walk ida e volta" in mensagens[-1]
            assert "peso: 34kg" in mensagens[-1]
            assert "2 barras de 40 cm + 17kg por mao" in mensagens[-1]

            legacy_db = temp_path / "legado.db"
            conn = sqlite3.connect(legacy_db)
            try:
                conn.execute(
                    """
                    CREATE TABLE training_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        training_type TEXT NOT NULL DEFAULT 'TREINO'
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE training_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL REFERENCES training_sessions(id),
                        exercise_name TEXT NOT NULL,
                        sets INTEGER NOT NULL,
                        reps INTEGER NOT NULL,
                        weight REAL,
                        rpe REAL,
                        sort_order INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                conn.execute(
                    "INSERT INTO training_sessions (date) VALUES ('2026-06-01')"
                )
                conn.commit()
            finally:
                conn.close()
            db_ops.DB_PATH = legacy_db
            db_ops.init_db()
            conn = sqlite3.connect(legacy_db)
            try:
                assert conn.execute(
                    "SELECT COUNT(*) FROM training_sessions"
                ).fetchone()[0] == 1
                assert conn.execute(
                    "SELECT MAX(version) FROM schema_migrations"
                ).fetchone()[0] == db_ops.SCHEMA_VERSION
            finally:
                conn.close()
            db_ops.DB_PATH = test_db

            telegram_poller.handle_preview()
            assert not test_session.exists()
            assert db_ops.count_filled([]) == 0

            telegram_poller.handle_exercises()
            assert "Lista de exercicios" in mensagens[-1]
            assert "Agachamento com barra nas costas" in mensagens[-1]

            telegram_poller.handle_volume()
            assert "Volume por musculo" in mensagens[-1]
            assert "Quadriceps" in mensagens[-1]

            session_id = db_ops.create_session("2026-06-09")
            log_id = db_ops.log_exercise(
                session_id,
                "Agachamento com barra nas costas",
                3,
                5,
                0,
            )
            session = {
                "session_id": session_id,
                "exercises": [
                    {
                        "log_id": log_id,
                        "name": "Agachamento com barra nas costas",
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
            assert "Resumo da sessao" in mensagens[-1]
            assert "Volume: <b>600 kg</b>" in mensagens[-1]

            telegram_poller.handle("42 8", session)
            assert mensagens[-1] == "O treino ja esta completo. Use /status."

            telegram_poller.handle("/status", session)
            assert "Treino completo. 1/1" in mensagens[-1]

            telegram_poller.handle("/desfazer", session)
            assert "Desfeito" in mensagens[-1]
            assert db_ops.count_filled([log_id]) == 0

            telegram_poller.handle("40 9", session)
            test_session.unlink()
            assert telegram_poller.load_session() is None
            assert not test_session.exists()

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
