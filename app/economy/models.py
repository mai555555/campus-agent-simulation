from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

from app.db.metadata import metadata


economic_actors = Table(
    "economic_actors",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("actor_key", String(120), nullable=False, unique=True),
    Column("actor_type", String(32), nullable=False),
    Column("display_name", String(160), nullable=False),
    Column("resident_id", ForeignKey("residents.id", ondelete="RESTRICT"), unique=True),
    Column(
        "organization_id",
        ForeignKey("campus_organizations.id", ondelete="RESTRICT"),
        unique=True,
    ),
    Column("status", String(32), nullable=False, default="active"),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "actor_type IN ('person', 'production_service', 'organization', "
        "'public', 'external', 'system')",
        name="economic_actors_type_valid",
    ),
)

ledger_accounts = Table(
    "ledger_accounts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("account_key", String(180), nullable=False, unique=True),
    Column(
        "actor_id",
        ForeignKey("economic_actors.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("account_code", String(64), nullable=False),
    Column("account_type", String(32), nullable=False),
    Column("normal_side", String(8), nullable=False),
    Column("currency", String(32), nullable=False, default="campus_coin"),
    Column("balance_minor", BigInteger, nullable=False, default=0),
    Column("status", String(32), nullable=False, default="active"),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint(
        "actor_id",
        "account_code",
        "currency",
        name="uq_ledger_accounts_actor_code_currency",
    ),
    CheckConstraint(
        "account_type IN ('asset', 'liability', 'equity', 'income', 'expense')",
        name="ledger_accounts_type_valid",
    ),
    CheckConstraint(
        "normal_side IN ('debit', 'credit')",
        name="ledger_accounts_normal_side_valid",
    ),
)

ledger_transactions = Table(
    "ledger_transactions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("transaction_key", String(200), nullable=False, unique=True),
    Column("transaction_type", String(64), nullable=False),
    Column("status", String(16), nullable=False, default="posted"),
    Column("source_type", String(64), nullable=False),
    Column("source_id", String(120), nullable=False, default=""),
    Column(
        "action_execution_id",
        ForeignKey("world_action_executions.id", ondelete="SET NULL"),
    ),
    Column("world_event_id", ForeignKey("world_event_stream.id", ondelete="SET NULL")),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("rule_version", String(80), nullable=False, default="economy-ledger-v1"),
    Column("description", Text, nullable=False, default=""),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "status IN ('posted', 'reversed')",
        name="ledger_transactions_status_valid",
    ),
)

ledger_entries = Table(
    "ledger_entries",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "transaction_id",
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "account_id",
        ForeignKey("ledger_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("entry_side", String(8), nullable=False),
    Column("amount_minor", BigInteger, nullable=False),
    Column("currency", String(32), nullable=False, default="campus_coin"),
    Column("memo", Text, nullable=False, default=""),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "entry_side IN ('debit', 'credit')",
        name="ledger_entries_side_valid",
    ),
    CheckConstraint("amount_minor > 0", name="ledger_entries_amount_positive"),
)

ledger_authorization_rules = Table(
    "ledger_authorization_rules",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("rule_key", String(160), nullable=False, unique=True),
    Column("operation_type", String(32), nullable=False),
    Column("authority_actor_key", String(120), nullable=False),
    Column("counterparty_account_key", String(180), nullable=False),
    Column("counterparty_side", String(8), nullable=False),
    Column("max_amount_minor", BigInteger, nullable=False, default=0),
    Column("allowed_target_actor_types", Text, nullable=False, default="[]"),
    Column("status", String(32), nullable=False, default="active"),
    Column(
        "rule_version",
        String(80),
        nullable=False,
        default="economy-authorization-v1",
    ),
    Column("metadata_json", Text, nullable=False, default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "operation_type IN ('issue', 'destroy', 'external_inflow', 'reverse')",
        name="ledger_authorization_rules_operation_valid",
    ),
    CheckConstraint(
        "counterparty_side IN ('debit', 'credit')",
        name="ledger_authorization_rules_side_valid",
    ),
    CheckConstraint(
        "max_amount_minor >= 0",
        name="ledger_authorization_rules_max_nonnegative",
    ),
)

ledger_reversals = Table(
    "ledger_reversals",
    metadata,
    Column(
        "original_transaction_id",
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column(
        "reversal_transaction_id",
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    ),
    Column(
        "authorization_rule_id",
        ForeignKey("ledger_authorization_rules.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("reason", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

ledger_authorized_operations = Table(
    "ledger_authorized_operations",
    metadata,
    Column(
        "transaction_id",
        ForeignKey("ledger_transactions.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column(
        "authorization_rule_id",
        ForeignKey("ledger_authorization_rules.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("authority_actor_key", String(120), nullable=False),
    Column("operation_type", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint(
        "operation_type IN ('issue', 'destroy', 'external_inflow')",
        name="ledger_authorized_operations_type_valid",
    ),
)

ledger_audit_events = Table(
    "ledger_audit_events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_key", String(200), nullable=False, unique=True),
    Column("event_type", String(64), nullable=False),
    Column("severity", String(16), nullable=False),
    Column(
        "transaction_id",
        ForeignKey("ledger_transactions.id", ondelete="SET NULL"),
    ),
    Column("source_type", String(64), nullable=False, default="ledger_audit"),
    Column("source_id", String(120), nullable=False, default=""),
    Column("status", String(16), nullable=False, default="open"),
    Column("details_json", Text, nullable=False, default="{}"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("resolved_at", String(64), nullable=False, default=""),
    CheckConstraint(
        "severity IN ('info', 'warning', 'critical')",
        name="ledger_audit_events_severity_valid",
    ),
    CheckConstraint(
        "status IN ('open', 'resolved')",
        name="ledger_audit_events_status_valid",
    ),
)
