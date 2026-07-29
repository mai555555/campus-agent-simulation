"""Add household budget and intertemporal choice runtime.

Revision ID: 20260729_0013
Revises: 20260729_0012
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0013"
down_revision = "20260729_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "household_budget_profiles",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("planning_horizon_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("savings_rate_basis_points", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("emergency_reserve_minor", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("risk_tolerance", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("credit_enabled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_limit_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outstanding_debt_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_savings_date", sa.String(10), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_household_budget_profiles_resident"),
        sa.CheckConstraint("planning_horizon_days > 0", name="ck_budget_profiles_horizon"),
        sa.CheckConstraint("savings_rate_basis_points BETWEEN 0 AND 10000", name="ck_budget_profiles_savings_rate"),
        sa.CheckConstraint("emergency_reserve_minor >= 0", name="ck_budget_profiles_emergency"),
        sa.CheckConstraint("risk_tolerance BETWEEN 0 AND 100", name="ck_budget_profiles_risk"),
        sa.CheckConstraint("credit_enabled = 0", name="ck_budget_profiles_credit_disabled"),
        sa.CheckConstraint("credit_limit_minor = 0", name="ck_budget_profiles_credit_limit_zero"),
        sa.CheckConstraint("outstanding_debt_minor = 0", name="ck_budget_profiles_debt_zero"),
        sa.CheckConstraint("status IN ('active', 'paused')", name="ck_budget_profiles_status"),
    )
    op.create_table(
        "household_budget_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_key", sa.String(180), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("budget_date", sa.String(10), nullable=False),
        sa.Column("cash_minor", sa.Integer(), nullable=False),
        sa.Column("savings_minor", sa.Integer(), nullable=False),
        sa.Column("expected_income_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transfer_income_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_expenses_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_debt_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("borrowing_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disposable_minor", sa.Integer(), nullable=False),
        sa.Column("time_budget_minutes", sa.Integer(), nullable=False),
        sa.Column("committed_time_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("free_time_minutes", sa.Integer(), nullable=False),
        sa.Column("liquidity_status", sa.String(16), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_budget_snapshots_resident"),
        sa.UniqueConstraint("resident_id", "budget_date", name="uq_budget_snapshots_resident_date"),
        sa.CheckConstraint("cash_minor >= 0 AND savings_minor >= 0", name="ck_budget_snapshots_assets"),
        sa.CheckConstraint("expected_income_minor >= 0 AND transfer_income_minor >= 0", name="ck_budget_snapshots_income"),
        sa.CheckConstraint("required_expenses_minor >= 0", name="ck_budget_snapshots_expenses"),
        sa.CheckConstraint("due_debt_minor = 0 AND borrowing_minor = 0", name="ck_budget_snapshots_credit_zero"),
        sa.CheckConstraint("disposable_minor >= 0", name="ck_budget_snapshots_disposable"),
        sa.CheckConstraint("time_budget_minutes >= 0 AND committed_time_minutes >= 0 AND free_time_minutes >= 0", name="ck_budget_snapshots_time"),
        sa.CheckConstraint("liquidity_status IN ('stable', 'tight', 'shortfall')", name="ck_budget_snapshots_liquidity"),
    )
    op.create_table(
        "savings_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_key", sa.String(200), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_savings_transfers_resident"),
        sa.ForeignKeyConstraint(["goal_id"], ["agent_goals.id"], ondelete="SET NULL", name="fk_savings_transfers_goal"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT", name="fk_savings_transfers_ledger"),
        sa.CheckConstraint("direction IN ('deposit', 'withdrawal')", name="ck_savings_transfers_direction"),
        sa.CheckConstraint("amount_minor > 0", name="ck_savings_transfers_amount"),
    )
    op.create_table(
        "choice_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_key", sa.String(200), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("action_execution_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(80), nullable=False),
        sa.Column("location", sa.String(120), nullable=False, server_default=""),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("required_money_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_time_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disposable_before_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("free_time_before_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("money_opportunity_cost_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_opportunity_cost_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("released_money_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("released_time_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alternative_action", sa.String(80), nullable=False, server_default=""),
        sa.Column("long_term_goal_id", sa.Integer(), nullable=True),
        sa.Column("emergency_override", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("rule_version", sa.String(40), nullable=False, server_default="budget-choice-v1"),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_choice_evaluations_resident"),
        sa.ForeignKeyConstraint(["action_execution_id"], ["world_action_executions.id"], ondelete="SET NULL", name="fk_choice_evaluations_action"),
        sa.ForeignKeyConstraint(["long_term_goal_id"], ["agent_goals.id"], ondelete="SET NULL", name="fk_choice_evaluations_goal"),
        sa.CheckConstraint("decision IN ('allowed', 'rejected', 'deferred')", name="ck_choice_evaluations_decision"),
        sa.CheckConstraint("required_money_minor >= 0 AND required_time_minutes >= 0", name="ck_choice_evaluations_required"),
        sa.CheckConstraint("disposable_before_minor >= 0 AND free_time_before_minutes >= 0", name="ck_choice_evaluations_available"),
        sa.CheckConstraint("money_opportunity_cost_minor >= 0 AND time_opportunity_cost_minutes >= 0", name="ck_choice_evaluations_cost"),
        sa.CheckConstraint("released_money_minor >= 0 AND released_time_minutes >= 0", name="ck_choice_evaluations_released"),
    )
    op.create_index("idx_budget_snapshots_resident_date", "household_budget_snapshots", ["resident_id", "budget_date"])
    op.create_index("idx_savings_transfers_resident", "savings_transfers", ["resident_id", "id"])
    op.create_index("idx_choice_evaluations_resident", "choice_evaluations", ["resident_id", "id"])


def downgrade() -> None:
    for table in (
        "choice_evaluations",
        "savings_transfers",
        "household_budget_snapshots",
        "household_budget_profiles",
    ):
        op.drop_table(table)
