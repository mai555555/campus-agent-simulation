LONGITUDINAL_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS longitudinal_profiles (
    resident_id INTEGER PRIMARY KEY,
    current_stage_key TEXT NOT NULL,
    habit_state_json TEXT NOT NULL DEFAULT '{}',
    reputation_state_json TEXT NOT NULL DEFAULT '{}',
    social_position_json TEXT NOT NULL DEFAULT '{}',
    economic_position_json TEXT NOT NULL DEFAULT '{}',
    goal_state_json TEXT NOT NULL DEFAULT '{}',
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS life_course_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    stage_type TEXT NOT NULL,
    stage_label TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    trigger_type TEXT NOT NULL,
    trigger_id TEXT NOT NULL DEFAULT '',
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (stage_type IN ('entry', 'academic', 'employment', 'leave',
        'exchange', 'graduated', 'departed', 'campus_member')),
    CHECK (status IN ('active', 'completed'))
);

CREATE TABLE IF NOT EXISTS life_turning_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    point_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    category TEXT NOT NULL,
    evidence_layer TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    salience REAL NOT NULL,
    objective_evidence_count INTEGER NOT NULL DEFAULT 0,
    subjective_evidence_count INTEGER NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    cause_refs_json TEXT NOT NULL DEFAULT '[]',
    consequence_refs_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (category IN ('transition', 'achievement', 'failure', 'relationship',
        'economic', 'adaptation', 'norm', 'institution', 'recovery')),
    CHECK (evidence_layer IN ('individual', 'group_norm', 'formal_institution')),
    CHECK (salience BETWEEN 0 AND 100),
    CHECK (objective_evidence_count >= 0),
    CHECK (subjective_evidence_count >= 0),
    CHECK (status IN ('candidate', 'confirmed', 'revised', 'retracted')),
    CHECK (objective_evidence_count > 0 OR status = 'candidate')
);

CREATE TABLE IF NOT EXISTS path_dependency_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    from_type TEXT NOT NULL,
    from_id TEXT NOT NULL,
    to_type TEXT NOT NULL,
    to_id TEXT NOT NULL,
    mechanism TEXT NOT NULL,
    direction TEXT NOT NULL,
    strength REAL NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (direction IN ('enables', 'constrains', 'redirects', 'reinforces',
        'weakens', 'corrects')),
    CHECK (strength BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS longitudinal_aggregations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregation_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    window_type TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    source_cursors_json TEXT NOT NULL DEFAULT '{}',
    evidence_completeness REAL NOT NULL,
    mechanism_version TEXT NOT NULL DEFAULT 'longitudinal-runtime-v1',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (window_type IN ('day', 'week', 'month', 'life_to_date')),
    CHECK (evidence_completeness BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS trajectory_reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    expected_json TEXT NOT NULL DEFAULT '{}',
    actual_json TEXT NOT NULL DEFAULT '{}',
    checked_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (check_type IN ('stage_continuity', 'turning_point_evidence',
        'path_reference', 'profile_persistence')),
    CHECK (status IN ('passed', 'failed', 'not_applicable'))
);

CREATE INDEX IF NOT EXISTS idx_life_stages_resident_time
ON life_course_stages(resident_id, starts_at, id);
CREATE INDEX IF NOT EXISTS idx_turning_points_resident_time
ON life_turning_points(resident_id, occurred_at, id);
CREATE INDEX IF NOT EXISTS idx_path_links_resident_time
ON path_dependency_links(resident_id, occurred_at, id);
CREATE INDEX IF NOT EXISTS idx_longitudinal_aggregations_resident
ON longitudinal_aggregations(resident_id, window_end, id);
"""
