"""Seed organization governance profiles, roles, and memberships."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.organizations.service import seed_organization_runtime  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_organization_runtime(conn)
        conn.commit()
    print(
        "Organization runtime ready: "
        f"profiles={result['organization_runtime_profiles']}, "
        f"roles={result['organization_roles']}, "
        f"assignments={result['organization_role_assignments']} "
        f"(+{result['assignments_created']}), "
        f"relationships={result['organization_relationships']}."
    )


if __name__ == "__main__":
    main()

