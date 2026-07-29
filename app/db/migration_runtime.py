from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.db.engine import PROJECT_ROOT, create_database_engine, get_database_url


BASELINE_REVISION = "20260729_0001"
BASELINE_REQUIRED_TABLES = {
    "residents",
    "campus_state",
    "campus_spaces",
    "world_runtime",
    "world_event_stream",
    "world_snapshots",
    "experiment_runs",
    "world_branches",
}


def get_alembic_config(database_url: str | None = None) -> Config:
    config_path = PROJECT_ROOT / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option(
        "script_location", str(PROJECT_ROOT / "app" / "db" / "migrations")
    )
    resolved_url = database_url or get_database_url()
    config.set_main_option("sqlalchemy.url", resolved_url.replace("%", "%%"))
    config.attributes["database_url"] = resolved_url
    return config


def get_current_revision(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def get_head_revision(config: Config | None = None) -> str:
    heads = ScriptDirectory.from_config(config or get_alembic_config()).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"Expected one migration head, found: {heads}")
    return heads[0]


def list_business_tables(engine: Engine) -> list[str]:
    return sorted(
        name for name in inspect(engine).get_table_names() if name != "alembic_version"
    )


def create_migration_engine(database_url: str | None = None) -> Engine:
    return create_database_engine(database_url)
