"""
FiberTrack Tickets - App configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tickets'
    verbose_name = _('Gestión de Tickets')

    def ready(self):
        import tickets.signals  # noqa: F401
