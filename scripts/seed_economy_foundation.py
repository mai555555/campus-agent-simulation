"""Seed economic actors, accounts, and traceable opening balances."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.economy.service import seed_economy_foundation  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_economy_foundation(conn)
        conn.commit()
    print(
        "Economy ledger ready: "
        f"actors={result['actors_total']}, "
        f"accounts={result['accounts_total']}, "
        f"transactions={result['transactions_total']} "
        f"(+{result['opening_transactions_created']} opening), "
        f"authorization_rules={result['authorization_rules']}, "
        f"balanced={str(result['balanced']).lower()}."
    )


if __name__ == "__main__":
    main()
