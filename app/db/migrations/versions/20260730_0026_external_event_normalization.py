"""Add normalized external events and evidence links.

Revision ID: 20260730_0026
Revises: 20260730_0025
"""

import re
from alembic import op
import sqlalchemy as sa
from app.external_world.schema import NORMALIZATION_SQL

revision = "20260730_0026"
down_revision = "20260730_0025"
branch_labels = None
depends_on = None


def upgrade():
    sql = NORMALIZATION_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    op.drop_table("external_event_links")
    op.drop_table("external_events")
    op.drop_table("external_event_catalog")
