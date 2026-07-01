"""
FiberTruck API URLs
"""
from rest_framework.routers import DefaultRouter
from .views import OLTViewSet, ZoneViewSet, SplitterViewSet, FiberBoxViewSet, ClientViewSet, FiberIncidentViewSet

router = DefaultRouter()
router.register(r'olts', OLTViewSet)
router.register(r'zones', ZoneViewSet)
router.register(r'splitters', SplitterViewSet)
router.register(r'boxes', FiberBoxViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'incidents', FiberIncidentViewSet)

urlpatterns = router.urls
