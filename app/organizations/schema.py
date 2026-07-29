ORGANIZATION_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS organization_runtime_profiles (
    organization_id INTEGER PRIMARY KEY,
    governance_mode TEXT NOT NULL DEFAULT 'council',
    mission TEXT NOT NULL DEFAULT '',
    reputation INTEGER NOT NULL DEFAULT 50,
    decision_delay_minutes INTEGER NOT NULL DEFAULT 60,
    quorum_weight INTEGER NOT NULL DEFAULT 1,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    CHECK (governance_mode IN ('executive', 'council', 'consensus')),
    CHECK (reputation BETWEEN 0 AND 100),
    CHECK (decision_delay_minutes >= 0),
    CHECK (quorum_weight > 0)
);

CREATE TABLE IF NOT EXISTS organization_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    role_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    permissions_json TEXT NOT NULL DEFAULT '[]',
    spending_limit_minor INTEGER NOT NULL DEFAULT 0,
    vote_weight INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, role_key),
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    CHECK (spending_limit_minor >= 0),
    CHECK (vote_weight > 0),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS organization_role_assignments (
    organization_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    assigned_by_resident_id INTEGER,
    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (organization_id, resident_id),
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES organization_roles(id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_by_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS organization_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_key TEXT NOT NULL UNIQUE,
    organization_id INTEGER NOT NULL,
    proposer_resident_id INTEGER NOT NULL,
    proposal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    requested_budget_minor INTEGER NOT NULL DEFAULT 0,
    target_actor_key TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    approvals_required INTEGER NOT NULL DEFAULT 1,
    approvals_weight INTEGER NOT NULL DEFAULT 0,
    rejections_weight INTEGER NOT NULL DEFAULT 0,
    earliest_decision_at TEXT NOT NULL,
    expires_at TEXT NOT NULL DEFAULT '',
    decision_reason TEXT NOT NULL DEFAULT '',
    ledger_transaction_id INTEGER,
    source_type TEXT NOT NULL DEFAULT 'organization_runtime',
    source_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at TEXT NOT NULL DEFAULT '',
    executed_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    FOREIGN KEY (proposer_resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (requested_budget_minor >= 0),
    CHECK (approvals_required > 0),
    CHECK (status IN ('pending', 'approved', 'rejected', 'executed', 'cancelled', 'expired'))
);

CREATE TABLE IF NOT EXISTS organization_votes (
    proposal_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    vote_weight INTEGER NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (proposal_id, resident_id),
    FOREIGN KEY (proposal_id) REFERENCES organization_proposals(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE RESTRICT,
    CHECK (decision IN ('approve', 'reject')),
    CHECK (vote_weight > 0)
);

CREATE TABLE IF NOT EXISTS organization_commitments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commitment_key TEXT NOT NULL UNIQUE,
    organization_id INTEGER NOT NULL,
    proposal_id INTEGER,
    commitment_type TEXT NOT NULL,
    counterparty_actor_key TEXT NOT NULL DEFAULT '',
    amount_minor INTEGER NOT NULL DEFAULT 0,
    due_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    responsibility_resident_id INTEGER,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    FOREIGN KEY (proposal_id) REFERENCES organization_proposals(id) ON DELETE SET NULL,
    FOREIGN KEY (responsibility_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (amount_minor >= 0),
    CHECK (status IN ('active', 'fulfilled', 'breached', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS organization_relationships (
    from_organization_id INTEGER NOT NULL,
    to_organization_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'neutral',
    trust INTEGER NOT NULL DEFAULT 50,
    influence INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (from_organization_id, to_organization_id),
    FOREIGN KEY (from_organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (to_organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    CHECK (from_organization_id <> to_organization_id),
    CHECK (relation_type IN ('neutral', 'alliance', 'service', 'competition', 'conflict')),
    CHECK (trust BETWEEN 0 AND 100),
    CHECK (influence BETWEEN -100 AND 100),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS organization_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    organization_id INTEGER NOT NULL,
    proposal_id INTEGER,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (proposal_id) REFERENCES organization_proposals(id) ON DELETE SET NULL,
    CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_organization_roles_org_status
ON organization_roles(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_organization_proposals_due
ON organization_proposals(status, earliest_decision_at, id);
CREATE INDEX IF NOT EXISTS idx_organization_commitments_due
ON organization_commitments(status, due_at, id);
CREATE INDEX IF NOT EXISTS idx_organization_events_org
ON organization_events(organization_id, id);
"""

