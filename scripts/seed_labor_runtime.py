"""Seed labor positions, contracts, income programs, and required expenses."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.labor.service import seed_labor_runtime  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_labor_runtime(conn)
        conn.commit()
    print(
        "Labor runtime ready: "
        f"positions={result['labor_positions']}, "
        f"contracts={result['employment_contracts']} "
        f"(+{result['contracts_created']}), "
        f"income_programs={result['income_programs']}, "
        f"expense_obligations={result['expense_obligations']}."
    )


if __name__ == "__main__":
    main()
