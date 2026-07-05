"""
FiberTrack Tickets - Gestión operativa de incidencias FTTH.

Modelos:
    TechnicianProfile  - Perfil extendido de técnicos de campo
    Ticket             - Ticket/incidencia operativa
    TicketStatusHistory - Trazabilidad de cambios de estado
    TicketComment      - Notas internas y visibles para el cliente
    TicketAttachment   - Evidencias fotográficas (Fase 1 básica)
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TechnicianProfile(models.Model):
    """
    Perfil extendido para usuarios con rol técnico.

    Incluye habilidades, ubicación actual, carga máxima y disponibilidad.
    Se crea automáticamente para usuarios con role='technician'.
    """

    class Skill(models.TextChoices):
        HOME = 'home', _('Avería en domicilio')
        NETWORK = 'network', _('Avería en red')
        SPLICING = 'splicing', _('Empalmes y fusiones')
        INSTALLATION = 'installation', _('Instalaciones')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='technician_profile',
        verbose_name=_('Usuario')
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Habilidades'),
        help_text=_('Lista de skills: home, network, splicing, installation')
    )
    max_workload = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_('Carga máxima de tickets activos'),
        help_text=_('Número máximo de tickets que puede tener asignados simultáneamente')
    )
    current_latitude = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Latitud actual')
    )
    current_longitude = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Longitud actual')
    )
    location_updated_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Última actualización de ubicación')
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Disponible')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Perfil de técnico')
        verbose_name_plural = _('Perfiles de técnicos')
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Técnico"

    @property
    def current_location(self):
        """Devuelve (lat, lng) o None."""
        if self.current_latitude is not None and self.current_longitude is not None:
            return (self.current_latitude, self.current_longitude)
        return None

    @property
    def active_ticket_count(self):
        """Tickets activos asignados al técnico."""
        return self.user.assigned_tickets.filter(
            status__in=['open', 'assigned', 'in_transit', 'in_progress']
        ).count()

    @property
    def is_overloaded(self):
        return self.active_ticket_count >= self.max_workload


class Ticket(models.Model):
    """
    Ticket operativo de gestión de incidencias FiberTrack.

    Representa el ciclo de vida completo de una avería reportada por un cliente
    desde su apertura hasta su cierre verificado.
    """

    class Status(models.TextChoices):
        OPEN = 'open', _('Abierto')
        ASSIGNED = 'assigned', _('Asignado')
        IN_TRANSIT = 'in_transit', _('En desplazamiento')
        IN_PROGRESS = 'in_progress', _('En trabajo')
        PAUSED = 'paused', _('Pausado')
        NEEDS_MATERIAL = 'needs_material', _('Pendiente de material')
        NEEDS_CLIENT = 'needs_client', _('Pendiente de cliente')
        RESOLVED = 'resolved', _('Resuelto - Pendiente verificación')
        ESCALATED = 'escalated', _('Escalado')
        CLOSED = 'closed', _('Cerrado')
        CANCELLED = 'cancelled', _('Cancelado')
        REOPENED = 'reopened', _('Reabierto')

    class Priority(models.TextChoices):
        LOW = 'low', _('Baja')
        MEDIUM = 'medium', _('Media')
        HIGH = 'high', _('Alta')
        CRITICAL = 'critical', _('Crítica')

    class Type(models.TextChoices):
        HOME_FAULT = 'home_fault', _('Avería en domicilio')
        NETWORK_FAULT = 'network_fault', _('Avería en red')
        DEGRADATION = 'degradation', _('Degradación de servicio')
        INSTALLATION = 'installation', _('Instalación nueva')
        MAINTENANCE = 'maintenance', _('Mantenimiento preventivo')

    # Identificación
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Código de ticket'),
        help_text=_('Formato: FT-YYYY-NNNNNN')
    )
    title = models.CharField(max_length=200, verbose_name=_('Título'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))

    # Clasificación
    ticket_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.HOME_FAULT,
        verbose_name=_('Tipo de incidencia')
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name=_('Prioridad')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name=_('Estado')
    )

    # Ubicación y cliente afectado
    client = models.ForeignKey(
        'network.Client',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets',
        verbose_name=_('Cliente afectado')
    )
    affected_box = models.ForeignKey(
        'network.FiberBox',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets',
        verbose_name=_('Caja afectada')
    )
    affected_splitter = models.ForeignKey(
        'network.Splitter',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets',
        verbose_name=_('Splitter afectado')
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_('Dirección de la incidencia')
    )
    latitude = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Latitud')
    )
    longitude = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Longitud')
    )

    # Asignaciones
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'role': 'technician'},
        verbose_name=_('Técnico asignado')
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='coordinated_tickets',
        limit_choices_to={'role__in': ['admin', 'supervisor']},
        verbose_name=_('Coordinador responsable')
    )

    # SLA y tiempos
    sla_hours = models.PositiveSmallIntegerField(
        default=24,
        verbose_name=_('SLA (horas)')
    )
    due_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Fecha límite de resolución')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Resolución
    root_cause = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Causa raíz')
    )
    solution_applied = models.TextField(
        blank=True,
        verbose_name=_('Solución aplicada')
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name=_('Notas de resolución')
    )
    optical_power_final = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Potencia óptica final (dBm)')
    )

    # Seguimiento cliente
    tracking_token = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        verbose_name=_('Token de seguimiento')
    )
    estimated_resolution = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Resolución estimada')
    )

    # Auditoría
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets_created',
        verbose_name=_('Creado por')
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"

    @property
    def is_open(self):
        return self.status not in ['closed', 'cancelled']

    @property
    def is_overdue(self):
        if self.due_at and self.status not in ['closed', 'cancelled']:
            return timezone.now() > self.due_at
        return False

    @property
    def duration_hours(self):
        """Duración desde apertura hasta cierre/resolución actual."""
        end = self.closed_at or self.resolved_at or timezone.now()
        return round((end - self.created_at).total_seconds() / 3600, 2)

    @property
    def location(self):
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None

    def can_transition_to(self, new_status):
        """Valida si la transición de estado es permitida."""
        transitions = {
            'open': ['assigned', 'escalated', 'cancelled'],
            'assigned': ['in_transit', 'open', 'escalated', 'cancelled'],
            'in_transit': ['in_progress', 'assigned', 'escalated'],
            'in_progress': ['paused', 'needs_material', 'needs_client', 'resolved', 'escalated'],
            'paused': ['in_progress'],
            'needs_material': ['in_progress'],
            'needs_client': ['in_progress'],
            'resolved': ['closed', 'reopened'],
            'escalated': ['assigned', 'in_progress', 'cancelled'],
            'reopened': ['assigned', 'escalated', 'cancelled'],
            'closed': ['reopened'],
            'cancelled': ['open'],
        }
        return new_status in transitions.get(self.status, [])

    def save(self, *args, **kwargs):
        # Generar código si es nuevo
        if not self.code:
            self.code = self._generate_code()
        # Generar token de seguimiento si es nuevo
        if not self.tracking_token:
            self.tracking_token = self._generate_tracking_token()
        # Calcular fecha límite SLA
        if self.sla_hours and not self.due_at:
            self.due_at = timezone.now() + timezone.timedelta(hours=self.sla_hours)
        super().save(*args, **kwargs)

    def _generate_code(self):
        from datetime import datetime
        prefix = f"FT-{timezone.now().year}"
        count = Ticket.objects.filter(code__startswith=prefix).count() + 1
        return f"{prefix}-{count:06d}"

    def _generate_tracking_token(self):
        import secrets
        return secrets.token_urlsafe(16)[:32]


class TicketStatusHistory(models.Model):
    """
    Registro inmutable de cada cambio de estado de un ticket.
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('Ticket')
    )
    previous_status = models.CharField(
        max_length=20,
        verbose_name=_('Estado anterior')
    )
    new_status = models.CharField(
        max_length=20,
        verbose_name=_('Estado nuevo')
    )
    reason = models.TextField(
        blank=True,
        verbose_name=_('Motivo')
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ticket_status_changes',
        verbose_name=_('Cambiado por')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Histórico de estado')
        verbose_name_plural = _('Histórico de estados')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket.code}: {self.previous_status} → {self.new_status}"


