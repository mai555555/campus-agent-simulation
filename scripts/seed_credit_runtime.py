"""Seed funded household credit, savings goals, and risk profiles."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.credit.service import seed_credit_runtime  # noqa: E402
from app.db import get_connection  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_credit_runtime(conn)
        conn.commit()
    print(
        "Credit runtime ready: "
        f"profiles={result['profiles']} "
        f"(+{result['profiles_created']}), "
        f"risk_profiles=+{result['risk_profiles_created']}, "
        f"savings_goals=+{result['savings_goals_created']}, "
        f"funded_reserve_minor={result['credit_union_cash_minor']}."
    )


if __name__ == "__main__":
    main()
