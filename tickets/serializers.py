"""
FiberTrack Tickets - Serializers DRF.
"""
from django.utils import timezone
from rest_framework import serializers

from tickets.models import Ticket, TicketStatusHistory, TicketComment, TechnicianProfile, DiagnosisLog


class TechnicianProfileSerializer(serializers.ModelSerializer):
    """Serializer ligero del perfil de técnico."""
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    active_tickets = serializers.IntegerField(source='active_ticket_count', read_only=True)

    class Meta:
        model = TechnicianProfile
        fields = [
            'id', 'user_id', 'username', 'name', 'skills', 'max_workload',
            'current_latitude', 'current_longitude', 'is_available',
            'active_tickets', 'location_updated_at'
        ]


class TicketStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True, default=None)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    previous_status_display = serializers.CharField(source='get_previous_status_display', read_only=True)

    class Meta:
        model = TicketStatusHistory
        fields = [
            'id', 'previous_status', 'previous_status_display',
            'new_status', 'new_status_display', 'reason',
            'changed_by_name', 'created_at'
        ]


class TicketCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True, default=None)

    class Meta:
        model = TicketComment
        fields = ['id', 'author_name', 'text', 'visibility', 'created_at', 'edited']
        read_only_fields = ['author', 'created_at', 'edited']


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer para listados: campos mínimos."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True, default=None)
    client_code = serializers.CharField(source='client.client_code', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default='Sin asignar')
    box_code = serializers.CharField(source='affected_box.code', read_only=True, default=None)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'code', 'title', 'status', 'status_display',
            'priority', 'priority_display', 'ticket_type', 'type_display',
            'client_name', 'client_code', 'box_code',
            'assigned_to', 'assigned_to_name', 'address',
            'latitude', 'longitude', 'created_at', 'due_at', 'is_overdue'
        ]


class DiagnosisLogSerializer(serializers.ModelSerializer):
    """Serializer ligero para registros de diagnostico asociados a un ticket."""
    box_code = serializers.CharField(source='box.code', read_only=True)
    splitter_code = serializers.CharField(source='splitter.code', read_only=True, default=None)

    class Meta:
        model = DiagnosisLog
        fields = [
            'id', 'box_code', 'splitter_code', 'severity', 'confidence',
            'power_analysis', 'affected_clients', 'possible_solutions',
            'recommended_action', 'affected_route', 'solution_applied',
            'resolved', 'resolved_at', 'created_at'
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de ticket."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True, default=None)
    client_code = serializers.CharField(source='client.client_code', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default='Sin asignar')
    coordinator_name = serializers.CharField(source='coordinator.get_full_name', read_only=True, default=None)
    box_code = serializers.CharField(source='affected_box.code', read_only=True, default=None)
    splitter_code = serializers.CharField(source='affected_splitter.code', read_only=True, default=None)
    status_history = TicketStatusHistorySerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    diagnosis_logs = DiagnosisLogSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'code', 'title', 'description',
            'ticket_type', 'type_display',
            'priority', 'priority_display',
            'status', 'status_display',
            'client', 'client_name', 'client_code',
            'affected_box', 'box_code',
            'affected_splitter', 'splitter_code',
            'address', 'latitude', 'longitude',
            'assigned_to', 'assigned_to_name',
            'coordinator', 'coordinator_name',
            'sla_hours', 'due_at',
            'root_cause', 'solution_applied', 'resolution_notes', 'optical_power_final',
            'tracking_token', 'estimated_resolution',
            'created_by', 'created_at', 'updated_at',
            'assigned_at', 'started_at', 'resolved_at', 'closed_at',
            'is_overdue', 'duration_hours',
            'status_history', 'comments', 'diagnosis_logs'
        ]
        read_only_fields = ['code', 'tracking_token', 'created_at', 'updated_at']

    def get_comments(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role in ['admin', 'supervisor']:
                qs = obj.comments.all()
            else:
                qs = obj.comments.filter(visibility__in=['client', 'internal'])
        else:
            qs = obj.comments.filter(visibility='client')
        return TicketCommentSerializer(qs, many=True).data


class TicketCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar tickets."""
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'ticket_type', 'priority',
            'client', 'affected_box', 'affected_splitter',
            'address', 'latitude', 'longitude',
            'sla_hours', 'estimated_resolution'
        ]

    def validate(self, data):
        if data.get('affected_box') and data.get('client'):
            if data['client'].box != data['affected_box']:
                raise serializers.ValidationError({
                    'affected_box': 'La caja afectada no coincide con la caja del cliente seleccionado.'
                })
        return data


class TicketTransitionSerializer(serializers.Serializer):
    """Serializer para cambios de estado."""
    new_status = serializers.ChoiceField(choices=Ticket.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate_new_status(self, value):
        ticket = self.context.get('ticket')
        if ticket and not ticket.can_transition_to(value):
            raise serializers.ValidationError(
                f"Transición no permitida desde '{ticket.get_status_display()}' a '{dict(Ticket.Status.choices).get(value, value)}'."
            )
        return value


class TicketAssignSerializer(serializers.Serializer):
    """Serializer para asignar un ticket a un técnico."""
    technician_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class TicketCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketComment
        fields = ['text', 'visibility']


class TrackingSerializer(serializers.ModelSerializer):
    """Serializer público para el portal de seguimiento."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_ticket_type_display', read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'code', 'title', 'status', 'status_display',
            'ticket_type', 'type_display',
            'address', 'created_at', 'estimated_resolution',
            'duration_hours', 'timeline'
        ]

    def get_timeline(self, obj):
        events = []
        events.append({
            'status': 'open',
            'label': 'Incidencia registrada',
            'date': obj.created_at,
            'completed': True
        })
        if obj.assigned_at:
            events.append({
                'status': 'assigned',
                'label': 'Técnico asignado',
                'date': obj.assigned_at,
                'completed': True
            })
        if obj.started_at:
            events.append({
                'status': 'in_progress',
                'label': 'Reparación en curso',
                'date': obj.started_at,
                'completed': True
            })
        if obj.resolved_at:
            events.append({
                'status': 'resolved',
                'label': 'Reparación completada',
                'date': obj.resolved_at,
                'completed': True
            })
        if obj.closed_at:
            events.append({
                'status': 'closed',
                'label': 'Incidencia resuelta',
                'date': obj.closed_at,
                'completed': True
            })
        return events
