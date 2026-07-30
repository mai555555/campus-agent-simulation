"""Add reproducible internal shocks, exposure, and recovery.

Revision ID: 20260730_0023
Revises: 20260730_0022
"""

import re

from alembic import op
import sqlalchemy as sa

from app.resilience.schema import RESILIENCE_RUNTIME_SQL


revision = "20260730_0023"
down_revision = "20260730_0022"
branch_labels = None
depends_on = None


def upgrade():
    sql = RESILIENCE_RUNTIME_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(
            r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
            "SERIAL PRIMARY KEY",
            sql,
            flags=re.IGNORECASE,
        )
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            op.execute(sa.text(statement))


def downgrade():
    for table_name in (
        "shock_state_transitions",
        "recovery_actions",
        "resident_shock_exposures",
        "shock_impacts",
        "shock_instances",
        "shock_definitions",
    ):
        op.drop_table(table_name)

