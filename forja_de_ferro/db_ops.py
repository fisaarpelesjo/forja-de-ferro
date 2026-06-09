"""Operacoes SQLite para os dados da Forja de Ferro."""

import sqlite3
from itertools import groupby
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "forja_de_ferro.db"
SCHEMA_VERSION = 4

DEFAULT_EXERCISES = [
    {"name": "Agachamento Zercher", "sets": 3, "reps": 5},
    {"name": "Supino reto (barra)", "sets": 3, "reps": 5},
    {"name": "Supino reto back-off", "sets": 2, "reps": 8},
    {"name": "Remada curvada (barra)", "sets": 3, "reps": 8},
    {"name": "Desenvolvimento (barra em pé)", "sets": 3, "reps": 5},
    {"name": "Levantamento Terra Romeno", "sets": 3, "reps": 8},
    {"name": "Pullover (barra)", "sets": 3, "reps": 10},
    {"name": "Remada alta (barra)", "sets": 3, "reps": 10},
    {"name": "Remada curvada alta no peito (barra)", "sets": 3, "reps": 10},
    {"name": "Rosca martelo (barra H)", "sets": 3, "reps": 8},
    {"name": "Tríceps testa", "sets": 3, "reps": 8},
]

DEFAULT_MUSCLE_GROUPS = {
    "Agachamento (barra)": [
        ("Quadriceps", "principal"),
        ("Gluteos", "secundario"),
    ],
    "Agachamento Zercher": [
        ("Quadriceps", "principal"),
        ("Gluteos", "secundario"),
        ("Core", "secundario"),
    ],
    "Zercher squat": [
        ("Quadriceps", "principal"),
        ("Gluteos", "secundario"),
        ("Core", "secundario"),
    ],
    "Supino reto (barra)": [("Peitoral", "principal")],
    "Supino reto back-off": [("Peitoral", "principal")],
    "Remada curvada (barra)": [("Dorsais", "principal")],
    "Desenvolvimento (barra em pé)": [("Deltoide anterior", "principal")],
    "Desenvolvimento (barra em pe)": [("Deltoide anterior", "principal")],
    "Levantamento Terra Romeno": [
        ("Posteriores", "principal"),
        ("Gluteos", "secundario"),
    ],
    "Pullover (barra)": [("Dorsais", "principal")],
    "Remada alta (barra)": [
        ("Deltoide lateral", "principal"),
        ("Trapezio", "secundario"),
    ],
    "Remada curvada alta no peito (barra)": [
        ("Deltoide posterior", "principal"),
        ("Trapezio", "secundario"),
    ],
    "Elevação lateral": [("Deltoide lateral", "principal")],
    "Elevacao lateral": [("Deltoide lateral", "principal")],
    "Crucifixo invertido": [("Deltoide posterior", "principal")],
    "Encolhimento com barra": [("Trapezio", "principal")],
    "Rosca direta": [("Biceps", "principal")],
    "Rosca martelo (barra H)": [
        ("Biceps", "principal"),
        ("Antebraco", "secundario"),
    ],
    "Rosca de punho (barra)": [("Antebraco", "principal")],
    "Rosca de punho reversa (barra)": [("Antebraco", "principal")],
    "Wrist curl (barra)": [("Antebraco", "principal")],
    "Reverse wrist curl (barra)": [("Antebraco", "principal")],
    "Tríceps testa": [("Triceps", "principal")],
    "Triceps testa": [("Triceps", "principal")],
}


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA_V1_STATEMENTS = (
    """
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                sort_order INTEGER NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1
            )
            """,
    """
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                training_type TEXT NOT NULL DEFAULT 'TREINO'
            )
            """,
    """
            CREATE TABLE IF NOT EXISTS training_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES training_sessions(id),
                exercise_name TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                weight REAL,
                rpe REAL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """,
    """
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit TEXT NOT NULL,
                serving_g REAL NOT NULL DEFAULT 100,
                protein_g REAL NOT NULL DEFAULT 0,
                carbo_g REAL NOT NULL DEFAULT 0,
                fat_g REAL NOT NULL DEFAULT 0,
                calories REAL NOT NULL DEFAULT 0,
                fiber_g REAL NOT NULL DEFAULT 0,
                omega3_g REAL NOT NULL DEFAULT 0,
                potassium_mg REAL NOT NULL DEFAULT 0,
                magnesium_mg REAL NOT NULL DEFAULT 0,
                zinc_mg REAL NOT NULL DEFAULT 0,
                vitamin_d_ui REAL NOT NULL DEFAULT 0
            )
            """,
    """
            CREATE TABLE IF NOT EXISTS diet_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protein_g REAL,
                carbo_g REAL,
                fat_g REAL,
                calories REAL,
                fiber_g REAL,
                omega3_g REAL,
                potassium_mg REAL,
                magnesium_mg REAL,
                zinc_mg REAL,
                vitamin_d_ui REAL
            )
            """,
    """
            CREATE TABLE IF NOT EXISTS diet_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal TEXT NOT NULL,
                food_id INTEGER NOT NULL REFERENCES foods(id),
                quantity REAL NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """,
)

