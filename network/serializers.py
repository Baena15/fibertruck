"""
FiberTruck API Serializers
Serializadores completos para el modelo FTTH de ingenieria de red.
"""
from rest_framework import serializers
from .models import OLT, Zone, Splitter, FiberBox, Client, FiberIncident
from .models import FiberCable, SpliceClosure, CableSegment, FiberAssignment


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


class FiberCableSerializer(serializers.ModelSerializer):
    fibers_used = serializers.ReadOnlyField()
    fibers_free = serializers.ReadOnlyField()
    utilization_percent = serializers.ReadOnlyField()
    class Meta:
        model = FiberCable
        fields = '__all__'


class SpliceClosureSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    fibers_free = serializers.ReadOnlyField()
    input_cable_code = serializers.CharField(source='input_cable.code', read_only=True, default=None)
    output_cable_code = serializers.CharField(source='output_cable.code', read_only=True, default=None)
    class Meta:
        model = SpliceClosure
        fields = '__all__'


class SplitterSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    total_ports = serializers.ReadOnlyField()
    occupied_ports = serializers.ReadOnlyField()
    free_ports = serializers.ReadOnlyField()
    insertion_loss_db = serializers.ReadOnlyField()
    input_cable_code = serializers.CharField(source='input_cable.code', read_only=True, default=None)
    splice_code = serializers.CharField(source='splice_in.code', read_only=True, default=None)
    class Meta:
        model = Splitter
        fields = '__all__'


class FiberBoxSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    splitter_code = serializers.CharField(source='splitter.code', read_only=True)
    client_count = serializers.ReadOnlyField()
    affected_count = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    power_deviation_db = serializers.ReadOnlyField()
    input_cable_code = serializers.CharField(source='input_cable.code', read_only=True, default=None)
    splice_code = serializers.CharField(source='splice_in.code', read_only=True, default=None)
    class Meta:
        model = FiberBox
        fields = '__all__'


class ClientListSerializer(serializers.ModelSerializer):
    box_code = serializers.CharField(source='box.code', read_only=True)
    zone_code = serializers.CharField(source='box.zone.code', read_only=True)
    full_path = serializers.ReadOnlyField()
    power_margin_db = serializers.ReadOnlyField()
    class Meta:
        model = Client
        fields = ['id', 'client_code', 'full_name', 'address', 'status', 'optical_power_rx',
                  'expected_power_dbm', 'box_code', 'zone_code', 'full_path', 'power_margin_db',
                  'latitude', 'longitude']


class ClientSerializer(serializers.ModelSerializer):
    box_code = serializers.CharField(source='box.code', read_only=True)
    zone_code = serializers.CharField(source='box.zone.code', read_only=True)
    full_path = serializers.ReadOnlyField()
    power_margin_db = serializers.ReadOnlyField()
    class Meta:
        model = Client
        fields = '__all__'


class CableSegmentSerializer(serializers.ModelSerializer):
    cable_code = serializers.CharField(source='cable.code', read_only=True)
    cable_type = serializers.CharField(source='cable.cable_type', read_only=True)
    route_as_list = serializers.ReadOnlyField()
    fiber_numbers_list = serializers.ReadOnlyField()
    origin_name = serializers.SerializerMethodField()
    destination_name = serializers.SerializerMethodField()

    def get_origin_name(self, obj):
        el = obj.origin_element
        return getattr(el, 'code', getattr(el, 'name', str(el))) if el else None

    def get_destination_name(self, obj):
        el = obj.destination_element
        return getattr(el, 'code', getattr(el, 'name', str(el))) if el else None

    class Meta:
        model = CableSegment
        fields = '__all__'


class FiberAssignmentSerializer(serializers.ModelSerializer):
    cable_code = serializers.CharField(source='cable.code', read_only=True)
    cable_type = serializers.CharField(source='cable.cable_type', read_only=True)
    target_type = serializers.ReadOnlyField()
    target_code = serializers.SerializerMethodField()

    def get_target_code(self, obj):
        target = obj.target_element
        return getattr(target, 'code', getattr(target, 'client_code', str(target))) if target else None

    class Meta:
        model = FiberAssignment
        fields = '__all__'


class FiberIncidentSerializer(serializers.ModelSerializer):
    affected_client_count = serializers.ReadOnlyField()
    is_open = serializers.ReadOnlyField()
    duration_hours = serializers.ReadOnlyField()
    class Meta:
        model = FiberIncident
        fields = '__all__'
