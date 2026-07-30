"""Backfill unique constraints required by runtime upserts.

Revision ID: 20260731_0033
Revises: 20260731_0032
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0033"
down_revision = "20260731_0032"
branch_labels = None
depends_on = None


UPSERT_CONSTRAINTS = (
    (
        "uq_household_budget_snapshots_resident_date",
        "household_budget_snapshots",
        ("resident_id", "budget_date"),
    ),
    (
        "uq_longitudinal_aggregations_key",
        "longitudinal_aggregations",
        ("aggregation_key",),
    ),
    (
        "uq_macro_metric_values_scope",
        "macro_metric_values",
        ("snapshot_id", "metric_definition_id", "group_type", "group_key"),
    ),
    (
        "uq_macro_reconciliation_checks_snapshot_key",
        "macro_reconciliation_checks",
        ("snapshot_id", "check_key"),
    ),
    (
        "uq_membership_transitions_org_resident",
        "membership_transitions",
        ("organization_id", "resident_id"),
    ),
    (
        "uq_organization_relationships_pair",
        "organization_relationships",
        ("from_organization_id", "to_organization_id"),
    ),
)


def _column_list(columns):
    return ", ".join(columns)


def _dedupe(table_name, columns):
    partition = _column_list(columns)
    op.execute(
        sa.text(
            f"""
            DELETE FROM {table_name}
            WHERE ctid IN (
                SELECT ctid
                FROM (
                    SELECT ctid,
                           row_number() OVER (
                               PARTITION BY {partition}
                               ORDER BY ctid DESC
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

    for name, table_name, columns in UPSERT_CONSTRAINTS:
        _dedupe(table_name, columns)
        op.create_unique_constraint(name, table_name, list(columns))


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    for name, table_name, _columns in reversed(UPSERT_CONSTRAINTS):
        op.drop_constraint(name, table_name, type_="unique")
