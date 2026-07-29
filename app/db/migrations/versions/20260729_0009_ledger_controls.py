"""Add authorized balance operations, reversals, and ledger audit events.

Revision ID: 20260729_0009
Revises: 20260729_0008
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0009"
down_revision = "20260729_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ledger_authorization_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_key", sa.String(length=160), nullable=False, unique=True),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("authority_actor_key", sa.String(length=120), nullable=False),
        sa.Column("counterparty_account_key", sa.String(length=180), nullable=False),
        sa.Column("counterparty_side", sa.String(length=8), nullable=False),
        sa.Column("max_amount_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "allowed_target_actor_types",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "rule_version",
            sa.String(length=80),
            nullable=False,
            server_default="economy-authorization-v1",
        ),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
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
            "operation_type IN ('issue', 'destroy', 'external_inflow', 'reverse')",
            name="ck_ledger_authorization_rules_operation_valid",
        ),
        sa.CheckConstraint(
            "counterparty_side IN ('debit', 'credit')",
            name="ck_ledger_authorization_rules_side_valid",
        ),
        sa.CheckConstraint(
            "max_amount_minor >= 0",
            name="ck_ledger_authorization_rules_max_nonnegative",
        ),
    )
    op.create_index(
        "ix_ledger_authorization_rules_operation",
        "ledger_authorization_rules",
        ["operation_type", "status"],
    )

    op.create_table(
        "ledger_reversals",
        sa.Column("original_transaction_id", sa.Integer(), primary_key=True),
        sa.Column("reversal_transaction_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("authorization_rule_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["original_transaction_id"],
            ["ledger_transactions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reversal_transaction_id"],
            ["ledger_transactions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["authorization_rule_id"],
            ["ledger_authorization_rules.id"],
            ondelete="RESTRICT",
        ),
    )

    op.create_table(
        "ledger_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(length=200), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("transaction_id", sa.Integer()),
        sa.Column(
            "source_type",
            sa.String(length=64),
            nullable=False,
            server_default="ledger_audit",
        ),
        sa.Column("source_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.String(length=64), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="ck_ledger_audit_events_severity_valid",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'resolved')",
            name="ck_ledger_audit_events_status_valid",
        ),
    )
    op.create_index(
        "ix_ledger_audit_events_status",
        "ledger_audit_events",
        ["status", "severity", "id"],
    )
    op.create_table(
        "ledger_authorized_operations",
        sa.Column("transaction_id", sa.Integer(), primary_key=True),
        sa.Column("authorization_rule_id", sa.Integer(), nullable=False),
        sa.Column("authority_actor_key", sa.String(length=120), nullable=False),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["ledger_transactions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["authorization_rule_id"],
            ["ledger_authorization_rules.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "operation_type IN ('issue', 'destroy', 'external_inflow')",
            name="ck_ledger_authorized_operations_type_valid",
        ),
    )


def downgrade() -> None:
    op.drop_table("ledger_authorized_operations")
    op.drop_index("ix_ledger_audit_events_status", table_name="ledger_audit_events")
    op.drop_table("ledger_audit_events")
    op.drop_table("ledger_reversals")
    op.drop_index(
        "ix_ledger_authorization_rules_operation",
        table_name="ledger_authorization_rules",
    )
    op.drop_table("ledger_authorization_rules")
