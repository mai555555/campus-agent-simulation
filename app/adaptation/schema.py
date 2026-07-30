CONSTRAINT_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS constraint_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    constraint_layer TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL DEFAULT '*',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    enforcement_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    effective_from TEXT NOT NULL DEFAULT '',
    effective_to TEXT NOT NULL DEFAULT '',
    created_by_type TEXT NOT NULL DEFAULT 'system',
    created_by_id TEXT NOT NULL DEFAULT '',
    source_norm_id INTEGER,
    parent_rule_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_rule_id) REFERENCES constraint_rules(id) ON DELETE SET NULL,
    CHECK (constraint_layer IN ('physical', 'institutional', 'service', 'capacity', 'enforcement')),
    CHECK (status IN ('draft', 'active', 'paused', 'retired', 'superseded')),
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS constraint_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_key TEXT NOT NULL UNIQUE,
    branch_key TEXT NOT NULL DEFAULT 'main',
    tick_number INTEGER NOT NULL DEFAULT 0,
    resident_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    action TEXT NOT NULL,
    physically_possible INTEGER NOT NULL,
    officially_permitted INTEGER NOT NULL,
    service_available INTEGER NOT NULL,
    occupancy INTEGER NOT NULL DEFAULT 0,
    capacity INTEGER NOT NULL DEFAULT 0,
    capacity_pressure REAL NOT NULL DEFAULT 0,
    expected_time_minutes REAL NOT NULL DEFAULT 0,
    expected_cost_minor INTEGER NOT NULL DEFAULT 0,
    success_probability REAL NOT NULL,
    detection_probability REAL NOT NULL,
    harm_probability REAL NOT NULL,
    expected_sanction_minor INTEGER NOT NULL DEFAULT 0,
    selected_response TEXT NOT NULL,
    rule_versions_json TEXT NOT NULL DEFAULT '{}',
    evidence_json TEXT NOT NULL DEFAULT '{}',
    evaluated_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (tick_number >= 0 AND occupancy >= 0 AND capacity >= 0),
    CHECK (physically_possible IN (0, 1)),
    CHECK (officially_permitted IN (0, 1)),
    CHECK (service_available IN (0, 1)),
    CHECK (capacity_pressure >= 0),
    CHECK (expected_time_minutes >= 0 AND expected_cost_minor >= 0),
    CHECK (success_probability BETWEEN 0 AND 1),
    CHECK (detection_probability BETWEEN 0 AND 1),
    CHECK (harm_probability BETWEEN 0 AND 1),
    CHECK (expected_sanction_minor >= 0),
    CHECK (selected_response IN ('enter', 'queue', 'bypass', 'request_exception', 'abandon', 'blocked'))
);

CREATE TABLE IF NOT EXISTS boundary_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_key TEXT NOT NULL UNIQUE,
    evaluation_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    strategy TEXT NOT NULL,
    status TEXT NOT NULL,
    succeeded INTEGER NOT NULL DEFAULT 0,
    detected INTEGER NOT NULL DEFAULT 0,
    harmed INTEGER NOT NULL DEFAULT 0,
    actual_cost_minor INTEGER NOT NULL DEFAULT 0,
    sanction_minor INTEGER NOT NULL DEFAULT 0,
    institutional_case_id INTEGER,
    started_at TEXT NOT NULL,
    resolved_at TEXT NOT NULL DEFAULT '',
    outcome_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluation_id) REFERENCES constraint_evaluations(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (strategy IN ('enter', 'queue', 'bypass', 'request_exception', 'abandon', 'blocked')),
    CHECK (status IN ('planned', 'pending', 'succeeded', 'failed', 'abandoned')),
    CHECK (succeeded IN (0, 1) AND detected IN (0, 1) AND harmed IN (0, 1)),
    CHECK (actual_cost_minor >= 0 AND sanction_minor >= 0)
);

CREATE TABLE IF NOT EXISTS constraint_consequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    consequence_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    magnitude REAL NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'score',
    source_event_id INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES boundary_attempts(id) ON DELETE CASCADE,
    CHECK (consequence_type IN ('admission', 'delay', 'detection', 'sanction', 'injury', 'stress', 'reputation', 'externality'))
);

CREATE INDEX IF NOT EXISTS idx_constraint_evaluations_resident_tick
ON constraint_evaluations(resident_id, tick_number, id);

CREATE INDEX IF NOT EXISTS idx_constraint_evaluations_target
ON constraint_evaluations(target_type, target_key, evaluated_at);

CREATE INDEX IF NOT EXISTS idx_boundary_attempts_resident
ON boundary_attempts(resident_id, started_at, id);

