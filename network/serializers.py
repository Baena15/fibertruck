"""
FiberTruck API Serializers
"""
from rest_framework import serializers
from .models import OLT, Zone, Splitter, FiberBox, Client, FiberIncident


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
