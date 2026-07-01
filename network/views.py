"""
FiberTruck API Views
CRUD + Algoritmo de diagnostico LCA (Fault Locator)
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views import IsAdmin, IsSupervisor, IsTechnician
from .models import OLT, Zone, Splitter, FiberBox, Client, FiberIncident
from .serializers import (
    OLTSerializer, ZoneSerializer, SplitterSerializer,
    FiberBoxSerializer, ClientSerializer, ClientListSerializer, FiberIncidentSerializer
)


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
