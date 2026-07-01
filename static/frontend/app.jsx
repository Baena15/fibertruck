const { useState, useEffect } = React;
const API_URL = window.location.hostname === 'localhost'
  ? 'http://localhost:8000/api' : '/api';

const ZONE_COLORS = {
  'Z-ERA': '#e74c3c', 'Z-SJOR': '#f39c12',
  'Z-SJOA': '#3498db', 'Z-SJBO': '#2ecc71', 'Z-HORT': '#9b59b6'
};

const CABLE_COLORS = {
  feeder: '#dc2626',
  distribution: '#2563eb',
  drop: '#16a34a',
  fault: '#f59e0b'
};

const SEVERITY_STYLES = {
  critical: { bg: 'bg-red-100', text: 'text-red-800',
    border: 'border-red-400', badge: 'bg-red-600' },
  high: { bg: 'bg-orange-100', text: 'text-orange-800',
    border: 'border-orange-400', badge: 'bg-orange-500' },
  medium: { bg: 'bg-yellow-100', text: 'text-yellow-800',
    border: 'border-yellow-400', badge: 'bg-yellow-500' },
  low: { bg: 'bg-blue-100', text: 'text-blue-800',
    border: 'border-blue-400', badge: 'bg-blue-500' }
};

const getToken = () => localStorage.getItem('ft_token');

const getUser = () => {
  try { return JSON.parse(localStorage.getItem('ft_user')); }
  catch { return null; }
};

const apiHeaders = () => {
  const t = getToken();
  const h = { 'Content-Type': 'application/json' };
  if (t) h['Authorization'] = `Bearer ${t}`;
  return h;
};

const logout = () => {
  localStorage.removeItem('ft_token');
  localStorage.removeItem('ft_refresh');
  localStorage.removeItem('ft_user');
  window.location.reload();
};

const fetchAPI = async (endpoint) => {
  try {
    const r = await fetch(`${API_URL}${endpoint}`,
      { headers: apiHeaders() });
    if (r.status === 401) { logout(); return null; }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) { console.error(e); return null; }
};

const postAPI = async (endpoint, body) => {
  try {
    const r = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST', headers: apiHeaders(),
      body: JSON.stringify(body)
    });
    if (r.status === 401) { logout(); return null; }
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) { console.error(e); return null; }
};

/* ============================================================
   LOGIN SCREEN
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
      const r = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const d = await r.json();
      if (r.ok && d.access) {
        localStorage.setItem('ft_token', d.access);
        localStorage.setItem('ft_refresh', d.refresh);
        const m = await fetch(`${API_URL}/auth/me/`, {
          headers: { 'Authorization': `Bearer ${d.access}` }
        });
        if (m.ok) {
          localStorage.setItem('ft_user', JSON.stringify(await m.json()));
        }
        onLogin();
      } else {
        setError(d.detail || 'Usuario o contrasena incorrectos');
      }
    } catch { setError('Error de conexion'); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-800
      to-blue-900 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <span className="text-4xl">&#128667;</span>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">
            FiberTruck
          </h1>
          <p className="text-gray-500 text-sm">
            Diagnostico FTTH - Cieza, Murcia
          </p>
          <p className="text-xs text-blue-500 mt-1">v2.0</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <input type="text" value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Usuario"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg
              focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required />
          <input type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Contrasena"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg
              focus:ring-2 focus:ring-blue-500 focus:outline-none"
            required />
          {error && (
            <p className="text-red-600 text-sm bg-red-50 p-2 rounded">
              &#9888; {error}
            </p>
          )}
          <button type="submit" disabled={loading}
            className="w-full py-2 bg-blue-600 text-white rounded-lg
              font-semibold hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-2 font-semibold">
            Usuarios de prueba:
          </p>
          <div className="grid grid-cols-3 gap-2">
            { [
                ['admin','admin123'],
                ['tecnico1','tecno123'],
                ['supervisor1','super123']
              ].map(([u, p]) => (
              <button key={u}
                onClick={() => { setUsername(u); setPassword(p); }}
                className="text-xs bg-white border border-gray-200
                  rounded px-2 py-1 hover:border-blue-400
                  hover:text-blue-700">
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
   HEADER
   ============================================================ */

