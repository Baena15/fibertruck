#!/usr/bin/env bash
# FiberTruck - Build script for Railway

set -o errexit

echo "=== FiberTruck Build ==="

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Populate Cieza data if empty
python -c "
import django
django.setup()
from network.models import Zone
if Zone.objects.count() == 0:
    from django.core.management import call_command
    call_command('populate_cieza')
    print('Cieza data populated')
else:
    print('Data already exists, skipping population')
"

echo "=== Build complete ==="
