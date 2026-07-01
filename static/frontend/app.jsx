const { useState, useEffect } = React;

/* ============================================================
   1. HELPERS GLOBALES
   ============================================================ */

const API_URL = '';

const ZONE_COLORS = {
  'Z-ERA': '#dc2626',
  'Z-SJOR': '#2563eb',
  'Z-SJOA': '#16a34a',
  'Z-SJBO': '#f59e0b',
  'Z-HORT': '#8b5cf6'
};

const CABLE_COLORS = {
  feeder: '#dc2626',
  distribution: '#2563eb',
  drop: '#16a34a'
};

const getToken = () => localStorage.getItem('token');

const apiHeaders = () => ({
  'Authorization': 'Bearer ' + getToken(),
  'Content-Type': 'application/json'
});

const fetchAPI = async (path) => {
  const r = await fetch(API_URL + path, { headers: apiHeaders() });
  return r.ok ? r.json() : null;
};

const postAPI = async (path, body) => {
  const r = await fetch(API_URL + path, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify(body)
  });
  return r.ok ? r.json() : null;
};

const logout = () => {
  localStorage.removeItem('token');
  window.location.reload();
};

/* ============================================================
   2. LOGIN SCREEN
   ============================================================ */

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const r = await fetch(API_URL + '/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const d = await r.json();
      if (r.ok && d.access) {
        localStorage.setItem('token', d.access);
        onLogin();
      } else {
        setError(d.detail || 'Usuario o contrasena incorrectos');
      }
    } catch {
      setError('Error de conexion');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-800 to-blue-900 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <span className="text-4xl">&#128667;</span>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">FiberTruck</h1>
          <p className="text-gray-500 text-sm">Diagnostico FTTH - Cieza, Murcia</p>
          <p className="text-xs text-blue-500 mt-1">v2.0</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="text" value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Usuario"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required
          />
          <input
            type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Contrasena"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required
          />
          {error && (
            <p className="text-red-600 text-sm bg-red-50 p-2 rounded">&#9888; {error}</p>
          )}
          <button
            type="submit" disabled={loading}
            className="w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-2 font-semibold">Usuarios de prueba:</p>
          <div className="grid grid-cols-3 gap-2">
            {[
              ['admin', 'admin123'],
              ['tecnico1', 'tecno123'],
              ['supervisor1', 'super123']
            ].map(([u, p]) => (
              <button
                key={u}
                onClick={() => { setUsername(u); setPassword(p); }}
                className="text-xs bg-white border border-gray-200 rounded px-2 py-1 hover:border-blue-400 hover:text-blue-700"
              >
                {u}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   3. HEADER
   ============================================================ */

function Header({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '\uD83D\uDCCA' },
    { id: 'map', label: 'Mapa', icon: '\uD83D\uDDFA' },
    { id: 'topology', label: 'Red', icon: '\uD83C\uDF10' },
    { id: 'diagnose', label: 'Diagnostico', icon: '\uD83D\uDD0D' },
    { id: 'simulate', label: 'Simular', icon: '\u26A1' },
  ];

  return (
    <header className="bg-blue-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">&#128667;</span>
            <div>
              <h1 className="text-xl font-bold">FiberTruck</h1>
              <p className="text-xs text-blue-200">v2.0 - Cieza, Murcia</p>
            </div>
          </div>
          <nav className="flex space-x-1 flex-wrap">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === t.id
                    ? 'bg-blue-600 text-white'
                    : 'text-blue-200 hover:bg-blue-700 hover:text-white'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </nav>
          <div className="flex items-center space-x-3">
            <button onClick={logout} className="text-xs text-blue-300 hover:text-white" title="Cerrar sesion">
              Salir
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

/* ============================================================
   4. DASHBOARD
   ============================================================ */

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [cables, setCables] = useState([]);
  const [olts, setOlts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [s, z, c, o] = await Promise.all([
        fetchAPI('/api/incidents/stats/'),
        fetchAPI('/api/zones/'),
        fetchAPI('/api/cables/'),
        fetchAPI('/api/olts/')
      ]);
      setStats(s);
      setZones(z || []);
      setCables(c || []);
      setOlts(o || []);
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Cargando dashboard...</div>;
  }

  const olt = olts[0] || { output_power_dbm: '+3.0', splitter_ratio: '1x32' };
  const zoneCount = zones.length;
  const boxCount = stats?.active_boxes || 29;
  const clientCount = stats?.total_clients || 161;

  const feederCables = cables.filter(c => c.cable_type === 'feeder');
  const distCables = cables.filter(c => c.cable_type === 'distribution');
  const dropCables = cables.filter(c => c.cable_type === 'drop');

  const sumFibers = (list) => list.reduce((s, c) => s + (c.fiber_count || 0), 0);
  const sumUsed = (list) => list.reduce((s, c) => s + (c.fibers_used || c.used_fibers || 0), 0);

  const feederFibers = sumFibers(feederCables);
  const distFibers = sumFibers(distCables);
  const dropFibers = sumFibers(dropCables);

  const feederUsed = sumUsed(feederCables);
  const distUsed = sumUsed(distCables);
  const dropUsed = sumUsed(dropCables);

  const feederFree = feederFibers - feederUsed;
  const distFree = distFibers - distUsed;
  const dropFree = dropFibers - dropUsed;

  const feederPct = feederFibers > 0 ? ((feederUsed / feederFibers) * 100).toFixed(1) : '0.0';
  const distPct = distFibers > 0 ? ((distUsed / distFibers) * 100).toFixed(1) : '0.0';
  const dropPct = dropFibers > 0 ? ((dropUsed / dropFibers) * 100).toFixed(1) : '0.0';

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* FIBERTRUCK DASHBOARD Title */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h1 className="text-2xl font-bold text-center text-gray-800 tracking-wide">FIBERTRUCK DASHBOARD</h1>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 text-center">
          <p className="text-sm text-gray-500 mb-1">OLT</p>
          <p className="text-3xl font-bold text-blue-700">{olt.code || 'OLT-01'}</p>
          <p className="text-lg font-semibold text-blue-600 mt-1">{olt.output_power_dbm || '+3.0'} dBm</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 text-center">
          <p className="text-sm text-gray-500 mb-1">Zonas</p>
          <p className="text-3xl font-bold text-purple-700">{zoneCount}</p>
          <p className="text-sm text-gray-400 mt-1">barrios</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 text-center">
          <p className="text-sm text-gray-500 mb-1">Cajas CTO</p>
          <p className="text-3xl font-bold text-blue-700">{boxCount}</p>
          <p className="text-sm text-gray-400 mt-1">activas</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 text-center">
          <p className="text-sm text-gray-500 mb-1">Clientes</p>
          <p className="text-3xl font-bold text-green-700">{clientCount}</p>
          <p className="text-sm text-gray-400 mt-1">totales</p>
        </div>
      </div>

      {/* CABLES DE RED */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">&#128225; CABLES DE RED</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-center">Capacidad</th>
                <th className="px-4 py-3 text-center">Usadas</th>
                <th className="px-4 py-3 text-center">Libres</th>
                <th className="px-4 py-3 text-center">Uso</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              <tr className="hover:bg-gray-50">
                <td className="px-4 py-3 font-semibold text-red-700">Feeder</td>
                <td className="px-4 py-3 text-center font-mono">{feederFibers}f ({feederCables.length})</td>
                <td className="px-4 py-3 text-center">{feederUsed}</td>
                <td className="px-4 py-3 text-center">{feederFree}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="power-bar-bg w-24">
                      <div className="power-bar-fill bg-red-500" style={{ width: feederPct + '%' }} />
                    </div>
                    <span className="text-xs font-medium w-12">{feederPct}%</span>
                  </div>
                </td>
              </tr>
              <tr className="hover:bg-gray-50">
                <td className="px-4 py-3 font-semibold text-blue-700">Distribution</td>
                <td className="px-4 py-3 text-center font-mono">{distFibers}f ({distCables.length})</td>
                <td className="px-4 py-3 text-center">{distUsed}</td>
                <td className="px-4 py-3 text-center">{distFree}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="power-bar-bg w-24">
                      <div className="power-bar-fill bg-blue-500" style={{ width: distPct + '%' }} />
                    </div>
                    <span className="text-xs font-medium w-12">{distPct}%</span>
                  </div>
                </td>
              </tr>
              <tr className="hover:bg-gray-50">
                <td className="px-4 py-3 font-semibold text-green-700">Drop</td>
                <td className="px-4 py-3 text-center font-mono">{dropFibers}f ({dropCables.length})</td>
                <td className="px-4 py-3 text-center">{dropUsed}</td>
                <td className="px-4 py-3 text-center">{dropFree}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="power-bar-bg w-24">
                      <div className="power-bar-fill bg-green-500" style={{ width: dropPct + '%' }} />
                    </div>
                    <span className="text-xs font-medium w-12">{dropPct}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ESTADO DE LA RED */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">&#127968; ESTADO DE LA RED</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3 text-left">Zona</th>
                <th className="px-4 py-3 text-center">Clientes</th>
                <th className="px-4 py-3 text-center">Afectados</th>
                <th className="px-4 py-3 text-left">Empalmes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {zones.map(z => (
                <tr key={z.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ZONE_COLORS[z.code] || '#666' }} />
                      <span className="font-semibold text-gray-800">{z.name}</span>
                      <span className="text-xs text-gray-400 font-mono">({z.code})</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center font-semibold">{z.client_count || 0}</td>
                  <td className="px-4 py-3 text-center">
                    {(z.affected_client_count || 0) > 0 ? (
                      <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-bold text-xs">
                        {z.affected_client_count}
                      </span>
                    ) : (
                      <span className="text-green-600">0</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">
                    SPC-{z.code?.replace('Z-', '') || ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   5. NETWORK MAP
   ============================================================ */

function NetworkMap() {
  const [segments, setSegments] = useState([]);
  const [boxes, setBoxes] = useState([]);
  const [splices, setSplices] = useState([]);
  const [splitters, setSplitters] = useState([]);
  const [zones, setZones] = useState([]);
  const [olts, setOlts] = useState([]);
  const [selectedElement, setSelectedElement] = useState(null);
  const [selectedBoxClients, setSelectedBoxClients] = useState([]);
  const [showLayer, setShowLayer] = useState({
    feeder: true, distribution: true, drop: true,
    boxes: true, splices: true, splitters: true, olt: true
  });
  const [loading, setLoading] = useState(true);

  const mapRef = React.useRef(null);
  const leafletMap = React.useRef(null);
  const layersRef = React.useRef({});

  // Load all data
  useEffect(() => {
    const load = async () => {
      const [seg, b, sp, spl, z, o] = await Promise.all([
        fetchAPI('/api/segments/'),
        fetchAPI('/api/boxes/'),
        fetchAPI('/api/splices/'),
        fetchAPI('/api/splitters/'),
        fetchAPI('/api/zones/'),
        fetchAPI('/api/olts/')
      ]);
      setSegments(seg || []);
      setBoxes(b || []);
      setSplices(sp || []);
      setSplitters(spl || []);
      setZones(z || []);
      setOlts(o || []);
      setLoading(false);
    };
    load();
  }, []);

  // Initialize Leaflet map
  useEffect(() => {
    if (!leafletMap.current && mapRef.current) {
      leafletMap.current = L.map(mapRef.current).setView([38.2395, -1.4165], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 19
      }).addTo(leafletMap.current);
    }
    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, []);

  // Draw all layers on map
  useEffect(() => {
    if (!leafletMap.current || loading) return;

    // Clear previous layers
    Object.values(layersRef.current).forEach(layer => {
      if (layer && leafletMap.current.hasLayer(layer)) {
        leafletMap.current.removeLayer(layer);
      }
    });
    layersRef.current = {};

    const layerGroups = {
      feeder: L.layerGroup(),
      distribution: L.layerGroup(),
      drop: L.layerGroup(),
      boxes: L.layerGroup(),
      splices: L.layerGroup(),
      splitters: L.layerGroup(),
      olt: L.layerGroup()
    };

    // Draw OLT
    if (showLayer.olt && olts.length > 0) {
      const olt = olts[0];
      if (olt.latitude && olt.longitude) {
        const oltIcon = L.divIcon({
          className: 'custom-olt-marker',
          html: `<div style="width:20px;height:20px;background:#dc2626;border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });
        L.marker([olt.latitude, olt.longitude], { icon: oltIcon })
          .addTo(layerGroups.olt)
          .bindPopup(`<b>${olt.code || 'OLT'}</b><br/>${olt.name || ''}<br/>Potencia: ${olt.output_power_dbm || '?'} dBm<br/>Ratio: ${olt.splitter_ratio || '?'}`);
      }
    }

    // Draw zone areas
    zones.forEach(z => {
      if (z.latitude && z.longitude) {
        const color = ZONE_COLORS[z.code] || '#666';
        L.circle([z.latitude, z.longitude], {
          radius: 400, color, fillColor: color,
          fillOpacity: 0.05, weight: 2, dashArray: '5,5'
        }).addTo(layerGroups.feeder)
          .bindPopup(`<b>${z.name}</b><br/>${z.code}<br/>${z.client_count || 0} clientes`);
      }
    });

    // Draw cable segments as polylines
    segments.forEach(seg => {
      const sType = seg.segment_type || seg.cable_type || 'drop';
      if (!showLayer[sType]) return;

      const route = seg.route_as_list || [];
      if (route.length < 2) return;

      const color = CABLE_COLORS[sType] || '#666';
      const weight = sType === 'feeder' ? 4 : sType === 'distribution' ? 3 : 2;
      const dashArray = sType === 'feeder' ? '10,5' : sType === 'drop' ? '5,5' : null;

      const poly = L.polyline(route, { color, weight, dashArray, opacity: 0.85 })
        .addTo(layerGroups[sType]);

      const popupContent = `
        <div style="min-width:180px">
          <b style="color:${color}">${seg.cable_code || 'Tramo ' + seg.id}</b><br/>
          <small>Tipo: <b>${sType.toUpperCase()}</b></small><br/>
          <small>Origen: ${seg.origin_name || '?'}</small><br/>
          <small>Destino: ${seg.destination_name || '?'}</small><br/>
          <small>Fibras: ${seg.fiber_numbers || '?'}</small><br/>
          <small>Longitud: ${seg.length_m || '?'}m</small><br/>
          <small>Atenuacion: ${seg.attenuation_db || '?'} dB</small>
        </div>
      `;
      poly.bindPopup(popupContent);
      poly.on('click', () => setSelectedElement({ type: 'segment', data: seg }));
    });

    // Draw splices (empalmes)
    if (showLayer.splices) {
      splices.forEach(sp => {
        if (!sp.latitude || !sp.longitude) return;
        const marker = L.circleMarker([sp.latitude, sp.longitude], {
          radius: 8, fillColor: '#111827',
          color: '#fbbf24', weight: 3, fillOpacity: 0.9
        }).addTo(layerGroups.splices)
          .bindPopup(`
            <div style="min-width:160px">
              <b>${sp.code || sp.name}</b><br/>
              <small>Tipo: ${sp.closure_type || 'Fusion'}</small><br/>
              <small>Zona: ${sp.zone_name || sp.zone_code || 'N/A'}</small><br/>
              <small>Fibras: ${sp.fiber_count_used || 0}/${sp.fiber_capacity || 0}</small><br/>
              <small style="color:green">Libres: ${sp.fibers_free || 0}</small>
            </div>
          `);
        marker.on('click', () => setSelectedElement({ type: 'splice', data: sp }));
      });
    }

    // Draw splitters (estrella naranja)
    if (showLayer.splitters) {
      splitters.forEach(spl => {
        if (!spl.latitude || !spl.longitude) return;
        const starIcon = L.divIcon({
          className: 'custom-splitter-icon',
          html: `<svg width="20" height="20" viewBox="0 0 24 24" fill="#f97316" stroke="#fff" stroke-width="1"><polygon points="12,2 15,9 22,9 16,14 18,22 12,17 6,22 8,14 2,9 9,9"/></svg>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });
        L.marker([spl.latitude, spl.longitude], { icon: starIcon })
          .addTo(layerGroups.splitters)
          .bindPopup(`
            <div style="min-width:160px">
              <b style="color:#f97316">${spl.code || spl.name}</b><br/>
              <small>Ratio: 1:${spl.ratio || '?'}</small><br/>
              <small>Zona: ${spl.zone_code || 'N/A'}</small><br/>
              <small>Puertos: ${spl.occupied_ports || 0}/${spl.total_ports || 0} ocupados</small><br/>
              <small>Potencia entrada: ${spl.output_power_dbm || '?'} dBm</small>
            </div>
          `)
          .on('click', () => setSelectedElement({ type: 'splitter', data: spl }));
      });
    }

    // Draw boxes (CTOs) - circulo con color de zona
    if (showLayer.boxes) {
      boxes.forEach(b => {
        if (!b.latitude || !b.longitude) return;
        const color = ZONE_COLORS[b.zone_code] || '#0ea5e9';
        const isAffected = (b.affected_count || 0) > 0;

        L.circleMarker([b.latitude, b.longitude], {
          radius: isAffected ? 12 : 8,
          fillColor: color,
          color: isAffected ? '#dc2626' : '#fff',
          weight: isAffected ? 3 : 2,
          fillOpacity: isAffected ? 0.95 : 0.75
        }).addTo(layerGroups.boxes)
          .bindPopup(`
            <b>${b.code}</b><br/>
            ${b.name || ''}<br/>
            ${b.client_count || 0} clientes
            ${isAffected ? `<br/><span style="color:red; font-weight:bold;">${b.affected_count} afectados</span>` : ''}
          `)
          .on('click', async () => {
            setSelectedElement({ type: 'box', data: b });
            const c = await fetchAPI('/api/boxes/' + b.id + '/clients/');
            setSelectedBoxClients(c || []);
          });
      });
    }

    // Add all layer groups to map based on visibility
    Object.entries(layerGroups).forEach(([key, group]) => {
      if (showLayer[key] !== false) {
        group.addTo(leafletMap.current);
      }
      layersRef.current[key] = group;
    });
  }, [segments, boxes, splices, splitters, zones, olts, showLayer, loading]);

  const toggleLayer = (layer) => {
    setShowLayer(p => ({ ...p, [layer]: !p[layer] }));
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Cargando mapa...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Layer controls */}
      <div className="mb-4 flex flex-wrap gap-2">
        {[
          { k: 'feeder', l: 'Feeder', c: 'bg-red-100 text-red-700 border-red-300' },
          { k: 'distribution', l: 'Distribution', c: 'bg-blue-100 text-blue-700 border-blue-300' },
          { k: 'drop', l: 'Drop', c: 'bg-green-100 text-green-700 border-green-300' },
          { k: 'boxes', l: 'Cajas CTO', c: 'bg-gray-100 text-gray-700 border-gray-300' },
          { k: 'splices', l: 'Empalmes', c: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
          { k: 'splitters', l: 'Splitters', c: 'bg-orange-100 text-orange-700 border-orange-300' },
          { k: 'olt', l: 'OLT', c: 'bg-red-100 text-red-800 border-red-400' },
        ].map(item => (
          <button
            key={item.k}
            onClick={() => toggleLayer(item.k)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              showLayer[item.k] ? item.c : 'bg-gray-50 text-gray-400 border-gray-200'
            }`}
          >
            {showLayer[item.k] ? '\u2713' : '\u2717'} {item.l}
          </button>
        ))}
        <button
          onClick={() => { if (leafletMap.current) leafletMap.current.setView([38.2395, -1.4165], 15); }}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200 ml-auto"
        >
          Centrar
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-4" style={{ height: '75vh' }}>
        {/* Map */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden relative">
          <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
          {/* Legend - esquina inferior derecha */}
          <div className="absolute bottom-3 right-3 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-3 text-xs border border-gray-200 z-[500]">
            <p className="font-bold text-gray-700 mb-2">Leyenda</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-6 rounded" style={{ background: '#dc2626', height: '4px', borderStyle: 'dashed', borderWidth: '1px', borderColor: '#dc2626' }} />
                <span>Feeder</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 rounded" style={{ background: '#2563eb', height: '3px' }} />
                <span>Distribution</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 rounded" style={{ background: '#16a34a', height: '2px', borderStyle: 'dashed', borderWidth: '1px', borderColor: '#16a34a' }} />
                <span>Drop</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#1f2937', border: '2px solid #fbbf24' }} />
                <span>Empalme</span>
              </div>
              <div className="flex items-center gap-2">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#f97316"><polygon points="12,2 15,9 22,9 16,14 18,22 12,17 6,22 8,14 2,9 9,9"/></svg>
                <span>Splitter</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#0ea5e9' }} />
                <span>Caja CTO</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3" style={{ background: '#dc2626', border: '1px solid #fff' }} />
                <span>OLT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        <div className="w-full lg:w-80 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h3 className="font-bold text-gray-800">Elemento seleccionado</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {!selectedElement && (
              <div className="text-center text-gray-400 py-8">
                <p className="text-3xl mb-2">&#128506;</p>
                <p className="text-sm">Haz clic en un elemento</p>
                <p className="text-xs">para ver sus detalles</p>
              </div>
            )}
            {selectedElement?.type === 'segment' && (
              <div className="p-3 rounded-lg border border-blue-200 bg-blue-50">
                <h4 className="font-bold text-blue-800 mb-2">{selectedElement.data.cable_code || 'Tramo'}</h4>
                <p className="text-sm text-blue-700">Tipo: <b>{selectedElement.data.segment_type || selectedElement.data.cable_type}</b></p>
                <p className="text-sm text-blue-700">Origen: {selectedElement.data.origin_name || '?'}</p>
                <p className="text-sm text-blue-700">Destino: {selectedElement.data.destination_name || '?'}</p>
                <p className="text-sm text-blue-700">Fibras: {selectedElement.data.fiber_numbers || '?'}</p>
                <p className="text-sm text-blue-700">Longitud: {selectedElement.data.length_m || '?'}m</p>
              </div>
            )}
            {selectedElement?.type === 'splice' && (
              <div className="p-3 rounded-lg border border-yellow-200 bg-yellow-50">
                <h4 className="font-bold text-yellow-800 mb-2">{selectedElement.data.code || selectedElement.data.name}</h4>
                <p className="text-sm text-yellow-700">Tipo: {selectedElement.data.closure_type || 'Fusion'}</p>
                <p className="text-sm text-yellow-700">Zona: {selectedElement.data.zone_name || '?'}</p>
                <p className="text-sm text-yellow-700">Fibras: {selectedElement.data.fiber_count_used || 0}/{selectedElement.data.fiber_capacity || 0}</p>
                <p className="text-sm text-yellow-700">Direccion: {selectedElement.data.address || '?'}</p>
              </div>
            )}
            {selectedElement?.type === 'splitter' && (
              <div className="p-3 rounded-lg border border-orange-200 bg-orange-50">
                <h4 className="font-bold text-orange-800 mb-2">{selectedElement.data.code || selectedElement.data.name}</h4>
                <p className="text-sm text-orange-700">Ratio: 1:{selectedElement.data.ratio || '?'}</p>
                <p className="text-sm text-orange-700">Zona: {selectedElement.data.zone_code || '?'}</p>
                <p className="text-sm text-orange-700">Puertos: {selectedElement.data.occupied_ports || 0}/{selectedElement.data.total_ports || 0}</p>
                <p className="text-sm text-orange-700">Potencia: {selectedElement.data.output_power_dbm || '?'} dBm</p>
              </div>
            )}
            {selectedElement?.type === 'box' && (
              <div className="space-y-3">
                <div className="p-3 rounded-lg border border-gray-200 bg-gray-50">
                  <h4 className="font-bold text-gray-800 mb-1">{selectedElement.data.code}</h4>
                  <p className="text-sm text-gray-600">{selectedElement.data.name}</p>
                  <p className="text-xs text-gray-400">{selectedElement.data.full_path}</p>
                  <p className="text-sm mt-2">Potencia esperada: {selectedElement.data.expected_power_dbm || '?'} dBm</p>
                  <p className="text-sm">Potencia medida: {selectedElement.data.measured_power_dbm || '?'} dBm</p>
                  {selectedElement.data.power_deviation_db && (
                    <p className={`text-sm font-semibold ${selectedElement.data.power_deviation_db > 5 ? 'text-red-600' : 'text-green-600'}`}>
                      Desviacion: {selectedElement.data.power_deviation_db} dB
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-2">Clientes ({selectedBoxClients.length}):</p>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {selectedBoxClients.map(c => (
                      <div key={c.id} className={`text-xs px-2 py-1 rounded ${c.status === 'affected' ? 'bg-red-100 text-red-700' : 'bg-green-50 text-green-700'}`}>
                        {c.client_code} - {c.full_name}
                        {c.optical_power_rx && ` (${c.optical_power_rx} dBm)`}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   6. DIAGNOSE V2 - Wizard de 3 pasos
   ============================================================ */

function DiagnoseV2() {
  const [step, setStep] = useState(1);
  const [boxCode, setBoxCode] = useState('');
  const [box, setBox] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClients, setSelectedClients] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const miniMapRef = React.useRef(null);
  const miniLeafletMap = React.useRef(null);

  // Buscar caja por codigo
  const searchBox = async () => {
    setLoading(true);
    setError('');
    const allBoxes = await fetchAPI('/api/boxes/');
    if (allBoxes) {
      const found = allBoxes.find(b => b.code.toUpperCase() === boxCode.toUpperCase());
      if (found) {
        setBox(found);
        const c = await fetchAPI('/api/boxes/' + found.id + '/clients/');
        setClients(c || []);
        setStep(2);
      } else {
        setError('Caja no encontrada: ' + boxCode);
      }
    } else {
      setError('Error al cargar cajas');
    }
    setLoading(false);
  };

  // Ejecutar diagnostico
  const runDiagnosis = async () => {
    if (selectedClients.length === 0) {
      setError('Selecciona al menos un cliente afectado');
      return;
    }
    setLoading(true);
    setError('');

    // Reportar outage para cada cliente
    for (const cid of selectedClients) {
      await postAPI('/api/clients/report_outage/', { client_id: cid });
    }

    // Llamar a diagnostico v2
    const diagnosis = await postAPI('/api/diagnose/v2/', {
      box_code: boxCode.toUpperCase(),
      affected_client_ids: selectedClients
    });

    if (diagnosis) {
      setResult(diagnosis);
      setStep(3);
    } else {
      setError('Error al ejecutar diagnostico v2');
    }
    setLoading(false);
  };

  const toggleClient = (id) => {
    setSelectedClients(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id]);
  };

  const reset = () => {
    setStep(1);
    setBoxCode('');
    setBox(null);
    setClients([]);
    setSelectedClients([]);
    setResult(null);
    setError('');
    if (miniLeafletMap.current) {
      miniLeafletMap.current.remove();
      miniLeafletMap.current = null;
    }
  };

  // Mini mapa para el tramo afectado
  useEffect(() => {
    if (step === 3 && result?.affected_route && miniMapRef.current) {
      if (miniLeafletMap.current) {
        miniLeafletMap.current.remove();
        miniLeafletMap.current = null;
      }
      miniLeafletMap.current = L.map(miniMapRef.current);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OSM',
        maxZoom: 19
      }).addTo(miniLeafletMap.current);

      const route = result.affected_route;
      if (route.length >= 2) {
        L.polyline(route, { color: '#dc2626', weight: 5, dashArray: '8,4', opacity: 0.9 })
          .addTo(miniLeafletMap.current);
        L.circleMarker(route[0], { radius: 6, fillColor: '#16a34a', color: '#fff', weight: 2 })
          .addTo(miniLeafletMap.current).bindPopup('Origen');
        L.circleMarker(route[route.length - 1], { radius: 6, fillColor: '#dc2626', color: '#fff', weight: 2 })
          .addTo(miniLeafletMap.current).bindPopup('Caja');
        const bounds = L.latLngBounds(route);
        miniLeafletMap.current.fitBounds(bounds.pad(0.3));
      }
    }
  }, [step, result]);

  const severityClass = result?.severity === 'critical' ? 'severity-critical'
    : result?.severity === 'high' ? 'severity-high'
    : result?.severity === 'medium' ? 'severity-medium'
    : 'severity-low';

  const severityTitle = result?.severity === 'critical' ? 'CRITICO'
    : result?.severity === 'high' ? 'ALTO'
    : result?.severity === 'medium' ? 'MEDIO'
    : 'BAJO';

  const severityEmoji = result?.severity === 'critical' ? '\uD83D\uDEA8'
    : result?.severity === 'high' ? '\u26A0\uFE0F'
    : '\u2139\uFE0F';

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* Wizard Steps */}
      <div className="flex items-center mb-8">
        {['Introducir Caja', 'Seleccionar Afectados', 'Resultado'].map((s, i) => (
          <React.Fragment key={i}>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-sm ${
              step > i + 1 ? 'bg-green-500 text-white'
              : step === i + 1 ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-500'
            }`}>
              {step > i + 1 ? '\u2713' : i + 1}
            </div>
            <span className="text-xs ml-2 mr-2 hidden md:inline ${step >= i + 1 ? 'text-gray-800 font-medium' : 'text-gray-400'}">{s}</span>
            {i < 2 && <div className={`flex-1 h-1 mx-2 ${step > i + 1 ? 'bg-green-500' : 'bg-gray-200'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* PASO 1: Introducir codigo de caja */}
      {step === 1 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-2">Codigo de caja</h2>
          <p className="text-gray-500 mb-6">Introduce el codigo de la caja a diagnosticar (ej: CTO-023)</p>
          <div className="flex gap-3">
            <input
              type="text" value={boxCode}
              onChange={e => setBoxCode(e.target.value.toUpperCase())}
              onKeyPress={e => e.key === 'Enter' && searchBox()}
              placeholder="CTO-023"
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none text-lg font-mono uppercase"
            />
            <button onClick={searchBox} disabled={loading || !boxCode}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">
              {loading ? '...' : 'Buscar'}
            </button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm bg-red-50 p-2 rounded">{error}</p>}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm font-semibold text-gray-600 mb-2">Ejemplos rapidos:</p>
            <div className="grid grid-cols-4 gap-2">
              {['CTO-001','CTO-010','CTO-020','CTO-023','CTO-030','CTO-015','CTO-025','CTO-036'].map(c => (
                <button key={c} onClick={() => { setBoxCode(c); }}
                  className="text-xs font-mono bg-white border border-gray-200 rounded px-2 py-1 hover:border-blue-400 hover:text-blue-700">
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* PASO 2: Seleccionar clientes afectados */}
      {step === 2 && box && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-800">{box.code} - {box.name}</h2>
            <p className="text-gray-500 text-sm">{box.full_path}</p>
            <p className="text-gray-400 text-xs mt-1">{box.client_count} clientes registrados</p>
          </div>
          <h3 className="font-semibold text-gray-700 mb-3">Selecciona los clientes afectados:</h3>
          <div className="space-y-2 mb-6 max-h-80 overflow-y-auto border border-gray-100 rounded-lg p-2">
            {clients.map(c => (
              <div key={c.id} onClick={() => toggleClient(c.id)}
                className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                  selectedClients.includes(c.id) ? 'border-red-400 bg-red-50' : 'border-gray-200 hover:border-blue-300'
                }`}>
                <div className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center ${
                  selectedClients.includes(c.id) ? 'bg-red-500 border-red-500' : 'border-gray-300'
                }`}>
                  {selectedClients.includes(c.id) && <span className="text-white text-xs">\u2713</span>}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-sm">{c.full_name}</p>
                  <p className="text-xs text-gray-500">{c.client_code} - {c.address}</p>
                </div>
                {c.optical_power_rx && (
                  <span className={`text-xs font-mono px-2 py-1 rounded ${
                    parseFloat(c.optical_power_rx) < -25 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {c.optical_power_rx} dBm
                  </span>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setStep(1)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700">
              Atras
            </button>
            <button onClick={runDiagnosis} disabled={loading}
              className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">
              {loading ? 'Analizando red...' : `Diagnosticar ${selectedClients.length} cliente(s) afectado(s)`}
            </button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}
        </div>
      )}

      {/* PASO 3: RESULTADO DEL DIAGNOSTICO */}
      {step === 3 && result && (
        <div className="space-y-6">
          {/* Header de severidad */}
          <div className={`rounded-xl shadow-sm border p-6 ${severityClass}`}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">
                  {severityEmoji} DIAGNOSTICO: {severityTitle}
                </h2>
                <p className="text-sm mt-1 opacity-80">
                  Confianza: <strong>{result.confidence || 0}%</strong>
                </p>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-bold text-white ${
                result.severity === 'critical' ? 'bg-red-600'
                : result.severity === 'high' ? 'bg-orange-500'
                : result.severity === 'medium' ? 'bg-blue-500'
                : 'bg-green-500'
              }`}>
                {result.severity?.toUpperCase()}
              </div>
            </div>
          </div>

          {/* FALLO DETECTADO */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-bold text-gray-800 mb-4 text-lg">&#128205; FALLO DETECTADO</h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              {result.fault_location?.description && (
                <p className="text-gray-800 font-semibold">{result.fault_location.description}</p>
              )}
              {result.affected_segment && (
                <>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">Tramo:</span> {result.affected_segment.from_node || result.affected_segment.origin_name || 'Splitter'} 
                    {' \u2192 '} 
                    {result.affected_segment.to_node || result.affected_segment.destination_name || 'Caja'}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">Cable:</span> {result.affected_segment.cable || result.affected_segment.cable_code || 'N/A'}
                    {result.affected_segment.fiber_numbers && `, Fibra #${Array.isArray(result.affected_segment.fiber_numbers) ? result.affected_segment.fiber_numbers.join(', #') : result.affected_segment.fiber_numbers}`}
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">Longitud:</span> {result.affected_segment.length_m || '?'} metros
                  </p>
                </>
              )}
              {!result.affected_segment && result.fault_location?.description && (
                <p className="text-sm text-gray-600">{result.fault_location.description}</p>
              )}
            </div>
          </div>

          {/* ANALISIS DE POTENCIA */}
          {result.power_analysis && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">&#128202; ANALISIS DE POTENCIA</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-green-50 rounded-lg text-center border border-green-200">
                  <p className="text-sm text-green-600 mb-1">Potencia esperada</p>
                  <p className="text-2xl font-bold text-green-800">{result.power_analysis.expected_dbm} dBm</p>
                  <div className="power-bar-bg mt-2">
                    <div className="power-bar-fill bg-green-500" style={{ width: '90%' }} />
                  </div>
                </div>
                <div className="p-4 bg-red-50 rounded-lg text-center border border-red-200">
                  <p className="text-sm text-red-600 mb-1">Potencia medida</p>
                  <p className="text-2xl font-bold text-red-800">{result.power_analysis.measured_dbm} dBm</p>
                  <div className="power-bar-bg mt-2">
                    <div className="power-bar-fill bg-red-500" style={{ width: '15%' }} />
                  </div>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg text-center border border-orange-200">
                  <p className="text-sm text-orange-600 mb-1">Perdida total</p>
                  <p className="text-2xl font-bold text-orange-800">{result.power_analysis.loss_db} dB</p>
                  <p className="text-xs text-orange-600 mt-1 font-bold">
                    {result.power_analysis.status || '\u26A0\uFE0F CORTE TOTAL'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* UBICACION */}
          {result.fault_location && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">&#127759; UBICACION</h3>
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <p className="text-gray-800">
                  <span className="font-semibold">Direccion:</span> {result.fault_location.address || 'N/A'}
                </p>
                {result.fault_location.coordinates && (
                  <p className="text-sm text-gray-500 font-mono">
                    Coordenadas: {result.fault_location.coordinates[0]?.toFixed(4)}, {result.fault_location.coordinates[1]?.toFixed(4)}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ACCION RECOMENDADA */}
          {result.recommended_action && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">&#128295; ACCION RECOMENDADA</h3>
              <div className="bg-blue-50 rounded-lg border border-blue-100 p-4">
                <div className="space-y-3">
                  {result.recommended_action.split('\n').map((line, i) => {
                    const match = line.match(/^(\d+)\.\s*(.+)$/);
                    if (match) {
                      return (
                        <div key={i} className="flex items-start gap-3">
                          <div className="step-number">{match[1]}</div>
                          <p className="text-sm text-blue-900 pt-1">{match[2]}</p>
                        </div>
                      );
                    }
                    return <p key={i} className="text-sm text-blue-900">{line}</p>;
                  })}
                </div>
              </div>
            </div>
          )}

          {/* MAPA DEL TRAMO AFECTADO */}
          {result.affected_route && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">&#127758; MAPA DEL TRAMO AFECTADO</h3>
              <div ref={miniMapRef} className="w-full h-64 rounded-lg border border-gray-200" />
            </div>
          )}

          {/* CLIENTES AFECTADOS */}
          {result.affected_clients && result.affected_clients.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                &#128101; CLIENTES AFECTADOS ({result.affected_clients.length})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600">
                    <tr>
                      <th className="px-3 py-2 text-left">#</th>
                      <th className="px-3 py-2 text-left">Codigo</th>
                      <th className="px-3 py-2 text-left">Nombre</th>
                      <th className="px-3 py-2 text-center">Potencia</th>
                      <th className="px-3 py-2 text-center">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {result.affected_clients.map((c, i) => (
                      <tr key={i} className="hover:bg-red-50">
                        <td className="px-3 py-2 text-gray-500">{i + 1}</td>
                        <td className="px-3 py-2 font-mono text-sm">{c.client_code || c.code}</td>
                        <td className="px-3 py-2">{c.full_name || c.name}</td>
                        <td className="px-3 py-2 text-center font-mono">
                          {c.power_dbm || c.optical_power_rx || '-'} dBm
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span className="text-red-600 font-bold">&#128308;</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Boton nuevo diagnostico */}
          <button onClick={reset}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700">
              Nuevo diagnostico
          </button>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   7. TOPOLOGY - Arbol jerarquico expandible
   ============================================================ */

function TopologyNode({ node, level = 0 }) {
  const [expanded, setExpanded] = useState(level < 3);
  const hasChildren = node.children && node.children.length > 0;

  const indent = level * 20;

  return (
    <div className="topology-tree">
      <div
        className="flex items-center gap-1 py-1 px-1 rounded hover:bg-gray-50 cursor-pointer select-none"
        style={{ paddingLeft: (indent + 8) + 'px' }}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {/* Expand/collapse icon */}
        <span className="expand-btn w-4 text-center text-gray-400 text-xs">
          {hasChildren ? (expanded ? '\u25BC' : '\u25B6') : ''}
        </span>

        {/* Type icon */}
        <span className="text-sm mr-1">
          {node.type === 'olt' && '\uD83D\uDCE1'}
          {node.type === 'cable' && node.cable_type === 'feeder' && '\uD83D\udd34'}
          {node.type === 'cable' && node.cable_type === 'distribution' && '\uD83D\udd35'}
          {node.type === 'cable' && node.cable_type === 'drop' && '\uD83D\udfe2'}
          {node.type === 'splice' && '\u26ab'}
          {node.type === 'splitter' && '\u2B50'}
          {node.type === 'box' && '\u25A1'}
          {node.type === 'zone_group' && '\uD83C\uDFD8'}
        </span>

        {/* Name and code */}
        <span className="text-sm font-semibold text-gray-800 truncate" title={node.name}>
          {node.name}
        </span>

        {/* Code badge */}
        {node.code && node.code !== node.name && (
          <span className="text-[10px] text-gray-400 font-mono ml-1">{node.code}</span>
        )}

        {/* Type badge */}
        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ml-1 ${
          node.type === 'olt' ? 'bg-red-100 text-red-700'
          : node.type === 'cable' && node.cable_type === 'feeder' ? 'bg-red-100 text-red-700'
          : node.type === 'cable' && node.cable_type === 'distribution' ? 'bg-blue-100 text-blue-700'
          : node.type === 'cable' && node.cable_type === 'drop' ? 'bg-green-100 text-green-700'
          : node.type === 'splice' ? 'bg-yellow-100 text-yellow-700'
          : node.type === 'splitter' ? 'bg-orange-100 text-orange-700'
          : node.type === 'box' ? 'bg-blue-100 text-blue-700'
          : 'bg-gray-100 text-gray-600'
        }`}>
          {node.type === 'cable' ? node.cable_type : node.type}
        </span>

        {/* Extra info */}
        {node.ratio && (
          <span className="text-[10px] text-orange-600 ml-1">1:{node.ratio}</span>
        )}
        {node.output_power_dbm && (
          <span className="text-[10px] text-gray-500 ml-1">{node.output_power_dbm}dBm</span>
        )}
        {node.fiber_count !== undefined && (
          <span className="text-[10px] text-gray-400 ml-1">
            {node.fibers_used || node.used_fibers || 0}/{node.fiber_count}f
          </span>
        )}
        {node.client_count !== undefined && (
          <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full ml-1">
            {node.client_count}cli
          </span>
        )}
        {node.affected_count > 0 && (
          <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full ml-1 font-bold">
            {node.affected_count}
          </span>
        )}
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div>
          {node.children.map((child, i) => (
            <TopologyNode key={i} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function Topology() {
  const [topology, setTopology] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const t = await fetchAPI('/api/topology/');
      setTopology(t);
      setLoading(false);
    };
    load();
  }, []);

  const buildTree = () => {
    if (!topology) return null;

    // OLT root
    const root = {
      type: 'olt',
      name: topology.olt?.name || 'OLT-CIEZA-01',
      code: topology.olt?.code,
      output_power_dbm: topology.olt?.output_power_dbm,
      ratio: topology.olt?.splitter_ratio,
      children: []
    };

    // Process each zone branch
    const zonesData = topology.zones || [];
    zonesData.forEach(z => {
      const zoneNode = {
        type: 'zone_group',
        name: z.zone?.name || 'Zona',
        code: z.zone?.code,
        client_count: z.zone?.client_count,
        affected_count: z.zone?.affected_client_count,
        children: []
      };

      // Feeder cables for this zone
      (z.cables || []).filter(c => c.cable_type === 'feeder').forEach(c => {
        zoneNode.children.push({
          type: 'cable',
          name: c.code,
          code: c.code,
          cable_type: 'feeder',
          fiber_count: c.fiber_count,
          fibers_used: c.fibers_used || c.used_fibers,
          children: []
        });
      });

      // Splice -> splitter -> drop cable -> boxes
      if (z.splice) {
        const spliceNode = {
          type: 'splice',
          name: z.splice.name || z.splice.code,
          code: z.splice.code,
          fiber_count: z.splice.fiber_capacity,
          fibers_used: z.splice.fiber_count_used,
          children: []
        };

        // Splitters connected to this splice
        (z.splitters || []).forEach(spl => {
          const splitterNode = {
            type: 'splitter',
            name: spl.name || spl.code,
            code: spl.code,
            ratio: spl.ratio,
            output_power_dbm: spl.output_power_dbm,
            client_count: spl.client_count,
            affected_count: spl.affected_count,
            children: []
          };

          // Drop cables from this splitter
          (z.cables || []).filter(c => c.cable_type === 'drop').forEach(dc => {
            const dropNode = {
              type: 'cable',
              name: dc.code,
              code: dc.code,
              cable_type: 'drop',
              fiber_count: dc.fiber_count,
              fibers_used: dc.fibers_used || dc.used_fibers,
              children: []
            };

            // Boxes on this drop cable
            (z.boxes || []).filter(b => b.input_cable_code === dc.code).forEach(b => {
              dropNode.children.push({
                type: 'box',
                name: b.name,
                code: b.code,
                client_count: b.client_count,
                affected_count: b.affected_count,
                output_power_dbm: b.measured_power_dbm || b.expected_power_dbm,
                fiber_number: b.input_fiber_number,
                children: []
              });
            });

            if (dropNode.children.length > 0) {
              splitterNode.children.push(dropNode);
            }
          });

          spliceNode.children.push(splitterNode);
        });

        zoneNode.children.push(spliceNode);
      }

      root.children.push(zoneNode);
    });

    return root;
  };

  const tree = buildTree();

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Cargando topologia...</div>;
  }

  const boxCount = topology?.zones?.reduce((s, z) => s + (z.boxes?.length || 0), 0) || 0;
  const totalClients = topology?.zones?.reduce((s, z) => s + (z.zone?.client_count || 0), 0) || 0;
  const totalAffected = topology?.zones?.reduce((s, z) => s + (z.zone?.affected_client_count || 0), 0) || 0;
  const cableCount = topology?.zones?.reduce((s, z) => s + (z.cables?.length || 0), 0) || 0;
  const spliceCount = topology?.zones?.reduce((s, z) => s + (z.splice ? 1 : 0), 0) || 0;
  const splitterCount = topology?.zones?.reduce((s, z) => s + (z.splitters?.length || 0), 0) || 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { l: 'OLT', v: 1, c: 'text-red-600' },
          { l: 'Zonas', v: topology?.zones?.length || 0, c: 'text-purple-600' },
          { l: 'Cables', v: cableCount, c: 'text-blue-600' },
          { l: 'Cajas', v: boxCount, c: 'text-blue-600' },
          { l: 'Clientes', v: totalClients, c: totalAffected > 0 ? 'text-red-600' : 'text-green-600' },
        ].map((s, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-4 border border-gray-100 text-center">
            <p className={`text-3xl font-bold ${s.c}`}>{s.v}</p>
            <p className="text-xs text-gray-500 mt-1">{s.l}</p>
          </div>
        ))}
      </div>

      {/* Tree */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">&#127795; Topologia de Red</h2>
          <p className="text-xs text-gray-500">OLT &rarr; Feeder &rarr; Splice &rarr; Distribution &rarr; Splitter &rarr; Drop &rarr; Cajas</p>
        </div>
        <div className="p-4 max-h-[70vh] overflow-y-auto">
          {tree ? <TopologyNode node={tree} /> : (
            <div className="text-center text-gray-400 py-8">No hay datos de topologia disponibles</div>
          )}
        </div>
      </div>

      {/* Cable details */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">&#128225; Cables por Zona</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 text-left">Cable</th>
                <th className="px-4 py-2 text-left">Tipo</th>
                <th className="px-4 py-2 text-left">Zona</th>
                <th className="px-4 py-2 text-center">Fibras</th>
                <th className="px-4 py-2 text-center">Usadas</th>
                <th className="px-4 py-2 text-center">Longitud</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(topology?.zones || []).flatMap(z =>
                (z.cables || []).map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono font-semibold">{c.code}</td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        c.cable_type === 'feeder' ? 'bg-red-100 text-red-700'
                        : c.cable_type === 'distribution' ? 'bg-blue-100 text-blue-700'
                        : 'bg-green-100 text-green-700'
                      }`}>{c.cable_type}</span>
                    </td>
                    <td className="px-4 py-2 text-xs">{z.zone?.name}</td>
                    <td className="px-4 py-2 text-center">{c.fiber_count}</td>
                    <td className="px-4 py-2 text-center">{c.fibers_used || c.used_fibers || 0}</td>
                    <td className="px-4 py-2 text-center">{c.length_m}m</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   8. SIMULATE
   ============================================================ */

function Simulate() {
  const [boxes, setBoxes] = useState([]);
  const [splitters, setSplitters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [simType, setSimType] = useState('box');

  useEffect(() => {
    fetchAPI('/api/boxes/').then(b => setBoxes(b || []));
    fetchAPI('/api/splitters/').then(s => setSplitters(s || []));
  }, []);

  const simulateRandom = async () => {
    setLoading(true);

    if (simType === 'box') {
      const activeBoxes = boxes.filter(b => b.client_count > 0);
      const targetBox = activeBoxes[Math.floor(Math.random() * activeBoxes.length)];
      if (targetBox) {
        const boxClients = await fetchAPI('/api/boxes/' + targetBox.id + '/clients/');
        const clientList = boxClients || [];
        const numAffected = Math.min(Math.floor(Math.random() * 3) + 1, clientList.length);
        const affectedClients = clientList.sort(() => 0.5 - Math.random()).slice(0, numAffected);
        for (const c of affectedClients) {
          await postAPI('/api/clients/report_outage/', { client_id: c.id });
        }
        setResult({
          type: 'box',
          box: targetBox,
          affectedCount: affectedClients.length
        });
      }
    } else {
      const targetSpl = splitters[Math.floor(Math.random() * splitters.length)];
      if (targetSpl) {
        const allBoxes = await fetchAPI('/api/boxes/');
        const splBoxes = (allBoxes || []).filter(b => b.splitter_code === targetSpl.code);
        let count = 0;
        for (const b of splBoxes) {
          const boxClients = await fetchAPI('/api/boxes/' + b.id + '/clients/');
          for (const c of (boxClients || []).slice(0, 2)) {
            await postAPI('/api/clients/report_outage/', { client_id: c.id });
            count++;
          }
        }
        setResult({
          type: 'splitter',
          splitter: targetSpl,
          affectedCount: count
        });
      }
    }

    const updated = await fetchAPI('/api/boxes/');
    setBoxes(updated || []);
    setLoading(false);
  };

  const resetAll = async () => {
    setLoading(true);
    setResult(null);
    const allBoxes = await fetchAPI('/api/boxes/');
    for (const b of (allBoxes || [])) {
      const clients = await fetchAPI('/api/boxes/' + b.id + '/clients/');
      for (const c of (clients || [])) {
        if (c.status === 'affected') {
          await fetch(API_URL + '/api/clients/' + c.id + '/', {
            method: 'PATCH',
            headers: apiHeaders(),
            body: JSON.stringify({ status: 'active' })
          });
        }
      }
    }
    const updated = await fetchAPI('/api/boxes/');
    setBoxes(updated || []);
    setLoading(false);
  };

  const affectedBoxes = boxes.filter(b => (b.affected_count || 0) > 0);
  const totalAffected = affectedBoxes.reduce((s, b) => s + (b.affected_count || 0), 0);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <h2 className="text-xl font-bold text-gray-800 mb-2">Simulador de Averias</h2>
        <p className="text-gray-500 mb-6">Inyecta averias aleatorias para probar el algoritmo de diagnostico.</p>

        <div className="flex gap-2 mb-6">
          <button onClick={() => setSimType('box')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              simType === 'box' ? 'bg-blue-100 text-blue-700 border-2 border-blue-300' : 'bg-gray-50 text-gray-600 border border-gray-200'
            }`}>
            A nivel de Caja
          </button>
          <button onClick={() => setSimType('splitter')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              simType === 'splitter' ? 'bg-orange-100 text-orange-700 border-2 border-orange-300' : 'bg-gray-50 text-gray-600 border border-gray-200'
            }`}>
            A nivel de Splitter
          </button>
        </div>

        <div className="flex gap-4 mb-6">
          <button onClick={simulateRandom} disabled={loading}
            className="flex-1 px-6 py-4 bg-red-500 text-white rounded-lg font-bold text-lg hover:bg-red-600 disabled:opacity-50">
            {loading ? '...' : 'Simular averia'}
          </button>
          <button onClick={resetAll} disabled={loading}
            className="px-6 py-4 bg-green-500 text-white rounded-lg font-bold hover:bg-green-600 disabled:opacity-50">
            Restaurar todo
          </button>
        </div>

        {result && (
          <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h3 className="font-bold text-orange-800 mb-2">Simulacion ejecutada</h3>
            <p className="text-sm text-orange-700">
              {result.type === 'box'
                ? `${result.affectedCount} cliente(s) de ${result.box.code} marcados como afectados.`
                : `${result.affectedCount} cliente(s) del splitter ${result.splitter.code} afectados.`}
            </p>
          </div>
        )}

        <div className="border-t border-gray-100 pt-6">
          <h3 className="font-bold text-gray-700 mb-4">Estado actual</h3>
          {affectedBoxes.length === 0 ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
              <p className="text-green-700 font-semibold text-lg">&#9989; Todo operativo</p>
              <p className="text-green-600 text-sm mt-1">No hay clientes afectados</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-600">{affectedBoxes.length} caja(s) con averias</span>
                <span className="text-sm font-bold text-red-600">{totalAffected} cliente(s) afectado(s)</span>
              </div>
              {affectedBoxes.map(b => (
                <div key={b.id} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div>
                    <span className="font-mono font-bold text-red-800">{b.code}</span>
                    <span className="text-sm text-gray-600 ml-2">{b.name}</span>
                  </div>
                  <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">{b.affected_count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   9. APP ROOT
   ============================================================ */

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!getToken());
  const [activeTab, setActiveTab] = useState('dashboard');

  if (!isLoggedIn) {
    return <LoginScreen onLogin={() => setIsLoggedIn(true)} />;
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'dashboard': return <Dashboard />;
      case 'map': return <NetworkMap />;
      case 'topology': return <Topology />;
      case 'diagnose': return <DiagnoseV2 />;
      case 'simulate': return <Simulate />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      <main>{renderTab()}</main>
      <footer className="bg-gray-800 text-gray-400 text-center py-4 text-sm mt-8">
        <p>FiberTruck v2.0 - TFM Master Full Stack</p>
        <p>Despliegue FTTH ficticio de Cieza, Murcia</p>
      </footer>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
