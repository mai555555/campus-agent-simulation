"""Seed household budget profiles and non-credit savings accounts."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.budget.service import seed_budget_runtime  # noqa: E402
from app.db import get_connection  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_budget_runtime(conn)
        conn.commit()
    print(
        "Budget runtime ready: "
        f"profiles={result['profiles']} "
        f"(+{result['profiles_created']}), credit_enabled=false."
    )


if __name__ == "__main__":
    main()
