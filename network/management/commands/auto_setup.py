"""
Auto-setup para Railway - crea usuarios y ejecuta populate_cieza.
Se ejecuta en cada arranque pero solo crea datos si faltan.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from network.models import FiberCable

User = get_user_model()


class Command(BaseCommand):
    help = 'Auto-setup para Railway'

    def handle(self, *args, **options):
        # Crear usuarios
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@fibertruck.local', 'admin123', first_name='Administrador', role='admin')
            self.stdout.write(self.style.SUCCESS('Superusuario admin creado'))
        if not User.objects.filter(username='tecnico1').exists():
            User.objects.create_user('tecnico1', password='tecno123', first_name='Tecnico', last_name='Campo', role='technician')
            self.stdout.write(self.style.SUCCESS('Usuario tecnico1 creado'))
        if not User.objects.filter(username='supervisor1').exists():
            User.objects.create_user('supervisor1', password='super123', first_name='Supervisor', last_name='NOC', role='supervisor')
            self.stdout.write(self.style.SUCCESS('Usuario supervisor1 creado'))

        # Ejecutar populate_cieza si no hay cables (nuevos modelos v2)
        if not FiberCable.objects.exists():
            self.stdout.write(self.style.MIGRATE_HEADING('=== Ejecutando populate_cieza (v2) ==='))
            from django.core.management import call_command
            call_command('populate_cieza')
        else:
            count = FiberCable.objects.count()
            self.stdout.write(self.style.SUCCESS(f'Despliegue v2 ya existe: {count} cables'))
