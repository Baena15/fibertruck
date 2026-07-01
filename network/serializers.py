"""
FiberTruck API Serializers
"""
from rest_framework import serializers
from .models import (
    OLT, Zone, Splitter, FiberBox, Client, FiberIncident,
    FiberCable, SpliceClosure, CableSegment, FiberAssignment,
)


class OLTSerializer(serializers.ModelSerializer):
    class Meta:
        model = OLT
        fields = '__all__'


class ZoneSerializer(serializers.ModelSerializer):
    client_count = serializers.ReadOnlyField()
    affected_client_count = serializers.ReadOnlyField()
    class Meta:
        model = Zone
        fields = '__all__'


class SplitterSerializer(serializers.ModelSerializer):
    total_ports = serializers.ReadOnlyField()
    occupied_ports = serializers.ReadOnlyField()
    free_ports = serializers.ReadOnlyField()
    olt_name = serializers.CharField(source='olt.name', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    class Meta:
        model = Splitter
        fields = '__all__'


class FiberBoxSerializer(serializers.ModelSerializer):
    client_count = serializers.ReadOnlyField()
    affected_count = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    splitter_name = serializers.CharField(source='splitter.name', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    class Meta:
        model = FiberBox
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    full_path = serializers.ReadOnlyField()
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    box_code = serializers.CharField(source='box.code', read_only=True)
    class Meta:
        model = Client
        fields = '__all__'


class ClientListSerializer(serializers.ModelSerializer):
    box_code = serializers.CharField(source='box.code', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    class Meta:
        model = Client
        fields = ['id', 'client_code', 'full_name', 'address', 'status', 'optical_power_rx', 'box_code', 'zone_name']


class FiberIncidentSerializer(serializers.ModelSerializer):
    affected_client_count = serializers.ReadOnlyField()
    olt_code = serializers.CharField(source='olt.code', read_only=True, default=None)
    splitter_code = serializers.CharField(source='splitter.code', read_only=True, default=None)
    box_code = serializers.CharField(source='box.code', read_only=True, default=None)
    class Meta:
        model = FiberIncident
        fields = '__all__'


# ============================================================
# NUEVOS SERIALIZERS FTTH - Ingenieria de Red
# ============================================================

class FiberCableSerializer(serializers.ModelSerializer):
    """
    Serializer para cables de fibra optica.
    Incluye conteo de tramos y estadisticas de uso.
    """
    segments_count = serializers.SerializerMethodField()
    fibers_used = serializers.ReadOnlyField()
    fibers_free = serializers.ReadOnlyField()
    utilization_percent = serializers.ReadOnlyField()

    class Meta:
        model = FiberCable
        fields = '__all__'

    def get_segments_count(self, obj):
        return obj.segments.count()


class SpliceClosureSerializer(serializers.ModelSerializer):
    """
    Serializer para cajas de empalme.
    Incluye datos de zona y cables relacionados.
    """
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    input_cable_code = serializers.CharField(source='input_cable.code', read_only=True, default=None)
    output_cable_code = serializers.CharField(source='output_cable.code', read_only=True, default=None)
    fibers_free = serializers.ReadOnlyField()
    splitter_count = serializers.SerializerMethodField()

    class Meta:
        model = SpliceClosure
        fields = '__all__'

    def get_splitter_count(self, obj):
        return obj.splitters.count()


class CableSegmentSerializer(serializers.ModelSerializer):
    """
    Serializer para tramos de cable.
    Incluye coordenadas de ruta como lista y elementos de origen/destino.
    """
    route_as_list = serializers.ReadOnlyField()
    origin_element = serializers.SerializerMethodField()
    destination_element = serializers.SerializerMethodField()
    cable_code = serializers.CharField(source='cable.code', read_only=True)
    cable_type = serializers.CharField(source='cable.cable_type', read_only=True)
    fiber_numbers_list = serializers.ReadOnlyField()

    class Meta:
        model = CableSegment
        fields = '__all__'

    def get_origin_element(self, obj):
        elem = obj.origin_element
        if elem:
            return {
                'id': elem.id,
                'type': elem.__class__.__name__.lower(),
                'code': getattr(elem, 'code', str(elem)),
                'name': getattr(elem, 'name', str(elem)),
            }
        return None

    def get_destination_element(self, obj):
        elem = obj.destination_element
        if elem:
            return {
                'id': elem.id,
                'type': elem.__class__.__name__.lower(),
                'code': getattr(elem, 'code', str(elem)),
                'name': getattr(elem, 'name', str(elem)),
            }
        return None


class FiberAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer para asignaciones de fibra.
    Incluye datos del cable y del elemento destino.
    """
    cable_code = serializers.CharField(source='cable.code', read_only=True)
    cable_type = serializers.CharField(source='cable.cable_type', read_only=True)
    target_type = serializers.ReadOnlyField()
    target_element = serializers.SerializerMethodField()
    zone_name = serializers.SerializerMethodField()

    class Meta:
        model = FiberAssignment
        fields = '__all__'

    def get_target_element(self, obj):
        elem = obj.target_element
        if elem:
            return {
                'id': elem.id,
                'type': obj.target_type,
                'code': getattr(elem, 'code', str(elem)),
                'name': getattr(elem, 'name', str(elem)),
            }
        return None

    def get_zone_name(self, obj):
        elem = obj.target_element
        if elem:
            zone = getattr(elem, 'zone', None)
            if zone:
                return zone.name
        return None
