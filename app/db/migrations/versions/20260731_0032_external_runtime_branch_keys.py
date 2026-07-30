"""Backfill unique branch keys for external runtime state tables.

Revision ID: 20260731_0032
Revises: 20260730_0031
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0032"
down_revision = "20260730_0031"
branch_labels = None
depends_on = None


def _dedupe_by_latest_updated_at(table_name):
    op.execute(
        sa.text(
            f"""
            DELETE FROM {table_name}
            WHERE ctid IN (
                SELECT ctid
                FROM (
                    SELECT ctid,
                           row_number() OVER (
                               PARTITION BY branch_key
                               ORDER BY updated_at DESC, ctid DESC
                           ) AS row_number
                    FROM {table_name}
                ) ranked_rows
                WHERE row_number > 1
            )
            """
        )
    )


def _dedupe_by_latest_evaluated_at(table_name):
    op.execute(
        sa.text(
            f"""
            DELETE FROM {table_name}
            WHERE ctid IN (
                SELECT ctid
                FROM (
                    SELECT ctid,
                           row_number() OVER (
                               PARTITION BY branch_key
                               ORDER BY last_evaluated_at DESC, ctid DESC
                           ) AS row_number
                    FROM {table_name}
                ) ranked_rows
                WHERE row_number > 1
            )
            """
        )
    )


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    _dedupe_by_latest_updated_at("external_runtime_modes")
    _dedupe_by_latest_evaluated_at("external_runtime_health")
    op.create_unique_constraint(
        "uq_external_runtime_modes_branch_key",
        "external_runtime_modes",
        ["branch_key"],
    )
    op.create_unique_constraint(
        "uq_external_runtime_health_branch_key",
        "external_runtime_health",
        ["branch_key"],
    )


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    op.drop_constraint(
        "uq_external_runtime_health_branch_key",
        "external_runtime_health",
        type_="unique",
    )
    op.drop_constraint(
        "uq_external_runtime_modes_branch_key",
        "external_runtime_modes",
        type_="unique",
    )
