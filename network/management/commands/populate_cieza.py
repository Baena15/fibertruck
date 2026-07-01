"""
FiberTruck - Comando para poblar la base de datos con datos de INGENIERIA REAL
de un despliegue FTTH en Cieza, Murcia.

Topologia completa:
  OLT -> Cable Feeder (144f) -> SpliceClosure (5) -> Cable Distribution (72f)
       -> Splitter (1x32) -> Cable Drop (12f) -> FiberBox/CTO (29) -> Client (161)

Calculos opticos basados en:
  - Atenuacion fibra monomodo G.652D: 0.35 dB/km @ 1490nm
  - Atenuacion conector: 0.5 dB cada uno
  - Atenuacion empalme de fusion: 0.1 dB cada uno
  - Atenuacion splitter 1x32: 16.5 dB (tipico)
  - OLT salida: +3.0 dBm
"""
import json
import random
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


def generate_route(start_lat, start_lng, end_lat, end_lng, num_points=4):
    """Genera coordenadas intermedias realistas entre dos puntos."""
    route = [[start_lat, start_lng]]
    for i in range(1, num_points + 1):
        frac = i / (num_points + 1)
        lat = start_lat + (end_lat - start_lat) * frac + random.uniform(-0.0001, 0.0001)
        lng = start_lng + (end_lng - start_lng) * frac + random.uniform(-0.0001, 0.0001)
        route.append([round(lat, 6), round(lng, 6)])
    route.append([end_lat, end_lng])
    return route


# ============================================================
# DATOS DEL DESPLIEGUE REAL DE CIEZA
# ============================================================

ZONES_DATA = [
    {'code': 'Z-ERA',  'name': 'La Era - La Asuncion',    'lat': 38.2375, 'lng': -1.4195, 'pop': 6300,  'desc': 'Casco historico y zona suroeste. Barrio mas antiguo con calles estrechas.'},
    {'code': 'Z-SJOR', 'name': 'San Jose Obrero',         'lat': 38.2395, 'lng': -1.4150, 'pop': 7249,  'desc': 'Zona sureste. Alta densidad. Atravesado por la Rambla del Realejo.'},
    {'code': 'Z-SJOA', 'name': 'San Joaquin',              'lat': 38.2390, 'lng': -1.4175, 'pop': 5800,  'desc': 'Centro urbano. Zona comercial. Calles anchas y edificios de 4-6 plantas.'},
    {'code': 'Z-SJBO', 'name': 'San Juan Bosco',           'lat': 38.2420, 'lng': -1.4140, 'pop': 9479,  'desc': 'Zona noreste, barrio moderno. Edificios de 10-20 anios de antiguedad.'},
    {'code': 'Z-HORT', 'name': 'La Horta',                 'lat': 38.2440, 'lng': -1.4180, 'pop': 4230,  'desc': 'Zona norte. Mezcla de viviendas nuevas y zona suburbanizada.'},
]

FEEDER_CABLES_DATA = [
    {'code': 'CBL-FDR-ERA',  'name': 'Feeder La Era',         'zone': 'Z-ERA',  'length_m': 600},
    {'code': 'CBL-FDR-SJOR', 'name': 'Feeder San Jose',       'zone': 'Z-SJOR', 'length_m': 800},
    {'code': 'CBL-FDR-SJOA', 'name': 'Feeder San Joaquin',    'zone': 'Z-SJOA', 'length_m': 400},
    {'code': 'CBL-FDR-SJBO', 'name': 'Feeder San Juan Bosco', 'zone': 'Z-SJBO', 'length_m': 1000},
    {'code': 'CBL-FDR-HORT', 'name': 'Feeder La Horta',       'zone': 'Z-HORT', 'length_m': 700},
]

SPLICES_DATA = [
    {'code': 'SPC-ERA',  'name': 'Empalme La Era',         'zone': 'Z-ERA',  'type': 'inline', 'lat': 38.2375, 'lng': -1.4195, 'addr': 'C/ Real, 15, La Era, Cieza',        'cap': 144},
    {'code': 'SPC-SJOR', 'name': 'Empalme San Jose',       'zone': 'Z-SJOR', 'type': 'inline', 'lat': 38.2395, 'lng': -1.4150, 'addr': 'Avda. Juan Carlos I, 40, San Jose, Cieza', 'cap': 144},
    {'code': 'SPC-SJOA', 'name': 'Empalme San Joaquin',    'zone': 'Z-SJOA', 'type': 'dome',   'lat': 38.2390, 'lng': -1.4175, 'addr': 'C/ Marques de Camachos, 10, San Joaquin, Cieza', 'cap': 144},
    {'code': 'SPC-SJBO', 'name': 'Empalme San Juan Bosco', 'zone': 'Z-SJBO', 'type': 'dome',   'lat': 38.2420, 'lng': -1.4140, 'addr': 'Avda. de Murcia, 75, San Juan Bosco, Cieza', 'cap': 144},
    {'code': 'SPC-HORT', 'name': 'Empalme La Horta',       'zone': 'Z-HORT', 'type': 'inline', 'lat': 38.2440, 'lng': -1.4180, 'addr': 'C/ Santiago, 8, La Horta, Cieza',  'cap': 144},
]

