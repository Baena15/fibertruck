"""
FiberTruck Network Models
Modelo de datos jerarquico para redes FTTH
Topologia: OLT -> Splitter -> Caja(CTO) -> Cliente
"""
from django.db import models


class OLT(models.Model):
    """Optical Line Terminal - Cabecera de la red"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Ej: OLT-CIEZA-01")
    address = models.CharField(max_length=200, verbose_name="Direccion")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    max_ports = models.PositiveIntegerField(default=16, verbose_name="Puertos PON maximos")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "OLT"
        verbose_name_plural = "OLTs"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Zone(models.Model):
    """Zona de despliegue (barrio de Cieza)"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                           help_text="Ej: Z-SJOA")
    description = models.TextField(blank=True, verbose_name="Descripcion")
    latitude = models.FloatField(verbose_name="Latitud centro")
    longitude = models.FloatField(verbose_name="Longitud centro")
    population_estimate = models.PositiveIntegerField(default=0, verbose_name="Poblacion estimada")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def client_count(self):
        return Client.objects.filter(box__zone=self, is_active=True).count()

    @property
    def affected_client_count(self):
        return Client.objects.filter(box__zone=self, status='affected').count()


class Splitter(models.Model):
    """Splitter de fibra optica"""
    SPLITTER_RATIOS = [
        ('1x2', '1x2'), ('1x4', '1x4'), ('1x8', '1x8'), ('1x16', '1x16'), ('1x32', '1x32'), ('1x64', '1x64'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo", help_text="Ej: SPL-001")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    ratio = models.CharField(max_length=10, choices=SPLITTER_RATIOS, default='1x32', verbose_name="Ratio")
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='splitters', verbose_name="OLT padre")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='splitters', verbose_name="Zona")
    input_port_olt = models.PositiveIntegerField(default=0, verbose_name="Puerto PON OLT")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    address = models.CharField(max_length=200, blank=True, verbose_name="Direccion/Ubicacion")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Splitter"
        verbose_name_plural = "Splitters"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.ratio}) - {self.zone.name}"

    @property
    def total_ports(self):
        try:
            return int(self.ratio.split('x')[1])
        except (IndexError, ValueError):
            return 32

    @property
    def occupied_ports(self):
        return self.boxes.count()

    @property
    def free_ports(self):
        return self.total_ports - self.occupied_ports


class FiberBox(models.Model):
    """Caja de reparto FTTH (CTO)"""
    BOX_TYPES = [
        ('CTO', 'Caja de Terminacion Optica (CTO)'),
        ('CTO-MINI', 'CTO Mini'), ('FAT', 'Fiber Access Terminal'), ('FDT', 'Fiber Distribution Terminal'),
    ]
    STATUS_CHOICES = [
        ('active', 'Activa - OK'), ('warning', 'Advertencia'), ('fault', 'Con averia'),
        ('maintenance', 'En mantenimiento'), ('inactive', 'Inactiva'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                           help_text="Numero de caja que introduce el tecnico. Ej: CTO-001")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    box_type = models.CharField(max_length=20, choices=BOX_TYPES, default='CTO', verbose_name="Tipo")
    splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE, related_name='boxes', verbose_name="Splitter padre")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='boxes', verbose_name="Zona")
    splitter_port = models.PositiveIntegerField(default=0, verbose_name="Puerto del splitter")
    max_capacity = models.PositiveIntegerField(default=16, verbose_name="Capacidad maxima")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    address = models.CharField(max_length=200, blank=True, verbose_name="Direccion")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    notes = models.TextField(blank=True, verbose_name="Notas tecnicas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Caja de Fibra"
        verbose_name_plural = "Cajas de Fibra"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def client_count(self):
        return self.clients.filter(is_active=True).count()

    @property
    def affected_count(self):
        return self.clients.filter(status='affected').count()

    @property
    def full_path(self):
        return f"{self.splitter.olt.code} > {self.splitter.code} > {self.code}"


class Client(models.Model):
    """Cliente final conectado a la red FTTH"""
    STATUS_CHOICES = [
        ('active', 'Activo - Servicio OK'), ('affected', 'Afectado - Sin servicio'),
        ('degraded', 'Degradado'), ('installing', 'En instalacion'), ('disconnected', 'Desconectado'),
    ]

    client_code = models.CharField(max_length=20, unique=True, verbose_name="Codigo cliente", help_text="Ej: CLI-0001")
    full_name = models.CharField(max_length=200, verbose_name="Nombre completo")
    address = models.CharField(max_length=300, verbose_name="Direccion de instalacion")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    box = models.ForeignKey(FiberBox, on_delete=models.CASCADE, related_name='clients', verbose_name="Caja asignada")
    box_port = models.PositiveIntegerField(default=0, verbose_name="Puerto de la caja")
    olt_port = models.PositiveIntegerField(default=0, verbose_name="Puerto PON OLT")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Estado")
    optical_power_rx = models.FloatField(null=True, blank=True, verbose_name="Potencia RX (dBm)")
    optical_power_tx = models.FloatField(null=True, blank=True, verbose_name="Potencia TX (dBm)")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    installation_date = models.DateField(null=True, blank=True, verbose_name="Fecha instalacion")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['client_code']

    def __str__(self):
        return f"{self.client_code} - {self.full_name}"

    @property
    def zone(self):
        return self.box.zone

    @property
    def splitter(self):
        return self.box.splitter

    @property
    def olt(self):
        return self.splitter.olt

    @property
    def full_path(self):
        return f"{self.olt.code} > {self.splitter.code} > {self.box.code} > {self.client_code}"


class FiberIncident(models.Model):
    """Incidencia de fallo en la red"""
    SEVERITY_CHOICES = [
        ('critical', 'Critica'), ('high', 'Alta'), ('medium', 'Media'), ('low', 'Baja'),
    ]
    STATUS_CHOICES = [
        ('open', 'Abierta'), ('diagnosing', 'En diagnostico'), ('assigned', 'Asignada'),
        ('in_progress', 'En reparacion'), ('resolved', 'Resuelta'), ('closed', 'Cerrada'),
    ]
    INCIDENT_TYPES = [
        ('fiber_break', 'Rotura de fibra'), ('splitter_fault', 'Fallo en splitter'),
        ('connector_fault', 'Fallo en conector'), ('olt_fault', 'Fallo en OLT'),
        ('power_issue', 'Problema de potencia optica'), ('unknown', 'Desconocido'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo", help_text="Ej: INC-20250701-001")
    title = models.CharField(max_length=200, verbose_name="Titulo")
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES, default='unknown', verbose_name="Tipo")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium', verbose_name="Severidad")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Estado")
    olt = models.ForeignKey(OLT, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    splitter = models.ForeignKey(Splitter, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    box = models.ForeignKey(FiberBox, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    affected_clients = models.ManyToManyField(Client, blank=True, related_name='incidents')
    diagnosis_result = models.TextField(blank=True, verbose_name="Resultado del diagnostico")
    diagnosis_confidence = models.FloatField(default=0.0, verbose_name="Confianza del diagnostico (%)")
    root_cause_node = models.CharField(max_length=50, blank=True, verbose_name="Nodo causa raiz")
    description = models.TextField(blank=True, verbose_name="Descripcion")
    reported_by = models.CharField(max_length=100, blank=True, verbose_name="Reportado por")
    assigned_to = models.CharField(max_length=100, blank=True, verbose_name="Tecnico asignado")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha resolucion")
    resolution_notes = models.TextField(blank=True, verbose_name="Notas de resolucion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.title}"

    @property
    def affected_client_count(self):
        return self.affected_clients.count()
