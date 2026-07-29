"""Add spatial resources and the active admission queue.

Revision ID: 20260729_0004
Revises: 20260729_0003
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0004"
down_revision = "20260729_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spatial_resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("resource_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("available_units", sa.Integer(), nullable=False),
        sa.Column("service_rate_per_hour", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["spatial_nodes.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "node_id", "resource_key", name="uq_spatial_resources_node_key"
        ),
        sa.CheckConstraint(
            "capacity >= 0", name="ck_spatial_resources_capacity_nonnegative"
        ),
        sa.CheckConstraint(
            "available_units >= 0 AND available_units <= capacity",
            name="ck_spatial_resources_available_range",
        ),
        sa.CheckConstraint(
            "service_rate_per_hour > 0",
            name="ck_spatial_resources_service_rate_positive",
        ),
    )
    op.create_table(
        "spatial_admission_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.Integer()),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queue_position", sa.Integer(), nullable=False),
        sa.Column("patience_minutes", sa.Float(), nullable=False),
        sa.Column("estimated_wait_minutes", sa.Float(), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column("requested_tick", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["spatial_nodes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["resource_id"], ["spatial_resources.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "resident_id", name="uq_spatial_admission_queue_resident"
        ),
        sa.CheckConstraint(
            "queue_position > 0",
            name="ck_spatial_admission_queue_position_positive",
        ),
        sa.CheckConstraint(
            "patience_minutes > 0",
            name="ck_spatial_admission_queue_patience_positive",
        ),
        sa.CheckConstraint(
            "estimated_wait_minutes >= 0",
            name="ck_spatial_admission_queue_wait_nonnegative",
        ),
        sa.CheckConstraint(
            "requested_tick >= 0",
            name="ck_spatial_admission_queue_tick_nonnegative",
        ),
    )
    op.create_index(
        "ix_spatial_admission_queue_node_position",
        "spatial_admission_queue",
        ["node_id", "queue_position"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_spatial_admission_queue_node_position",
        table_name="spatial_admission_queue",
    )
    op.drop_table("spatial_admission_queue")
    op.drop_table("spatial_resources")
