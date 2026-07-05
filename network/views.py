"""
FiberTruck API Views
CRUD + Algoritmo de diagnostico LCA (Fault Locator) + Ingenieria FTTH
"""
import json
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from core.views import IsAdmin, IsSupervisor, IsTechnician
from tickets.models import Ticket, TechnicianProfile, DiagnosisLog
from tickets.services.assignment import suggest_technicians
from .models import (
    OLT, Zone, Splitter, FiberBox, Client, FiberIncident,
    FiberCable, SpliceClosure, CableSegment, FiberAssignment,
)
from .serializers import (
    OLTSerializer, ZoneSerializer, SplitterSerializer,
    FiberBoxSerializer, ClientSerializer, ClientListSerializer, FiberIncidentSerializer,
    FiberCableSerializer, SpliceClosureSerializer, CableSegmentSerializer, FiberAssignmentSerializer,
)


User = get_user_model()


ZONES_DATA = [
    {'name': 'La Era - La Asuncion', 'code': 'Z-ERA', 'description': 'Casco historico y zona suroeste de Cieza. Barrio mas antiguo con calles estrechas.', 'lat': 38.2375, 'lng': -1.4195, 'population': 6300},
    {'name': 'San Jose Obrero', 'code': 'Z-SJOR', 'description': 'Zona sureste de Cieza. Barrio humilde con alta densidad. Atravesado por la Rambla del Realejo.', 'lat': 38.2395, 'lng': -1.4150, 'population': 7249},
    {'name': 'San Joaquin', 'code': 'Z-SJOA', 'description': 'Centro urbano de Cieza. Zona comercial y de servicios principales.', 'lat': 38.2390, 'lng': -1.4175, 'population': 5800},
    {'name': 'San Juan Bosco', 'code': 'Z-SJBO', 'description': 'Zona noreste, barrio mas moderno. Edificios de 10-20 anos de antiguedad.', 'lat': 38.2420, 'lng': -1.4140, 'population': 9479},
    {'name': 'La Horta', 'code': 'Z-HORT', 'description': 'Zona norte y noroeste. Mezcla de viviendas nuevas y zona suburbanizada.', 'lat': 38.2440, 'lng': -1.4180, 'population': 4230},
]

OLT_DATA = {'name': 'Cabecera Principal Cieza', 'code': 'OLT-CIEZA-01', 'address': 'Calle Mayor, 45 - Centro de Datos Municipal, Cieza (Murcia)', 'lat': 38.2390, 'lng': -1.4175, 'max_ports': 16}

SPLITTERS_DATA = [
    {'code': 'SPL-ERA-01', 'name': 'Splitter La Era', 'zone_code': 'Z-ERA', 'ratio': '1x32', 'port': 1, 'lat': 38.2375, 'lng': -1.4195},
    {'code': 'SPL-SJOR-01', 'name': 'Splitter San Jose Obrero', 'zone_code': 'Z-SJOR', 'ratio': '1x32', 'port': 2, 'lat': 38.2395, 'lng': -1.4150},
    {'code': 'SPL-SJOA-01', 'name': 'Splitter San Joaquin Central', 'zone_code': 'Z-SJOA', 'ratio': '1x32', 'port': 3, 'lat': 38.2390, 'lng': -1.4175},
    {'code': 'SPL-SJBO-01', 'name': 'Splitter San Juan Bosco', 'zone_code': 'Z-SJBO', 'ratio': '1x32', 'port': 4, 'lat': 38.2420, 'lng': -1.4140},
    {'code': 'SPL-HORT-01', 'name': 'Splitter La Horta', 'zone_code': 'Z-HORT', 'ratio': '1x32', 'port': 5, 'lat': 38.2440, 'lng': -1.4180},
]

BOXES_DATA = [
    {'code': 'CTO-001', 'name': 'Caja La Era - Plaza Constitucion', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 1, 'lat': 38.2378, 'lng': -1.4198, 'address': 'Plaza de la Constitucion, 5'},
    {'code': 'CTO-002', 'name': 'Caja La Era - C/ Real', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 2, 'lat': 38.2372, 'lng': -1.4190, 'address': 'Calle Real, 23'},
    {'code': 'CTO-003', 'name': 'Caja La Era - Museo Siyasa', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 3, 'lat': 38.2370, 'lng': -1.4205, 'address': 'Avda. del Mediterraneo, 55'},
    {'code': 'CTO-004', 'name': 'Caja La Era - C/ Espinosa', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 4, 'lat': 38.2380, 'lng': -1.4185, 'address': 'Calle Espinosa, 12'},
    {'code': 'CTO-005', 'name': 'Caja La Era - C/ Colon', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 5, 'lat': 38.2368, 'lng': -1.4195, 'address': 'Calle Colon, 34'},
    {'code': 'CTO-010', 'name': 'Caja San Jose - C/ Murcia', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 1, 'lat': 38.2398, 'lng': -1.4155, 'address': 'Calle Murcia, 18'},
    {'code': 'CTO-011', 'name': 'Caja San Jose - Centro Cultural', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 2, 'lat': 38.2392, 'lng': -1.4145, 'address': 'Calle Generos de Punto'},
    {'code': 'CTO-012', 'name': 'Caja San Jose - C/ Albacete', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 3, 'lat': 38.2402, 'lng': -1.4148, 'address': 'Calle Albacete, 42'},
    {'code': 'CTO-013', 'name': 'Caja San Jose - Avda. Juan Carlos I', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 4, 'lat': 38.2405, 'lng': -1.4158, 'address': 'Avda. Juan Carlos I, 67'},
    {'code': 'CTO-014', 'name': 'Caja San Jose - C/ Granada', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 5, 'lat': 38.2390, 'lng': -1.4162, 'address': 'Calle Granada, 9'},
    {'code': 'CTO-015', 'name': 'Caja San Jose - C/ Jaen', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 6, 'lat': 38.2400, 'lng': -1.4138, 'address': 'Calle Jaen, 28'},
    {'code': 'CTO-020', 'name': 'Caja San Joaquin - Plaza de Espana', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 1, 'lat': 38.2392, 'lng': -1.4180, 'address': 'Plaza de Espana, 1'},
    {'code': 'CTO-021', 'name': 'Caja San Joaquin - Mercado Abastos', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 2, 'lat': 38.2385, 'lng': -1.4170, 'address': 'Calle del Mercado, 10'},
    {'code': 'CTO-022', 'name': 'Caja San Joaquin - Biblioteca Salmeron', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 3, 'lat': 38.2395, 'lng': -1.4172, 'address': 'Calle Fray Pascual Salmeron, 3'},
    {'code': 'CTO-023', 'name': 'Caja San Joaquin - Oficina Turismo', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 4, 'lat': 38.2388, 'lng': -1.4185, 'address': 'Plaza de Espana, 8'},
    {'code': 'CTO-024', 'name': 'Caja San Joaquin - C/ Marques de Camachos', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 5, 'lat': 38.2398, 'lng': -1.4168, 'address': 'Calle Marques de Camachos, 45'},
    {'code': 'CTO-025', 'name': 'Caja San Joaquin - Delegacion Hacienda', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 6, 'lat': 38.2382, 'lng': -1.4178, 'address': 'Avda. de Murcia, 12'},
    {'code': 'CTO-030', 'name': 'Caja S.J. Bosco - Piscina Cubierta', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 1, 'lat': 38.2415, 'lng': -1.4135, 'address': 'Calle Pintor Villodres'},
    {'code': 'CTO-031', 'name': 'Caja S.J. Bosco - IES Diego Tortosa', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 2, 'lat': 38.2425, 'lng': -1.4130, 'address': 'Avda. de Murcia, 80'},
    {'code': 'CTO-032', 'name': 'Caja S.J. Bosco - Centro Salud Zona Este', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 3, 'lat': 38.2420, 'lng': -1.4145, 'address': 'Calle Molino de Papel, 15'},
    {'code': 'CTO-033', 'name': 'Caja S.J. Bosco - Palacio Justicia', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 4, 'lat': 38.2410, 'lng': -1.4155, 'address': 'Calle Urano, 2'},
    {'code': 'CTO-034', 'name': 'Caja S.J. Bosco - Estacion Autobuses', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 5, 'lat': 38.2430, 'lng': -1.4140, 'address': 'Calle Federico Garcia Lorca, 1'},
    {'code': 'CTO-035', 'name': 'Caja S.J. Bosco - C/ Beniel', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 6, 'lat': 38.2428, 'lng': -1.4125, 'address': 'Calle Beniel, 33'},
    {'code': 'CTO-036', 'name': 'Caja S.J. Bosco - Avda. Alcantarilla', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 7, 'lat': 38.2412, 'lng': -1.4130, 'address': 'Avda. de Alcantarilla, 55'},
    {'code': 'CTO-040', 'name': 'Caja La Horta - Auditorio Gabriel Celaya', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 1, 'lat': 38.2435, 'lng': -1.4185, 'address': 'Calle Rio Segura, 20'},
    {'code': 'CTO-041', 'name': 'Caja La Horta - Escuela Idiomas', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 2, 'lat': 38.2442, 'lng': -1.4175, 'address': 'Calle Santiago, 12'},
    {'code': 'CTO-042', 'name': 'Caja La Horta - C/ San Cristobal', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 3, 'lat': 38.2445, 'lng': -1.4190, 'address': 'Calle San Cristobal, 44'},
    {'code': 'CTO-043', 'name': 'Caja La Horta - Cabezo Fuensantilla', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 4, 'lat': 38.2450, 'lng': -1.4180, 'address': 'Camino del Cabezo, 8'},
    {'code': 'CTO-044', 'name': 'Caja La Horta - C/ Poligono Industrial', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 5, 'lat': 38.2430, 'lng': -1.4165, 'address': 'Calle Industrial, 15'},
]

