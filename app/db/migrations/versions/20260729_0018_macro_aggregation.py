"""Add traceable macro aggregation and reconciliation.

Revision ID: 20260729_0018
Revises: 20260729_0017
"""

from alembic import op

from app.macro.schema import MACRO_RUNTIME_SQL


revision = "20260729_0018"
down_revision = "20260729_0017"
branch_labels = None
depends_on = None


def _statements(sql):
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def upgrade():
    connection = op.get_bind()
    sql = MACRO_RUNTIME_SQL
    if connection.dialect.name == "postgresql":
        sql = sql.replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY"
        )
    for statement in _statements(sql):
        op.execute(statement)


def downgrade():
    for table in (
        "macro_reconciliation_checks",
        "macro_metric_components",
        "macro_metric_values",
        "macro_snapshots",
        "macro_metric_definitions",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
