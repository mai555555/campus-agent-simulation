"""Bring the pre-Alembic schema to the complete migration baseline."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.main import (  # noqa: E402
    ensure_agent_news_system,
    ensure_campus_state_table,
    ensure_external_information_system,
    ensure_space_system,
    ensure_world_runtime_tables,
)
from app.models import SCHEMA_SQL  # noqa: E402


def prepare_legacy_schema() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        ensure_campus_state_table(conn)
        ensure_space_system(conn)
        ensure_agent_news_system(conn)
        ensure_external_information_system(conn)
        ensure_world_runtime_tables(conn)
        conn.commit()


def main() -> None:
    prepare_legacy_schema()
    print("Legacy campus schema is ready for the Alembic baseline.")


if __name__ == "__main__":
    main()
