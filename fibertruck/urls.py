"""
FiberTruck main URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import FileResponse, HttpResponse
import os
import mimetypes


def _serve_static_file(request, relative_path):
    """Serve a file from static or staticfiles dirs."""
    # Try source static dir first
    file_path = os.path.join(settings.BASE_DIR, 'static', relative_path)
    if not os.path.exists(file_path):
        # Fallback to collected staticfiles
        file_path = os.path.join(settings.STATIC_ROOT, relative_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        return response
    return HttpResponse(f'Not found: {relative_path}', status=404)


def serve_index(request):
    """Serve the static index.html for the React frontend."""
    return _serve_static_file(request, 'frontend/index.html')


def serve_app_jsx(request):
    """Serve the React app.jsx file."""
    return _serve_static_file(request, 'frontend/app.jsx')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('network.urls')),
    # Serve frontend files directly (no whitenoise dependency for these)
    path('static/frontend/app.jsx', serve_app_jsx),
    path('', serve_index, name='frontend'),
]
