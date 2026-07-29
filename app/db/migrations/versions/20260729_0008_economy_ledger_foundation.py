"""Add auditable economic actors and a balanced money ledger.

Revision ID: 20260729_0008
Revises: 20260729_0007
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0008"
down_revision = "20260729_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "economic_actors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("resident_id", sa.Integer(), unique=True),
        sa.Column("organization_id", sa.Integer(), unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["campus_organizations.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "actor_type IN ('person', 'production_service', 'organization', "
            "'public', 'external', 'system')",
            name="ck_economic_actors_type_valid",
        ),
    )
    op.create_index(
        "ix_economic_actors_type_status",
        "economic_actors",
        ["actor_type", "status"],
    )

    op.create_table(
        "ledger_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_key", sa.String(length=180), nullable=False, unique=True),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("account_code", sa.String(length=64), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("normal_side", sa.String(length=8), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=32),
            nullable=False,
            server_default="campus_coin",
        ),
        sa.Column("balance_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(
            ["actor_id"], ["economic_actors.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "actor_id",
            "account_code",
            "currency",
            name="uq_ledger_accounts_actor_code_currency",
        ),
        sa.CheckConstraint(
            "account_type IN ('asset', 'liability', 'equity', 'income', 'expense')",
            name="ck_ledger_accounts_type_valid",
        ),
        sa.CheckConstraint(
            "normal_side IN ('debit', 'credit')",
            name="ck_ledger_accounts_normal_side_valid",
        ),
    )
    op.create_index(
        "ix_ledger_accounts_actor",
        "ledger_accounts",
        ["actor_id", "account_code"],
    )

    op.create_table(
        "ledger_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_key", sa.String(length=200), nullable=False, unique=True),
        sa.Column("transaction_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="posted"),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("action_execution_id", sa.Integer()),
        sa.Column("world_event_id", sa.Integer()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "rule_version",
            sa.String(length=80),
            nullable=False,
            server_default="economy-ledger-v1",
        ),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["action_execution_id"],
            ["world_action_executions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["world_event_id"], ["world_event_stream.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "status IN ('posted', 'reversed')",
            name="ck_ledger_transactions_status_valid",
        ),
    )
    op.create_index(
        "ix_ledger_transactions_source",
        "ledger_transactions",
        ["source_type", "source_id"],
    )
    op.create_index(
        "ix_ledger_transactions_occurred",
        "ledger_transactions",
        ["occurred_at", "id"],
    )

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("entry_side", sa.String(length=8), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=32),
            nullable=False,
            server_default="campus_coin",
        ),
        sa.Column("memo", sa.Text(), nullable=False, server_default=""),
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
            ["account_id"], ["ledger_accounts.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "entry_side IN ('debit', 'credit')",
            name="ck_ledger_entries_side_valid",
        ),
        sa.CheckConstraint(
            "amount_minor > 0",
            name="ck_ledger_entries_amount_positive",
        ),
    )
    op.create_index(
        "ix_ledger_entries_transaction",
        "ledger_entries",
        ["transaction_id", "id"],
    )
    op.create_index(
        "ix_ledger_entries_account",
        "ledger_entries",
        ["account_id", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ledger_entries_account", table_name="ledger_entries")
    op.drop_index("ix_ledger_entries_transaction", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index(
        "ix_ledger_transactions_occurred", table_name="ledger_transactions"
    )
    op.drop_index("ix_ledger_transactions_source", table_name="ledger_transactions")
    op.drop_table("ledger_transactions")
    op.drop_index("ix_ledger_accounts_actor", table_name="ledger_accounts")
    op.drop_table("ledger_accounts")
    op.drop_index("ix_economic_actors_type_status", table_name="economic_actors")
    op.drop_table("economic_actors")
