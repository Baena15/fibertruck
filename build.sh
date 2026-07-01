#!/usr/bin/env bash
# FiberTruck - Build script for Railway (only static files)
set -o errexit

echo "=== FiberTruck Build ==="
python manage.py collectstatic --no-input
echo "=== Static files collected ==="
