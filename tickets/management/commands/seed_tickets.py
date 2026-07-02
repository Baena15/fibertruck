"""
Seed de datos de prueba para FiberTrack Tickets.

Crea técnicos con perfiles, supervisor y tickets de ejemplo asociados
a clientes reales del despliegue FTTH de Cieza.
Es idempotente: solo crea datos si faltan.
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from network.models import Zone, Client, FiberBox
from tickets.models import Ticket, TechnicianProfile

User = get_user_model()

TECHNICIANS = [
    {
        'username': 'tecnico1',
        'password': 'tecno123',
        'first_name': 'Técnico',
        'last_name': 'La Era',
        'zone_code': 'Z-ERA',
        'skills': ['home', 'installation'],
        'max_workload': 5,
        'lat': 38.2375,
        'lng': -1.4195,
    },
    {
        'username': 'tecnico2',
        'password': 'tecno123',
        'first_name': 'Técnico',
        'last_name': 'San José',
        'zone_code': 'Z-SJOR',
        'skills': ['network', 'splicing'],
        'max_workload': 4,
        'lat': 38.2395,
        'lng': -1.4150,
    },
    {
        'username': 'tecnico3',
        'password': 'tecno123',
        'first_name': 'Técnico',
        'last_name': 'San Juan Bosco',
        'zone_code': 'Z-SJBO',
        'skills': ['home', 'splicing'],
        'max_workload': 6,
        'lat': 38.2420,
        'lng': -1.4140,
    },
]

SUPERVISOR = {
    'username': 'supervisor1',
    'password': 'super123',
    'first_name': 'Supervisor',
    'last_name': 'NOC',
}

TICKET_SAMPLES = [
    {
        'title': 'Corte total de servicio fibra',
        'description': 'Cliente reporta que la ONT no sincroniza desde esta mañana. Posible rotura de drop.',
        'ticket_type': 'home_fault',
        'priority': 'critical',
        'sla_hours': 4,
    },
    {
        'title': 'Velocidad inferior a la contratada',
        'description': 'Test de velocidad arroja 120 Mbps en tarifa 300 Mbps. Revisar nivel óptico.',
        'ticket_type': 'degradation',
        'priority': 'medium',
        'sla_hours': 24,
    },
    {
        'title': 'Instalación nueva FTTH',
        'description': 'Nuevo cliente solicita instalación. Cableado interior pendiente.',
        'ticket_type': 'installation',
        'priority': 'low',
        'sla_hours': 72,
    },
    {
        'title': 'Avería en caja CTO',
        'description': 'Varios clientes de la misma caja sin servicio. Posible splitter desconectado.',
        'ticket_type': 'network_fault',
        'priority': 'high',
        'sla_hours': 8,
    },
    {
        'title': 'Mantenimiento preventivo zona',
        'description': 'Revisión programada de conectores y niveles ópticos en caja.',
        'ticket_type': 'maintenance',
        'priority': 'low',
        'sla_hours': 168,
    },
    {
        'title': 'Intermitencias en conexión',
        'description': 'La conexión se corta varias veces al día. Revisar empalmes y potencia.',
        'ticket_type': 'degradation',
        'priority': 'medium',
        'sla_hours': 24,
    },
    {
        'title': 'Rotura de fibra drop por obra',
        'description': 'Obras en la acera han roto el cable drop. Urgente restablecimiento.',
        'ticket_type': 'home_fault',
        'priority': 'high',
        'sla_hours': 8,
    },
    {
        'title': 'ONT sin luz roja',
        'description': 'La luz LOS está encendida. Revisar trayecto hasta splitter.',
        'ticket_type': 'home_fault',
        'priority': 'high',
        'sla_hours': 8,
    },
    {
        'title': 'Cambio de ubicación ONT',
        'description': 'Cliente solicita traslado de la ONT a otra habitación.',
        'ticket_type': 'installation',
        'priority': 'low',
        'sla_hours': 72,
    },
    {
        'title': 'Splitter saturado',
        'description': 'Más usuarios reportan pérdida de servicio. Verificar splitter y puertos.',
        'ticket_type': 'network_fault',
        'priority': 'critical',
        'sla_hours': 4,
    },
    {
        'title': 'Potencia óptica fuera de rango',
        'description': 'Lectura de -28 dBm en cliente. Ajustar conectores o rehacer empalme.',
        'ticket_type': 'degradation',
        'priority': 'medium',
        'sla_hours': 24,
    },
    {
        'title': 'Revisión post-tormenta',
        'description': 'Después de la tormenta varios clientes reportan cortes. Inspección de red.',
        'ticket_type': 'network_fault',
        'priority': 'high',
        'sla_hours': 8,
    },
]


class Command(BaseCommand):
    help = 'Seed de tickets y perfiles de técnicos para FiberTrack'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra tickets existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            supervisor = self._get_or_create_supervisor()
            technicians = self._get_or_create_technicians()

            if options['reset']:
                deleted, _ = Ticket.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'Borrados {deleted} tickets'))

            if Ticket.objects.exists():
                self.stdout.write(self.style.SUCCESS(
                    f'Ya existen {Ticket.objects.count()} tickets. Saltando seed.'
                ))
                return

            self._create_sample_tickets(supervisor, technicians)

        self.stdout.write(self.style.SUCCESS(
            f'Seed completado: {Ticket.objects.count()} tickets, '
            f'{TechnicianProfile.objects.count()} perfiles de técnico.'
        ))

    def _get_or_create_supervisor(self):
        user, created = User.objects.get_or_create(
            username=SUPERVISOR['username'],
            defaults={
                'first_name': SUPERVISOR['first_name'],
                'last_name': SUPERVISOR['last_name'],
                'role': 'supervisor',
                'is_available': True,
            },
        )
        if created or not user.has_usable_password():
            user.set_password(SUPERVISOR['password'])
            user.save()
        self.stdout.write(self.style.SUCCESS(
            f'Supervisor {"creado" if created else "verificado"}: {user.username}'
        ))
        return user

    def _get_or_create_technicians(self):
        technicians = []
        for data in TECHNICIANS:
            zone = Zone.objects.filter(code=data['zone_code']).first()
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'technician',
                    'is_available': True,
                    'zone_assigned': zone,
                },
            )
            if created or not user.has_usable_password():
                user.set_password(data['password'])
                user.save()
            if zone and not user.zone_assigned:
                user.zone_assigned = zone
                user.save()

            profile, _ = TechnicianProfile.objects.get_or_create(
                user=user,
                defaults={
                    'skills': data['skills'],
                    'max_workload': data['max_workload'],
                    'current_latitude': data['lat'],
                    'current_longitude': data['lng'],
                    'is_available': True,
                },
            )
            # Actualizar por si cambiaron los datos de seed
            profile.skills = data['skills']
            profile.max_workload = data['max_workload']
            profile.current_latitude = data['lat']
            profile.current_longitude = data['lng']
            profile.is_available = True
            profile.save()

            technicians.append(user)
            self.stdout.write(self.style.SUCCESS(
                f'Técnico {"creado" if created else "verificado"}: {user.username} '
                f'({", ".join(profile.skills)})'
            ))
        return technicians

    def _create_sample_tickets(self, supervisor, technicians):
        clients = list(Client.objects.select_related('box__splitter', 'box__zone').all())
        if len(clients) < len(TICKET_SAMPLES):
            self.stdout.write(self.style.WARNING(
                f'Solo hay {len(clients)} clientes; se crearán tickets sobre los disponibles.'
            ))

        random.seed(42)
        random.shuffle(clients)

        active_statuses = ['open', 'assigned', 'in_transit', 'in_progress']
        pending_statuses = ['paused', 'needs_material', 'needs_client']
        terminal_statuses = ['resolved', 'closed']

        for idx, sample in enumerate(TICKET_SAMPLES):
            if idx >= len(clients):
                break
            client = clients[idx]
            box = client.box
            splitter = box.splitter if box else None

            # Distribuir estados para la demo
            if idx < 4:
                status = 'open'
            elif idx < 7:
                status = 'assigned'
            elif idx < 9:
                status = 'in_progress'
            elif idx < 11:
                status = 'resolved'
            else:
                status = random.choice(active_statuses + pending_statuses)

            ticket = Ticket.objects.create(
                title=sample['title'],
                description=sample['description'],
                ticket_type=sample['ticket_type'],
                priority=sample['priority'],
                status=status,
                client=client,
                affected_box=box,
                affected_splitter=splitter,
                address=client.address,
                latitude=client.latitude,
                longitude=client.longitude,
                coordinator=supervisor,
                created_by=supervisor,
                sla_hours=sample['sla_hours'],
            )

            if status in ('assigned', 'in_transit', 'in_progress', 'paused',
                          'needs_material', 'needs_client', 'resolved', 'closed'):
                tech = technicians[idx % len(technicians)]
                ticket.assigned_to = tech
                ticket.assigned_at = ticket.created_at
                ticket.save(update_fields=['assigned_to', 'assigned_at'])

            if status == 'in_progress':
                ticket.started_at = ticket.created_at
                ticket.save(update_fields=['started_at'])

            if status in ('resolved', 'closed'):
                tech = ticket.assigned_to or technicians[0]
                ticket.resolved_at = ticket.created_at
                ticket.solution_applied = 'Revisado y restablecido por el técnico.'
                ticket.optical_power_final = round(random.uniform(-18.0, -23.0), 1)
                if status == 'closed':
                    ticket.closed_at = ticket.created_at
                ticket.save(update_fields=[
                    'resolved_at', 'solution_applied',
                    'optical_power_final', 'closed_at',
                ])

            self.stdout.write(self.style.HTTP_INFO(
                f'  Ticket {ticket.code}: {ticket.title} [{ticket.get_status_display()}]'
            ))
