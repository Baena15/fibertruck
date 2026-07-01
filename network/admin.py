"""
FiberTruck Django Admin
"""
from django.contrib import admin
from .models import OLT, Zone, Splitter, FiberBox, Client, FiberIncident


@admin.register(OLT)
class OLTAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'max_ports', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'address']


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'population_estimate', 'client_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(Splitter)
class SplitterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'ratio', 'olt', 'zone', 'free_ports', 'is_active']
    list_filter = ['ratio', 'zone', 'is_active']
    search_fields = ['code', 'name']


@admin.register(FiberBox)
class FiberBoxAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'zone', 'splitter', 'client_count', 'affected_count', 'status', 'is_active']
    list_filter = ['status', 'zone', 'box_type', 'is_active']
    search_fields = ['code', 'name', 'address']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_code', 'full_name', 'box', 'status', 'optical_power_rx', 'is_active']
    list_filter = ['status', 'box__zone', 'is_active']
    search_fields = ['client_code', 'full_name', 'address']


@admin.register(FiberIncident)
class FiberIncidentAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'severity', 'status', 'incident_type', 'affected_client_count', 'created_at']
    list_filter = ['severity', 'status', 'incident_type']
    search_fields = ['code', 'title', 'description']
