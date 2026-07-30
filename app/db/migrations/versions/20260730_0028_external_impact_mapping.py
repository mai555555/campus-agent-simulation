"""Add deterministic external event impact mapping.

Revision ID: 20260730_0028
Revises: 20260730_0027
"""

import re
from alembic import op
import sqlalchemy as sa
from app.external_world.schema import IMPACT_SQL

revision = "20260730_0028"
down_revision = "20260730_0027"
branch_labels = None
depends_on = None


def upgrade():
    sql = IMPACT_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    op.drop_table("external_state_reconciliations")
    op.drop_table("external_event_impacts")
    op.drop_table("external_impact_rules")
