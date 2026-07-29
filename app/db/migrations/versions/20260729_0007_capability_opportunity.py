"""Add structured capability and opportunity access profiles.

Revision ID: 20260729_0007
Revises: 20260729_0006
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa

from app.capability_models import CAPABILITY_FIELDS


revision = "20260729_0007"
down_revision = "20260729_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_capability_profiles",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        *[
            sa.Column(field, sa.Integer(), nullable=False)
            for field in CAPABILITY_FIELDS
        ],
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_detail", sa.JSON(), nullable=False),
        sa.Column("defaults_version", sa.String(length=40), nullable=False),
        sa.Column("missing_value_policy", sa.String(length=120), nullable=False),
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
        *[
            sa.CheckConstraint(
                f"{field} >= 0 AND {field} <= 100",
                name=f"ck_agent_capability_profiles_{field}_range",
            )
            for field in CAPABILITY_FIELDS
        ],
        sa.CheckConstraint(
            "version > 0",
            name="ck_agent_capability_profiles_version_positive",
        ),
    )
    op.create_table(
        "agent_opportunity_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("opportunity_key", sa.String(length=80), nullable=False),
        sa.Column("access_level", sa.Integer(), nullable=False),
        sa.Column("time_cost_multiplier", sa.Float(), nullable=False),
        sa.Column("monetary_barrier", sa.Integer(), nullable=False),
        sa.Column("eligibility", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_detail", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "resident_id",
            "opportunity_key",
            name="uq_agent_opportunity_access_resident_key",
        ),
        sa.CheckConstraint(
            "access_level >= 0 AND access_level <= 100",
            name="ck_agent_opportunity_access_level_range",
        ),
        sa.CheckConstraint(
            "time_cost_multiplier > 0",
            name="ck_agent_opportunity_access_time_positive",
        ),
        sa.CheckConstraint(
            "monetary_barrier >= 0",
            name="ck_agent_opportunity_access_money_nonnegative",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="ck_agent_opportunity_access_version_positive",
        ),
    )
    op.create_index(
        "ix_agent_opportunity_access_key_level",
        "agent_opportunity_access",
        ["opportunity_key", "access_level"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_opportunity_access_key_level",
        table_name="agent_opportunity_access",
    )
    op.drop_table("agent_opportunity_access")
    op.drop_table("agent_capability_profiles")
