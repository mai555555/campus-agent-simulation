"""Add auditable external source ingestion.

Revision ID: 20260730_0025
Revises: 20260730_0024
"""

import re
from alembic import op
import sqlalchemy as sa
from app.external_world.schema import INGESTION_SQL

revision = "20260730_0025"
down_revision = "20260730_0024"
branch_labels = None
depends_on = None


def upgrade():
    sql = INGESTION_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    for table in ("external_source_locks", "external_raw_observations", "external_sync_runs", "external_sources"):
        op.drop_table(table)
