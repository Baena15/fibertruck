# 🚛 FiberTruck

**Aplicacion web de diagnostico de fallos para redes FTTH** — Proyecto Final de Master en Desarrollo Full Stack.

> Despliegue FTTH ficticio diseñado para la poblacion de **Cieza, Murcia** como trabajo de ingenieria original.

---

## Descripcion del Proyecto

FiberTruck es una aplicacion web que permite a tecnicos de campo diagnosticar fallos en redes de fibra optica FTTH mediante un algoritmo de busqueda ascendente en el arbol jerarquico de la red.

Cuando un cliente reporta una incidencia, el sistema analiza la topologia (OLT > Splitter > Caja > Cliente) para determinar si el problema es individual o afecta a multiples clientes, encontrando el "punto de divergencia" donde se produce la averia.

### Ingenieria de Despliegue - Cieza, Murcia

Se ha disenado un despliegue FTTH completo y ficticio basado en la geografia urbana real de Cieza:

| Elemento | Cantidad | Detalle |
|----------|----------|---------|
| **OLT** | 1 | Central en centro urbano (OLT-CIEZA-01) |
| **Zonas** | 5 | La Era, San Jose, San Joaquin, San Juan Bosco, La Horta |
| **Splitters** | 5 | 1 por zona, ratio 1x32 |
| **Cajas CTO** | 29 | CTO-001 a CTO-044, distribuidas por barrios |
| **Clientes** | 161 | 4-7 por caja, potencia optica realista |

Las coordenadas GPS de cada elemento se han asignado de forma coherente con el plan urbanistico del municipio.

---

## Tecnologias

| Capa | Tecnologia | Justificacion |
|------|-----------|---------------|
| **Backend** | Django 5 + DRF | Framework requerido por el master. API REST con algoritmo de diagnostico |
| **Frontend** | React 18 + Tailwind | Framework requerido. Interfaz responsive con mapa interactivo |
| **Mapas** | Leaflet + OpenStreetMap | Open-source, visualizacion geoespacial de red FTTH |
| **Base de datos** | SQLite (dev) / PostgreSQL (prod) | SQLite para desarrollo, PostgreSQL en Railway |
| **Auth** | JWT (SimpleJWT) | Tokens seguros con expiracion, 3 roles de usuario |

---

## Estructura del Proyecto

```
fibertruck/
├── fibertruck/          # Configuracion Django
├── core/                # Auth: modelo User, JWT, permisos RBAC
├── network/             # App principal: modelos, API, algoritmo FTFL
│   └── management/
│       └── populate_cieza.py  # Datos de Cieza
├── frontend/            # React app
│   ├── public/
│   │   └── index.html
│   └── src/
│       └── app.jsx      # Dashboard, Mapa, Diagnostico, Simulador
├── manage.py
├── requirements.txt     # Detectado por Railway
├── Procfile            # Comando de inicio
├── railway.toml        # Config Railway
└── build.sh            # Build script
```

---

## Modelo de Datos

```
OLT (raiz)
  └── Splitter (5, uno por zona)
       └── FiberBox/CTO (29, distribuidas)
            └── Client (161, hojas)
```

---

## Algoritmo de Diagnostico (FTFL)

1. **Entrada**: Cliente(s) afectados reportados
2. **Agrupacion**: Busca otros afectados en la misma caja
3. **Expansion**: Si multiples, busca en el mismo splitter
4. **Punto de divergencia**: Nodo mas cercano a cabecera donde todos comparten ruta
5. **Salida**: Recomendacion con nivel de confianza

**Severidad**:
- **Critica**: 3+ clientes, mismo splitter → problema en splitter/fibra
- **Alta**: 2+ clientes, misma caja → problema en caja/conectores
- **Media**: Cliente individual → problema en drop/ONT

---

## Roles de Usuario

| Rol | Permisos |
|-----|----------|
| **Administrador** | CRUD completo, gestion de usuarios |
| **Tecnico de campo** | Ver mapa, diagnosticar, reportar incidencias |
| **Supervisor/NOC** | Dashboard, estadisticas, gestion de incidencias |

---

## API Endpoints

### Auth
```
POST /api/auth/login/          # Login (JWT)
POST /api/auth/register/       # Registro
GET  /api/auth/me/             # Perfil usuario
POST /api/auth/change-password/
```

### Network
```
GET  /api/zones/               # Zonas (barrios)
GET  /api/boxes/               # Cajas de fibra
GET  /api/boxes/search/?code=CTO-001  # Buscar caja
GET  /api/boxes/{id}/clients/  # Clientes de caja
GET  /api/boxes/{id}/hierarchy/# Jerarquia completa
GET  /api/clients/             # Clientes
POST /api/clients/report_outage/  # Reportar + diagnosticar
GET  /api/incidents/stats/     # Estadisticas dashboard
```

---

## Instalacion Local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_cieza
python manage.py runserver
```

Abrir `frontend/public/index.html` en navegador para el frontend.

Usuarios de prueba:
- `admin` / `admin123`
- `tecnico1` / `tecno123`
- `supervisor1` / `super123`

---

## Despliegue en Railway

1. **Crear proyecto** en [railway.app](https://railway.app) → Deploy from GitHub repo
2. **Añadir PostgreSQL**: New → Database → PostgreSQL
3. **Variables**: `SECRET_KEY`, `DEBUG=False`
4. Railway detecta `requirements.txt` + `Procfile` automaticamente

---

## Tests

```bash
python manage.py test network.tests --verbosity=2
```

15 tests unitarios que verifican:
- Jerarquia de red
- Algoritmo de diagnostico (individual, caja, bulk outage)
- Niveles de confianza
- Aislamiento entre splitters

---

## Autor

Proyecto Final de Master en Desarrollo Full Stack
Ingenieria de despliegue FTTH de Cieza, Murcia — Trabajo original para el TFM
