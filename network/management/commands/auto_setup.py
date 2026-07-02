"""
Auto-setup para Railway - crea usuarios, despliegue FTTH y tickets de demo.
Se ejecuta en cada arranque pero solo crea datos si faltan.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from network.models import FiberCable

User = get_user_model()


class Command(BaseCommand):
    help = 'Auto-setup para Railway'

    def handle(self, *args, **options):
        # Crear superusuario si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin', 'admin@fibertruck.local', 'admin123',
                first_name='Administrador', role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario admin creado'))
        else:
            self.stdout.write(self.style.SUCCESS('Superusuario admin ya existe'))

        # Ejecutar populate_cieza si no hay cables (nuevos modelos v2)
        if not FiberCable.objects.exists():
            self.stdout.write(self.style.MIGRATE_HEADING('=== Ejecutando populate_cieza (v2) ==='))
            from django.core.management import call_command
            call_command('populate_cieza')
        else:
            count = FiberCable.objects.count()
            self.stdout.write(self.style.SUCCESS(f'Despliegue v2 ya existe: {count} cables'))

        # Crear tickets/perfiles de demo si no existen
        if not FiberCable.objects.exists():
            self.stdout.write(self.style.WARNING(
                'No hay despliegue FTTH; se omite seed de tickets hasta tener clientes.'
            ))
        else:
            from django.core.management import call_command
            call_command('seed_tickets')
