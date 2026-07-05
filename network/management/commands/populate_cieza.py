"""
FiberTruck - Comando para poblar la base de datos con datos de INGENIERIA REAL
y geográficamente extensa de un despliegue FTTH en Cieza, Murcia.

Topologia completa (version 2.0):
  OLT -> Cable Feeder (288f) -> SpliceClosure (16) -> Cable Distribution (144f)
       -> Splitter (1x32) -> Cable Drop (12f) -> FiberBox/CTO (~96) -> Client (~576)

Calculos opticos basados en:
  - Atenuacion fibra monomodo G.652D: 0.35 dB/km @ 1490nm
  - Atenuacion conector: 0.5 dB cada uno
  - Atenuacion empalme de fusion: 0.1 dB cada uno
  - Atenuacion splitter 1x32: 16.5 dB (tipico)
  - OLT salida: +3.0 dBm
"""
import json
import math
import os
import random
import time

import requests
from django.core.management.base import BaseCommand
from network.models import (
    OLT, Zone, FiberCable, SpliceClosure, Splitter, FiberBox,
    Client, FiberAssignment, CableSegment,
)

# ============================================================
# CONSTANTES DE INGENIERIA OPTICA
# ============================================================
ATT_FIBER_DB_KM = 0.35       # dB/km @ 1490nm (fibra monomodo G.652D)
ATT_CONNECTOR_DB = 0.5       # dB por conector
ATT_SPLICE_DB = 0.1          # dB por empalme de fusion
ATT_SPLITTER_1X32_DB = 16.5  # dB de insercion splitter 1x32
OLT_OUTPUT_POWER_DBM = 3.0   # dBm de salida del OLT

FIRST_NAMES = [
    'Antonio', 'Maria', 'Jose', 'Carmen', 'Francisco', 'Ana', 'Manuel', 'Isabel',
    'David', 'Laura', 'Juan', 'Pilar', 'Javier', 'Dolores', 'Daniel', 'Teresa',
    'Pedro', 'Rosa', 'Alejandro', 'Cristina', 'Miguel', 'Patricia', 'Rafael', 'Sofia',
    'Fernando', 'Lucia', 'Luis', 'Martina', 'Pablo', 'Valentina', 'Sergio', 'Julia',
    'Andres', 'Paula', 'Jorge', 'Emma', 'Alberto', 'Marta', 'Diego', 'Noa',
    'Carlos', 'Elena', 'Ramon', 'Inmaculada', 'Ruben', 'Mercedes', 'Victor', 'Nuria',
    'Jesus', 'Angela', 'Gabriel', 'Montserrat', 'Adrian', 'Raquel', 'Alvaro', 'Beatriz',
    'Enrique', 'Rocio', 'Mario', 'Claudia', 'Oscar', 'Esther', 'Marcos', 'Sara',
    'Ivan', 'Catherine', 'Nicolas', 'Alba', 'Guillermo', 'Lorena', 'Francisco Javier',
    'Belen', 'Hugo', 'Natalia', 'Mariano', 'Silvia', 'Joan', 'Carolina', 'Tomas',
    'Eva', 'Ignacio', 'Virginia', 'Eduardo', 'Ines', 'German', 'Lidia', 'Andrea',
    'Salvador', 'Monica', 'Santiago', 'Aurora', 'Felipe', 'Marina', 'Vicente', 'Gloria',
    'Alex', 'Celia', 'Julio', 'Aranzazu', 'Adam', 'Nerea', 'Eric', 'Naiara',
    'Ismael', 'Yolanda', 'Erik', 'Olga', 'Iker', 'Nieves', 'Marc', 'Nadia',
    'Pol', 'Montse', 'Biel', 'Ainhoa', 'Jan', 'Triana', 'Bruno', 'Elia',
    'Unai', 'India', 'Arnau', 'Jimena', 'Luka', 'Ainara', 'Pau', 'Ainoha',
    'Ander', 'Aiala', 'Martin', 'Naia', 'Nil', 'Zoe', 'Aleix', 'Cayetana',
    'Teo', 'Berta', 'Mikel', 'Candela', 'Izan', 'Diana', 'Alonso', 'Africa',
    'Enzo', 'Paloma', 'Oier', 'Vega', 'Aday', 'Iria', 'Asier', 'Jara',
    'Gorka', 'Mireia', 'Eneko', 'Nahia', 'Jon', 'Irati', 'Imanol', 'Laia',
    'Koldo', 'Amaia', 'Xabier', 'Maialen', 'Aitor', 'Elixane', 'Ibai', 'Nagore',
]
LAST_NAMES = [
    'Garcia', 'Martinez', 'Lopez', 'Sanchez', 'Rodriguez', 'Perez', 'Fernandez',
    'Gonzalez', 'Gomez', 'Ruiz', 'Alvarez', 'Jimenez', 'Moreno', 'Romero',
    'Hernandez', 'Diaz', 'Muñoz', 'Serrano', 'Iglesias', 'Medina', 'Cieza',
    'Segura', 'Vega', 'Murcia', 'Rico', 'Blanco', 'Castillo', 'Torres',
    'Aguilar', 'Rivera', 'Nieto', 'Mendez', 'Guerrero', 'Contreras', 'Molina',
    'Soto', 'Delgado', 'Marquez', 'Cortes', 'Navarro', 'Dominguez', 'Ortega',
    'Reyes', 'Vargas', 'Ramos', 'Campos', 'Santos', 'Cabrera', 'Mora',
    'Leon', 'Rubio', 'Arias', 'Carmona', 'Espinosa', 'Herrera', 'Fuentes',
    'Camacho', 'Pascual', 'Velasco', 'Reina', 'Miranda', 'Padilla', 'Soler',
    'Esteban', 'Bravo', 'Morales', 'Vila', 'Salgado', 'Cuesta', 'Aguilera',
    'Macias', 'Maldonado', 'Prieto', 'Roldan', 'Pacheco', 'Cano', 'Villar',
    'Pons', 'Aranda', 'Quintero', 'Pardo', 'Lozano', 'Cordero', 'Ballesteros',
    'Barragan', 'Casado', 'Varela', 'Luna', 'Valero', 'Rovira', 'Cuenca',
    'Oliva', 'Gisbert', 'Salcedo', 'Bernal', 'Ponsa', 'Ayala', 'Caro',
    'Llanos', 'Perales', 'Olmo', 'Tortosa', 'Montero', 'Ojeda', 'Valverde',
]

