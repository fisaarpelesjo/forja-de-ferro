"""Operacoes SQLite para os dados da Forja de Ferro."""

import sqlite3
from itertools import groupby
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "forja_de_ferro.db"

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


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                sort_order INTEGER NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                training_type TEXT NOT NULL DEFAULT 'TREINO'
            )
            """
        )
        conn.execute(
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
            """
        )
        conn.execute(
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
            """
        )
        conn.execute(
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
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS diet_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal TEXT NOT NULL,
                food_id INTEGER NOT NULL REFERENCES foods(id),
                quantity REAL NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


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
