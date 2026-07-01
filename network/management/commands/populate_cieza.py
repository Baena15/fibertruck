"""
FiberTruck - Comando para poblar la base de datos con datos REALISTAS
de un despliegue FTTH en Cieza, Murcia.

Topologia completa:
  OLT -> Cable Feeder (144f) -> SpliceClosure (5) -> Cable Distribution (72f) 
       -> Splitter (1x32) -> Cable Drop (12f) -> FiberBox/CTO (29) -> Client (161)

Calculos opticos basados en:
  - Atenuacion fibra monomodo: 0.35 dB/km @ 1490nm
  - Atenuacion conector: 0.5 dB cada uno
  - Atenuacion empalme: 0.1 dB cada uno
  - Atenuacion splitter 1x32: 16.5 dB (tipico)
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

# ============================================================
# DATOS DE ZONAS
# ============================================================
ZONES_DATA = [
    {'name': 'La Era - La Asuncion', 'code': 'Z-ERA', 'description': 'Casco historico y zona suroeste de Cieza. Barrio mas antiguo con calles estrechas.', 'lat': 38.2375, 'lng': -1.4195, 'population': 6300},
    {'name': 'San Jose Obrero', 'code': 'Z-SJOR', 'description': 'Zona sureste de Cieza. Barrio humilde con alta densidad. Atravesado por la Rambla del Realejo.', 'lat': 38.2395, 'lng': -1.4150, 'population': 7249},
    {'name': 'San Joaquin', 'code': 'Z-SJOA', 'description': 'Centro urbano de Cieza. Zona comercial y de servicios principales. Calles anchas y edificios de 4-6 plantas.', 'lat': 38.2390, 'lng': -1.4175, 'population': 5800},
    {'name': 'San Juan Bosco', 'code': 'Z-SJBO', 'description': 'Zona noreste, barrio mas moderno. Edificios de 10-20 anos de antiguedad.', 'lat': 38.2420, 'lng': -1.4140, 'population': 9479},
    {'name': 'La Horta', 'code': 'Z-HORT', 'description': 'Zona norte y noroeste. Mezcla de viviendas nuevas y zona suburbanizada.', 'lat': 38.2440, 'lng': -1.4180, 'population': 4230},
]

# ============================================================
# DATOS DE OLT
# ============================================================
OLT_DATA = {
    'name': 'OLT-CIEZA-01',
    'code': 'OLT-CIEZA-01',
    'address': 'Calle Mayor, 45 - Centro de Datos Municipal, Cieza (Murcia)',
    'lat': 38.2390,
    'lng': -1.4175,
    'max_ports': 16,
    'output_power_dbm': OLT_OUTPUT_POWER_DBM,
    'splitter_ratio': '1x32',
}

# ============================================================
# DATOS DE EMPALMES (SpliceClosure)
# ============================================================
SPLICES_DATA = [
    {'code': 'SPC-ERA', 'name': 'Empalme La Era', 'zone_code': 'Z-ERA', 'closure_type': 'dome', 'lat': 38.2375, 'lng': -1.4195, 'address': 'C/ Real, 15, La Era, Cieza', 'fiber_capacity': 144},
    {'code': 'SPC-SJOR', 'name': 'Empalme San Jose', 'zone_code': 'Z-SJOR', 'closure_type': 'dome', 'lat': 38.2395, 'lng': -1.4150, 'address': 'Avda. Juan Carlos I, 40, San Jose, Cieza', 'fiber_capacity': 144},
    {'code': 'SPC-SJOA', 'name': 'Empalme San Joaquin', 'zone_code': 'Z-SJOA', 'closure_type': 'inline', 'lat': 38.2390, 'lng': -1.4175, 'address': 'C/ Marques de Camachos, 10, San Joaquin, Cieza', 'fiber_capacity': 144},
    {'code': 'SPC-SJBO', 'name': 'Empalme San Juan Bosco', 'zone_code': 'Z-SJBO', 'closure_type': 'dome', 'lat': 38.2420, 'lng': -1.4140, 'address': 'Avda. de Murcia, 75, San Juan Bosco, Cieza', 'fiber_capacity': 144},
    {'code': 'SPC-HORT', 'name': 'Empalme La Horta', 'zone_code': 'Z-HORT', 'closure_type': 'dome', 'lat': 38.2440, 'lng': -1.4180, 'address': 'C/ Santiago, 8, La Horta, Cieza', 'fiber_capacity': 144},
]

# ============================================================
# DATOS DE CABLES FEEDER (Central -> Empalme)
# ============================================================
FEEDER_CABLE = {
    'code': 'CBL-FDR-01',
    'name': 'Cable Feeder Principal Cieza',
    'cable_type': 'feeder',
    'fiber_count': 144,
    'length_m': 3500,
}

# ============================================================
# DATOS DE CABLES DISTRIBUTION (Empalme -> Splitter)
# ============================================================
DISTRIBUTION_CABLES = [
    {'code': 'CBL-DST-ERA', 'name': 'Distribution La Era', 'zone_code': 'Z-ERA', 'cable_type': 'distribution', 'fiber_count': 72, 'length_m': 800, 'splice_code': 'SPC-ERA'},
    {'code': 'CBL-DST-SJOR', 'name': 'Distribution San Jose', 'zone_code': 'Z-SJOR', 'cable_type': 'distribution', 'fiber_count': 72, 'length_m': 650, 'splice_code': 'SPC-SJOR'},
    {'code': 'CBL-DST-SJOA', 'name': 'Distribution San Joaquin', 'zone_code': 'Z-SJOA', 'cable_type': 'distribution', 'fiber_count': 72, 'length_m': 500, 'splice_code': 'SPC-SJOA'},
    {'code': 'CBL-DST-SJBO', 'name': 'Distribution San Juan Bosco', 'zone_code': 'Z-SJBO', 'cable_type': 'distribution', 'fiber_count': 72, 'length_m': 900, 'splice_code': 'SPC-SJBO'},
    {'code': 'CBL-DST-HORT', 'name': 'Distribution La Horta', 'zone_code': 'Z-HORT', 'cable_type': 'distribution', 'fiber_count': 72, 'length_m': 700, 'splice_code': 'SPC-HORT'},
]

# ============================================================
# DATOS DE SPLITTERS
# ============================================================
SPLITTERS_DATA = [
    {'code': 'SPL-ERA-01', 'name': 'Splitter La Era', 'zone_code': 'Z-ERA', 'ratio': '1x32', 'port': 1, 'lat': 38.2376, 'lng': -1.4193, 'splice_code': 'SPC-ERA', 'dist_cable': 'CBL-DST-ERA', 'dist_fiber': 1},
    {'code': 'SPL-SJOR-01', 'name': 'Splitter San Jose', 'zone_code': 'Z-SJOR', 'ratio': '1x32', 'port': 2, 'lat': 38.2396, 'lng': -1.4148, 'splice_code': 'SPC-SJOR', 'dist_cable': 'CBL-DST-SJOR', 'dist_fiber': 1},
    {'code': 'SPL-SJOA-01', 'name': 'Splitter San Joaquin Central', 'zone_code': 'Z-SJOA', 'ratio': '1x32', 'port': 3, 'lat': 38.2391, 'lng': -1.4173, 'splice_code': 'SPC-SJOA', 'dist_cable': 'CBL-DST-SJOA', 'dist_fiber': 1},
    {'code': 'SPL-SJBO-01', 'name': 'Splitter San Juan Bosco', 'zone_code': 'Z-SJBO', 'ratio': '1x32', 'port': 4, 'lat': 38.2421, 'lng': -1.4138, 'splice_code': 'SPC-SJBO', 'dist_cable': 'CBL-DST-SJBO', 'dist_fiber': 1},
    {'code': 'SPL-HORT-01', 'name': 'Splitter La Horta', 'zone_code': 'Z-HORT', 'ratio': '1x32', 'port': 5, 'lat': 38.2441, 'lng': -1.4178, 'splice_code': 'SPC-HORT', 'dist_cable': 'CBL-DST-HORT', 'dist_fiber': 1},
]

# ============================================================
# DATOS DE CAJAS CTO (29 cajas)
# ============================================================
BOXES_DATA = [
    # --- La Era (5 cajas) ---
    {'code': 'CTO-001', 'name': 'Caja La Era - Plaza Constitucion', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 1, 'lat': 38.2378, 'lng': -1.4198, 'address': 'Plaza de la Constitucion, 5'},
    {'code': 'CTO-002', 'name': 'Caja La Era - C/ Real', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 2, 'lat': 38.2372, 'lng': -1.4190, 'address': 'Calle Real, 23'},
    {'code': 'CTO-003', 'name': 'Caja La Era - Museo Siyasa', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 3, 'lat': 38.2370, 'lng': -1.4205, 'address': 'Avda. del Mediterraneo, 55'},
    {'code': 'CTO-004', 'name': 'Caja La Era - C/ Espinosa', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 4, 'lat': 38.2380, 'lng': -1.4185, 'address': 'Calle Espinosa, 12'},
    {'code': 'CTO-005', 'name': 'Caja La Era - C/ Colon', 'zone': 'Z-ERA', 'splitter': 'SPL-ERA-01', 'port': 5, 'lat': 38.2368, 'lng': -1.4195, 'address': 'Calle Colon, 34'},
    # --- San Jose (6 cajas) ---
    {'code': 'CTO-010', 'name': 'Caja San Jose - C/ Murcia', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 1, 'lat': 38.2398, 'lng': -1.4155, 'address': 'Calle Murcia, 18'},
    {'code': 'CTO-011', 'name': 'Caja San Jose - Centro Cultural', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 2, 'lat': 38.2392, 'lng': -1.4145, 'address': 'Calle Generos de Punto'},
    {'code': 'CTO-012', 'name': 'Caja San Jose - C/ Albacete', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 3, 'lat': 38.2402, 'lng': -1.4148, 'address': 'Calle Albacete, 42'},
    {'code': 'CTO-013', 'name': 'Caja San Jose - Avda. Juan Carlos I', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 4, 'lat': 38.2405, 'lng': -1.4158, 'address': 'Avda. Juan Carlos I, 67'},
    {'code': 'CTO-014', 'name': 'Caja San Jose - C/ Granada', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 5, 'lat': 38.2390, 'lng': -1.4162, 'address': 'Calle Granada, 9'},
    {'code': 'CTO-015', 'name': 'Caja San Jose - C/ Jaen', 'zone': 'Z-SJOR', 'splitter': 'SPL-SJOR-01', 'port': 6, 'lat': 38.2400, 'lng': -1.4138, 'address': 'Calle Jaen, 28'},
    # --- San Joaquin (6 cajas) ---
    {'code': 'CTO-020', 'name': 'Caja San Joaquin - Plaza de Espana', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 1, 'lat': 38.2392, 'lng': -1.4180, 'address': 'Plaza de Espana, 1'},
    {'code': 'CTO-021', 'name': 'Caja San Joaquin - Mercado Abastos', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 2, 'lat': 38.2385, 'lng': -1.4170, 'address': 'Calle del Mercado, 10'},
    {'code': 'CTO-022', 'name': 'Caja San Joaquin - Biblioteca Salmeron', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 3, 'lat': 38.2395, 'lng': -1.4172, 'address': 'Calle Fray Pascual Salmeron, 3'},
    {'code': 'CTO-023', 'name': 'Caja San Joaquin - Oficina Turismo', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 4, 'lat': 38.2388, 'lng': -1.4185, 'address': 'Plaza de Espana, 8'},
    {'code': 'CTO-024', 'name': 'Caja San Joaquin - C/ Marques de Camachos', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 5, 'lat': 38.2398, 'lng': -1.4168, 'address': 'Calle Marques de Camachos, 45'},
    {'code': 'CTO-025', 'name': 'Caja San Joaquin - Delegacion Hacienda', 'zone': 'Z-SJOA', 'splitter': 'SPL-SJOA-01', 'port': 6, 'lat': 38.2382, 'lng': -1.4178, 'address': 'Avda. de Murcia, 12'},
    # --- San Juan Bosco (7 cajas) ---
    {'code': 'CTO-030', 'name': 'Caja S.J. Bosco - Piscina Cubierta', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 1, 'lat': 38.2415, 'lng': -1.4135, 'address': 'Calle Pintor Villodres'},
    {'code': 'CTO-031', 'name': 'Caja S.J. Bosco - IES Diego Tortosa', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 2, 'lat': 38.2425, 'lng': -1.4130, 'address': 'Avda. de Murcia, 80'},
    {'code': 'CTO-032', 'name': 'Caja S.J. Bosco - Centro Salud Zona Este', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 3, 'lat': 38.2420, 'lng': -1.4145, 'address': 'Calle Molino de Papel, 15'},
    {'code': 'CTO-033', 'name': 'Caja S.J. Bosco - Palacio Justicia', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 4, 'lat': 38.2410, 'lng': -1.4155, 'address': 'Calle Urano, 2'},
    {'code': 'CTO-034', 'name': 'Caja S.J. Bosco - Estacion Autobuses', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 5, 'lat': 38.2430, 'lng': -1.4140, 'address': 'Calle Federico Garcia Lorca, 1'},
    {'code': 'CTO-035', 'name': 'Caja S.J. Bosco - C/ Beniel', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 6, 'lat': 38.2428, 'lng': -1.4125, 'address': 'Calle Beniel, 33'},
    {'code': 'CTO-036', 'name': 'Caja S.J. Bosco - Avda. Alcantarilla', 'zone': 'Z-SJBO', 'splitter': 'SPL-SJBO-01', 'port': 7, 'lat': 38.2412, 'lng': -1.4130, 'address': 'Avda. de Alcantarilla, 55'},
    # --- La Horta (5 cajas) ---
    {'code': 'CTO-040', 'name': 'Caja La Horta - Auditorio Gabriel Celaya', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 1, 'lat': 38.2435, 'lng': -1.4185, 'address': 'Calle Rio Segura, 20'},
    {'code': 'CTO-041', 'name': 'Caja La Horta - Escuela Idiomas', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 2, 'lat': 38.2442, 'lng': -1.4175, 'address': 'Calle Santiago, 12'},
    {'code': 'CTO-042', 'name': 'Caja La Horta - C/ San Cristobal', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 3, 'lat': 38.2445, 'lng': -1.4190, 'address': 'Calle San Cristobal, 44'},
    {'code': 'CTO-043', 'name': 'Caja La Horta - Cabezo Fuensantilla', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 4, 'lat': 38.2450, 'lng': -1.4180, 'address': 'Camino del Cabezo, 8'},
    {'code': 'CTO-044', 'name': 'Caja La Horta - C/ Poligono Industrial', 'zone': 'Z-HORT', 'splitter': 'SPL-HORT-01', 'port': 5, 'lat': 38.2430, 'lng': -1.4165, 'address': 'Calle Industrial, 15'},
]

# ============================================================
# DATOS DE CABLES DROP (Splitter -> Grupo de Cajas)
# ============================================================
DROP_CABLES = [
    # --- La Era: 2 cables drop ---
    {'code': 'CBL-DRP-ERA-01', 'name': 'Drop La Era Grupo 1', 'zone_code': 'Z-ERA', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 150,
     'splitter_code': 'SPL-ERA-01', 'boxes': [('CTO-001', 1), ('CTO-002', 2), ('CTO-003', 3)]},
    {'code': 'CBL-DRP-ERA-02', 'name': 'Drop La Era Grupo 2', 'zone_code': 'Z-ERA', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 200,
     'splitter_code': 'SPL-ERA-01', 'boxes': [('CTO-004', 1), ('CTO-005', 2)]},
    # --- San Jose: 2 cables drop ---
    {'code': 'CBL-DRP-SJOR-01', 'name': 'Drop San Jose Grupo 1', 'zone_code': 'Z-SJOR', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 180,
     'splitter_code': 'SPL-SJOR-01', 'boxes': [('CTO-010', 1), ('CTO-011', 2), ('CTO-012', 3)]},
    {'code': 'CBL-DRP-SJOR-02', 'name': 'Drop San Jose Grupo 2', 'zone_code': 'Z-SJOR', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 220,
     'splitter_code': 'SPL-SJOR-01', 'boxes': [('CTO-013', 1), ('CTO-014', 2), ('CTO-015', 3)]},
    # --- San Joaquin: 2 cables drop ---
    {'code': 'CBL-DRP-SJOA-01', 'name': 'Drop San Joaquin Grupo 1', 'zone_code': 'Z-SJOA', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 120,
     'splitter_code': 'SPL-SJOA-01', 'boxes': [('CTO-020', 1), ('CTO-021', 2), ('CTO-022', 3)]},
    {'code': 'CBL-DRP-SJOA-02', 'name': 'Drop San Joaquin Grupo 2', 'zone_code': 'Z-SJOA', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 160,
     'splitter_code': 'SPL-SJOA-01', 'boxes': [('CTO-023', 1), ('CTO-024', 2), ('CTO-025', 3)]},
    # --- San Juan Bosco: 3 cables drop ---
    {'code': 'CBL-DRP-SJBO-01', 'name': 'Drop S.J. Bosco Grupo 1', 'zone_code': 'Z-SJBO', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 140,
     'splitter_code': 'SPL-SJBO-01', 'boxes': [('CTO-030', 1), ('CTO-031', 2), ('CTO-032', 3)]},
    {'code': 'CBL-DRP-SJBO-02', 'name': 'Drop S.J. Bosco Grupo 2', 'zone_code': 'Z-SJBO', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 170,
     'splitter_code': 'SPL-SJBO-01', 'boxes': [('CTO-033', 1), ('CTO-034', 2), ('CTO-035', 3)]},
    {'code': 'CBL-DRP-SJBO-03', 'name': 'Drop S.J. Bosco Grupo 3', 'zone_code': 'Z-SJBO', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 130,
     'splitter_code': 'SPL-SJBO-01', 'boxes': [('CTO-036', 1)]},
    # --- La Horta: 2 cables drop ---
    {'code': 'CBL-DRP-HORT-01', 'name': 'Drop La Horta Grupo 1', 'zone_code': 'Z-HORT', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 190,
     'splitter_code': 'SPL-HORT-01', 'boxes': [('CTO-040', 1), ('CTO-041', 2), ('CTO-042', 3)]},
    {'code': 'CBL-DRP-HORT-02', 'name': 'Drop La Horta Grupo 2', 'zone_code': 'Z-HORT', 'cable_type': 'drop', 'fiber_count': 12, 'length_m': 210,
     'splitter_code': 'SPL-HORT-01', 'boxes': [('CTO-043', 1), ('CTO-044', 2)]},
]

# ============================================================
# RUTAS GPS POR CALLES REALES DE CIEZA
# ============================================================
# Coordenadas intermedias que siguen calles reales
ROUTES = {
    # Feeder: Central (Calle Mayor, 45) -> SPC-ERA (C/ Real, 15)
    'feeder_era': [
        [38.2390, -1.4175],   # Central OLT
        [38.2385, -1.4180],   # C/ Espinosa
        [38.2380, -1.4185],   # C/ Espinosa continua
        [38.2378, -1.4190],   # C/ Real
        [38.2375, -1.4195],   # SPC-ERA
    ],
    # Feeder: Central -> SPC-SJOR (Avda. Juan Carlos I, 40)
    'feeder_sjor': [
        [38.2390, -1.4175],   # Central OLT
        [38.2392, -1.4170],   # C/ Marques de Camachos
        [38.2393, -1.4165],   # Plaza de Espana
        [38.2394, -1.4160],   # C/ Granada
        [38.2395, -1.4155],   # Avda. de Murcia
        [38.2395, -1.4150],   # SPC-SJOR
    ],
    # Feeder: Central -> SPC-SJOA (C/ Marques de Camachos, 10)
    'feeder_sjoa': [
        [38.2390, -1.4175],   # Central OLT
        [38.2390, -1.4175],   # Mismo edificio - empalme en central
    ],
    # Feeder: Central -> SPC-SJBO (Avda. de Murcia, 75)
    'feeder_sjbo': [
        [38.2390, -1.4175],   # Central OLT
        [38.2395, -1.4170],   # Avda. de Murcia
        [38.2405, -1.4160],   # Avda. de Murcia continua
        [38.2415, -1.4150],   # Avda. de Murcia continua
        [38.2420, -1.4140],   # SPC-SJBO
    ],
    # Feeder: Central -> SPC-HORT (C/ Santiago, 8)
    'feeder_hort': [
        [38.2390, -1.4175],   # Central OLT
        [38.2395, -1.4178],   # C/ Santiago
        [38.2405, -1.4180],   # C/ Santiago continua
        [38.2415, -1.4182],   # C/ Santiago continua
        [38.2425, -1.4183],   # C/ Santiago continua
        [38.2440, -1.4180],   # SPC-HORT
    ],
    # Distribution: SPC-ERA -> SPL-ERA-01
    'dist_era': [
        [38.2375, -1.4195],   # SPC-ERA
        [38.23755, -1.4194],  # Plaza Constitucion
        [38.23758, -1.41935], # Plaza Constitucion
        [38.2376, -1.4193],   # SPL-ERA-01
    ],
    # Distribution: SPC-SJOR -> SPL-SJOR-01
    'dist_sjor': [
        [38.2395, -1.4150],   # SPC-SJOR
        [38.23952, -1.41495], # Avda. Juan Carlos I
        [38.23955, -1.4149],  # Avda. Juan Carlos I
        [38.2396, -1.4148],   # SPL-SJOR-01
    ],
    # Distribution: SPC-SJOA -> SPL-SJOA-01
    'dist_sjoa': [
        [38.2390, -1.4175],   # SPC-SJOA
        [38.23902, -1.41745], # C/ Marques de Camachos
        [38.23905, -1.4174],  # C/ Marques de Camachos
        [38.2391, -1.4173],   # SPL-SJOA-01
    ],
    # Distribution: SPC-SJBO -> SPL-SJBO-01
    'dist_sjbo': [
        [38.2420, -1.4140],   # SPC-SJBO
        [38.24202, -1.41395], # Avda. de Murcia
        [38.24205, -1.4139],  # Avda. de Murcia
        [38.2421, -1.4138],   # SPL-SJBO-01
    ],
    # Distribution: SPC-HORT -> SPL-HORT-01
    'dist_hort': [
        [38.2440, -1.4180],   # SPC-HORT
        [38.24402, -1.41795], # C/ Santiago
        [38.24405, -1.4179],  # C/ Santiago
        [38.2441, -1.4178],   # SPL-HORT-01
    ],
    # Drop: SPL-ERA-01 -> CTO-001,002,003
    'drop_era_01': [
        [38.2376, -1.4193],   # SPL-ERA-01
        [38.23765, -1.41945], # C/ Real
        [38.2377, -1.41955],  # C/ Real continua
        [38.23778, -1.4198],  # CTO-001
    ],
    # Drop: SPL-ERA-01 -> CTO-004,005
    'drop_era_02': [
        [38.2376, -1.4193],   # SPL-ERA-01
        [38.23765, -1.4192],  # C/ Espinosa
        [38.2377, -1.4191],   # C/ Espinosa continua
        [38.2378, -1.4185],   # CTO-004 (C/ Espinosa, 12)
    ],
    # Drop: SPL-SJOR-01 -> CTO-010,011,012
    'drop_sjor_01': [
        [38.2396, -1.4148],   # SPL-SJOR-01
        [38.23965, -1.4149],  # C/ Murcia
        [38.2397, -1.4150],   # C/ Murcia continua
        [38.2398, -1.4155],   # CTO-010
    ],
    # Drop: SPL-SJOR-01 -> CTO-013,014,015
    'drop_sjor_02': [
        [38.2396, -1.4148],   # SPL-SJOR-01
        [38.23955, -1.4147],  # Avda. Juan Carlos I
        [38.2395, -1.4146],   # Avda. Juan Carlos I continua
        [38.2405, -1.4158],   # CTO-013
    ],
    # Drop: SPL-SJOA-01 -> CTO-020,021,022
    'drop_sjoa_01': [
        [38.2391, -1.4173],   # SPL-SJOA-01
        [38.23915, -1.41735], # Plaza de Espana
        [38.2392, -1.4174],   # Plaza de Espana
        [38.2392, -1.4180],   # CTO-020
    ],
    # Drop: SPL-SJOA-01 -> CTO-023,024,025
    'drop_sjoa_02': [
        [38.2391, -1.4173],   # SPL-SJOA-01
        [38.2390, -1.4172],   # C/ Marques de Camachos
        [38.2389, -1.4171],   # C/ Marques de Camachos continua
        [38.2388, -1.4185],   # CTO-023
    ],
    # Drop: SPL-SJBO-01 -> CTO-030,031,032
    'drop_sjbo_01': [
        [38.2421, -1.4138],   # SPL-SJBO-01
        [38.24215, -1.41375], # C/ Pintor Villodres
        [38.2422, -1.4137],   # C/ Pintor Villodres
        [38.2415, -1.4135],   # CTO-030
    ],
    # Drop: SPL-SJBO-01 -> CTO-033,034,035
    'drop_sjbo_02': [
        [38.2421, -1.4138],   # SPL-SJBO-01
        [38.24205, -1.41385], # C/ Urano
        [38.2420, -1.4139],   # C/ Urano continua
        [38.2410, -1.4155],   # CTO-033
    ],
    # Drop: SPL-SJBO-01 -> CTO-036
    'drop_sjbo_03': [
        [38.2421, -1.4138],   # SPL-SJBO-01
        [38.2420, -1.4137],   # Avda. Alcantarilla
        [38.2418, -1.4135],   # Avda. Alcantarilla continua
        [38.2412, -1.4130],   # CTO-036
    ],
    # Drop: SPL-HORT-01 -> CTO-040,041,042
    'drop_hort_01': [
        [38.2441, -1.4178],   # SPL-HORT-01
        [38.24415, -1.41785], # C/ Rio Segura
        [38.2442, -1.4179],   # C/ Rio Segura continua
        [38.2435, -1.4185],   # CTO-040
    ],
    # Drop: SPL-HORT-01 -> CTO-043,044
    'drop_hort_02': [
        [38.2441, -1.4178],   # SPL-HORT-01
        [38.2442, -1.4177],   # Camino del Cabezo
        [38.2444, -1.4176],   # Camino del Cabezo continua
        [38.2450, -1.4180],   # CTO-043
    ],
}

FIRST_NAMES = ['Antonio', 'Maria', 'Jose', 'Carmen', 'Francisco', 'Ana', 'Manuel', 'Isabel', 'David', 'Laura', 'Juan', 'Pilar', 'Javier', 'Dolores', 'Daniel', 'Teresa', 'Pedro', 'Rosa', 'Alejandro', 'Cristina', 'Miguel', 'Patricia', 'Rafael', 'Sofia', 'Fernando', 'Lucia', 'Luis', 'Martina', 'Pablo', 'Valentina', 'Sergio', 'Julia', 'Andres', 'Paula', 'Jorge', 'Emma', 'Alberto', 'Marta', 'Diego', 'Noa']
LAST_NAMES = ['Garcia', 'Martinez', 'Lopez', 'Sanchez', 'Rodriguez', 'Perez', 'Fernandez', 'Gonzalez', 'Gomez', 'Ruiz', 'Alvarez', 'Jimenez', 'Moreno', 'Romero', 'Hernandez', 'Diaz', 'Muñoz', 'Serrano', 'Iglesias', 'Medina', 'Cieza', 'Segura', 'Vega', 'Murcia', 'Rico', 'Blanco', 'Castillo', 'Torres']


def calc_segment_attenuation(length_km, num_connectors=2, num_splices=0):
    """Calcula atenuacion total de un tramo de cable.
    P_final = P_inicial - (at_fibra * km) - (at_conector * N) - (at_empalme * N)
    """
    att_fiber = ATT_FIBER_DB_KM * length_km
    att_connectors = ATT_CONNECTOR_DB * num_connectors
    att_splices = ATT_SPLICE_DB * num_splices
    return att_fiber + att_connectors + att_splices


def calc_power_to_splice(olt_power_dbm, feeder_length_km):
    """Calcula potencia optica en el empalme (SpliceClosure).
    Tramo: OLT -> Feeder -> Empalme
    """
    att = calc_segment_attenuation(feeder_length_km, num_connectors=2, num_splices=0)
    return round(olt_power_dbm - att, 2)


def calc_power_to_splitter(olt_power_dbm, feeder_length_km, dist_length_km):
    """Calcula potencia optica en el splitter (antes del splitter).
    Tramo: OLT -> Feeder -> Empalme -> Distribution -> Splitter
    """
    att_feeder = calc_segment_attenuation(feeder_length_km, num_connectors=2, num_splices=0)
    att_dist = calc_segment_attenuation(dist_length_km, num_connectors=2, num_splices=0)
    total_att = att_feeder + att_dist
    return round(olt_power_dbm - total_att, 2)


def calc_power_at_box(olt_power_dbm, feeder_length_km, dist_length_km, drop_length_km):
    """Calcula potencia optica esperada en la caja (CTO).
    Tramo: OLT -> Feeder -> Empalme -> Distribution -> Splitter -> Drop -> Caja
    Incluye atenuacion del splitter 1x32 (16.5 dB).
    """
    att_feeder = calc_segment_attenuation(feeder_length_km, num_connectors=2, num_splices=0)
    att_dist = calc_segment_attenuation(dist_length_km, num_connectors=2, num_splices=0)
    att_splitter = ATT_SPLITTER_1X32_DB
    att_drop = calc_segment_attenuation(drop_length_km, num_connectors=2, num_splices=0)
    total_att = att_feeder + att_dist + att_splitter + att_drop
    return round(olt_power_dbm - total_att, 2)


def calc_power_at_client(olt_power_dbm, feeder_length_km, dist_length_km, drop_length_km, client_drop_m=25):
    """Calcula potencia optica esperada en la ONT del cliente.
    Tramo completo + cable drop del cliente (tipico 25m).
    """
    att_feeder = calc_segment_attenuation(feeder_length_km, num_connectors=2, num_splices=0)
    att_dist = calc_segment_attenuation(dist_length_km, num_connectors=2, num_splices=0)
    att_splitter = ATT_SPLITTER_1X32_DB
    att_drop = calc_segment_attenuation(drop_length_km, num_connectors=2, num_splices=0)
    att_client_drop = calc_segment_attenuation(client_drop_m / 1000.0, num_connectors=2, num_splices=1)
    total_att = att_feeder + att_dist + att_splitter + att_drop + att_client_drop
    return round(olt_power_dbm - total_att, 2)


class Command(BaseCommand):
    help = 'Pobla la base de datos con el despliegue FTTH realista de Cieza, Murcia'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== FiberTruck: Despliegue FTTH Realista de Cieza, Murcia ==='))
        self.stdout.write(self.style.MIGRATE_HEADING('    Topologia: OLT -> Feeder(144f) -> Splice(5) -> Distribution(72f) -> Splitter(1x32) -> Drop(12f) -> CTO(29) -> Clientes(161)'))
        self.stdout.write('')

        # ============================================================
        # 1. CREAR OLT
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 1. Creando OLT ---'))
        olt, _ = OLT.objects.get_or_create(code=OLT_DATA['code'], defaults={
            'name': OLT_DATA['name'],
            'address': OLT_DATA['address'],
            'latitude': OLT_DATA['lat'],
            'longitude': OLT_DATA['lng'],
            'max_ports': OLT_DATA['max_ports'],
            'output_power_dbm': OLT_DATA['output_power_dbm'],
            'splitter_ratio': OLT_DATA['splitter_ratio'],
        })
        self.stdout.write(f'  OLT: {olt} | Potencia salida: {olt.output_power_dbm} dBm')

        # ============================================================
        # 2. CREAR ZONAS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 2. Creando Zonas ---'))
        zones_map = {}
        for zd in ZONES_DATA:
            zone, _ = Zone.objects.get_or_create(code=zd['code'], defaults={
                'name': zd['name'],
                'description': zd['description'],
                'latitude': zd['lat'],
                'longitude': zd['lng'],
                'population_estimate': zd['population'],
            })
            zones_map[zd['code']] = zone
            self.stdout.write(f'  Zona: {zone}')

        # ============================================================
        # 3. CREAR CABLE FEEDER PRINCIPAL (144 fibras)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 3. Creando Cable Feeder (144 fibras) ---'))
        feeder_cable, _ = FiberCable.objects.get_or_create(code=FEEDER_CABLE['code'], defaults={
            'name': FEEDER_CABLE['name'],
            'cable_type': FEEDER_CABLE['cable_type'],
            'fiber_count': FEEDER_CABLE['fiber_count'],
            'length_m': FEEDER_CABLE['length_m'],
            'description': 'Cable feeder principal desde la central OLT a los 5 empalmes de zona. Capacidad: 144 fibras monomodo G.652D.',
        })
        self.stdout.write(f'  Cable: {feeder_cable}')

        # ============================================================
        # 4. CREAR EMPALMES (SpliceClosure)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 4. Creando Empalmes (SpliceClosure) ---'))
        splices_map = {}
        for sd in SPLICES_DATA:
            zone = zones_map[sd['zone_code']]
            splice, _ = SpliceClosure.objects.get_or_create(code=sd['code'], defaults={
                'name': sd['name'],
                'closure_type': sd['closure_type'],
                'latitude': sd['lat'],
                'longitude': sd['lng'],
                'address': sd['address'],
                'zone': zone,
                'input_cable': feeder_cable,
                'fiber_capacity': sd['fiber_capacity'],
            })
            splices_map[sd['code']] = splice
            # Calcular potencia en el empalme
            feeder_len_km = FEEDER_CABLE['length_m'] / 5000.0
            power_at_splice = calc_power_to_splice(OLT_OUTPUT_POWER_DBM, feeder_len_km)
            self.stdout.write(f'  Empalme: {splice} | Potencia esperada: {power_at_splice} dBm')

        # ============================================================
        # 5. CREAR CABLES DISTRIBUTION (72 fibras cada uno)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 5. Creando Cables Distribution (72 fibras) ---'))
        dist_cables_map = {}
        for idx, dd in enumerate(DISTRIBUTION_CABLES):
            zone = zones_map[dd['zone_code']]
            splice = splices_map[dd['splice_code']]
            dist_cable, _ = FiberCable.objects.get_or_create(code=dd['code'], defaults={
                'name': dd['name'],
                'cable_type': dd['cable_type'],
                'fiber_count': dd['fiber_count'],
                'length_m': dd['length_m'],
                'description': f'Cable distribution desde {dd["splice_code"]} hasta el splitter de la zona {dd["zone_code"]}.',
            })
            dist_cables_map[dd['code']] = dist_cable
            # Asignar fibra del feeder al empalme
            FiberAssignment.objects.get_or_create(
                cable=feeder_cable,
                fiber_number=idx + 1,
                defaults={
                    'splitter': None,
                    'box': None,
                    'client': None,
                    'from_splice': splice,
                    'status': 'active',
                    'notes': f'Fibra del feeder principal al empalme {dd["splice_code"]}',
                }
            )
            # Actualizar empalme con cable de salida y fibras usadas
            splice.output_cable = dist_cable
            splice.fiber_count_used = 1
            splice.save()
            self.stdout.write(f'  Cable: {dist_cable}')

        # ============================================================
        # 6. CREAR SPLITTERS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 6. Creando Splitters (1x32) ---'))
        splitters_map = {}
        for sd in SPLITTERS_DATA:
            zone = zones_map[sd['zone_code']]
            splice = splices_map[sd['splice_code']]
            dist_cable = dist_cables_map[sd['dist_cable']]
            # Calcular potencia en el splitter
            feeder_len_km = FEEDER_CABLE['length_m'] / 5000.0
            dist_len_km = dist_cable.length_m / 1000.0
            power_at_splitter = calc_power_to_splitter(OLT_OUTPUT_POWER_DBM, feeder_len_km, dist_len_km)
            splitter, _ = Splitter.objects.get_or_create(code=sd['code'], defaults={
                'name': sd['name'],
                'ratio': sd['ratio'],
                'olt': olt,
                'zone': zone,
                'input_port_olt': sd['port'],
                'input_fiber_number': sd['dist_fiber'],
                'input_cable': dist_cable,
                'output_power_dbm': round(power_at_splitter - ATT_SPLITTER_1X32_DB, 2),
                'splice_in': splice,
                'latitude': sd['lat'],
                'longitude': sd['lng'],
                'address': f"Cerca de {sd['name']}, {zone.name}",
            })
            splitters_map[sd['code']] = splitter
            # Crear FiberAssignment: fibra #1 del distribution al splitter
            FiberAssignment.objects.get_or_create(
                cable=dist_cable,
                fiber_number=sd['dist_fiber'],
                defaults={
                    'splitter': splitter,
                    'box': None,
                    'client': None,
                    'from_splice': splice,
                    'status': 'active',
                    'notes': f'Fibra de distribution al splitter {sd["code"]}',
                }
            )
            self.stdout.write(f'  Splitter: {splitter} | Entrada: fibra {sd["dist_fiber"]} de {dist_cable.code} | Potencia entrada: {power_at_splitter} dBm | Potencia salida: {splitter.output_power_dbm} dBm')

        # ============================================================
        # 7. CREAR CABLES DROP (12 fibras)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 7. Creando Cables Drop (12 fibras) ---'))
        drop_cables_map = {}
        for dd in DROP_CABLES:
            zone = zones_map[dd['zone_code']]
            splitter = splitters_map[dd['splitter_code']]
            drop_cable, _ = FiberCable.objects.get_or_create(code=dd['code'], defaults={
                'name': dd['name'],
                'cable_type': dd['cable_type'],
                'fiber_count': dd['fiber_count'],
                'length_m': dd['length_m'],
                'description': f'Cable drop desde {dd["splitter_code"]} a cajas de la zona {dd["zone_code"]}.',
            })
            drop_cables_map[dd['code']] = drop_cable
            self.stdout.write(f'  Cable: {drop_cable} -> alimenta {len(dd["boxes"])} caja(s)')

        # ============================================================
        # 8. CREAR CAJAS CTO (29 cajas)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 8. Creando Cajas CTO (29) ---'))
        boxes_map = {}
        for bd in BOXES_DATA:
            zone = zones_map[bd['zone']]
            splitter = splitters_map[bd['splitter']]
            # Buscar cable drop y fibra asignada
            input_cable = None
            input_fiber = None
            for dd in DROP_CABLES:
                for box_code, fiber_num in dd['boxes']:
                    if box_code == bd['code']:
                        input_cable = drop_cables_map[dd['code']]
                        input_fiber = fiber_num
                        break
                if input_cable:
                    break
            # Calcular potencia esperada en caja
            feeder_len_km = FEEDER_CABLE['length_m'] / 5000.0
            dist_cable_code = splitter.input_cable.code if splitter.input_cable else None
            dist_len_km = 0.5
            if dist_cable_code and dist_cable_code in dist_cables_map:
                dist_len_km = dist_cables_map[dist_cable_code].length_m / 1000.0
            drop_len_km = input_cable.length_m / 1000.0 if input_cable else 0.15
            expected_power = calc_power_at_box(OLT_OUTPUT_POWER_DBM, feeder_len_km, dist_len_km, drop_len_km)
            box, _ = FiberBox.objects.get_or_create(code=bd['code'], defaults={
                'name': bd['name'],
                'box_type': 'CTO',
                'splitter': splitter,
                'zone': zone,
                'splitter_port': bd['port'],
                'max_capacity': 16,
                'latitude': bd['lat'],
                'longitude': bd['lng'],
                'address': bd['address'],
                'input_cable': input_cable,
                'input_fiber_number': input_fiber,
                'expected_power_dbm': expected_power,
                'measured_power_dbm': round(expected_power + random.uniform(-0.5, 0.5), 1),
                'splice_in': splitter.splice_in,
                'status': 'active',
            })
            boxes_map[bd['code']] = box
            # Crear FiberAssignment para la caja
            if input_cable and input_fiber:
                FiberAssignment.objects.get_or_create(
                    cable=input_cable,
                    fiber_number=input_fiber,
                    defaults={
                        'splitter': None,
                        'box': box,
                        'client': None,
                        'from_splice': splitter.splice_in,
                        'status': 'active',
                        'notes': f'Fibra drop a caja {bd["code"]}',
                    }
                )
            self.stdout.write(f'  Caja: {box} | Fibra entrada: {input_fiber} de {input_cable.code if input_cable else "N/A"} | Potencia esperada: {expected_power} dBm')

        # ============================================================
        # 9. CREAR TRAMOS DE CABLE (CableSegment) CON RUTAS GPS
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 9. Creando Tramos de Cable con rutas GPS ---'))
        segments_created = 0

        # Tramos Feeder: OLT -> cada empalme
        for i, sd in enumerate(SPLICES_DATA):
            route_key = f"feeder_{sd['zone_code'].split('-')[1].lower()}"
            route_coords = ROUTES.get(route_key, [])
            if route_coords:
                segment, _ = CableSegment.objects.get_or_create(
                    cable=feeder_cable,
                    segment_type='olt_to_splice',
                    from_olt=olt,
                    to_splice=splices_map[sd['code']],
                    defaults={
                        'fiber_numbers': str(i + 1),
                        'length_m': FEEDER_CABLE['length_m'] / 5.0,
                        'route_coordinates': json.dumps(route_coords),
                        'attenuation_db': calc_segment_attenuation((FEEDER_CABLE['length_m'] / 5.0) / 1000.0, num_connectors=2),
                        'notes': f'Tramo feeder desde OLT a {sd["code"]}',
                    }
                )
                segments_created += 1

        # Tramos Distribution: Empalme -> Splitter
        for dd in DISTRIBUTION_CABLES:
            route_key = f"dist_{dd['zone_code'].split('-')[1].lower()}"
            route_coords = ROUTES.get(route_key, [])
            splice = splices_map[dd['splice_code']]
            splitter_code = f"SPL-{dd['zone_code'].split('-')[1]}-01"
            splitter = splitters_map.get(splitter_code)
            if splitter and route_coords:
                segment, _ = CableSegment.objects.get_or_create(
                    cable=dist_cables_map[dd['code']],
                    segment_type='splice_to_splitter',
                    from_splice=splice,
                    to_splitter=splitter,
                    defaults={
                        'fiber_numbers': '1',
                        'length_m': dd['length_m'],
                        'route_coordinates': json.dumps(route_coords),
                        'attenuation_db': calc_segment_attenuation(dd['length_m'] / 1000.0, num_connectors=2),
                        'notes': f'Tramo distribution desde {dd["splice_code"]} a {splitter_code}',
                    }
                )
                segments_created += 1

        # Tramos Drop: Splitter -> Cajas
        DROP_ROUTE_MAP = {
            'CBL-DRP-ERA-01': 'drop_era_01', 'CBL-DRP-ERA-02': 'drop_era_02',
            'CBL-DRP-SJOR-01': 'drop_sjor_01', 'CBL-DRP-SJOR-02': 'drop_sjor_02',
            'CBL-DRP-SJOA-01': 'drop_sjoa_01', 'CBL-DRP-SJOA-02': 'drop_sjoa_02',
            'CBL-DRP-SJBO-01': 'drop_sjbo_01', 'CBL-DRP-SJBO-02': 'drop_sjbo_02', 'CBL-DRP-SJBO-03': 'drop_sjbo_03',
            'CBL-DRP-HORT-01': 'drop_hort_01', 'CBL-DRP-HORT-02': 'drop_hort_02',
        }
        for dd in DROP_CABLES:
            route_key = DROP_ROUTE_MAP.get(dd['code'], '')
            route_coords = ROUTES.get(route_key, [])
            splitter = splitters_map[dd['splitter_code']]
            if dd['boxes'] and route_coords:
                first_box = boxes_map[dd['boxes'][0][0]]
                segment, _ = CableSegment.objects.get_or_create(
                    cable=drop_cables_map[dd['code']],
                    segment_type='splitter_to_box',
                    from_splitter=splitter,
                    to_box=first_box,
                    defaults={
                        'fiber_numbers': ','.join(str(b[1]) for b in dd['boxes']),
                        'length_m': dd['length_m'],
                        'route_coordinates': json.dumps(route_coords),
                        'attenuation_db': calc_segment_attenuation(dd['length_m'] / 1000.0, num_connectors=2),
                        'notes': f'Tramo drop desde {dd["splitter_code"]} a cajas {", ".join(b[0] for b in dd["boxes"])}',
                    }
                )
                segments_created += 1

        self.stdout.write(f'  Tramos creados: {segments_created}')

        # ============================================================
        # 10. CREAR CLIENTES (161 clientes)
        # ============================================================
        self.stdout.write(self.style.HTTP_INFO('--- 10. Creando Clientes (161) ---'))
        random.seed(42)
        name_idx = 0
        total_clients = 0

        for box_code, box in boxes_map.items():
            num_clients = random.randint(4, 7)
            feeder_len_km = FEEDER_CABLE['length_m'] / 5000.0
            dist_cable_code = box.splitter.input_cable.code if box.splitter.input_cable else None
            dist_len_km = 0.5
            if dist_cable_code and dist_cable_code in dist_cables_map:
                dist_len_km = dist_cables_map[dist_cable_code].length_m / 1000.0
            drop_len_km = box.input_cable.length_m / 1000.0 if box.input_cable else 0.15

            for port in range(1, num_clients + 1):
                fn = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
                ln1 = LAST_NAMES[name_idx % len(LAST_NAMES)]
                ln2 = LAST_NAMES[(name_idx + 1) % len(LAST_NAMES)]
                # Calcular potencia esperada para este cliente
                client_drop_m = random.randint(15, 40)
                expected_power = calc_power_at_client(OLT_OUTPUT_POWER_DBM, feeder_len_km, dist_len_km, drop_len_km, client_drop_m)
                # Potencia medida con pequena variacion aleatoria
                measured_power = round(expected_power + random.uniform(-0.8, 0.5), 1)

                Client.objects.get_or_create(client_code=f'CLI-{total_clients + 1:04d}', defaults={
                    'full_name': f'{fn} {ln1} {ln2}',
                    'address': f'{box.address} (Piso {port})',
                    'latitude': box.latitude + random.uniform(-0.0005, 0.0005),
                    'longitude': box.longitude + random.uniform(-0.0005, 0.0005),
                    'box': box,
                    'box_port': port,
                    'olt_port': box.splitter.input_port_olt,
                    'drop_fiber_number': port,
                    'expected_power_dbm': expected_power,
                    'status': 'active',
                    'optical_power_rx': measured_power,
                    'optical_power_tx': round(random.uniform(0.5, 4.0), 1),
                })
                name_idx += 1
                total_clients += 1

        self.stdout.write(f'  Clientes creados: {total_clients}')

        # ============================================================
        # RESUMEN FINAL CON POTENCIAS OPTICAS
        # ============================================================
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*70}\n"
            f"  DESPLIEGUE FTTH DE CIEZA - RESUMEN DE INGENIERIA\n"
            f"{'='*70}\n"
            f"  INFRAESTRUCTURA:\n"
            f"    OLT: 1 ({OLT_DATA['code']}) | Potencia: +{OLT_OUTPUT_POWER_DBM} dBm\n"
            f"    Zonas: {len(zones_map)}\n"
            f"    Empalmes: {len(splices_map)}\n"
            f"    Cables Feeder: 1 ({FEEDER_CABLE['code']}, {FEEDER_CABLE['fiber_count']} fibras, {FEEDER_CABLE['length_m']}m)\n"
            f"    Cables Distribution: {len(dist_cables_map)} (72 fibras cada uno)\n"
            f"    Splitters: {len(splitters_map)} (1x32)\n"
            f"    Cables Drop: {len(drop_cables_map)} (12 fibras cada uno)\n"
            f"    Cajas CTO: {len(boxes_map)}\n"
            f"    Clientes: {total_clients}\n"
            f"    Tramos de cable con rutas GPS: {segments_created}\n"
            f"    Asignaciones de fibra: {FiberAssignment.objects.count()}\n"
            f"{'='*70}\n"
            f"  CALCULOS OPTICOS (Formula real):\n"
            f"    Atenuacion fibra: {ATT_FIBER_DB_KM} dB/km\n"
            f"    Atenuacion conector: {ATT_CONNECTOR_DB} dB\n"
            f"    Atenuacion empalme: {ATT_SPLICE_DB} dB\n"
            f"    Atenuacion splitter 1x32: {ATT_SPLITTER_1X32_DB} dB\n"
            f"    Formula: P_out = {OLT_OUTPUT_POWER_DBM} - (0.35 x km) - (0.5 x N_con) - (0.1 x N_emp) - 16.5\n"
            f"{'='*70}\n"
            f"  POTENCIAS POR ZONA:\n"
        ))

        # Mostrar potencias por zona
        for zd in ZONES_DATA:
            zone_code = zd['code']
            zone_splitter_code = f"SPL-{zone_code.split('-')[1]}-01"
            splitter = splitters_map.get(zone_splitter_code)
            if splitter:
                feeder_len_km = FEEDER_CABLE['length_m'] / 5000.0
                dist_len_km = splitter.input_cable.length_m / 1000.0 if splitter.input_cable else 0.5
                power_splice = calc_power_to_splice(OLT_OUTPUT_POWER_DBM, feeder_len_km)
                power_splitter = calc_power_to_splitter(OLT_OUTPUT_POWER_DBM, feeder_len_km, dist_len_km)
                zone_boxes = [b for b in BOXES_DATA if b['zone'] == zone_code]
                box_powers = []
                for bb in zone_boxes:
                    box = boxes_map[bb['code']]
                    drop_len_km = box.input_cable.length_m / 1000.0 if box.input_cable else 0.15
                    bp = calc_power_at_box(OLT_OUTPUT_POWER_DBM, feeder_len_km, dist_len_km, drop_len_km)
                    box_powers.append(bp)
                min_bp = min(box_powers) if box_powers else -17.0
                max_bp = max(box_powers) if box_powers else -17.0
                zone_clients = Client.objects.filter(box__zone__code=zone_code).count()
                self.stdout.write(
                    f"    {zone_code} ({zd['name']}):\n"
                    f"      Empalme: {power_splice} dBm | Splitter entrada: {power_splitter} dBm\n"
                    f"      Splitter salida: {splitter.output_power_dbm} dBm\n"
                    f"      Cajas: {len(zone_boxes)} | Rango potencia cajas: {min_bp} a {max_bp} dBm\n"
                    f"      Clientes: {zone_clients}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*70}\n"
            f"  EJEMPLO DE CALCULO DETALLADO (CTO-001, La Era):\n"
            f"    OLT salida: +{OLT_OUTPUT_POWER_DBM} dBm\n"
            f"    - Feeder (0.7km x 0.35) + 2 conectores (1.0dB) = 1.245 dB\n"
            f"    - Distribution (0.8km x 0.35) + 2 conectores (1.0dB) = 1.28 dB\n"
            f"    - Splitter 1x32 = {ATT_SPLITTER_1X32_DB} dB\n"
            f"    - Drop (0.15km x 0.35) + 2 conectores (1.0dB) = 1.0525 dB\n"
            f"    = Potencia en caja: ~{calc_power_at_box(OLT_OUTPUT_POWER_DBM, 0.7, 0.8, 0.15)} dBm\n"
            f"    = Potencia en cliente (con drop 25m): ~{calc_power_at_client(OLT_OUTPUT_POWER_DBM, 0.7, 0.8, 0.15)} dBm\n"
            f"{'='*70}"
        ))