STREETS_BY_ZONE = {
    'Z-ERA': [
        'Calle Real', 'Calle Colon', 'Calle Espinosa', 'Calle Mayor',
        'Plaza de la Constitucion', 'Calle del Mediterraneo', 'Calle Virgen de la Asuncion',
        'Calle San Sebastian', 'Calle Castillo', 'Calle Nueva',
    ],
    'Z-SJOR': [
        'Avenida Juan Carlos I', 'Calle Murcia', 'Calle Albacete', 'Calle Granada',
        'Calle Jaen', 'Calle Generos de Punto', 'Avenida de Murcia',
        'Calle Rambla del Realejo', 'Calle Cartagena', 'Calle Almeria',
    ],
    'Z-SJOA': [
        'Plaza de España', 'Calle Marques de Camachos', 'Calle Fray Pascual Salmeron',
        'Calle del Mercado', 'Avenida de Murcia', 'Calle del Carmen',
        'Calle San Joaquin', 'Calle Iglesia', 'Calle Horno', 'Callejon de la Feria',
    ],
    'Z-SJBO': [
        'Avenida de Murcia', 'Calle Pintor Villodres', 'Calle Molino de Papel',
        'Calle Federico Garcia Lorca', 'Calle Beniel', 'Avenida de Alcantarilla',
        'Calle Urano', 'Calle Orion', 'Calle Jupiter', 'Calle Saturno',
    ],
    'Z-HORT': [
        'Calle Santiago', 'Calle Rio Segura', 'Calle San Cristobal', 'Camino del Cabezo',
        'Calle Industrial', 'Calle Poligono', 'Calle de la Fuensantilla',
        'Calle Los Olmos', 'Calle El Romeral', 'Calle La Horta',
    ],
    'Z-CARM': [
        'Calle del Carmen', 'Calle San Pedro', 'Calle Concejo', 'Calle Angustias',
        'Plaza del Carmen', 'Callejon de las Monjas', 'Calle Veracruz',
        'Calle Estacion', 'Calle del Puente', 'Calle Ribera',
    ],
    'Z-CONC': [
        'Calle Concejo', 'Calle San Pedro', 'Callejon del Concejo', 'Calle Alta',
        'Calle Baja', 'Plaza de la Iglesia', 'Calle Eras', 'Calle Horno Viejo',
        'Calle Camino de la Finca', 'Calle Loma',
    ],
    'Z-ESTA': [
        'Calle de la Estacion', 'Avenida del Ferrocarril', 'Calle Alfonso X',
        'Calle Ronda Norte', 'Calle del Angosto', 'Calle Molino',
        'Calle Acequia', 'Calle Camino de Ricote', 'Calle Barranco',
    ],
}

BOX_TYPE_BY_DENSITY = ['CTO', 'CTO', 'CTO', 'CTO-MINI', 'FAT']


def att_fiber(length_km):
    """Atenuacion por fibra: 0.35 dB/km"""
    return ATT_FIBER_DB_KM * length_km


def att_connectors(n=2):
    """Atenuacion por conectores: 0.5 dB cada uno"""
    return ATT_CONNECTOR_DB * n


def att_splices(n=1):
    """Atenuacion por empalmes: 0.1 dB cada uno"""
    return ATT_SPLICE_DB * n


def calc_attenuation(fiber_km, connectors=2, splices=1):
    """Atenuacion total de un tramo."""
    return att_fiber(fiber_km) + att_connectors(connectors) + att_splices(splices)


def calc_power_to_splice(olt_power, feeder_km):
    """Potencia en el empalme (despues del cable feeder)."""
    att = calc_attenuation(feeder_km, connectors=2, splices=1)
    return round(olt_power - att, 2)


def calc_power_to_splitter(olt_power, feeder_km, dist_km):
    """Potencia en el splitter (entrada, antes de la perdida del splitter)."""
    att = calc_attenuation(feeder_km, connectors=2, splices=1)
    att += calc_attenuation(dist_km, connectors=2, splices=1)
    return round(olt_power - att, 2)


def calc_power_at_box(olt_power, feeder_km, dist_km, drop_km):
    """Potencia esperada en la caja CTO (despues del splitter y drop)."""
    att = calc_attenuation(feeder_km, connectors=2, splices=1)
    att += calc_attenuation(dist_km, connectors=2, splices=1)
    att += ATT_SPLITTER_1X32_DB
    att += calc_attenuation(drop_km, connectors=2, splices=1)
    return round(olt_power - att, 2)


def calc_power_at_client(olt_power, feeder_km, dist_km, drop_km, client_drop_km=0.025):
    """Potencia esperada en la ONT del cliente (incluye drop final del cliente)."""
    att = calc_attenuation(feeder_km, connectors=2, splices=1)
    att += calc_attenuation(dist_km, connectors=2, splices=1)
    att += ATT_SPLITTER_1X32_DB
    att += calc_attenuation(drop_km, connectors=2, splices=1)
    att += calc_attenuation(client_drop_km, connectors=2, splices=1)
    return round(olt_power - att, 2)


