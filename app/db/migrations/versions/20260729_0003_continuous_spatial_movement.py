"""Add continuous movement state.

Revision ID: 20260729_0003
Revises: 20260729_0002
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0003"
down_revision = "20260729_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_spatial_states") as batch:
        batch.add_column(sa.Column("origin_node_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column(
                "route_distance_meters",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "remaining_distance_meters",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(sa.Column("planned_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("started_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("last_progress_at", sa.DateTime(timezone=True)))
        batch.add_column(sa.Column("estimated_arrival_at", sa.DateTime(timezone=True)))
        batch.add_column(
            sa.Column(
                "replan_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.add_column(
            sa.Column(
                "last_replan_reason",
                sa.String(length=240),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "interrupted_reason",
                sa.String(length=240),
                nullable=False,
                server_default="",
            )
        )
        batch.create_foreign_key(
            "fk_agent_spatial_states_origin_node",
            "spatial_nodes",
            ["origin_node_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_check_constraint(
            "ck_agent_spatial_states_route_distance_nonnegative",
            "route_distance_meters >= 0",
        )
        batch.create_check_constraint(
            "ck_agent_spatial_states_remaining_distance_nonnegative",
            "remaining_distance_meters >= 0",
        )
        batch.create_check_constraint(
            "ck_agent_spatial_states_replan_count_nonnegative",
            "replan_count >= 0",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_spatial_states") as batch:
        batch.drop_constraint(
            "ck_agent_spatial_states_replan_count_nonnegative",
            type_="check",
        )
        batch.drop_constraint(
            "ck_agent_spatial_states_remaining_distance_nonnegative",
            type_="check",
        )
        batch.drop_constraint(
            "ck_agent_spatial_states_route_distance_nonnegative",
            type_="check",
        )
        batch.drop_constraint(
            "fk_agent_spatial_states_origin_node",
            type_="foreignkey",
        )
        batch.drop_column("interrupted_reason")
        batch.drop_column("last_replan_reason")
        batch.drop_column("replan_count")
        batch.drop_column("estimated_arrival_at")
        batch.drop_column("last_progress_at")
        batch.drop_column("started_at")
        batch.drop_column("planned_at")
        batch.drop_column("remaining_distance_meters")
        batch.drop_column("route_distance_meters")
        batch.drop_column("origin_node_id")