FIRST_NAMES = ['Antonio', 'Maria', 'Jose', 'Carmen', 'Francisco', 'Ana', 'Manuel', 'Isabel', 'David', 'Laura', 'Juan', 'Pilar', 'Javier', 'Dolores', 'Daniel', 'Teresa', 'Pedro', 'Rosa', 'Alejandro', 'Cristina', 'Miguel', 'Patricia', 'Rafael', 'Sofia', 'Fernando', 'Lucia', 'Luis', 'Martina', 'Pablo', 'Valentina', 'Sergio', 'Julia', 'Andres', 'Paula', 'Jorge', 'Emma', 'Alberto', 'Marta', 'Diego', 'Noa']
LAST_NAMES = ['Garcia', 'Martinez', 'Lopez', 'Sanchez', 'Rodriguez', 'Perez', 'Fernandez', 'Gonzalez', 'Gomez', 'Ruiz', 'Alvarez', 'Jimenez', 'Moreno', 'Romero', 'Hernandez', 'Diaz', 'Muñoz', 'Serrano', 'Iglesias', 'Medina', 'Cieza', 'Segura', 'Vega', 'Murcia', 'Rico', 'Blanco', 'Castillo', 'Torres']


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def setup_view(request):
    """
    Endpoint para inicializar la base de datos con el despliegue FTTH de Cieza
    y los tickets de demo de FiberTrack.
    """
    try:
        from django.core.management import call_command
        call_command('auto_setup')

        users = User.objects.filter(username__in=['admin', 'supervisor1', 'tecnico1', 'tecnico2', 'tecnico3'])
        user_list = []
        for u in users:
            role_map = {'admin': 'admin', 'supervisor': 'supervisor', 'technician': 'technician'}
            user_list.append({'username': u.username, 'password': 'admin123' if u.username == 'admin' else 'super123' if u.username == 'supervisor1' else 'tecno123', 'role': role_map.get(u.role, u.role)})

        return Response({
            'success': True,
            'message': 'FiberTruck / FiberTrack inicializado correctamente',
            'users': user_list,
            'deployment': {
                'olt': OLT.objects.count(),
                'zones': Zone.objects.count(),
                'splitters': Splitter.objects.count(),
                'boxes': FiberBox.objects.count(),
                'clients': Client.objects.count(),
                'tickets': Ticket.objects.count(),
                'technician_profiles': TechnicianProfile.objects.count(),
            },
        })
    except Exception as e:
        import traceback
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=500)


# ============================================================
# VIEWSETS CORE (existentes)
# ============================================================

class OLTViewSet(viewsets.ModelViewSet):
    queryset = OLT.objects.all()
    serializer_class = OLTSerializer
    permission_classes = [IsSupervisor]
    pagination_class = None


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsSupervisor()]


class SplitterViewSet(viewsets.ModelViewSet):
    queryset = Splitter.objects.all()
    serializer_class = SplitterSerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsSupervisor()]

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        zone_id = request.query_params.get('zone')
        if zone_id:
            qs = self.queryset.filter(zone_id=zone_id, is_active=True)
            return Response(SplitterSerializer(qs, many=True).data)
        return Response([])