SCHEMA_V2_STATEMENTS = (
    """
    CREATE INDEX IF NOT EXISTS idx_training_logs_session_pending
    ON training_logs (session_id, weight, sort_order)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_training_logs_exercise_history
    ON training_logs (exercise_name, id)
    """,
)

SCHEMA_V3_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS exercise_muscle_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_name TEXT NOT NULL,
        muscle_group TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('principal', 'secundario')),
        sort_order INTEGER NOT NULL DEFAULT 0,
        UNIQUE (exercise_name, muscle_group)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_exercise_muscle_groups_exercise
    ON exercise_muscle_groups (exercise_name, sort_order)
    """,
)

SCHEMA_V4_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS training_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        active INTEGER NOT NULL DEFAULT 0,
        sort_order INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_plan_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
        exercise_name TEXT NOT NULL,
        sets INTEGER NOT NULL,
        reps INTEGER NOT NULL,
        sort_order INTEGER NOT NULL,
        UNIQUE (plan_id, sort_order)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_training_plan_exercises_plan
    ON training_plan_exercises (plan_id, sort_order)
    """,
)

MIGRATIONS = {
    1: SCHEMA_V1_STATEMENTS,
    2: SCHEMA_V2_STATEMENTS,
    3: SCHEMA_V3_STATEMENTS,
    4: SCHEMA_V4_STATEMENTS,
}


def get_schema_version(conn=None):
    owns_connection = conn is None
    connection = conn or _connect()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        row = connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
        ).fetchone()
        return int(row["version"])
    finally:
        if owns_connection:
            connection.close()


def init_db():
    with _connect() as conn:
        current_version = get_schema_version(conn)
        if current_version > SCHEMA_VERSION:
            raise RuntimeError(
                f"Banco usa esquema {current_version}, mas o codigo suporta ate "
                f"{SCHEMA_VERSION}."
            )

        for version in range(current_version + 1, SCHEMA_VERSION + 1):
            statements = MIGRATIONS.get(version)
            if statements is None:
                raise RuntimeError(f"Migracao de esquema ausente para a versao {version}.")
            for statement in statements:
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )
        _seed_default_muscle_groups(conn)
        _seed_default_training_plan(conn)


