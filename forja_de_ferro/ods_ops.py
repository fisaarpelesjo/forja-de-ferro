"""Operacoes de treino da Forja de Ferro."""

import json
from datetime import date
from pathlib import Path

from . import db_ops

SESSION_FILE = Path(__file__).resolve().parents[1] / "session.json"

TRAINING_EXERCISES = range(0, 11)
TREINO_EXERCISES = TRAINING_EXERCISES
RPE_PROGRESSION_KG = {
    7: 4.0,
    8: 2.0,
    9: 0.0,
    10: -2.0,
}

INITIAL_TARGET_WEIGHTS = {
    "Rosca martelo (barra H)": 16.0,
}

REST_INTERVALS = {
    "Agachamento Zercher": "4 min",
    "Supino reto (barra)": "4 min",
    "Supino reto back-off": "2 min",
    "Remada curvada (barra)": "3 min",
    "Desenvolvimento (barra em pé)": "3 min",
    "Desenvolvimento (barra em pe)": "3 min",
    "Levantamento Terra Romeno": "4 min",
    "Pullover (barra)": "2 min",
    "Remada alta (barra)": "2 min",
    "Remada curvada alta no peito (barra)": "2 min",
    "Rosca direta": "2 min",
    "Rosca martelo (barra H)": "2 min",
    "Tríceps testa": "2 min",
    "Triceps testa": "2 min",
}

LOAD_EQUIPMENT = {
    "Pullover (barra)": {"name": "barra W", "weight": 6.0},
    "Rosca martelo (barra H)": {"name": "barra H", "weight": 9.0},
    "Tríceps testa": {"name": "barra W", "weight": 6.0},
    "Triceps testa": {"name": "barra W", "weight": 6.0},
}

def read_exercises():
    return db_ops.get_or_seed_exercises()


def read_previous_weights():
    return db_ops.get_last_weights()


def read_previous_performance():
    return db_ops.get_last_performance()


def read_muscle_groups():
    return db_ops.list_muscle_groups()


def suggest_next_weight(previous_weight, previous_rpe=None):
    if previous_weight is None:
        return None
    if previous_rpe is None:
        return float(previous_weight)

    rpe = int(previous_rpe)
    if rpe <= 7:
        delta = RPE_PROGRESSION_KG[7]
    elif rpe >= 10:
        delta = RPE_PROGRESSION_KG[10]
    else:
        delta = RPE_PROGRESSION_KG.get(rpe, 0.0)
    return float(previous_weight) + delta


def get_initial_target_weight(exercise_name):
    return INITIAL_TARGET_WEIGHTS.get(exercise_name)


def get_rest_interval(exercise_name):
    return REST_INTERVALS.get(exercise_name, "2 min")


def format_weight(weight):
    return str(int(weight) if weight == int(weight) else weight)


def format_loading_note(exercise_name, target_weight):
    equipment = LOAD_EQUIPMENT.get(exercise_name)
    if not equipment or target_weight is None:
        return None

    bar_weight = equipment["weight"]
    plates_weight = max(float(target_weight) - bar_weight, 0.0)
    return (
        f"{equipment['name']} {format_weight(bar_weight)}kg"
        f" + {format_weight(plates_weight)}kg de anilhas"
    )


def build_training_plan(persist=True):
    """
    Monta o treino atual com carga alvo e descanso.
    Se persist=True, cria sessao e logs no SQLite.
    """
    all_ex = read_exercises()
    exercises = [all_ex[i] for i in TRAINING_EXERCISES if i < len(all_ex)]
    previous_performance = read_previous_performance()

    session_id = None
    if persist:
        today = date.today().strftime("%Y-%m-%d")
        session_id = db_ops.create_session(today)

    session_exercises = []
    for idx, ex in enumerate(exercises):
        log_id = None
        if persist:
            log_id = db_ops.log_exercise(session_id, ex["name"], ex["sets"], ex["reps"], idx)
        previous = previous_performance.get(ex["name"], {})
        target_weight = suggest_next_weight(previous.get("weight"), previous.get("rpe"))
        if target_weight is None:
            target_weight = get_initial_target_weight(ex["name"])
        item = {
            "name": ex["name"],
            "sets": ex["sets"],
            "reps": ex["reps"],
            "target_weight": target_weight,
            "rest_interval": get_rest_interval(ex["name"]),
        }
        loading_note = format_loading_note(ex["name"], target_weight)
        if loading_note:
            item["loading_note"] = loading_note
        if log_id is not None:
            item["log_id"] = log_id
        session_exercises.append(item)

    return session_exercises, session_id


def generate_training():
    """
    Cria uma sessao de treino no SQLite.
    Retorna (exercises, session_id), onde exercises e uma lista de
    {log_id, name, sets, reps}.
    """
    return build_training_plan(persist=True)


def preview_training():
    return build_training_plan(persist=False)[0]


def gerar_treino():
    return generate_training()


def write_session(exercises, session_id=None):
    data = {
        "date": date.today().strftime("%Y-%m-%d"),
        "exercises": exercises,
    }
    if session_id is not None:
        data["session_id"] = session_id
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def recover_active_session():
    """Reconstrui o cache da sessao ativa a partir do SQLite."""
    stored = db_ops.get_latest_incomplete_session()
    if stored is None:
        return None

    exercises = []
    for row in stored["exercises"]:
        target_weight = suggest_next_weight(
            row["previous_weight"],
            row["previous_rpe"],
        )
        if target_weight is None:
            target_weight = get_initial_target_weight(row["name"])
        item = {
            "log_id": row["log_id"],
            "name": row["name"],
            "sets": row["sets"],
            "reps": row["reps"],
            "target_weight": target_weight,
            "rest_interval": get_rest_interval(row["name"]),
        }
        loading_note = format_loading_note(row["name"], target_weight)
        if loading_note:
            item["loading_note"] = loading_note
        exercises.append(item)

    data = {
        "date": stored["date"],
        "session_id": stored["session_id"],
        "exercises": exercises,
    }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data
