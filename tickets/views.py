"""
FiberTrack Tickets - API REST Views.
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from tickets.models import Ticket, TicketComment, TechnicianProfile
from tickets.serializers import (
    TicketListSerializer, TicketDetailSerializer, TicketCreateUpdateSerializer,
    TicketTransitionSerializer, TicketAssignSerializer,
    TicketCommentCreateSerializer, TrackingSerializer,
    TechnicianProfileSerializer
)
from tickets.permissions import (
    IsAdminOrSupervisor, IsTicketManagerOrAssignedTechnician, ReadOnly
)
from tickets.services.assignment import suggest_technicians


User = get_user_model()


class TicketViewSet(viewsets.ModelViewSet):
    """
    API REST para gestión de tickets de incidencias.

    - Admin/Supervisor: CRUD completo y asignaciones.
    - Técnico: solo lectura/escritura de sus tickets asignados.
    """

    def get_queryset(self):
        user = self.request.user
        base_qs = Ticket.objects.select_related(
            'client', 'affected_box', 'affected_splitter',
            'assigned_to', 'coordinator', 'created_by'
        ).prefetch_related('status_history', 'comments')

        if user.role in ['admin', 'supervisor']:
            return base_qs.all()
        if user.role == 'technician':
            return base_qs.filter(assigned_to=user)
        return base_qs.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return TicketCreateUpdateSerializer
        if self.action == 'transition':
            return TicketTransitionSerializer
        if self.action == 'assign':
            return TicketAssignSerializer
        if self.action == 'add_comment':
            return TicketCommentCreateSerializer
        return TicketDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'assign', 'suggest']:
            return [permissions.IsAuthenticated(), IsAdminOrSupervisor()]
        if self.action in ['transition', 'add_comment']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        ticket = serializer.save(created_by=self.request.user)
        self._log_status_change(ticket, None, ticket.status, 'Ticket creado')

    def _log_status_change(self, ticket, previous, new, reason, user=None):
        from tickets.models import TicketStatusHistory
        TicketStatusHistory.objects.create(
            ticket=ticket,
            previous_status=previous or 'open',
            new_status=new,
            reason=reason,
            changed_by=user or self.request.user
        )

    @action(detail=True, methods=['post'], url_path='transition')
    def transition(self, request, pk=None):
        """Cambia el estado de un ticket validando la transición permitida."""
        ticket = self.get_object()
        user = request.user

        # Validación de permisos a nivel de objeto
        if user.role == 'technician' and ticket.assigned_to != user:
            raise PermissionDenied('No estás asignado a este ticket.')

        serializer = TicketTransitionSerializer(
            data=request.data,
            context={'ticket': ticket, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['new_status']
        reason = serializer.validated_data.get('reason', '')
        previous_status = ticket.status

        # Actualizar timestamps según estado destino
        now = timezone.now()
        if new_status == 'assigned' and not ticket.assigned_at:
            ticket.assigned_at = now
        if new_status == 'in_progress' and not ticket.started_at:
            ticket.started_at = now
        if new_status == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = now
        if new_status == 'closed' and not ticket.closed_at:
            ticket.closed_at = now
        if new_status == 'reopened':
            ticket.resolved_at = None
            ticket.closed_at = None

        ticket.status = new_status
        ticket.save()

        self._log_status_change(ticket, previous_status, new_status, reason)

        return Response({
            'success': True,
            'ticket': TicketDetailSerializer(ticket, context={'request': request}).data
        })

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        """Asigna un ticket a un técnico y registra el histórico."""
        ticket = self.get_object()
        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tech_id = serializer.validated_data['technician_id']
        reason = serializer.validated_data.get('reason', '')

        try:
            technician = User.objects.get(pk=tech_id, role='technician')
        except User.DoesNotExist:
            return Response(
                {'error': 'Técnico no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        previous_status = ticket.status
        ticket.assigned_to = technician
        ticket.coordinator = request.user
        if ticket.status == 'open':
            ticket.status = 'assigned'
            ticket.assigned_at = timezone.now()
        ticket.save()

        self._log_status_change(
            ticket, previous_status, ticket.status,
            f'Asignado a {technician.get_full_name() or technician.username}. {reason}'
        )

        return Response({
            'success': True,
            'ticket': TicketDetailSerializer(ticket, context={'request': request}).data
        })

    @action(detail=True, methods=['get'], url_path='suggest')
    def suggest(self, request, pk=None):
        """Sugiere los técnicos más adecuados para este ticket."""
        ticket = self.get_object()
        limit = int(request.query_params.get('limit', 3))
        suggestions = suggest_technicians(ticket, limit=limit)
        return Response({
            'ticket': ticket.code,
            'suggestions': suggestions
        })

    @action(detail=True, methods=['post'], url_path='comments')
    def add_comment(self, request, pk=None):
        """Añade un comentario a un ticket."""
        ticket = self.get_object()
        user = request.user

        if user.role == 'technician' and ticket.assigned_to != user:
            raise PermissionDenied('No estás asignado a este ticket.')

        serializer = TicketCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save(ticket=ticket, author=user)
        return Response({
            'success': True,
            'comment': {
                'id': comment.id,
                'author_name': user.get_full_name() or user.username,
                'text': comment.text,
                'visibility': comment.visibility,
                'created_at': comment.created_at
            }
        }, status=status.HTTP_201_CREATED)


class TechnicianProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API REST de solo lectura para perfiles de técnicos.
    Útil para el panel de coordinador.
    """
    queryset = TechnicianProfile.objects.select_related('user').filter(user__is_active=True)
    serializer_class = TechnicianProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        """Devuelve técnicos disponibles."""
        qs = self.get_queryset().filter(is_available=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def tracking_view(request, code):
    """
    Portal público de seguimiento de ticket.
    No requiere autenticación.
    """
    ticket = get_object_or_404(Ticket, code__iexact=code)
    serializer = TrackingSerializer(ticket)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ticket_stats_view(request):
    """
    Estadísticas de tickets para el dashboard.
    """
    user = request.user
    base_qs = Ticket.objects.all()
    if user.role == 'technician':
        base_qs = base_qs.filter(assigned_to=user)

    return Response({
        'total': base_qs.count(),
        'open': base_qs.filter(status='open').count(),
        'assigned': base_qs.filter(status='assigned').count(),
        'in_progress': base_qs.filter(status='in_progress').count(),
        'resolved': base_qs.filter(status='resolved').count(),
        'closed': base_qs.filter(status='closed').count(),
        'escalated': base_qs.filter(status='escalated').count(),
        'overdue': base_qs.filter(status__in=['open', 'assigned', 'in_progress'], due_at__lt=timezone.now()).count(),
    })
