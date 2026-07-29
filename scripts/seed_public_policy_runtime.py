"""Seed public services, externalities, and policy instruments."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.public_policy.service import seed_public_policy_runtime  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_public_policy_runtime(conn)
        conn.commit()
    print(
        "Public policy runtime ready: "
        f"services={result['services']} (+{result['services_created']}), "
        f"policies={result['policies']} (+{result['policies_created']}), "
        f"fund_cash_minor={result['public_fund_cash_minor']}."
    )


if __name__ == "__main__":
    main()
