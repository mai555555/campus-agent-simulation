PUBLIC_POLICY_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS public_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    service_type TEXT NOT NULL,
    provider_actor_key TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    daily_capacity INTEGER NOT NULL,
    base_daily_cost_minor INTEGER NOT NULL DEFAULT 0,
    marginal_cost_minor INTEGER NOT NULL DEFAULT 0,
    quality INTEGER NOT NULL DEFAULT 70,
    access_mode TEXT NOT NULL DEFAULT 'universal',
    status TEXT NOT NULL DEFAULT 'active',
    rule_version TEXT NOT NULL DEFAULT 'public-policy-v1',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (service_type IN ('library', 'network', 'security', 'public_space')),
    CHECK (daily_capacity > 0),
    CHECK (base_daily_cost_minor >= 0 AND marginal_cost_minor >= 0),
    CHECK (quality BETWEEN 0 AND 100),
    CHECK (access_mode IN ('universal', 'location', 'role', 'eligible')),
    CHECK (status IN ('active', 'degraded', 'paused'))
);

CREATE TABLE IF NOT EXISTS public_service_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_key TEXT NOT NULL UNIQUE,
    service_id INTEGER NOT NULL,
    operation_date TEXT NOT NULL,
    available_capacity INTEGER NOT NULL,
    used_capacity INTEGER NOT NULL DEFAULT 0,
    denied_count INTEGER NOT NULL DEFAULT 0,
    operating_cost_minor INTEGER NOT NULL DEFAULT 0,
    funded_cost_minor INTEGER NOT NULL DEFAULT 0,
    quality INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    ledger_transaction_id INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (service_id, operation_date),
    FOREIGN KEY (service_id) REFERENCES public_services(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (available_capacity >= 0 AND used_capacity >= 0),
    CHECK (used_capacity <= available_capacity),
    CHECK (denied_count >= 0),
    CHECK (operating_cost_minor >= 0 AND funded_cost_minor >= 0),
    CHECK (funded_cost_minor <= operating_cost_minor),
    CHECK (quality BETWEEN 0 AND 100),
    CHECK (status IN ('open', 'capacity_limited', 'underfunded', 'closed'))
);

CREATE TABLE IF NOT EXISTS public_service_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usage_key TEXT NOT NULL UNIQUE,
    operation_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    access_group TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    units INTEGER NOT NULL DEFAULT 1,
    wait_minutes INTEGER NOT NULL DEFAULT 0,
    access_cost_minor INTEGER NOT NULL DEFAULT 0,
    welfare_delta INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES public_service_operations(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES public_services(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (units > 0 AND wait_minutes >= 0 AND access_cost_minor >= 0),
    CHECK (welfare_delta BETWEEN -100 AND 100),
    CHECK (status IN ('served', 'queued', 'denied', 'not_eligible'))
);

CREATE TABLE IF NOT EXISTS externality_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_key TEXT NOT NULL UNIQUE,
    externality_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    source_resident_id INTEGER,
    source_actor_key TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    magnitude INTEGER NOT NULL,
    direction TEXT NOT NULL,
    radius_meters INTEGER NOT NULL DEFAULT 0,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    CHECK (externality_type IN ('congestion', 'noise', 'pollution', 'reputation', 'knowledge_spillover')),
    CHECK (magnitude BETWEEN 1 AND 100),
    CHECK (direction IN ('positive', 'negative')),
    CHECK (radius_meters >= 0),
    CHECK (status IN ('active', 'expired', 'mitigated'))
);

CREATE TABLE IF NOT EXISTS externality_exposures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exposure_key TEXT NOT NULL UNIQUE,
    externality_event_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    exposure_score INTEGER NOT NULL,
    welfare_delta INTEGER NOT NULL,
    behavioral_pressure INTEGER NOT NULL DEFAULT 0,
    distance_meters INTEGER NOT NULL DEFAULT 0,
    evidence_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (externality_event_id) REFERENCES externality_events(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (exposure_score BETWEEN 0 AND 100),
    CHECK (welfare_delta BETWEEN -100 AND 100),
    CHECK (behavioral_pressure BETWEEN -100 AND 100),
    CHECK (distance_meters >= 0),
    CHECK (evidence_type IN ('co_location', 'global_service', 'organization', 'market'))
);

