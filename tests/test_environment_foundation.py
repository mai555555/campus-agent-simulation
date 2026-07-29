import json
import sqlite3
import unittest

import app.main as main
from app.models import SCHEMA_SQL


class EnvironmentFoundationTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.execute("INSERT INTO simulation_state (key, value) VALUES ('current_day', '1')")
        self.conn.execute(
            """
            INSERT INTO residents
            (id, name, role, personality, goal, money, location)
            VALUES (1, '环境测试学生', '学生', '认真', '完成环境实验', 100, '宿舍区')
            """
        )
        self.conn.execute(
            """
            INSERT INTO agent_profiles
            (resident_id, gender, avatar_style, energy, mood, current_task,
             skills, strategy, schedule, perception)
            VALUES (1, '女', '测试', 80, '平稳', '观察环境', '{}', '{}', '[]', '{}')
            """
        )
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False
        main.ensure_campus_state_table(self.conn)
        main.ensure_space_system(self.conn)
        main.ensure_world_runtime_tables(self.conn)

    def tearDown(self):
        self.conn.close()
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False

    def test_default_config_is_versioned_and_bound_to_runtime(self):
        config = main.get_active_environment_config(self.conn)
        runtime = dict(
            self.conn.execute(
                "SELECT * FROM world_runtime WHERE id = ?",
                (main.WORLD_RUNTIME_ID,),
            ).fetchone()
        )

        self.assertEqual(config["config_key"], "campus-default")
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["checksum"], main.content_checksum(config["config"]))
        self.assertEqual(runtime["environment_config_id"], config["id"])
        self.assertEqual(runtime["environment_version"], config["version_label"])
        self.assertTrue(runtime["random_seed"])

    def test_new_config_version_can_be_activated_and_applied(self):
        config = json.loads(json.dumps(main.default_environment_config(), ensure_ascii=False))
        config["spaces"][0]["capacity"] = 321
        config["environment_baseline"]["resource_pressure"] = 72
        created = main.create_environment_config_record(
            self.conn,
            "campus-default",
            "资源紧张校园",
            config,
            parent_config_id=main.get_active_environment_config(self.conn)["id"],
        )
        row = self.conn.execute(
            "SELECT * FROM environment_configs WHERE id = ?",
            (created["id"],),
        ).fetchone()

        applied = main.apply_environment_config(self.conn, dict(row))
        active = main.get_active_environment_config(self.conn)
        dorm = self.conn.execute(
            "SELECT capacity FROM campus_spaces WHERE code = 'dorm'"
        ).fetchone()
        environment = main.get_campus_environment(self.conn, 1)

        self.assertEqual(created["version"], 2)
        self.assertEqual(active["id"], created["id"])
        self.assertEqual(dorm["capacity"], 321)
        self.assertEqual(environment["resource_pressure"], 72)
        self.assertEqual(applied["spaces"], len(config["spaces"]))
        self.assertIn("resource_pressure", applied["baseline_fields"])

    def test_world_events_preserve_parent_and_root_lineage(self):
        root = main.append_world_event(
            self.conn,
            "test_root",
            "根事件",
            "环境改变开始",
            source_type="test",
            source_id="root-1",
        )
        child = main.append_world_event(
            self.conn,
            "test_child",
            "子事件",
            "Agent 对环境作出反应",
            parent_event_id=root["id"],
            source_type="agent_action",
            source_id="action-1",
            rule_version="test-rule-v1",
        )
        grandchild = main.append_world_event(
            self.conn,
            "test_grandchild",
            "后续事件",
            "反应产生后续影响",
            parent_event_id=child["id"],
        )

        self.assertEqual(root["root_event_id"], root["id"])
        self.assertEqual(child["parent_event_id"], root["id"])
        self.assertEqual(child["root_event_id"], root["id"])
        self.assertEqual(grandchild["root_event_id"], root["id"])
        self.assertEqual(child["source_type"], "agent_action")
        self.assertEqual(child["rule_version"], "test-rule-v1")

    def test_snapshot_contains_objective_state_and_replay_metadata(self):
        event = main.append_world_event(
            self.conn,
            "snapshot_test",
            "快照前事件",
            "用于确定事件游标",
        )
        snapshot = main.create_world_snapshot_record(
            self.conn,
            reason="阶段 0 测试",
            run_id="run-test-1",
            branch_key="control",
            external_data_version="external-snapshot-1",
            metadata={"experiment": "foundation"},
        )
        stored = self.conn.execute(
            "SELECT * FROM world_snapshots WHERE id = ?",
            (snapshot["id"],),
        ).fetchone()
        decoded = main.decode_world_snapshot(stored, include_state=True)

        self.assertEqual(snapshot["event_cursor"], event["id"])
        self.assertEqual(snapshot["branch_key"], "control")
        self.assertEqual(snapshot["external_data_version"], "external-snapshot-1")
        self.assertTrue(snapshot["environment_version"])
        self.assertTrue(snapshot["random_seed"])
        self.assertEqual(snapshot["checksum"], main.content_checksum(stored["state_json"]))
        self.assertEqual(decoded["metadata"]["experiment"], "foundation")
        self.assertEqual(decoded["state"]["residents"][0]["name"], "环境测试学生")
        self.assertIn("campus_spaces", decoded["state"])


class EnvironmentFoundationMigrationTest(unittest.TestCase):
    def tearDown(self):
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False

    def test_existing_runtime_tables_receive_foundation_columns(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        conn.execute("INSERT INTO simulation_state (key, value) VALUES ('current_day', '1')")
        conn.executescript(
            """
            CREATE TABLE world_runtime (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'paused',
                world_timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
                world_time TEXT NOT NULL DEFAULT '',
                tick_interval_seconds INTEGER NOT NULL DEFAULT 60,
                agents_per_tick INTEGER NOT NULL DEFAULT 3,
                daily_auto_model_budget INTEGER NOT NULL DEFAULT 500,
                auto_model_calls_used INTEGER NOT NULL DEFAULT 0,
                budget_date TEXT NOT NULL DEFAULT '',
                current_agent_cursor INTEGER NOT NULL DEFAULT 0,
                last_tick_started_at TEXT NOT NULL DEFAULT '',
                last_tick_completed_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE world_event_stream (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick_id INTEGER,
                day INTEGER NOT NULL,
                slot TEXT NOT NULL,
                event_type TEXT NOT NULL,
                resident_id INTEGER,
                location TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE world_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL DEFAULT '',
                snapshot_type TEXT NOT NULL DEFAULT 'manual_checkpoint',
                world_time TEXT NOT NULL DEFAULT '',
                day INTEGER NOT NULL DEFAULT 0,
                tick_id INTEGER,
                reason TEXT NOT NULL DEFAULT '',
                state_json TEXT NOT NULL DEFAULT '{}',
                schema_version TEXT NOT NULL DEFAULT 'research-v1',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False

        main.ensure_world_runtime_tables(conn)

        runtime_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(world_runtime)")
        }
        event_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(world_event_stream)")
        }
        snapshot_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(world_snapshots)")
        }
        self.assertIn("environment_config_id", runtime_columns)
        self.assertIn("parent_event_id", event_columns)
        self.assertIn("event_cursor", snapshot_columns)
        self.assertIn("checksum", snapshot_columns)
        conn.close()


if __name__ == "__main__":
    unittest.main()
