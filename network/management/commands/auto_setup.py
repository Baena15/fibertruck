"""
Auto-setup para Railway - crea usuarios + ejecuta populate_cieza si no hay datos.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from network.models import OLT

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

        # Ejecutar populate_cieza si no hay OLT
        if not OLT.objects.exists():
            self.stdout.write(self.style.MIGRATE_HEADING('=== Ejecutando populate_cieza ==='))
            from django.core.management import call_command
            call_command('populate_cieza')
        else:
            self.stdout.write(self.style.SUCCESS('Despliegue ya existe'))