CREATE INDEX IF NOT EXISTS idx_constraint_consequences_attempt
ON constraint_consequences(attempt_id, id);
"""


LEARNING_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS experience_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experience_key TEXT NOT NULL UNIQUE,
    branch_key TEXT NOT NULL DEFAULT 'main',
    tick_number INTEGER NOT NULL DEFAULT 0,
    resident_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    objective_summary TEXT NOT NULL,
    outcome TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (tick_number >= 0),
    CHECK (source_type IN ('world_event', 'boundary_attempt', 'legacy_memory', 'observation', 'information', 'manual'))
);

CREATE TABLE IF NOT EXISTS adaptive_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    experience_id INTEGER NOT NULL,
    memory_type TEXT NOT NULL,
    interpretation TEXT NOT NULL,
    confidence REAL NOT NULL,
    salience REAL NOT NULL,
    valence REAL NOT NULL DEFAULT 0,
    strength REAL NOT NULL DEFAULT 1,
    retrieval_count INTEGER NOT NULL DEFAULT 0,
    last_retrieved_at TEXT NOT NULL DEFAULT '',
    last_reinforced_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    superseded_by_id INTEGER,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (experience_id) REFERENCES experience_records(id) ON DELETE CASCADE,
    FOREIGN KEY (superseded_by_id) REFERENCES adaptive_memories(id) ON DELETE SET NULL,
    CHECK (memory_type IN ('episodic', 'semantic', 'relationship', 'strategy', 'working')),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (salience BETWEEN 0 AND 100),
    CHECK (valence BETWEEN -100 AND 100),
    CHECK (strength BETWEEN 0 AND 1),
    CHECK (retrieval_count >= 0),
    CHECK (status IN ('active', 'weakened', 'superseded', 'forgotten'))
);

CREATE TABLE IF NOT EXISTS memory_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    revision_type TEXT NOT NULL,
    previous_confidence REAL NOT NULL,
    new_confidence REAL NOT NULL,
    previous_interpretation TEXT NOT NULL,
    new_interpretation TEXT NOT NULL,
    evidence_experience_id INTEGER,
    reason TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES adaptive_memories(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_experience_id) REFERENCES experience_records(id) ON DELETE SET NULL,
    CHECK (revision_type IN ('reinforce', 'weaken', 'correct', 'generalize', 'forget')),
    CHECK (previous_confidence BETWEEN 0 AND 1),
    CHECK (new_confidence BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS strategy_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resident_id INTEGER NOT NULL,
    strategy_key TEXT NOT NULL,
    context_key TEXT NOT NULL,
    expected_utility REAL NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0.25,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    observation_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    learned_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    rule_version TEXT NOT NULL DEFAULT 'adaptive-learning-v1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resident_id, strategy_key, context_key),
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (success_count >= 0 AND failure_count >= 0 AND observation_count >= 0),
    CHECK (status IN ('active', 'stale', 'retired'))
);

CREATE TABLE IF NOT EXISTS learning_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_key TEXT NOT NULL UNIQUE,
    branch_key TEXT NOT NULL DEFAULT 'main',
    tick_number INTEGER NOT NULL DEFAULT 0,
    resident_id INTEGER NOT NULL,
    experience_id INTEGER NOT NULL,
    memory_id INTEGER,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    before_json TEXT NOT NULL DEFAULT '{}',
    after_json TEXT NOT NULL DEFAULT '{}',
    update_reason TEXT NOT NULL,
    rule_version TEXT NOT NULL DEFAULT 'adaptive-learning-v1',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (experience_id) REFERENCES experience_records(id) ON DELETE CASCADE,
    FOREIGN KEY (memory_id) REFERENCES adaptive_memories(id) ON DELETE SET NULL,
    CHECK (tick_number >= 0),
    CHECK (target_type IN ('strategy', 'skill', 'habit', 'belief', 'goal_priority', 'risk_expectation'))
);

CREATE INDEX IF NOT EXISTS idx_experience_records_resident_tick
ON experience_records(resident_id, tick_number, id);

CREATE INDEX IF NOT EXISTS idx_adaptive_memories_resident_status
ON adaptive_memories(resident_id, status, salience, id);

CREATE INDEX IF NOT EXISTS idx_strategy_states_resident
ON strategy_states(resident_id, status, last_updated_at);

CREATE INDEX IF NOT EXISTS idx_learning_updates_resident_tick
ON learning_updates(resident_id, tick_number, id);
"""


