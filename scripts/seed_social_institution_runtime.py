"""Seed communication channels, institutional rules, and power profiles."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection  # noqa: E402
from app.social_institutions.service import seed_social_institution_runtime  # noqa: E402


def main() -> None:
    with get_connection() as conn:
        result = seed_social_institution_runtime(conn)
        conn.commit()
    print(
        "Social institution runtime ready: "
        f"channels={result['channels']} (+{result['channels_created']}), "
        f"rules={result['rules']} (+{result['rules_created']}), "
        f"power_profiles={result['power_profiles']}."
    )


if __name__ == "__main__":
    main()