def haversine_m(lat1, lng1, lat2, lng2):
    """Distancia en metros entre dos coordenadas GPS."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def route_length_m(coords):
    """Longitud total de una ruta en metros."""
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return total


# ============================================================
# ROUTING POR CALLES REALES (OSRM + cache local)
# ============================================================
ROUTE_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'cieza_routes_cache.json'
)


def _load_route_cache():
    """Carga cache de rutas OSRM desde disco."""
    if os.path.exists(ROUTE_CACHE_FILE):
        try:
            with open(ROUTE_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_route_cache(cache):
    """Guarda cache de rutas OSRM en disco."""
    try:
        with open(ROUTE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
    except IOError:
        pass


def _route_cache_key(start_lat, start_lng, end_lat, end_lng):
    """Clave de cache redondeada a 5 decimales (~1m de precision)."""
    return (
        f"{round(start_lat, 5)},{round(start_lng, 5)};"
        f"{round(end_lat, 5)},{round(end_lng, 5)}"
    )


def get_osrm_route(start_lat, start_lng, end_lat, end_lng, cache=None, delay_ms=100):
    """
    Obtiene una ruta por calles reales usando OSRM.
    Usa cache local para evitar peticiones repetidas y rate limits.
    Si falla, retorna None para que el caller use el generador procedural.
    """
    if cache is None:
        cache = _load_route_cache()

    key = _route_cache_key(start_lat, start_lng, end_lat, end_lng)
    if key in cache:
        return cache[key]

    # OSRM public API (driving profile es suficiente para calles urbanas)
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_lng},{start_lat};{end_lng},{end_lat}"
        f"?overview=full&geometries=geojson"
    )

    try:
        # Pausa para no saturar la API publica
        time.sleep(delay_ms / 1000.0)
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 'Ok' or not data.get('routes'):
            return None

        # OSRM devuelve [lng, lat]; convertimos a [lat, lng]
        coords = [
            [round(point[1], 6), round(point[0], 6)]
            for point in data['routes'][0]['geometry']['coordinates']
        ]
        if len(coords) < 2:
            return None

        cache[key] = coords
        _save_route_cache(cache)
        return coords
    except Exception:
        return None


def generate_route(start_lat, start_lng, end_lat, end_lng, num_points=None, urban_factor=0.15, osrm_cache=None):
    """
    Genera coordenadas intermedias realistas entre dos puntos.

    Si se proporciona osrm_cache, intenta obtener una ruta por calles reales
    usando OSRM. Si OSRM no esta disponible o falla, genera una ruta procedural.

    Crea trayectorias con mas vertices para que parezcan cables desplegados
    por calles y aceras. Añade desvios perpendiculares para romper la linea recta.
    urban_factor: maxima desviacion perpendicular como fraccion de la distancia.
    """
    # Intentar routing por calles reales
    if osrm_cache is not None:
        osrm_route = get_osrm_route(
            start_lat, start_lng, end_lat, end_lng, cache=osrm_cache
        )
        if osrm_route:
            # Añadir ligero ruido para que cables paralelos no se solapen exactamente
            noisy_route = [osrm_route[0]]
            for pt in osrm_route[1:-1]:
                noisy_route.append([
                    round(pt[0] + random.uniform(-0.00001, 0.00001), 6),
                    round(pt[1] + random.uniform(-0.00001, 0.00001), 6),
                ])
            noisy_route.append(osrm_route[-1])
            return noisy_route

    distance_m = haversine_m(start_lat, start_lng, end_lat, end_lng)

    # Un punto cada ~60 m, minimo 3, maximo 16
    if num_points is None:
        num_points = max(3, min(16, int(distance_m / 60)))

    # Punto intermedio desplazado perpendicularmente para simular rodear manzana
    mid_lat = (start_lat + end_lat) / 2.0
    mid_lng = (start_lng + end_lng) / 2.0
    if distance_m > 80:
        dx = end_lng - start_lng
        dy = end_lat - start_lat
        norm = math.sqrt(dx ** 2 + dy ** 2) or 1.0
        offset_m = min(random.uniform(20, 60), distance_m * urban_factor)
        offset_lat = (-dx / norm) * (offset_m / 111000)
        offset_lng = (dy / norm) * (offset_m / (111000 * math.cos(math.radians(mid_lat))))
        mid_lat += offset_lat
        mid_lng += offset_lng

    def interpolate(p1, p2, steps):
        pts = []
        for i in range(1, steps + 1):
            frac = i / steps
            lat = p1[0] + (p2[0] - p1[0]) * frac
            lng = p1[1] + (p2[1] - p1[1]) * frac
            pts.append([lat, lng])
        return pts

    route = [[start_lat, start_lng]]
    route.extend(interpolate(route[-1], [mid_lat, mid_lng], num_points // 2 + 1))
    route.extend(interpolate(route[-1], [end_lat, end_lng], num_points // 2 + 1))

    # Añadir ruido realista (hasta ~6 m) a puntos intermedios
    final_route = [route[0]]
    for pt in route[1:-1]:
        noise_lat = random.uniform(-0.000055, 0.000055)
        noise_lng = random.uniform(-0.000055, 0.000055)
        final_route.append([round(pt[0] + noise_lat, 6), round(pt[1] + noise_lng, 6)])
    final_route.append(route[-1])

    return final_route


# ============================================================
# DATOS DEL DESPLIEGUE REAL DE CIEZA
# ============================================================
# Centro aproximado de Cieza y zonas con cobertura completa.
# Las zonas estan distribuidas por todo el casco urbano para evitar
# la concentracion del despliegue anterior.
ZONES_DATA = [
    {
        'code': 'Z-ERA',
        'name': 'La Era - La Asuncion',
        'lat': 38.2370,
        'lng': -1.4205,
        'radius_m': 650,
        'pop': 6300,
        'desc': 'Casco historico y zona suroeste. Barrio mas antiguo con calles estrechas y alta densidad de viviendas.',
        'splice_count': 2,
        'splitters_per_splice': 2,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (4, 8),
    },
    {
        'code': 'Z-SJOR',
        'name': 'San Jose Obrero',
        'lat': 38.2385,
        'lng': -1.4135,
        'radius_m': 700,
        'pop': 7249,
        'desc': 'Zona sureste. Alta densidad. Atravesado por la Rambla del Realejo y avenida Juan Carlos I.',
        'splice_count': 2,
        'splitters_per_splice': 2,
        'boxes_per_splitter': (4, 6),
        'clients_per_box': (5, 8),
    },
    {
        'code': 'Z-SJOA',
        'name': 'San Joaquin',
        'lat': 38.2393,
        'lng': -1.4178,
        'radius_m': 600,
        'pop': 5800,
        'desc': 'Centro urbano. Zona comercial. Calles anchas y edificios de 4-6 plantas.',
        'splice_count': 2,
        'splitters_per_splice': 1,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (4, 7),
    },
    {
        'code': 'Z-SJBO',
        'name': 'San Juan Bosco',
        'lat': 38.2430,
        'lng': -1.4145,
        'radius_m': 800,
        'pop': 9479,
        'desc': 'Zona noreste, barrio moderno. Edificios de 10-20 años de antigüedad y amplias avenidas.',
        'splice_count': 3,
        'splitters_per_splice': 2,
        'boxes_per_splitter': (4, 6),
        'clients_per_box': (5, 9),
    },
    {
        'code': 'Z-HORT',
        'name': 'La Horta',
        'lat': 38.2455,
        'lng': -1.4190,
        'radius_m': 750,
        'pop': 4230,
        'desc': 'Zona norte. Mezcla de viviendas unifamiliares y zona suburbanizada junto al Cabezo.',
        'splice_count': 2,
        'splitters_per_splice': 1,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (3, 6),
    },
    {
        'code': 'Z-CARM',
        'name': 'Barrio del Carmen',
        'lat': 38.2410,
        'lng': -1.4160,
        'radius_m': 550,
        'pop': 5100,
        'desc': 'Zona este, entre el casco antiguo y San Juan Bosco. Calles medias y plazas.',
        'splice_count': 2,
        'splitters_per_splice': 1,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (4, 7),
    },
    {
        'code': 'Z-CONC',
        'name': 'El Concejo - San Pedro',
        'lat': 38.2360,
        'lng': -1.4165,
        'radius_m': 600,
        'pop': 4600,
        'desc': 'Zona sureste del casco historico, cerca del Concejo y San Pedro. Calles tradicionales.',
        'splice_count': 2,
        'splitters_per_splice': 1,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (4, 7),
    },
    {
        'code': 'Z-ESTA',
        'name': 'Estacion - El Angosto',
        'lat': 38.2415,
        'lng': -1.4240,
        'radius_m': 700,
        'pop': 3800,
        'desc': 'Zona oeste junto a la estacion de tren y el Angosto. Viviendas en franjas paralelas al ferrocarril.',
        'splice_count': 2,
        'splitters_per_splice': 1,
        'boxes_per_splitter': (3, 5),
        'clients_per_box': (3, 6),
    },
]

# ============================================================
# FUNCIONES DE GENERACION PROCEDURAL
# ============================================================
def random_point_in_radius(center_lat, center_lng, radius_m):
    """Genera un punto aleatorio uniforme dentro de un circulo."""
    r = radius_m * math.sqrt(random.uniform(0, 1))
    theta = random.uniform(0, 2 * math.pi)
    lat_offset = (r * math.sin(theta)) / 111000
    lng_offset = (r * math.cos(theta)) / (111000 * math.cos(math.radians(center_lat)))
    return center_lat + lat_offset, center_lng + lng_offset


def random_point_near_box(box_lat, box_lng, max_distance_m=50):
    """Genera un punto cercano a una caja (cliente)."""
    return random_point_in_radius(box_lat, box_lng, max_distance_m)


def pick_client_status():
    """Distribucion realista de estados de clientes."""
    return random.choices(
        ['active', 'affected', 'degraded', 'installing', 'disconnected'],
        weights=[70, 10, 10, 5, 5]
    )[0]


def pick_box_status():
    """Mayoria de cajas activas, algunas en mantenimiento o averia."""
    return random.choices(
        ['active', 'warning', 'fault', 'maintenance', 'inactive'],
        weights=[85, 7, 4, 3, 1]
    )[0]


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))



class Command(BaseCommand):
    help = 'Poblar despliegue FTTH de Cieza con datos de ingenieria real y cobertura completa'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.box_counter = 0
        self.client_counter = 0
        self.global_splitter_port = 0
        self.osrm_cache = _load_route_cache()

    def handle(self, *args, **options):
        random.seed(42)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== FiberTruck: Despliegue FTTH Real y Extenso de Cieza, Murcia ==='))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '    OLT(1) -> Feeder -> SpliceClosure -> Distribution'
            ' -> Splitter(1x32) -> Drop -> CTO(~96) -> Clientes(~576)'))
        self.stdout.write('')

        # Idempotencia: salir si ya existe un OLT
        if OLT.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Ya existe un despliegue. Borra la base de datos para regenerarlo.'))
            return

        # ============================================================
        # 1. CREAR OLT
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 1. Creando OLT ---'))
        olt = OLT.objects.create(
            code='OLT-CIEZA-01',
            name='OLT Central Cieza',
            address='Calle Mayor, 45 - Centro de Datos Municipal, Cieza (Murcia)',
            latitude=38.2390,
            longitude=-1.4175,
            max_ports=16,
            output_power_dbm=OLT_OUTPUT_POWER_DBM,
            splitter_ratio='1x32',
        )
        self.stdout.write(f'  OLT: {olt} | Potencia: +{olt.output_power_dbm} dBm')

        # ============================================================
        # 2. CREAR ZONAS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 2. Creando Zonas ---'))
        zones_map = {}
        for zd in ZONES_DATA:
            zone = Zone.objects.create(
                code=zd['code'],
                name=zd['name'],
                description=zd['desc'],
                latitude=zd['lat'],
                longitude=zd['lng'],
                population_estimate=zd['pop'],
            )
            zones_map[zd['code']] = zone
            self.stdout.write(f'  Zona: {zone} | radio {zd["radius_m"]}m')

        # ============================================================
        # 3-9. CREAR INFRAESTRUCTURA POR ZONA (procedural)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO(
            '--- 3-9. Generando feeders, empalmes, splitters, cajas y clientes ---'))

        # Mapas para resumen
        all_splices = []
        all_splitters = []
        all_boxes = []
        all_clients = []
        feeder_map = {}     # zone_code -> [cables]
        dist_map = {}       # splice -> [cables]
        drop_box_map = {}   # box -> cable
        drop_client_map = {}  # client -> cable

        olt_port = 1

        for zd in ZONES_DATA:
            zone = zones_map[zd['code']]
            zone_prefix = zd['code'].split('-')[1]
            self.stdout.write(self.style.HTTP_INFO(
                f'  Zona {zd["code"]} ({zd["name"]}):'))

            feeder_map[zone.code] = []
            splices_in_zone = []

            for s_idx in range(1, zd['splice_count'] + 1):
                # Empalme ubicado en subarea de la zona
                angle = (2 * math.pi / zd['splice_count']) * (s_idx - 1) + random.uniform(-0.3, 0.3)
                dist = random.uniform(zd['radius_m'] * 0.25, zd['radius_m'] * 0.55)
                splice_lat = zd['lat'] + (dist * math.sin(angle)) / 111000
                splice_lng = zd['lng'] + (dist * math.cos(angle)) / (111000 * math.cos(math.radians(zd['lat'])))

                # Feeder desde OLT
                feeder_code = f'CBL-FDR-{zone_prefix}-{s_idx:02d}'
                feeder_route = generate_route(
                    olt.latitude, olt.longitude,
                    splice_lat, splice_lng, num_points=random.randint(5, 9)
                )
                feeder_length_m = route_length_m(feeder_route)
                feeder = FiberCable.objects.create(
                    code=feeder_code,
                    name=f'Feeder {zd["name"]} E{s_idx}',
                    cable_type='feeder',
                    fiber_count=288,
                    length_m=round(feeder_length_m, 1),
                    description=(
                        f'Cable feeder desde central OLT a empalme {s_idx} de {zd["name"]}. '
                        f'Capacidad: 288 fibras monomodo G.652D.'
                    ),
                )
                feeder_map[zone.code].append(feeder)

                splice = SpliceClosure.objects.create(
                    code=f'SPC-{zone_prefix}-{s_idx:02d}',
                    name=f'Empalme {zd["name"]} {s_idx}',
                    closure_type=random.choice(['inline', 'dome']),
                    latitude=round(splice_lat, 6),
                    longitude=round(splice_lng, 6),
                    address=f'{random.choice(STREETS_BY_ZONE[zone.code])}, {zd["name"]}, Cieza',
                    zone=zone,
                    input_cable=feeder,
                    fiber_capacity=288,
                    fiber_count_used=0,
                )
                splices_in_zone.append(splice)
                all_splices.append(splice)

                power_at_splice = calc_power_to_splice(
                    OLT_OUTPUT_POWER_DBM, feeder_length_m / 1000.0
                )
                self.stdout.write(
                    f'    {splice.code}: feeder {feeder.length_m:.0f}m | '
                    f'PWR {power_at_splice:.2f} dBm'
                )

                dist_map[splice.code] = []

                for sp_idx in range(1, zd['splitters_per_splice'] + 1):
                    # Splitter cerca del empalme
                    splitter_lat, splitter_lng = random_point_in_radius(
                        splice_lat, splice_lng, 120)

                    distribution_code = f'CBL-DST-{zone_prefix}-{s_idx:02d}-{sp_idx:02d}'
                    dist_route = generate_route(
                        splice_lat, splice_lng,
                        splitter_lat, splitter_lng, num_points=random.randint(3, 5)
                    )
                    dist_length_m = route_length_m(dist_route)
                    dist_cable = FiberCable.objects.create(
                        code=distribution_code,
                        name=f'Distribution {zd["name"]} E{s_idx} S{sp_idx}',
                        cable_type='distribution',
                        fiber_count=144,
                        length_m=round(dist_length_m, 1),
                        description=(
                            f'Cable distribution desde {splice.code} al splitter {sp_idx} '
                            f'de {zd["name"]}. 144 fibras.'
                        ),
                    )
                    dist_map[splice.code].append(dist_cable)
                    splice.output_cable = dist_cable
                    splice.fiber_count_used += 1
                    splice.save()

                    power_at_splitter_in = calc_power_to_splitter(
                        OLT_OUTPUT_POWER_DBM,
                        feeder_length_m / 1000.0,
                        dist_length_m / 1000.0,
                    )
                    power_at_splitter_out = round(
                        power_at_splitter_in - ATT_SPLITTER_1X32_DB, 2)

                    splitter = Splitter.objects.create(
                        code=f'SPL-{zone_prefix}-{s_idx:02d}-{sp_idx:02d}',
                        name=f'Splitter {zd["name"]} E{s_idx} S{sp_idx}',
                        ratio='1x32',
                        olt=olt,
                        zone=zone,
                        input_port_olt=olt_port,
                        input_fiber_number=1,
                        input_cable=dist_cable,
                        output_power_dbm=power_at_splitter_out,
                        splice_in=splice,
                        latitude=round(splitter_lat, 6),
                        longitude=round(splitter_lng, 6),
                        address=f'Cerca de {splice.address}',
                    )
                    all_splitters.append(splitter)
                    olt_port += 1
                    self.global_splitter_port += 1

                    self.stdout.write(
                        f'      {splitter.code}: dist {dist_cable.length_m:.0f}m | '
                        f'IN {power_at_splitter_in:.2f} dBm | OUT {power_at_splitter_out:.2f} dBm'
                    )

                    # Cajas alrededor del splitter
                    num_boxes = random.randint(*zd['boxes_per_splitter'])
                    boxes_for_splitter = self._generate_boxes_for_splitter(
                        splitter, num_boxes, zone, zd
                    )

                    for box_idx, (box_lat, box_lng, box_address) in enumerate(boxes_for_splitter, 1):
                        self.box_counter += 1
                        box_code = f'CTO-{self.box_counter:04d}'

                        # Cable drop splitter -> caja
                        drop_code = f'CBL-DRP-{box_code}'
                        drop_route = generate_route(
                            splitter_lat, splitter_lng,
                            box_lat, box_lng, num_points=random.randint(2, 4)
                        )
                        drop_length_m = route_length_m(drop_route)
                        drop_cable = FiberCable.objects.create(
                            code=drop_code,
                            name=f'Drop {box_code}',
                            cable_type='drop',
                            fiber_count=12,
                            length_m=round(drop_length_m, 1),
                            description=f'Cable drop desde {splitter.code} a {box_code}.',
                        )
                        drop_box_map[box_code] = drop_cable

                        expected_pwr_box = calc_power_at_box(
                            OLT_OUTPUT_POWER_DBM,
                            feeder_length_m / 1000.0,
                            dist_length_m / 1000.0,
                            drop_length_m / 1000.0,
                        )

                        box = FiberBox.objects.create(
                            code=box_code,
                            name=f'CTO {zd["name"]} {box_idx} ({box_address.split(",")[0]})',
                            box_type=random.choice(BOX_TYPE_BY_DENSITY),
                            splitter=splitter,
                            zone=zone,
                            splitter_port=box_idx,
                            max_capacity=16,
                            latitude=round(box_lat, 6),
                            longitude=round(box_lng, 6),
                            address=box_address,
                            input_cable=drop_cable,
                            input_fiber_number=1,
                            expected_power_dbm=expected_pwr_box,
                            measured_power_dbm=round(
                                expected_pwr_box + random.uniform(-0.4, 0.4), 2),
                            splice_in=splice,
                            status=pick_box_status(),
                        )
                        all_boxes.append(box)

                        # Clientes conectados a esta caja
                        num_clients = random.randint(*zd['clients_per_box'])
                        for cli_idx in range(1, num_clients + 1):
                            self.client_counter += 1
                            client_code = f'CLI-{self.client_counter:04d}'
                            cli_lat, cli_lng = random_point_near_box(
                                box_lat, box_lng, max_distance_m=random.uniform(15, 55)
                            )

                            # Cable drop caja -> cliente
                            cli_drop_code = f'CBL-DRP-{client_code}'
                            cli_drop_route = generate_route(
                                box_lat, box_lng,
                                cli_lat, cli_lng, num_points=random.randint(1, 2)
                            )
                            cli_drop_length_m = route_length_m(cli_drop_route)
                            cli_drop_cable = FiberCable.objects.create(
                                code=cli_drop_code,
                                name=f'Drop cliente {client_code}',
                                cable_type='drop',
                                fiber_count=2,
                                length_m=round(cli_drop_length_m, 1),
                                description=f'Cable drop desde {box_code} a {client_code}.',
                            )
                            drop_client_map[client_code] = cli_drop_cable

                            expected_pwr_client = calc_power_at_client(
                                OLT_OUTPUT_POWER_DBM,
                                feeder_length_m / 1000.0,
                                dist_length_m / 1000.0,
                                drop_length_m / 1000.0,
                                client_drop_km=cli_drop_length_m / 1000.0,
                            )

                            status = pick_client_status()
                            # Si el estado no es active, la potencia medida se desvia mas
                            if status == 'active':
                                measured_rx = round(expected_pwr_client + random.uniform(-1.0, 0.5), 2)
                            elif status == 'degraded':
                                measured_rx = round(expected_pwr_client + random.uniform(-4.0, -1.5), 2)
                            elif status == 'affected':
                                measured_rx = round(expected_pwr_client + random.uniform(-15.0, -8.0), 2)
                            elif status == 'installing':
                                measured_rx = None
                            else:  # disconnected
                                measured_rx = round(expected_pwr_client + random.uniform(-20.0, -10.0), 2)

                            client = Client.objects.create(
                                client_code=client_code,
                                full_name=self._random_full_name(),
                                address=f'{box_address} (Piso {cli_idx}, Puerta {random.choice("AB")})',
                                latitude=round(cli_lat, 6),
                                longitude=round(cli_lng, 6),
                                box=box,
                                box_port=cli_idx,
                                olt_port=splitter.input_port_olt,
                                drop_fiber_number=cli_idx,
                                expected_power_dbm=expected_pwr_client,
                                status=status,
                                optical_power_rx=measured_rx,
                                optical_power_tx=round(random.uniform(0.5, 4.0), 1) if status != 'installing' else None,
                            )
                            all_clients.append(client)

        self.stdout.write(self.style.HTTP_INFO(
            f'  Infraestructura generada: '
            f'{len(all_splices)} empalmes, {len(all_splitters)} splitters, '
            f'{len(all_boxes)} cajas, {len(all_clients)} clientes.'
        ))

        # ============================================================
        # 10. CREAR FIBER ASSIGNMENTS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 10. Creando FiberAssignments ---'))
        fa_count = 0

        # Feeder fiber #1 -> cada empalme
        for zone_code, feeders in feeder_map.items():
            for feeder in feeders:
                splice = SpliceClosure.objects.get(input_cable=feeder)
                FiberAssignment.objects.create(
                    cable=feeder,
                    fiber_number=1,
                    splitter=None,
                    box=None,
                    client=None,
                    from_splice=None,
                    from_splitter_port=None,
                    status='active',
                    notes=f'Feeder {feeder.code} fibra 1 -> {splice.code}',
                )
                fa_count += 1

        # Distribution fiber #1 -> cada splitter
        for splitter in all_splitters:
            dist_cable = splitter.input_cable
            FiberAssignment.objects.create(
                cable=dist_cable,
                fiber_number=1,
                splitter=splitter,
                box=None,
                client=None,
                from_splice=splitter.splice_in,
                from_splitter_port=None,
                status='active',
                notes=f'Distribution {dist_cable.code} fibra 1 -> {splitter.code}',
            )
            fa_count += 1

        # Drop fiber #1 -> cada caja
        for box in all_boxes:
            drop_cable = box.input_cable
            FiberAssignment.objects.create(
                cable=drop_cable,
                fiber_number=1,
                splitter=None,
                box=box,
                client=None,
                from_splice=box.splice_in,
                from_splitter_port=box.splitter_port,
                status='active',
                notes=f'Drop {drop_cable.code} fibra 1 -> {box.code}',
            )
            fa_count += 1

        # Drop fiber #1 -> cada cliente
        for client in all_clients:
            cli_drop_cable = drop_client_map[client.client_code]
            FiberAssignment.objects.create(
                cable=cli_drop_cable,
                fiber_number=1,
                splitter=None,
                box=None,
                client=client,
                from_splice=None,
                from_splitter_port=None,
                status='active',
                notes=f'Drop {cli_drop_cable.code} fibra 1 -> {client.client_code}',
            )
            fa_count += 1

        self.stdout.write(f'  FiberAssignments creadas: {fa_count}')

        # ============================================================
        # 11. CREAR CABLE SEGMENTS CON RUTAS GPS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO(
            '--- 11. Creando CableSegments con rutas GPS ---'))
        seg_count = 0

        # Feeder segments: OLT -> cada empalme
        for zone_code, feeders in feeder_map.items():
            for feeder in feeders:
                splice = SpliceClosure.objects.get(input_cable=feeder)
                route = generate_route(
                    olt.latitude, olt.longitude,
                    splice.latitude, splice.longitude,
                    num_points=max(5, min(12, int(feeder.length_m / 80))),
                    osrm_cache=self.osrm_cache,
                )
                CableSegment.objects.create(
                    cable=feeder,
                    segment_type='olt_to_splice',
                    from_olt=olt,
                    to_splice=splice,
                    fiber_numbers='1',
                    length_m=feeder.length_m,
                    route_coordinates=json.dumps(route),
                    attenuation_db=calc_attenuation(
                        feeder.length_m / 1000.0, connectors=2, splices=1),
                    notes=f'Feeder: OLT -> {splice.code}',
                )
                seg_count += 1
            self.stdout.write(self.style.HTTP_INFO(
                f'  {len(feeder_map[zone_code])} feeders creados para {zone_code}'))

        # Distribution segments: Empalme -> Splitter
        for splitter in all_splitters:
            dist_cable = splitter.input_cable
            splice = splitter.splice_in
            route = generate_route(
                splice.latitude, splice.longitude,
                splitter.latitude, splitter.longitude,
                num_points=random.randint(3, 5),
                osrm_cache=self.osrm_cache,
            )
            CableSegment.objects.create(
                cable=dist_cable,
                segment_type='splice_to_splitter',
                from_splice=splice,
                to_splitter=splitter,
                fiber_numbers='1',
                length_m=dist_cable.length_m,
                route_coordinates=json.dumps(route),
                attenuation_db=calc_attenuation(
                    dist_cable.length_m / 1000.0, connectors=2, splices=1),
                notes=f'Distribution: {splice.code} -> {splitter.code}',
            )
            seg_count += 1
        self.stdout.write(self.style.HTTP_INFO(
            f'  {len(all_splitters)} distribution segments creados'))

        # Drop segments: Splitter -> Caja
        for box in all_boxes:
            drop_cable = box.input_cable
            splitter = box.splitter
            route = generate_route(
                splitter.latitude, splitter.longitude,
                box.latitude, box.longitude,
                num_points=random.randint(2, 5),
                osrm_cache=self.osrm_cache,
            )
            CableSegment.objects.create(
                cable=drop_cable,
                segment_type='splitter_to_box',
                from_splitter=splitter,
                to_box=box,
                fiber_numbers='1',
                length_m=drop_cable.length_m,
                route_coordinates=json.dumps(route),
                attenuation_db=calc_attenuation(
                    drop_cable.length_m / 1000.0, connectors=2, splices=1),
                notes=f'Drop: {splitter.code} -> {box.code}',
            )
            seg_count += 1
        self.stdout.write(self.style.HTTP_INFO(
            f'  {len(all_boxes)} drop segments splitter->caja creados'))

        # Box-to-client segments
        for client in all_clients:
            cli_drop_cable = drop_client_map[client.client_code]
            box = client.box
            # Los tramos box_to_client son muy cortos; usamos rutas procedurales
            # para no saturar OSRM con cientos de peticiones.
            route = generate_route(
                box.latitude, box.longitude,
                client.latitude, client.longitude,
                num_points=random.randint(1, 3),
            )
            CableSegment.objects.create(
                cable=cli_drop_cable,
                segment_type='box_to_client',
                from_box=box,
                to_client=client,
                fiber_numbers=str(client.box_port),
                length_m=cli_drop_cable.length_m,
                route_coordinates=json.dumps(route),
                attenuation_db=calc_attenuation(
                    cli_drop_cable.length_m / 1000.0, connectors=2, splices=1),
                notes=f'Drop: {box.code} puerto {client.box_port} -> {client.client_code}',
            )
            seg_count += 1

        self.stdout.write(f'  Total CableSegments: {seg_count}')

        # ============================================================
        # RESUMEN FINAL
        # ============================================================
        self._print_summary(
            olt, zones_map, all_splices, feeder_map, dist_map,
            all_splitters, all_boxes, all_clients,
            fa_count, seg_count
        )

    # ============================================================
    # METODOS AUXILIARES
    # ============================================================
    def _random_full_name(self):
        fn = random.choice(FIRST_NAMES)
        ln1 = random.choice(LAST_NAMES)
        ln2 = random.choice(LAST_NAMES)
        return f'{fn} {ln1} {ln2}'

    def _generate_boxes_for_splitter(self, splitter, num_boxes, zone, zd):
        """Genera coordenadas y direcciones para las cajas de un splitter."""
        boxes = []
        streets = STREETS_BY_ZONE.get(zone.code, ['Calle Principal'])
        # Distribuir cajas en un patron de cuadricula con jitter alrededor del splitter
        radius_m = min(zd['radius_m'] * 0.35, 350)
        # Calcular pasos angulares para cubrir un sector
        for i in range(num_boxes):
            angle = (2 * math.pi / num_boxes) * i + random.uniform(-0.4, 0.4)
            dist = random.uniform(radius_m * 0.25, radius_m * 0.9)
            lat = splitter.latitude + (dist * math.sin(angle)) / 111000
            lng = splitter.longitude + (dist * math.cos(angle)) / (111000 * math.cos(math.radians(splitter.latitude)))
            address = f'{random.choice(streets)}, {random.randint(1, 120)}, {zd["name"]}'
            boxes.append((round(lat, 6), round(lng, 6), address))
        return boxes

    def _print_summary(self, olt, zones_map, all_splices, feeder_map, dist_map,
                       all_splitters, all_boxes, all_clients,
                       fa_count, seg_count):
        """Imprime resumen detallado del despliegue con potencias opticas."""
        sep = "=" * 72
        self.stdout.write(self.style.SUCCESS(
            f'\n{sep}\n'
            f'  DESPLIEGUE FTTH DE CIEZA - RESUMEN DE INGENIERIA\n'
            f'{sep}'
        ))
        self.stdout.write(
            f'  INFRAESTRUCTURA:\n'
            f'    OLT:         1  ({olt.code}) | '
            f'Potencia: +{olt.output_power_dbm} dBm\n'
            f'    Zonas:       {len(zones_map)}\n'
            f'    Empalmes:    {len(all_splices)}\n'
            f'    Feeders:     {sum(len(v) for v in feeder_map.values())}  (288 fibras cada uno)\n'
            f'    Distrib.:    {sum(len(v) for v in dist_map.values())}  (144 fibras cada uno)\n'
            f'    Splitters:   {len(all_splitters)}  '
            f'(1x32, -{ATT_SPLITTER_1X32_DB} dB)\n'
            f'    Cajas CTO:   {len(all_boxes)}\n'
            f'    Clientes:    {len(all_clients)}\n'
            f'    FiberAssignments: {fa_count}\n'
            f'    CableSegments:    {seg_count} (con rutas GPS)\n'
            f'  FORMULA OPTICA:\n'
            f'    P_final = {OLT_OUTPUT_POWER_DBM} - (0.35 x km) - '
            f'(0.5 x N_con) - (0.1 x N_emp) - {ATT_SPLITTER_1X32_DB}'
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n  POTENCIAS POR ZONA:'
        ))
        for zd in ZONES_DATA:
            zc = zd['code']
            zone = zones_map[zc]
            zone_splices = [s for s in all_splices if s.zone == zone]
            zone_splitters = [s for s in all_splitters if s.zone == zone]
            zone_boxes = [b for b in all_boxes if b.zone == zone]
            zone_clients = [c for c in all_clients if c.zone == zone]
            box_pwrs = [b.expected_power_dbm for b in zone_boxes if b.expected_power_dbm is not None]
            cli_pwrs = [c.expected_power_dbm for c in zone_clients if c.expected_power_dbm is not None]
            affected = [c for c in zone_clients if c.status == 'affected']

            splice_in_pwrs = [s.input_cable.length_m for s in zone_splices]
            dist_lengths = []
            for s in zone_splices:
                dist_lengths.extend([d.length_m for d in dist_map.get(s.code, [])])

            self.stdout.write(
                f'    {zc} ({zd["name"]}):\n'
                f'      Feeders: {len(zone_splices)} | Distribuciones: {len(zone_splitters)}\n'
                f'      Long. feeder media: {sum(splice_in_pwrs)/max(len(splice_in_pwrs),1):.0f}m | '
                f'distribucion media: {sum(dist_lengths)/max(len(dist_lengths),1):.0f}m\n'
                f'      Cajas: {len(zone_boxes)} | '
                f'Rango PWR cajas: {min(box_pwrs):.2f} a {max(box_pwrs):.2f} dBm\n'
                f'      Clientes: {len(zone_clients)} | '
                f'Rango PWR clientes: {min(cli_pwrs):.2f} a {max(cli_pwrs):.2f} dBm\n'
                f'      Clientes afectados: {len(affected)}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n  CONTADOS EN BASE DE DATOS:\n'
            f'    OLT:              {OLT.objects.count()}\n'
            f'    Zonas:            {Zone.objects.count()}\n'
            f'    Cables:           {FiberCable.objects.count()}\n'
            f'    Empalmes:         {SpliceClosure.objects.count()}\n'
            f'    Splitters:        {Splitter.objects.count()}\n'
            f'    Cajas:            {FiberBox.objects.count()}\n'
            f'    Clientes:         {Client.objects.count()}\n'
            f'    FiberAssignments: {FiberAssignment.objects.count()}\n'
            f'    CableSegments:    {CableSegment.objects.count()}\n'
            f'{sep}'
        ))