def _seed_default_muscle_groups(conn):
    if get_schema_version(conn) < 3:
        return
    for exercise_name, groups in DEFAULT_MUSCLE_GROUPS.items():
        for sort_order, (muscle_group, role) in enumerate(groups):
            conn.execute(
                """
                INSERT OR IGNORE INTO exercise_muscle_groups
                    (exercise_name, muscle_group, role, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (exercise_name, muscle_group, role, sort_order),
            )


def _seed_default_training_plan(conn):
    if get_schema_version(conn) < 4:
        return
    plan = conn.execute(
        "SELECT id FROM training_plans WHERE name = 'A'"
    ).fetchone()
    if plan is None:
        cur = conn.execute(
            """
            INSERT INTO training_plans (name, active, sort_order)
            VALUES ('A', 1, 0)
            """
        )
        plan_id = cur.lastrowid
    else:
        plan_id = plan["id"]

    active_plan = conn.execute(
        "SELECT id FROM training_plans WHERE active = 1 LIMIT 1"
    ).fetchone()
    if active_plan is None:
        conn.execute("UPDATE training_plans SET active = 1 WHERE id = ?", (plan_id,))

    count = conn.execute(
        "SELECT COUNT(*) FROM training_plan_exercises WHERE plan_id = ?",
        (plan_id,),
    ).fetchone()[0]
    if count:
        return

    exercises = conn.execute(
        """
        SELECT name, sets, reps
        FROM exercises
        WHERE active = 1
        ORDER BY sort_order
        """
    ).fetchall()
    for sort_order, exercise in enumerate(exercises):
        conn.execute(
            """
            INSERT INTO training_plan_exercises
                (plan_id, exercise_name, sets, reps, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                exercise["name"],
                exercise["sets"],
                exercise["reps"],
                sort_order,
            ),
        )


# --- exercises ---

def _insert_exercises(conn, exercises):
    conn.execute("DELETE FROM exercises")
    for idx, ex in enumerate(exercises, start=1):
        conn.execute(
            """
            INSERT INTO exercises (name, sets, reps, sort_order, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (ex["name"], int(ex["sets"]), int(ex["reps"]), idx),
        )
    _seed_default_training_plan(conn)


def list_exercises():
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT name, sets, reps
            FROM exercises
            WHERE active = 1
            ORDER BY sort_order ASC
            """
        ).fetchall()
        return [{"name": r["name"], "sets": r["sets"], "reps": r["reps"]} for r in rows]


def get_or_seed_exercises(seed_exercises=None):
    init_db()
    existing = list_exercises()
    if existing:
        return existing

    to_seed = seed_exercises if seed_exercises else DEFAULT_EXERCISES
    with _connect() as conn:
        _insert_exercises(conn, to_seed)
        conn.commit()
    return list_exercises()


def replace_exercises(exercises):
    init_db()
    with _connect() as conn:
        _insert_exercises(conn, exercises)
        conn.commit()


def get_muscle_groups(exercise_name):
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT muscle_group, role
            FROM exercise_muscle_groups
            WHERE exercise_name = ?
            ORDER BY sort_order, id
            """,
            (exercise_name,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_muscle_groups():
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT exercise_name, muscle_group, role
            FROM exercise_muscle_groups
            ORDER BY exercise_name, sort_order, id
            """
        ).fetchall()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["exercise_name"], []).append(
            {
                "muscle_group": row["muscle_group"],
                "role": row["role"],
            }
        )
    return grouped


def list_training_plans():
    get_or_seed_exercises()
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.active, p.sort_order, COUNT(e.id) AS exercise_count
            FROM training_plans p
            LEFT JOIN training_plan_exercises e ON e.plan_id = p.id
            GROUP BY p.id
            ORDER BY p.sort_order, p.id
            """
        ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "active": bool(row["active"]),
                "exercise_count": row["exercise_count"],
            }
            for row in rows
        ]


def get_active_training_plan():
    get_or_seed_exercises()
    init_db()
    with _connect() as conn:
        plan = conn.execute(
            """
            SELECT id, name
            FROM training_plans
            WHERE active = 1
            ORDER BY sort_order, id
            LIMIT 1
            """
        ).fetchone()
        if plan is None:
            return None
        exercises = conn.execute(
            """
            SELECT exercise_name AS name, sets, reps
            FROM training_plan_exercises
            WHERE plan_id = ?
            ORDER BY sort_order, id
            """,
            (plan["id"],),
        ).fetchall()
        return {
            "id": plan["id"],
            "name": plan["name"],
            "exercises": [dict(row) for row in exercises],
        }


def replace_training_plan(name, exercises, active=False):
    get_or_seed_exercises()
    init_db()
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Nome do plano nao pode ficar vazio.")
    if not exercises:
        raise ValueError("Plano precisa ter pelo menos um exercicio.")

    with _connect() as conn:
        plan = conn.execute(
            "SELECT id FROM training_plans WHERE name = ?",
            (normalized_name,),
        ).fetchone()
        if plan is None:
            next_order = conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM training_plans"
            ).fetchone()[0]
            cur = conn.execute(
                """
                INSERT INTO training_plans (name, active, sort_order)
                VALUES (?, 0, ?)
                """,
                (normalized_name, next_order),
            )
            plan_id = cur.lastrowid
        else:
            plan_id = plan["id"]
            conn.execute(
                "DELETE FROM training_plan_exercises WHERE plan_id = ?",
                (plan_id,),
            )

        for sort_order, exercise in enumerate(exercises):
            conn.execute(
                """
                INSERT INTO training_plan_exercises
                    (plan_id, exercise_name, sets, reps, sort_order)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    exercise["name"],
                    int(exercise["sets"]),
                    int(exercise["reps"]),
                    sort_order,
                ),
            )
        if active:
            conn.execute("UPDATE training_plans SET active = 0")
            conn.execute(
                "UPDATE training_plans SET active = 1 WHERE id = ?",
                (plan_id,),
            )
        return plan_id


