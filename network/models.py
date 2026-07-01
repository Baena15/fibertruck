"""
FiberTruck Network Models
Modelo de datos jerarquico para redes FTTH profesional

Topologia: OLT -> FiberCable (feeder) -> SpliceClosure -> FiberCable (distribution) 
          -> Splitter -> FiberCable (drop) -> FiberBox -> Cliente

Modelos:
    OLT              - Optical Line Terminal (cabecera)
    Zone             - Zona de despliegue (barrio)
    FiberCable       - Cable de fibra optica (feeder/distribution/drop)
    SpliceClosure    - Caja de empalme fisica de fibra
    Splitter         - Splitter optico (1xN)
    FiberBox         - Caja de reparto FTTH (CTO)
    Client           - Cliente final conectado
    FiberAssignment  - Asignacion de fibra N de un cable a caja/cliente
    CableSegment     - Tramo de cable entre dos elementos de red
    FiberIncident    - Incidencia de fallo en la red
"""
from django.db import models
import json


# ============================================================
# OLT - Optical Line Terminal
# ============================================================
class OLT(models.Model):
    """Optical Line Terminal - Cabecera de la red FTTH"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Ej: OLT-CIEZA-01")
    address = models.CharField(max_length=200, verbose_name="Direccion")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    max_ports = models.PositiveIntegerField(default=16, verbose_name="Puertos PON maximos")
    output_power_dbm = models.FloatField(default=3.0, verbose_name="Potencia de salida (dBm)",
                                         help_text="Potencia de salida del OLT en dBm (tipico: +3 dBm)")
    splitter_ratio = models.CharField(max_length=10, default='1x32', verbose_name="Ratio splitter",
                                      choices=[('1x32', '1x32'), ('1x64', '1x64')],
                                      help_text="Ratio de splitter que soporta el OLT")
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


# ============================================================
# Zone - Zona de despliegue
# ============================================================
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


# ============================================================
# FiberCable - Cable de fibra optica
# ============================================================
class FiberCable(models.Model):
    """Cable de fibra optica con capacidad y tipo definidos"""
    CABLE_TYPES = [
        ('feeder', 'Feeder (Central -> Zona)'),
        ('distribution', 'Distribution (Splitter -> Caja)'),
        ('drop', 'Drop (Caja -> Cliente)'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Ej: CBL-FDR-01, CBL-DST-ERA-01")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    cable_type = models.CharField(max_length=20, choices=CABLE_TYPES, verbose_name="Tipo de cable")
    fiber_count = models.PositiveIntegerField(verbose_name="Numero de fibras",
                                              help_text="12, 72, 144, etc.")
    length_m = models.FloatField(verbose_name="Longitud (m)",
                                 help_text="Longitud del cable en metros")
    description = models.TextField(blank=True, verbose_name="Descripcion")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cable de Fibra"
        verbose_name_plural = "Cables de Fibra"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.cable_type}, {self.fiber_count}f) - {self.name}"

    @property
    def fibers_used(self):
        """Numero de fibras del cable ya asignadas"""
        return self.fiber_assignments.count()

    @property
    def fibers_free(self):
        """Numero de fibras libres del cable"""
        return self.fiber_count - self.fibers_used

    @property
    def utilization_percent(self):
        """Porcentaje de utilizacion del cable"""
        if self.fiber_count == 0:
            return 0.0
        return (self.fibers_used / self.fiber_count) * 100.0


# ============================================================
# SpliceClosure - Caja de empalme
# ============================================================
class SpliceClosure(models.Model):
    """Caja de empalme fisico de fibra optica"""
    SPLICE_TYPES = [
        ('inline', 'Inline'),
        ('dome', 'Dome / Encapsulado'),
        ('rack', 'Rack'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Ej: SPC-ERA-01")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    closure_type = models.CharField(max_length=20, choices=SPLICE_TYPES,
                                    verbose_name="Tipo de cierre")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    address = models.CharField(max_length=200, verbose_name="Direccion")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,
                             related_name='splices', verbose_name="Zona")
    input_cable = models.ForeignKey(FiberCable, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='input_splices',
                                    verbose_name="Cable de entrada",
                                    help_text="Cable que entra al empalme")
    output_cable = models.ForeignKey(FiberCable, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='output_splices',
                                     verbose_name="Cable de salida",
                                     help_text="Cable que sale del empalme")
    fiber_capacity = models.PositiveIntegerField(default=144,
                                                  verbose_name="Capacidad de fibras")
    fiber_count_used = models.PositiveIntegerField(default=0,
                                                    verbose_name="Fibras usadas")
    notes = models.TextField(blank=True, verbose_name="Notas")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Caja de Empalme"
        verbose_name_plural = "Cajas de Empalme"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} ({self.closure_type}) - {self.zone.name}"

    @property
    def fibers_free(self):
        """Fibras libres en el empalme"""
        return self.fiber_capacity - self.fiber_count_used


# ============================================================
# Splitter - Splitter optico
# ============================================================
class Splitter(models.Model):
    """Splitter de fibra optica (1xN)"""
    SPLITTER_RATIOS = [
        ('1x2', '1x2'), ('1x4', '1x4'), ('1x8', '1x8'),
        ('1x16', '1x16'), ('1x32', '1x32'), ('1x64', '1x64'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Ej: SPL-001")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    ratio = models.CharField(max_length=10, choices=SPLITTER_RATIOS,
                             default='1x32', verbose_name="Ratio")
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE,
                            related_name='splitters', verbose_name="OLT padre")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,
                             related_name='splitters', verbose_name="Zona")
    input_port_olt = models.PositiveIntegerField(default=0,
                                                  verbose_name="Puerto PON OLT")
    input_fiber_number = models.PositiveIntegerField(null=True, blank=True,
                                                      verbose_name="Fibra de entrada",
                                                      help_text="Numero de fibra del cable feeder que entra al splitter")
    input_cable = models.ForeignKey(FiberCable, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='splitter_inputs',
                                    verbose_name="Cable feeder de entrada",
                                    help_text="Cable feeder que alimenta este splitter")
    output_power_dbm = models.FloatField(null=True, blank=True,
                                          verbose_name="Potencia de salida (dBm)",
                                          help_text="Potencia de salida por puerto en dBm")
    splice_in = models.ForeignKey(SpliceClosure, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='splitters',
                                  verbose_name="Empalme de entrada",
                                  help_text="Empalme donde se conecta el splitter")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    address = models.CharField(max_length=200, blank=True,
                               verbose_name="Direccion/Ubicacion")
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

    @property
    def insertion_loss_db(self):
        """Perdida de insercion teorica del splitter en dB"""
        try:
            n = int(self.ratio.split('x')[1])
            return round(3.0 + 10 * __import__('math').log10(n), 2)
        except (IndexError, ValueError, Exception):
            return 17.0  # Default para 1x32


# ============================================================
# FiberBox - Caja de reparto FTTH (CTO)
# ============================================================
class FiberBox(models.Model):
    """Caja de reparto FTTH (CTO - Caja de Terminacion Optica)"""
    BOX_TYPES = [
        ('CTO', 'Caja de Terminacion Optica (CTO)'),
        ('CTO-MINI', 'CTO Mini'),
        ('FAT', 'Fiber Access Terminal'),
        ('FDT', 'Fiber Distribution Terminal'),
    ]
    STATUS_CHOICES = [
        ('active', 'Activa - OK'),
        ('warning', 'Advertencia'),
        ('fault', 'Con averia'),
        ('maintenance', 'En mantenimiento'),
        ('inactive', 'Inactiva'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Codigo",
                            help_text="Numero de caja que introduce el tecnico. Ej: CTO-001")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    box_type = models.CharField(max_length=20, choices=BOX_TYPES,
                                default='CTO', verbose_name="Tipo")
    splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE,
                                 related_name='boxes', verbose_name="Splitter padre")
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE,
                             related_name='boxes', verbose_name="Zona")
    splitter_port = models.PositiveIntegerField(default=0,
                                                 verbose_name="Puerto del splitter")
    max_capacity = models.PositiveIntegerField(default=16,
                                                verbose_name="Capacidad maxima")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    address = models.CharField(max_length=200, blank=True, verbose_name="Direccion")
    input_cable = models.ForeignKey(FiberCable, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='box_inputs',
                                    verbose_name="Cable de entrada",
                                    help_text="Cable distribution que alimenta esta caja")
    input_fiber_number = models.PositiveIntegerField(null=True, blank=True,
                                                      verbose_name="Fibra de entrada",
                                                      help_text="Numero de fibra del cable que alimenta esta caja")
    measured_power_dbm = models.FloatField(null=True, blank=True,
                                            verbose_name="Potencia medida (dBm)",
                                            help_text="Potencia optica medida en la caja en dBm")
    expected_power_dbm = models.FloatField(null=True, blank=True,
                                            verbose_name="Potencia esperada (dBm)",
                                            help_text="Potencia esperada calculada en la caja en dBm")
    splice_in = models.ForeignKey(SpliceClosure, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='boxes',
                                  verbose_name="Empalme de entrada",
                                  help_text="Empalme por el que llega el cable a esta caja")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='active', verbose_name="Estado")
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

    @property
    def power_deviation_db(self):
        """Desviacion entre potencia medida y esperada en dB"""
        if self.measured_power_dbm is not None and self.expected_power_dbm is not None:
            return round(self.measured_power_dbm - self.expected_power_dbm, 2)
        return None


# ============================================================
# Client - Cliente final
# ============================================================
class Client(models.Model):
    """Cliente final conectado a la red FTTH"""
    STATUS_CHOICES = [
        ('active', 'Activo - Servicio OK'),
        ('affected', 'Afectado - Sin servicio'),
        ('degraded', 'Degradado'),
        ('installing', 'En instalacion'),
        ('disconnected', 'Desconectado'),
    ]

    client_code = models.CharField(max_length=20, unique=True,
                                   verbose_name="Codigo cliente",
                                   help_text="Ej: CLI-0001")
    full_name = models.CharField(max_length=200, verbose_name="Nombre completo")
    address = models.CharField(max_length=300, verbose_name="Direccion de instalacion")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    box = models.ForeignKey(FiberBox, on_delete=models.CASCADE,
                            related_name='clients', verbose_name="Caja asignada")
    box_port = models.PositiveIntegerField(default=0, verbose_name="Puerto de la caja")
    olt_port = models.PositiveIntegerField(default=0, verbose_name="Puerto PON OLT")
    drop_fiber_number = models.PositiveIntegerField(null=True, blank=True,
                                                     verbose_name="Fibra drop",
                                                     help_text="Numero de fibra drop asignada al cliente")
    expected_power_dbm = models.FloatField(null=True, blank=True,
                                            verbose_name="Potencia esperada (dBm)",
                                            help_text="Potencia optica esperada calculada en la ONT del cliente")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='active', verbose_name="Estado")
    optical_power_rx = models.FloatField(null=True, blank=True,
                                          verbose_name="Potencia RX (dBm)")
    optical_power_tx = models.FloatField(null=True, blank=True,
                                          verbose_name="Potencia TX (dBm)")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    installation_date = models.DateField(null=True, blank=True,
                                          verbose_name="Fecha instalacion")
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
        return (f"{self.olt.code} > {self.splitter.code} > "
                f"{self.box.code} > {self.client_code}")

    @property
    def power_margin_db(self):
        """Margen de potencia: diferencia entre RX medida y RX esperada"""
        if self.optical_power_rx is not None and self.expected_power_dbm is not None:
            return round(self.optical_power_rx - self.expected_power_dbm, 2)
        return None


# ============================================================
# FiberAssignment - Asignacion de fibra a elemento
# ============================================================
class FiberAssignment(models.Model):
    """
    Registra que fibra (numero N) de que cable alimenta a que elemento
    de red (splitter, caja o cliente).
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('fault', 'Con fallo'),
        ('reserved', 'Reservada'),
    ]

    fiber_number = models.PositiveIntegerField(verbose_name="Numero de fibra",
                                                help_text="Numero de fibra en el cable (1-N)")
    cable = models.ForeignKey(FiberCable, on_delete=models.CASCADE,
                              related_name='fiber_assignments',
                              verbose_name="Cable")

    # A quien alimenta (una u otra, nunca multiples)
    splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE,
                                 null=True, blank=True,
                                 related_name='fiber_assignments',
                                 verbose_name="Splitter alimentado")
    box = models.ForeignKey(FiberBox, on_delete=models.CASCADE,
                            null=True, blank=True,
                            related_name='fiber_assignments',
                            verbose_name="Caja alimentada")
    client = models.ForeignKey(Client, on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='fiber_assignments',
                               verbose_name="Cliente alimentado")

    # Desde donde viene esta fibra
    from_splice = models.ForeignKey(SpliceClosure, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='output_fibers',
                                    verbose_name="Empalme de origen")
    from_splitter_port = models.PositiveIntegerField(null=True, blank=True,
                                                      verbose_name="Puerto splitter origen")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='active', verbose_name="Estado")
    notes = models.CharField(max_length=200, blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Asignacion de Fibra"
        verbose_name_plural = "Asignaciones de Fibra"
        ordering = ['cable', 'fiber_number']
        unique_together = [['cable', 'fiber_number']]

    def __str__(self):
        target = self.splitter or self.box or self.client
        target_str = str(target) if target else "Sin destino"
        return f"Fibra {self.fiber_number} de {self.cable.code} -> {target_str}"

    @property
    def target_element(self):
        """Retorna el elemento destino de esta asignacion"""
        return self.splitter or self.box or self.client

    @property
    def target_type(self):
        """Retorna el tipo de elemento destino"""
        if self.splitter:
            return 'splitter'
        if self.box:
            return 'box'
        if self.client:
            return 'client'
        return 'unknown'


# ============================================================
# CableSegment - Tramo de cable entre dos elementos
# ============================================================
class CableSegment(models.Model):
    """
    Un tramo de cable une dos elementos de la red.
    Representa un segmento fisico de un cable entre dos puntos.
    """
    SEGMENT_TYPES = [
        ('olt_to_splice', 'OLT -> Empalme'),
        ('splice_to_splitter', 'Empalme -> Splitter'),
        ('splitter_to_box', 'Splitter -> Caja'),
        ('splice_to_box', 'Empalme -> Caja'),
        ('box_to_client', 'Caja -> Cliente'),
    ]

    cable = models.ForeignKey(FiberCable, on_delete=models.CASCADE,
                              related_name='segments',
                              verbose_name="Cable")
    segment_type = models.CharField(max_length=30, choices=SEGMENT_TYPES,
                                    verbose_name="Tipo de tramo")

    # Elemento de origen (solo uno debe estar poblado)
    from_olt = models.ForeignKey(OLT, on_delete=models.CASCADE,
                                 null=True, blank=True,
                                 related_name='outgoing_segments',
                                 verbose_name="Desde OLT")
    from_splice = models.ForeignKey(SpliceClosure, on_delete=models.CASCADE,
                                    null=True, blank=True,
                                    related_name='outgoing_segments',
                                    verbose_name="Desde Empalme")
    from_splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE,
                                      null=True, blank=True,
                                      related_name='outgoing_segments',
                                      verbose_name="Desde Splitter")
    from_box = models.ForeignKey(FiberBox, on_delete=models.CASCADE,
                                 null=True, blank=True,
                                 related_name='outgoing_segments',
                                 verbose_name="Desde Caja")

    # Elemento de destino (solo uno debe estar poblado)
    to_splice = models.ForeignKey(SpliceClosure, on_delete=models.CASCADE,
                                  null=True, blank=True,
                                  related_name='incoming_segments',
                                  verbose_name="Hacia Empalme")
    to_splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE,
                                    null=True, blank=True,
                                    related_name='incoming_segments',
                                    verbose_name="Hacia Splitter")
    to_box = models.ForeignKey(FiberBox, on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='incoming_segments',
                               verbose_name="Hacia Caja")
    to_client = models.ForeignKey(Client, on_delete=models.CASCADE,
                                  null=True, blank=True,
                                  related_name='incoming_segments',
                                  verbose_name="Hacia Cliente")

    # Fibra especifica del cable que usa este tramo
    fiber_numbers = models.CharField(max_length=100, blank=True,
                                     verbose_name="Fibras utilizadas",
                                     help_text="Numeros de fibra separados por coma. Ej: 1,2,3")
    length_m = models.FloatField(verbose_name="Longitud real (m)",
                                 help_text="Longitud real de este tramo en metros")
    route_coordinates = models.TextField(blank=True,
                                          verbose_name="Coordenadas de ruta",
                                          help_text="JSON array de [lat,lng] con la trayectoria por calles")
    attenuation_db = models.FloatField(default=0.0,
                                        verbose_name="Atenuacion (dB)",
                                        help_text="Perdida de este tramo en dB")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tramo de Cable"
        verbose_name_plural = "Tramos de Cable"
        ordering = ['cable', 'segment_type']

    def __str__(self):
        origin = self.origin_element or "?"
        dest = self.destination_element or "?"
        return f"{self.cable.code}: {origin} -> {dest} ({self.length_m}m)"

    @property
    def route_as_list(self):
        """Coordenadas de ruta como lista Python"""
        try:
            coords = json.loads(self.route_coordinates)
            if isinstance(coords, list):
                return coords
            return []
        except (json.JSONDecodeError, TypeError, ValueError):
            return []

    @property
    def origin_element(self):
        """Elemento de origen del tramo"""
        return self.from_olt or self.from_splice or self.from_splitter or self.from_box

    @property
    def destination_element(self):
        """Elemento de destino del tramo"""
        return self.to_splice or self.to_splitter or self.to_box or self.to_client

    @property
    def fiber_numbers_list(self):
        """Lista de numeros de fibra como enteros"""
        if not self.fiber_numbers:
            return []
        try:
            return [int(x.strip()) for x in self.fiber_numbers.split(',') if x.strip()]
        except ValueError:
            return []


