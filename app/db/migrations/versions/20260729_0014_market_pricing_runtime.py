"""Add supply, demand, pricing, and market friction runtime.

Revision ID: 20260729_0014
Revises: 20260729_0013
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0014"
down_revision = "20260729_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_mechanisms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mechanism_key", sa.String(220), nullable=False, unique=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("provider_actor_key", sa.String(160), nullable=False),
        sa.Column("location", sa.String(120), nullable=False, server_default=""),
        sa.Column("pricing_mode", sa.String(20), nullable=False),
        sa.Column("base_price_minor", sa.Integer(), nullable=False),
        sa.Column("floor_price_minor", sa.Integer(), nullable=False),
        sa.Column("ceiling_price_minor", sa.Integer(), nullable=False),
        sa.Column("variable_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_supply", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("target_daily_demand", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("adjustment_rate_basis_points", sa.Integer(), nullable=False, server_default="2500"),
        sa.Column("demand_elasticity_basis_points", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("search_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transaction_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("daily_quota_per_resident", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rule_version", sa.String(40), nullable=False, server_default="market-pricing-v1"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["item_id"], ["catalog_items.id"], ondelete="RESTRICT", name="fk_market_mechanisms_item"),
        sa.UniqueConstraint("item_id", "provider_actor_key", "location", name="uq_market_mechanisms_scope"),
        sa.CheckConstraint("pricing_mode IN ('fixed', 'dynamic', 'rationed', 'negotiated')", name="ck_market_mechanisms_mode"),
        sa.CheckConstraint("base_price_minor >= 0", name="ck_market_mechanisms_base"),
        sa.CheckConstraint("floor_price_minor >= 0", name="ck_market_mechanisms_floor"),
        sa.CheckConstraint("ceiling_price_minor >= floor_price_minor", name="ck_market_mechanisms_ceiling"),
        sa.CheckConstraint("base_price_minor BETWEEN floor_price_minor AND ceiling_price_minor", name="ck_market_mechanisms_base_range"),
        sa.CheckConstraint("variable_cost_minor >= 0", name="ck_market_mechanisms_cost"),
        sa.CheckConstraint("target_supply > 0 AND target_daily_demand > 0", name="ck_market_mechanisms_targets"),
        sa.CheckConstraint("adjustment_rate_basis_points BETWEEN 0 AND 10000", name="ck_market_mechanisms_adjustment"),
        sa.CheckConstraint("demand_elasticity_basis_points BETWEEN 0 AND 30000", name="ck_market_mechanisms_elasticity"),
        sa.CheckConstraint("search_cost_minor >= 0 AND transaction_cost_minor >= 0", name="ck_market_mechanisms_friction"),
        sa.CheckConstraint("daily_quota_per_resident >= 0", name="ck_market_mechanisms_quota"),
        sa.CheckConstraint("status IN ('active', 'paused')", name="ck_market_mechanisms_status"),
    )
    op.create_table(
        "market_price_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quote_key", sa.String(220), nullable=False, unique=True),
        sa.Column("mechanism_id", sa.Integer(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("base_price_minor", sa.Integer(), nullable=False),
        sa.Column("variable_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inventory_pressure_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("demand_pressure_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("environment_pressure_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_adjustment_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("search_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transaction_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_supply", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observed_demand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fulfilled_demand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rationed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("valid_from", sa.String(40), nullable=False),
        sa.Column("valid_until", sa.String(40), nullable=False),
        sa.Column("state_fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["mechanism_id"], ["market_mechanisms.id"], ondelete="CASCADE", name="fk_market_prices_mechanism"),
        sa.CheckConstraint("price_minor >= 0 AND base_price_minor >= 0 AND variable_cost_minor >= 0", name="ck_market_prices_money"),
        sa.CheckConstraint("search_cost_minor >= 0 AND transaction_cost_minor >= 0", name="ck_market_prices_friction"),
        sa.CheckConstraint("available_supply >= 0 AND observed_demand >= 0 AND fulfilled_demand >= 0", name="ck_market_prices_quantities"),
        sa.CheckConstraint("rationed IN (0, 1)", name="ck_market_prices_rationed"),
    )
    op.create_table(
        "market_demand_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_key", sa.String(240), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("mechanism_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("action_execution_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("need_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("preference_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("social_influence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disposable_budget_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("maximum_unit_price_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quoted_unit_price_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_unit_price_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("substitute_item_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_market_demand_resident"),
        sa.ForeignKeyConstraint(["mechanism_id"], ["market_mechanisms.id"], ondelete="CASCADE", name="fk_market_demand_mechanism"),
        sa.ForeignKeyConstraint(["item_id"], ["catalog_items.id"], ondelete="RESTRICT", name="fk_market_demand_item"),
        sa.ForeignKeyConstraint(["substitute_item_id"], ["catalog_items.id"], ondelete="SET NULL", name="fk_market_demand_substitute"),
        sa.ForeignKeyConstraint(["action_execution_id"], ["world_action_executions.id"], ondelete="SET NULL", name="fk_market_demand_action"),
        sa.CheckConstraint("quantity > 0", name="ck_market_demand_quantity"),
        sa.CheckConstraint("need_score BETWEEN 0 AND 100 AND preference_score BETWEEN 0 AND 100 AND social_influence_score BETWEEN 0 AND 100", name="ck_market_demand_scores"),
        sa.CheckConstraint("disposable_budget_minor >= 0 AND maximum_unit_price_minor >= 0", name="ck_market_demand_budget"),
        sa.CheckConstraint("quoted_unit_price_minor >= 0 AND final_unit_price_minor >= 0", name="ck_market_demand_prices"),
        sa.CheckConstraint("status IN ('accepted', 'fulfilled', 'price_rejected', 'substituted', 'deferred', 'out_of_stock', 'rationed')", name="ck_market_demand_status"),
    )
    op.create_table(
        "market_friction_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(260), nullable=False, unique=True),
        sa.Column("mechanism_id", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=True),
        sa.Column("demand_signal_id", sa.Integer(), nullable=True),
        sa.Column("friction_type", sa.String(24), nullable=False),
        sa.Column("monetary_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wait_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["mechanism_id"], ["market_mechanisms.id"], ondelete="CASCADE", name="fk_market_friction_mechanism"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="SET NULL", name="fk_market_friction_resident"),
        sa.ForeignKeyConstraint(["demand_signal_id"], ["market_demand_signals.id"], ondelete="SET NULL", name="fk_market_friction_demand"),
        sa.CheckConstraint("friction_type IN ('search_cost', 'transaction_cost', 'stockout', 'rationing', 'queue', 'information_gap', 'substitution')", name="ck_market_friction_type"),
        sa.CheckConstraint("monetary_cost_minor >= 0 AND wait_minutes >= 0", name="ck_market_friction_cost"),
    )
    op.create_index("idx_market_mechanisms_item", "market_mechanisms", ["item_id", "provider_actor_key"])
    op.create_index("idx_market_prices_mechanism_time", "market_price_snapshots", ["mechanism_id", "valid_from"])
    op.create_index("idx_market_demand_mechanism_time", "market_demand_signals", ["mechanism_id", "occurred_at"])
    op.create_index("idx_market_demand_resident_time", "market_demand_signals", ["resident_id", "occurred_at"])
    op.create_index("idx_market_friction_time", "market_friction_events", ["mechanism_id", "occurred_at"])


def downgrade() -> None:
    for table in (
        "market_friction_events",
        "market_demand_signals",
        "market_price_snapshots",
        "market_mechanisms",
    ):
        op.drop_table(table)
