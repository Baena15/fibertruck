"""
FiberTruck - Custom User Model con roles
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario con roles especificos para FiberTruck"""
    ROLES = [
        ('admin', 'Administrador'),
        ('technician', 'Tecnico de campo'),
        ('supervisor', 'Supervisor/NOC'),
    ]

    role = models.CharField(max_length=20, choices=ROLES, default='technician', verbose_name='Rol')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefono')
    zone_assigned = models.ForeignKey(
        'network.Zone', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='technicians', verbose_name='Zona asignada'
    )
    is_available = models.BooleanField(default=True, verbose_name='Disponible')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
