from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    UniqueConstraint,
    func,
)

from app.db.metadata import metadata


agent_observations = Table(
    "agent_observations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "observer_resident_id",
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("tick_id", ForeignKey("world_ticks.id", ondelete="SET NULL")),
    Column(
        "source_event_id",
        ForeignKey("world_event_stream.id", ondelete="SET NULL"),
    ),
    Column("origin_node_id", ForeignKey("spatial_nodes.id", ondelete="SET NULL")),
    Column("subject_type", String(32), nullable=False),
    Column("subject_id", String(120), nullable=False),
    Column("modality", String(32), nullable=False),
    Column("fact_type", String(80), nullable=False),
    Column("summary", String(600), nullable=False),
    Column("distance_meters", Float),
    Column("confidence", Integer, nullable=False),
    Column("error_margin", Float, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("branch_key", String(80), nullable=False),
    Column("metadata", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "observer_resident_id",
        "source_event_id",
        "modality",
        name="uq_agent_observations_observer_event_modality",
    ),
    CheckConstraint(
        "confidence >= 0 AND confidence <= 100",
        name="agent_observations_confidence_range",
    ),
    CheckConstraint(
        "error_margin >= 0",
        name="agent_observations_error_nonnegative",
    ),
    CheckConstraint(
        "distance_meters IS NULL OR distance_meters >= 0",
        name="agent_observations_distance_nonnegative",
    ),
)

agent_belief_states = Table(
    "agent_belief_states",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "resident_id",
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("subject_type", String(32), nullable=False),
    Column("subject_id", String(120), nullable=False),
    Column("belief_type", String(64), nullable=False),
    Column("summary", String(600), nullable=False),
    Column("confidence", Integer, nullable=False),
    Column(
        "last_observation_id",
        ForeignKey("agent_observations.id", ondelete="SET NULL"),
    ),
    Column("evidence_count", Integer, nullable=False),
    Column("status", String(32), nullable=False),
    Column("branch_key", String(80), nullable=False),
    Column("first_formed_at", DateTime(timezone=True), nullable=False),
    Column("last_updated_at", DateTime(timezone=True), nullable=False),
    Column("metadata", JSON, nullable=False),
    UniqueConstraint(
        "resident_id",
        "subject_type",
        "subject_id",
        "belief_type",
        "branch_key",
        name="uq_agent_belief_states_subject",
    ),
    CheckConstraint(
        "confidence >= 0 AND confidence <= 100",
        name="agent_belief_states_confidence_range",
    ),
    CheckConstraint(
        "evidence_count > 0",
        name="agent_belief_states_evidence_positive",
    ),
)

agent_spatial_memories = Table(
    "agent_spatial_memories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "resident_id",
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "observation_id",
        ForeignKey("agent_observations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("node_id", ForeignKey("spatial_nodes.id", ondelete="SET NULL")),
    Column("memory_type", String(32), nullable=False),
    Column("summary", String(600), nullable=False),
    Column("salience", Integer, nullable=False),
    Column("confidence", Integer, nullable=False),
    Column("valence", Integer, nullable=False),
    Column("visit_count", Integer, nullable=False),
    Column("last_recalled_at", DateTime(timezone=True)),
    Column("formed_at", DateTime(timezone=True), nullable=False),
    Column("branch_key", String(80), nullable=False),
    Column("metadata", JSON, nullable=False),
    CheckConstraint(
        "salience >= 0 AND salience <= 100",
        name="agent_spatial_memories_salience_range",
    ),
    CheckConstraint(
        "confidence >= 0 AND confidence <= 100",
        name="agent_spatial_memories_confidence_range",
    ),
    CheckConstraint(
        "valence >= -100 AND valence <= 100",
        name="agent_spatial_memories_valence_range",
    ),
    CheckConstraint(
        "visit_count > 0",
        name="agent_spatial_memories_visit_positive",
    ),
)
