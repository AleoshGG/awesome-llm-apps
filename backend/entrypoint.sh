#!/bin/sh
set -e

echo "=== Initializing Demo Ntry Backend ==="

# 1. Wait for database connection
echo "Checking database connectivity..."
python - << 'EOF'
import sys
import time
import psycopg
from src.core.settings.settings import settings

max_retries = 30
interval = 2
connection_kwargs = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "dbname": settings.DB_NAME,
}

for attempt in range(1, max_retries + 1):
    try:
        with psycopg.connect(**connection_kwargs, connect_timeout=3) as conn:
            print("Database connection successfully established.")
            sys.exit(0)
    except Exception as exc:
        print(f"Waiting for database to be ready (attempt {attempt}/{max_retries}): {exc}")
        time.sleep(interval)

print("Error: Timed out waiting for database.", file=sys.stderr)
sys.exit(1)
EOF

# 2. Run database migrations with Alembic
echo "Applying database migrations..."
alembic upgrade head

# 3. Seed mock catalog SQL file
echo "Applying mock catalog data..."
python - << 'EOF'
import sys
import psycopg
from src.core.settings.settings import settings

sql_file = "src/core/db/seeds/mock_catalog.sql"
print(f"Executing SQL file: {sql_file}")
try:
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    with psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dbname=settings.DB_NAME,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Mock catalog SQL loaded successfully.")
except Exception as exc:
    print(f"Error loading mock catalog SQL: {exc}", file=sys.stderr)
    sys.exit(1)
EOF

echo "Backend ready. Launching application..."
exec "$@"
