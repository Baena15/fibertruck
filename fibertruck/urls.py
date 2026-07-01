"""
FiberTruck main URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse
import os


def serve_index(request):
    """Serve the static index.html for the React frontend."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'index.html'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'index.html'),
        os.path.join('/app', 'static', 'frontend', 'index.html'),
        os.path.join('/app', 'staticfiles', 'frontend', 'index.html'),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return HttpResponse(f.read(), content_type='text/html')
    # Fallback: return inline HTML with app.js reference
    return HttpResponse('''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FiberTruck - Diagnostico FTTH Cieza</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://cdn.tailwindcss.com"></script>
</head><body class="bg-gray-100"><div id="root"></div>
<script type="text/javascript" src="/static/frontend/app.js"></script>
</body></html>''', content_type='text/html')


def serve_app_js(request):
    """Serve the React app.js file."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'app.js'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'app.js'),
        os.path.join('/app', 'static', 'frontend', 'app.js'),
        os.path.join('/app', 'staticfiles', 'frontend', 'app.js'),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return HttpResponse(f.read(), content_type='application/javascript')
    return HttpResponse('// app.js not found', content_type='application/javascript', status=404)


def serve_app_jsx(request):
    """Backward compat: redirect old app.jsx requests to app.js."""
    return serve_app_js(request)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('network.urls')),
    path('static/frontend/app.js', serve_app_js),
    path('static/frontend/app.jsx', serve_app_jsx),
    path('', serve_index, name='frontend'),
]
