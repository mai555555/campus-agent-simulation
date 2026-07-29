"""Add traceable social diffusion, institutions, and power.

Revision ID: 20260729_0017
Revises: 20260729_0016
"""

import re

from alembic import op
import sqlalchemy as sa

from app.social_institutions.schema import SOCIAL_INSTITUTION_RUNTIME_SQL


revision = "20260729_0017"
down_revision = "20260729_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = SOCIAL_INSTITUTION_RUNTIME_SQL
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


def downgrade() -> None:
    for table_name in (
        "institutional_trust_events",
        "resident_power_profiles",
        "institutional_decisions",
        "institutional_cases",
        "institutional_rules",
        "information_beliefs",
        "information_exposures",
        "information_transmissions",
        "information_versions",
        "information_claims",
        "communication_channels",
    ):
        op.drop_table(table_name)

