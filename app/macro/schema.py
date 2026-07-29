MACRO_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS macro_metric_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    stock_flow_type TEXT NOT NULL,
    aggregation_method TEXT NOT NULL,
    source_tables_json TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    rule_version TEXT NOT NULL DEFAULT 'macro-runtime-v1',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (category IN (
        'money', 'income', 'consumption', 'market', 'distribution',
        'public_service', 'policy', 'organization', 'welfare'
    )),
    CHECK (stock_flow_type IN ('stock', 'flow', 'ratio', 'index')),
    CHECK (aggregation_method IN (
        'sum', 'count', 'weighted_mean', 'ratio', 'gini'
    )),
    CHECK (status IN ('active', 'retired'))
);

CREATE TABLE IF NOT EXISTS macro_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_key TEXT NOT NULL UNIQUE,
    window_type TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    observed_through_event_id INTEGER NOT NULL DEFAULT 0,
    observed_through_transaction_id INTEGER NOT NULL DEFAULT 0,
    population INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'valid',
    state_fingerprint TEXT NOT NULL,
    rule_version TEXT NOT NULL DEFAULT 'macro-runtime-v1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (window_type, window_start, window_end),
    CHECK (window_type IN ('daily', 'weekly', 'manual')),
    CHECK (population >= 0),
    CHECK (status IN ('valid', 'warning', 'invalid'))
);

CREATE TABLE IF NOT EXISTS macro_metric_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    metric_definition_id INTEGER NOT NULL,
    group_type TEXT NOT NULL DEFAULT 'overall',
    group_key TEXT NOT NULL DEFAULT 'all',
    value REAL NOT NULL DEFAULT 0,
    numerator REAL NOT NULL DEFAULT 0,
    denominator REAL NOT NULL DEFAULT 0,
    sample_count INTEGER NOT NULL DEFAULT 0,
    quality_status TEXT NOT NULL DEFAULT 'verified',
    explanation TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (snapshot_id, metric_definition_id, group_type, group_key),
    FOREIGN KEY (snapshot_id) REFERENCES macro_snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (metric_definition_id) REFERENCES macro_metric_definitions(id) ON DELETE RESTRICT,
    CHECK (group_type IN ('overall', 'role', 'income_group', 'actor_type')),
    CHECK (sample_count >= 0),
    CHECK (quality_status IN ('verified', 'estimated', 'insufficient', 'invalid'))
);

CREATE TABLE IF NOT EXISTS macro_metric_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_value_id INTEGER NOT NULL,
    source_table TEXT NOT NULL,
    source_id TEXT NOT NULL,
    component_key TEXT NOT NULL DEFAULT '',
    contribution REAL NOT NULL DEFAULT 0,
    weight REAL NOT NULL DEFAULT 1,
    occurred_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (metric_value_id, source_table, source_id, component_key),
    FOREIGN KEY (metric_value_id) REFERENCES macro_metric_values(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS macro_reconciliation_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    check_key TEXT NOT NULL,
    check_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    expected_value REAL NOT NULL DEFAULT 0,
    actual_value REAL NOT NULL DEFAULT 0,
    difference REAL NOT NULL DEFAULT 0,
    source_tables_json TEXT NOT NULL DEFAULT '[]',
    details_json TEXT NOT NULL DEFAULT '{}',
    checked_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (snapshot_id, check_key),
    FOREIGN KEY (snapshot_id) REFERENCES macro_snapshots(id) ON DELETE CASCADE,
    CHECK (check_type IN (
        'ledger', 'projection', 'inventory', 'credit', 'coverage', 'components'
    )),
    CHECK (severity IN ('info', 'warning', 'critical')),
    CHECK (status IN ('passed', 'warning', 'failed', 'not_applicable'))
);

CREATE INDEX IF NOT EXISTS ix_macro_snapshots_window
ON macro_snapshots(window_type, window_start, id);
CREATE INDEX IF NOT EXISTS ix_macro_values_snapshot
ON macro_metric_values(snapshot_id, group_type, group_key);
CREATE INDEX IF NOT EXISTS ix_macro_components_value
ON macro_metric_components(metric_value_id, source_table, source_id);
CREATE INDEX IF NOT EXISTS ix_macro_checks_snapshot
ON macro_reconciliation_checks(snapshot_id, status, severity);
"""
