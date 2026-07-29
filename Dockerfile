FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# A cloud deployment starts with a fresh, reproducible campus world.
RUN python scripts/init_campus.py \
    && python scripts/prepare_legacy_schema.py \
    && python scripts/migrate_db.py \
    && python scripts/seed_spatial_foundation.py

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
