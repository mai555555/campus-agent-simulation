INGESTION_SQL = """
CREATE TABLE IF NOT EXISTS external_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT NOT NULL DEFAULT '',
    adapter_key TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    trust_prior REAL NOT NULL DEFAULT 0.5,
    allowed_event_types_json TEXT NOT NULL DEFAULT '[]',
    poll_interval_seconds INTEGER NOT NULL DEFAULT 3600,
    stale_after_seconds INTEGER NOT NULL DEFAULT 7200,
    timeout_seconds INTEGER NOT NULL DEFAULT 15,
    rate_limit INTEGER NOT NULL DEFAULT 60,
    license_note TEXT NOT NULL DEFAULT '',
    allowed_use TEXT NOT NULL DEFAULT 'simulation',
    retention_days INTEGER NOT NULL DEFAULT 30,
    sensitivity TEXT NOT NULL DEFAULT 'public',
    config_json TEXT NOT NULL DEFAULT '{}',
    last_success_at TEXT NOT NULL DEFAULT '',
    last_attempt_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (source_type IN ('rss', 'weather', 'api', 'file', 'manual', 'synthetic')),
    CHECK (enabled IN (0, 1)),
    CHECK (trust_prior BETWEEN 0 AND 1),
    CHECK (poll_interval_seconds > 0),
    CHECK (stale_after_seconds > 0),
    CHECK (timeout_seconds BETWEEN 1 AND 60),
    CHECK (rate_limit > 0),
    CHECK (retention_days >= 0),
    CHECK (sensitivity IN ('public', 'restricted', 'sensitive')),
    CHECK (status IN ('active', 'paused', 'retired'))
);

CREATE TABLE IF NOT EXISTS external_sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_key TEXT NOT NULL UNIQUE,
    source_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'running',
    request_count INTEGER NOT NULL DEFAULT 0,
    raw_count INTEGER NOT NULL DEFAULT 0,
    new_event_count INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    cursor_before TEXT NOT NULL DEFAULT '',
    cursor_after TEXT NOT NULL DEFAULT '',
    error_summary TEXT NOT NULL DEFAULT '',
    leader_key TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES external_sources(id) ON DELETE RESTRICT,
    CHECK (status IN ('running', 'success', 'partial', 'failed', 'dead_letter'))
);

CREATE TABLE IF NOT EXISTS external_raw_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    source_record_id TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    http_status INTEGER NOT NULL DEFAULT 200,
    content_type TEXT NOT NULL DEFAULT 'application/json',
    payload_json TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    sync_run_id INTEGER,
    validation_status TEXT NOT NULL DEFAULT 'valid',
    validation_errors_json TEXT NOT NULL DEFAULT '[]',
    duplicate_of_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES external_sources(id) ON DELETE RESTRICT,
    FOREIGN KEY (sync_run_id) REFERENCES external_sync_runs(id) ON DELETE SET NULL,
    FOREIGN KEY (duplicate_of_id) REFERENCES external_raw_observations(id) ON DELETE SET NULL,
    CHECK (validation_status IN ('valid', 'invalid', 'quarantined', 'duplicate')),
    UNIQUE (source_id, source_record_id, content_hash)
);

CREATE TABLE IF NOT EXISTS external_source_locks (
    source_id INTEGER PRIMARY KEY,
    owner_key TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES external_sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_external_raw_source_time
ON external_raw_observations(source_id, ingested_at, id);
CREATE INDEX IF NOT EXISTS idx_external_sync_source_time
ON external_sync_runs(source_id, started_at, id);
"""

