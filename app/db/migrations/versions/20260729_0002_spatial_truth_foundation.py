"""Create the spatial truth foundation.

Revision ID: 20260729_0002
Revises: 20260729_0001
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0002"
down_revision = "20260729_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spatial_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("z", sa.Float(), nullable=False),
        sa.Column("radius", sa.Float(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "capacity >= 0", name="ck_spatial_nodes_capacity_nonnegative"
        ),
        sa.CheckConstraint("radius > 0", name="ck_spatial_nodes_radius_positive"),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_spatial_nodes_parent_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["spatial_nodes.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("code", name="uq_spatial_nodes_code"),
    )
    op.create_table(
        "spatial_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_node_id", sa.Integer(), nullable=False),
        sa.Column("to_node_id", sa.Integer(), nullable=False),
        sa.Column("distance_meters", sa.Float(), nullable=False),
        sa.Column("base_minutes", sa.Float(), nullable=False),
        sa.Column("bidirectional", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("congestion_factor", sa.Float(), nullable=False),
        sa.Column("weather_factor", sa.Float(), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "from_node_id <> to_node_id",
            name="ck_spatial_edges_distinct_nodes",
        ),
        sa.CheckConstraint(
            "distance_meters > 0", name="ck_spatial_edges_distance_positive"
        ),
        sa.CheckConstraint(
            "base_minutes > 0", name="ck_spatial_edges_minutes_positive"
        ),
        sa.CheckConstraint(
            "congestion_factor > 0",
            name="ck_spatial_edges_congestion_positive",
        ),
        sa.CheckConstraint(
            "weather_factor > 0", name="ck_spatial_edges_weather_positive"
        ),
        sa.ForeignKeyConstraint(
            ["from_node_id"], ["spatial_nodes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_node_id"], ["spatial_nodes.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "from_node_id", "to_node_id", name="uq_spatial_edges_from_to"
        ),
    )
    op.create_table(
        "agent_spatial_capabilities",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("base_speed_m_per_min", sa.Float(), nullable=False),
        sa.Column("mobility_class", sa.String(length=32), nullable=False),
        sa.Column("accessibility_needs", sa.JSON(), nullable=False),
        sa.Column("perception_radius_m", sa.Float(), nullable=False),
        sa.Column("hearing_radius_m", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "base_speed_m_per_min > 0",
            name="ck_agent_spatial_capabilities_speed_positive",
        ),
        sa.CheckConstraint(
            "perception_radius_m > 0",
            name="ck_agent_spatial_capabilities_perception_positive",
        ),
        sa.CheckConstraint(
            "hearing_radius_m > 0",
            name="ck_agent_spatial_capabilities_hearing_positive",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="ck_agent_spatial_capabilities_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
    )
    op.create_table(
        "agent_spatial_states",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("current_node_id", sa.Integer(), nullable=False),
        sa.Column("target_node_id", sa.Integer(), nullable=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("z", sa.Float(), nullable=False),
        sa.Column("facing_x", sa.Float(), nullable=False),
        sa.Column("facing_z", sa.Float(), nullable=False),
        sa.Column("movement_status", sa.String(length=32), nullable=False),
        sa.Column("path", sa.JSON(), nullable=False),
        sa.Column("path_index", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("updated_tick", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "path_index >= 0",
            name="ck_agent_spatial_states_path_index_nonnegative",
        ),
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 1",
            name="ck_agent_spatial_states_progress_range",
        ),
        sa.CheckConstraint(
            "updated_tick >= 0",
            name="ck_agent_spatial_states_tick_nonnegative",
        ),
        sa.CheckConstraint(
            "version > 0", name="ck_agent_spatial_states_version_positive"
        ),
        sa.ForeignKeyConstraint(
            ["resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["current_node_id"], ["spatial_nodes.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"], ["spatial_nodes.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_agent_spatial_states_current_node",
        "agent_spatial_states",
        ["current_node_id"],
    )
    op.create_table(
        "agent_trajectories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_run_id", sa.Integer(), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column("tick_number", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.Integer(), nullable=True),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("z", sa.Float(), nullable=False),
        sa.Column("movement_status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "tick_number >= 0", name="ck_agent_trajectories_tick_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["experiment_run_id"], ["experiment_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["node_id"], ["spatial_nodes.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "experiment_run_id",
            "branch_key",
            "tick_number",
            "resident_id",
            name="uq_agent_trajectories_run_branch_tick_resident",
        ),
    )
    op.create_index(
        "ix_agent_trajectories_run_tick",
        "agent_trajectories",
        ["experiment_run_id", "branch_key", "tick_number"],
    )
    op.create_index(
        "ix_agent_trajectories_resident_tick",
        "agent_trajectories",
        ["resident_id", "tick_number"],
    )
    op.create_index(
        "ix_agent_trajectories_node_tick",
        "agent_trajectories",
        ["node_id", "tick_number"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_trajectories_node_tick", table_name="agent_trajectories")
    op.drop_index(
        "ix_agent_trajectories_resident_tick", table_name="agent_trajectories"
    )
    op.drop_index("ix_agent_trajectories_run_tick", table_name="agent_trajectories")
    op.drop_table("agent_trajectories")
    op.drop_index(
        "ix_agent_spatial_states_current_node", table_name="agent_spatial_states"
    )
    op.drop_table("agent_spatial_states")
    op.drop_table("agent_spatial_capabilities")
    op.drop_table("spatial_edges")
    op.drop_table("spatial_nodes")
