"""
FiberTrack Tickets - API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, TechnicianProfileViewSet, tracking_view, ticket_stats_view


router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'technicians', TechnicianProfileViewSet, basename='technician')

urlpatterns = [
    path('tracking/<str:code>/', tracking_view, name='ticket-tracking'),
    path('ticket-stats/', ticket_stats_view, name='ticket-stats'),
] + router.urls
