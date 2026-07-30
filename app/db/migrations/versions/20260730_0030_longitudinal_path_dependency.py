"""Add cross-cycle life course and path-dependency aggregation.

Revision ID: 20260730_0030
Revises: 20260730_0029
"""

import re
from alembic import op
import sqlalchemy as sa
from app.longitudinal.schema import LONGITUDINAL_RUNTIME_SQL

revision = "20260730_0030"
down_revision = "20260730_0029"
branch_labels = None
depends_on = None


def upgrade():
    sql = LONGITUDINAL_RUNTIME_SQL
    if op.get_bind().dialect.name == "postgresql":
        sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    for statement in sql.split(";"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))


def downgrade():
    for table in (
        "trajectory_reconciliations",
        "longitudinal_aggregations",
        "path_dependency_links",
        "life_turning_points",
        "life_course_stages",
        "longitudinal_profiles",
    ):
        op.drop_table(table)
