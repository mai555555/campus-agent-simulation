"""Add softened constraints and traceable boundary attempts.

Revision ID: 20260730_0019
Revises: 20260729_0018
"""

import re

from alembic import op
import sqlalchemy as sa

from app.adaptation.schema import CONSTRAINT_RUNTIME_SQL


revision = "20260730_0019"
down_revision = "20260729_0018"
branch_labels = None
depends_on = None


def upgrade():
    sql = CONSTRAINT_RUNTIME_SQL
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
        "constraint_consequences",
        "boundary_attempts",
        "constraint_evaluations",
        "constraint_rules",
    ):
        op.drop_table(table_name)

