FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Validate the full bootstrap path without depending on a runtime disk or database.
RUN mkdir -p /app/data /tmp/campus-build \
    && DATABASE_URL="" DB_PATH="/tmp/campus-build/city.db" sh -c \
       "python scripts/init_campus_safe.py \
        && python scripts/prepare_legacy_schema.py \
        && python scripts/migrate_db.py \
        && python scripts/seed_spatial_foundation.py \
        && python scripts/seed_economy_foundation.py \
        && python scripts/seed_organization_runtime.py \
        && python scripts/seed_supply_foundation.py \
        && python scripts/seed_labor_runtime.py \
        && python scripts/seed_budget_runtime.py \
        && python scripts/seed_market_runtime.py \
        && python scripts/seed_credit_runtime.py \
        && python scripts/seed_public_policy_runtime.py \
        && python scripts/seed_social_institution_runtime.py \
        && python scripts/seed_macro_runtime.py \
        && python scripts/seed_adaptation_runtime.py \
        && python scripts/seed_resilience_runtime.py \
        && python scripts/seed_population_runtime.py \
        && python scripts/seed_external_world.py \
        && python scripts/seed_longitudinal_runtime.py \
        && python scripts/audit_economy_ledger.py"

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
