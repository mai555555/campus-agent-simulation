"""Reconcile the economy ledger and persist a deduplicated anomaly if needed."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.economy.service import audit_ledger  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = audit_ledger(conn, source_type="operations_script")
        conn.commit()
    print(
        "Economy ledger audit: "
        f"actors={result['actor_count']}, "
        f"accounts={result['account_count']}, "
        f"transactions={result['transaction_count']}, "
        f"entries={result['entry_count']}, "
        f"balanced={str(result['balanced']).lower()}."
    )
    if not result["balanced"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
