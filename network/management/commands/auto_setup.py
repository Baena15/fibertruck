"""
Auto-setup para Railway - ejecuta migrate + populate si la BD esta vacia.
Se ejecuta en cada arranque pero solo crea datos si no existen.
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from network.models import OLT, Zone, Splitter, FiberBox, Client

User = get_user_model()

ZONES_DATA = [
    {'name': 'La Era - La Asuncion', 'code': 'Z-ERA', 'description': 'Casco historico y zona suroeste de Cieza.', 'lat': 38.2375, 'lng': -1.4195, 'population': 6300},
    {'name': 'San Jose Obrero', 'code': 'Z-SJOR', 'description': 'Zona sureste de Cieza.', 'lat': 38.2395, 'lng': -1.4150, 'population': 7249},
    {'name': 'San Joaquin', 'code': 'Z-SJOA', 'description': 'Centro urbano de Cieza.', 'lat': 38.2390, 'lng': -1.4175, 'population': 5800},
    {'name': 'San Juan Bosco', 'code': 'Z-SJBO', 'description': 'Zona noreste, barrio moderno.', 'lat': 38.2420, 'lng': -1.4140, 'population': 9479},
    {'name': 'La Horta', 'code': 'Z-HORT', 'description': 'Zona norte y noroeste.', 'lat': 38.2440, 'lng': -1.4180, 'population': 4230},
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


class Command(BaseCommand):
    help = 'Auto-setup para Railway - crea datos solo si no existen'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@fibertruck.local', 'admin123', first_name='Administrador', role='admin')
            self.stdout.write(self.style.SUCCESS('Superusuario admin creado'))
        if not User.objects.filter(username='tecnico1').exists():
            User.objects.create_user('tecnico1', password='tecno123', first_name='Tecnico', last_name='Campo', role='technician')
            self.stdout.write(self.style.SUCCESS('Usuario tecnico1 creado'))
        if not User.objects.filter(username='supervisor1').exists():
            User.objects.create_user('supervisor1', password='super123', first_name='Supervisor', last_name='NOC', role='supervisor')
            self.stdout.write(self.style.SUCCESS('Usuario supervisor1 creado'))

        if OLT.objects.exists():
            self.stdout.write(self.style.SUCCESS('Despliegue FTTH ya existe, omitiendo'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING('=== Creando despliegue FTTH de Cieza ==='))

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

        self.stdout.write(self.style.SUCCESS(
            f'\nDespliegue creado: OLT=1, Zonas={len(zones_map)}, Splitters={len(splitters_map)}, Cajas={len(boxes_map)}, Clientes={total_clients}'
        ))
