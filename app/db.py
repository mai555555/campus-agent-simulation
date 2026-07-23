from pathlib import Path
import sqlite3
import os
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "city.db")))

POSTGRES_ID_TABLES = {
    "agent_information", "agent_learning", "agent_news_posts", "campus_events",
    "city_events", "collaborations", "competitions", "external_information",
    "group_goals", "inventory", "long_term_goals", "memories", "policies",
    "residents", "simulation_action_logs", "transactions",
}


def using_postgres() -> bool:
    return bool(os.getenv("DATABASE_URL"))


def _postgres_sql(sql: str) -> str:
    """Translate the SQLite syntax used by this project to PostgreSQL."""
    statement = sql.strip()
    pragma = re.fullmatch(r"PRAGMA table_info\((\w+)\)", statement, re.IGNORECASE)
    if pragma:
        return (
            "SELECT column_name AS name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s "
            "ORDER BY ordinal_position"
        )

    statement = re.sub(
        r"INSERT\s+OR\s+REPLACE\s+INTO\s+simulation_state",
        "INSERT INTO simulation_state",
        statement,
        flags=re.IGNORECASE,
    )
    if statement.upper().startswith("INSERT INTO SIMULATION_STATE"):
        statement = re.sub(
            r"\)\s*VALUES\s*\((.*?)\)$",
            r") VALUES (\1) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            statement,
            flags=re.IGNORECASE | re.DOTALL,
        )
    elif "INSERT OR IGNORE" in sql.upper():
        statement = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", statement, flags=re.IGNORECASE)
        if "ON CONFLICT" not in statement.upper():
            statement = f"{statement.rstrip(';')} ON CONFLICT DO NOTHING"

    # PostgreSQL requires the target table on the left side of this upsert.
    statement = re.sub(
        r"SET\s+quantity\s*=\s*quantity\s*\+\s*excluded\.quantity",
        "SET quantity = inventory.quantity + excluded.quantity",
        statement,
        flags=re.IGNORECASE,
    )
    return statement.replace("?", "%s")


def _postgres_script(sql: str) -> list[str]:
    normalized = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    return [statement.strip() for statement in normalized.split(";") if statement.strip()]


class PostgresCursor:
    def __init__(self, cursor, lastrowid=None, rowcount=0):
        self._cursor = cursor
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()

    def execute(self, sql: str, params=()):
        statement = _postgres_sql(sql)
        pragma = re.fullmatch(r"PRAGMA table_info\((\w+)\)", sql.strip(), re.IGNORECASE)
        execute_params = (pragma.group(1),) if pragma else params
        table_match = re.search(r"INSERT\s+(?:OR\s+IGNORE\s+)?INTO\s+(\w+)", sql, re.IGNORECASE)
        table = table_match.group(1).lower() if table_match else ""
        needs_id = table in POSTGRES_ID_TABLES and "RETURNING" not in statement.upper()
        if needs_id:
            statement = f"{statement.rstrip(';')} RETURNING id"

        cursor = self._connection.execute(statement, execute_params)
        rowcount = cursor.rowcount
        inserted_row = cursor.fetchone() if needs_id and rowcount else None
        lastrowid = inserted_row["id"] if inserted_row else None
        return PostgresCursor(cursor, lastrowid, rowcount)

    def executescript(self, sql: str):
        for statement in _postgres_script(sql):
            self._connection.execute(statement)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def get_connection():
    if using_postgres():
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL support requires psycopg[binary].") from exc
        return PostgresConnection(psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row))

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute_script(sql: str) -> None:
    with get_connection() as conn:
        conn.executescript(sql)
        conn.commit()
