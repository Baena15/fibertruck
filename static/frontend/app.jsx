const { useState, useEffect } = React;
const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : '/api';
const ZONE_COLORS = {'Z-ERA': '#e74c3c', 'Z-SJOR': '#f39c12', 'Z-SJOA': '#3498db', 'Z-SJBO': '#2ecc71', 'Z-HORT': '#9b59b6'};

const getToken = () => localStorage.getItem('ft_token');
const getUser = () => { try { return JSON.parse(localStorage.getItem('ft_user')); } catch { return null; } };
const apiHeaders = () => { const t = getToken(); const h = {'Content-Type': 'application/json'}; if (t) h['Authorization'] = `Bearer ${t}`; return h; };
const logout = () => { localStorage.removeItem('ft_token'); localStorage.removeItem('ft_user'); window.location.reload(); };
const fetchAPI = async (endpoint) => { try { const r = await fetch(`${API_URL}${endpoint}`, {headers: apiHeaders()}); if (r.status === 401) { logout(); return null; } if (!r.ok) throw new Error(`HTTP ${r.status}`); return await r.json(); } catch (e) { console.error(e); return null; } };
const postAPI = async (endpoint, body) => { try { const r = await fetch(`${API_URL}${endpoint}`, {method: 'POST', headers: apiHeaders(), body: JSON.stringify(body)}); if (r.status === 401) { logout(); return null; } if (!r.ok) throw new Error(`HTTP ${r.status}`); return await r.json(); } catch (e) { console.error(e); return null; } };

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const r = await fetch(`${API_URL}/auth/login/`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username, password})});
      const d = await r.json();
      if (r.ok && d.access) {
        localStorage.setItem('ft_token', d.access); localStorage.setItem('ft_refresh', d.refresh);
        const m = await fetch(`${API_URL}/auth/me/`, {headers: {'Authorization': `Bearer ${d.access}`}});
        if (m.ok) localStorage.setItem('ft_user', JSON.stringify(await m.json()));
        onLogin();
      } else { setError(d.detail || 'Usuario o contrasena incorrectos'); }
    } catch { setError('Error de conexion'); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-800 to-blue-900 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <span className="text-4xl">🚛</span>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">FiberTruck</h1>
          <p className="text-gray-500 text-sm">Diagnostico FTTH - Cieza, Murcia</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Usuario" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Contrasena" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none" required />
          {error && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">⚠️ {error}</p>}
          <button type="submit" disabled={loading} className="w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">{loading ? '⏳...' : '🔑 Entrar'}</button>
        </form>
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-2 font-semibold">Usuarios de prueba:</p>
          <div className="grid grid-cols-3 gap-2">
            { [['admin','admin123'], ['tecnico1','tecno123'], ['supervisor1','super123'] ].map(([u,p]) => (
              <button key={u} onClick={() => {setUsername(u); setPassword(p);}} className="text-xs bg-white border border-gray-200 rounded px-2 py-1 hover:border-blue-400 hover:text-blue-700">{u}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Header({ activeTab, setActiveTab }) {
  const user = getUser();
  const roleLabels = { admin: '👨‍💼 Admin', technician: '🔧 Tecnico', supervisor: '📡 Supervisor' };
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', roles: ['admin', 'technician', 'supervisor'] },
    { id: 'map', label: 'Mapa', icon: '🗺️', roles: ['admin', 'technician', 'supervisor'] },
    { id: 'diagnose', label: 'Diagnostico', icon: '🔍', roles: ['admin', 'technician', 'supervisor'] },
    { id: 'simulate', label: 'Simular', icon: '⚡', roles: ['admin', 'supervisor'] },
  ];
  const visibleTabs = tabs.filter(t => !user?.role || t.roles.includes(user.role));

  return (
    <header className="bg-blue-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🚛</span>
            <div><h1 className="text-xl font-bold">FiberTruck</h1><p className="text-xs text-blue-200">Cieza, Murcia</p></div>
          </div>
          <nav className="flex space-x-1">
            {visibleTabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === t.id ? 'bg-blue-600 text-white' : 'text-blue-200 hover:bg-blue-700 hover:text-white'}`}>{t.icon} {t.label}</button>
            ))}
          </nav>
          <div className="flex items-center space-x-3">
            <span className="text-xs bg-blue-700 px-2 py-1 rounded-full">{roleLabels[user?.role]}</span>
            <span className="text-sm font-medium">{user?.first_name || user?.username}</span>
            <button onClick={logout} className="text-xs text-blue-300 hover:text-white" title="Cerrar sesion">🚪</button>
          </div>
        </div>
      </div>
    </header>
  );
}

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [s, z] = await Promise.all([fetchAPI('/incidents/stats/'), fetchAPI('/zones/')]);
      setStats(s); setZones(z?.results || z || []); setLoading(false);
    };
    load(); const iv = setInterval(load, 5000); return () => clearInterval(iv);
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          {l: 'OLTs', v: 1, c: 'bg-blue-500', i: '📡'}, {l: 'Zonas', v: 5, c: 'bg-purple-500', i: '🏘️'},
          {l: 'Cajas', v: stats?.active_boxes || 29, c: 'bg-blue-500', i: '📦'},
          {l: 'Clientes', v: stats?.total_clients || 161, c: 'bg-green-500', i: '👥'},
          {l: 'Afectados', v: stats?.affected_clients || 0, c: stats?.affected_clients > 0 ? 'bg-red-500' : 'bg-green-500', i: '⚠️'},
          {l: 'Incidencias', v: stats?.open_incidents || 0, c: 'bg-orange-500', i: '🚨'},
        ].map((s, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
            <div className="flex items-center justify-between mb-2"><span className="text-2xl">{s.i}</span><span className={`text-xs font-bold text-white px-2 py-0.5 rounded-full ${s.c}`}>{s.l}</span></div>
            <p className="text-3xl font-bold text-gray-800">{s.v}</p>
          </div>
        ))}
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100"><h2 className="text-lg font-bold text-gray-800">🏘️ Zonas de Despliegue (Barrios de Cieza)</h2></div>
        <div className="divide-y divide-gray-50">
          {zones.map(z => (
            <div key={z.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
              <div><span className="text-sm font-mono text-gray-500 mr-2">{z.code}</span><span className="font-semibold text-gray-800">{z.name}</span></div>
              <div className="flex items-center space-x-6 text-sm">
                <span className="text-gray-500">👥 {z.population_estimate?.toLocaleString()} hab.</span>
                <span className="text-blue-600 font-semibold">{z.client_count} clientes</span>
                {z.affected_client_count > 0 && <span className="text-red-600 font-bold bg-red-50 px-2 py-0.5 rounded-full">⚠️ {z.affected_client_count}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FiberMap() {
  const [boxes, setBoxes] = useState([]);
  const [zones, setZones] = useState([]);
  const [selectedBox, setSelectedBox] = useState(null);
  const [boxClients, setBoxClients] = useState([]);
  const mapRef = React.useRef(null);
  const leafletMap = React.useRef(null);

  useEffect(() => { const load = async () => { const [b, z] = await Promise.all([fetchAPI('/boxes/'), fetchAPI('/zones/')]); setBoxes(b?.results || b || []); setZones(z?.results || z || []); }; load(); }, []);

  useEffect(() => {
    if (!leafletMap.current && mapRef.current) {
      leafletMap.current = L.map(mapRef.current).setView([38.2395, -1.4165], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap', maxZoom: 19}).addTo(leafletMap.current);
    }
  }, []);

  useEffect(() => {
    if (!leafletMap.current || boxes.length === 0) return;
    leafletMap.current.eachLayer(l => { if (l instanceof L.Circle || l instanceof L.CircleMarker) leafletMap.current.removeLayer(l); });
    zones.forEach(z => { const color = ZONE_COLORS[z.code] || '#666'; L.circle([z.latitude, z.longitude], {radius: 300, color, fillColor: color, fillOpacity: 0.08, weight: 2, dashArray: '5,5'}).addTo(leafletMap.current).bindPopup(`<b>${z.name}</b><br/>${z.code}`); });
    boxes.forEach(b => {
      const color = b.status === 'fault' ? '#dc2626' : (ZONE_COLORS[b.zone] || '#0ea5e9');
      const isAffected = b.affected_count > 0;
      L.circleMarker([b.latitude, b.longitude], {radius: isAffected ? 14 : 10, fillColor: color, color: isAffected ? '#dc2626' : '#fff', weight: isAffected ? 3 : 2, fillOpacity: isAffected ? 0.9 : 0.7}).addTo(leafletMap.current).bindPopup(`<b>${b.code}</b><br/>${b.name}<br/>👥 ${b.client_count}${b.affected_count > 0 ? `<br/><span style="color:red">⚠️ ${b.affected_count} afectados</span>` : ''}`).on('click', async () => { setSelectedBox(b); const c = await fetchAPI(`/boxes/${b.id}/clients/`); setBoxClients(c || []); });
    });
  }, [boxes, zones]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="flex flex-col lg:flex-row gap-4" style={{height: '70vh'}}>
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"><div ref={mapRef} style={{height: '100%', width: '100%'}}></div></div>
        <div className="w-full lg:w-80 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50"><h3 className="font-bold text-gray-800">📦 Cajas ({boxes.length})</h3></div>
          <div className="flex-1 overflow-y-auto">
            {boxes.map(b => (
              <div key={b.id} className={`px-4 py-3 border-b border-gray-50 cursor-pointer hover:bg-blue-50 transition-colors ${selectedBox?.id === b.id ? 'bg-blue-100 border-l-4 border-l-blue-500' : ''}`}>
                <div className="flex items-center justify-between"><span className="font-mono text-sm font-bold text-blue-700">{b.code}</span>{b.affected_count > 0 && <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-bold">⚠️ {b.affected_count}</span>}</div>
                <p className="text-xs text-gray-600 truncate">{b.name}</p>
                <div className="flex items-center justify-between mt-1"><span className="text-xs text-gray-400">{b.zone_name}</span><span className="text-xs text-blue-600">{b.client_count} cli.</span></div>
              </div>
            ))}
          </div>
          {selectedBox && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <h4 className="font-bold text-blue-800 mb-2">{selectedBox.code}</h4>
              <p className="text-sm text-gray-600 mb-1">{selectedBox.name}</p>
              <p className="text-xs text-gray-400 mb-2">{selectedBox.full_path}</p>
              <p className="text-sm mb-2">👥 {boxClients.length} clientes:</p>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {boxClients.map(c => <div key={c.id} className={`text-xs px-2 py-1 rounded ${c.status === 'affected' ? 'bg-red-100 text-red-700' : 'bg-green-50 text-green-700'}`}>{c.client_code} - {c.full_name} {c.optical_power_rx && `(${c.optical_power_rx} dBm)`}</div>)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Diagnose() {
  const [step, setStep] = useState(1);
  const [boxCode, setBoxCode] = useState('');
  const [box, setBox] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClients, setSelectedClients] = useState([]);
  const [diagnosis, setDiagnosis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchBox = async () => { setLoading(true); setError(''); const data = await fetchAPI(`/boxes/search/?code=${boxCode.toUpperCase()}`); if (data && !data.error) { setBox(data); const c = await fetchAPI(`/boxes/${data.id}/clients/`); setClients(c || []); setStep(2); } else { setError(data?.error || 'Caja no encontrada'); } setLoading(false); };
  const runDiagnosis = async () => { if (selectedClients.length === 0) { setError('Selecciona al menos un cliente'); return; } setLoading(true); setError(''); for (const cid of selectedClients) { await postAPI('/clients/report_outage/', {client_id: cid}); } const c = await fetchAPI(`/boxes/${box.id}/clients/`); setClients(c || []); const affected = (c || []).filter(x => x.status === 'affected'); const total = affected.length; const isMulti = total >= 2; setDiagnosis({severity: total >= 3 ? 'critical' : isMulti ? 'high' : 'medium', confidence: total >= 3 ? 95 : isMulti ? 80 : 65, diagnosis_type: total >= 3 ? 'splitter_fault' : isMulti ? 'connector_fault' : 'unknown', root_cause_node: total >= 3 ? box.splitter_name : box.code, message: total >= 3 ? `ALERTA: ${total} clientes afectados. Problema en splitter ${box.splitter_name}.` : isMulti ? `${total} clientes afectados en ${box.code}. Revisar conectores.` : 'Problema individual. Revisar fibra de drop.', affected_total: total, recommended_action: total >= 3 ? 'Revisar splitter y fibra de alimentacion.' : isMulti ? 'Revisar conectores y splitter interno.' : 'Verificar ONT y fibra de drop.', affected_clients_details: affected.map(x => ({code: x.client_code, name: x.full_name, address: x.address}))}); setStep(3); setLoading(false); };
  const reset = () => { setStep(1); setBoxCode(''); setBox(null); setClients([]); setSelectedClients([]); setDiagnosis(null); setError(''); };
  const toggleClient = (id) => { setSelectedClients(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id]); };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center mb-8">
        {['Introducir Caja', 'Seleccionar Afectados', 'Resultado'].map((s, i) => (
          <React.Fragment key={i}>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-sm ${step > i+1 ? 'bg-green-500 text-white' : step === i+1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>{step > i+1 ? '✓' : i+1}</div>
            {i < 2 && <div className={`flex-1 h-1 mx-2 ${step > i+1 ? 'bg-green-500' : 'bg-gray-200'}`}></div>}
          </React.Fragment>
        ))}
      </div>

      {step === 1 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-2">📦 Numero de caja</h2>
          <p className="text-gray-500 mb-6">El tecnico introduce el codigo de la caja a diagnosticar</p>
          <div className="flex gap-3">
            <input type="text" value={boxCode} onChange={e => setBoxCode(e.target.value.toUpperCase())} onKeyPress={e => e.key === 'Enter' && searchBox()} placeholder="Ej: CTO-001" className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none text-lg font-mono uppercase" />
            <button onClick={searchBox} disabled={loading || !boxCode} className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">{loading ? '...' : '🔍 Buscar'}</button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">⚠️ {error}</p>}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm font-semibold text-gray-600 mb-2">💡 Ejemplos:</p>
            <div className="grid grid-cols-4 gap-2">
              {['CTO-001','CTO-010','CTO-020','CTO-030','CTO-040','CTO-015','CTO-025','CTO-036'].map(c => <button key={c} onClick={() => setBoxCode(c)} className="text-xs font-mono bg-white border border-gray-200 rounded px-2 py-1 hover:border-blue-400 hover:text-blue-700">{c}</button>)}
            </div>
          </div>
        </div>
      )}

      {step === 2 && box && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <div className="mb-6"><h2 className="text-xl font-bold text-gray-800">📦 {box.code} - {box.name}</h2><p className="text-gray-500 text-sm">{box.full_path}</p></div>
          <h3 className="font-semibold text-gray-700 mb-3">👥 Selecciona clientes afectados:</h3>
          <div className="space-y-2 mb-6">
            {clients.map(c => (
              <div key={c.id} onClick={() => toggleClient(c.id)} className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-colors ${selectedClients.includes(c.id) ? 'border-red-400 bg-red-50' : 'border-gray-200 hover:border-blue-300'}`}>
                <div className={`w-5 h-5 rounded border-2 mr-3 flex items-center justify-center ${selectedClients.includes(c.id) ? 'bg-red-500 border-red-500' : 'border-gray-300'}`}>{selectedClients.includes(c.id) && <span className="text-white text-xs">✓</span>}</div>
                <div className="flex-1"><p className="font-semibold text-sm">{c.full_name}</p><p className="text-xs text-gray-500">{c.client_code} - {c.address}</p></div>
                {c.optical_power_rx && <span className={`text-xs font-mono px-2 py-1 rounded ${parseFloat(c.optical_power_rx) < -25 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>{c.optical_power_rx} dBm</span>}
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">← Atras</button>
            <button onClick={runDiagnosis} disabled={loading} className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">{loading ? 'Analizando...' : `🔍 Diagnosticar ${selectedClients.length} afectados`}</button>
          </div>
          {error && <p className="mt-3 text-red-600 text-sm">⚠️ {error}</p>}
        </div>
      )}

      {step === 3 && diagnosis && (
        <div className="space-y-4">
          <div className={`diagnosis-card rounded-xl shadow-sm border p-6 severity-${diagnosis.severity}`}>
            <div className="flex items-start justify-between">
              <div><h2 className="text-xl font-bold mb-1">{diagnosis.severity === 'critical' ? '🚨 DIAGNOSTICO CRITICO' : diagnosis.severity === 'high' ? '⚠️ Multiples afectados' : 'ℹ️ Diagnostico Individual'}</h2><p className="text-sm opacity-70">Confianza: <strong>{diagnosis.confidence}%</strong></p></div>
              <div className={`px-3 py-1 rounded-full text-sm font-bold ${diagnosis.severity === 'critical' ? 'bg-red-600 text-white' : diagnosis.severity === 'high' ? 'bg-orange-500 text-white' : 'bg-blue-500 text-white'}`}>{diagnosis.severity.toUpperCase()}</div>
            </div>
            <div className="mt-4 p-4 bg-white/60 rounded-lg"><p className="text-lg font-medium">{diagnosis.message}</p></div>
            <div className="mt-4"><p className="font-semibold text-sm mb-2">🔧 Accion recomendada:</p><p className="text-sm bg-white/60 p-3 rounded-lg">{diagnosis.recommended_action}</p></div>
          </div>
          {diagnosis.affected_clients_details?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-800 mb-3">👥 Afectados ({diagnosis.affected_clients_details.length})</h3>
              <div className="space-y-2">{diagnosis.affected_clients_details.map((c, i) => <div key={i} className="flex items-center justify-between p-2 bg-red-50 rounded-lg"><span className="text-sm font-semibold text-red-800">{c.code}</span><span className="text-sm text-red-600">{c.name}</span></div>)}</div>
            </div>
          )}
          <button onClick={reset} className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700">🔄 Nuevo diagnostico</button>
        </div>
      )}
    </div>
  );
}

function Simulate() {
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => { fetchAPI('/boxes/').then(b => setBoxes(b?.results || b || [])); }, []);

  const simulateRandom = async () => {
    setLoading(true);
    const allClients = await fetchAPI('/clients/');
    const clientList = allClients?.results || allClients || [];
    const activeBoxes = boxes.filter(b => b.is_active);
    const targetBox = activeBoxes[Math.floor(Math.random() * activeBoxes.length)];
    if (targetBox) {
      const boxClients = clientList.filter(c => c.box === targetBox.id);
      const numAffected = Math.min(Math.floor(Math.random() * 3) + 2, boxClients.length);
      const affectedClients = boxClients.sort(() => 0.5 - Math.random()).slice(0, numAffected);
      for (const c of affectedClients) { await postAPI('/clients/report_outage/', {client_id: c.id}); }
      setResult({box: targetBox, affectedCount: affectedClients.length});
    }
    const updated = await fetchAPI('/boxes/');
    setBoxes(updated?.results || updated || []);
    setLoading(false);
  };

  const resetAll = async () => {
    setLoading(true);
    const allClients = await fetchAPI('/clients/');
    for (const c of (allClients?.results || allClients || [])) {
      if (c.status === 'affected') { await fetch(`${API_URL}/clients/${c.id}/`, {method: 'PATCH', headers: apiHeaders(), body: JSON.stringify({status: 'active'})}); }
    }
    setResult(null);
    const updated = await fetchAPI('/boxes/');
    setBoxes(updated?.results || updated || []);
    setLoading(false);
  };

  const affectedBoxes = boxes.filter(b => b.affected_count > 0);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <h2 className="text-xl font-bold text-gray-800 mb-2">⚡ Simulador de Averias</h2>
        <p className="text-gray-500 mb-6">Inyecta averias aleatorias para probar el algoritmo.</p>
        <div className="flex gap-4 mb-6">
          <button onClick={simulateRandom} disabled={loading} className="flex-1 px-6 py-4 bg-red-500 text-white rounded-lg font-bold text-lg hover:bg-red-600 disabled:opacity-50">{loading ? '⏳...' : '⚡ Simular averia'}</button>
          <button onClick={resetAll} disabled={loading} className="px-6 py-4 bg-green-500 text-white rounded-lg font-bold hover:bg-green-600 disabled:opacity-50">✅ Restaurar</button>
        </div>
        {result && <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg"><h3 className="font-bold text-orange-800 mb-2">🎯 Simulacion ejecutada</h3><p className="text-sm text-orange-700">{result.affectedCount} clientes de <strong>{result.box.code}</strong> marcados como afectados.</p></div>}
        <div className="border-t border-gray-100 pt-6">
          <h3 className="font-bold text-gray-700 mb-4">📊 Estado actual</h3>
          {affectedBoxes.length === 0 ? <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center"><p className="text-green-700 font-semibold">✅ Todo operativo</p></div> : <div className="space-y-3">{affectedBoxes.map(b => <div key={b.id} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg"><div><span className="font-mono font-bold text-red-800">{b.code}</span><span className="text-sm text-gray-600 ml-2">{b.name}</span></div><span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">⚠️ {b.affected_count}</span></div>)}</div>}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!getToken());
  const [activeTab, setActiveTab] = useState('dashboard');

  if (!isLoggedIn) return <LoginScreen onLogin={() => setIsLoggedIn(true)} />;

  return (
    <div className="min-h-screen bg-gray-100">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      <main>{activeTab === 'dashboard' && <Dashboard />}{activeTab === 'map' && <FiberMap />}{activeTab === 'diagnose' && <Diagnose />}{activeTab === 'simulate' && <Simulate />}</main>
      <footer className="bg-gray-800 text-gray-400 text-center py-4 text-sm mt-8"><p>FiberTruck v1.0 - TFM Master Full Stack</p><p>Despliegue FTTH ficticio de Cieza, Murcia</p></footer>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