def set_active_training_plan(name):
    get_or_seed_exercises()
    init_db()
    with _connect() as conn:
        plan = conn.execute(
            """
            SELECT id
            FROM training_plans
            WHERE lower(name) = lower(?)
            """,
            (name.strip(),),
        ).fetchone()
        if plan is None:
            return False
        count = conn.execute(
            "SELECT COUNT(*) FROM training_plan_exercises WHERE plan_id = ?",
            (plan["id"],),
        ).fetchone()[0]
        if count == 0:
            return False
        conn.execute("UPDATE training_plans SET active = 0")
        conn.execute(
            "UPDATE training_plans SET active = 1 WHERE id = ?",
            (plan["id"],),
        )
        return True


# --- training sessions ---

def create_session(date_iso, training_type="TREINO"):
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO training_sessions (date, training_type) VALUES (?, ?)",
            (date_iso, training_type),
        )
        conn.commit()
        return cur.lastrowid


def log_exercise(session_id, exercise_name, sets, reps, sort_order):
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO training_logs (session_id, exercise_name, sets, reps, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, exercise_name, int(sets), int(reps), sort_order),
        )
        conn.commit()
        return cur.lastrowid


def update_log_weight(log_id, weight, rpe=None):
    with _connect() as conn:
        conn.execute(
            "UPDATE training_logs SET weight=?, rpe=? WHERE id=?",
            (
                float(weight) if weight is not None else None,
                float(rpe) if rpe is not None else None,
                log_id,
            ),
        )
        conn.commit()


def get_last_weights():
    """Return {exercise_name: last_weight} from most recent entry per exercise."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT exercise_name, weight
            FROM training_logs
            WHERE weight IS NOT NULL AND weight > 0
              AND id IN (
                SELECT MAX(id)
                FROM training_logs
                WHERE weight IS NOT NULL AND weight > 0
                GROUP BY exercise_name
              )
            """
        ).fetchall()
        return {r["exercise_name"]: r["weight"] for r in rows}


def get_last_performance():
    """Return {exercise_name: {weight, rpe}} from most recent entry per exercise."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT exercise_name, weight, rpe
            FROM training_logs
            WHERE weight IS NOT NULL AND weight > 0
              AND id IN (
                SELECT MAX(id)
                FROM training_logs
                WHERE weight IS NOT NULL AND weight > 0
                GROUP BY exercise_name
              )
            """
        ).fetchall()
        return {
            r["exercise_name"]: {"weight": r["weight"], "rpe": r["rpe"]}
            for r in rows
        }


def count_filled(log_ids):
    """Count how many of the given log_ids already have weight set."""
    if not log_ids:
        return 0
    placeholders = ",".join("?" * len(log_ids))
    with _connect() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) FROM training_logs WHERE id IN ({placeholders}) AND weight IS NOT NULL",
            list(log_ids),
        ).fetchone()
        return row[0]