NORMALIZATION_SQL = """
CREATE TABLE IF NOT EXISTS external_event_catalog (
    event_type TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    objective_impact_allowed INTEGER NOT NULL DEFAULT 0,
    high_impact INTEGER NOT NULL DEFAULT 0,
    schema_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (objective_impact_allowed IN (0, 1)),
    CHECK (high_impact IN (0, 1)),
    CHECK (status IN ('active', 'retired'))
);

CREATE TABLE IF NOT EXISTS external_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    raw_observation_id INTEGER NOT NULL,
    source_record_id TEXT NOT NULL,
    semantic_fingerprint TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    published_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT NOT NULL DEFAULT '',
    expires_at TEXT NOT NULL,
    geo_scope_json TEXT NOT NULL DEFAULT '{}',
    campus_scope_json TEXT NOT NULL DEFAULT '{}',
    affected_spaces_json TEXT NOT NULL DEFAULT '[]',
    affected_roles_json TEXT NOT NULL DEFAULT '[]',
    affected_organizations_json TEXT NOT NULL DEFAULT '[]',
    affected_economic_sectors_json TEXT NOT NULL DEFAULT '[]',
    magnitude REAL,
    direction TEXT NOT NULL DEFAULT 'neutral',
    unit TEXT NOT NULL DEFAULT '',
    severity REAL NOT NULL DEFAULT 0,
    novelty REAL NOT NULL DEFAULT 0,
    confidence REAL NOT NULL,
    verification_state TEXT NOT NULL DEFAULT 'unverified',
    payload_json TEXT NOT NULL DEFAULT '{}',
    transform_version TEXT NOT NULL,
    correction_of INTEGER,
    replaces_event_id INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_type) REFERENCES external_event_catalog(event_type) ON DELETE RESTRICT,
    FOREIGN KEY (source_id) REFERENCES external_sources(id) ON DELETE RESTRICT,
    FOREIGN KEY (raw_observation_id) REFERENCES external_raw_observations(id) ON DELETE RESTRICT,
    FOREIGN KEY (correction_of) REFERENCES external_events(id) ON DELETE SET NULL,
    FOREIGN KEY (replaces_event_id) REFERENCES external_events(id) ON DELETE SET NULL,
    CHECK (direction IN ('increase', 'decrease', 'neutral', 'mixed')),
    CHECK (severity BETWEEN 0 AND 1),
    CHECK (novelty BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (verification_state IN ('unverified', 'corroborated', 'verified',
        'conflicted', 'retracted')),
    CHECK (status IN ('active', 'superseded', 'retracted', 'expired'))
);

CREATE TABLE IF NOT EXISTS external_event_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_event_id INTEGER NOT NULL,
    to_event_id INTEGER NOT NULL,
    link_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_event_id) REFERENCES external_events(id) ON DELETE CASCADE,
    FOREIGN KEY (to_event_id) REFERENCES external_events(id) ON DELETE CASCADE,
    CHECK (link_type IN ('corroborates', 'possible_duplicate', 'conflicts',
        'corrects', 'replaces', 'retracts', 'contains')),
    CHECK (confidence BETWEEN 0 AND 1),
    UNIQUE (from_event_id, to_event_id, link_type)
);

CREATE INDEX IF NOT EXISTS idx_external_events_consumption
ON external_events(status, effective_from, expires_at, id);
CREATE INDEX IF NOT EXISTS idx_external_events_fingerprint
ON external_events(semantic_fingerprint, occurred_at, id);
"""