NORM_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS norm_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_key TEXT NOT NULL UNIQUE,
    branch_key TEXT NOT NULL DEFAULT 'main',
    tick_number INTEGER NOT NULL DEFAULT 0,
    resident_id INTEGER,
    group_type TEXT NOT NULL,
    group_key TEXT NOT NULL,
    context_type TEXT NOT NULL,
    context_key TEXT NOT NULL,
    behavior_key TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    stance TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (tick_number >= 0),
    CHECK (signal_type IN ('behavior', 'approval', 'disapproval', 'imitation', 'reminder', 'gossip', 'exclusion', 'sanction', 'counterexample')),
    CHECK (stance IN ('support', 'oppose', 'neutral')),
    CHECK (weight > 0)
);

CREATE TABLE IF NOT EXISTS norm_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norm_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    behavior_key TEXT NOT NULL,
    group_type TEXT NOT NULL,
    group_key TEXT NOT NULL,
    context_type TEXT NOT NULL,
    context_key TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'emerging',
    support_score REAL NOT NULL DEFAULT 0,
    opposition_score REAL NOT NULL DEFAULT 0,
    descriptive_expectation REAL NOT NULL DEFAULT 0,
    injunctive_expectation REAL NOT NULL DEFAULT 0,
    observation_coverage REAL NOT NULL DEFAULT 0,
    behavior_count INTEGER NOT NULL DEFAULT 0,
    distinct_actor_count INTEGER NOT NULL DEFAULT 0,
    feedback_count INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0,
    evidence_window_start TEXT NOT NULL,
    evidence_window_end TEXT NOT NULL,
    first_detected_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (state IN ('emerging', 'contested', 'established', 'weakening', 'dissolved')),
    CHECK (descriptive_expectation BETWEEN 0 AND 1),
    CHECK (injunctive_expectation BETWEEN 0 AND 1),
    CHECK (observation_coverage BETWEEN 0 AND 1),
    CHECK (behavior_count >= 0 AND distinct_actor_count >= 0 AND feedback_count >= 0),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS norm_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norm_id INTEGER NOT NULL,
    signal_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    resident_id INTEGER,
    stance TEXT NOT NULL,
    weight REAL NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (norm_id, signal_id),
    FOREIGN KEY (norm_id) REFERENCES norm_candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (signal_id) REFERENCES norm_signals(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (stance IN ('support', 'oppose', 'neutral')),
    CHECK (weight > 0)
);

CREATE TABLE IF NOT EXISTS agent_norm_beliefs (
    resident_id INTEGER NOT NULL,
    norm_id INTEGER NOT NULL,
    descriptive_expectation REAL NOT NULL DEFAULT 0,
    injunctive_expectation REAL NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0,
    exposure_count INTEGER NOT NULL DEFAULT 0,
    personal_stance TEXT NOT NULL DEFAULT 'uncertain',
    last_updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (resident_id, norm_id),
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (norm_id) REFERENCES norm_candidates(id) ON DELETE CASCADE,
    CHECK (descriptive_expectation BETWEEN 0 AND 1),
    CHECK (injunctive_expectation BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (exposure_count >= 0),
    CHECK (personal_stance IN ('support', 'oppose', 'uncertain', 'strategic'))
);

CREATE TABLE IF NOT EXISTS norm_state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norm_id INTEGER NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    evidence_summary_json TEXT NOT NULL DEFAULT '{}',
    transitioned_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (norm_id) REFERENCES norm_candidates(id) ON DELETE CASCADE,
    CHECK (from_state IN ('none', 'emerging', 'contested', 'established', 'weakening', 'dissolved')),
    CHECK (to_state IN ('emerging', 'contested', 'established', 'weakening', 'dissolved'))
);

CREATE TABLE IF NOT EXISTS norm_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    response_key TEXT NOT NULL UNIQUE,
    norm_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    response_type TEXT NOT NULL,
    public_behavior TEXT NOT NULL,
    private_stance TEXT NOT NULL,
    detected INTEGER NOT NULL DEFAULT 0,
    consequence_json TEXT NOT NULL DEFAULT '{}',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (norm_id) REFERENCES norm_candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (response_type IN ('comply', 'perform', 'hidden_violate', 'open_challenge', 'imitate', 'ignore')),
    CHECK (private_stance IN ('support', 'oppose', 'uncertain', 'strategic')),
    CHECK (detected IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_norm_signals_scope
ON norm_signals(group_type, group_key, context_type, context_key, behavior_key, observed_at);

CREATE INDEX IF NOT EXISTS idx_norm_candidates_scope
ON norm_candidates(group_type, group_key, state, last_updated_at);

CREATE INDEX IF NOT EXISTS idx_norm_evidence_norm
ON norm_evidence(norm_id, occurred_at, id);

CREATE INDEX IF NOT EXISTS idx_norm_responses_norm
ON norm_responses(norm_id, occurred_at, id);
"""


INSTITUTION_EVOLUTION_SQL = """
CREATE TABLE IF NOT EXISTS rule_primitives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    primitive_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    rule_layer TEXT NOT NULL,
    executor_key TEXT NOT NULL,
    parameter_schema_json TEXT NOT NULL DEFAULT '{}',
    allowed_scope_types_json TEXT NOT NULL DEFAULT '[]',
    immutable_invariants_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (rule_layer IN ('institutional', 'service', 'capacity', 'enforcement', 'economic')),
    CHECK (status IN ('active', 'paused', 'retired')),
    CHECK (version > 0)
);

