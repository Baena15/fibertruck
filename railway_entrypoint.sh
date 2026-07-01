#!/usr/bin/env bash
set -e

echo "=== FiberTruck Railway Entrypoint ==="
echo "Step 1: Remove old SQLite db..."
rm -f db.sqlite3
rm -f /app/db.sqlite3

echo "Step 2: Run migrations..."
python manage.py migrate --verbosity 2

echo "Step 3: Run auto_setup..."
python manage.py auto_setup --verbosity 2

echo "Step 4: Start gunicorn..."
exec gunicorn fibertruck.wsgi:application --bind 0.0.0.0:$PORT
