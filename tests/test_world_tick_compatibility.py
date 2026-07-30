import json
import sqlite3
import unittest
from datetime import datetime, timezone

import app.main as main
from app.models import SCHEMA_SQL


class WorldTickCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA_SQL)
        self.conn.execute(
            "INSERT INTO simulation_state (key, value) VALUES ('current_day', '26')"
        )
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False
        main.ensure_world_runtime_tables(self.conn, allow_ddl=True)

    def tearDown(self):
        self.conn.close()
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False

    def test_world_event_payload_serializes_postgres_datetime_values(self):
        observed_at = datetime(2026, 7, 30, 9, 38, tzinfo=timezone.utc)
        event = main.append_world_event(
            self.conn,
            "runtime_test",
            "运行时兼容测试",
            "PostgreSQL 时间字段可以写入事件 payload。",
            payload={"nested": {"observed_at": observed_at}},
        )
        stored = self.conn.execute(
            "SELECT payload FROM world_event_stream WHERE id = ?", (event["id"],)
        ).fetchone()
        payload = json.loads(stored["payload"])
        self.assertEqual(payload["nested"]["observed_at"], observed_at.isoformat())

    def test_action_resource_state_defaults_legacy_null_values(self):
        class LegacyConnection:
            def execute(self, *_args, **_kwargs):
                return self

            def fetchone(self):
                return {
                    "energy": None,
                    "time_budget": None,
                    "money": None,
                    "mood": None,
                }

        state = main.action_resource_state(LegacyConnection(), 1)
        self.assertEqual(state["energy"], 80)
        self.assertEqual(state["time_budget"], 100)
        self.assertEqual(state["money"], 0)
        self.assertEqual(state["mood"], "平稳")


if __name__ == "__main__":
    unittest.main()
