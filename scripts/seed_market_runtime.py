"""Seed market mechanisms from real catalog, inventory, and service supply."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.market.service import seed_market_runtime  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_market_runtime(conn)
        conn.commit()
    print(
        "Market runtime ready: "
        f"mechanisms={result['mechanisms']} "
        f"(+{result['mechanisms_created']})."
    )


if __name__ == "__main__":
    main()
