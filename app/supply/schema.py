SUPPLY_FOUNDATION_SQL = """
CREATE TABLE IF NOT EXISTS catalog_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    item_type TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'unit',
    base_price_minor INTEGER NOT NULL DEFAULT 0,
    standard_cost_minor INTEGER NOT NULL DEFAULT 0,
    shelf_life_hours INTEGER NOT NULL DEFAULT 0,
    quality INTEGER NOT NULL DEFAULT 70,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (item_type IN ('good', 'service', 'input')),
    CHECK (base_price_minor >= 0),
    CHECK (standard_cost_minor >= 0),
    CHECK (shelf_life_hours >= 0),
    CHECK (quality BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS inventory_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_key TEXT NOT NULL UNIQUE,
    owner_actor_key TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    target_stock INTEGER NOT NULL DEFAULT 0,
    average_cost_minor INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (owner_actor_key, item_id, location),
    FOREIGN KEY (item_id) REFERENCES catalog_items(id) ON DELETE RESTRICT,
    CHECK (quantity_on_hand >= 0),
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_reserved <= quantity_on_hand),
    CHECK (reorder_point >= 0),
    CHECK (target_stock >= reorder_point),
    CHECK (average_cost_minor >= 0),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS production_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_key TEXT NOT NULL UNIQUE,
    producer_actor_key TEXT NOT NULL,
    output_item_id INTEGER NOT NULL,
    output_quantity INTEGER NOT NULL,
    duration_minutes INTEGER NOT NULL,
    cash_cost_minor INTEGER NOT NULL DEFAULT 0,
    location TEXT NOT NULL,
    spatial_resource_key TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (output_item_id) REFERENCES catalog_items(id) ON DELETE RESTRICT,
    CHECK (output_quantity > 0),
    CHECK (duration_minutes > 0),
    CHECK (cash_cost_minor >= 0),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS production_recipe_inputs (
    recipe_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (recipe_id, item_id),
    FOREIGN KEY (recipe_id) REFERENCES production_recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES catalog_items(id) ON DELETE RESTRICT,
    CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS production_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_key TEXT NOT NULL UNIQUE,
    recipe_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    output_quantity INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    ledger_transaction_id INTEGER,
    failure_reason TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES production_recipes(id) ON DELETE RESTRICT,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (output_quantity > 0),
    CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_key TEXT NOT NULL UNIQUE,
    inventory_account_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL,
    quantity_delta INTEGER NOT NULL,
    unit_cost_minor INTEGER NOT NULL DEFAULT 0,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL DEFAULT '',
    ledger_transaction_id INTEGER,
    production_batch_id INTEGER,
    occurred_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inventory_account_id) REFERENCES inventory_accounts(id) ON DELETE RESTRICT,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    FOREIGN KEY (production_batch_id) REFERENCES production_batches(id) ON DELETE SET NULL,
    CHECK (quantity_delta <> 0),
    CHECK (unit_cost_minor >= 0),
    CHECK (movement_type IN ('opening', 'purchase', 'sale', 'consumption', 'production_input', 'production_output', 'waste', 'adjustment'))
);

CREATE TABLE IF NOT EXISTS service_offerings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offering_key TEXT NOT NULL UNIQUE,
    provider_actor_key TEXT NOT NULL,
    service_item_id INTEGER NOT NULL,
    location TEXT NOT NULL,
    spatial_resource_key TEXT NOT NULL DEFAULT '',
    capacity_per_hour INTEGER NOT NULL,
    price_minor INTEGER NOT NULL DEFAULT 0,
    duration_minutes INTEGER NOT NULL,
    quality INTEGER NOT NULL DEFAULT 70,
    status TEXT NOT NULL DEFAULT 'active',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_item_id) REFERENCES catalog_items(id) ON DELETE RESTRICT,
    CHECK (capacity_per_hour > 0),
    CHECK (price_minor >= 0),
    CHECK (duration_minutes > 0),
    CHECK (quality BETWEEN 0 AND 100),
    CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS service_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_key TEXT NOT NULL UNIQUE,
    offering_id INTEGER NOT NULL,
    consumer_actor_key TEXT NOT NULL,
    consumer_resident_id INTEGER,
    status TEXT NOT NULL DEFAULT 'requested',
    quantity INTEGER NOT NULL DEFAULT 1,
    price_minor INTEGER NOT NULL DEFAULT 0,
    requested_at TEXT NOT NULL,
    delivered_at TEXT NOT NULL DEFAULT '',
    world_action_execution_id INTEGER,
    ledger_transaction_id INTEGER,
    result_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (offering_id) REFERENCES service_offerings(id) ON DELETE RESTRICT,
    FOREIGN KEY (consumer_resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (world_action_execution_id) REFERENCES world_action_executions(id) ON DELETE SET NULL,
    FOREIGN KEY (ledger_transaction_id) REFERENCES ledger_transactions(id) ON DELETE SET NULL,
    CHECK (quantity > 0),
    CHECK (price_minor >= 0),
    CHECK (status IN ('requested', 'queued', 'in_progress', 'delivered', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_inventory_accounts_item_owner ON inventory_accounts(item_id, owner_actor_key);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_account ON inventory_movements(inventory_account_id, id);
CREATE INDEX IF NOT EXISTS idx_production_batches_due ON production_batches(status, due_at, id);
CREATE INDEX IF NOT EXISTS idx_service_deliveries_status ON service_deliveries(status, requested_at, id);
"""

