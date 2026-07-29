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
        && python scripts/seed_spatial_foundation.py"

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python scripts/init_campus_safe.py && python scripts/prepare_legacy_schema.py && python scripts/migrate_db.py && python scripts/seed_spatial_foundation.py && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
