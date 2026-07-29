"""Add public services, externalities, and economic policy.

Revision ID: 20260729_0016
Revises: 20260729_0015
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0016"
down_revision = "20260729_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_key", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("service_type", sa.String(32), nullable=False),
        sa.Column("provider_actor_key", sa.String(160), nullable=False),
        sa.Column("location", sa.String(120), nullable=False, server_default=""),
        sa.Column("daily_capacity", sa.Integer(), nullable=False),
        sa.Column("base_daily_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("marginal_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("access_mode", sa.String(20), nullable=False, server_default="universal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("rule_version", sa.String(40), nullable=False, server_default="public-policy-v1"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("service_type IN ('library', 'network', 'security', 'public_space')", name="ck_public_services_type"),
        sa.CheckConstraint("daily_capacity > 0", name="ck_public_services_capacity"),
        sa.CheckConstraint("base_daily_cost_minor >= 0 AND marginal_cost_minor >= 0", name="ck_public_services_cost"),
        sa.CheckConstraint("quality BETWEEN 0 AND 100", name="ck_public_services_quality"),
        sa.CheckConstraint("access_mode IN ('universal', 'location', 'role', 'eligible')", name="ck_public_services_access"),
        sa.CheckConstraint("status IN ('active', 'degraded', 'paused')", name="ck_public_services_status"),
    )
    op.create_table(
        "public_service_operations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation_key", sa.String(240), nullable=False, unique=True),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("operation_date", sa.String(10), nullable=False),
        sa.Column("available_capacity", sa.Integer(), nullable=False),
        sa.Column("used_capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("denied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("operating_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("funded_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["service_id"], ["public_services.id"], ondelete="CASCADE", name="fk_public_operations_service"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_public_operations_ledger"),
        sa.UniqueConstraint("service_id", "operation_date", name="uq_public_operations_service_date"),
        sa.CheckConstraint("available_capacity >= 0 AND used_capacity >= 0 AND used_capacity <= available_capacity", name="ck_public_operations_capacity"),
        sa.CheckConstraint("denied_count >= 0", name="ck_public_operations_denied"),
        sa.CheckConstraint("operating_cost_minor >= 0 AND funded_cost_minor >= 0 AND funded_cost_minor <= operating_cost_minor", name="ck_public_operations_cost"),
        sa.CheckConstraint("quality BETWEEN 0 AND 100", name="ck_public_operations_quality"),
        sa.CheckConstraint("status IN ('open', 'capacity_limited', 'underfunded', 'closed')", name="ck_public_operations_status"),
    )
    op.create_table(
        "public_service_usages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usage_key", sa.String(280), nullable=False, unique=True),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("access_group", sa.String(40), nullable=False),
        sa.Column("location", sa.String(120), nullable=False, server_default=""),
        sa.Column("units", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("wait_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("access_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("welfare_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["operation_id"], ["public_service_operations.id"], ondelete="CASCADE", name="fk_public_usages_operation"),
        sa.ForeignKeyConstraint(["service_id"], ["public_services.id"], ondelete="CASCADE", name="fk_public_usages_service"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_public_usages_resident"),
        sa.CheckConstraint("units > 0 AND wait_minutes >= 0 AND access_cost_minor >= 0", name="ck_public_usages_amounts"),
        sa.CheckConstraint("welfare_delta BETWEEN -100 AND 100", name="ck_public_usages_welfare"),
        sa.CheckConstraint("status IN ('served', 'queued', 'denied', 'not_eligible')", name="ck_public_usages_status"),
    )
    op.create_table(
        "externality_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(280), nullable=False, unique=True),
        sa.Column("externality_type", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("source_resident_id", sa.Integer(), nullable=True),
        sa.Column("source_actor_key", sa.String(160), nullable=False, server_default=""),
        sa.Column("location", sa.String(120), nullable=False, server_default=""),
        sa.Column("magnitude", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(12), nullable=False),
        sa.Column("radius_meters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.String(40), nullable=False),
        sa.Column("ends_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_resident_id"], ["residents.id"], ondelete="SET NULL", name="fk_externality_source_resident"),
        sa.CheckConstraint("externality_type IN ('congestion', 'noise', 'pollution', 'reputation', 'knowledge_spillover')", name="ck_externality_type"),
        sa.CheckConstraint("magnitude BETWEEN 1 AND 100", name="ck_externality_magnitude"),
        sa.CheckConstraint("direction IN ('positive', 'negative')", name="ck_externality_direction"),
        sa.CheckConstraint("radius_meters >= 0", name="ck_externality_radius"),
        sa.CheckConstraint("status IN ('active', 'expired', 'mitigated')", name="ck_externality_status"),
    )
    op.create_table(
        "externality_exposures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exposure_key", sa.String(320), nullable=False, unique=True),
        sa.Column("externality_event_id", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("exposure_score", sa.Integer(), nullable=False),
        sa.Column("welfare_delta", sa.Integer(), nullable=False),
        sa.Column("behavioral_pressure", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("distance_meters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_type", sa.String(24), nullable=False),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["externality_event_id"], ["externality_events.id"], ondelete="CASCADE", name="fk_externality_exposure_event"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_externality_exposure_resident"),
        sa.CheckConstraint("exposure_score BETWEEN 0 AND 100", name="ck_externality_exposure_score"),
        sa.CheckConstraint("welfare_delta BETWEEN -100 AND 100 AND behavioral_pressure BETWEEN -100 AND 100", name="ck_externality_exposure_effect"),
        sa.CheckConstraint("distance_meters >= 0", name="ck_externality_exposure_distance"),
        sa.CheckConstraint("evidence_type IN ('co_location', 'global_service', 'organization', 'market')", name="ck_externality_exposure_evidence"),
    )
    op.create_table(
        "policy_instruments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_key", sa.String(160), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("policy_type", sa.String(32), nullable=False),
        sa.Column("authority_actor_key", sa.String(160), nullable=False),
        sa.Column("budget_account_key", sa.String(200), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_key", sa.String(200), nullable=False, server_default=""),
        sa.Column("eligibility_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("parameters_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("daily_budget_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spent_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.String(40), nullable=False),
        sa.Column("ends_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("rule_version", sa.String(40), nullable=False, server_default="public-policy-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("policy_type IN ('subsidy', 'price_cap', 'scholarship', 'quota', 'fee', 'public_investment')", name="ck_policy_type"),
        sa.CheckConstraint("target_type IN ('catalog_item', 'market', 'resident', 'role', 'location', 'public_service')", name="ck_policy_target"),
        sa.CheckConstraint("daily_budget_minor >= 0 AND spent_minor >= 0", name="ck_policy_budget"),
        sa.CheckConstraint("status IN ('draft', 'active', 'paused', 'expired', 'budget_exhausted')", name="ck_policy_status"),
    )
    op.create_table(
        "policy_benefits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("benefit_key", sa.String(300), nullable=False, unique=True),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=True),
        sa.Column("beneficiary_actor_key", sa.String(160), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("gross_value_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("public_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("private_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("welfare_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["policy_id"], ["policy_instruments.id"], ondelete="CASCADE", name="fk_policy_benefit_policy"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="SET NULL", name="fk_policy_benefit_resident"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_policy_benefit_ledger"),
        sa.CheckConstraint("gross_value_minor >= 0 AND public_cost_minor >= 0 AND private_cost_minor >= 0", name="ck_policy_benefit_cost"),
        sa.CheckConstraint("welfare_delta BETWEEN -100 AND 100", name="ck_policy_benefit_welfare"),
        sa.CheckConstraint("status IN ('eligible', 'delivered', 'rationed', 'ineligible', 'unfunded')", name="ck_policy_benefit_status"),
    )
    op.create_table(
        "policy_outcome_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_key", sa.String(280), nullable=False, unique=True),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("window_type", sa.String(16), nullable=False),
        sa.Column("window_start", sa.String(40), nullable=False),
        sa.Column("window_end", sa.String(40), nullable=False),
        sa.Column("group_key", sa.String(80), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reached_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("public_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_private_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_welfare_delta", sa.Float(), nullable=False, server_default="0"),
        sa.Column("behavior_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("baseline_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("outcome_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["policy_id"], ["policy_instruments.id"], ondelete="CASCADE", name="fk_policy_outcome_policy"),
        sa.UniqueConstraint("policy_id", "window_type", "window_start", "window_end", "group_key", name="uq_policy_outcome_window_group"),
        sa.CheckConstraint("window_type IN ('baseline', 'daily', 'weekly')", name="ck_policy_outcome_window"),
        sa.CheckConstraint("eligible_count >= 0 AND reached_count >= 0 AND public_cost_minor >= 0", name="ck_policy_outcome_counts"),
        sa.CheckConstraint("average_private_cost_minor >= 0 AND behavior_count >= 0", name="ck_policy_outcome_values"),
    )
    op.create_index("ix_public_service_operations_date", "public_service_operations", ["operation_date", "service_id"])
    op.create_index("ix_public_service_usages_resident", "public_service_usages", ["resident_id", "occurred_at"])
    op.create_index("ix_externality_events_active", "externality_events", ["status", "location", "starts_at"])
    op.create_index("ix_externality_exposures_resident", "externality_exposures", ["resident_id", "occurred_at"])
    op.create_index("ix_policy_instruments_active", "policy_instruments", ["status", "policy_type", "starts_at"])
    op.create_index("ix_policy_benefits_policy", "policy_benefits", ["policy_id", "occurred_at", "status"])
    op.create_index("ix_policy_outcomes_policy", "policy_outcome_snapshots", ["policy_id", "window_start", "group_key"])


def downgrade() -> None:
    for table in (
        "policy_outcome_snapshots",
        "policy_benefits",
        "policy_instruments",
        "externality_exposures",
        "externality_events",
        "public_service_usages",
        "public_service_operations",
        "public_services",
    ):
        op.drop_table(table)
