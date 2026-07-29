"""Add deterministic Agent body states.

Revision ID: 20260729_0005
Revises: 20260729_0004
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0005"
down_revision = "20260729_0004"
branch_labels = None
depends_on = None

RANGE_FIELDS = (
    "hunger",
    "fatigue",
    "sleep_debt",
    "stress",
    "attention",
    "social_energy",
    "health",
    "weather_exposure",
)


def upgrade() -> None:
    constraints = [
        sa.CheckConstraint(
            f"{field} >= 0 AND {field} <= 100",
            name=f"ck_agent_body_states_{field}_range",
        )
        for field in RANGE_FIELDS
    ]
    op.create_table(
        "agent_body_states",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        *[sa.Column(field, sa.Float(), nullable=False) for field in RANGE_FIELDS],
        sa.Column("last_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "last_updated_tick",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "source",
            sa.String(length=64),
            nullable=False,
            server_default="seeded",
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
        *constraints,
        sa.CheckConstraint(
            "last_updated_tick >= 0",
            name="ck_agent_body_states_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="ck_agent_body_states_version_positive",
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_body_states")
