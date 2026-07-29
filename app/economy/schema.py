"""SQLite-compatible schema used by focused runtime tests."""

ECONOMY_FOUNDATION_SQL = """
CREATE TABLE IF NOT EXISTS economic_actors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_key TEXT NOT NULL UNIQUE,
    actor_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    resident_id INTEGER UNIQUE,
    organization_id INTEGER UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    CHECK (actor_type IN (
        'person', 'production_service', 'organization', 'public', 'external', 'system'
    ))
);

CREATE TABLE IF NOT EXISTS ledger_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_key TEXT NOT NULL UNIQUE,
    actor_id INTEGER NOT NULL,
    account_code TEXT NOT NULL,
    account_type TEXT NOT NULL,
    normal_side TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'campus_coin',
    balance_minor INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES economic_actors(id) ON DELETE RESTRICT,
    UNIQUE (actor_id, account_code, currency),
    CHECK (account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    CHECK (normal_side IN ('debit', 'credit'))
);

CREATE TABLE IF NOT EXISTS ledger_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_key TEXT NOT NULL UNIQUE,
    transaction_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'posted',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    action_execution_id INTEGER,
    world_event_id INTEGER,
    occurred_at TEXT NOT NULL,
    rule_version TEXT NOT NULL DEFAULT 'economy-ledger-v1',
    description TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (action_execution_id) REFERENCES world_action_executions(id) ON DELETE SET NULL,
    FOREIGN KEY (world_event_id) REFERENCES world_event_stream(id) ON DELETE SET NULL,
    CHECK (status IN ('posted', 'reversed'))
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    entry_side TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'campus_coin',
    memo TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    FOREIGN KEY (account_id) REFERENCES ledger_accounts(id) ON DELETE RESTRICT,
    CHECK (entry_side IN ('debit', 'credit')),
    CHECK (amount_minor > 0)
);

CREATE TABLE IF NOT EXISTS ledger_authorization_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    operation_type TEXT NOT NULL,
    authority_actor_key TEXT NOT NULL,
    counterparty_account_key TEXT NOT NULL,
    counterparty_side TEXT NOT NULL,
    max_amount_minor INTEGER NOT NULL DEFAULT 0,
    allowed_target_actor_types TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    rule_version TEXT NOT NULL DEFAULT 'economy-authorization-v1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (operation_type IN (
        'issue', 'destroy', 'external_inflow', 'reverse'
    )),
    CHECK (counterparty_side IN ('debit', 'credit')),
    CHECK (max_amount_minor >= 0)
);

CREATE TABLE IF NOT EXISTS ledger_reversals (
    original_transaction_id INTEGER PRIMARY KEY,
    reversal_transaction_id INTEGER NOT NULL UNIQUE,
    authorization_rule_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (original_transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    FOREIGN KEY (reversal_transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    FOREIGN KEY (authorization_rule_id) REFERENCES ledger_authorization_rules(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS ledger_authorized_operations (
    transaction_id INTEGER PRIMARY KEY,
    authorization_rule_id INTEGER NOT NULL,
    authority_actor_key TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    FOREIGN KEY (authorization_rule_id) REFERENCES ledger_authorization_rules(id) ON DELETE RESTRICT,
    CHECK (operation_type IN ('issue', 'destroy', 'external_inflow'))
);

CREATE TABLE IF NOT EXISTS ledger_audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    transaction_id INTEGER,
    source_type TEXT NOT NULL DEFAULT 'ledger_audit',
    source_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (severity IN ('info', 'warning', 'critical')),
    CHECK (status IN ('open', 'resolved'))
);

CREATE INDEX IF NOT EXISTS ix_economic_actors_type_status
ON economic_actors(actor_type, status);
CREATE INDEX IF NOT EXISTS ix_ledger_accounts_actor
ON ledger_accounts(actor_id, account_code);
CREATE INDEX IF NOT EXISTS ix_ledger_transactions_source
ON ledger_transactions(source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_ledger_transactions_occurred
ON ledger_transactions(occurred_at, id);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_transaction
ON ledger_entries(transaction_id, id);
CREATE INDEX IF NOT EXISTS ix_ledger_entries_account
ON ledger_entries(account_id, id);
CREATE INDEX IF NOT EXISTS ix_ledger_authorization_rules_operation
ON ledger_authorization_rules(operation_type, status);
CREATE INDEX IF NOT EXISTS ix_ledger_audit_events_status
ON ledger_audit_events(status, severity, id);
"""
