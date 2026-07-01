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
from core.views import IsAdmin, IsSupervisor, IsTechnician
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
    Endpoint para inicializar la base de datos con el despliegue FTTH de Cieza.
    Solo funciona cuando la base de datos esta vacia (seguridad).
    """
    if User.objects.filter(is_superuser=True).exists():
        return Response({'error': 'Setup ya completado.'}, status=403)

    try:
        # Crear superusuario y usuarios de prueba
        User.objects.create_superuser('admin', 'admin@fibertruck.local', 'admin123', first_name='Administrador', role='admin')
        User.objects.create_user('tecnico1', password='tecno123', first_name='Tecnico', last_name='Campo', role='technician')
        User.objects.create_user('supervisor1', password='super123', first_name='Supervisor', last_name='NOC', role='supervisor')

        # Crear despliegue FTTH de Cieza
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
            'users': [
                {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
                {'username': 'tecnico1', 'password': 'tecno123', 'role': 'technician'},
                {'username': 'supervisor1', 'password': 'super123', 'role': 'supervisor'},
            ],
            'deployment': {'olt': 1, 'zones': len(zones_map), 'splitters': len(splitters_map), 'boxes': len(boxes_map), 'clients': total_clients},
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def diagnose_v2(request):
    """
    Diagnostico avanzado FTTH v2 con analisis de tramos y potencia.

    POST /api/diagnose/v2/
    Body: {"box_code": "CTO-023", "affected_client_ids": [45,46,47]}

    Devuelve:
    {
        "severity": "critical|high|medium|low",
        "confidence": 95,
        "affected_segment": {...},
        "power_analysis": {"expected_dbm": -17.5, "measured_dbm": -45.0, "loss_db": 27.5, "status": "CORTE TOTAL"},
        "fault_location": {"description": "...", "coordinates": [lat,lng], "address": "..."},
        "recommended_action": "paso a paso...",
        "affected_clients": [...],
        "affected_route": [[lat,lng], ...]
    }
    """
    box_code = request.data.get('box_code', '')
    affected_client_ids = request.data.get('affected_client_ids', [])

    if not box_code:
        return Response({'error': 'box_code es requerido'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        box = FiberBox.objects.select_related('splitter', 'splitter__olt', 'zone').get(code__iexact=box_code, is_active=True)
    except FiberBox.DoesNotExist:
        return Response({'error': f'Caja {box_code} no encontrada'}, status=status.HTTP_404_NOT_FOUND)

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

    # 10. Clientes afectados serializados
    clients_data = ClientListSerializer(affected_clients, many=True).data

    return Response({
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
        'affected_clients': clients_data,
        'affected_route': affected_route,
        'affected_count': affected_count,
        'total_affected_in_splitter': total_affected_in_splitter,
        'boxes_affected_in_splitter': len(boxes_with_issues),
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
    Trace de ruta de fibra desde OLT hasta cliente.
    GET /api/fiber-trace/?client_id=45

    Devuelve la cadena completa: OLT -> Feeder(fibra N) -> Empalme -> Distribution(fibra N) -> Splitter -> Drop(fibra N) -> Caja -> Cliente
    Con potencias en cada nodo y atenuaciones.
    """
    client_id = request.query_params.get('client_id')
    if not client_id:
        return Response({'error': 'client_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Client.objects.select_related('box', 'box__splitter', 'box__splitter__olt', 'box__zone').get(id=client_id, is_active=True)
    except Client.DoesNotExist:
        return Response({'error': f'Cliente {client_id} no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    box = client.box
    splitter = box.splitter
    olt = splitter.olt

    # 1-2. Construir la cadena: Cliente -> Caja -> Splitter -> Empalme -> OLT
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

    # Buscar tramo feeder (OLT -> Empalme)
    feeder_segments = CableSegment.objects.filter(
        segment_type='olt_to_splice',
        is_active=True
    ).select_related('cable')

    splice = None
    for seg in feeder_segments:
        if hasattr(seg, 'to_splice') and seg.to_splice:
            splice = seg.to_splice
            feeder_loss = seg.attenuation_db if seg.attenuation_db else round(0.4 * (seg.length_m / 1000), 2)
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
            # Nodo: Empalme
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
        dist_loss = seg.attenuation_db if seg.attenuation_db else round(0.4 * (seg.length_m / 1000), 2)
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
        splitter_input_power = round(olt_power - (trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0), 2)

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
        'cumulative_loss_db': round((trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + splitter_loss, 2),
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
        drop_loss = seg.attenuation_db if seg.attenuation_db else round(0.4 * (seg.length_m / 1000), 2)
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
        'cumulative_loss_db': round((trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + 0.3, 2),
        'coordinates': [box.latitude, box.longitude] if box.latitude else None,
    })

    # Nodo final: Cliente
    trace_chain.append({
        'step': 8,
        'element_type': 'client',
        'id': client.id,
        'code': client.client_code,
        'name': client.full_name,
        'power_expected_dbm': round(box_input_power - 0.5, 2),
        'power_measured_dbm': client.optical_power_rx,
        'power_margin_db': round(client.optical_power_rx - (box_input_power - 0.5), 2) if client.optical_power_rx else None,
        'attenuation_db': 0.5,
        'cumulative_loss_db': round((trace_chain[-1]['cumulative_loss_db'] if trace_chain else 0) + 0.5, 2),
        'coordinates': [client.latitude, client.longitude] if client.latitude else None,
    })

    # 5. Calcular potencia en cada nodo y resumen
    expected_client_power = round(olt_power - trace_chain[-1]['cumulative_loss_db'], 2) if trace_chain else None

    return Response({
        'client': {
            'id': client.id,
            'client_code': client.client_code,
            'full_name': client.full_name,
            'address': client.address,
            'status': client.status,
        },
        'trace': trace_chain,
        'summary': {
            'olt_output_dbm': olt_power,
            'expected_client_dbm': expected_client_power,
            'measured_client_dbm': client.optical_power_rx,
            'total_attenuation_db': round(trace_chain[-1]['cumulative_loss_db'], 2) if trace_chain else 0,
            'power_margin_db': round(client.optical_power_rx - expected_client_power, 2) if client.optical_power_rx and expected_client_power else None,
            'status': 'OK' if client.optical_power_rx and expected_client_power and client.optical_power_rx > (expected_client_power - 3) else 'DEGRADED' if client.optical_power_rx and expected_client_power and client.optical_power_rx > (expected_client_power - 6) else 'CRITICAL',
        }
    })
