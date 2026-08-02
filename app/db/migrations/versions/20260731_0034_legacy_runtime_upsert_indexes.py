"""Repair legacy PostgreSQL upsert targets.

Revision ID: 20260731_0034
Revises: 20260731_0033

Older databases may already contain these tables without the primary-key or
unique constraints declared by the current schema.  ``CREATE TABLE IF NOT
EXISTS`` does not retrofit those constraints, so PostgreSQL rejects the
runtime's ``ON CONFLICT`` statements.
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
    (
        "uq_world_action_rules_type_version",
        "world_action_rules",
        ("action_type", "rule_version"),
    ),
)


def _quoted_csv(columns):
    return ", ".join(f'"{column}"' for column in columns)


def _dedupe_identical_seed_rules():
    # Legacy startup runs inserted the same 13 seed rules repeatedly.  Refuse
    # to merge a key if any business field differs; that requires a manual
    # decision rather than a migration silently discarding data.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF to_regclass(current_schema() || '.world_action_rules') IS NULL THEN
                    RETURN;
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM world_action_rules
                    GROUP BY action_type, rule_version
                    HAVING count(*) > 1
                       AND count(DISTINCT jsonb_build_array(
                           rule_key,
                           preconditions_json,
                           required_resources_json,
                           duration_minutes,
                           success_probability,
                           direct_effects_json,
                           delayed_effects_json,
                           failure_policy_json,
                           status
                       )) > 1
                ) THEN
                    RAISE EXCEPTION
                        'world_action_rules contains conflicting duplicate definitions';
                END IF;

                DELETE FROM world_action_rules
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id,
                               row_number() OVER (
                                   PARTITION BY action_type, rule_version
                                   ORDER BY id DESC
                               ) AS row_number
                        FROM world_action_rules
                    ) ranked_rows
                    WHERE row_number > 1
                );
            END $$;
            """
        )
    )


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

    _dedupe_identical_seed_rules()
    for index_name, table_name, columns in UPSERT_INDEXES:
        _create_unique_index(index_name, table_name, columns)


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    for index_name, _table_name, _columns in reversed(UPSERT_INDEXES):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))
