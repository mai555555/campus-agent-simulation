"""Add missing unique indexes for legacy PostgreSQL upsert targets.

Revision ID: 20260731_0034
Revises: 20260731_0033

The production preflight verified that these four targets contain no duplicate
keys. This migration intentionally performs no automatic data deletion.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0034"
down_revision = "20260731_0033"
branch_labels = None
depends_on = None


UPSERT_INDEXES = (
    (
        "uq_agent_norm_beliefs_resident_norm",
        "agent_norm_beliefs",
        ("resident_id", "norm_id"),
    ),
    ("uq_norm_candidates_key", "norm_candidates", ("norm_key",)),
    (
        "uq_resident_power_profiles_resident",
        "resident_power_profiles",
        ("resident_id",),
    ),
    (
        "uq_strategy_states_resident_strategy_context",
        "strategy_states",
        ("resident_id", "strategy_key", "context_key"),
    ),
)


def _quoted_csv(columns):
    return ", ".join(f'"{column}"' for column in columns)


def _create_unique_index(index_name, table_name, columns):
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF to_regclass(current_schema() || '.{table_name}') IS NOT NULL THEN
                    EXECUTE 'CREATE UNIQUE INDEX IF NOT EXISTS {index_name} '
                         || 'ON ' || quote_ident(current_schema()) || '.{table_name} '
                         || '({_quoted_csv(columns)})';
                END IF;
            END $$;
            """
        )
    )


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    for index_name, table_name, columns in UPSERT_INDEXES:
        _create_unique_index(index_name, table_name, columns)


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    for index_name, _table_name, _columns in reversed(UPSERT_INDEXES):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))
