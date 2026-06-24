"""Backup, exportacao e restauracao dos dados da Forja de Ferro."""

import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime
from pathlib import Path

from . import db_ops

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BACKUP_DIR = ROOT_DIR / "backups"
DEFAULT_EXPORT_DIR = ROOT_DIR / "exportacoes"

EXPORT_TABLES = (
    "exercises",
    "exercise_muscle_groups",
    "training_plans",
    "training_plan_exercises",
    "training_sessions",
    "training_logs",
    "foods",
    "diet_targets",
    "diet_entries",
    "body_weights",
    "waist_measurements",
    "schema_migrations",
)


def _timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _database_path(database_path=None):
    return Path(database_path) if database_path else Path(db_ops.DB_PATH)


def validar_banco(database_path):
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(f"Banco nao encontrado: {path}")

    with closing(sqlite3.connect(path)) as conn:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Falha na integridade do banco: {result}")
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    required = {"training_sessions", "training_logs", "exercises"}
    missing = required - tables
    if missing:
        raise RuntimeError(
            "Banco incompativel; tabelas ausentes: " + ", ".join(sorted(missing))
        )
    return True


def criar_backup(destination_dir=None, database_path=None):
    source_path = _database_path(database_path)
    validar_banco(source_path)
    destination = Path(destination_dir or DEFAULT_BACKUP_DIR)
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f"forja-de-ferro-{_timestamp()}.db"

    with closing(sqlite3.connect(source_path)) as source:
        with closing(sqlite3.connect(output)) as target:
            source.backup(target)
    validar_banco(output)
    return output


def exportar_dados(destination_dir=None, database_path=None):
    source_path = _database_path(database_path)
    validar_banco(source_path)
    destination = Path(destination_dir or DEFAULT_EXPORT_DIR)
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f"forja-de-ferro-{_timestamp()}.json"

    with closing(sqlite3.connect(source_path)) as conn:
        conn.row_factory = sqlite3.Row
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        data = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "schema_version": (
                conn.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
                ).fetchone()[0]
                if "schema_migrations" in tables
                else 0
            ),
            "tables": {},
        }
        for table in EXPORT_TABLES:
            if table in tables:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                data["tables"][table] = [dict(row) for row in rows]

    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output


def restaurar_backup(
    backup_path,
    database_path=None,
    safety_backup_dir=None,
    create_safety_backup=True,
):
    source_path = Path(backup_path)
    target_path = _database_path(database_path)
    validar_banco(source_path)

    safety_backup = None
    if target_path.exists() and create_safety_backup:
        safety_backup = criar_backup(
            safety_backup_dir or DEFAULT_BACKUP_DIR,
            target_path,
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f"{target_path.stem}-restauracao-",
        suffix=".db",
        dir=target_path.parent,
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        with closing(sqlite3.connect(source_path)) as source:
            with closing(sqlite3.connect(temporary_path)) as target:
                source.backup(target)
        validar_banco(temporary_path)
        os.replace(temporary_path, target_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return target_path, safety_backup
