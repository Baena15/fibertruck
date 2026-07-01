"""
FiberTruck main URLs
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
import os

def serve_index(request):
    """Serve the static index.html for the React frontend."""
    index_path = os.path.join(settings.BASE_DIR, 'static', 'frontend', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'))
    # Fallback to staticfiles (production after collectstatic)
    index_path_prod = os.path.join(settings.STATIC_ROOT, 'frontend', 'index.html')
    if os.path.exists(index_path_prod):
        return FileResponse(open(index_path_prod, 'rb'))
    from django.http import HttpResponse
    return HttpResponse('<h1>FiberTruck</h1><p>Loading...</p>', content_type='text/html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('network.urls')),
    path('', serve_index, name='frontend'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
