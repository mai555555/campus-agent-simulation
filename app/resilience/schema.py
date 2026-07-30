RESILIENCE_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS shock_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shock_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    shock_type TEXT NOT NULL,
    default_duration_minutes INTEGER NOT NULL,
    impact_template_json TEXT NOT NULL DEFAULT '[]',
    recovery_template_json TEXT NOT NULL DEFAULT '{}',
    severity_range_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (shock_type IN ('weather', 'power', 'facility', 'supply', 'safety', 'exam', 'public_health', 'employment', 'price', 'income', 'policy')),
    CHECK (default_duration_minutes > 0),
    CHECK (status IN ('active', 'paused', 'retired')),
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS shock_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_key TEXT NOT NULL UNIQUE,
    definition_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    branch_key TEXT NOT NULL DEFAULT 'main',
    random_seed INTEGER NOT NULL DEFAULT 0,
    severity REAL NOT NULL,
    scope_json TEXT NOT NULL DEFAULT '{}',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'scheduled',
    scheduled_at TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT '',
    expected_end_at TEXT NOT NULL,
    recovery_started_at TEXT NOT NULL DEFAULT '',
    resolved_at TEXT NOT NULL DEFAULT '',
    replay_of_instance_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (definition_id) REFERENCES shock_definitions(id) ON DELETE RESTRICT,
    FOREIGN KEY (replay_of_instance_id) REFERENCES shock_instances(id) ON DELETE SET NULL,
    CHECK (source_type IN ('internal', 'synthetic', 'external_mapped', 'replay')),
    CHECK (severity BETWEEN 0 AND 1),
    CHECK (status IN ('scheduled', 'active', 'recovering', 'resolved', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS shock_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    impact_key TEXT NOT NULL UNIQUE,
    shock_instance_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    dimension TEXT NOT NULL,
    magnitude REAL NOT NULL,
    unit TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    previous_state_json TEXT NOT NULL DEFAULT '{}',
    applied_state_json TEXT NOT NULL DEFAULT '{}',
    applied_at TEXT NOT NULL DEFAULT '',
    reverted_at TEXT NOT NULL DEFAULT '',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shock_instance_id) REFERENCES shock_instances(id) ON DELETE CASCADE,
    CHECK (target_type IN ('space', 'resource', 'market', 'sector', 'role', 'organization', 'campus')),
    CHECK (dimension IN ('official_access', 'physical_access', 'travel_cost', 'service_capacity', 'resource_availability', 'supply', 'price', 'income', 'employment', 'health_risk', 'policy')),
    CHECK (status IN ('pending', 'active', 'reverted', 'failed'))
);

CREATE TABLE IF NOT EXISTS resident_shock_exposures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exposure_key TEXT NOT NULL UNIQUE,
    shock_instance_id INTEGER NOT NULL,
    impact_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    exposure_level REAL NOT NULL,
    vulnerability REAL NOT NULL,
    coping_capacity REAL NOT NULL,
    consequence_score REAL NOT NULL,
    consequence_json TEXT NOT NULL DEFAULT '{}',
    observed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shock_instance_id) REFERENCES shock_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (impact_id) REFERENCES shock_impacts(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (exposure_level BETWEEN 0 AND 1),
    CHECK (vulnerability BETWEEN 0 AND 1),
    CHECK (coping_capacity BETWEEN 0 AND 1),
    CHECK (consequence_score >= 0)
);

CREATE TABLE IF NOT EXISTS recovery_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_key TEXT NOT NULL UNIQUE,
    shock_instance_id INTEGER NOT NULL,
    organization_id INTEGER,
    responsible_resident_id INTEGER,
    action_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    resource_cost_minor INTEGER NOT NULL DEFAULT 0,
    effectiveness REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    planned_at TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT '',
    completed_at TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shock_instance_id) REFERENCES shock_instances(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE SET NULL,
    FOREIGN KEY (responsible_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (action_type IN ('repair', 'reopen', 'reroute', 'substitute_service', 'restock', 'aid', 'communication', 'policy_adjustment')),
    CHECK (resource_cost_minor >= 0),
    CHECK (effectiveness BETWEEN 0 AND 1),
    CHECK (status IN ('planned', 'active', 'completed', 'failed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS shock_state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shock_instance_id INTEGER NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    transitioned_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shock_instance_id) REFERENCES shock_instances(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_shock_instances_status
ON shock_instances(status, scheduled_at, expected_end_at);

CREATE INDEX IF NOT EXISTS idx_shock_impacts_instance
ON shock_impacts(shock_instance_id, status, id);

CREATE INDEX IF NOT EXISTS idx_resident_shock_exposures_resident
ON resident_shock_exposures(resident_id, observed_at, id);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_instance
ON recovery_actions(shock_instance_id, status, id);
"""

