SOCIAL_INSTITUTION_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS communication_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    channel_type TEXT NOT NULL,
    reach_mode TEXT NOT NULL,
    base_fidelity INTEGER NOT NULL,
    delay_minutes INTEGER NOT NULL DEFAULT 0,
    authority_weight INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (channel_type IN ('in_person', 'group_chat', 'social_feed', 'authority_notice')),
    CHECK (reach_mode IN ('direct', 'group', 'network', 'broadcast')),
    CHECK (base_fidelity BETWEEN 0 AND 100),
    CHECK (delay_minutes >= 0 AND authority_weight BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'paused'))
);

CREATE TABLE IF NOT EXISTS information_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_key TEXT NOT NULL UNIQUE,
    claim_type TEXT NOT NULL,
    title TEXT NOT NULL,
    canonical_content TEXT NOT NULL,
    subject_type TEXT NOT NULL DEFAULT 'world_event',
    subject_key TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    origin_resident_id INTEGER,
    origin_actor_key TEXT NOT NULL DEFAULT '',
    truth_status TEXT NOT NULL DEFAULT 'unverified',
    source_reliability INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'active',
    occurred_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (claim_type IN ('fact', 'gossip', 'rumor', 'announcement', 'clarification')),
    CHECK (truth_status IN ('verified', 'unverified', 'disputed', 'false', 'corrected')),
    CHECK (source_reliability BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'resolved', 'withdrawn'))
);

CREATE TABLE IF NOT EXISTS information_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_key TEXT NOT NULL UNIQUE,
    claim_id INTEGER NOT NULL,
    parent_version_id INTEGER,
    content TEXT NOT NULL,
    fidelity INTEGER NOT NULL,
    distortion_score INTEGER NOT NULL DEFAULT 0,
    omitted_context_json TEXT NOT NULL DEFAULT '[]',
    emphasis_json TEXT NOT NULL DEFAULT '[]',
    transformation_type TEXT NOT NULL DEFAULT 'original',
    created_by_resident_id INTEGER,
    created_at_world TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES information_claims(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_version_id) REFERENCES information_versions(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (fidelity BETWEEN 0 AND 100 AND distortion_score BETWEEN 0 AND 100),
    CHECK (transformation_type IN ('original', 'verbatim', 'summary', 'omission', 'emphasis', 'misreading', 'clarification'))
);

