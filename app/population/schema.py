POPULATION_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS population_profiles (
    resident_id INTEGER PRIMARY KEY,
    lifecycle_status TEXT NOT NULL DEFAULT 'active',
    lifecycle_stage TEXT NOT NULL DEFAULT 'campus_member',
    origin_type TEXT NOT NULL DEFAULT 'existing',
    entry_reason TEXT NOT NULL DEFAULT '',
    entered_at TEXT NOT NULL,
    expected_exit_at TEXT NOT NULL DEFAULT '',
    exited_at TEXT NOT NULL DEFAULT '',
    exit_reason TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (lifecycle_status IN ('pending', 'active', 'leave', 'departed')),
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS population_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    resident_id INTEGER,
    effective_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    source_type TEXT NOT NULL DEFAULT 'internal',
    source_id TEXT NOT NULL DEFAULT '',
    branch_key TEXT NOT NULL DEFAULT 'main',
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    applied_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (event_type IN ('new_student', 'exchange_arrival', 'graduation',
        'transfer_program', 'leave_of_absence', 'resume_study', 'withdrawal',
        'teacher_transfer', 'job_change', 'organization_join',
        'organization_leave', 'leadership_change', 'dorm_move',
        'external_opportunity', 'family_support_change', 'city_migration')),
    CHECK (status IN ('scheduled', 'applied', 'failed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS resident_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    role_type TEXT NOT NULL,
    role_key TEXT NOT NULL,
    organization_id INTEGER,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    source_event_id INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE SET NULL,
    FOREIGN KEY (source_event_id) REFERENCES population_events(id) ON DELETE SET NULL,
    CHECK (role_type IN ('campus', 'academic', 'employment', 'organization')),
    CHECK (status IN ('active', 'ended'))
);

CREATE TABLE IF NOT EXISTS resident_residency_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    residence_type TEXT NOT NULL,
    location TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    source_event_id INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (source_event_id) REFERENCES population_events(id) ON DELETE SET NULL,
    CHECK (status IN ('active', 'ended'))
);

CREATE TABLE IF NOT EXISTS membership_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transition_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    transition_type TEXT NOT NULL,
    role_before TEXT NOT NULL DEFAULT '',
    role_after TEXT NOT NULL DEFAULT '',
    source_event_id INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    FOREIGN KEY (source_event_id) REFERENCES population_events(id) ON DELETE RESTRICT,
    CHECK (transition_type IN ('join', 'leave', 'role_change', 'departure'))
);

CREATE TABLE IF NOT EXISTS population_effects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    effect_key TEXT NOT NULL UNIQUE,
    population_event_id INTEGER NOT NULL,
    effect_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    magnitude REAL NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL DEFAULT '{}',
    recorded_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (population_event_id) REFERENCES population_events(id) ON DELETE CASCADE,
    CHECK (effect_type IN ('resource_demand', 'organization_memory',
        'relationship_network', 'economic_participation', 'opportunity_access'))
);

CREATE INDEX IF NOT EXISTS idx_population_events_due
ON population_events(status, effective_at, id);
CREATE INDEX IF NOT EXISTS idx_population_profiles_status
ON population_profiles(lifecycle_status, resident_id);
CREATE INDEX IF NOT EXISTS idx_resident_roles_current
ON resident_role_assignments(resident_id, status, role_type);
CREATE INDEX IF NOT EXISTS idx_residency_periods_current
ON resident_residency_periods(resident_id, status);
CREATE INDEX IF NOT EXISTS idx_membership_transitions_resident
ON membership_transitions(resident_id, occurred_at, id);
"""
