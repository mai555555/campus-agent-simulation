"""Add goods, services, production, and inventory runtime.

Revision ID: 20260729_0011
Revises: 20260729_0010
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_0011"
down_revision = "20260729_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_key", sa.String(160), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("item_type", sa.String(16), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default="unit"),
        sa.Column("base_price_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("standard_cost_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("shelf_life_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("item_type IN ('good', 'service', 'input')", name="ck_catalog_items_type_valid"),
        sa.CheckConstraint("base_price_minor >= 0", name="ck_catalog_items_price_nonnegative"),
        sa.CheckConstraint("standard_cost_minor >= 0", name="ck_catalog_items_cost_nonnegative"),
        sa.CheckConstraint("shelf_life_hours >= 0", name="ck_catalog_items_shelf_nonnegative"),
        sa.CheckConstraint("quality BETWEEN 0 AND 100", name="ck_catalog_items_quality_valid"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_catalog_items_status_valid"),
    )
    op.create_table(
        "inventory_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("inventory_key", sa.String(200), nullable=False, unique=True),
        sa.Column("owner_actor_key", sa.String(120), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(80), nullable=False, server_default=""),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_point", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_cost_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["item_id"], ["catalog_items.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("owner_actor_key", "item_id", "location", name="uq_inventory_accounts_owner_item_location"),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_accounts_quantity_nonnegative"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_inventory_accounts_reserved_nonnegative"),
        sa.CheckConstraint("quantity_reserved <= quantity_on_hand", name="ck_inventory_accounts_reserved_valid"),
        sa.CheckConstraint("reorder_point >= 0", name="ck_inventory_accounts_reorder_nonnegative"),
        sa.CheckConstraint("target_stock >= reorder_point", name="ck_inventory_accounts_target_valid"),
        sa.CheckConstraint("average_cost_minor >= 0", name="ck_inventory_accounts_cost_nonnegative"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_inventory_accounts_status_valid"),
    )
    op.create_index("ix_inventory_accounts_item_owner", "inventory_accounts", ["item_id", "owner_actor_key"])
    op.create_table(
        "production_recipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipe_key", sa.String(160), nullable=False, unique=True),
        sa.Column("producer_actor_key", sa.String(120), nullable=False),
        sa.Column("output_item_id", sa.Integer(), nullable=False),
        sa.Column("output_quantity", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("cash_cost_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("location", sa.String(80), nullable=False),
        sa.Column("spatial_resource_key", sa.String(120), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["output_item_id"], ["catalog_items.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("output_quantity > 0", name="ck_production_recipes_output_positive"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_production_recipes_duration_positive"),
        sa.CheckConstraint("cash_cost_minor >= 0", name="ck_production_recipes_cash_nonnegative"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_production_recipes_status_valid"),
    )
    op.create_table(
        "production_recipe_inputs",
        sa.Column("recipe_id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), primary_key=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["production_recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["catalog_items.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_production_recipe_inputs_quantity_positive"),
    )
    op.create_table(
        "production_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_key", sa.String(200), nullable=False, unique=True),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="running"),
        sa.Column("output_quantity", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.String(64), nullable=False),
        sa.Column("due_at", sa.String(64), nullable=False),
        sa.Column("completed_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("ledger_transaction_id", sa.Integer()),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recipe_id"], ["production_recipes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL"),
        sa.CheckConstraint("output_quantity > 0", name="ck_production_batches_output_positive"),
        sa.CheckConstraint("status IN ('running', 'completed', 'failed', 'cancelled')", name="ck_production_batches_status_valid"),
    )
    op.create_index("ix_production_batches_due", "production_batches", ["status", "due_at", "id"])
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movement_key", sa.String(220), nullable=False, unique=True),
        sa.Column("inventory_account_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("unit_cost_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False, server_default=""),
        sa.Column("ledger_transaction_id", sa.Integer()),
        sa.Column("production_batch_id", sa.Integer()),
        sa.Column("occurred_at", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["inventory_account_id"], ["inventory_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["production_batch_id"], ["production_batches.id"], ondelete="SET NULL"),
        sa.CheckConstraint("quantity_delta <> 0", name="ck_inventory_movements_delta_nonzero"),
        sa.CheckConstraint("unit_cost_minor >= 0", name="ck_inventory_movements_cost_nonnegative"),
        sa.CheckConstraint("movement_type IN ('opening', 'purchase', 'sale', 'consumption', 'production_input', 'production_output', 'waste', 'adjustment')", name="ck_inventory_movements_type_valid"),
    )
    op.create_index("ix_inventory_movements_account", "inventory_movements", ["inventory_account_id", "id"])
    op.create_table(
        "service_offerings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offering_key", sa.String(160), nullable=False, unique=True),
        sa.Column("provider_actor_key", sa.String(120), nullable=False),
        sa.Column("service_item_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(80), nullable=False),
        sa.Column("spatial_resource_key", sa.String(120), nullable=False, server_default=""),
        sa.Column("capacity_per_hour", sa.Integer(), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["service_item_id"], ["catalog_items.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("capacity_per_hour > 0", name="ck_service_offerings_capacity_positive"),
        sa.CheckConstraint("price_minor >= 0", name="ck_service_offerings_price_nonnegative"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_service_offerings_duration_positive"),
        sa.CheckConstraint("quality BETWEEN 0 AND 100", name="ck_service_offerings_quality_valid"),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_service_offerings_status_valid"),
    )
    op.create_table(
        "service_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("delivery_key", sa.String(200), nullable=False, unique=True),
        sa.Column("offering_id", sa.Integer(), nullable=False),
        sa.Column("consumer_actor_key", sa.String(120), nullable=False),
        sa.Column("consumer_resident_id", sa.Integer()),
        sa.Column("status", sa.String(16), nullable=False, server_default="requested"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("requested_at", sa.String(64), nullable=False),
        sa.Column("delivered_at", sa.String(64), nullable=False, server_default=""),
        sa.Column("world_action_execution_id", sa.Integer()),
        sa.Column("ledger_transaction_id", sa.Integer()),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["offering_id"], ["service_offerings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["consumer_resident_id"], ["residents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["world_action_execution_id"], ["world_action_executions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ledger_transaction_id"], ["ledger_transactions.id"], ondelete="SET NULL"),
        sa.CheckConstraint("quantity > 0", name="ck_service_deliveries_quantity_positive"),
        sa.CheckConstraint("price_minor >= 0", name="ck_service_deliveries_price_nonnegative"),
        sa.CheckConstraint("status IN ('requested', 'queued', 'in_progress', 'delivered', 'failed', 'cancelled')", name="ck_service_deliveries_status_valid"),
    )
    op.create_index("ix_service_deliveries_status", "service_deliveries", ["status", "requested_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_service_deliveries_status", table_name="service_deliveries")
    op.drop_table("service_deliveries")
    op.drop_table("service_offerings")
    op.drop_index("ix_inventory_movements_account", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_production_batches_due", table_name="production_batches")
    op.drop_table("production_batches")
    op.drop_table("production_recipe_inputs")
    op.drop_table("production_recipes")
    op.drop_index("ix_inventory_accounts_item_owner", table_name="inventory_accounts")
    op.drop_table("inventory_accounts")
    op.drop_table("catalog_items")