def get_latest_incomplete_session():
    """Retorna a sessao mais recente que possui logs pendentes."""
    init_db()
    with _connect() as conn:
        session = conn.execute(
            """
            SELECT s.id, s.date, s.training_type
            FROM training_sessions s
            WHERE EXISTS (
                SELECT 1 FROM training_logs l WHERE l.session_id = s.id
            )
              AND EXISTS (
                SELECT 1
                FROM training_logs l
                WHERE l.session_id = s.id AND l.weight IS NULL
            )
            ORDER BY s.id DESC
            LIMIT 1
            """
        ).fetchone()
        if session is None:
            return None

        logs = conn.execute(
            """
            SELECT id, exercise_name, sets, reps, weight, rpe, sort_order
            FROM training_logs
            WHERE session_id = ?
            ORDER BY sort_order, id
            """,
            (session["id"],),
        ).fetchall()

        exercises = []
        for log in logs:
            previous = conn.execute(
                """
                SELECT weight, rpe
                FROM training_logs
                WHERE exercise_name = ?
                  AND id < ?
                  AND weight IS NOT NULL
                  AND weight > 0
                ORDER BY id DESC
                LIMIT 1
                """,
                (log["exercise_name"], log["id"]),
            ).fetchone()
            exercises.append(
                {
                    "log_id": log["id"],
                    "name": log["exercise_name"],
                    "sets": log["sets"],
                    "reps": log["reps"],
                    "weight": log["weight"],
                    "rpe": log["rpe"],
                    "sort_order": log["sort_order"],
                    "previous_weight": previous["weight"] if previous else None,
                    "previous_rpe": previous["rpe"] if previous else None,
                }
            )

        return {
            "session_id": session["id"],
            "date": session["date"],
            "training_type": session["training_type"],
            "exercises": exercises,
        }


