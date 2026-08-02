"""Bring the pre-Alembic schema to the complete migration baseline."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection, using_postgres  # noqa: E402
from app.main import (  # noqa: E402
    ensure_agent_news_system,
    ensure_campus_state_table,
    ensure_external_information_system,
    ensure_space_system,
    ensure_world_runtime_tables,
)
from app.models import SCHEMA_SQL  # noqa: E402


LEGACY_UPSERT_INDEXES = {
    "resident_power_profiles": ("resident_id",),
    "agent_norm_beliefs": ("resident_id", "norm_id"),
}


def _table_exists(conn, table_name: str) -> bool:
    if using_postgres():
        row = conn.execute("SELECT to_regclass(?) AS table_name", (f"public.{table_name}",)).fetchone()
        return bool(row and row["table_name"])
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def ensure_legacy_upsert_indexes(conn) -> None:
    for table_name, columns in LEGACY_UPSERT_INDEXES.items():
        if not _table_exists(conn, table_name):
            continue
        index_name = f"uq_{table_name}_{'_'.join(columns)}"
        conn.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name} ({', '.join(columns)})"
        )


def prepare_legacy_schema() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        ensure_campus_state_table(conn, allow_ddl=True)
        ensure_space_system(conn, allow_ddl=True)
        ensure_agent_news_system(conn, allow_ddl=True)
        ensure_external_information_system(conn, allow_ddl=True)
        ensure_world_runtime_tables(conn, allow_ddl=True)
        ensure_legacy_upsert_indexes(conn)
        conn.commit()


def main() -> None:
    prepare_legacy_schema()
    print("Legacy campus schema is ready for the Alembic baseline.")


if __name__ == "__main__":
    main()
