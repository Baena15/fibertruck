"""
FiberTrack Tickets - Permisos personalizados de DRF.
"""
from rest_framework import permissions


class IsAdminOrSupervisor(permissions.BasePermission):
    """Permite acceso a administradores y supervisores/coordinadores."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['admin', 'supervisor']
        )


class IsAssignedTechnician(permissions.BasePermission):
    """Permite acceso solo al técnico asignado al ticket."""
    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'technician'
            and obj.assigned_to == request.user
        )


class IsTicketManagerOrAssignedTechnician(permissions.BasePermission):
    """
    Admin/Supervisor pueden gestionar cualquier ticket;
    técnicos solo pueden leer/modificar los tickets que les están asignados.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'supervisor']:
            return True
        if request.user.role == 'technician':
            return obj.assigned_to == request.user
        return False


class ReadOnly(permissions.BasePermission):
    """Permite solo lectura."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
