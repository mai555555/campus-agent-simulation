"""Add controlled institutional rule creation and version lineage.

Revision ID: 20260730_0022
Revises: 20260730_0021
"""

import re

from alembic import op
import sqlalchemy as sa

from app.adaptation.schema import INSTITUTION_EVOLUTION_SQL


revision = "20260730_0022"
down_revision = "20260730_0021"
branch_labels = None
depends_on = None


def upgrade():
    sql = INSTITUTION_EVOLUTION_SQL
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
        "rule_effect_reviews",
        "evolved_rule_versions",
        "rule_deliberations",
        "institutional_rule_proposals",
        "rule_primitives",
    ):
        op.drop_table(table_name)

