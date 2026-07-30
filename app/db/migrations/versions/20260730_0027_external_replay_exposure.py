"""Add external snapshots, replay modes, and cognitive exposures.

Revision ID: 20260730_0027
Revises: 20260730_0026
"""

import re
from alembic import op
import sqlalchemy as sa
from app.external_world.schema import REPLAY_EXPOSURE_SQL

revision = "20260730_0027"
down_revision = "20260730_0026"
branch_labels = None
depends_on = None


def upgrade():
    sql = REPLAY_EXPOSURE_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    for table in ("external_replay_deliveries", "external_exposures", "external_runtime_modes", "external_snapshot_items", "external_data_snapshots"):
        op.drop_table(table)