CREATE TABLE IF NOT EXISTS policy_instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    authority_actor_key TEXT NOT NULL,
    budget_account_key TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_key TEXT NOT NULL DEFAULT '',
    eligibility_json TEXT NOT NULL DEFAULT '{}',
    parameters_json TEXT NOT NULL DEFAULT '{}',
    daily_budget_minor INTEGER NOT NULL DEFAULT 0,
    spent_minor INTEGER NOT NULL DEFAULT 0,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    rule_version TEXT NOT NULL DEFAULT 'public-policy-v1',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (policy_type IN ('subsidy', 'price_cap', 'scholarship', 'quota', 'fee', 'public_investment')),
    CHECK (target_type IN ('catalog_item', 'market', 'resident', 'role', 'location', 'public_service')),
    CHECK (daily_budget_minor >= 0 AND spent_minor >= 0),
    CHECK (status IN ('draft', 'active', 'paused', 'expired', 'budget_exhausted'))
);

CREATE TABLE IF NOT EXISTS policy_benefits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benefit_key TEXT NOT NULL UNIQUE,
    policy_id INTEGER NOT NULL,
    resident_id INTEGER,
    beneficiary_actor_key TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL DEFAULT '',
    gross_value_minor INTEGER NOT NULL DEFAULT 0,
    public_cost_minor INTEGER NOT NULL DEFAULT 0,
    private_cost_minor INTEGER NOT NULL DEFAULT 0,
    welfare_delta INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    ledger_transaction_id INTEGER,
    occurred_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policy_instruments(id) ON DELETE CASCADE,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (gross_value_minor >= 0 AND public_cost_minor >= 0 AND private_cost_minor >= 0),
    CHECK (welfare_delta BETWEEN -100 AND 100),
    CHECK (status IN ('eligible', 'delivered', 'rationed', 'ineligible', 'unfunded'))
);

CREATE TABLE IF NOT EXISTS policy_outcome_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_key TEXT NOT NULL UNIQUE,
    policy_id INTEGER NOT NULL,
    window_type TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    group_key TEXT NOT NULL,
    eligible_count INTEGER NOT NULL DEFAULT 0,
    reached_count INTEGER NOT NULL DEFAULT 0,
    public_cost_minor INTEGER NOT NULL DEFAULT 0,
    average_private_cost_minor INTEGER NOT NULL DEFAULT 0,
    average_welfare_delta REAL NOT NULL DEFAULT 0,
    behavior_count INTEGER NOT NULL DEFAULT 0,
    baseline_json TEXT NOT NULL DEFAULT '{}',
    outcome_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (policy_id, window_type, window_start, window_end, group_key),
    FOREIGN KEY (policy_id) REFERENCES policy_instruments(id) ON DELETE CASCADE,
    CHECK (window_type IN ('baseline', 'daily', 'weekly')),
    CHECK (eligible_count >= 0 AND reached_count >= 0),
    CHECK (public_cost_minor >= 0 AND average_private_cost_minor >= 0),
    CHECK (behavior_count >= 0)
);

CREATE INDEX IF NOT EXISTS ix_public_service_operations_date
ON public_service_operations(operation_date, service_id);
CREATE INDEX IF NOT EXISTS ix_public_service_usages_resident
ON public_service_usages(resident_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_externality_events_active
ON externality_events(status, location, starts_at);
CREATE INDEX IF NOT EXISTS ix_externality_exposures_resident
ON externality_exposures(resident_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_policy_instruments_active
ON policy_instruments(status, policy_type, starts_at);
CREATE INDEX IF NOT EXISTS ix_policy_benefits_policy
ON policy_benefits(policy_id, occurred_at, status);
CREATE INDEX IF NOT EXISTS ix_policy_outcomes_policy
ON policy_outcome_snapshots(policy_id, window_start, group_key);
"""