def is_session_incomplete(session_id, log_ids):
    """Valida se os logs pertencem a uma sessao existente e ainda incompleta."""
    if session_id is None or not log_ids:
        return False
    placeholders = ",".join("?" * len(log_ids))
    with _connect() as conn:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN weight IS NULL THEN 1 ELSE 0 END) AS pending
            FROM training_logs
            WHERE session_id = ? AND id IN ({placeholders})
            """,
            [session_id, *log_ids],
        ).fetchone()
        return row["total"] == len(log_ids) and row["pending"] > 0


def get_session_summary(session_id):
    """Retorna resumo e comparacoes de uma sessao preenchida."""
    init_db()
    with _connect() as conn:
        session = conn.execute(
            "SELECT id, date, training_type FROM training_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if session is None:
            return None

        logs = conn.execute(
            """
            SELECT id, exercise_name, sets, reps, weight, rpe, sort_order
            FROM training_logs
            WHERE session_id = ? AND weight IS NOT NULL AND weight > 0
            ORDER BY sort_order, id
            """,
            (session_id,),
        ).fetchall()
        if not logs:
            return None

        current_names = [row["exercise_name"] for row in logs]
        previous_session = None
        candidates = conn.execute(
            """
            SELECT id, date
            FROM training_sessions
            WHERE id < ?
            ORDER BY id DESC
            """,
            (session_id,),
        ).fetchall()
        for candidate in candidates:
            candidate_logs = conn.execute(
                """
                SELECT exercise_name, sets, reps, weight
                FROM training_logs
                WHERE session_id = ? AND weight IS NOT NULL AND weight > 0
                ORDER BY sort_order, id
                """,
                (candidate["id"],),
            ).fetchall()
            if [row["exercise_name"] for row in candidate_logs] == current_names:
                previous_session = {
                    "id": candidate["id"],
                    "date": candidate["date"],
                    "volume": sum(
                        row["sets"] * row["reps"] * row["weight"]
                        for row in candidate_logs
                    ),
                }
                break

        increases = []
        reductions = []
        consolidations = []
        maintained_rpe9 = []
        records = []
        rpes = []

        for log in logs:
            if log["rpe"] is not None:
                rpes.append(float(log["rpe"]))
            previous = conn.execute(
                """
                SELECT weight, rpe
                FROM training_logs
                WHERE exercise_name = ?
                  AND id < ?
                  AND weight IS NOT NULL
                  AND weight > 0
                ORDER BY id DESC
                LIMIT 1
                """,
                (log["exercise_name"], log["id"]),
            ).fetchone()
            previous_best = conn.execute(
                """
                SELECT
                    MAX(weight) AS max_weight,
                    MAX(sets * reps * weight) AS max_volume
                FROM training_logs
                WHERE exercise_name = ?
                  AND id < ?
                  AND weight IS NOT NULL
                  AND weight > 0
                """,
                (log["exercise_name"], log["id"]),
            ).fetchone()

            current_weight = float(log["weight"])
            current_volume = float(log["sets"] * log["reps"] * log["weight"])
            item = {
                "name": log["exercise_name"],
                "weight": current_weight,
                "rpe": float(log["rpe"]) if log["rpe"] is not None else None,
            }

            if previous:
                previous_weight = float(previous["weight"])
                previous_rpe = (
                    float(previous["rpe"]) if previous["rpe"] is not None else None
                )
                item["previous_weight"] = previous_weight
                item["previous_rpe"] = previous_rpe
                if current_weight > previous_weight:
                    increases.append(item)
                elif current_weight < previous_weight:
                    reductions.append(item)
                elif (
                    previous_rpe is not None
                    and previous_rpe >= 9
                    and item["rpe"] is not None
                    and item["rpe"] <= 8
                ):
                    consolidations.append(item)
                elif item["rpe"] == 9:
                    maintained_rpe9.append(item)

            if previous_best["max_weight"] is not None:
                record_types = []
                if current_weight > float(previous_best["max_weight"]):
                    record_types.append("carga")
                if current_volume > float(previous_best["max_volume"]):
                    record_types.append("volume")
                if record_types:
                    records.append(
                        {
                            "name": log["exercise_name"],
                            "types": record_types,
                            "weight": current_weight,
                        }
                    )

        volume = sum(
            float(log["sets"] * log["reps"] * log["weight"]) for log in logs
        )
        return {
            "session_id": session["id"],
            "date": session["date"],
            "volume": volume,
            "rpe_average": sum(rpes) / len(rpes) if rpes else None,
            "exercise_count": len(logs),
            "previous_session": previous_session,
            "volume_delta": (
                volume - previous_session["volume"] if previous_session else None
            ),
            "increases": increases,
            "reductions": reductions,
            "consolidations": consolidations,
            "maintained_rpe9": maintained_rpe9,
            "records": records,
        }


def import_log_rows(rows):
    """
    Bulk-import historical diary rows. Groups by (date, training_type) into sessions.
    Each row dict: {date, training_type, exercise_name, sets, reps, weight?, rpe?}
    """
    init_db()
    rows_sorted = sorted(rows, key=lambda r: (r["date"], r.get("training_type", "TREINO")))
    with _connect() as conn:
        for key, group in groupby(rows_sorted, key=lambda r: (r["date"], r.get("training_type", "TREINO"))):
            date_iso, ttype = key
            cur = conn.execute(
                "INSERT INTO training_sessions (date, training_type) VALUES (?, ?)",
                (date_iso, ttype),
            )
            session_id = cur.lastrowid
            for idx, row in enumerate(group):
                conn.execute(
                    """
                    INSERT INTO training_logs
                        (session_id, exercise_name, sets, reps, weight, rpe, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        row["exercise_name"],
                        int(row.get("sets", 0)),
                        int(row.get("reps", 0)),
                        row.get("weight"),
                        row.get("rpe"),
                        idx,
                    ),
                )
        conn.commit()


# --- diet ---

_NUTRIENT_COLS = (
    "protein_g", "carbo_g", "fat_g", "calories",
    "fiber_g", "omega3_g", "potassium_mg", "magnesium_mg", "zinc_mg", "vitamin_d_ui",
)

# Nutrients stored per serving_g for unit='g' foods, per 1 unit otherwise.
# consumed = quantity * nutrient / (serving_g if unit='g' else 1)
_NUTRIENT_SELECT = ", ".join(
    f"e.quantity * f.{c} / CASE WHEN f.unit = 'g' THEN f.serving_g ELSE 1.0 END AS {c}"
    for c in _NUTRIENT_COLS
)