CREATE TABLE IF NOT EXISTS information_transmissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transmission_key TEXT NOT NULL UNIQUE,
    claim_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    parent_transmission_id INTEGER,
    channel_id INTEGER NOT NULL,
    sender_resident_id INTEGER,
    sender_actor_key TEXT NOT NULL DEFAULT '',
    recipient_resident_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_id TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    sent_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES information_claims(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES information_versions(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_transmission_id) REFERENCES information_transmissions(id) ON DELETE SET NULL,
    FOREIGN KEY (channel_id) REFERENCES communication_channels(id) ON DELETE RESTRICT,
    FOREIGN KEY (sender_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (recipient_resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (evidence_type IN ('source_event', 'co_location', 'relationship', 'organization', 'broadcast')),
    CHECK (status IN ('scheduled', 'received', 'blocked', 'retracted'))
);

CREATE TABLE IF NOT EXISTS information_exposures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exposure_key TEXT NOT NULL UNIQUE,
    transmission_id INTEGER NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    claim_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    attention_score INTEGER NOT NULL,
    comprehension_score INTEGER NOT NULL,
    credibility_score INTEGER NOT NULL,
    reaction TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transmission_id) REFERENCES information_transmissions(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (claim_id) REFERENCES information_claims(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES information_versions(id) ON DELETE CASCADE,
    CHECK (attention_score BETWEEN 0 AND 100),
    CHECK (comprehension_score BETWEEN 0 AND 100),
    CHECK (credibility_score BETWEEN 0 AND 100),
    CHECK (reaction IN ('accept', 'doubt', 'reject', 'share', 'clarify'))
);

CREATE TABLE IF NOT EXISTS information_beliefs (
    resident_id INTEGER NOT NULL,
    claim_id INTEGER NOT NULL,
    believed_version_id INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    stance TEXT NOT NULL,
    exposure_count INTEGER NOT NULL DEFAULT 1,
    first_formed_at TEXT NOT NULL,
    last_updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (resident_id, claim_id),
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (claim_id) REFERENCES information_claims(id) ON DELETE CASCADE,
    FOREIGN KEY (believed_version_id) REFERENCES information_versions(id) ON DELETE RESTRICT,
    CHECK (confidence BETWEEN 0 AND 100 AND exposure_count > 0),
    CHECK (stance IN ('believes', 'uncertain', 'disbelieves', 'corrected')),
    CHECK (status IN ('active', 'superseded'))
);

CREATE TABLE IF NOT EXISTS institutional_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    case_type TEXT NOT NULL,
    authority_actor_key TEXT NOT NULL,
    required_permission TEXT NOT NULL DEFAULT '',
    applies_to_roles_json TEXT NOT NULL DEFAULT '[]',
    evidence_requirements_json TEXT NOT NULL DEFAULT '[]',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    decision_delay_minutes INTEGER NOT NULL DEFAULT 60,
    appeal_allowed INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    rule_version TEXT NOT NULL DEFAULT 'social-institution-v1',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (case_type IN ('leave_request', 'access_request', 'conduct_violation', 'reward_nomination', 'appeal')),
    CHECK (decision_delay_minutes >= 0 AND appeal_allowed IN (0, 1)),
    CHECK (status IN ('active', 'paused', 'retired'))
);

CREATE TABLE IF NOT EXISTS institutional_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_key TEXT NOT NULL UNIQUE,
    rule_id INTEGER NOT NULL,
    case_type TEXT NOT NULL,
    subject_resident_id INTEGER NOT NULL,
    submitted_by_resident_id INTEGER,
    parent_case_id INTEGER,
    organization_id INTEGER,
    status TEXT NOT NULL DEFAULT 'submitted',
    priority INTEGER NOT NULL DEFAULT 50,
    formal_path INTEGER NOT NULL DEFAULT 1,
    bypass_attempted INTEGER NOT NULL DEFAULT 0,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    requested_outcome TEXT NOT NULL DEFAULT '',
    submitted_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    resolved_at TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES institutional_rules(id) ON DELETE RESTRICT,
    FOREIGN KEY (subject_resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (submitted_by_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_case_id) REFERENCES institutional_cases(id) ON DELETE SET NULL,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE SET NULL,
    CHECK (case_type IN ('leave_request', 'access_request', 'conduct_violation', 'reward_nomination', 'appeal')),
    CHECK (status IN ('submitted', 'under_review', 'approved', 'rejected', 'sanctioned', 'rewarded', 'appealed', 'bypassed', 'cancelled')),
    CHECK (priority BETWEEN 0 AND 100),
    CHECK (formal_path IN (0, 1) AND bypass_attempted IN (0, 1))
);

CREATE TABLE IF NOT EXISTS institutional_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_key TEXT NOT NULL UNIQUE,
    case_id INTEGER NOT NULL UNIQUE,
    decision_maker_resident_id INTEGER,
    decision_maker_actor_key TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL,
    reason TEXT NOT NULL,
    rule_compliance_score INTEGER NOT NULL,
    procedural_fairness_score INTEGER NOT NULL,
    consequence_minor INTEGER NOT NULL DEFAULT 0,
    ledger_transaction_id INTEGER,
    opportunity_delta INTEGER NOT NULL DEFAULT 0,
    relationship_delta INTEGER NOT NULL DEFAULT 0,
    decided_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES institutional_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (decision_maker_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (outcome IN ('approved', 'rejected', 'sanctioned', 'rewarded', 'appeal_upheld', 'appeal_denied', 'bypass_detected')),
    CHECK (rule_compliance_score BETWEEN 0 AND 100),
    CHECK (procedural_fairness_score BETWEEN 0 AND 100),
    CHECK (consequence_minor >= 0),
    CHECK (opportunity_delta BETWEEN -100 AND 100),
    CHECK (relationship_delta BETWEEN -100 AND 100)
);

CREATE TABLE IF NOT EXISTS resident_power_profiles (
    resident_id INTEGER PRIMARY KEY,
    formal_authority INTEGER NOT NULL DEFAULT 0,
    informal_influence INTEGER NOT NULL DEFAULT 0,
    network_reach INTEGER NOT NULL DEFAULT 0,
    information_influence INTEGER NOT NULL DEFAULT 0,
    institutional_trust INTEGER NOT NULL DEFAULT 50,
    procedural_access INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'active',
    evidence_json TEXT NOT NULL DEFAULT '{}',
    calculated_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (formal_authority BETWEEN 0 AND 100),
    CHECK (informal_influence BETWEEN 0 AND 100),
    CHECK (network_reach BETWEEN 0 AND 100),
    CHECK (information_influence BETWEEN 0 AND 100),
    CHECK (institutional_trust BETWEEN 0 AND 100),
    CHECK (procedural_access BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'restricted'))
);

CREATE TABLE IF NOT EXISTS institutional_trust_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    case_id INTEGER,
    event_type TEXT NOT NULL,
    trust_before INTEGER NOT NULL,
    trust_after INTEGER NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES institutional_cases(id) ON DELETE SET NULL,
    CHECK (event_type IN ('fair_process', 'unfair_process', 'appeal_success', 'appeal_failure', 'bypass_detected', 'authority_notice')),
    CHECK (trust_before BETWEEN 0 AND 100 AND trust_after BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS ix_information_claims_status ON information_claims(status, occurred_at);
CREATE INDEX IF NOT EXISTS ix_information_versions_claim ON information_versions(claim_id, id);
CREATE INDEX IF NOT EXISTS ix_information_transmissions_recipient ON information_transmissions(recipient_resident_id, received_at);
CREATE INDEX IF NOT EXISTS ix_information_exposures_claim ON information_exposures(claim_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_information_beliefs_claim ON information_beliefs(claim_id, confidence);
CREATE INDEX IF NOT EXISTS ix_institutional_cases_due ON institutional_cases(status, due_at, id);
CREATE INDEX IF NOT EXISTS ix_institutional_decisions_outcome ON institutional_decisions(outcome, decided_at);
CREATE INDEX IF NOT EXISTS ix_trust_events_resident ON institutional_trust_events(resident_id, occurred_at);
"""

