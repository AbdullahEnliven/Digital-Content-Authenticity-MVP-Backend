#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U trust_user -d trust_db >/dev/null 2>&1; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
