LABOR_RUNTIME_SQL = """
CREATE TABLE IF NOT EXISTS labor_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_key TEXT NOT NULL UNIQUE,
    organization_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    allowed_actions_json TEXT NOT NULL DEFAULT '[]',
    skill_dimension TEXT NOT NULL,
    minimum_skill INTEGER NOT NULL DEFAULT 0,
    capacity INTEGER NOT NULL DEFAULT 1,
    hourly_wage_minor INTEGER NOT NULL,
    standard_daily_minutes INTEGER NOT NULL DEFAULT 120,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES campus_organizations(id) ON DELETE RESTRICT,
    CHECK (minimum_skill BETWEEN 0 AND 100),
    CHECK (capacity > 0),
    CHECK (hourly_wage_minor > 0),
    CHECK (standard_daily_minutes > 0),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS employment_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_key TEXT NOT NULL UNIQUE,
    position_id INTEGER NOT NULL,
    resident_id INTEGER NOT NULL,
    contract_type TEXT NOT NULL DEFAULT 'part_time',
    hourly_wage_minor INTEGER NOT NULL,
    scheduled_daily_minutes INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    skill_score_at_hire INTEGER NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (position_id, resident_id),
    FOREIGN KEY (position_id) REFERENCES labor_positions(id) ON DELETE RESTRICT,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (contract_type IN ('staff', 'part_time', 'assistantship', 'project')),
    CHECK (hourly_wage_minor > 0),
    CHECK (scheduled_daily_minutes > 0),
    CHECK (skill_score_at_hire BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'suspended', 'ended'))
);

CREATE TABLE IF NOT EXISTS labor_shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_key TEXT NOT NULL UNIQUE,
    contract_id INTEGER NOT NULL,
    work_date TEXT NOT NULL,
    scheduled_minutes INTEGER NOT NULL,
    evidenced_minutes INTEGER NOT NULL DEFAULT 0,
    payable_minutes INTEGER NOT NULL DEFAULT 0,
    gross_pay_minor INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'scheduled',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    ledger_transaction_id INTEGER,
    failure_reason TEXT NOT NULL DEFAULT '',
    processed_at TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (contract_id, work_date),
    FOREIGN KEY (contract_id) REFERENCES employment_contracts(id) ON DELETE RESTRICT,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (scheduled_minutes > 0),
    CHECK (evidenced_minutes >= 0),
    CHECK (payable_minutes >= 0),
    CHECK (gross_pay_minor >= 0),
    CHECK (status IN ('scheduled', 'completed', 'partial', 'absent', 'blocked'))
);

CREATE TABLE IF NOT EXISTS income_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_key TEXT NOT NULL UNIQUE,
    program_type TEXT NOT NULL,
    payer_actor_key TEXT NOT NULL,
    recipient_resident_id INTEGER NOT NULL,
    amount_minor INTEGER NOT NULL,
    cadence_days INTEGER NOT NULL,
    next_due_date TEXT NOT NULL,
    eligibility_rule TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    CHECK (program_type IN ('scholarship', 'financial_aid', 'family_support', 'subsidy', 'reimbursement')),
    CHECK (amount_minor > 0),
    CHECK (cadence_days > 0),
    CHECK (status IN ('active', 'paused', 'ended'))
);

CREATE TABLE IF NOT EXISTS income_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_key TEXT NOT NULL UNIQUE,
    payment_type TEXT NOT NULL,
    payer_actor_key TEXT NOT NULL,
    recipient_actor_key TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    labor_shift_id INTEGER,
    income_program_id INTEGER,
    status TEXT NOT NULL DEFAULT 'posted',
    ledger_transaction_id INTEGER,
    due_date TEXT NOT NULL,
    paid_at TEXT NOT NULL DEFAULT '',
    failure_reason TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (labor_shift_id) REFERENCES labor_shifts(id) ON DELETE SET NULL,
    FOREIGN KEY (income_program_id) REFERENCES income_programs(id) ON DELETE SET NULL,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (payment_type IN ('wage', 'scholarship', 'financial_aid', 'family_support', 'subsidy', 'reimbursement')),
    CHECK (amount_minor > 0),
    CHECK (status IN ('posted', 'blocked', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS expense_obligations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obligation_key TEXT NOT NULL UNIQUE,
    resident_id INTEGER NOT NULL,
    expense_type TEXT NOT NULL,
    recipient_actor_key TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    cadence_days INTEGER NOT NULL,
    next_due_date TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 50,
    status TEXT NOT NULL DEFAULT 'active',
    last_ledger_transaction_id INTEGER,
    last_attempt_date TEXT NOT NULL DEFAULT '',
    failure_reason TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE CASCADE,
    FOREIGN KEY (last_ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (expense_type IN ('tuition', 'housing', 'meal_plan', 'transport', 'study', 'tax', 'fine')),
    CHECK (amount_minor > 0),
    CHECK (cadence_days > 0),
    CHECK (priority BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'paused', 'ended'))
);

CREATE INDEX IF NOT EXISTS idx_employment_contracts_resident
ON employment_contracts(resident_id, status);
CREATE INDEX IF NOT EXISTS idx_labor_shifts_status_date
ON labor_shifts(status, work_date, id);
CREATE INDEX IF NOT EXISTS idx_income_programs_due
ON income_programs(status, next_due_date, id);
CREATE INDEX IF NOT EXISTS idx_income_payments_recipient
ON income_payments(recipient_actor_key, id);
CREATE INDEX IF NOT EXISTS idx_expense_obligations_due
ON expense_obligations(status, next_due_date, priority, id);
"""
