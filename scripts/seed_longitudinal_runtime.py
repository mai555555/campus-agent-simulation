"""Seed longitudinal profiles and initial life-course stages."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.longitudinal.service import seed_longitudinal_runtime  # noqa: E402


def main():
    with get_connection() as conn:
        result = seed_longitudinal_runtime(conn)
        conn.commit()
    print(
        "Longitudinal runtime ready: "
        f"profiles={result['profiles']} (+{result['created']}), "
        f"stages=+{result['stages_created']}."
    )


if __name__ == "__main__":
    main()