CREATE TABLE IF NOT EXISTS institutional_rule_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_key TEXT NOT NULL UNIQUE,
    source_norm_id INTEGER,
    organization_id INTEGER NOT NULL,
    proposer_resident_id INTEGER NOT NULL,
    organization_proposal_id INTEGER,
    primitive_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    rationale TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    requested_budget_minor INTEGER NOT NULL DEFAULT 0,
    monitoring_plan_json TEXT NOT NULL DEFAULT '{}',
    review_after_days INTEGER NOT NULL DEFAULT 30,
    repeal_conditions_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'agenda',
    submitted_at TEXT NOT NULL,
    decided_at TEXT NOT NULL DEFAULT '',
    enacted_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_norm_id) REFERENCES norm_candidates(id) ON DELETE SET NULL,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    FOREIGN KEY (proposer_resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_proposal_id) REFERENCES organization_proposals(id) ON DELETE SET NULL,
    FOREIGN KEY (primitive_id) REFERENCES rule_primitives(id) ON DELETE RESTRICT,
    CHECK (requested_budget_minor >= 0 AND review_after_days > 0),
    CHECK (status IN ('agenda', 'deliberation', 'approved', 'rejected', 'trial', 'enacted', 'retired', 'unsupported'))
);

CREATE TABLE IF NOT EXISTS rule_deliberations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    participant_type TEXT NOT NULL,
    participant_id TEXT NOT NULL,
    stance TEXT NOT NULL,
    influence_weight REAL NOT NULL DEFAULT 1,
    argument TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    recorded_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES institutional_rule_proposals(id) ON DELETE CASCADE,
    CHECK (participant_type IN ('resident', 'organization', 'public')),
    CHECK (stance IN ('support', 'oppose', 'amend', 'abstain')),
    CHECK (influence_weight > 0)
);

CREATE TABLE IF NOT EXISTS evolved_rule_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lineage_key TEXT NOT NULL,
    version INTEGER NOT NULL,
    proposal_id INTEGER NOT NULL,
    primitive_id INTEGER NOT NULL,
    scope_type TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    effective_from TEXT NOT NULL,
    effective_to TEXT NOT NULL DEFAULT '',
    replaces_rule_version_id INTEGER,
    constraint_rule_id INTEGER,
    enacted_by_type TEXT NOT NULL DEFAULT 'organization',
    enacted_by_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lineage_key, version),
    FOREIGN KEY (proposal_id) REFERENCES institutional_rule_proposals(id) ON DELETE RESTRICT,
    FOREIGN KEY (primitive_id) REFERENCES rule_primitives(id) ON DELETE RESTRICT,
    FOREIGN KEY (replaces_rule_version_id) REFERENCES evolved_rule_versions(id) ON DELETE SET NULL,
    FOREIGN KEY (constraint_rule_id) REFERENCES constraint_rules(id) ON DELETE SET NULL,
    CHECK (version > 0),
    CHECK (status IN ('trial', 'active', 'superseded', 'repealed'))
);

CREATE TABLE IF NOT EXISTS rule_effect_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_version_id INTEGER NOT NULL,
    review_key TEXT NOT NULL UNIQUE,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    target_outcome_json TEXT NOT NULL DEFAULT '{}',
    distributional_impact_json TEXT NOT NULL DEFAULT '{}',
    evasion_json TEXT NOT NULL DEFAULT '{}',
    enforcement_cost_json TEXT NOT NULL DEFAULT '{}',
    externality_json TEXT NOT NULL DEFAULT '{}',
    trust_impact_json TEXT NOT NULL DEFAULT '{}',
    recommendation TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    reviewed_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_version_id) REFERENCES evolved_rule_versions(id) ON DELETE CASCADE,
    CHECK (recommendation IN ('retain', 'amend', 'repeal', 'extend_trial', 'insufficient_evidence'))
);

CREATE INDEX IF NOT EXISTS idx_rule_proposals_status
ON institutional_rule_proposals(status, submitted_at, id);

CREATE INDEX IF NOT EXISTS idx_evolved_rule_versions_lineage
ON evolved_rule_versions(lineage_key, version, status);

CREATE INDEX IF NOT EXISTS idx_rule_effect_reviews_version
ON rule_effect_reviews(rule_version_id, reviewed_at, id);
"""