DISTRIBUTION_CABLES_DATA = [
    {'code': 'CBL-DST-ERA',  'name': 'Distribution La Era',         'zone': 'Z-ERA',  'splice': 'SPC-ERA',  'length_m': 800},
    {'code': 'CBL-DST-SJOR', 'name': 'Distribution San Jose',       'zone': 'Z-SJOR', 'splice': 'SPC-SJOR', 'length_m': 650},
    {'code': 'CBL-DST-SJOA', 'name': 'Distribution San Joaquin',    'zone': 'Z-SJOA', 'splice': 'SPC-SJOA', 'length_m': 500},
    {'code': 'CBL-DST-SJBO', 'name': 'Distribution San Juan Bosco', 'zone': 'Z-SJBO', 'splice': 'SPC-SJBO', 'length_m': 900},
    {'code': 'CBL-DST-HORT', 'name': 'Distribution La Horta',       'zone': 'Z-HORT', 'splice': 'SPC-HORT', 'length_m': 700},
]

SPLITTERS_DATA = [
    {'code': 'SPL-ERA-01',  'name': 'Splitter La Era',         'zone': 'Z-ERA',  'port': 1, 'lat': 38.2376, 'lng': -1.4193, 'splice': 'SPC-ERA',  'dist': 'CBL-DST-ERA'},
    {'code': 'SPL-SJOR-01', 'name': 'Splitter San Jose',       'zone': 'Z-SJOR', 'port': 2, 'lat': 38.2396, 'lng': -1.4148, 'splice': 'SPC-SJOR', 'dist': 'CBL-DST-SJOR'},
    {'code': 'SPL-SJOA-01', 'name': 'Splitter San Joaquin',    'zone': 'Z-SJOA', 'port': 3, 'lat': 38.2391, 'lng': -1.4173, 'splice': 'SPC-SJOA', 'dist': 'CBL-DST-SJOA'},
    {'code': 'SPL-SJBO-01', 'name': 'Splitter San Juan Bosco', 'zone': 'Z-SJBO', 'port': 4, 'lat': 38.2421, 'lng': -1.4138, 'splice': 'SPC-SJBO', 'dist': 'CBL-DST-SJBO'},
    {'code': 'SPL-HORT-01', 'name': 'Splitter La Horta',       'zone': 'Z-HORT', 'port': 5, 'lat': 38.2441, 'lng': -1.4178, 'splice': 'SPC-HORT', 'dist': 'CBL-DST-HORT'},
]

DROP_CABLES_DATA = [
    # La Era (2 cables -> 5 cajas)
    {'code': 'CBL-DRP-ERA-01', 'name': 'Drop La Era G1', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'length_m': 150, 'boxes': [('CTO-001',1),('CTO-002',2),('CTO-003',3)]},
    {'code': 'CBL-DRP-ERA-02', 'name': 'Drop La Era G2', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'length_m': 200, 'boxes': [('CTO-004',1),('CTO-005',2)]},
    # San Jose (2 cables -> 6 cajas)
    {'code': 'CBL-DRP-SJOR-01', 'name': 'Drop San Jose G1', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'length_m': 180, 'boxes': [('CTO-010',1),('CTO-011',2),('CTO-012',3)]},
    {'code': 'CBL-DRP-SJOR-02', 'name': 'Drop San Jose G2', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'length_m': 220, 'boxes': [('CTO-013',1),('CTO-014',2),('CTO-015',3)]},
    # San Joaquin (2 cables -> 6 cajas)
    {'code': 'CBL-DRP-SJOA-01', 'name': 'Drop San Joaquin G1', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'length_m': 160, 'boxes': [('CTO-020',1),('CTO-021',2),('CTO-022',3)]},
    {'code': 'CBL-DRP-SJOA-02', 'name': 'Drop San Joaquin G2', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'length_m': 190, 'boxes': [('CTO-023',1),('CTO-024',2),('CTO-025',3)]},
    # San Juan Bosco (3 cables -> 7 cajas)
    {'code': 'CBL-DRP-SJBO-01', 'name': 'Drop S.J. Bosco G1', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'length_m': 170, 'boxes': [('CTO-030',1),('CTO-031',2),('CTO-032',3)]},
    {'code': 'CBL-DRP-SJBO-02', 'name': 'Drop S.J. Bosco G2', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'length_m': 210, 'boxes': [('CTO-033',1),('CTO-034',2),('CTO-035',3)]},
    {'code': 'CBL-DRP-SJBO-03', 'name': 'Drop S.J. Bosco G3', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'length_m': 250, 'boxes': [('CTO-036',1)]},
    # La Horta (2 cables -> 5 cajas)
    {'code': 'CBL-DRP-HORT-01', 'name': 'Drop La Horta G1', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'length_m': 140, 'boxes': [('CTO-040',1),('CTO-041',2),('CTO-042',3)]},
    {'code': 'CBL-DRP-HORT-02', 'name': 'Drop La Horta G2', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'length_m': 260, 'boxes': [('CTO-043',1),('CTO-044',2)]},
]