class FiberBoxViewSet(viewsets.ModelViewSet):
    queryset = FiberBox.objects.all()
    serializer_class = FiberBoxSerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search', 'clients', 'hierarchy']:
            return [permissions.IsAuthenticated()]
        return [IsSupervisor()]

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        zone_id = request.query_params.get('zone')
        if zone_id:
            qs = self.queryset.filter(zone_id=zone_id, is_active=True)
            return Response(FiberBoxSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def by_splitter(self, request):
        splitter_id = request.query_params.get('splitter')
        if splitter_id:
            qs = self.queryset.filter(splitter_id=splitter_id, is_active=True)
            return Response(FiberBoxSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def search(self, request):
        code = request.query_params.get('code', '').upper()
        if code:
            try:
                box = FiberBox.objects.get(code__iexact=code, is_active=True)
                return Response(FiberBoxSerializer(box).data)
            except FiberBox.DoesNotExist:
                return Response({'error': f'Caja {code} no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'error': 'Introduce un codigo de caja'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def clients(self, request, pk=None):
        box = self.get_object()
        clients = box.clients.filter(is_active=True)
        return Response(ClientListSerializer(clients, many=True).data)

    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        box = self.get_object()
        clients = box.clients.filter(is_active=True)
        return Response({
            'olt': {'id': box.splitter.olt.id, 'code': box.splitter.olt.code, 'name': box.splitter.olt.name},
            'splitter': {'id': box.splitter.id, 'code': box.splitter.code, 'name': box.splitter.name},
            'box': {'id': box.id, 'code': box.code, 'name': box.name, 'status': box.status},
            'clients': ClientListSerializer(clients, many=True).data,
            'affected_count': box.affected_count,
            'total_clients': clients.count(),
        })


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_zone', 'by_box', 'affected']:
            return [permissions.IsAuthenticated()]
        if self.action == 'report_outage':
            return [IsTechnician()]
        return [IsSupervisor()]

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        zone_id = request.query_params.get('zone')
        if zone_id:
            qs = self.queryset.filter(box__zone_id=zone_id, is_active=True)
            return Response(ClientListSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def by_box(self, request):
        box_id = request.query_params.get('box')
        if box_id:
            qs = self.queryset.filter(box_id=box_id, is_active=True)
            return Response(ClientListSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def affected(self, request):
        qs = self.queryset.filter(status='affected', is_active=True)
        return Response(ClientListSerializer(qs, many=True).data)

    @action(detail=False, methods=['post'])
    def report_outage(self, request):
        client_id = request.data.get('client_id')
        if not client_id:
            return Response({'error': 'client_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        client.status = 'affected'
        client.save()
        diagnosis = self._run_diagnosis(client)
        return Response({'client': ClientSerializer(client).data, 'diagnosis': diagnosis})

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """Restaura un cliente a estado activo tras reparar su avería."""
        client = self.get_object()
        optical_power = request.data.get('optical_power_rx')
        client.status = 'active'
        if optical_power is not None:
            try:
                client.optical_power_rx = float(optical_power)
            except (ValueError, TypeError):
                pass
        client.save()
        # Actualizar logs de diagnóstico abiertos para este cliente
        DiagnosisLog.objects.filter(
            affected_clients__contains=[{'id': client.id}],
            resolved=False
        ).update(resolved=True, resolved_at=timezone.now())
        return Response({'success': True, 'client': ClientSerializer(client).data})

    def _run_diagnosis(self, initial_client):
        """Algoritmo FTFL: Fault Locator con puntos de divergencia"""
        from collections import Counter
        same_box_affected = Client.objects.filter(box=initial_client.box, status='affected', is_active=True).exclude(id=initial_client.id)
        same_splitter_affected = Client.objects.filter(box__splitter=initial_client.splitter, status='affected', is_active=True).exclude(box=initial_client.box)
        total_affected = Client.objects.filter(box__splitter=initial_client.splitter, status='affected', is_active=True).count()
        same_box_count = same_box_affected.count()
        same_splitter_count = same_splitter_affected.count()

        if total_affected >= 3:
            severity = 'critical'
            confidence = min(85 + (total_affected - 3) * 5, 99)
            if same_splitter_count > 0:
                diagnosis_type = 'splitter_fault'
                root_node = initial_client.splitter.code
                message = f"ALERTA: {total_affected} clientes afectados en splitter {initial_client.splitter.code}."
            else:
                diagnosis_type = 'fiber_break'
                root_node = initial_client.box.code
                message = f"{total_affected} clientes afectados en caja {initial_client.box.code}."
        elif same_box_count >= 1:
            severity = 'high'
            confidence = 75 + same_box_count * 5
            diagnosis_type = 'connector_fault'
            root_node = initial_client.box.code
            message = f"{same_box_count + 1} clientes afectados en {initial_client.box.code}."
        else:
            severity = 'medium'
            confidence = 60
            diagnosis_type = 'unknown'
            root_node = initial_client.client_code
            message = f"Solo {initial_client.full_name} esta afectado."

        return {
            'severity': severity, 'confidence': confidence, 'diagnosis_type': diagnosis_type,
            'root_cause_node': root_node, 'message': message,
            'affected_total': total_affected, 'suspected_fault_location': root_node,
            'recommended_action': self._get_recommended_action(diagnosis_type),
            'affected_clients_details': [
                {'code': c.client_code, 'name': c.full_name, 'address': c.address}
                for c in Client.objects.filter(box__splitter=initial_client.splitter, status='affected', is_active=True)
            ],
        }

    def _get_recommended_action(self, diagnosis_type):
        actions = {
            'splitter_fault': 'Revisar splitter y fibra de alimentacion.',
            'fiber_break': 'Inspeccionar conectores de la caja.',
            'connector_fault': 'Revisar conectores y splitter interno.',
            'olt_fault': 'Verificar estado del OLT. Escalar al NOC.',
            'power_issue': 'Medir potencia optica con power meter.',
            'unknown': 'Verificar ONT del cliente y fibra de drop.',
        }
        return actions.get(diagnosis_type, 'Diagnostico completo en campo.')


class FiberIncidentViewSet(viewsets.ModelViewSet):
    queryset = FiberIncident.objects.all()
    serializer_class = FiberIncidentSerializer
    pagination_class = None
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'open', 'stats']:
            return [permissions.IsAuthenticated()]
        return [IsSupervisor()]

    @action(detail=False, methods=['get'])
    def open(self, request):
        qs = self.queryset.filter(status__in=['open', 'diagnosing', 'assigned', 'in_progress'])
        return Response(FiberIncidentSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def stats(self, request):
        return Response({
            'total_incidents': self.queryset.count(),
            'open_incidents': self.queryset.filter(status__in=['open', 'diagnosing', 'assigned', 'in_progress']).count(),
            'critical_incidents': self.queryset.filter(severity='critical', status__in=['open', 'diagnosing', 'assigned', 'in_progress']).count(),
            'resolved_today': self.queryset.filter(status='resolved').count(),
            'total_clients': Client.objects.filter(is_active=True).count(),
            'affected_clients': Client.objects.filter(status='affected', is_active=True).count(),
            'active_boxes': FiberBox.objects.filter(is_active=True).count(),
            'faulty_boxes': FiberBox.objects.filter(status='fault', is_active=True).count(),
        })


# ============================================================
# NUEVOS VIEWSETS FTTH - Ingenieria de Red
# ============================================================

class FiberCableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para cables de fibra optica.
    Expone datos de ingenieria: tipo, capacidad, uso y tramos.
    """
    queryset = FiberCable.objects.all()
    serializer_class = FiberCableSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # El dashboard necesita la lista completa

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Filtrar cables por tipo: feeder, distribution, drop"""
        cable_type = request.query_params.get('type')
        if cable_type:
            qs = self.queryset.filter(cable_type=cable_type, is_active=True)
            return Response(FiberCableSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        """Filtrar cables por zona: ?zone=<id>"""
        zone_id = request.query_params.get('zone')
        if zone_id:
            cables = self.queryset.filter(
                Q(segments__to_splice__zone_id=zone_id) |
                Q(segments__to_splitter__zone_id=zone_id) |
                Q(segments__to_box__zone_id=zone_id)
            ).distinct()
            return Response(FiberCableSerializer(cables, many=True).data)
        return Response([])


class SpliceClosureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para cajas de empalme.
    Incluye filtrado por zona.
    """
    queryset = SpliceClosure.objects.all()
    serializer_class = SpliceClosureSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        """Filtrar empalmes por zona: ?zone=<id>"""
        zone_id = request.query_params.get('zone')
        if zone_id:
            qs = self.queryset.filter(zone_id=zone_id, is_active=True)
            return Response(SpliceClosureSerializer(qs, many=True).data)
        return Response([])


class CableSegmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para tramos de cable.
    Permite filtrar por zona y por tipo de segmento.
    """
    queryset = CableSegment.objects.all()
    serializer_class = CableSegmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=['get'])
    def by_zone(self, request):
        """Filtrar tramos por zona: ?zone=<id>"""
        zone_id = request.query_params.get('zone')
        if zone_id:
            segs = self.queryset.filter(
                Q(from_splice__zone_id=zone_id) | Q(to_splice__zone_id=zone_id) |
                Q(from_splitter__zone_id=zone_id) | Q(to_splitter__zone_id=zone_id) |
                Q(from_box__zone_id=zone_id) | Q(to_box__zone_id=zone_id)
            ).distinct()
            return Response(CableSegmentSerializer(segs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def feeder(self, request):
        """Devuelve solo los tramos feeder (olt_to_splice)"""
        qs = self.queryset.filter(segment_type='olt_to_splice', is_active=True)
        return Response(CableSegmentSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """Devuelve tramos de distribucion: splice_to_splitter, splice_to_box"""
        qs = self.queryset.filter(segment_type__in=['splice_to_splitter', 'splice_to_box'], is_active=True)
        return Response(CableSegmentSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def drop(self, request):
        """Devuelve tramos de drop: splitter_to_box, box_to_client"""
        qs = self.queryset.filter(segment_type__in=['splitter_to_box', 'box_to_client'], is_active=True)
        return Response(CableSegmentSerializer(qs, many=True).data)


class FiberAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para asignaciones de fibra.
    Permite filtrar por cable y por caja.
    """
    queryset = FiberAssignment.objects.all()
    serializer_class = FiberAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=['get'])
    def by_cable(self, request):
        """Filtrar asignaciones por cable: ?cable=<id>"""
        cable_id = request.query_params.get('cable')
        if cable_id:
            qs = self.queryset.filter(cable_id=cable_id)
            return Response(FiberAssignmentSerializer(qs, many=True).data)
        return Response([])

    @action(detail=False, methods=['get'])
    def by_box(self, request):
        """Filtrar asignaciones por caja: ?box=<id>"""
        box_id = request.query_params.get('box')
        if box_id:
            qs = self.queryset.filter(box_id=box_id)
            return Response(FiberAssignmentSerializer(qs, many=True).data)
        return Response([])


# ============================================================
# ENDPOINTS FTTH AVANZADOS - Diagnostico, Topologia y Trace
# ============================================================

def _run_diagnosis(box_code, affected_client_ids):
    """
    Ejecuta el algoritmo de diagnostico FTTH v2 y devuelve un dict con los resultados.
    Si hay error devuelve {'error': '...', 'status': codigo_http}.
    """
    if not box_code:
        return {'error': 'box_code es requerido', 'status': status.HTTP_400_BAD_REQUEST}

    try:
        box = FiberBox.objects.select_related('splitter', 'splitter__olt', 'zone').get(code__iexact=box_code, is_active=True)
    except FiberBox.DoesNotExist:
        return {'error': f'Caja {box_code} no encontrada', 'status': status.HTTP_404_NOT_FOUND}

    # 1. Obtener clientes afectados por IDs o por status
    if affected_client_ids:
        affected_clients = Client.objects.filter(
            id__in=affected_client_ids, box=box, is_active=True
        ).select_related('box')
    else:
        affected_clients = Client.objects.filter(
            box=box, status='affected', is_active=True
        ).select_related('box')

    affected_count = affected_clients.count()

    # 2. Contar cuantos afectados hay en la misma caja, mismo splitter, misma zona
    same_box_count = affected_count

    # Verificar si hay mas clientes afectados en cajas del mismo splitter
    splitter_affected_boxes = FiberBox.objects.filter(
        splitter=box.splitter, is_active=True
    ).annotate(
        affected_client_count=Count('clients', filter=Q(clients__status='affected', clients__is_active=True))
    )
    boxes_with_issues = [b for b in splitter_affected_boxes if b.affected_client_count > 0]
    total_affected_in_splitter = sum(b.affected_client_count for b in boxes_with_issues)

    # 3-6. Determinar severidad
    if total_affected_in_splitter >= 3:
        severity = 'critical'
        confidence = min(85 + (total_affected_in_splitter - 3) * 5, 99)
    elif same_box_count >= 3:
        severity = 'high'
        confidence = 80
    elif same_box_count >= 2:
        severity = 'medium'
        confidence = 65
    else:
        severity = 'low'
        confidence = 50

    # 7. Buscar tramos afectados en la topologia
    affected_segments = CableSegment.objects.filter(
        Q(to_box=box) | Q(from_splitter=box.splitter) | Q(to_splitter=box.splitter),
        is_active=True
    ).select_related('cable').order_by('segment_type')

    # Seleccionar el tramo mas probable (prioridad: splitter_to_box > distribution > feeder)
    affected_segment_data = None
    for seg in affected_segments:
        if seg.segment_type == 'splitter_to_box':
            affected_segment_data = seg
            break
    if not affected_segment_data:
        affected_segment_data = affected_segments.first()

    # Construir datos del tramo afectado
    segment_json = None
    if affected_segment_data:
        segment_json = {
            'id': affected_segment_data.id,
            'segment_type': affected_segment_data.segment_type,
            'cable': affected_segment_data.cable.code if affected_segment_data.cable else None,
            'fiber_numbers': affected_segment_data.fiber_numbers,
            'attenuation_db': affected_segment_data.attenuation_db,
            'length_m': affected_segment_data.length_m,
            'route_coordinates': affected_segment_data.route_as_list,
        }

    # 8. Calcular potencia esperada vs medida
    splitter_loss = box.splitter.insertion_loss_db if hasattr(box.splitter, 'insertion_loss_db') else 17.0
    olt_power = box.splitter.olt.output_power_dbm if hasattr(box.splitter.olt, 'output_power_dbm') else 3.0

    fiber_attenuation = 0.4 * (affected_segment_data.length_m / 1000 if affected_segment_data else 0)
    expected_dbm = round(olt_power - splitter_loss - fiber_attenuation, 2)

    measured_powers = [c.optical_power_rx for c in affected_clients if c.optical_power_rx is not None]
    measured_dbm = round(sum(measured_powers) / len(measured_powers), 2) if measured_powers else -45.0
    loss_db = round(expected_dbm - measured_dbm, 2) if measured_dbm else 27.5

    if loss_db > 20:
        power_status = 'CORTE TOTAL'
    elif loss_db > 10:
        power_status = 'PERDIDA SEVERA'
    elif loss_db > 5:
        power_status = 'PERDIDA MODERADA'
    else:
        power_status = 'NORMAL'

    # 9. Coordenadas para la ruta afectada
    affected_route = []
    if affected_segment_data and affected_segment_data.route_as_list:
        affected_route = affected_segment_data.route_as_list
    else:
        affected_route = [
            [box.splitter.latitude, box.splitter.longitude],
            [box.latitude, box.longitude],
        ]

    # 9b. Punto intermedio de la ruta como ubicacion estimada del fallo
    if affected_route:
        mid_idx = len(affected_route) // 2
        fault_coords = affected_route[mid_idx]
    else:
        fault_coords = [(box.splitter.latitude + box.latitude) / 2,
                        (box.splitter.longitude + box.longitude) / 2]

    # 9c. Generar instrucciones paso a paso con direcciones
    instructions = _generate_diagnose_instructions(box, affected_segment_data, affected_clients, severity)

    # 9d. Posibles soluciones concretas segun el tipo de fallo
    possible_solutions = _get_possible_solutions(box, affected_segment_data, severity, power_status)

    # 10. Clientes afectados serializados
    clients_data = ClientListSerializer(affected_clients, many=True).data

    result = {
        'severity': severity,
        'confidence': confidence,
        'affected_segment': segment_json,
        'power_analysis': {
            'expected_dbm': expected_dbm,
            'measured_dbm': measured_dbm,
            'loss_db': loss_db,
            'status': power_status,
        },
        'fault_location': {
            'description': _build_fault_description(box, affected_segment_data),
            'coordinates': fault_coords,
            'address': box.address,
        },
        'recommended_action': instructions,
        'possible_solutions': possible_solutions,
        'affected_clients': clients_data,
        'affected_route': affected_route,
        'affected_count': affected_count,
        'total_affected_in_splitter': total_affected_in_splitter,
        'boxes_affected_in_splitter': len(boxes_with_issues),
    }
    result["box"] = box
    result["affected_clients_qs"] = affected_clients
    return result

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def diagnose_v2(request):
    """
    Diagnostico avanzado FTTH v2 con analisis de tramos y potencia.
    """
    box_code = request.data.get('box_code', '')
    affected_client_ids = request.data.get('affected_client_ids', [])
    result = _run_diagnosis(box_code, affected_client_ids)
    if 'error' in result:
        status_code = result.pop('status', status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status_code)
    result.pop('box', None)
    result.pop('affected_clients_qs', None)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def diagnose_create_ticket(request):
    """
    Ejecuta el diagnostico y crea un ticket operativo a partir del resultado.
    Opcionalmente asigna el tecnico mas cercano disponible.
    POST /api/diagnose/v2/create_ticket/
    Body: {"box_code": "CTO-0023", "affected_client_ids": [143], "auto_assign": true}
    """
    box_code = request.data.get('box_code', '')
    affected_client_ids = request.data.get('affected_client_ids', [])
    auto_assign = request.data.get('auto_assign', False)

    diag = _run_diagnosis(box_code, affected_client_ids)
    if 'error' in diag:
        status_code = diag.pop('status', status.HTTP_400_BAD_REQUEST)
        return Response(diag, status=status_code)

    box = diag.pop('box')
    affected_clients_qs = diag.pop('affected_clients_qs')
    affected_clients = list(affected_clients_qs)

    severity = diag['severity']
    priority_map = {'critical': 'critical', 'high': 'high', 'medium': 'medium', 'low': 'low'}
    ticket_type = 'network_fault' if diag.get('affected_count', 0) > 1 or diag.get('total_affected_in_splitter', 0) > 1 else 'home_fault'

    first_client = affected_clients[0] if affected_clients else None

    title = f"Avería {box.code} - {diag.get('affected_count', 0)} cliente(s) afectado(s)"
    description_lines = [
        f"Diagnóstico automático: {diag.get('confidence', 0)}% de confianza.",
        f"Fallo detectado: {diag.get('fault_location', {}).get('description', 'N/A')}",
        f"Potencia esperada: {diag.get('power_analysis', {}).get('expected_dbm')} dBm | "
        f"Medida: {diag.get('power_analysis', {}).get('measured_dbm')} dBm | "
        f"Pérdida: {diag.get('power_analysis', {}).get('loss_db')} dB",
        "",
        "Acción recomendada:",
        diag.get('recommended_action', ''),
        "",
        "Posibles soluciones:",
    ]
    description_lines.extend([f"- {s}" for s in diag.get('possible_solutions', [])])
    description = "\\n".join(description_lines)

    ticket = Ticket.objects.create(
        title=title,
        description=description,
        ticket_type=ticket_type,
        priority=priority_map.get(severity, 'medium'),
        client=first_client,
        affected_box=box,
        affected_splitter=box.splitter,
        address=box.address or '',
        latitude=box.latitude,
        longitude=box.longitude,
        sla_hours=4 if severity == 'critical' else 8 if severity == 'high' else 24,
        created_by=request.user,
    )

    suggestions = []
    if ticket.latitude is not None and ticket.longitude is not None:
        suggestions = suggest_technicians(ticket, limit=3)

    assigned = None
    if auto_assign and suggestions:
        best = suggestions[0]
        tech_id = best.get('user_id') or best.get('technician_id')
        if tech_id:
            try:
                technician = User.objects.get(pk=tech_id, role='technician')
                ticket.assigned_to = technician
                ticket.coordinator = request.user
                ticket.status = 'assigned'
                ticket.assigned_at = timezone.now()
                ticket.save()
                assigned = technician.get_full_name() or technician.username
            except User.DoesNotExist:
                pass

    DiagnosisLog.objects.create(
        box=box,
        splitter=box.splitter,
        ticket=ticket,
        severity=diag['severity'],
        confidence=diag['confidence'],
        power_analysis=diag.get('power_analysis', {}),
        affected_clients=diag.get('affected_clients', []),
        possible_solutions=diag.get('possible_solutions', []),
        recommended_action=diag.get('recommended_action', ''),
        affected_route=diag.get('affected_route', []),
        created_by=request.user,
    )

    return Response({
        'success': True,
        'ticket_id': ticket.id,
        'ticket_code': ticket.code,
        'diagnosis': diag,
        'suggestions': suggestions,
        'assigned_to': assigned,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def diagnosis_history(request):
    """Devuelve el historial de diagnósticos automáticos."""
    limit = int(request.query_params.get('limit', 50))
    qs = DiagnosisLog.objects.select_related('box', 'splitter', 'ticket').order_by('-created_at')[:limit]
    data = []
    for log in qs:
        data.append({
            'id': log.id,
            'box_code': log.box.code,
            'box_name': log.box.name,
            'splitter_code': log.splitter.code if log.splitter else None,
            'severity': log.severity,
            'confidence': log.confidence,
            'power_analysis': log.power_analysis,
            'affected_clients': log.affected_clients,
            'possible_solutions': log.possible_solutions,
            'recommended_action': log.recommended_action,
            'affected_route': log.affected_route,
            'solution_applied': log.solution_applied,
            'resolved': log.resolved,
            'resolved_at': log.resolved_at,
            'ticket_code': log.ticket.code if log.ticket else None,
            'ticket_status': log.ticket.status if log.ticket else None,
            'created_at': log.created_at,
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def apply_solution(request, log_id):
    """
    Aplica una solucion a un diagnostico guardado, resuelve el ticket asociado
    y opcionalmente restaura los clientes afectados.
    POST /api/diagnose/v2/apply_solution/<log_id>/
    Body: {"solution_applied": "Reparado empalme...", "restore_clients": true}
    """
    try:
        log = DiagnosisLog.objects.select_related('ticket', 'box').get(pk=log_id)
    except DiagnosisLog.DoesNotExist:
        return Response({'error': 'Diagnostico no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    solution_applied = request.data.get('solution_applied', '').strip()
    restore_clients = request.data.get('restore_clients', True)

    if not solution_applied:
        return Response({'error': 'solution_applied es requerido'}, status=status.HTTP_400_BAD_REQUEST)

    log.solution_applied = solution_applied
    log.resolved = True
    log.resolved_at = timezone.now()
    log.save()

    # Resolver ticket asociado si existe y esta abierto
    ticket = log.ticket
    if ticket and ticket.status not in ['closed', 'cancelled', 'resolved']:
        ticket.solution_applied = solution_applied
        ticket.status = 'resolved'
        ticket.resolved_at = timezone.now()
        ticket.save()

    # Restaurar clientes afectados
    restored = 0
    if restore_clients and log.affected_clients:
        client_ids = []
        for item in log.affected_clients:
            cid = item.get('id') if isinstance(item, dict) else None
            if cid:
                client_ids.append(cid)
        if client_ids:
            restored = Client.objects.filter(id__in=client_ids, status='affected').update(
                status='active', updated_at=timezone.now()
            )

    return Response({
        'success': True,
        'log_id': log.id,
        'ticket_code': ticket.code if ticket else None,
        'solution_applied': solution_applied,
        'resolved': log.resolved,
        'restored_clients': restored,
    })


def _build_fault_description(box, segment):
    """Construye una descripcion textual del fallo para el tecnico."""
    if segment:
        return (
            f"Tramo {segment.get_segment_type_display()} "
            f"del cable {segment.cable.code} "
            f"(fibras #{segment.fiber_numbers}, {segment.length_m}m) "
            f"entre {box.splitter.code} y la caja {box.code}"
        )
    return f"Posible fallo entre splitter {box.splitter.code} y caja {box.code}"


def _generate_diagnose_instructions(box, segment, affected_clients, severity):
    """Genera instrucciones paso a paso detalladas para el tecnico de campo."""
    lines = []

    # Paso 1: Ir a la caja
    lines.append(f"1. Dirigirse a la caja {box.code} ubicada en {box.address}.")

    # Paso 2: Medir potencia en la caja
    lines.append("2. Medir potencia optica con power meter en el conector de entrada de la caja.")

    # Paso 3: Verificar splitter
    lines.append(
        f"3. Si hay potencia en la caja: desplazarse al splitter {box.splitter.code} "
        f"({box.splitter.address}) y medir salida del puerto asignado a esta caja."
    )

    # Paso 4: Verificar cable
    if segment:
        lines.append(
            f"4. Si el splitter tiene potencia pero la caja no: revisar cable "
            f"{segment.cable.code} fibra #{segment.fiber_numbers} entre ambos puntos "
            f"({segment.length_m}m de longitud)."
        )
    else:
        lines.append(
            f"4. Si el splitter tiene potencia pero la caja no: revisar el cable "
            f"entre {box.splitter.code} y {box.code}."
        )

    # Paso 5: Buscar rotura visual
    if segment and segment.route_as_list:
        lines.append(
            f"5. Inspeccionar visualmente la trayectoria completa desde "
            f"{box.splitter.address} hasta {box.address} buscando roturas."
        )
    else:
        lines.append(
            f"5. Inspeccionar visualmente el trayecto desde el splitter "
            f"hasta la caja {box.code}."
        )

    # Recomendacion adicional segun severidad
    if severity == 'critical':
        lines.append(
            "\n[ALERTA CRITICA] Multiples cajas afectadas bajo el mismo splitter. "
            "Priorizar revision del splitter y cable de distribucion. Escalar al NOC inmediatamente."
        )
    elif severity == 'high':
        lines.append(
            "\n[PRIORIDAD ALTA] Multiples clientes afectados en la misma caja. "
            "Probable corte en el cable drop o fallo en conectores de la caja."
        )
    elif severity == 'medium':
        lines.append(
            "\n[PRIORIDAD MEDIA] Revisar conectores internos de la caja y estado de la fibra de drop."
        )
    else:
        lines.append(
            "\n[PRIORIDAD BAJA] Verificar ONT del cliente y cable de drop individual."
        )

    return "\n".join(lines)


def _get_possible_solutions(box, segment, severity, power_status):
    """Devuelve una lista de soluciones concretas ordenadas por probabilidad."""
    solutions = []

    if power_status == 'CORTE TOTAL':
        solutions.append(
            'Reparar o empalmar la fibra cortada en el tramo ' +
            (segment.cable.code if segment and segment.cable else 'desconocido') +
            '. Verificar con OTDR la distancia exacta del corte.'
        )
        solutions.append(
            'Revisar conectores y adaptadores en ' + box.splitter.code +
            ' y en ' + box.code + ': limpiar, reapuntar o reemplazar si estan quemados.'
        )
        if segment and segment.length_m and segment.length_m > 200:
            solutions.append(
                'Inspeccionar canalizacion subterranea/aerea en el recorrido de ' +
                str(segment.length_m) + 'm: buscar roturas por obras, arbolado o roedores.'
            )
    elif power_status == 'PERDIDA SEVERA':
        solutions.append(
            'Limpiar y reapuntar conectores en ambos extremos del cable ' +
            (segment.cable.code if segment and segment.cable else 'afectado') + '.'
        )
        solutions.append(
            'Sustituir splitter ' + box.splitter.code + ' si la perdida es uniforme en todos los puertos.'
        )
        solutions.append('Revisar empalmes intermedios: mala fusion o macrocurvatura.')
    elif power_status == 'PERDIDA MODERADA':
        solutions.append('Revisar y limpiar conector de entrada de la caja ' + box.code + '.')
        solutions.append('Verificar macrocurvaturas en el cable de drop y tendido interior.')
        solutions.append('Comprobar estado de la ONT/Receptor del cliente.')
    else:
        solutions.append('Verificar configuracion de la ONT y reiniciar equipo.')
        solutions.append('Comprobar que no haya saturacion del receptor (potencia demasiado alta).')

    if severity == 'critical':
        solutions.insert(0, 'Escalar al NOC y coordinar cierre de calle/zona si el corte afecta a multiples cajas.')
        solutions.insert(1, 'Revisar splitter principal ' + box.splitter.code + ' y cable de distribucion compartido.')
    elif severity == 'high':
        solutions.insert(0, 'Priorizar visita a la caja ' + box.code + ': multiples clientes afectados.')

    return solutions


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def topology_view(request):
    """
    Topologia completa de la red para diagrama.
    GET /api/topology/

    Devuelve arbol jerarquico: OLT -> Feeder -> Empalmes -> Distribution -> Splitters -> Drop -> Cajas
    Con potencias, utilizacion de fibras, y conteos.
    """
    # 1. Obtener OLT
    olt = OLT.objects.filter(is_active=True).first()
    olt_data = OLTSerializer(olt).data if olt else None

    # 2. Construir topologia por zonas
    zones = Zone.objects.filter(is_active=True).select_related()
    zones_data = []

    for zone in zones:
        # Empalmes de la zona
        splices = SpliceClosure.objects.filter(zone=zone, is_active=True)
        splice_data = SpliceClosureSerializer(splices, many=True).data

        # Splitters de la zona
        splitters = Splitter.objects.filter(zone=zone, is_active=True).select_related('olt')
        splitter_data = SplitterSerializer(splitters, many=True).data

        # 3. Tramos feeder (OLT -> Empalme)
        feeder_segments = CableSegment.objects.filter(
            segment_type='olt_to_splice',
            to_splice__zone=zone,
            is_active=True
        ).select_related('cable')
        feeder_data = CableSegmentSerializer(feeder_segments, many=True).data

        # Tramos distribution (Empalme -> Splitter)
        distribution_segments = CableSegment.objects.filter(
            segment_type='splice_to_splitter',
            to_splitter__zone=zone,
            is_active=True
        ).select_related('cable')
        distribution_data = CableSegmentSerializer(distribution_segments, many=True).data

        # Tramos splice_to_box (Empalme -> Caja directo)
        splice_to_box_segments = CableSegment.objects.filter(
            segment_type='splice_to_box',
            to_box__zone=zone,
            is_active=True
        ).select_related('cable')
        splice_box_data = CableSegmentSerializer(splice_to_box_segments, many=True).data

        # Tramos splitter -> caja (drop principal)
        splitter_to_box_segments = CableSegment.objects.filter(
            segment_type='splitter_to_box',
            to_box__zone=zone,
            is_active=True
        ).select_related('cable')
        splitter_box_data = CableSegmentSerializer(splitter_to_box_segments, many=True).data

        # Tramos caja -> cliente (drop final)
        box_to_client_segments = CableSegment.objects.filter(
            segment_type='box_to_client',
            from_box__zone=zone,
            is_active=True
        ).select_related('cable')
        drop_data = CableSegmentSerializer(box_to_client_segments, many=True).data

        # 4. Cajas de la zona
        boxes = FiberBox.objects.filter(zone=zone, is_active=True).select_related('splitter')
        boxes_data = FiberBoxSerializer(boxes, many=True).data

        # 5. Contar clientes
        clients_count = Client.objects.filter(box__zone=zone, is_active=True).count()

        zones_data.append({
            'zone': ZoneSerializer(zone).data,
            'splices': splice_data,
            'splitters': splitter_data,
            'feeder_segments': feeder_data,
            'distribution_segments': distribution_data,
            'splice_to_box_segments': splice_box_data,
            'splitter_to_box_segments': splitter_box_data,
            'drop_segments': drop_data,
            'boxes': boxes_data,
            'clients_count': clients_count,
        })

    return Response({
        'olt': olt_data,
        'zones': zones_data,
        'summary': {
            'total_zones': zones.count(),
            'total_clients': Client.objects.filter(is_active=True).count(),
            'total_boxes': FiberBox.objects.filter(is_active=True).count(),
            'total_splitters': Splitter.objects.filter(is_active=True).count(),
            'total_cables': FiberCable.objects.filter(is_active=True).count(),
            'total_segments': CableSegment.objects.filter(is_active=True).count(),
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def fiber_trace_view(request):
    """
    Trace de ruta de fibra desde OLT hasta caja o cliente.
    GET /api/fiber-trace/?client_id=45
    GET /api/fiber-trace/?box_id=12

    Devuelve la cadena completa: OLT -> Feeder(fibra N) -> Empalme -> Distribution(fibra N) -> Splitter -> Drop(fibra N) -> Caja -> [Cliente]
    Con potencias en cada nodo, atenuaciones y coordenadas de ruta.
    """
    client_id = request.query_params.get('client_id')
    box_id = request.query_params.get('box_id')

    if not client_id and not box_id:
        return Response(
            {'error': 'client_id o box_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    client = None
    if client_id:
        try:
            client = Client.objects.select_related(
                'box', 'box__splitter', 'box__splitter__olt', 'box__zone'
            ).get(id=client_id, is_active=True)
        except Client.DoesNotExist:
            return Response(
                {'error': f'Cliente {client_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        box = client.box
    else:
        try:
            box = FiberBox.objects.select_related(
                'splitter', 'splitter__olt', 'zone'
            ).get(id=box_id, is_active=True)
        except FiberBox.DoesNotExist:
            return Response(
                {'error': f'Caja {box_id} no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    splitter = box.splitter
    olt = splitter.olt
    trace_chain = []

    # Nodo 1: OLT
    olt_power = getattr(olt, 'output_power_dbm', 3.0)
    trace_chain.append({
        'step': 1,
        'element_type': 'olt',
        'id': olt.id,
        'code': olt.code,
        'name': olt.name,
        'power_dbm': olt_power,
        'attenuation_db': 0,
        'cumulative_loss_db': 0,
        'coordinates': [olt.latitude, olt.longitude] if olt.latitude else None,
    })

    # Buscar tramo feeder (OLT -> Empalme) que alimente al splitter destino
    feeder_segments = CableSegment.objects.filter(
        segment_type='olt_to_splice',
        is_active=True
    ).select_related('cable', 'to_splice')

    splice = None
    for seg in feeder_segments:
        if seg.to_splice:
            # Seleccionar el empalme que alimenta la zona del splitter destino
            if seg.to_splice.id == splitter.splice_in_id:
                splice = seg.to_splice
                feeder_loss = seg.attenuation_db or round(0.4 * (seg.length_m / 1000), 2)
                trace_chain.append({
                    'step': 2,
                    'element_type': 'feeder_segment',
                    'id': seg.id,
                    'code': seg.cable.code if seg.cable else None,
                    'name': f"Feeder {seg.cable.code if seg.cable else 'N/A'}",
                    'fiber_numbers': seg.fiber_numbers,
                    'length_m': seg.length_m,
                    'power_dbm': round(olt_power - feeder_loss, 2),
                    'attenuation_db': feeder_loss,
                    'cumulative_loss_db': feeder_loss,
                    'coordinates': seg.route_as_list[0] if seg.route_as_list else None,
                    'route': seg.route_as_list,
                })
                splice_power = round(olt_power - feeder_loss, 2)
                trace_chain.append({
                    'step': 3,
                    'element_type': 'splice_closure',
                    'id': splice.id,
                    'code': splice.code,
                    'name': splice.name,
                    'power_dbm': splice_power,
                    'attenuation_db': 0.5,
                    'cumulative_loss_db': round(feeder_loss + 0.5, 2),
                    'coordinates': [splice.latitude, splice.longitude] if splice.latitude else None,
                })
                break

    # Buscar tramo distribution (Empalme -> Splitter)
    distribution_segments = CableSegment.objects.filter(
        segment_type='splice_to_splitter',
        to_splitter=splitter,
        is_active=True
    ).select_related('cable')

    if distribution_segments.exists():
        seg = distribution_segments.first()
        dist_loss = seg.attenuation_db or round(0.4 * (seg.length_m / 1000), 2)
        cumulative = trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0
        splitter_input_power = round(olt_power - cumulative - dist_loss, 2)
        trace_chain.append({
            'step': 4,
            'element_type': 'distribution_segment',
            'id': seg.id,
            'code': seg.cable.code if seg.cable else None,
            'name': f"Distribution {seg.cable.code if seg.cable else 'N/A'}",
            'fiber_numbers': seg.fiber_numbers,
            'length_m': seg.length_m,
            'power_dbm': splitter_input_power,
            'attenuation_db': dist_loss,
            'cumulative_loss_db': round(cumulative + dist_loss, 2),
            'coordinates': seg.route_as_list[-1] if seg.route_as_list else None,
            'route': seg.route_as_list,
        })
    else:
        splitter_input_power = round(
            olt_power - (trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0), 2
        )

    # Nodo: Splitter
    splitter_loss = splitter.insertion_loss_db if hasattr(splitter, 'insertion_loss_db') else 17.0
    splitter_output_power = round(splitter_input_power - splitter_loss, 2)
    trace_chain.append({
        'step': 5,
        'element_type': 'splitter',
        'id': splitter.id,
        'code': splitter.code,
        'name': splitter.name,
        'ratio': splitter.ratio,
        'power_input_dbm': splitter_input_power,
        'power_output_dbm': splitter_output_power,
        'attenuation_db': splitter_loss,
        'cumulative_loss_db': round(
            (trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + splitter_loss, 2
        ),
        'coordinates': [splitter.latitude, splitter.longitude] if splitter.latitude else None,
    })

    # Buscar tramo drop (Splitter -> Caja)
    drop_segments = CableSegment.objects.filter(
        segment_type='splitter_to_box',
        to_box=box,
        is_active=True
    ).select_related('cable')

    if drop_segments.exists():
        seg = drop_segments.first()
        drop_loss = seg.attenuation_db or round(0.4 * (seg.length_m / 1000), 2)
        cumulative = trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0
        box_input_power = round(splitter_output_power - drop_loss, 2)
        trace_chain.append({
            'step': 6,
            'element_type': 'drop_segment',
            'id': seg.id,
            'code': seg.cable.code if seg.cable else None,
            'name': f"Drop {seg.cable.code if seg.cable else 'N/A'}",
            'fiber_numbers': seg.fiber_numbers,
            'length_m': seg.length_m,
            'power_dbm': box_input_power,
            'attenuation_db': drop_loss,
            'cumulative_loss_db': round(cumulative + drop_loss, 2),
            'coordinates': seg.route_as_list[-1] if seg.route_as_list else None,
            'route': seg.route_as_list,
        })
    else:
        box_input_power = splitter_output_power

    # Nodo: Caja
    trace_chain.append({
        'step': 7,
        'element_type': 'fiber_box',
        'id': box.id,
        'code': box.code,
        'name': box.name,
        'power_dbm': round(box_input_power, 2),
        'attenuation_db': 0.3,
        'cumulative_loss_db': round(
            (trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + 0.3, 2
        ),
        'coordinates': [box.latitude, box.longitude] if box.latitude else None,
    })

    # Nodo final opcional: Cliente
    if client:
        trace_chain.append({
            'step': 8,
            'element_type': 'client',
            'id': client.id,
            'code': client.client_code,
            'name': client.full_name,
            'power_expected_dbm': round(box_input_power - 0.5, 2),
            'power_measured_dbm': client.optical_power_rx,
            'power_margin_db': round(
                client.optical_power_rx - (box_input_power - 0.5), 2
            ) if client.optical_power_rx else None,
            'attenuation_db': 0.5,
            'cumulative_loss_db': round(
                (trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + 0.5, 2
            ),
            'coordinates': [client.latitude, client.longitude] if client.latitude else None,
        })

    total_loss = round(trace_chain[-1]['cumulative_loss_db'], 2) if trace_chain else 0
    expected_end_power = round(olt_power - total_loss, 2)

    response_payload = {
        'trace': trace_chain,
        'summary': {
            'olt_output_dbm': olt_power,
            'total_attenuation_db': total_loss,
            'status': 'OK',
        }
    }

    if client:
        response_payload['client'] = {
            'id': client.id,
            'client_code': client.client_code,
            'full_name': client.full_name,
            'address': client.address,
            'status': client.status,
        }
        response_payload['summary']['expected_client_dbm'] = expected_end_power
        response_payload['summary']['measured_client_dbm'] = client.optical_power_rx
        response_payload['summary']['power_margin_db'] = (
            round(client.optical_power_rx - expected_end_power, 2)
            if client.optical_power_rx and expected_end_power else None
        )
        response_payload['summary']['status'] = (
            'OK' if client.optical_power_rx and expected_end_power
            and client.optical_power_rx > (expected_end_power - 3)
            else 'DEGRADED' if client.optical_power_rx and expected_end_power
            and client.optical_power_rx > (expected_end_power - 6)
            else 'CRITICAL'
        )
    else:
        response_payload['box'] = {
            'id': box.id,
            'code': box.code,
            'name': box.name,
            'address': box.address,
            'status': box.status,
        }
        response_payload['summary']['expected_box_dbm'] = expected_end_power
        response_payload['summary']['measured_box_dbm'] = box.measured_power_dbm
        response_payload['summary']['power_margin_db'] = (
            round(box.measured_power_dbm - expected_end_power, 2)
            if box.measured_power_dbm and expected_end_power else None
        )
        response_payload['summary']['status'] = (
            'OK' if box.measured_power_dbm and expected_end_power
            and box.measured_power_dbm > (expected_end_power - 3)
            else 'DEGRADED' if box.measured_power_dbm and expected_end_power
            and box.measured_power_dbm > (expected_end_power - 6)
            else 'CRITICAL'
        )

    return Response(response_payload)
