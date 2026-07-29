"""Add labor, income, and distribution runtime.

Revision ID: 20260729_0012
Revises: 20260729_0011
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0012"
down_revision = "20260729_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labor_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("position_key", sa.String(120), nullable=False, unique=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("location", sa.String(120), nullable=False),
        sa.Column("allowed_actions_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("skill_dimension", sa.String(80), nullable=False),
        sa.Column("minimum_skill", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("hourly_wage_minor", sa.Integer(), nullable=False),
        sa.Column("standard_daily_minutes", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["campus_organizations.id"], ondelete="RESTRICT", name="fk_labor_positions_org"),
        sa.CheckConstraint("minimum_skill BETWEEN 0 AND 100", name="ck_labor_positions_skill"),
        sa.CheckConstraint("capacity > 0", name="ck_labor_positions_capacity"),
        sa.CheckConstraint("hourly_wage_minor > 0", name="ck_labor_positions_wage"),
        sa.CheckConstraint("standard_daily_minutes > 0", name="ck_labor_positions_minutes"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_labor_positions_status"),
    )
    op.create_table(
        "employment_contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_key", sa.String(160), nullable=False, unique=True),
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("contract_type", sa.String(24), nullable=False, server_default="part_time"),
        sa.Column("hourly_wage_minor", sa.Integer(), nullable=False),
        sa.Column("scheduled_daily_minutes", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.String(10), nullable=False),
        sa.Column("end_date", sa.String(10), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("skill_score_at_hire", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["labor_positions.id"], ondelete="RESTRICT", name="fk_employment_contracts_position"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_employment_contracts_resident"),
        sa.UniqueConstraint("position_id", "resident_id", name="uq_employment_contracts_position_resident"),
        sa.CheckConstraint("contract_type IN ('staff', 'part_time', 'assistantship', 'project')", name="ck_employment_contracts_type"),
        sa.CheckConstraint("hourly_wage_minor > 0", name="ck_employment_contracts_wage"),
        sa.CheckConstraint("scheduled_daily_minutes > 0", name="ck_employment_contracts_minutes"),
        sa.CheckConstraint("skill_score_at_hire BETWEEN 0 AND 100", name="ck_employment_contracts_skill"),
        sa.CheckConstraint("status IN ('active', 'suspended', 'ended')", name="ck_employment_contracts_status"),
    )
    op.create_table(
        "labor_shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shift_key", sa.String(180), nullable=False, unique=True),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.String(10), nullable=False),
        sa.Column("scheduled_minutes", sa.Integer(), nullable=False),
        sa.Column("evidenced_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payable_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gross_pay_minor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="scheduled"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("processed_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["contract_id"], ["employment_contracts.id"], ondelete="RESTRICT", name="fk_labor_shifts_contract"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_labor_shifts_ledger"),
        sa.UniqueConstraint("contract_id", "work_date", name="uq_labor_shifts_contract_date"),
        sa.CheckConstraint("scheduled_minutes > 0", name="ck_labor_shifts_scheduled"),
        sa.CheckConstraint("evidenced_minutes >= 0", name="ck_labor_shifts_evidenced"),
        sa.CheckConstraint("payable_minutes >= 0", name="ck_labor_shifts_payable"),
        sa.CheckConstraint("gross_pay_minor >= 0", name="ck_labor_shifts_pay"),
        sa.CheckConstraint("status IN ('scheduled', 'completed', 'partial', 'absent', 'blocked')", name="ck_labor_shifts_status"),
    )
    op.create_table(
        "income_programs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("program_key", sa.String(180), nullable=False, unique=True),
        sa.Column("program_type", sa.String(24), nullable=False),
        sa.Column("payer_actor_key", sa.String(160), nullable=False),
        sa.Column("recipient_resident_id", sa.Integer(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("cadence_days", sa.Integer(), nullable=False),
        sa.Column("next_due_date", sa.String(10), nullable=False),
        sa.Column("eligibility_rule", sa.String(160), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipient_resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_income_programs_resident"),
        sa.CheckConstraint("program_type IN ('scholarship', 'financial_aid', 'family_support', 'subsidy', 'reimbursement')", name="ck_income_programs_type"),
        sa.CheckConstraint("amount_minor > 0", name="ck_income_programs_amount"),
        sa.CheckConstraint("cadence_days > 0", name="ck_income_programs_cadence"),
        sa.CheckConstraint("status IN ('active', 'paused', 'ended')", name="ck_income_programs_status"),
    )
    op.create_table(
        "income_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_key", sa.String(200), nullable=False, unique=True),
        sa.Column("payment_type", sa.String(24), nullable=False),
        sa.Column("payer_actor_key", sa.String(160), nullable=False),
        sa.Column("recipient_actor_key", sa.String(160), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("labor_shift_id", sa.Integer(), nullable=True),
        sa.Column("income_program_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="posted"),
        sa.Column("ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.String(10), nullable=False),
        sa.Column("paid_at", sa.String(40), nullable=False, server_default=""),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["labor_shift_id"], ["labor_shifts.id"], ondelete="SET NULL", name="fk_income_payments_shift"),
        sa.ForeignKeyConstraint(["income_program_id"], ["income_programs.id"], ondelete="SET NULL", name="fk_income_payments_program"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_income_payments_ledger"),
        sa.CheckConstraint("payment_type IN ('wage', 'scholarship', 'financial_aid', 'family_support', 'subsidy', 'reimbursement')", name="ck_income_payments_type"),
        sa.CheckConstraint("amount_minor > 0", name="ck_income_payments_amount"),
        sa.CheckConstraint("status IN ('posted', 'blocked', 'cancelled')", name="ck_income_payments_status"),
    )
    op.create_table(
        "expense_obligations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("obligation_key", sa.String(180), nullable=False, unique=True),
        sa.Column("resident_id", sa.Integer(), nullable=False),
        sa.Column("expense_type", sa.String(24), nullable=False),
        sa.Column("recipient_actor_key", sa.String(160), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("cadence_days", sa.Integer(), nullable=False),
        sa.Column("next_due_date", sa.String(10), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("last_ledger_transaction_id", sa.Integer(), nullable=True),
        sa.Column("last_attempt_date", sa.String(10), nullable=False, server_default=""),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE", name="fk_expense_obligations_resident"),
        sa.ForeignKeyConstraint(["last_ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL", name="fk_expense_obligations_ledger"),
        sa.CheckConstraint("expense_type IN ('tuition', 'housing', 'meal_plan', 'transport', 'study', 'tax', 'fine')", name="ck_expense_obligations_type"),
        sa.CheckConstraint("amount_minor > 0", name="ck_expense_obligations_amount"),
        sa.CheckConstraint("cadence_days > 0", name="ck_expense_obligations_cadence"),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_expense_obligations_priority"),
        sa.CheckConstraint("status IN ('active', 'paused', 'ended')", name="ck_expense_obligations_status"),
    )
    op.create_index("idx_employment_contracts_resident", "employment_contracts", ["resident_id", "status"])
    op.create_index("idx_labor_shifts_status_date", "labor_shifts", ["status", "work_date", "id"])
    op.create_index("idx_income_programs_due", "income_programs", ["status", "next_due_date", "id"])
    op.create_index("idx_income_payments_recipient", "income_payments", ["recipient_actor_key", "id"])
    op.create_index("idx_expense_obligations_due", "expense_obligations", ["status", "next_due_date", "priority", "id"])


def downgrade() -> None:
    for table in (
        "expense_obligations",
        "income_payments",
        "income_programs",
        "labor_shifts",
        "employment_contracts",
        "labor_positions",
    ):
        op.drop_table(table)
