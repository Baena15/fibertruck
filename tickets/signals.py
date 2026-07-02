"""
FiberTrack Tickets - Signals

Crea automáticamente un TechnicianProfile cuando se crea un usuario
con rol 'technician'.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_technician_profile(sender, instance, created, **kwargs):
    """Crea perfil de técnico para nuevos usuarios con role='technician'."""
    if created and instance.role == 'technician':
        from tickets.models import TechnicianProfile
        TechnicianProfile.objects.get_or_create(user=instance)
