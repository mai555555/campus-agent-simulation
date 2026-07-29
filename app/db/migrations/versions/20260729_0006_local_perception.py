"""Add local observations, beliefs, and spatial memories.

Revision ID: 20260729_0006
Revises: 20260729_0005
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0006"
down_revision = "20260729_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("observer_resident_id", sa.Integer(), nullable=False),
        sa.Column("tick_id", sa.Integer()),
        sa.Column("source_event_id", sa.Integer()),
        sa.Column("origin_node_id", sa.Integer()),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.String(length=120), nullable=False),
        sa.Column("modality", sa.String(length=32), nullable=False),
        sa.Column("fact_type", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("distance_meters", sa.Float()),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("error_margin", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["observer_resident_id"], ["residents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tick_id"], ["world_ticks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["source_event_id"], ["world_event_stream.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["origin_node_id"], ["spatial_nodes.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "observer_resident_id",
            "source_event_id",
            "modality",
            name="uq_agent_observations_observer_event_modality",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="ck_agent_observations_confidence_range",
        ),
        sa.CheckConstraint(
            "error_margin >= 0",
            name="ck_agent_observations_error_nonnegative",
        ),
        sa.CheckConstraint(
            "distance_meters IS NULL OR distance_meters >= 0",
            name="ck_agent_observations_distance_nonnegative",
        ),
    )
    op.create_index(
        "ix_agent_observations_observer_tick",
        "agent_observations",
        ["observer_resident_id", "tick_id"],
    )
    op.create_index(
        "ix_agent_observations_source_event",
        "agent_observations",
        ["source_event_id"],
    )

    op.create_table(
        "agent_belief_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.String(length=120), nullable=False),
        sa.Column("belief_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("last_observation_id", sa.Integer()),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column("first_formed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["last_observation_id"], ["agent_observations.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "resident_id",
            "subject_type",
            "subject_id",
            "belief_type",
            "branch_key",
            name="uq_agent_belief_states_subject",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="ck_agent_belief_states_confidence_range",
        ),
        sa.CheckConstraint(
            "evidence_count > 0",
            name="ck_agent_belief_states_evidence_positive",
        ),
    )
    op.create_index(
        "ix_agent_belief_states_resident_updated",
        "agent_belief_states",
        ["resident_id", "last_updated_at"],
    )

    op.create_table(
        "agent_spatial_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("observation_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("node_id", sa.Integer()),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=False),
        sa.Column("salience", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("valence", sa.Integer(), nullable=False),
        sa.Column("visit_count", sa.Integer(), nullable=False),
        sa.Column("last_recalled_at", sa.DateTime(timezone=True)),
        sa.Column("formed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("branch_key", sa.String(length=80), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["observation_id"], ["agent_observations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["node_id"], ["spatial_nodes.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "salience >= 0 AND salience <= 100",
            name="ck_agent_spatial_memories_salience_range",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="ck_agent_spatial_memories_confidence_range",
        ),
        sa.CheckConstraint(
            "valence >= -100 AND valence <= 100",
            name="ck_agent_spatial_memories_valence_range",
        ),
        sa.CheckConstraint(
            "visit_count > 0",
            name="ck_agent_spatial_memories_visit_positive",
        ),
    )
    op.create_index(
        "ix_agent_spatial_memories_resident_node",
        "agent_spatial_memories",
        ["resident_id", "node_id", "formed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_spatial_memories_resident_node",
        table_name="agent_spatial_memories",
    )
    op.drop_table("agent_spatial_memories")
    op.drop_index(
        "ix_agent_belief_states_resident_updated",
        table_name="agent_belief_states",
    )
    op.drop_table("agent_belief_states")
    op.drop_index(
        "ix_agent_observations_source_event",
        table_name="agent_observations",
    )
    op.drop_index(
        "ix_agent_observations_observer_tick",
        table_name="agent_observations",
    )
    op.drop_table("agent_observations")
