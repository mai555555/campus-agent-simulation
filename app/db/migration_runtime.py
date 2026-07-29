from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.engine import (
    PROJECT_ROOT,
    create_database_engine,
    get_database_schema,
    get_database_url,
)


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
    config.attributes["database_schema"] = get_database_schema()
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
    schema = get_database_schema() if engine.dialect.name == "postgresql" else None
    return sorted(
        name
        for name in inspect(engine).get_table_names(schema=schema)
        if name != "alembic_version"
    )


def create_migration_engine(database_url: str | None = None) -> Engine:
    return create_database_engine(database_url)


def describe_database_target(engine: Engine) -> dict:
    with engine.connect() as connection:
        if engine.dialect.name == "postgresql":
            row = connection.execute(
                text(
                    "SELECT current_database() AS database_name, "
                    "current_schema() AS schema_name"
                )
            ).mappings().one()
            return {
                "dialect": "postgresql",
                "database": row["database_name"],
                "schema": row["schema_name"],
            }
        return {
            "dialect": engine.dialect.name,
            "database": str(engine.url.database or ""),
            "schema": "",
        }
