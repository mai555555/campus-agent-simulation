"""Seed the external event catalog, controlled sources, and impact rules."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.external_world.service import seed_external_world  # noqa: E402


def main():
    with get_connection() as conn:
        result = seed_external_world(conn)
        conn.commit()
    print(
        "External world ready: "
        f"catalog={result['catalog']} (+{result['catalog_created']}), "
        f"sources={result['sources']} (+{result['sources_created']}), "
        f"impact_rules={result['impact_rules']} (+{result['impact_rules_created']})."
    )


if __name__ == "__main__":
    main()
