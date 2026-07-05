"""
FiberTruck main URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import connection
import os


def health_check(request):
    """Public health endpoint for Railway / load balancers."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=503)


def serve_index(request):
    """Serve the Django template for the React frontend (Babel + app.jsx)."""
    return render(request, 'frontend/index.html')


def serve_app_v9(request):
    """Serve the React app.v9.js file."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'app.v9.js'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'app.v9.js'),
        os.path.join('/app', 'static', 'frontend', 'app.v9.js'),
        os.path.join('/app', 'staticfiles', 'frontend', 'app.v9.js'),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='application/javascript')
    return HttpResponse('// app.v9.js not found', content_type='application/javascript', status=404)


# Backward compat: serve old app.js and app.jsx requests
def serve_app_js(request):
    return serve_app_v9(request)


def serve_app_jsx(request):
    return serve_app_v9(request)


def serve_app_v7(request):
    """Backward compat for old v7 references."""
    return serve_app_v9(request)


def serve_sw_js(request):
    """Serve service worker from root scope."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'sw.js'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'sw.js'),
        os.path.join('/app', 'static', 'frontend', 'sw.js'),
        os.path.join('/app', 'staticfiles', 'frontend', 'sw.js'),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='application/javascript')
    return HttpResponse('// sw.js not found', content_type='application/javascript', status=404)


def serve_manifest(request):
    """Serve PWA manifest."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'manifest.json'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'manifest.json'),
        os.path.join('/app', 'static', 'frontend', 'manifest.json'),
        os.path.join('/app', 'staticfiles', 'frontend', 'manifest.json'),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='application/json')
    return HttpResponse('{}', content_type='application/json', status=404)


def serve_icon(request, path):
    """Serve PWA icons from static/frontend/icons/."""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'frontend', 'icons', path),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'frontend', 'icons', path),
        os.path.join('/app', 'static', 'frontend', 'icons', path),
        os.path.join('/app', 'staticfiles', 'frontend', 'icons', path),
    ]
    for file_path in possible_paths:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
    return HttpResponse('', status=404)


urlpatterns = [
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('network.urls')),
    path('api/', include('tickets.urls')),
    path('sw.js', serve_sw_js),
    path('manifest.json', serve_manifest),
    path('static/frontend/icons/<path:path>', serve_icon),
    path('static/frontend/app.v9.js', serve_app_v9),
    path('static/frontend/app.v7.js', serve_app_v7),
    path('static/frontend/app.js', serve_app_js),
    path('static/frontend/app.jsx', serve_app_jsx),
    path('', serve_index, name='frontend'),
]
