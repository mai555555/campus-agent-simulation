import sqlite3
import unittest
from unittest.mock import Mock, patch

import app.main as main
from app.models import SCHEMA_SQL


class RuntimeSchemaSafetyTest(unittest.TestCase):
    def setUp(self):
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False
        main.WORLD_RUNNER_THREAD = None

    def tearDown(self):
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False
        main.WORLD_RUNNER_THREAD = None

    def _prepared_connection(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO simulation_state (key, value) VALUES ('current_day', '1')"
        )
        main.ensure_campus_state_table(conn, allow_ddl=True)
        main.ensure_space_system(conn, allow_ddl=True)
        main.ensure_agent_news_system(conn, allow_ddl=True)
        main.ensure_external_information_system(conn, allow_ddl=True)
        main.ensure_world_runtime_tables(conn, allow_ddl=True)
        conn.commit()
        main.SOCIAL_SCHEMA_READY = False
        main.WORLD_SCHEMA_READY = False
        return conn

    def test_runtime_schema_check_never_executes_ddl(self):
        conn = self._prepared_connection()
        statements = []
        conn.set_trace_callback(statements.append)

        main.ensure_campus_state_table(conn)
        main.ensure_space_system(conn)
        main.ensure_agent_news_system(conn)
        main.ensure_external_information_system(conn)
        main.ensure_world_runtime_tables(conn)

        ddl = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith(("ALTER ", "CREATE ", "DROP "))
        ]
        self.assertEqual(ddl, [])
        conn.close()

    def test_runtime_requires_build_migration_instead_of_creating_tables(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        statements = []
        conn.set_trace_callback(statements.append)

        with self.assertRaises(main.SchemaMigrationRequired):
            main.ensure_world_runtime_tables(conn)

        ddl = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith(("ALTER ", "CREATE ", "DROP "))
        ]
        self.assertEqual(ddl, [])
        conn.close()

    def test_startup_only_starts_runner_thread(self):
        runner = Mock()
        runner.is_alive.return_value = False

        with (
            patch.object(main, "Thread", return_value=runner) as thread_factory,
            patch.object(
                main,
                "get_connection",
                side_effect=AssertionError("startup must not access the database"),
            ),
        ):
            main.start_world_runner_thread()

        thread_factory.assert_called_once_with(
            target=main.world_runner_loop,
            daemon=True,
        )
        runner.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
