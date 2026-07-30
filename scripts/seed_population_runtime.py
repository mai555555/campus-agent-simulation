"""Seed lifecycle profiles for existing campus residents."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.population.service import seed_population_runtime  # noqa: E402


def main():
    with get_connection() as conn:
        result = seed_population_runtime(conn)
        conn.commit()
    print(
        "Population runtime ready: "
        f"profiles={result['profiles']} (+{result['created']}), "
        f"roles=+{result['roles_created']}, "
        f"residencies=+{result['residencies_created']}."
    )


if __name__ == "__main__":
    main()
