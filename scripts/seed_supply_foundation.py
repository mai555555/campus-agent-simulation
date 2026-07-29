"""Seed products, inventory accounts, recipes, and service offerings."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.supply.service import seed_supply_foundation  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_supply_foundation(conn)
        conn.commit()
    print(
        "Supply foundation ready: "
        f"catalog={result['catalog_items']}, "
        f"inventory_accounts={result['inventory_accounts']}, "
        f"recipes={result['production_recipes']}, "
        f"services={result['service_offerings']}, "
        f"opening_movements=+{result['opening_movements_created']}."
    )


if __name__ == "__main__":
    main()

