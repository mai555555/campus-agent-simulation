"""Seed metric definitions and create the current macro snapshot."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.macro.service import build_macro_snapshot, seed_macro_runtime  # noqa: E402


def main():
    with get_connection() as conn:
        seeded = seed_macro_runtime(conn)
        snapshot = build_macro_snapshot(conn)
        conn.commit()
    print(
        "Macro runtime ready: "
        f"definitions={seeded['definitions']} (+{seeded['created']}), "
        f"snapshot={snapshot.get('snapshot_id')}, "
        f"status={snapshot.get('status')}."
    )


if __name__ == "__main__":
    main()
