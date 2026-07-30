"""Add evidence-based informal norm emergence.

Revision ID: 20260730_0021
Revises: 20260730_0020
"""

import re

from alembic import op
import sqlalchemy as sa

from app.adaptation.schema import NORM_RUNTIME_SQL


revision = "20260730_0021"
down_revision = "20260730_0020"
branch_labels = None
depends_on = None


def upgrade():
    sql = NORM_RUNTIME_SQL
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
        "norm_responses",
        "norm_state_transitions",
        "agent_norm_beliefs",
        "norm_evidence",
        "norm_candidates",
        "norm_signals",
    ):
        op.drop_table(table_name)