function Header({ activeTab, setActiveTab }) {
  const user = getUser();
  const roleLabels = {
    admin: 'Admin',
    technician: 'Tecnico',
    supervisor: 'Supervisor'
  };
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '\uD83D\uDCCA',
      roles: ['admin', 'technician', 'supervisor'] },
    { id: 'map', label: 'Mapa', icon: '\uD83D\uDDFA',
      roles: ['admin', 'technician', 'supervisor'] },
    { id: 'topology', label: 'Red', icon: '\uD83C\uDF10',
      roles: ['admin', 'technician', 'supervisor'] },
    { id: 'diagnose', label: 'Diagnostico', icon: '\uD83D\uDD0D',
      roles: ['admin', 'technician', 'supervisor'] },
    { id: 'simulate', label: 'Simular', icon: '\u26A1',
      roles: ['admin', 'supervisor'] },
  ];
  const visibleTabs = tabs.filter(t =>
    !user?.role || t.roles.includes(user.role)
  );

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
            {visibleTabs.map(t => (
              <button key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium
                  transition-colors ${activeTab === t.id
                    ? 'bg-blue-600 text-white'
                    : 'text-blue-200 hover:bg-blue-700 hover:text-white'}`}>
                {t.icon} {t.label}
              </button>
            ))}
          </nav>
          <div className="flex items-center space-x-3">
            <span className="text-xs bg-blue-700 px-2 py-1 rounded-full">
              {roleLabels[user?.role] || ''}
            </span>
            <span className="text-sm font-medium">
              {user?.first_name || user?.username}
            </span>
            <button onClick={logout}
              className="text-xs text-blue-300 hover:text-white"
              title="Cerrar sesion">
              Salir
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

/* ============================================================
   DASHBOARD
   ============================================================ */

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [cables, setCables] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [s, z, c] = await Promise.all([
        fetchAPI('/incidents/stats/'),
        fetchAPI('/zones/'),
        fetchAPI('/cables/')
      ]);
      setStats(s);
      setZones(z?.results || z || []);
      setCables(c?.results || c || []);
      setLoading(false);
    };
    load();
    const iv = setInterval(load, 10000);
    return () => clearInterval(iv);
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Cargando dashboard...
      </div>
    );
  }

  const totalFibers = cables.reduce((sum, c) =>
    sum + (c.fiber_count || 0), 0);
  const totalLength = cables.reduce((sum, c) =>
    sum + (parseFloat(c.length_m) || 0), 0);

  const feederCables = cables.filter(c => c.cable_type === 'feeder');
  const distCables = cables.filter(c => c.cable_type === 'distribution');
  const dropCables = cables.filter(c => c.cable_type === 'drop');

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        { [
          { l: 'OLTs', v: stats?.olt_count || 1,
            c: 'bg-blue-500', i: '\uD83D\uDCE1' },
          { l: 'Zonas', v: stats?.zone_count || 5,
            c: 'bg-purple-500', i: '\uD83C\uDFD8' },
          { l: 'Cajas CTO', v: stats?.active_boxes || 29,
            c: 'bg-blue-500', i: '\uD83D\uDCE6' },
          { l: 'Clientes', v: stats?.total_clients || 161,
            c: 'bg-green-500', i: '\uD83D\uDC65' },
          { l: 'Afectados',
            v: stats?.affected_clients || 0,
            c: stats?.affected_clients > 0
              ? 'bg-red-500' : 'bg-green-500',
            i: '\u26A0' },
          { l: 'Incidencias',
            v: stats?.open_incidents || 0,
            c: 'bg-orange-500', i: '\uD83D\uDEA8' },
        ].map((s, i) => (
          <div key={i}
            className="bg-white rounded-xl shadow-sm p-4
              border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">{s.i}</span>
              <span className={`text-xs font-bold text-white px-2
                py-0.5 rounded-full ${s.c}`}>
                {s.l}
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-800">{s.v}</p>
          </div>
        ))}
      </div>

      {/* Cables Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm
          border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-800">
              &#128225; Cables de Red
            </h2>
            <p className="text-xs text-gray-500">
              {cables.length} cables &bull; {totalFibers} fibras
              &bull; {(totalLength / 1000).toFixed(1)} km total
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-2 text-left">Codigo</th>
                  <th className="px-4 py-2 text-left">Tipo</th>
                  <th className="px-4 py-2 text-center">Fibras</th>
                  <th className="px-4 py-2 text-center">Long.(m)</th>
                  <th className="px-4 py-2 text-center">Usadas</th>
                  <th className="px-4 py-2 text-center">Util.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {cables.map(c => {
                  const used = c.used_fibers || 0;
                  const total = c.fiber_count || 0;
                  const pct = total > 0 ? Math.round((used / total) * 100) : 0;
                  const barColor = pct > 80 ? 'bg-red-500'
                    : pct > 50 ? 'bg-yellow-500' : 'bg-green-500';
                  const typeLabel = c.cable_type === 'feeder' ? 'Feeder'
                    : c.cable_type === 'distribution' ? 'Distribution'
                    : 'Drop';
                  const typeColor = c.cable_type === 'feeder'
                    ? 'text-red-600 bg-red-50'
                    : c.cable_type === 'distribution'
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-green-600 bg-green-50';
                  return (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono font-semibold
                        text-gray-800">
                        {c.code}
                      </td>
                      <td className="px-4 py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full
                          font-medium ${typeColor}`}>
                          {typeLabel}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-center">{total}</td>
                      <td className="px-4 py-2 text-center">
                        {c.length_m}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {used}/{total}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full
                            h-2 max-w-[60px]">
                            <div className={`h-2 rounded-full ${barColor}`}
                              style={{width: `${pct}%`}} />
                          </div>
                          <span className="text-xs font-medium">{pct}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {cables.length === 0 && (
                  <tr>
                    <td colSpan="6"
                      className="px-4 py-8 text-center text-gray-400">
                      No hay cables registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Cable Type Summary */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100
          overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-800">
              &#128202; Resumen por Tipo
            </h2>
          </div>
          <div className="p-4 space-y-3">
            { [
                { type: 'feeder', label: 'Feeder (OLT)', color: '#dc2626',
                  list: feederCables },
                { type: 'distribution', label: 'Distribution',
                  color: '#2563eb', list: distCables },
                { type: 'drop', label: 'Drop (ultima milla)',
                  color: '#16a34a', list: dropCables },
              ].map(({ type, label, color, list }) => {
              const fibers = list.reduce((s, c) =>
                s + (c.fiber_count || 0), 0);
              const used = list.reduce((s, c) =>
                s + (c.used_fibers || 0), 0);
              const len = list.reduce((s, c) =>
                s + (parseFloat(c.length_m) || 0), 0);
              const pct = fibers > 0 ? Math.round((used / fibers) * 100) : 0;
              return (
                <div key={type} className="p-3 rounded-lg border"
                  style={{borderColor: color + '30',
                    backgroundColor: color + '08'}}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full"
                      style={{backgroundColor: color}} />
                    <span className="font-semibold text-sm text-gray-800">
                      {label}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-lg font-bold"
                        style={{color}}>{list.length}</p>
                      <p className="text-xs text-gray-500">cables</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold"
                        style={{color}}>{fibers}</p>
                      <p className="text-xs text-gray-500">fibras</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold"
                        style={{color}}>{(len/1000).toFixed(1)}km</p>
                      <p className="text-xs text-gray-500">longitud</p>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span>Utilizacion</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="bg-gray-200 rounded-full h-2">
                      <div className="h-2 rounded-full transition-all"
                        style={{width: `${pct}%`, backgroundColor: color}} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Zones */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100
        overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">
            &#127968; Zonas de Despliegue (Barrios de Cieza)
          </h2>
        </div>
        <div className="divide-y divide-gray-50">
          {zones.map(z => (
            <div key={z.id}
              className="px-6 py-4 flex items-center justify-between
                hover:bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded-full"
                  style={{backgroundColor: ZONE_COLORS[z.code] || '#666'}} />
                <span className="text-sm font-mono text-gray-500 mr-2">
                  {z.code}
                </span>
                <span className="font-semibold text-gray-800">
                  {z.name}
                </span>
              </div>
              <div className="flex items-center space-x-6 text-sm">
                <span className="text-gray-500">
                  &#128101; {z.population_estimate?.toLocaleString()} hab.
                </span>
                <span className="text-blue-600 font-semibold">
                  {z.client_count} clientes
                </span>
                {z.affected_client_count > 0 && (
                  <span className="text-red-600 font-bold bg-red-50 px-2
                    py-0.5 rounded-full">
                    &#9888; {z.affected_client_count}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   NETWORK MAP (replaces FiberMap)
   ============================================================ */

function NetworkMap() {
  const [boxes, setBoxes] = useState([]);
  const [zones, setZones] = useState([]);
  const [cables, setCables] = useState([]);
  const [splices, setSplices] = useState([]);
  const [splitters, setSplitters] = useState([]);
  const [segments, setSegments] = useState([]);
  const [selectedBox, setSelectedBox] = useState(null);
  const [boxClients, setBoxClients] = useState([]);
  const [selectedCable, setSelectedCable] = useState(null);
  const [selectedSplice, setSelectedSplice] = useState(null);
  const [showLayer, setShowLayer] = useState({
    feeder: true, distribution: true, drop: true,
    boxes: true, splices: true, splitters: true
  });
  const [loading, setLoading] = useState(true);

  const mapRef = React.useRef(null);
  const leafletMap = React.useRef(null);
  const layersRef = React.useRef({});

  // Load data
  useEffect(() => {
    const load = async () => {
      const [b, z, c, sp, spl, seg] = await Promise.all([
        fetchAPI('/boxes/'),
        fetchAPI('/zones/'),
        fetchAPI('/cables/'),
        fetchAPI('/splices/'),
        fetchAPI('/splitters/'),
        fetchAPI('/segments/')
      ]);
      setBoxes(b?.results || b || []);
      setZones(z?.results || z || []);
      setCables(c?.results || c || []);
      setSplices(sp?.results || sp || []);
      setSplitters(spl?.results || spl || []);
      setSegments(seg?.results || seg || []);
      setLoading(false);
    };
    load();
  }, []);

  // Initialize map
  useEffect(() => {
    if (!leafletMap.current && mapRef.current) {
      leafletMap.current = L.map(mapRef.current)
        .setView([38.2395, -1.4165], 15);
      L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        { attribution: '&copy; OpenStreetMap', maxZoom: 19 }
      ).addTo(leafletMap.current);
    }
    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, []);

  // Draw all layers
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
      zones: L.layerGroup()
    };

    // Draw zone circles
    zones.forEach(z => {
      const color = ZONE_COLORS[z.code] || '#666';
      L.circle([z.latitude, z.longitude], {
        radius: 350, color, fillColor: color,
        fillOpacity: 0.06, weight: 2, dashArray: '5,5'
      }).addTo(layerGroups.zones)
        .bindPopup(`<b>${z.name}</b><br/>${z.code}<br/>
          ${z.client_count} clientes`);
    });

    // Draw cable segments as polylines
    segments.forEach(seg => {
      const cable = cables.find(c => c.id === seg.cable) || {};
      const cType = cable.cable_type || 'drop';
      if (!showLayer[cType]) return;

      const route = seg.route_as_list || seg.route || [];
      if (route.length < 2) return;

      const color = cType === 'feeder' ? CABLE_COLORS.feeder
        : cType === 'distribution' ? CABLE_COLORS.distribution
        : CABLE_COLORS.drop;
      const weight = cType === 'feeder' ? 4
        : cType === 'distribution' ? 3 : 2;
      const dash = cType === 'feeder' ? '10,5'
        : cType === 'drop' ? '5,5' : null;

      const poly = L.polyline(route, {
        color, weight,
        dashArray: dash,
        opacity: 0.85
      }).addTo(layerGroups[cType]);

      const usedFibers = cable.used_fibers || 0;
      const totalFibers = cable.fiber_count || 0;
      const popupContent = `
        <div style="min-width:180px">
          <b style="color:${color}">${cable.code || 'Tramo ' + seg.id}</b><br/>
          <small>Tipo: <b>${cType.toUpperCase()}</b></small><br/>
          <small>Cable: ${cable.code || 'N/A'}</small><br/>
          <small>Fibras: ${usedFibers}/${totalFibers}</small><br/>
          <small>Longitud: ${seg.length_m || cable.length_m || '?'}m</small>
        </div>
      `;
      poly.bindPopup(popupContent);
      poly.on('click', () => {
        setSelectedCable({...cable, segment: seg});
        setSelectedSplice(null);
      });
    });

    // Draw splices (empalmes)
    if (showLayer.splices) {
      splices.forEach(sp => {
        if (!sp.latitude || !sp.longitude) return;
        const usedFibers = sp.used_fibers || 0;
        const totalFibers = sp.fiber_capacity || 0;
        const freeFibers = totalFibers - usedFibers;

        const marker = L.circleMarker([sp.latitude, sp.longitude], {
          radius: 10, fillColor: '#1f2937',
          color: '#fbbf24', weight: 3, fillOpacity: 0.9
        }).addTo(layerGroups.splices)
          .bindPopup(`
            <div style="min-width:160px">
              <b>${sp.code || sp.name}</b><br/>
              <small>Tipo: ${sp.splice_type || 'Fusion'}</small><br/>
              <small>Fibras: ${totalFibers}</small><br/>
              <small style="color:green">Libres: ${freeFibers}</small><br/>
              <small style="color:red">Usadas: ${usedFibers}</small>
            </div>
          `);
        marker.on('click', () => {
          setSelectedSplice(sp);
          setSelectedCable(null);
        });
      });
    }

    // Draw splitters
    if (showLayer.splitters) {
      splitters.forEach(spl => {
        if (!spl.latitude || !spl.longitude) return;
        const color = spl.splitter_type === 'zone_root'
          ? '#dc2626' : '#f97316';
        const radius = spl.splitter_type === 'zone_root' ? 12 : 9;

        const marker = L.circleMarker(
          [spl.latitude, spl.longitude], {
            radius, fillColor: color,
            color: '#fff', weight: 2, fillOpacity: 0.9
          }).addTo(layerGroups.splitters)
            .bindPopup(`
              <div style="min-width:160px">
                <b style="color:${color}">${spl.code || spl.name}</b><br/>
                <small>Tipo: ${spl.splitter_type_display || spl.splitter_type}</small><br/>
                <small>Ratio: 1:${spl.ratio || '?'}</small><br/>
                <small>Zona: ${spl.zone_name || 'N/A'}</small>
              </div>
            `);
        marker.on('click', () => setSelectedSplice(null));
      });
    }

    // Draw boxes (CTOs)
    if (showLayer.boxes) {
      boxes.forEach(b => {
        const color = b.status === 'fault' ? '#dc2626'
          : (ZONE_COLORS[b.zone_code || b.zone] || '#0ea5e9');
        const isAffected = b.affected_count > 0;

        L.circleMarker([b.latitude, b.longitude], {
          radius: isAffected ? 14 : 10,
          fillColor: color,
          color: isAffected ? '#dc2626' : '#fff',
          weight: isAffected ? 3 : 2,
          fillOpacity: isAffected ? 0.9 : 0.7
        }).addTo(layerGroups.boxes)
          .bindPopup(`
            <b>${b.code}</b><br/>
            ${b.name}<br/>
            ${b.client_count} clientes
            ${isAffected
              ? `<br/><span style="color:red">${b.affected_count} afectados</span>`
              : ''}
          `)
          .on('click', async () => {
            setSelectedBox(b);
            setSelectedCable(null);
            setSelectedSplice(null);
            const c = await fetchAPI(`/boxes/${b.id}/clients/`);
            setBoxClients(c || []);
          });
      });
    }

    // Add all layer groups to map
    Object.entries(layerGroups).forEach(([key, group]) => {
      if (key === 'zones' || showLayer[key] !== false) {
        group.addTo(leafletMap.current);
      }
      layersRef.current[key] = group;
    });
  }, [boxes, zones, cables, splices, splitters, segments,
      showLayer, loading]);

  const toggleLayer = (layer) => {
    setShowLayer(p => ({...p, [layer]: !p[layer]}));
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Cargando mapa de red...
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Layer controls */}
      <div className="mb-4 flex flex-wrap gap-2">
        { [
          { k: 'feeder', l: 'Feeder', c: 'bg-red-100 text-red-700' },
          { k: 'distribution', l: 'Distribution',
            c: 'bg-blue-100 text-blue-700' },
          { k: 'drop', l: 'Drop', c: 'bg-green-100 text-green-700' },
          { k: 'boxes', l: 'Cajas CTO', c: 'bg-gray-100 text-gray-700' },
          { k: 'splices', l: 'Empalmes',
            c: 'bg-yellow-100 text-yellow-700' },
          { k: 'splitters', l: 'Splitters',
            c: 'bg-orange-100 text-orange-700' },
        ].map(item => (
          <button key={item.k}
            onClick={() => toggleLayer(item.k)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium
              border transition-all ${showLayer[item.k]
                ? item.c + ' border-current'
                : 'bg-gray-50 text-gray-400 border-gray-200'}`}>
            {showLayer[item.k] ? '\u2713' : '\u2717'} {item.l}
          </button>
        ))}
        <button onClick={() => {
          if (leafletMap.current) {
            leafletMap.current.setView([38.2395, -1.4165], 15);
          }
        }} className="px-3 py-1.5 rounded-lg text-xs font-medium
          bg-gray-100 text-gray-600 border border-gray-200
          hover:bg-gray-200 ml-auto">
          Centrar
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-4" style={{height: '70vh'}}>
        {/* Map */}
        <div className="flex-1 bg-white rounded-xl shadow-sm
          border border-gray-100 overflow-hidden relative">
          <div ref={mapRef} style={{height: '100%', width: '100%'}} />
          {/* Legend */}
          <div className="absolute bottom-3 right-3 bg-white/90
            backdrop-blur-sm rounded-lg shadow-md p-3 text-xs
            border border-gray-200 z-[500]">
            <p className="font-bold text-gray-700 mb-2">Leyenda</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <div className="w-6 rounded"
                  style={{background: '#dc2626', height: '4px'}} />
                <span>Feeder (OLT)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 rounded"
                  style={{background: '#2563eb', height: '3px'}} />
                <span>Distribution</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 rounded"
                  style={{background: '#16a34a', height: '2px'}} />
                <span>Drop</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full"
                  style={{background: '#1f2937',
                    border: '2px solid #fbbf24'}} />
                <span>Empalme</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full"
                  style={{background: '#f97316'}} />
                <span>Splitter</span>
              </div>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        <div className="w-full lg:w-96 bg-white rounded-xl shadow-sm
          border border-gray-100 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h3 className="font-bold text-gray-800">
              Elementos de Red
            </h3>
            <p className="text-xs text-gray-500">
              {boxes.length} cajas &bull; {splices.length} empalmes
              &bull; {splitters.length} splitters
            </p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Selected Cable */}
            {selectedCable && (
              <div className="p-3 rounded-lg border border-blue-200
                bg-blue-50">
                <h4 className="font-bold text-blue-800 mb-2">
                  {selectedCable.code}
                </h4>
                <p className="text-sm text-blue-700 capitalize">
                  Tipo: {selectedCable.cable_type}
                </p>
                <p className="text-sm text-blue-700">
                  Fibras: {selectedCable.used_fibers || 0}/
                  {selectedCable.fiber_count || 0}
                </p>
                <p className="text-sm text-blue-700">
                  Longitud: {selectedCable.length_m}m
                </p>
                {selectedCable.segments && (
                  <p className="text-sm text-blue-700">
                    Tramos: {selectedCable.segments.length}
                  </p>
                )}
              </div>
            )}
            {/* Selected Splice */}
            {selectedSplice && (
              <div className="p-3 rounded-lg border border-yellow-200
                bg-yellow-50">
                <h4 className="font-bold text-yellow-800 mb-2">
                  {selectedSplice.code || selectedSplice.name}
                </h4>
                <p className="text-sm text-yellow-700">
                  Tipo: {selectedSplice.splice_type || 'Fusion'}
                </p>
                <p className="text-sm text-yellow-700">
                  Fibras: {selectedSplice.fiber_capacity || 0}
                </p>
                <p className="text-sm text-yellow-700">
                  Libres: {(selectedSplice.fiber_capacity || 0) -
                    (selectedSplice.used_fibers || 0)}
                </p>
              </div>
            )}
            {/* Selected Box */}
            {selectedBox && (
              <div className="p-3 rounded-lg border border-gray-200
                bg-gray-50">
                <h4 className="font-bold text-gray-800 mb-2">
                  {selectedBox.code}
                </h4>
                <p className="text-sm text-gray-600 mb-1">
                  {selectedBox.name}
                </p>
                <p className="text-xs text-gray-400 mb-2">
                  {selectedBox.full_path}
                </p>
                <p className="text-sm mb-2">
                  {boxClients.length} clientes:
                </p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {boxClients.map(c => (
                    <div key={c.id}
                      className={`text-xs px-2 py-1 rounded ${
                        c.status === 'affected'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-green-50 text-green-700'}`}>
                      {c.client_code} - {c.full_name}
                      {c.optical_power_rx
                        && ` (${c.optical_power_rx} dBm)`}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {!selectedBox && !selectedCable && !selectedSplice && (
              <div className="text-center text-gray-400 py-8">
                <p className="text-3xl mb-2">&#128506;</p>
                <p className="text-sm">Haz clic en un elemento del mapa</p>
                <p className="text-xs">para ver sus detalles</p>
              </div>
            )}
          </div>
          {/* Boxes list */}
          <div className="border-t border-gray-200 max-h-48 overflow-y-auto">
            <div className="px-4 py-2 bg-gray-50 text-xs font-semibold
              text-gray-600">
              Cajas ({boxes.length})
            </div>
            {boxes.map(b => (
              <div key={b.id}
                className={`px-4 py-2 border-b border-gray-50
                  cursor-pointer hover:bg-blue-50 transition-colors ${
                  selectedBox?.id === b.id
                    ? 'bg-blue-100 border-l-4 border-l-blue-500' : ''}`}
                onClick={() => {
                  setSelectedBox(b);
                  if (leafletMap.current) {
                    leafletMap.current.setView(
                      [b.latitude, b.longitude], 17);
                  }
                  fetchAPI(`/boxes/${b.id}/clients/`)
                    .then(c => setBoxClients(c || []));
                }}>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold
                    text-blue-700">{b.code}</span>
                  {b.affected_count > 0 && (
                    <span className="text-xs bg-red-100 text-red-700
                      px-1.5 py-0.5 rounded-full font-bold">
                      {b.affected_count}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 truncate">
                  {b.name}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   DIAGNOSE V2
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

  const searchBox = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchAPI(
        `/boxes/search/?code=${boxCode.toUpperCase()}`);
      if (data && !data.error) {
        setBox(data);
        const c = await fetchAPI(`/boxes/${data.id}/clients/`);
        setClients(c || []);
        setStep(2);
      } else {
        setError(data?.error || 'Caja no encontrada');
      }
    } catch {
      setError('Error al buscar caja');
    }
    setLoading(false);
  };

  const runDiagnosis = async () => {
    if (selectedClients.length === 0) {
      setError('Selecciona al menos un cliente');
      return;
    }
    setLoading(true);
    setError('');

    for (const cid of selectedClients) {
      await postAPI('/clients/report_outage/', { client_id: cid });
    }

    const diagnosis = await postAPI('/diagnose/v2/', {
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
    setSelectedClients(p =>
      p.includes(id) ? p.filter(x => x !== id) : [...p, id]
    );
  };

  const reset = () => {
    setStep(1);
    setBoxCode('');
    setBox(null);
    setClients([]);
    setSelectedClients([]);
    setResult(null);
    setError('');
  };

  // Mini map for affected route
  useEffect(() => {
    if (step === 3 && result?.affected_route && miniMapRef.current) {
      if (!miniLeafletMap.current) {
        miniLeafletMap.current = L.map(miniMapRef.current);
        L.tileLayer(
          'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
          { attribution: '&copy; OSM', maxZoom: 19 }
        ).addTo(miniLeafletMap.current);
      }
      const route = result.affected_route;
      if (route.length >= 2) {
        miniLeafletMap.current.eachLayer(l => {
          if (l instanceof L.Polyline && !(l instanceof L.TileLayer)) {
            miniLeafletMap.current.removeLayer(l);
          }
        });
        L.polyline(route, {
          color: '#dc2626', weight: 5,
          dashArray: '8,4', opacity: 0.9
        }).addTo(miniLeafletMap.current);
        L.circleMarker(route[0], {
          radius: 6, fillColor: '#16a34a',
          color: '#fff', weight: 2
        }).addTo(miniLeafletMap.current)
          .bindPopup('Origen');
        L.circleMarker(route[route.length - 1], {
          radius: 6, fillColor: '#dc2626',
          color: '#fff', weight: 2
        }).addTo(miniLeafletMap.current)
          .bindPopup('Destino (caja)');
        const bounds = L.latLngBounds(route);
        miniLeafletMap.current.fitBounds(bounds.pad(0.3));
      }
    }
    return () => {
      if (miniLeafletMap.current) {
        miniLeafletMap.current.remove();
        miniLeafletMap.current = null;
      }
    };
  }, [step, result]);

  const sev = result?.severity || 'medium';
  const sevStyle = SEVERITY_STYLES[sev] || SEVERITY_STYLES.medium;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Wizard Steps */}
      <div className="flex items-center mb-8">
        { ['Introducir Caja', 'Seleccionar Afectados',
            'Resultado'].map((s, i) => (
          <React.Fragment key={i}>
            <div className={`flex items-center justify-center w-10 h-10
              rounded-full font-bold text-sm ${
              step > i + 1 ? 'bg-green-500 text-white'
              : step === i + 1 ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-500'}`}>
              {step > i + 1 ? '\u2713' : i + 1}
            </div>
            {i < 2 && (
              <div className={`flex-1 h-1 mx-2 ${
                step > i + 1 ? 'bg-green-500' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Enter Box Code */}
      {step === 1 && (
        <div className="bg-white rounded-xl shadow-sm border
          border-gray-100 p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-2">
            Codigo de caja
          </h2>
          <p className="text-gray-500 mb-6">
            Introduce el codigo de la caja a diagnosticar
          </p>
          <div className="flex gap-3">
            <input type="text" value={boxCode}
              onChange={e => setBoxCode(e.target.value.toUpperCase())}
              onKeyPress={e => e.key === 'Enter' && searchBox()}
              placeholder="Ej: CTO-023"
              className="flex-1 px-4 py-3 border-2 border-gray-200
                rounded-lg focus:border-blue-500 focus:outline-none
                text-lg font-mono uppercase" />
            <button onClick={searchBox}
              disabled={loading || !boxCode}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg
                font-semibold hover:bg-blue-700 disabled:opacity-50">
              {loading ? '...' : 'Buscar'}
            </button>
          </div>
          {error && (
            <p className="mt-3 text-red-600 text-sm bg-red-50 p-2
              rounded">{error}</p>
          )}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm font-semibold text-gray-600 mb-2">
              Ejemplos:
            </p>
            <div className="grid grid-cols-4 gap-2">
              { ['CTO-001','CTO-010','CTO-020','CTO-023',
                  'CTO-030','CTO-015','CTO-025','CTO-036'
                ].map(c => (
                <button key={c}
                  onClick={() => setBoxCode(c)}
                  className="text-xs font-mono bg-white border
                    border-gray-200 rounded px-2 py-1
                    hover:border-blue-400 hover:text-blue-700">
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Select Affected Clients */}
      {step === 2 && box && (
        <div className="bg-white rounded-xl shadow-sm border
          border-gray-100 p-8">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              {box.code} - {box.name}
            </h2>
            <p className="text-gray-500 text-sm">{box.full_path}</p>
          </div>
          <h3 className="font-semibold text-gray-700 mb-3">
            Selecciona clientes afectados:
          </h3>
          <div className="space-y-2 mb-6 max-h-80 overflow-y-auto">
            {clients.map(c => (
              <div key={c.id}
                onClick={() => toggleClient(c.id)}
                className={`flex items-center p-3 rounded-lg border-2
                  cursor-pointer transition-colors ${
                  selectedClients.includes(c.id)
                    ? 'border-red-400 bg-red-50'
                    : 'border-gray-200 hover:border-blue-300'}`}>
                <div className={`w-5 h-5 rounded border-2 mr-3 flex
                  items-center justify-center ${
                  selectedClients.includes(c.id)
                    ? 'bg-red-500 border-red-500'
                    : 'border-gray-300'}`}>
                  {selectedClients.includes(c.id) && (
                    <span className="text-white text-xs">\u2713</span>
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-sm">{c.full_name}</p>
                  <p className="text-xs text-gray-500">
                    {c.client_code} - {c.address}
                  </p>
                </div>
                {c.optical_power_rx && (
                  <span className={`text-xs font-mono px-2 py-1 rounded ${
                    parseFloat(c.optical_power_rx) < -25
                      ? 'bg-red-100 text-red-700'
                      : 'bg-green-100 text-green-700'}`}>
                    {c.optical_power_rx} dBm
                  </span>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setStep(1)}
              className="px-4 py-2 border border-gray-300 rounded-lg
                hover:bg-gray-50">
              Atras
            </button>
            <button onClick={runDiagnosis}
              disabled={loading}
              className="flex-1 px-4 py-3 bg-blue-600 text-white
                rounded-lg font-semibold hover:bg-blue-700
                disabled:opacity-50">
              {loading ? 'Analizando...'
                : `Diagnosticar ${selectedClients.length} afectados`}
            </button>
          </div>
          {error && (
            <p className="mt-3 text-red-600 text-sm">{error}</p>
          )}
        </div>
      )}

      {/* Step 3: Detailed Result */}
      {step === 3 && result && (
        <div className="space-y-6">
          {/* Severity Header */}
          <div className={`rounded-xl shadow-sm border-2 p-6
            ${sevStyle.bg} ${sevStyle.border}`}>
            <div className="flex items-start justify-between">
              <div>
                <h2 className={`text-xl font-bold mb-1 ${sevStyle.text}`}>
                  {sev === 'critical' ? 'DIAGNOSTICO: CRITICO'
                  : sev === 'high' ? 'DIAGNOSTICO: ALTO'
                  : sev === 'medium'
                    ? 'DIAGNOSTICO: MEDIO'
                    : 'DIAGNOSTICO: BAJO'}
                </h2>
                <p className="text-sm opacity-70">
                  Confianza: <strong>{result.confidence}%</strong>
                </p>
              </div>
              <div className={`px-4 py-1.5 rounded-full text-sm
                font-bold text-white ${sevStyle.badge}`}>
                {sev.toUpperCase()}
              </div>
            </div>
          </div>

          {/* Fault Location */}
          {result.affected_segment && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                FALLO DETECTADO
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Tramo</p>
                  <p className="font-semibold text-gray-800">
                    {result.affected_segment.from_node || 'Splitter'}
                    {' -> '}
                    {result.affected_segment.to_node || 'Caja'}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Cable</p>
                  <p className="font-semibold text-gray-800">
                    {result.affected_segment.cable || 'N/A'}
                  </p>
                </div>
                {result.affected_segment.fiber_numbers && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500 mb-1">Fibras</p>
                    <p className="font-semibold text-gray-800">
                      {Array.isArray(result.affected_segment.fiber_numbers)
                        ? result.affected_segment.fiber_numbers.join(', ')
                        : result.affected_segment.fiber_numbers}
                    </p>
                  </div>
                )}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500 mb-1">Tipo</p>
                  <p className="font-semibold capitalize text-gray-800">
                    {result.affected_segment.segment_type || 'drop'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Power Analysis */}
          {result.power_analysis && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                ANALISIS DE POTENCIA
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-green-50 rounded-lg text-center">
                  <p className="text-sm text-green-600 mb-1">Esperada</p>
                  <p className="text-2xl font-bold text-green-800">
                    {result.power_analysis.expected_dbm} dBm
                  </p>
                </div>
                <div className="p-4 bg-red-50 rounded-lg text-center">
                  <p className="text-sm text-red-600 mb-1">Medida</p>
                  <p className="text-2xl font-bold text-red-800">
                    {result.power_analysis.measured_dbm} dBm
                  </p>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg text-center">
                  <p className="text-sm text-orange-600 mb-1">Perdida</p>
                  <p className="text-2xl font-bold text-orange-800">
                    {result.power_analysis.loss_db} dB
                  </p>
                  <p className="text-xs text-orange-600 mt-1">
                    {result.power_analysis.status || 'CORTE TOTAL'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Fault Location Details */}
          {result.fault_location && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                UBICACION
              </h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-800 mb-1">
                  <strong>Direccion:</strong>
                  {' '}{result.fault_location.address || 'N/A'}
                </p>
                {result.fault_location.coordinates && (
                  <p className="text-sm text-gray-500 font-mono">
                    {result.fault_location.coordinates[0].toFixed(4)},
                    {' '}{result.fault_location.coordinates[1].toFixed(4)}
                  </p>
                )}
                {result.fault_location.description && (
                  <p className="text-sm text-gray-600 mt-2">
                    {result.fault_location.description}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Recommended Action */}
          {result.recommended_action && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                ACCION RECOMENDADA
              </h3>
              <div className="p-4 bg-blue-50 rounded-lg border
                border-blue-100">
                <pre className="text-sm text-blue-900 whitespace-pre-wrap
                  font-sans leading-relaxed">
                  {result.recommended_action}
                </pre>
              </div>
            </div>
          )}

          {/* Affected Route Map */}
          {result.affected_route && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-4 text-lg">
                MAPA DEL TRAMO AFECTADO
              </h3>
              <div ref={miniMapRef}
                className="w-full h-64 rounded-lg border
                  border-gray-200" />
            </div>
          )}

          {/* Affected Clients */}
          {result.affected_clients && (
            <div className="bg-white rounded-xl shadow-sm border
              border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-3 text-lg">
                CLIENTES AFECTADOS
                {' '}({result.affected_clients.length})
              </h3>
              <div className="space-y-2">
                {result.affected_clients.map((c, i) => (
                  <div key={i}
                    className="flex items-center justify-between p-3
                      bg-red-50 rounded-lg">
                    <div>
                      <span className="text-sm font-semibold text-red-800
                        block">
                        {c.client_code || c.code}
                      </span>
                      <span className="text-sm text-red-600">
                        {c.full_name || c.name}
                      </span>
                    </div>
                    {c.address && (
                      <span className="text-xs text-gray-500">
                        {c.address}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reset Button */}
          <button onClick={reset}
            className="w-full px-4 py-3 bg-blue-600 text-white
              rounded-lg font-semibold hover:bg-blue-700">
            Nuevo diagnostico
          </button>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   TOPOLOGY
   ============================================================ */

function TopologyNode({ node, level = 0 }) {
  const [expanded, setExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;

  const getIcon = () => {
    const t = node.type;
    if (t === 'olt') return '\uD83D\uDCE1';
    if (t === 'splice') return '\u2696';
    if (t === 'splitter') return '\u2726';
    if (t === 'box') return '\uD83D\uDCE6';
    if (t === 'client') return '\uD83D\uDC64';
    if (t === 'cable') return '\uD83D\uDCE1';
    return '\u25CF';
  };

  const getTypeColor = () => {
    const t = node.type;
    if (t === 'olt') return '#2563eb';
    if (t === 'splice') return '#fbbf24';
    if (t === 'splitter') return '#f97316';
    if (t === 'box') return '#0ea5e9';
    if (t === 'client') return '#16a34a';
    if (t === 'cable') return '#dc2626';
    return '#666';
  };

  const getTypeLabel = () => {
    const t = node.type;
    if (t === 'olt') return 'OLT';
    if (t === 'cable' && node.cable_type === 'feeder')
      return 'Feeder';
    if (t === 'cable' && node.cable_type === 'distribution')
      return 'Distribution';
    if (t === 'cable' && node.cable_type === 'drop')
      return 'Drop';
    if (t === 'cable') return 'Cable';
    if (t === 'splice') return 'Empalme';
    if (t === 'splitter') return 'Splitter';
    if (t === 'box') return 'CTO';
    if (t === 'client') return 'Cliente';
    return t;
  };

  return (
    <div className="select-none">
      <div
        className="flex items-center gap-2 py-1.5 px-2 rounded-lg
          hover:bg-gray-50 cursor-pointer transition-colors"
        style={{paddingLeft: `${level * 20 + 8}px`}}
        onClick={() => hasChildren && setExpanded(!expanded)}>
        {hasChildren ? (
          <span className="text-gray-400 text-xs w-4 text-center">
            {expanded ? '\u25BC' : '\u25B6'}
          </span>
        ) : (
          <span className="w-4" />
        )}
        <span className="text-lg">{getIcon()}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-gray-800
              truncate">
              {node.name || node.code || 'Sin nombre'}
            </span>
            <span
              className="text-[10px] px-1.5 py-0.5 rounded-full
                font-medium text-white"
              style={{backgroundColor: getTypeColor()}}>
              {getTypeLabel()}
            </span>
          </div>
          {node.code && node.code !== node.name && (
            <span className="text-xs text-gray-400 font-mono">
              {node.code}
            </span>
          )}
        </div>
        {node.fiber_count && (
          <span className="text-xs text-gray-500">
            {node.used_fibers || 0}/{node.fiber_count} fibras
          </span>
        )}
        {node.client_count !== undefined && (
          <span className="text-xs bg-blue-100 text-blue-700 px-2
            py-0.5 rounded-full">
            {node.client_count} cli.
          </span>
        )}
        {node.affected_count > 0 && (
          <span className="text-xs bg-red-100 text-red-700 px-2
            py-0.5 rounded-full font-bold">
            {node.affected_count}
          </span>
        )}
      </div>
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
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const load = async () => {
      const t = await fetchAPI('/topology/');
      setTopology(t);
      setLoading(false);
    };
    load();
  }, []);

  const buildTree = () => {
    if (!topology || !topology.olt) return null;

    const root = {
      type: 'olt',
      name: topology.olt.name,
      code: topology.olt.code,
      fiber_count: topology.olt.fiber_capacity,
      children: []
    };

    // Add feeder cables
    (topology.cables || [])
      .filter(c => c.cable_type === 'feeder')
      .forEach(c => {
        root.children.push({
          type: 'cable',
          name: c.code,
          code: c.code,
          cable_type: c.cable_type,
          fiber_count: c.fiber_count,
          used_fibers: c.used_fibers,
          children: []
        });
      });

    // Group by zone: splice -> splitter -> boxes
    const zoneGroups = {};
    (topology.splices || []).forEach(sp => {
      const zoneCode = sp.zone_code || 'General';
      if (!zoneGroups[zoneCode]) {
        zoneGroups[zoneCode] = {
          type: 'zone_group',
          name: sp.zone_name || zoneCode,
          code: zoneCode,
          color: ZONE_COLORS[zoneCode] || '#666',
          children: []
        };
      }
      const spliceNode = {
        type: 'splice',
        name: sp.name,
        code: sp.code,
        fiber_count: sp.fiber_capacity,
        used_fibers: sp.used_fibers,
        children: []
      };

      const connectedSplitters = (topology.splitters || []).filter(
        spl => spl.splice_code === sp.code
      );
      connectedSplitters.forEach(spl => {
        const splitterNode = {
          type: 'splitter',
          name: spl.name,
          code: spl.code,
          fiber_count: spl.ratio,
          client_count: spl.client_count || 0,
          affected_count: spl.affected_count || 0,
          children: []
        };

        const connectedBoxes = (topology.boxes || []).filter(
          b => b.splitter_code === spl.code
        );
        connectedBoxes.forEach(b => {
          splitterNode.children.push({
            type: 'box',
            name: b.name,
            code: b.code,
            client_count: b.client_count || 0,
            affected_count: b.affected_count || 0,
            children: []
          });
        });

        spliceNode.children.push(splitterNode);
      });

      zoneGroups[zoneCode].children.push(spliceNode);
    });

    Object.values(zoneGroups).forEach(zg => {
      root.children.push(zg);
    });

    return root;
  };

  const tree = buildTree();

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Cargando topologia...
      </div>
    );
  }

  const cableCount = topology?.cables?.length || 0;
  const spliceCount = topology?.splices?.length || 0;
  const splitterCount = topology?.splitters?.length || 0;
  const boxCount = topology?.boxes?.length || 0;
  const totalClients = (topology?.boxes || []).reduce(
    (s, b) => s + (b.client_count || 0), 0);
  const totalAffected = (topology?.boxes || []).reduce(
    (s, b) => s + (b.affected_count || 0), 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        { [
          { l: 'Cables', v: cableCount, c: 'text-red-600 bg-red-50' },
          { l: 'Empalmes', v: spliceCount,
            c: 'text-yellow-600 bg-yellow-50' },
          { l: 'Splitters', v: splitterCount,
            c: 'text-orange-600 bg-orange-50' },
          { l: 'Cajas', v: boxCount,
            c: 'text-blue-600 bg-blue-50' },
          { l: 'Clientes', v: totalClients,
            c: totalAffected > 0
              ? 'text-red-600 bg-red-50'
              : 'text-green-600 bg-green-50' },
        ].map((s, i) => (
          <div key={i}
            className="bg-white rounded-xl shadow-sm p-4 border
              border-gray-100 text-center">
            <p className={`text-3xl font-bold ${s.c.split(' ')[0]}`}>
              {s.v}
            </p>
            <p className="text-xs text-gray-500 mt-1">{s.l}</p>
          </div>
        ))}
      </div>

      {/* Topology Tree */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100
        overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex
          items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-lg font-bold text-gray-800">
              Topologia de Red
            </h2>
            <p className="text-xs text-gray-500">
              OLT &rarr; Splice &rarr; Splitter &rarr; Cajas &rarr; Clientes
            </p>
          </div>
          <div className="flex gap-2">
            <input type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Buscar elemento..."
              className="px-3 py-1.5 border border-gray-300 rounded-lg
                text-sm focus:outline-none focus:border-blue-500" />
          </div>
        </div>
        <div className="p-4 max-h-[60vh] overflow-y-auto">
          {tree ? (
            <TopologyNode node={tree} />
          ) : (
            <div className="text-center text-gray-400 py-8">
              No hay datos de topologia disponibles
            </div>
          )}
        </div>
      </div>

      {/* Cable Paths Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100
        overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-800">
            Rutas de Cable
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 text-left">Ruta</th>
                <th className="px-4 py-2 text-center">Fibras</th>
                <th className="px-4 py-2 text-center">Usadas</th>
                <th className="px-4 py-2 text-center">Cajas</th>
                <th className="px-4 py-2 text-center">Afectados</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(topology?.cables || [])
                .filter(c => c.cable_type === 'distribution')
                .map(c => {
                  const zoneBoxes = (topology?.boxes || []).filter(
                    b => b.zone_code === c.zone_code);
                  const zoneAffected = zoneBoxes.reduce(
                    (s, b) => s + (b.affected_count || 0), 0);
                  return (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2">
                        <span className="font-semibold text-blue-700">
                          {c.code}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          {c.zone_name}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-center">
                        {c.fiber_count}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span className={c.used_fibers > c.fiber_count * 0.8
                          ? 'text-red-600 font-bold'
                          : 'text-gray-600'}>
                          {c.used_fibers}/{c.fiber_count}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-center">
                        {zoneBoxes.length}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {zoneAffected > 0 ? (
                          <span className="text-red-600 font-bold
                            bg-red-50 px-2 py-0.5 rounded-full">
                            {zoneAffected}
                          </span>
                        ) : (
                          <span className="text-green-600">0</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   SIMULATE
   ============================================================ */

function Simulate() {
  const [boxes, setBoxes] = useState([]);
  const [splitters, setSplitters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [simType, setSimType] = useState('box');

  useEffect(() => {
    fetchAPI('/boxes/').then(b =>
      setBoxes(b?.results || b || []));
    fetchAPI('/splitters/').then(s =>
      setSplitters(s?.results || s || []));
  }, []);

  const simulateRandom = async () => {
    setLoading(true);
    const allClients = await fetchAPI('/clients/');
    const clientList = allClients?.results || allClients || [];

    if (simType === 'box') {
      const activeBoxes = boxes.filter(b => b.is_active);
      const targetBox = activeBoxes[
        Math.floor(Math.random() * activeBoxes.length)];
      if (targetBox) {
        const boxClients = clientList.filter(
          c => c.box === targetBox.id);
        const numAffected = Math.min(
          Math.floor(Math.random() * 3) + 2,
          boxClients.length);
        const affectedClients = boxClients
          .sort(() => 0.5 - Math.random())
          .slice(0, numAffected);
        for (const c of affectedClients) {
          await postAPI('/clients/report_outage/', { client_id: c.id });
        }
        setResult({
          type: 'box',
          box: targetBox,
          affectedCount: affectedClients.length
        });
      }
    } else {
      const targetSpl = splitters[
        Math.floor(Math.random() * splitters.length)];
      if (targetSpl) {
        const splClients = clientList.filter(
          c => c.splitter === targetSpl.id);
        for (const c of splClients.slice(0, 5)) {
          await postAPI('/clients/report_outage/', { client_id: c.id });
        }
        setResult({
          type: 'splitter',
          splitter: targetSpl,
          affectedCount: splClients.length
        });
      }
    }

    const updated = await fetchAPI('/boxes/');
    setBoxes(updated?.results || updated || []);
    setLoading(false);
  };

  const resetAll = async () => {
    setLoading(true);
    const allClients = await fetchAPI('/clients/');
    for (const c of (allClients?.results || allClients || [])) {
      if (c.status === 'affected') {
        await fetch(`${API_URL}/clients/${c.id}/`, {
          method: 'PATCH',
          headers: apiHeaders(),
          body: JSON.stringify({ status: 'active' })
        });
      }
    }
    setResult(null);
    const updated = await fetchAPI('/boxes/');
    setBoxes(updated?.results || updated || []);
    setLoading(false);
  };

  const affectedBoxes = boxes.filter(b => b.affected_count > 0);
  const totalAffected = affectedBoxes.reduce(
    (s, b) => s + b.affected_count, 0);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100
        p-8">
        <h2 className="text-xl font-bold text-gray-800 mb-2">
          Simulador de Averias
        </h2>
        <p className="text-gray-500 mb-6">
          Inyecta averias aleatorias para probar el algoritmo.
        </p>

        <div className="flex gap-2 mb-6">
          <button onClick={() => setSimType('box')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              simType === 'box'
                ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                : 'bg-gray-50 text-gray-600 border border-gray-200'}`}>
            A nivel de Caja
          </button>
          <button onClick={() => setSimType('splitter')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              simType === 'splitter'
                ? 'bg-orange-100 text-orange-700 border-2 border-orange-300'
                : 'bg-gray-50 text-gray-600 border border-gray-200'}`}>
            A nivel de Splitter
          </button>
        </div>

        <div className="flex gap-4 mb-6">
          <button onClick={simulateRandom} disabled={loading}
            className="flex-1 px-6 py-4 bg-red-500 text-white rounded-lg
              font-bold text-lg hover:bg-red-600 disabled:opacity-50">
            {loading ? '...' : 'Simular averia'}
          </button>
          <button onClick={resetAll} disabled={loading}
            className="px-6 py-4 bg-green-500 text-white rounded-lg
              font-bold hover:bg-green-600 disabled:opacity-50">
            Restaurar todo
          </button>
        </div>

        {result && (
          <div className="mb-6 p-4 bg-orange-50 border border-orange-200
            rounded-lg">
            <h3 className="font-bold text-orange-800 mb-2">
              Simulacion ejecutada
            </h3>
            <p className="text-sm text-orange-700">
              {result.type === 'box'
                ? `${result.affectedCount} clientes de
                    ${result.box.code} marcados como afectados.`
                : `${result.affectedCount} clientes del splitter
                    ${result.splitter.code} afectados.`}
            </p>
          </div>
        )}

        <div className="border-t border-gray-100 pt-6">
          <h3 className="font-bold text-gray-700 mb-4">
            Estado actual
          </h3>
          {affectedBoxes.length === 0 ? (
            <div className="p-4 bg-green-50 border border-green-200
              rounded-lg text-center">
              <p className="text-green-700 font-semibold text-lg">
                Todo operativo
              </p>
              <p className="text-green-600 text-sm mt-1">
                No hay clientes afectados
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-600">
                  {affectedBoxes.length} cajas con averias
                </span>
                <span className="text-sm font-bold text-red-600">
                  {totalAffected} clientes afectados
                </span>
              </div>
              {affectedBoxes.map(b => (
                <div key={b.id}
                  className="flex items-center justify-between p-3
                    bg-red-50 border border-red-200 rounded-lg">
                  <div>
                    <span className="font-mono font-bold text-red-800">
                      {b.code}
                    </span>
                    <span className="text-sm text-gray-600 ml-2">
                      {b.name}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">
                      {b.zone_name}
                    </span>
                  </div>
                  <span className="bg-red-500 text-white px-3 py-1
                    rounded-full text-sm font-bold">
                    {b.affected_count}
                  </span>
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
   APP
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
      <footer className="bg-gray-800 text-gray-400 text-center py-4
        text-sm mt-8">
        <p>FiberTruck v2.0 - TFM Master Full Stack</p>
        <p>Despliegue FTTH ficticio de Cieza, Murcia</p>
      </footer>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);