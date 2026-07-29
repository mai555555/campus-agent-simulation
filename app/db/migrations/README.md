# Database migrations

`20260729_0001` is a stamp-only baseline for databases created by the legacy
idempotent initializer. It does not recreate or delete existing business
tables.

During the transition:

1. `scripts/init_campus_safe.py` creates or preserves seed data.
2. `scripts/prepare_legacy_schema.py` brings all legacy tables to the complete
   baseline without resetting business data.
3. `scripts/migrate_db.py` validates and stamps an unversioned database at the
   baseline and upgrades it to the latest revision.
4. New spatial tables and later schema changes are added only through Alembic.

After all legacy tables have migration coverage, deployment can run Alembic
before seed-data initialization.
