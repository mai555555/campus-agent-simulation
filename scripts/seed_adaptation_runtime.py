"""Seed softened constraint rules."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.adaptation.service import seed_constraint_runtime  # noqa: E402
from app.adaptation.institutions import seed_rule_primitives  # noqa: E402
from app.db import get_connection  # noqa: E402


def main():
    with get_connection() as conn:
        result = seed_constraint_runtime(conn)
        primitives = seed_rule_primitives(conn)
        conn.commit()
    print(
        "Adaptation constraint runtime ready: "
        f"rules={result['rules']} (+{result['created']})."
        f" primitives={primitives['primitives']} (+{primitives['created']})."
    )


if __name__ == "__main__":
    main()