def upsert_food(name, unit, serving_g, protein_g=0, carbo_g=0, fat_g=0,
                calories=0, fiber_g=0, omega3_g=0, potassium_mg=0,
                magnesium_mg=0, zinc_mg=0, vitamin_d_ui=0):
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO foods
                (name, unit, serving_g, protein_g, carbo_g, fat_g, calories,
                 fiber_g, omega3_g, potassium_mg, magnesium_mg, zinc_mg, vitamin_d_ui)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                unit=excluded.unit, serving_g=excluded.serving_g,
                protein_g=excluded.protein_g, carbo_g=excluded.carbo_g,
                fat_g=excluded.fat_g, calories=excluded.calories,
                fiber_g=excluded.fiber_g, omega3_g=excluded.omega3_g,
                potassium_mg=excluded.potassium_mg, magnesium_mg=excluded.magnesium_mg,
                zinc_mg=excluded.zinc_mg, vitamin_d_ui=excluded.vitamin_d_ui
            """,
            (name, unit, float(serving_g),
             float(protein_g), float(carbo_g), float(fat_g), float(calories),
             float(fiber_g), float(omega3_g), float(potassium_mg),
             float(magnesium_mg), float(zinc_mg), float(vitamin_d_ui)),
        )
        conn.commit()
        row = conn.execute("SELECT id FROM foods WHERE name=?", (name,)).fetchone()
        return row[0]


def get_food_by_name(name):
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM foods WHERE name=?", (name,)).fetchone()
        return dict(row) if row else None


def list_foods():
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM foods ORDER BY name ASC").fetchall()
        return [dict(r) for r in rows]


def set_diet_targets(protein_g=None, carbo_g=None, fat_g=None, calories=None,
                     fiber_g=None, omega3_g=None, potassium_mg=None,
                     magnesium_mg=None, zinc_mg=None, vitamin_d_ui=None):
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM diet_targets")
        cur = conn.execute(
            """
            INSERT INTO diet_targets
                (protein_g, carbo_g, fat_g, calories, fiber_g, omega3_g,
                 potassium_mg, magnesium_mg, zinc_mg, vitamin_d_ui)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (protein_g, carbo_g, fat_g, calories, fiber_g, omega3_g,
             potassium_mg, magnesium_mg, zinc_mg, vitamin_d_ui),
        )
        conn.commit()
        return cur.lastrowid


def get_diet_targets():
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM diet_targets LIMIT 1").fetchone()
        return dict(row) if row else None


def add_diet_entry(meal, food_id, quantity, sort_order=0):
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO diet_entries (meal, food_id, quantity, sort_order) VALUES (?, ?, ?, ?)",
            (meal, food_id, float(quantity), sort_order),
        )
        conn.commit()
        return cur.lastrowid


def list_diet_entries():
    """Return diet entries with per-entry computed nutrients."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT e.id, e.meal, f.name, e.quantity, f.unit, f.serving_g,
                   {_NUTRIENT_SELECT}
            FROM diet_entries e
            JOIN foods f ON f.id = e.food_id
            ORDER BY e.sort_order ASC
            """,
        ).fetchall()
        return [dict(r) for r in rows]


def get_diet_totals():
    """Return summed nutrients across all diet_entries + current targets."""
    init_db()
    with _connect() as conn:
        sums = conn.execute(
            """
            SELECT {}
            FROM diet_entries e
            JOIN foods f ON f.id = e.food_id
            """.format(", ".join(
                f"SUM(e.quantity * f.{c} / CASE WHEN f.unit = 'g' THEN f.serving_g ELSE 1.0 END) AS {c}"
                for c in _NUTRIENT_COLS
            )),
        ).fetchone()
        targets_row = conn.execute("SELECT * FROM diet_targets LIMIT 1").fetchone()
        return {
            "totals": dict(sums),
            "targets": dict(targets_row) if targets_row else None,
        }
