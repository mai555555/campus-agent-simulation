"""Enable row-level security on public runtime tables.

Revision ID: 20260730_0031
Revises: 20260730_0030
"""

from alembic import op
import sqlalchemy as sa


revision = "20260730_0031"
down_revision = "20260730_0030"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                table_record record;
            BEGIN
                FOR table_record IN
                    SELECT quote_ident(n.nspname) AS schema_name,
                           quote_ident(c.relname) AS table_name
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = current_schema()
                      AND c.relkind = 'r'
                LOOP
                    EXECUTE format(
                        'ALTER TABLE %s.%s ENABLE ROW LEVEL SECURITY',
                        table_record.schema_name,
                        table_record.table_name
                    );
                END LOOP;
            END $$;
            """
        )
    )


def downgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                table_record record;
            BEGIN
                FOR table_record IN
                    SELECT quote_ident(n.nspname) AS schema_name,
                           quote_ident(c.relname) AS table_name
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = current_schema()
                      AND c.relkind = 'r'
                LOOP
                    EXECUTE format(
                        'ALTER TABLE %s.%s DISABLE ROW LEVEL SECURITY',
                        table_record.schema_name,
                        table_record.table_name
                    );
                END LOOP;
            END $$;
            """
        )
    )
