"""
FiberTruck API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OLTViewSet, ZoneViewSet, SplitterViewSet, FiberBoxViewSet,
    ClientViewSet, FiberIncidentViewSet, setup_view
)

router = DefaultRouter()
router.register(r'olts', OLTViewSet)
router.register(r'zones', ZoneViewSet)
router.register(r'splitters', SplitterViewSet)
router.register(r'boxes', FiberBoxViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'incidents', FiberIncidentViewSet)

urlpatterns = [
    path('setup/', setup_view, name='setup'),
] + router.urls
