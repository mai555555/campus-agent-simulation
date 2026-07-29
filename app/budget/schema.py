BUDGET_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS household_budget_profiles (
    resident_id INTEGER PRIMARY KEY,
    planning_horizon_days INTEGER NOT NULL DEFAULT 7,
    savings_rate_basis_points INTEGER NOT NULL DEFAULT 500,
    emergency_reserve_minor INTEGER NOT NULL DEFAULT 1000,
    risk_tolerance INTEGER NOT NULL DEFAULT 50,
    credit_enabled INTEGER NOT NULL DEFAULT 0,
    credit_limit_minor INTEGER NOT NULL DEFAULT 0,
    outstanding_debt_minor INTEGER NOT NULL DEFAULT 0,
    last_savings_date TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (planning_horizon_days > 0),
    CHECK (savings_rate_basis_points BETWEEN 0 AND 10000),
    CHECK (emergency_reserve_minor >= 0),
    CHECK (risk_tolerance BETWEEN 0 AND 100),
    CHECK (credit_enabled IN (0, 1)),
    CHECK (credit_limit_minor >= 0),
    CHECK (outstanding_debt_minor >= 0),
    CHECK (status IN ('active', 'paused'))
);

CREATE TABLE IF NOT EXISTS household_budget_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    budget_date TEXT NOT NULL,
    cash_minor INTEGER NOT NULL,
    savings_minor INTEGER NOT NULL,
    expected_income_minor INTEGER NOT NULL DEFAULT 0,
    transfer_income_minor INTEGER NOT NULL DEFAULT 0,
    required_expenses_minor INTEGER NOT NULL DEFAULT 0,
    due_debt_minor INTEGER NOT NULL DEFAULT 0,
    borrowing_minor INTEGER NOT NULL DEFAULT 0,
    disposable_minor INTEGER NOT NULL,
    time_budget_minutes INTEGER NOT NULL,
    committed_time_minutes INTEGER NOT NULL DEFAULT 0,
    free_time_minutes INTEGER NOT NULL,
    liquidity_status TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (resident_id, budget_date),
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (cash_minor >= 0),
    CHECK (savings_minor >= 0),
    CHECK (expected_income_minor >= 0),
    CHECK (transfer_income_minor >= 0),
    CHECK (required_expenses_minor >= 0),
    CHECK (due_debt_minor >= 0),
    CHECK (borrowing_minor >= 0),
    CHECK (disposable_minor >= 0),
    CHECK (time_budget_minutes >= 0),
    CHECK (committed_time_minutes >= 0),
    CHECK (free_time_minutes >= 0),
    CHECK (liquidity_status IN ('stable', 'tight', 'shortfall'))
);

CREATE TABLE IF NOT EXISTS savings_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    direction TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    reason TEXT NOT NULL,
    goal_id INTEGER,
    ledger_transaction_id INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES agent_goals(id) ON DELETE SET NULL,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    CHECK (direction IN ('deposit', 'withdrawal')),
    CHECK (amount_minor > 0)
);

CREATE TABLE IF NOT EXISTS choice_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    action_execution_id INTEGER,
    action_type TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    decision TEXT NOT NULL,
    required_money_minor INTEGER NOT NULL DEFAULT 0,
    required_time_minutes INTEGER NOT NULL DEFAULT 0,
    disposable_before_minor INTEGER NOT NULL DEFAULT 0,
    free_time_before_minutes INTEGER NOT NULL DEFAULT 0,
    money_opportunity_cost_minor INTEGER NOT NULL DEFAULT 0,
    time_opportunity_cost_minutes INTEGER NOT NULL DEFAULT 0,
    released_money_minor INTEGER NOT NULL DEFAULT 0,
    released_time_minutes INTEGER NOT NULL DEFAULT 0,
    alternative_action TEXT NOT NULL DEFAULT '',
    long_term_goal_id INTEGER,
    emergency_override INTEGER NOT NULL DEFAULT 0,
    rationale TEXT NOT NULL DEFAULT '',
    rule_version TEXT NOT NULL DEFAULT 'budget-choice-v1',
    occurred_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (action_execution_id) REFERENCES world_action_executions(id) ON DELETE SET NULL,
    FOREIGN KEY (long_term_goal_id) REFERENCES agent_goals(id) ON DELETE SET NULL,
    CHECK (decision IN ('allowed', 'rejected', 'deferred')),
    CHECK (required_money_minor >= 0),
    CHECK (required_time_minutes >= 0),
    CHECK (disposable_before_minor >= 0),
    CHECK (free_time_before_minutes >= 0),
    CHECK (money_opportunity_cost_minor >= 0),
    CHECK (time_opportunity_cost_minutes >= 0),
    CHECK (released_money_minor >= 0),
    CHECK (released_time_minutes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_budget_snapshots_resident_date
ON household_budget_snapshots(resident_id, budget_date);
CREATE INDEX IF NOT EXISTS idx_savings_transfers_resident
ON savings_transfers(resident_id, id);
CREATE INDEX IF NOT EXISTS idx_choice_evaluations_resident
ON choice_evaluations(resident_id, id);
"""
