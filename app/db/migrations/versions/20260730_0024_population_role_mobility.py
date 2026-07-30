"""Add population, role, residency, and membership evolution.

Revision ID: 20260730_0024
Revises: 20260730_0023
"""

import re

from alembic import op
import sqlalchemy as sa

from app.population.schema import POPULATION_RUNTIME_SQL


revision = "20260730_0024"
down_revision = "20260730_0023"
branch_labels = None
depends_on = None


def upgrade():
    sql = POPULATION_RUNTIME_SQL
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
        "population_effects",
        "membership_transitions",
        "resident_residency_periods",
        "resident_role_assignments",
        "population_events",
        "population_profiles",
    ):
        op.drop_table(table_name)