# ============================================================
# FiberIncident - Incidencia en la red
# ============================================================
class FiberIncident(models.Model):
    """Incidencia de fallo en la red FTTH con diagnostico avanzado"""
    SEVERITY_CHOICES = [
        ('critical', 'Critica'),
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ]
    STATUS_CHOICES = [
        ('open', 'Abierta'),
        ('diagnosing', 'En diagnostico'),
        ('assigned', 'Asignada'),
        ('in_progress', 'En reparacion'),
        ('resolved', 'Resuelta'),
        ('closed', 'Cerrada'),
    ]
    INCIDENT_TYPES = [
        ('fiber_break', 'Rotura de fibra'),
        ('splitter_fault', 'Fallo en splitter'),
        ('connector_fault', 'Fallo en conector'),
        ('olt_fault', 'Fallo en OLT'),
        ('power_issue', 'Problema de potencia optica'),
        ('unknown', 'Desconocido'),
    ]

    code = models.CharField(max_length=20, unique=True,
                            verbose_name="Codigo",
                            help_text="Ej: INC-20250701-001")
    title = models.CharField(max_length=200, verbose_name="Titulo")
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES,
                                     default='unknown', verbose_name="Tipo")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES,
                                default='medium', verbose_name="Severidad")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='open', verbose_name="Estado")

    # Elementos afectados
    olt = models.ForeignKey(OLT, on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='incidents')
    splitter = models.ForeignKey(Splitter, on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='incidents')
    box = models.ForeignKey(FiberBox, on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='incidents')
    affected_clients = models.ManyToManyField(Client, blank=True,
                                               related_name='incidents')

    # Diagnostico
    diagnosis_result = models.TextField(blank=True,
                                        verbose_name="Resultado del diagnostico")
    diagnosis_confidence = models.FloatField(default=0.0,
                                              verbose_name="Confianza del diagnostico (%)")
    root_cause_node = models.CharField(max_length=50, blank=True,
                                        verbose_name="Nodo causa raiz")

    # Campos para diagnostico avanzado con topologia
    affected_segment = models.ForeignKey(CableSegment, on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='incidents',
                                          verbose_name="Tramo afectado",
                                          help_text="Tramo de cable afectado por la incidencia")
    affected_fibers = models.CharField(max_length=100, blank=True,
                                        verbose_name="Fibras afectadas",
                                        help_text="Fibras afectadas del cable, separadas por coma")
    splice_fault = models.ForeignKey(SpliceClosure, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='incidents',
                                     verbose_name="Empalme fallido",
                                     help_text="Empalme donde se detecto el fallo")
    affected_route = models.TextField(blank=True,
                                       verbose_name="Ruta afectada",
                                       help_text="JSON con coordenadas del tramo afectado para pintar en mapa")
    recommended_action = models.TextField(blank=True,
                                          verbose_name="Accion recomendada",
                                          help_text="Accion recomendada con detalle para el tecnico")

    # Administracion
    description = models.TextField(blank=True, verbose_name="Descripcion")
    reported_by = models.CharField(max_length=100, blank=True,
                                    verbose_name="Reportado por")
    assigned_to = models.CharField(max_length=100, blank=True,
                                    verbose_name="Tecnico asignado")
    resolved_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name="Fecha resolucion")
    resolution_notes = models.TextField(blank=True,
                                         verbose_name="Notas de resolucion")
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

    @property
    def affected_route_as_list(self):
        """Ruta afectada como lista de coordenadas"""
        try:
            route = json.loads(self.affected_route)
            if isinstance(route, list):
                return route
            return []
        except (json.JSONDecodeError, TypeError, ValueError):
            return []

    @property
    def is_open(self):
        return self.status in ('open', 'diagnosing', 'assigned', 'in_progress')

    @property
    def duration_hours(self):
        """Duracion de la incidencia en horas"""
        from django.utils import timezone
        end = self.resolved_at or timezone.now()
        delta = end - self.created_at
        return round(delta.total_seconds() / 3600, 2)