REPLAY_EXPOSURE_SQL = """
CREATE TABLE IF NOT EXISTS external_data_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_key TEXT NOT NULL UNIQUE,
    mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    event_catalog_version TEXT NOT NULL,
    transform_version TEXT NOT NULL,
    impact_rule_version TEXT NOT NULL,
    checksum TEXT NOT NULL DEFAULT '',
    sealed_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (mode IN ('live', 'snapshot', 'replay', 'synthetic')),
    CHECK (status IN ('draft', 'sealed', 'retired'))
);

CREATE TABLE IF NOT EXISTS external_snapshot_items (
    snapshot_id INTEGER NOT NULL,
    raw_observation_id INTEGER NOT NULL,
    external_event_id INTEGER NOT NULL,
    ordinal INTEGER NOT NULL,
    event_time TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, external_event_id),
    FOREIGN KEY (snapshot_id) REFERENCES external_data_snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (raw_observation_id) REFERENCES external_raw_observations(id) ON DELETE RESTRICT,
    FOREIGN KEY (external_event_id) REFERENCES external_events(id) ON DELETE RESTRICT,
    UNIQUE (snapshot_id, ordinal)
);

CREATE TABLE IF NOT EXISTS external_runtime_modes (
    branch_key TEXT PRIMARY KEY,
    mode TEXT NOT NULL DEFAULT 'live',
    snapshot_id INTEGER,
    replay_start_world_time TEXT NOT NULL DEFAULT '',
    replay_speed REAL NOT NULL DEFAULT 1,
    simulation_seed INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES external_data_snapshots(id) ON DELETE SET NULL,
    CHECK (mode IN ('live', 'snapshot', 'replay', 'synthetic')),
    CHECK (replay_speed > 0),
    CHECK (status IN ('active', 'paused'))
);

CREATE TABLE IF NOT EXISTS external_exposures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exposure_key TEXT NOT NULL UNIQUE,
    external_event_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    sender_resident_id INTEGER,
    parent_exposure_id INTEGER,
    scheduled_at TEXT NOT NULL,
    delivered_at TEXT NOT NULL DEFAULT '',
    noticed_at TEXT NOT NULL DEFAULT '',
    credibility_at_delivery REAL NOT NULL,
    distortion_json TEXT NOT NULL DEFAULT '{}',
    attention_cost REAL NOT NULL DEFAULT 0,
    response TEXT NOT NULL DEFAULT 'pending',
    memory_id INTEGER,
    correction_of_exposure_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (external_event_id) REFERENCES external_events(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (sender_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_exposure_id) REFERENCES external_exposures(id) ON DELETE SET NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE SET NULL,
    FOREIGN KEY (correction_of_exposure_id) REFERENCES external_exposures(id) ON DELETE SET NULL,
    CHECK (channel IN ('official', 'public_media', 'on_site',
        'organization', 'interpersonal', 'campus_newspaper')),
    CHECK (credibility_at_delivery BETWEEN 0 AND 1),
    CHECK (attention_cost >= 0),
    CHECK (response IN ('pending', 'believed', 'doubted', 'ignored', 'shared'))
);

CREATE TABLE IF NOT EXISTS external_replay_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_key TEXT NOT NULL UNIQUE,
    snapshot_id INTEGER NOT NULL,
    external_event_id INTEGER NOT NULL,
    branch_key TEXT NOT NULL,
    scheduled_world_time TEXT NOT NULL,
    delivered_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'scheduled',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES external_data_snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (external_event_id) REFERENCES external_events(id) ON DELETE RESTRICT,
    CHECK (status IN ('scheduled', 'delivered', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_external_exposures_delivery
ON external_exposures(response, scheduled_at, id);
CREATE INDEX IF NOT EXISTS idx_external_replay_due
ON external_replay_deliveries(status, scheduled_world_time, id);
"""

