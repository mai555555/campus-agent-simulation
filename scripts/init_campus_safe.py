"""Initialize a new campus once without resetting an existing world."""

from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_connection
from app.models import SCHEMA_SQL


def main():
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        marker = conn.execute(
            "SELECT value FROM simulation_state WHERE key = ?",
            ("campus_initialized",),
        ).fetchone()
        has_residents = conn.execute("SELECT 1 FROM residents LIMIT 1").fetchone()
        if (marker and marker["value"] == "1") or has_residents:
            if not marker:
                conn.execute(
                    "INSERT OR REPLACE INTO simulation_state (key, value) VALUES (?, ?)",
                    ("campus_initialized", "1"),
                )
                conn.commit()
            print("Campus data already initialized; skipping seed data.")
            return

    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / "init_campus.py")], check=True)

    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO simulation_state (key, value) VALUES (?, ?)",
            ("campus_initialized", "1"),
        )
        conn.commit()
    print("Campus seed data initialized and marked persistent.")


if __name__ == "__main__":
    main()
