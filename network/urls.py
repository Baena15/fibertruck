"""
FiberTruck API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OLTViewSet, ZoneViewSet, SplitterViewSet, FiberBoxViewSet,
    ClientViewSet, FiberIncidentViewSet, setup_view,
    # Nuevos ViewSets FTTH
    FiberCableViewSet, SpliceClosureViewSet, CableSegmentViewSet,
    FiberAssignmentViewSet,
    # Nuevos endpoints avanzados
    diagnose_v2, topology_view,
)

router = DefaultRouter()
router.register(r'olts', OLTViewSet)
router.register(r'zones', ZoneViewSet)
router.register(r'splitters', SplitterViewSet)
router.register(r'boxes', FiberBoxViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'incidents', FiberIncidentViewSet)
# Nuevos routers FTTH
router.register(r'cables', FiberCableViewSet)
router.register(r'splices', SpliceClosureViewSet)
router.register(r'segments', CableSegmentViewSet)
router.register(r'assignments', FiberAssignmentViewSet)

urlpatterns = [
    path('setup/', setup_view, name='setup'),
    # Nuevos endpoints avanzados
    path('diagnose/v2/', diagnose_v2, name='diagnose-v2'),
    path('topology/', topology_view, name='topology'),
] + router.urls
