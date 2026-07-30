"""Add evidence-linked memory and adaptive strategy learning.

Revision ID: 20260730_0020
Revises: 20260730_0019
"""

import re

from alembic import op
import sqlalchemy as sa

from app.adaptation.schema import LEARNING_RUNTIME_SQL


revision = "20260730_0020"
down_revision = "20260730_0019"
branch_labels = None
depends_on = None


def upgrade():
    sql = LEARNING_RUNTIME_SQL
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
        "learning_updates",
        "strategy_states",
        "memory_revisions",
        "adaptive_memories",
        "experience_records",
    ):
        op.drop_table(table_name)

