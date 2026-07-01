"""
FiberTruck API URLs
Rutas completas para la API FTTH de ingenieria de red.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OLTViewSet, ZoneViewSet, SplitterViewSet, FiberBoxViewSet,
    ClientViewSet, FiberIncidentViewSet, setup_view,
    FiberCableViewSet, SpliceClosureViewSet, CableSegmentViewSet,
    FiberAssignmentViewSet, diagnose_v2, topology_view, fiber_trace_view
)

router = DefaultRouter()
router.register(r'olts', OLTViewSet)
router.register(r'zones', ZoneViewSet)
router.register(r'splitters', SplitterViewSet)
router.register(r'boxes', FiberBoxViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'incidents', FiberIncidentViewSet)
router.register(r'cables', FiberCableViewSet)
router.register(r'splices', SpliceClosureViewSet)
router.register(r'segments', CableSegmentViewSet)
router.register(r'fiber-assignments', FiberAssignmentViewSet)

urlpatterns = [
    path('setup/', setup_view, name='setup'),
    path('diagnose/v2/', diagnose_v2, name='diagnose_v2'),
    path('topology/', topology_view, name='topology'),
    path('fiber-trace/', fiber_trace_view, name='fiber_trace'),
] + router.urls
