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


CAPABILITY_FIELDS = (
    "physical_endurance",
    "time_management",
    "risk_tolerance",
    "rule_adherence",
    "information_literacy",
    "economic_access",
    "social_capital",
    "institutional_access",
    "language_access",
    "stress_resilience",
)


agent_capability_profiles = Table(
    "agent_capability_profiles",
    metadata,
    Column(
        "resident_id",
        ForeignKey("residents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    *[Column(field, Integer, nullable=False) for field in CAPABILITY_FIELDS],
    Column("source", String(80), nullable=False),
    Column("source_detail", JSON, nullable=False),
    Column("defaults_version", String(40), nullable=False),
    Column("missing_value_policy", String(120), nullable=False),
    Column("version", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    *[
        CheckConstraint(
            f"{field} >= 0 AND {field} <= 100",
            name=f"agent_capability_profiles_{field}_range",
        )
        for field in CAPABILITY_FIELDS
    ],
    CheckConstraint("version > 0", name="agent_capability_profiles_version_positive"),
)


agent_opportunity_access = Table(
    "agent_opportunity_access",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "resident_id",
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("opportunity_key", String(80), nullable=False),
    Column("access_level", Integer, nullable=False),
    Column("time_cost_multiplier", Float, nullable=False),
    Column("monetary_barrier", Integer, nullable=False),
    Column("eligibility", String(32), nullable=False),
    Column("source", String(80), nullable=False),
    Column("source_detail", JSON, nullable=False),
    Column("version", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "resident_id",
        "opportunity_key",
        name="uq_agent_opportunity_access_resident_key",
    ),
    CheckConstraint(
        "access_level >= 0 AND access_level <= 100",
        name="agent_opportunity_access_level_range",
    ),
    CheckConstraint(
        "time_cost_multiplier > 0",
        name="agent_opportunity_access_time_positive",
    ),
    CheckConstraint(
        "monetary_barrier >= 0",
        name="agent_opportunity_access_money_nonnegative",
    ),
    CheckConstraint("version > 0", name="agent_opportunity_access_version_positive"),
)
