"""Add external-data governance, health, and research bindings.

Revision ID: 20260730_0029
Revises: 20260730_0028
"""

import re
from alembic import op
import sqlalchemy as sa
from app.external_world.schema import GOVERNANCE_SQL

revision = "20260730_0029"
down_revision = "20260730_0028"
branch_labels = None
depends_on = None


def upgrade():
    sql = GOVERNANCE_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    for table in ("external_experiment_bindings", "external_snapshot_exports", "external_runtime_health", "external_access_audit", "external_governance_reviews"):
        op.drop_table(table)
