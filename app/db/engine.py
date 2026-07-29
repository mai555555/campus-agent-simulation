from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "city.db"


def get_database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        if configured.startswith("postgres://"):
            configured = "postgresql://" + configured.removeprefix("postgres://")
        if configured.startswith("postgresql://"):
            return "postgresql+psycopg://" + configured.removeprefix("postgresql://")
        return configured

    db_path = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    return f"sqlite+pysqlite:///{db_path.resolve()}"


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    else:
        options.update({"pool_size": 5, "max_overflow": 5})

    engine = create_engine(url, **options)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()