BOXES_DATA = [
    # --- La Era (5 cajas) ---
    {'code': 'CTO-001', 'name': 'CTO La Era - Plaza Constitucion',      'zone': 'Z-ERA',  'splitter': 'SPL-ERA-01',  'port': 1,  'lat': 38.2378, 'lng': -1.4198, 'addr': 'Plaza de la Constitucion, 5, La Era'},
    {'code': 'CTO-002', 'name': 'CTO La Era - C/ Real',                'zone': 'Z-ERA',  'splitter': 'SPL-ERA-01',  'port': 2,  'lat': 38.2372, 'lng': -1.4190, 'addr': 'Calle Real, 23, La Era'},
    {'code': 'CTO-003', 'name': 'CTO La Era - Museo Siyasa',           'zone': 'Z-ERA',  'splitter': 'SPL-ERA-01',  'port': 3,  'lat': 38.2370, 'lng': -1.4205, 'addr': 'Avda. del Mediterraneo, 55, La Era'},
    {'code': 'CTO-004', 'name': 'CTO La Era - C/ Espinosa',            'zone': 'Z-ERA',  'splitter': 'SPL-ERA-01',  'port': 4,  'lat': 38.2380, 'lng': -1.4185, 'addr': 'Calle Espinosa, 12, La Era'},
    {'code': 'CTO-005', 'name': 'CTO La Era - C/ Colon',               'zone': 'Z-ERA',  'splitter': 'SPL-ERA-01',  'port': 5,  'lat': 38.2368, 'lng': -1.4195, 'addr': 'Calle Colon, 34, La Era'},
    # --- San Jose Obrero (6 cajas) ---
    {'code': 'CTO-010', 'name': 'CTO San Jose - C/ Murcia',            'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 6,  'lat': 38.2398, 'lng': -1.4155, 'addr': 'Calle Murcia, 18, San Jose'},
    {'code': 'CTO-011', 'name': 'CTO San Jose - Centro Cultural',      'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 7,  'lat': 38.2392, 'lng': -1.4145, 'addr': 'Calle Generos de Punto, San Jose'},
    {'code': 'CTO-012', 'name': 'CTO San Jose - C/ Albacete',          'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 8,  'lat': 38.2402, 'lng': -1.4148, 'addr': 'Calle Albacete, 42, San Jose'},
    {'code': 'CTO-013', 'name': 'CTO San Jose - Avda. Juan Carlos I',  'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 9,  'lat': 38.2405, 'lng': -1.4158, 'addr': 'Avda. Juan Carlos I, 67, San Jose'},
    {'code': 'CTO-014', 'name': 'CTO San Jose - C/ Granada',           'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 10, 'lat': 38.2390, 'lng': -1.4162, 'addr': 'Calle Granada, 9, San Jose'},
    {'code': 'CTO-015', 'name': 'CTO San Jose - C/ Jaen',              'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 11, 'lat': 38.2400, 'lng': -1.4138, 'addr': 'Calle Jaen, 28, San Jose'},
    # --- San Joaquin (6 cajas) ---
    {'code': 'CTO-020', 'name': 'CTO San Joaquin - Plaza Espana',       'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 12, 'lat': 38.2392, 'lng': -1.4180, 'addr': 'Plaza de Espana, 1, San Joaquin'},
    {'code': 'CTO-021', 'name': 'CTO San Joaquin - Mercado Abastos',    'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 13, 'lat': 38.2385, 'lng': -1.4170, 'addr': 'Calle del Mercado, 10, San Joaquin'},
    {'code': 'CTO-022', 'name': 'CTO San Joaquin - Bib. Salmeron',      'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 14, 'lat': 38.2395, 'lng': -1.4172, 'addr': 'Calle Fray Pascual Salmeron, 3, San Joaquin'},
    {'code': 'CTO-023', 'name': 'CTO San Joaquin - Oficina Turismo',    'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 15, 'lat': 38.2388, 'lng': -1.4185, 'addr': 'Plaza de Espana, 8, San Joaquin'},
    {'code': 'CTO-024', 'name': 'CTO San Joaquin - C/ Marques Camachos','zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 16, 'lat': 38.2398, 'lng': -1.4168, 'addr': 'Calle Marques de Camachos, 45, San Joaquin'},
    {'code': 'CTO-025', 'name': 'CTO San Joaquin - Deleg. Hacienda',    'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 17, 'lat': 38.2382, 'lng': -1.4178, 'addr': 'Avda. de Murcia, 12, San Joaquin'},
    # --- San Juan Bosco (7 cajas) ---
    {'code': 'CTO-030', 'name': 'CTO S.J. Bosco - Piscina Cubierta',    'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 18, 'lat': 38.2415, 'lng': -1.4135, 'addr': 'Calle Pintor Villodres, S.J. Bosco'},
    {'code': 'CTO-031', 'name': 'CTO S.J. Bosco - IES Diego Tortosa',   'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 19, 'lat': 38.2425, 'lng': -1.4130, 'addr': 'Avda. de Murcia, 80, S.J. Bosco'},
    {'code': 'CTO-032', 'name': 'CTO S.J. Bosco - Centro Salud Este',   'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 20, 'lat': 38.2420, 'lng': -1.4145, 'addr': 'Calle Molino de Papel, 15, S.J. Bosco'},
    {'code': 'CTO-033', 'name': 'CTO S.J. Bosco - Palacio Justicia',    'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 21, 'lat': 38.2410, 'lng': -1.4155, 'addr': 'Calle Urano, 2, S.J. Bosco'},
    {'code': 'CTO-034', 'name': 'CTO S.J. Bosco - Estacion Autobuses',  'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 22, 'lat': 38.2430, 'lng': -1.4140, 'addr': 'Calle Federico Garcia Lorca, 1, S.J. Bosco'},
    {'code': 'CTO-035', 'name': 'CTO S.J. Bosco - C/ Beniel',           'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 23, 'lat': 38.2428, 'lng': -1.4125, 'addr': 'Calle Beniel, 33, S.J. Bosco'},
    {'code': 'CTO-036', 'name': 'CTO S.J. Bosco - Avda. Alcantarilla',  'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 24, 'lat': 38.2412, 'lng': -1.4130, 'addr': 'Avda. de Alcantarilla, 55, S.J. Bosco'},
    # --- La Horta (5 cajas) ---
    {'code': 'CTO-040', 'name': 'CTO La Horta - Auditorio G. Celaya',   'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 25, 'lat': 38.2435, 'lng': -1.4185, 'addr': 'Calle Rio Segura, 20, La Horta'},
    {'code': 'CTO-041', 'name': 'CTO La Horta - Escuela Idiomas',       'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 26, 'lat': 38.2442, 'lng': -1.4175, 'addr': 'Calle Santiago, 12, La Horta'},
    {'code': 'CTO-042', 'name': 'CTO La Horta - C/ San Cristobal',      'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 27, 'lat': 38.2445, 'lng': -1.4190, 'addr': 'Calle San Cristobal, 44, La Horta'},
    {'code': 'CTO-043', 'name': 'CTO La Horta - Cabezo Fuensantilla',   'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 28, 'lat': 38.2450, 'lng': -1.4180, 'addr': 'Camino del Cabezo, 8, La Horta'},
    {'code': 'CTO-044', 'name': 'CTO La Horta - C/ Poligono Industrial','zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 29, 'lat': 38.2430, 'lng': -1.4165, 'addr': 'Calle Industrial, 15, La Horta'},
]


class Command(BaseCommand):
    help = 'Poblar despliegue FTTH de Cieza con datos de ingenieria real'

    def handle(self, *args, **options):
        random.seed(42)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '=== FiberTruck: Despliegue FTTH Real de Cieza, Murcia ==='))
        self.stdout.write(self.style.MIGRATE_HEADING(
            '    OLT(1) -> Feeder(5x144f) -> Splice(5) -> Distribution(5x72f)'
            ' -> Splitter(5x1x32) -> Drop(12x12f) -> CTO(29) -> Clientes(161)'))
        self.stdout.write('')

        # Idempotencia: salir si ya existe
        if OLT.objects.exists():
            self.stdout.write(self.style.WARNING('Ya existe un despliegue. Saltando.'))
            return

        # ============================================================
        # 1. CREAR OLT
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 1. Creando OLT ---'))
        olt, _ = OLT.objects.get_or_create(code='OLT-CIEZA-01', defaults={
            'name': 'OLT-CIEZA-01',
            'address': 'Calle Mayor, 45 - Centro de Datos Municipal, Cieza (Murcia)',
            'latitude': 38.2390,
            'longitude': -1.4175,
            'max_ports': 16,
            'output_power_dbm': OLT_OUTPUT_POWER_DBM,
            'splitter_ratio': '1x32',
        })
        self.stdout.write(f'  OLT: {olt} | Potencia: +{olt.output_power_dbm} dBm')

        # ============================================================
        # 2. CREAR ZONAS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 2. Creando Zonas ---'))
        zones_map = {}
        for zd in ZONES_DATA:
            zone, _ = Zone.objects.get_or_create(code=zd['code'], defaults={
                'name': zd['name'],
                'description': zd['desc'],
                'latitude': zd['lat'],
                'longitude': zd['lng'],
                'population_estimate': zd['pop'],
            })
            zones_map[zd['code']] = zone
            self.stdout.write(f'  Zona: {zone}')

        # ============================================================
        # 3. CREAR CABLES FEEDER (5 cables, 144 fibras cada uno)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 3. Creando Cables Feeder (5 x 144f) ---'))
        feeder_map = {}
        for fd in FEEDER_CABLES_DATA:
            fc, _ = FiberCable.objects.get_or_create(code=fd['code'], defaults={
                'name': fd['name'],
                'cable_type': 'feeder',
                'fiber_count': 144,
                'length_m': fd['length_m'],
                'description': (
                    f'Cable feeder desde central OLT a {fd["zone"]}. '
                    f'Capacidad: 144 fibras monomodo G.652D. '
                    f'Longitud: {fd["length_m"]}m.'
                ),
            })
            feeder_map[fd['code']] = fc
            self.stdout.write(f'  {fc.code}: {fc.length_m}m -> {fd["zone"]}')

        # ============================================================
        # 4. CREAR EMPALMES (SpliceClosure)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 4. Creando Empalmes (5) ---'))
        splices_map = {}
        for sd in SPLICES_DATA:
            zone = zones_map[sd['zone']]
            feeder = feeder_map[f'CBL-FDR-{sd["code"].split("-")[1]}']
            sp, _ = SpliceClosure.objects.get_or_create(code=sd['code'], defaults={
                'name': sd['name'],
                'closure_type': sd['type'],
                'latitude': sd['lat'],
                'longitude': sd['lng'],
                'address': sd['addr'],
                'zone': zone,
                'input_cable': feeder,
                'fiber_capacity': sd['cap'],
                'fiber_count_used': 1,
            })
            splices_map[sd['code']] = sp
            pwr = calc_power_to_splice(OLT_OUTPUT_POWER_DBM, feeder.length_m / 1000.0)
            self.stdout.write(
                f'  {sp.code}: {sd["type"]} | {sp.address} | Potencia: {pwr} dBm'
            )

        # ============================================================
        # 5. CREAR CABLES DISTRIBUTION (5 cables, 72 fibras cada uno)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO(
            '--- 5. Creando Cables Distribution (5 x 72f) ---'))
        dist_map = {}
        for dd in DISTRIBUTION_CABLES_DATA:
            zone = zones_map[dd['zone']]
            splice = splices_map[dd['splice']]
            dc, _ = FiberCable.objects.get_or_create(code=dd['code'], defaults={
                'name': dd['name'],
                'cable_type': 'distribution',
                'fiber_count': 72,
                'length_m': dd['length_m'],
                'description': (
                    f'Cable distribution desde {dd["splice"]} al splitter '
                    f'de {dd["zone"]}. 72 fibras.'
                ),
            })
            dist_map[dd['code']] = dc
            splice.output_cable = dc
            splice.save()
            self.stdout.write(f'  {dc.code}: {dc.length_m}m -> {dd["splice"]}')

        # ============================================================
        # 6. CREAR SPLITTERS (5 x 1x32)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 6. Creando Splitters (5 x 1x32) ---'))
        splitters_map = {}
        for sd in SPLITTERS_DATA:
            zone = zones_map[sd['zone']]
            splice = splices_map[sd['splice']]
            dist_cable = dist_map[sd['dist']]
            feeder_km = feeder_map[
                f'CBL-FDR-{sd["code"].split("-")[1]}'
            ].length_m / 1000.0
            dist_km = dist_cable.length_m / 1000.0
            pwr_in = calc_power_to_splitter(OLT_OUTPUT_POWER_DBM, feeder_km, dist_km)
            pwr_out = round(pwr_in - ATT_SPLITTER_1X32_DB, 2)
            spl, _ = Splitter.objects.get_or_create(code=sd['code'], defaults={
                'name': sd['name'],
                'ratio': '1x32',
                'olt': olt,
                'zone': zone,
                'input_port_olt': sd['port'],
                'input_fiber_number': 1,
                'input_cable': dist_cable,
                'output_power_dbm': pwr_out,
                'splice_in': splice,
                'latitude': sd['lat'],
                'longitude': sd['lng'],
                'address': f'Cerca de {sd["name"]}, {zone.name}',
            })
            splitters_map[sd['code']] = spl
            self.stdout.write(
                f'  {spl.code}: {sd["name"]} | '
                f'Entrada: {pwr_in} dBm | Salida: {pwr_out} dBm'
            )

        # ============================================================
        # 7. CREAR CABLES DROP (12 cables, 12 fibras cada uno)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 7. Creando Cables Drop (12 x 12f) ---'))
        drop_map = {}
        for dd in DROP_CABLES_DATA:
            dpc, _ = FiberCable.objects.get_or_create(code=dd['code'], defaults={
                'name': dd['name'],
                'cable_type': 'drop',
                'fiber_count': 12,
                'length_m': dd['length_m'],
                'description': (
                    f'Cable drop desde {dd["splitter"]} a '
                    f'{len(dd["boxes"])} caja(s) de {dd["zone"]}.'
                ),
            })
            drop_map[dd['code']] = dpc
            self.stdout.write(
                f'  {dpc.code}: {dpc.length_m}m -> {len(dd["boxes"])} caja(s)'
            )

        # ============================================================
        # 8. CREAR CAJAS CTO (29 cajas con potencias calculadas)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 8. Creando Cajas CTO (29) ---'))
        boxes_map = {}
        for bd in BOXES_DATA:
            zone = zones_map[bd['zone']]
            splitter = splitters_map[bd['splitter']]
            # Buscar cable drop y fibra de entrada para esta caja
            input_cable = None
            input_fiber = None
            drop_len_m = 150
            for dd in DROP_CABLES_DATA:
                for bc, fn in dd['boxes']:
                    if bc == bd['code']:
                        input_cable = drop_map[dd['code']]
                        input_fiber = fn
                        drop_len_m = dd['length_m']
                        break
                if input_cable:
                    break
            # Calcular potencia esperada en caja
            zone_prefix = bd['zone'].split('-')[1]
            feeder_km = feeder_map[f'CBL-FDR-{zone_prefix}'].length_m / 1000.0
            dist_km = dist_map[f'CBL-DST-{zone_prefix}'].length_m / 1000.0
            drop_km = drop_len_m / 1000.0
            expected_pwr = calc_power_at_box(
                OLT_OUTPUT_POWER_DBM, feeder_km, dist_km, drop_km
            )
            box, _ = FiberBox.objects.get_or_create(code=bd['code'], defaults={
                'name': bd['name'],
                'box_type': 'CTO',
                'splitter': splitter,
                'zone': zone,
                'splitter_port': bd['port'],
                'max_capacity': 16,
                'latitude': bd['lat'],
                'longitude': bd['lng'],
                'address': bd['addr'],
                'input_cable': input_cable,
                'input_fiber_number': input_fiber,
                'expected_power_dbm': expected_pwr,
                'measured_power_dbm': round(
                    expected_pwr + random.uniform(-0.5, 0.5), 1),
                'splice_in': splitter.splice_in,
                'status': 'active',
            })
            boxes_map[bd['code']] = box
            self.stdout.write(
                f'  {box.code}: {box.name[:45]:45s} | '
                f'Fibra: {input_fiber} de {input_cable.code if input_cable else "N/A"} | '
                f'PWR: {expected_pwr:.2f} dBm'
            )

        # ============================================================
        # 9. CREAR CLIENTES (161 clientes)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 9. Creando Clientes ---'))
        name_idx = 0
        total_clients = 0
        for bd in BOXES_DATA:
            box = boxes_map[bd['code']]
            zone_prefix = bd['zone'].split('-')[1]
            feeder_km = feeder_map[f'CBL-FDR-{zone_prefix}'].length_m / 1000.0
            dist_km = dist_map[f'CBL-DST-{zone_prefix}'].length_m / 1000.0
            # Encontrar drop length para esta caja
            drop_km = 0.15
            for dd in DROP_CABLES_DATA:
                for bc, fn in dd['boxes']:
                    if bc == bd['code']:
                        drop_km = dd['length_m'] / 1000.0
                        break
            num_clients = random.randint(4, 7)
            for port in range(1, num_clients + 1):
                fn = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
                ln1 = LAST_NAMES[name_idx % len(LAST_NAMES)]
                ln2 = LAST_NAMES[(name_idx + 3) % len(LAST_NAMES)]
                client_drop_m = random.randint(15, 40)
                expected_pwr = calc_power_at_client(
                    OLT_OUTPUT_POWER_DBM, feeder_km, dist_km, drop_km,
                    client_drop_km=client_drop_m / 1000.0
                )
                measured_rx = round(expected_pwr + random.uniform(-2.0, 1.0), 1)
                Client.objects.get_or_create(
                    client_code=f'CLI-{total_clients + 1:04d}',
                    defaults={
                        'full_name': f'{fn} {ln1} {ln2}',
                        'address': (
                            f'{box.address} (Piso {port}, Puerta {port})'
                        ),
                        'latitude': round(
                            box.latitude + random.uniform(-0.0003, 0.0003), 6),
                        'longitude': round(
                            box.longitude + random.uniform(-0.0003, 0.0003), 6),
                        'box': box,
                        'box_port': port,
                        'olt_port': box.splitter.input_port_olt,
                        'drop_fiber_number': port,
                        'expected_power_dbm': expected_pwr,
                        'status': 'active',
                        'optical_power_rx': measured_rx,
                        'optical_power_tx': round(random.uniform(0.5, 4.0), 1),
                    })
                name_idx += 1
                total_clients += 1

        self.stdout.write(f'  Total clientes creados: {total_clients}')

        # ============================================================
        # 10. CREAR FIBER ASSIGNMENTS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 10. Creando FiberAssignments ---'))
        fa_count = 0

        # Feeder fiber #1 -> cada empalme
        for fd in FEEDER_CABLES_DATA:
            splice_code = f'SPC-{fd["zone"].split("-")[1]}'
            splice = splices_map[splice_code]
            fa, _ = FiberAssignment.objects.get_or_create(
                cable=feeder_map[fd['code']],
                fiber_number=1,
                defaults={
                    'splitter': None,
                    'box': None,
                    'client': None,
                    'from_splice': None,
                    'from_splitter_port': None,
                    'status': 'active',
                    'notes': f'Feeder {fd["code"]} fibra 1 -> {splice_code}',
                })
            fa_count += 1

        # Distribution fiber #1 -> cada splitter
        for sd in SPLITTERS_DATA:
            dist_cable = dist_map[sd['dist']]
            splitter = splitters_map[sd['code']]
            fa, _ = FiberAssignment.objects.get_or_create(
                cable=dist_cable,
                fiber_number=1,
                defaults={
                    'splitter': splitter,
                    'box': None,
                    'client': None,
                    'from_splice': splitter.splice_in,
                    'from_splitter_port': None,
                    'status': 'active',
                    'notes': f'Distribution {sd["dist"]} fibra 1 -> {sd["code"]}',
                })
            fa_count += 1

        # Drop fibers -> cajas
        for dd in DROP_CABLES_DATA:
            drop_cable = drop_map[dd['code']]
            for box_code, fiber_num in dd['boxes']:
                box = boxes_map[box_code]
                fa, _ = FiberAssignment.objects.get_or_create(
                    cable=drop_cable,
                    fiber_number=fiber_num,
                    defaults={
                        'splitter': None,
                        'box': box,
                        'client': None,
                        'from_splice': box.splice_in,
                        'from_splitter_port': box.splitter_port,
                        'status': 'active',
                        'notes': f'Drop {dd["code"]} fibra {fiber_num} -> {box_code}',
                    })
                fa_count += 1

        self.stdout.write(f'  FiberAssignments creadas: {fa_count}')

        # ============================================================
        # 11. CREAR CABLE SEGMENTS CON RUTAS GPS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO(
            '--- 11. Creando CableSegments con rutas GPS ---'))
        seg_count = 0

        # Feeder segments: OLT -> cada empalme
        for fd in FEEDER_CABLES_DATA:
            zone_prefix = fd['zone'].split('-')[1]
            splice_code = f'SPC-{zone_prefix}'
            splice = splices_map[splice_code]
            route = generate_route(
                olt.latitude, olt.longitude,
                splice.latitude, splice.longitude, num_points=4
            )
            seg, _ = CableSegment.objects.get_or_create(
                cable=feeder_map[fd['code']],
                segment_type='olt_to_splice',
                from_olt=olt,
                to_splice=splice,
                defaults={
                    'fiber_numbers': '1',
                    'length_m': fd['length_m'],
                    'route_coordinates': json.dumps(route),
                    'attenuation_db': calc_attenuation(
                        fd['length_m'] / 1000.0, connectors=2, splices=1),
                    'notes': f'Feeder: OLT -> {splice_code}',
                })
            seg_count += 1

        # Distribution segments: Empalme -> Splitter
        for dd in DISTRIBUTION_CABLES_DATA:
            splice = splices_map[dd['splice']]
            splitter_code = f'SPL-{dd["zone"].split("-")[1]}-01'
            splitter = splitters_map[splitter_code]
            route = generate_route(
                splice.latitude, splice.longitude,
                splitter.latitude, splitter.longitude, num_points=3
            )
            seg, _ = CableSegment.objects.get_or_create(
                cable=dist_map[dd['code']],
                segment_type='splice_to_splitter',
                from_splice=splice,
                to_splitter=splitter,
                defaults={
                    'fiber_numbers': '1',
                    'length_m': dd['length_m'],
                    'route_coordinates': json.dumps(route),
                    'attenuation_db': calc_attenuation(
                        dd['length_m'] / 1000.0, connectors=2, splices=1),
                    'notes': f'Distribution: {dd["splice"]} -> {splitter_code}',
                })
            seg_count += 1

        # Drop segments: Splitter -> Cajas
        for dd in DROP_CABLES_DATA:
            splitter = splitters_map[dd['splitter']]
            first_box = boxes_map[dd['boxes'][0][0]]
            last_box = boxes_map[dd['boxes'][-1][0]]
            route = generate_route(
                splitter.latitude, splitter.longitude,
                last_box.latitude, last_box.longitude, num_points=3
            )
            fiber_nums = ','.join(str(b[1]) for b in dd['boxes'])
            seg, _ = CableSegment.objects.get_or_create(
                cable=drop_map[dd['code']],
                segment_type='splitter_to_box',
                from_splitter=splitter,
                to_box=first_box,
                defaults={
                    'fiber_numbers': fiber_nums,
                    'length_m': dd['length_m'],
                    'route_coordinates': json.dumps(route),
                    'attenuation_db': calc_attenuation(
                        dd['length_m'] / 1000.0, connectors=2, splices=1),
                    'notes': (
                        f'Drop: {dd["splitter"]} -> '
                        f'{", ".join(b[0] for b in dd["boxes"])}'
                    ),
                })
            seg_count += 1

        # Box-to-client segments
        self.stdout.write(self.style.HTTP_INFO(
            '--- 11b. Creando segmentos Caja->Cliente ---'))
        for bd in BOXES_DATA:
            box = boxes_map[bd['code']]
            clients = Client.objects.filter(box=box).order_by('client_code')
            for cli in clients:
                route = generate_route(
                    box.latitude, box.longitude,
                    cli.latitude, cli.longitude, num_points=1
                )
                drop_len_m = random.randint(15, 40)
                seg, _ = CableSegment.objects.get_or_create(
                    cable=box.input_cable,
                    segment_type='box_to_client',
                    from_box=box,
                    to_client=cli,
                    defaults={
                        'fiber_numbers': str(cli.box_port),
                        'length_m': drop_len_m,
                        'route_coordinates': json.dumps(route),
                        'attenuation_db': calc_attenuation(
                            drop_len_m / 1000.0, connectors=2, splices=1),
                        'notes': (
                            f'Drop: {box.code} puerto {cli.box_port} '
                            f'-> {cli.client_code}'
                        ),
                    })
                seg_count += 1

        self.stdout.write(f'  Total CableSegments: {seg_count}')

        # ============================================================
        # RESUMEN FINAL
        # ============================================================
        self._print_summary(
            olt, zones_map, splices_map, feeder_map, dist_map,
            splitters_map, drop_map, boxes_map, total_clients,
            fa_count, seg_count
        )

    def _print_summary(self, olt, zones_map, splices_map, feeder_map, dist_map,
                       splitters_map, drop_map, boxes_map, total_clients,
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
            f'    Empalmes:    {len(splices_map)}\n'
            f'    Feeders:     {len(feeder_map)}  (144 fibras cada uno)\n'
            f'    Distrib.:    {len(dist_map)}  (72 fibras cada uno)\n'
            f'    Splitters:   {len(splitters_map)}  '
            f'(1x32, -{ATT_SPLITTER_1X32_DB} dB)\n'
            f'    Drops:       {len(drop_map)}  (12 fibras cada uno)\n'
            f'    Cajas CTO:   {len(boxes_map)}\n'
            f'    Clientes:    {total_clients}\n'
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
            zp = zc.split('-')[1]
            feeder = feeder_map[f'CBL-FDR-{zp}']
            splice = splices_map[f'SPC-{zp}']
            splitter = splitters_map[f'SPL-{zp}-01']
            dist = dist_map[f'CBL-DST-{zp}']
            f_km = feeder.length_m / 1000.0
            d_km = dist.length_m / 1000.0
            p_splice = calc_power_to_splice(OLT_OUTPUT_POWER_DBM, f_km)
            p_split_in = calc_power_to_splitter(
                OLT_OUTPUT_POWER_DBM, f_km, d_km)
            p_split_out = round(p_split_in - ATT_SPLITTER_1X32_DB, 2)
            box_pwrs = []
            n_cli_zone = 0
            for bd in BOXES_DATA:
                if bd['zone'] == zc:
                    n_cli_zone += 1
                    drop_km = 0.15
                    for dd in DROP_CABLES_DATA:
                        for bc, fn in dd['boxes']:
                            if bc == bd['code']:
                                drop_km = dd['length_m'] / 1000.0
                                break
                    box_pwrs.append(calc_power_at_box(
                        OLT_OUTPUT_POWER_DBM, f_km, d_km, drop_km))
            n_clients = Client.objects.filter(box__zone__code=zc).count()
            self.stdout.write(
                f'    {zc} ({zd["name"]}):\n'
                f'      Feeder: {feeder.length_m}m | '
                f'Dist: {dist.length_m}m\n'
                f'      Empalme:     {p_splice:.2f} dBm\n'
                f'      Splitter IN: {p_split_in:.2f} dBm | '
                f'OUT: {p_split_out:.2f} dBm\n'
                f'      Cajas: {n_cli_zone} | '
                f'Rango PWR cajas: {min(box_pwrs):.2f} a {max(box_pwrs):.2f} dBm\n'
                f'      Clientes: {n_clients}'
            )

        ex_feed = 0.6
        ex_dist = 0.8
        ex_drop = 0.15
        ex_cli = 0.025
        att_f = calc_attenuation(ex_feed, 2, 1)
        att_d = calc_attenuation(ex_dist, 2, 1)
        att_dr = calc_attenuation(ex_drop, 2, 1)
        att_cli = calc_attenuation(ex_cli, 2, 1)
        pwr_box = calc_power_at_box(OLT_OUTPUT_POWER_DBM, ex_feed, ex_dist, ex_drop)
        pwr_cli = calc_power_at_client(
            OLT_OUTPUT_POWER_DBM, ex_feed, ex_dist, ex_drop, ex_cli)

        self.stdout.write(self.style.SUCCESS(
            f'\n  EJEMPLO CALCULO DETALLADO (CTO-001, La Era):\n'
            f'    OLT salida:     +{OLT_OUTPUT_POWER_DBM:.1f} dBm\n'
            f'    - Feeder {ex_feed}km:  {att_f:.2f} dB '
            f'({att_fiber(ex_feed):.2f} fibra + {att_connectors(2):.1f} '
            f'conectores + {att_splices(1):.1f} empalme)\n'
            f'    - Dist.  {ex_dist}km:  {att_d:.2f} dB '
            f'({att_fiber(ex_dist):.2f} fibra + {att_connectors(2):.1f} '
            f'conectores + {att_splices(1):.1f} empalme)\n'
            f'    - Splitter:      {ATT_SPLITTER_1X32_DB:.1f} dB\n'
            f'    - Drop   {ex_drop}km: {att_dr:.2f} dB '
            f'({att_fiber(ex_drop):.2f} fibra + {att_connectors(2):.1f} '
            f'conectores + {att_splices(1):.1f} empalme)\n'
            f'    = PWR en caja:   {pwr_box:.2f} dBm\n'
            f'    = PWR en cliente ({int(ex_cli*1000)}m drop): '
            f'{pwr_cli:.2f} dBm'
        ))

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
