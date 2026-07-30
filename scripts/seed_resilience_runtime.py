"""Seed internal shock definitions."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.resilience.service import seed_resilience_runtime  # noqa: E402


def main():
    with get_connection() as conn:
        result = seed_resilience_runtime(conn)
        conn.commit()
    print(
        "Resilience runtime ready: "
        f"definitions={result['definitions']} (+{result['created']})."
    )


if __name__ == "__main__":
    main()