IMPACT_SQL = """
CREATE TABLE IF NOT EXISTS external_impact_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    impact_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    state_key TEXT NOT NULL,
    operation TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT '',
    min_confidence REAL NOT NULL DEFAULT 0.5,
    high_impact INTEGER NOT NULL DEFAULT 0,
    requires_verification INTEGER NOT NULL DEFAULT 0,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    rule_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_type) REFERENCES external_event_catalog(event_type) ON DELETE RESTRICT,
    CHECK (operation IN ('set', 'add', 'multiply', 'trigger_shock')),
    CHECK (min_confidence BETWEEN 0 AND 1),
    CHECK (high_impact IN (0, 1)),
    CHECK (requires_verification IN (0, 1)),
    CHECK (status IN ('active', 'paused', 'retired'))
);

CREATE TABLE IF NOT EXISTS external_event_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    impact_key TEXT NOT NULL UNIQUE,
    external_event_id INTEGER NOT NULL,
    impact_rule_id INTEGER NOT NULL,
    impact_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    state_key TEXT NOT NULL,
    operation TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT '',
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL,
    rule_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    world_event_id INTEGER,
    shock_instance_id INTEGER,
    reason TEXT NOT NULL DEFAULT '',
    previous_state_json TEXT NOT NULL DEFAULT '{}',
    applied_state_json TEXT NOT NULL DEFAULT '{}',
    applied_at TEXT NOT NULL DEFAULT '',
    reverted_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (external_event_id) REFERENCES external_events(id) ON DELETE RESTRICT,
    FOREIGN KEY (impact_rule_id) REFERENCES external_impact_rules(id) ON DELETE RESTRICT,
    FOREIGN KEY (world_event_id) REFERENCES world_event_stream(id) ON DELETE SET NULL,
    FOREIGN KEY (shock_instance_id) REFERENCES shock_instances(id) ON DELETE SET NULL,
    CHECK (operation IN ('set', 'add', 'multiply', 'trigger_shock')),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (status IN ('proposed', 'validated', 'applied', 'rejected', 'reverted'))
);

CREATE TABLE IF NOT EXISTS external_state_reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_key TEXT NOT NULL UNIQUE,
    external_event_id INTEGER NOT NULL,
    impact_id INTEGER NOT NULL,
    expected_state_json TEXT NOT NULL,
    actual_state_json TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (external_event_id) REFERENCES external_events(id) ON DELETE RESTRICT,
    FOREIGN KEY (impact_id) REFERENCES external_event_impacts(id) ON DELETE CASCADE,
    CHECK (status IN ('matched', 'mismatch', 'not_applicable'))
);

CREATE INDEX IF NOT EXISTS idx_external_impacts_application
ON external_event_impacts(status, starts_at, id);
"""

GOVERNANCE_SQL = """
CREATE TABLE IF NOT EXISTS external_governance_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_key TEXT NOT NULL UNIQUE,
    source_id INTEGER NOT NULL,
    license_approved INTEGER NOT NULL DEFAULT 0,
    purpose_approved INTEGER NOT NULL DEFAULT 0,
    retention_approved INTEGER NOT NULL DEFAULT 0,
    privacy_approved INTEGER NOT NULL DEFAULT 0,
    reviewer TEXT NOT NULL,
    decision TEXT NOT NULL DEFAULT 'pending',
    notes TEXT NOT NULL DEFAULT '',
    reviewed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES external_sources(id) ON DELETE RESTRICT,
    CHECK (license_approved IN (0, 1)),
    CHECK (purpose_approved IN (0, 1)),
    CHECK (retention_approved IN (0, 1)),
    CHECK (privacy_approved IN (0, 1)),
    CHECK (decision IN ('pending', 'approved', 'rejected', 'restricted'))
);

CREATE TABLE IF NOT EXISTS external_access_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_key TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (decision IN ('allowed', 'denied'))
);

CREATE TABLE IF NOT EXISTS external_runtime_health (
    branch_key TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'healthy',
    stale_source_count INTEGER NOT NULL DEFAULT 0,
    failed_source_count INTEGER NOT NULL DEFAULT 0,
    dead_letter_count INTEGER NOT NULL DEFAULT 0,
    last_evaluated_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    CHECK (status IN ('healthy', 'stale', 'external_data_degraded'))
);

CREATE TABLE IF NOT EXISTS external_snapshot_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_key TEXT NOT NULL UNIQUE,
    snapshot_id INTEGER NOT NULL,
    requested_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    manifest_json TEXT NOT NULL DEFAULT '{}',
    checksum TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (snapshot_id) REFERENCES external_data_snapshots(id) ON DELETE RESTRICT,
    CHECK (status IN ('pending', 'complete', 'failed'))
);

CREATE TABLE IF NOT EXISTS external_experiment_bindings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_key TEXT NOT NULL UNIQUE,
    branch_key TEXT NOT NULL,
    external_mode TEXT NOT NULL,
    snapshot_id INTEGER,
    event_catalog_version TEXT NOT NULL,
    transform_version TEXT NOT NULL,
    impact_rule_version TEXT NOT NULL,
    simulation_seed INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES external_data_snapshots(id) ON DELETE RESTRICT,
    CHECK (external_mode IN ('live', 'snapshot', 'replay', 'synthetic'))
);
"""
