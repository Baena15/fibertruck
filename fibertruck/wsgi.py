"""
WSGI config for fibertruck project.
Runs migrate + auto_setup before serving requests.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fibertruck.settings')

import django
django.setup()

from django.core.management import call_command
try:
    call_command('migrate', verbosity=0)
    call_command('auto_setup', verbosity=0)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