class TicketComment(models.Model):
    """
    Nota o comunicación asociada a un ticket.
    """
    class Visibility(models.TextChoices):
        INTERNAL = 'internal', _('Interna')
        CLIENT = 'client', _('Visible para cliente')

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Ticket')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ticket_comments',
        verbose_name=_('Autor')
    )
    text = models.TextField(verbose_name=_('Contenido'))
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.INTERNAL,
        verbose_name=_('Visibilidad')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Comentario')
        verbose_name_plural = _('Comentarios')
        ordering = ['-created_at']

    def __str__(self):
        return f"Comentario en {self.ticket.code} por {self.author}"


class TicketAttachment(models.Model):
    """
    Evidencia fotográfica o documental adjunta a un ticket.
    Fase 1: almacenamiento local; en producción se migraría a S3/MinIO.
    """
    class AttachmentType(models.TextChoices):
        PHOTO_BEFORE = 'photo_before', _('Foto estado previo')
        PHOTO_DURING = 'photo_during', _('Foto durante trabajo')
        PHOTO_AFTER = 'photo_after', _('Foto resultado')
        METER_READING = 'meter_reading', _('Lectura de medidor')
        DOCUMENT = 'document', _('Documento')

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Ticket')
    )
    attachment_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        default=AttachmentType.PHOTO_BEFORE,
        verbose_name=_('Tipo de adjunto')
    )
    file = models.ImageField(
        upload_to='ticket_attachments/%Y/%m/%d/',
        verbose_name=_('Archivo')
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Descripción')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ticket_attachments',
        verbose_name=_('Subido por')
    )
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('Latitud'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('Longitud'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Adjunto')
        verbose_name_plural = _('Adjuntos')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.attachment_type} - {self.ticket.code}"


class DiagnosisLog(models.Model):
    """
    Registro histórico de diagnósticos automáticos FTTH.
    Permite trazabilidad de averías, soluciones aplicadas y restauración de clientes.
    """
    box = models.ForeignKey(
        'network.FiberBox',
        on_delete=models.CASCADE,
        related_name='diagnosis_logs',
        verbose_name=_('Caja afectada')
    )
    splitter = models.ForeignKey(
        'network.Splitter',
        on_delete=models.CASCADE,
        related_name='diagnosis_logs',
        null=True, blank=True,
        verbose_name=_('Splitter afectado')
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diagnosis_logs',
        verbose_name=_('Ticket operativo')
    )
    severity = models.CharField(max_length=20, verbose_name=_('Severidad'))
    confidence = models.PositiveSmallIntegerField(default=0, verbose_name=_('Confianza %'))
    power_analysis = models.JSONField(default=dict, verbose_name=_('Análisis de potencia'))
    affected_clients = models.JSONField(default=list, verbose_name=_('Clientes afectados'))
    possible_solutions = models.JSONField(default=list, verbose_name=_('Posibles soluciones'))
    recommended_action = models.TextField(blank=True, verbose_name=_('Acción recomendada'))
    affected_route = models.JSONField(default=list, verbose_name=_('Ruta afectada'))
    solution_applied = models.TextField(blank=True, verbose_name=_('Solución aplicada'))
    resolved = models.BooleanField(default=False, verbose_name=_('Resuelto'))
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Fecha de resolución'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diagnosis_logs',
        verbose_name=_('Creado por')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Registro de diagnóstico')
        verbose_name_plural = _('Registros de diagnóstico')
        ordering = ['-created_at']

    def __str__(self):
        return f"Diagnóstico {self.box.code} - {self.severity} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
