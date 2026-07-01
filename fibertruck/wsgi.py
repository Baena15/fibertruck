"""
WSGI config for fibertruck project.
Runs migrate + auto_setup before serving requests (Railway compatible).
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fibertruck.settings')

# Run migrations and auto-setup before creating the WSGI application
import django
django.setup()

from django.core.management import call_command
try:
    call_command('migrate', verbosity=0)
    call_command('auto_setup', verbosity=0)
except Exception:
    pass  # Continue even if setup fails (e.g., DB already configured)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
