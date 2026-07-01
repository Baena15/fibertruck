"""
FiberTruck API Views
CRUD + Algoritmo de diagnostico LCA (Fault Locator)
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from core.views import IsAdmin, IsSupervisor, IsTechnician
from .models import OLT, Zone, Splitter, FiberBox, Client, FiberIncident
from .serializers import (
    OLTSerializer, ZoneSerializer, SplitterSerializer,
    FiberBoxSerializer, ClientSerializer, ClientListSerializer, FiberIncidentSerializer
)


User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def setup_view(request):
    """
    Endpoint para inicializar la base de datos con el despliegue FTTH de Cieza.
    Solo funciona cuando la base de datos esta vacia (seguridad).
    Crea superusuario + ejecuta populate_cieza.
    """
    # Seguridad: solo funciona si no hay usuarios
    if User.objects.filter(is_superuser=True).exists():
        return Response({'error': 'Setup ya completado. Ya existen superusuarios.'}, status=403)

    try:
        # Crear superusuario
        admin = User.objects.create_superuser(
            username='admin', email='admin@fibertruck.local',
            password='admin123', first_name='Administrador', role='admin'
        )
        # Crear usuarios de prueba
        t1 = User.objects.create_user(
            username='tecnico1', password='tecno123',
            first_name='Tecnico', last_name='Campo', role='technician'
        )
        s1 = User.objects.create_user(
            username='supervisor1', password='super123',
            first_name='Supervisor', last_name='NOC', role='supervisor'
        )

        # Ejecutar populate (importar la logica del management command)
        from .management.commands.populate_cieza import (
            ZONES_DATA, OLT_DATA, SPLITTERS_DATA, BOXES_DATA,
            FIRST_NAMES, LAST_NAMES
        )
        import random

        olt, _ = OLT.objects.get_or_create(code=OLT_DATA['code'], defaults={
            'name': OLT_DATA['name'], 'address': OLT_DATA['address'],
            'latitude': OLT_DATA['lat'], 'longitude': OLT_DATA['lng'], 'max_ports': OLT_DATA['max_ports'],
        })

        zones_map = {}
        for zd in ZONES_DATA:
            zone, _ = Zone.objects.get_or_create(code=zd['code'], defaults={
                'name': zd['name'], 'description': zd['description'],
                'latitude': zd['lat'], 'longitude': zd['lng'], 'population_estimate': zd['population'],
            })
            zones_map[zd['code']] = zone

        splitters_map = {}
        for sd in SPLITTERS_DATA:
            zone = zones_map[sd['zone_code']]
            splitter, _ = Splitter.objects.get_or_create(code=sd['code'], defaults={
                'name': sd['name'], 'ratio': sd['ratio'], 'olt': olt, 'zone': zone,
                'input_port_olt': sd['port'], 'latitude': sd['lat'], 'longitude': sd['lng'],
                'address': f"Cerca de {sd['name']}",
            })
            splitters_map[sd['code']] = splitter

        boxes_map = {}
        for bd in BOXES_DATA:
            zone = zones_map[bd['zone']]
            splitter = splitters_map[bd['splitter']]
            box, _ = FiberBox.objects.get_or_create(code=bd['code'], defaults={
                'name': bd['name'], 'box_type': 'CTO', 'splitter': splitter, 'zone': zone,
                'splitter_port': bd['port'], 'max_capacity': 16,
                'latitude': bd['lat'], 'longitude': bd['lng'], 'address': bd['address'],
            })
            boxes_map[bd['code']] = box

        random.seed(42)
        name_idx = 0
        total_clients = 0
        for box_code, box in boxes_map.items():
            num_clients = random.randint(4, 7)
            for port in range(1, num_clients + 1):
                fn = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
                ln1 = LAST_NAMES[name_idx % len(LAST_NAMES)]
                ln2 = LAST_NAMES[(name_idx + 1) % len(LAST_NAMES)]
                Client.objects.get_or_create(client_code=f'CLI-{total_clients + 1:04d}', defaults={
                    'full_name': f'{fn} {ln1} {ln2}', 'address': f'{box.address} (Piso {port})',
                    'latitude': box.latitude + random.uniform(-0.0005, 0.0005),
                    'longitude': box.longitude + random.uniform(-0.0005, 0.0005),
                    'box': box, 'box_port': port, 'olt_port': box.splitter.input_port_olt,
                    'status': 'active', 'optical_power_rx': round(random.uniform(-15.0, -24.0), 1),
                    'optical_power_tx': round(random.uniform(0.5, 4.0), 1),
                })
                name_idx += 1
                total_clients += 1

        return Response({
            'success': True,
            'message': 'FiberTruck inicializado correctamente',
            'users_created': [
                {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
                {'username': 'tecnico1', 'password': 'tecno123', 'role': 'technician'},
                {'username': 'supervisor1', 'password': 'super123', 'role': 'supervisor'},
            ],
            'deployment': {
                'olt': 1, 'zones': len(zones_map), 'splitters': len(splitters_map),
                'boxes': len(boxes_map), 'clients': total_clients,
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


class OLTViewSet(viewsets.ModelViewSet):
    queryset = OLT.objects.all()
    serializer_class = OLTSerializer
    permission_classes = [IsSupervisor]


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsSupervisor()]


class SplitterViewSet(viewsets.ModelViewSet):
    queryset = Splitter.objects.all()
    serializer_class = SplitterSerializer
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
