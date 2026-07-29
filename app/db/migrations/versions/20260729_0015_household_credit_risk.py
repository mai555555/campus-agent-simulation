"""Add funded household credit, savings goals, risk, and default runtime.

Revision ID: 20260729_0015
Revises: 20260729_0014
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0015"
down_revision = "20260729_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("household_budget_profiles") as batch:
        batch.drop_constraint("ck_budget_profiles_credit_disabled", type_="check")
        batch.drop_constraint("ck_budget_profiles_credit_limit_zero", type_="check")
        batch.drop_constraint("ck_budget_profiles_debt_zero", type_="check")
        batch.create_check_constraint(
            "ck_budget_profiles_credit_enabled",
            "credit_enabled IN (0, 1)",
        )
        batch.create_check_constraint(
            "ck_budget_profiles_credit_limit_nonnegative",
            "credit_limit_minor >= 0",
        )
        batch.create_check_constraint(
            "ck_budget_profiles_debt_nonnegative",
            "outstanding_debt_minor >= 0",
        )
    with op.batch_alter_table("household_budget_snapshots") as batch:
        batch.drop_constraint("ck_budget_snapshots_credit_zero", type_="check")
        batch.create_check_constraint(
            "ck_budget_snapshots_credit_nonnegative",
            "due_debt_minor >= 0 AND borrowing_minor >= 0",
        )

    op.create_table(
        "savings_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("goal_key", sa.String(200), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("goal_type", sa.String(24), nullable=False),
        sa.Column("target_amount_minor", sa.Integer(), nullable=False),
        sa.Column("current_amount_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_date", sa.String(10), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_savings_goals_resident"),
        sa.CheckConstraint("goal_type IN ('emergency_reserve', 'education', 'purchase', 'general')", name="ck_savings_goals_type"),
        sa.CheckConstraint("target_amount_minor > 0 AND current_amount_minor >= 0", name="ck_savings_goals_amount"),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_savings_goals_priority"),
        sa.CheckConstraint("status IN ('active', 'achieved', 'paused', 'cancelled')", name="ck_savings_goals_status"),
    )
    op.create_table(
        "household_risk_profiles",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("income_volatility", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("health_exposure", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("essential_cost_exposure", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("shock_sensitivity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("mutual_aid_enrolled", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("coverage_basis_points", sa.Integer(), nullable=False, server_default="3000"),
        sa.Column("coverage_limit_minor", sa.Integer(), nullable=False, server_default="3000"),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_risk_profiles_resident"),
        sa.CheckConstraint("income_volatility BETWEEN 0 AND 100", name="ck_risk_profiles_income"),
        sa.CheckConstraint("health_exposure BETWEEN 0 AND 100", name="ck_risk_profiles_health"),
        sa.CheckConstraint("essential_cost_exposure BETWEEN 0 AND 100", name="ck_risk_profiles_cost"),
        sa.CheckConstraint("shock_sensitivity BETWEEN 0 AND 100", name="ck_risk_profiles_sensitivity"),
        sa.CheckConstraint("mutual_aid_enrolled IN (0, 1)", name="ck_risk_profiles_enrolled"),
        sa.CheckConstraint("coverage_basis_points BETWEEN 0 AND 10000", name="ck_risk_profiles_coverage"),
        sa.CheckConstraint("coverage_limit_minor >= 0", name="ck_risk_profiles_limit"),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="ck_risk_profiles_score"),
        sa.CheckConstraint("status IN ('active', 'paused')", name="ck_risk_profiles_status"),
    )
    op.create_table(
        "economic_shocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shock_key", sa.String(220), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("shock_type", sa.String(24), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("cash_used_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("savings_used_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_pool_paid_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_used_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uncovered_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impact_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("source_type", sa.String(80), nullable=False, server_default="credit_runtime"),
        sa.Column("source_id", sa.String(160), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("settled_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_economic_shocks_resident"),
        sa.CheckConstraint("shock_type IN ('income_loss', 'medical', 'essential_repair', 'family_emergency')", name="ck_economic_shocks_type"),
        sa.CheckConstraint("severity BETWEEN 1 AND 100", name="ck_economic_shocks_severity"),
        sa.CheckConstraint("amount_minor > 0", name="ck_economic_shocks_amount"),
        sa.CheckConstraint("cash_used_minor >= 0 AND savings_used_minor >= 0 AND risk_pool_paid_minor >= 0 AND credit_used_minor >= 0 AND uncovered_minor >= 0", name="ck_economic_shocks_funding"),
        sa.CheckConstraint("impact_score BETWEEN 0 AND 100", name="ck_economic_shocks_impact"),
        sa.CheckConstraint("status IN ('pending', 'settled', 'partially_covered', 'uncovered')", name="ck_economic_shocks_status"),
    )
    op.create_table(
        "credit_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_key", sa.String(180), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("lender_actor_key", sa.String(160), nullable=False),
        sa.Column("product_type", sa.String(20), nullable=False),
        sa.Column("min_principal_minor", sa.Integer(), nullable=False),
        sa.Column("max_principal_minor", sa.Integer(), nullable=False),
        sa.Column("annual_interest_basis_points", sa.Integer(), nullable=False),
        sa.Column("penalty_interest_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("term_days", sa.Integer(), nullable=False),
        sa.Column("payment_cadence_days", sa.Integer(), nullable=False),
        sa.Column("grace_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("minimum_credit_score", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("collateral_required", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("guarantor_allowed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("rule_version", sa.String(40), nullable=False, server_default="household-credit-v1"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("product_type IN ('emergency', 'consumer', 'relationship')", name="ck_credit_products_type"),
        sa.CheckConstraint("min_principal_minor > 0 AND max_principal_minor >= min_principal_minor", name="ck_credit_products_principal"),
        sa.CheckConstraint("annual_interest_basis_points BETWEEN 0 AND 10000", name="ck_credit_products_interest"),
        sa.CheckConstraint("penalty_interest_basis_points BETWEEN 0 AND 30000", name="ck_credit_products_penalty"),
        sa.CheckConstraint("term_days > 0 AND payment_cadence_days > 0 AND grace_days >= 0", name="ck_credit_products_term"),
        sa.CheckConstraint("minimum_credit_score BETWEEN 300 AND 850", name="ck_credit_products_score"),
        sa.CheckConstraint("collateral_required IN (0, 1) AND guarantor_allowed IN (0, 1)", name="ck_credit_products_security"),
        sa.CheckConstraint("status IN ('active', 'paused', 'retired')", name="ck_credit_products_status"),
    )
    op.create_table(
        "credit_profiles",
        sa.Column("resident_id", sa.Integer(), primary_key=True),
        sa.Column("credit_score", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("credit_limit_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outstanding_principal_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accrued_interest_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("delinquency_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("default_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_review_date", sa.String(10), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_credit_profiles_resident"),
        sa.CheckConstraint("credit_score BETWEEN 300 AND 850", name="ck_credit_profiles_score"),
        sa.CheckConstraint("credit_limit_minor >= 0", name="ck_credit_profiles_limit"),
        sa.CheckConstraint("outstanding_principal_minor >= 0 AND outstanding_principal_minor <= credit_limit_minor", name="ck_credit_profiles_principal"),
        sa.CheckConstraint("accrued_interest_minor >= 0", name="ck_credit_profiles_interest"),
        sa.CheckConstraint("delinquency_count >= 0 AND default_count >= 0", name="ck_credit_profiles_history"),
        sa.CheckConstraint("status IN ('active', 'restricted', 'defaulted', 'closed')", name="ck_credit_profiles_status"),
    )
    op.create_table(
        "credit_contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_key", sa.String(240), nullable=False, unique=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("borrower_resident_id", sa.Integer(), nullable=False),
        sa.Column("lender_actor_key", sa.String(160), nullable=False),
        sa.Column("guarantor_resident_id", sa.Integer(), nullable=True),
        sa.Column("principal_minor", sa.Integer(), nullable=False),
        sa.Column("outstanding_principal_minor", sa.Integer(), nullable=False),
        sa.Column("accrued_interest_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("annual_interest_basis_points", sa.Integer(), nullable=False),
        sa.Column("penalty_interest_basis_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("originated_at", sa.String(40), nullable=False),
        sa.Column("maturity_date", sa.String(10), nullable=False),
        sa.Column("next_due_date", sa.String(10), nullable=False),
        sa.Column("last_accrual_date", sa.String(10), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("collateral_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=False),
        sa.Column("defaulted_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["product_id"], ["credit_products.id"], ondelete="RESTRICT", name="fk_credit_contracts_product"),
        sa.ForeignKeyConstraint(["borrower_resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_credit_contracts_borrower"),
        sa.ForeignKeyConstraint(["guarantor_resident_id"], ["residents.id"], ondelete="SET NULL", name="fk_credit_contracts_guarantor"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT", name="fk_credit_contracts_ledger"),
        sa.CheckConstraint("principal_minor > 0", name="ck_credit_contracts_principal"),
        sa.CheckConstraint("outstanding_principal_minor >= 0 AND outstanding_principal_minor <= principal_minor", name="ck_credit_contracts_outstanding"),
        sa.CheckConstraint("accrued_interest_minor >= 0", name="ck_credit_contracts_interest_due"),
        sa.CheckConstraint("annual_interest_basis_points BETWEEN 0 AND 10000", name="ck_credit_contracts_interest"),
        sa.CheckConstraint("penalty_interest_basis_points BETWEEN 0 AND 30000", name="ck_credit_contracts_penalty"),
        sa.CheckConstraint("status IN ('active', 'late', 'defaulted', 'paid', 'restructured')", name="ck_credit_contracts_status"),
    )
    op.create_table(
        "credit_installments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("installment_key", sa.String(260), nullable=False, unique=True),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.String(10), nullable=False),
        sa.Column("principal_due_minor", sa.Integer(), nullable=False),
        sa.Column("interest_due_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_due_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("principal_paid_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interest_paid_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_paid_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="scheduled"),
        sa.Column("paid_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["contract_id"], ["credit_contracts.id"], ondelete="CASCADE", name="fk_credit_installments_contract"),
        sa.UniqueConstraint("contract_id", "sequence_number", name="uq_credit_installments_sequence"),
        sa.CheckConstraint("sequence_number > 0 AND principal_due_minor > 0", name="ck_credit_installments_principal"),
        sa.CheckConstraint("interest_due_minor >= 0 AND penalty_due_minor >= 0", name="ck_credit_installments_due"),
        sa.CheckConstraint("principal_paid_minor >= 0 AND principal_paid_minor <= principal_due_minor", name="ck_credit_installments_principal_paid"),
        sa.CheckConstraint("interest_paid_minor >= 0 AND interest_paid_minor <= interest_due_minor", name="ck_credit_installments_interest_paid"),
        sa.CheckConstraint("penalty_paid_minor >= 0 AND penalty_paid_minor <= penalty_due_minor", name="ck_credit_installments_penalty_paid"),
        sa.CheckConstraint("status IN ('scheduled', 'due', 'partial', 'paid', 'late', 'defaulted')", name="ck_credit_installments_status"),
    )
    op.create_table(
        "credit_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_key", sa.String(280), nullable=False, unique=True),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("installment_id", sa.Integer(), nullable=True),
        sa.Column("borrower_resident_id", sa.Integer(), nullable=False),
        sa.Column("principal_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interest_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("penalty_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_minor", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="posted"),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["contract_id"], ["credit_contracts.id"], ondelete="CASCADE", name="fk_credit_payments_contract"),
        sa.ForeignKeyConstraint(["installment_id"], ["credit_installments.id"], ondelete="SET NULL", name="fk_credit_payments_installment"),
        sa.ForeignKeyConstraint(["borrower_resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_credit_payments_borrower"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT", name="fk_credit_payments_ledger"),
        sa.CheckConstraint("principal_minor >= 0 AND interest_minor >= 0 AND penalty_minor >= 0", name="ck_credit_payments_components"),
        sa.CheckConstraint("total_minor > 0 AND total_minor = principal_minor + interest_minor + penalty_minor", name="ck_credit_payments_total"),
        sa.CheckConstraint("status IN ('posted', 'reversed')", name="ck_credit_payments_status"),
    )
    op.create_table(
        "credit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(300), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(24), nullable=False),
        sa.Column("score_before", sa.Integer(), nullable=False),
        sa.Column("score_after", sa.Integer(), nullable=False),
        sa.Column("credit_limit_before_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("credit_limit_after_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_credit_events_resident"),
        sa.ForeignKeyConstraint(["contract_id"], ["credit_contracts.id"], ondelete="SET NULL", name="fk_credit_events_contract"),
        sa.CheckConstraint("event_type IN ('profile_created', 'loan_originated', 'interest_accrued', 'payment', 'late', 'default', 'restructured', 'limit_review')", name="ck_credit_events_type"),
        sa.CheckConstraint("score_before BETWEEN 300 AND 850 AND score_after BETWEEN 300 AND 850", name="ck_credit_events_score"),
        sa.CheckConstraint("credit_limit_before_minor >= 0 AND credit_limit_after_minor >= 0", name="ck_credit_events_limit"),
    )
    op.create_table(
        "risk_pool_claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_key", sa.String(240), nullable=False, unique=True),
        sa.Column("shock_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("requested_minor", sa.Integer(), nullable=False),
        sa.Column("approved_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["shock_id"], ["economic_shocks.id"], ondelete="CASCADE", name="fk_risk_claims_shock"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_risk_claims_resident"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_risk_claims_ledger"),
        sa.CheckConstraint("requested_minor > 0 AND approved_minor >= 0 AND approved_minor <= requested_minor", name="ck_risk_claims_amount"),
        sa.CheckConstraint("status IN ('approved', 'partial', 'rejected')", name="ck_risk_claims_status"),
    )
    op.create_index("idx_savings_goals_resident", "savings_goals", ["resident_id", "status"])
    op.create_index("idx_economic_shocks_resident", "economic_shocks", ["resident_id", "occurred_at"])
    op.create_index("idx_credit_contracts_borrower", "credit_contracts", ["borrower_resident_id", "status"])
    op.create_index("idx_credit_installments_due", "credit_installments", ["status", "due_date"])
    op.create_index("idx_credit_payments_contract", "credit_payments", ["contract_id", "id"])
    op.create_index("idx_credit_events_resident", "credit_events", ["resident_id", "id"])


def downgrade() -> None:
    for table in (
        "risk_pool_claims",
        "credit_events",
        "credit_payments",
        "credit_installments",
        "credit_contracts",
        "credit_profiles",
        "credit_products",
        "economic_shocks",
        "household_risk_profiles",
        "savings_goals",
    ):
        op.drop_table(table)
    with op.batch_alter_table("household_budget_snapshots") as batch:
        batch.drop_constraint("ck_budget_snapshots_credit_nonnegative", type_="check")
        batch.create_check_constraint(
            "ck_budget_snapshots_credit_zero",
            "due_debt_minor = 0 AND borrowing_minor = 0",
        )
    with op.batch_alter_table("household_budget_profiles") as batch:
        batch.drop_constraint("ck_budget_profiles_credit_enabled", type_="check")
        batch.drop_constraint("ck_budget_profiles_credit_limit_nonnegative", type_="check")
        batch.drop_constraint("ck_budget_profiles_debt_nonnegative", type_="check")
        batch.create_check_constraint("ck_budget_profiles_credit_disabled", "credit_enabled = 0")
        batch.create_check_constraint("ck_budget_profiles_credit_limit_zero", "credit_limit_minor = 0")
        batch.create_check_constraint("ck_budget_profiles_debt_zero", "outstanding_debt_minor = 0")
