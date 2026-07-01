var API_URL = '';
var ZC = {'Z-ERA': '#dc2626', 'Z-SJOR': '#2563eb', 'Z-SJOA': '#16a34a', 'Z-SJBO': '#f59e0b', 'Z-HORT': '#8b5cf6'};
var CC = {feeder: '#dc2626', distribution: '#2563eb', drop: '#16a34a'};

function gt() { return localStorage.getItem('token'); }
function ah() { return {'Authorization': 'Bearer ' + gt(), 'Content-Type': 'application/json'}; }

function fa(path) {
  return fetch(API_URL + path, {headers: ah()}).then(function(r) {
    return r.ok ? r.json() : null;
  }).catch(function() { return null; });
}
function pa(path, body) {
  return fetch(API_URL + path, {method: 'POST', headers: ah(), body: JSON.stringify(body)}).then(function(r) {
    return r.ok ? r.json() : null;
  }).catch(function() { return null; });
}
function lo() { localStorage.removeItem('token'); window.location.reload(); }

function ce(type, props, children) {
  var args = [type, props || {}];
  if (children) {
    for (var i = 0; i < children.length; i++) args.push(children[i]);
  }
  return React.createElement.apply(React, args);
}

function LoginScreen(props) {
  var onLogin = props.onLogin;
  var u = React.useState('');
  var setU = u[1]; u = u[0];
  var pw = React.useState('');
  var setPw = pw[1]; pw = pw[0];
  var er = React.useState('');
  var setEr = er[1]; er = er[0];

  function handleLogin(e) {
    e.preventDefault();
    fetch(API_URL + '/api/auth/login/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username: u, password: pw})
    }).then(function(r) { return r.json().then(function(d) {
      if (r.ok && d.access) { localStorage.setItem('token', d.access); onLogin(); }
      else { setEr('Credenciales incorrectas'); }
    }); }).catch(function() { setEr('Error de conexion'); });
  }

  return ce('div', {className: 'min-h-screen bg-gradient-to-br from-blue-800 to-blue-900 flex items-center justify-center px-4'}, [
    ce('div', {className: 'bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md'}, [
      ce('div', {className: 'text-center mb-6'}, [
        ce('h1', {className: 'text-2xl font-bold text-gray-800 mt-2'}, ['FiberTruck']),
        ce('p', {className: 'text-gray-500 text-sm'}, ['Diagnostico FTTH - Cieza, Murcia']),
        ce('p', {className: 'text-xs text-blue-500 mt-1'}, ['v2.0 Ingenieria'])
      ]),
      ce('form', {onSubmit: handleLogin, className: 'space-y-4'}, [
        ce('input', {type: 'text', value: u, onChange: function(e) { setU(e.target.value); }, placeholder: 'Usuario', className: 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        ce('input', {type: 'password', value: pw, onChange: function(e) { setPw(e.target.value); }, placeholder: 'Contrasena', className: 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        er ? ce('p', {className: 'text-red-600 text-sm bg-red-50 p-2 rounded'}, ['⚠ ' + er]) : null,
        ce('button', {type: 'submit', className: 'w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700'}, ['Entrar'])
      ]),
      ce('div', {className: 'mt-4 p-3 bg-gray-50 rounded-lg'}, [
        ce('p', {className: 'text-xs text-gray-500 mb-2 font-semibold'}, ['Usuarios de prueba:']),
        ce('div', {className: 'grid grid-cols-3 gap-2'}, [
          ce('button', {onClick: function() { setU('admin'); setPw('admin123'); }, className: 'text-xs bg-white border rounded px-2 py-1 hover:border-blue-400'}, ['admin']),
          ce('button', {onClick: function() { setU('tecnico1'); setPw('tecno123'); }, className: 'text-xs bg-white border rounded px-2 py-1 hover:border-blue-400'}, ['tecnico1']),
          ce('button', {onClick: function() { setU('supervisor1'); setPw('super123'); }, className: 'text-xs bg-white border rounded px-2 py-1 hover:border-blue-400'}, ['supervisor1'])
        ])
      ])
    ])
  ]);
}

function Header(props) {
  var activeTab = props.activeTab;
  var setActiveTab = props.setActiveTab;
  var tabs = [
    {id: 'dashboard', l: 'Dashboard', i: '📊'},
    {id: 'map', l: 'Mapa', i: '🗺️'},
    {id: 'topology', l: 'Red', i: '🌐'},
    {id: 'diagnose', l: 'Diagnostico', i: '🔍'},
    {id: 'simulate', l: 'Simular', i: '⚡'}
  ];
  return ce('header', {className: 'bg-blue-800 text-white shadow-lg'}, [
    ce('div', {className: 'max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-2'}, [
      ce('div', {className: 'flex items-center gap-2'}, [
        ce('h1', {className: 'text-xl font-bold'}, ['FiberTruck']),
        ce('p', {className: 'text-xs text-blue-200'}, ['v2.0 - Cieza, Murcia'])
      ]),
      ce('nav', {className: 'flex gap-1 flex-wrap'}, tabs.map(function(t) {
        return ce('button', {
          key: t.id,
          onClick: function() { setActiveTab(t.id); },
          className: 'px-3 py-2 rounded-lg text-sm font-medium transition ' + (activeTab === t.id ? 'bg-blue-600 text-white' : 'text-blue-200 hover:bg-blue-700')
        }, [t.i + ' ' + t.l]);
      })),
      ce('button', {onClick: lo, className: 'text-xs text-blue-300 hover:text-white'}, ['Salir'])
    ])
  ]);
}

function Dashboard() {
  var st = React.useState(null);
  var stats = st[0], setStats = st[1];
  var zo = React.useState([]);
  var zones = zo[0], setZones = zo[1];
  var cb = React.useState([]);
  var cables = cb[0], setCables = cb[1];
  var ld = React.useState(true);
  var loading = ld[0], setLoading = ld[1];

  React.useEffect(function() {
    Promise.all([fa('/api/incidents/stats/'), fa('/api/zones/'), fa('/api/cables/')]).then(function(results) {
      setStats(results[0]);
      setZones(results[1] || []);
      setCables(results[2] || []);
      setLoading(false);
    });
  }, []);

  if (loading) return ce('div', {className: 'p-8 text-center text-gray-500'}, ['Cargando datos de red...']);

  function fb(type) { return (cables || []).filter(function(x) { return x.cable_type === type; }); }
  function sf(list) { return list.reduce(function(s, x) { return s + (x.fiber_count || 0); }, 0); }
  function su(list) { return list.reduce(function(s, x) { return s + (x.fibers_used || 0); }, 0); }

  return ce('div', {className: 'max-w-7xl mx-auto px-4 py-6 space-y-6'}, [
    ce('div', {className: 'text-center bg-white rounded-xl p-4 shadow-sm'}, [
      ce('h1', {className: 'text-2xl font-bold tracking-wide text-blue-800'}, ['FIBERTRUCK DASHBOARD']),
      ce('p', {className: 'text-xs text-gray-500 mt-1'}, ['Red FTTH - Cieza (Murcia)'])
    ]),
    ce('div', {className: 'grid grid-cols-2 md:grid-cols-4 gap-4'}, [
      {t: 'OLT', v: '+3.0 dBm', c: 'text-blue-700'},
      {t: 'Zonas', v: String(zones.length), c: 'text-purple-700'},
      {t: 'Cajas CTO', v: String((stats && stats.active_boxes) || 29), c: 'text-blue-700'},
      {t: 'Clientes', v: String((stats && stats.total_clients) || 161), c: 'text-green-700'}
    ].map(function(s, i) {
      return ce('div', {key: i, className: 'bg-white rounded-xl shadow-sm p-4 text-center border'}, [
        ce('p', {className: 'text-2xl font-bold ' + s.c}, [s.v]),
        ce('p', {className: 'text-xs text-gray-500'}, [s.t])
      ]);
    })),
    ce('div', {className: 'bg-white rounded-xl shadow-sm border overflow-hidden'}, [
      ce('div', {className: 'px-4 py-3 border-b font-bold bg-gray-50'}, ['CABLES DE RED']),
      ce('table', {className: 'w-full text-sm'}, [
        ce('thead', null, [ce('tr', {className: 'bg-gray-50 text-gray-600'}, [
          ce('th', {className: 'px-4 py-2 text-left'}, ['Tipo']),
          ce('th', {className: 'px-4 py-2 text-left'}, ['Capacidad']),
          ce('th', {className: 'px-4 py-2 text-left'}, ['Usadas']),
          ce('th', {className: 'px-4 py-2 text-left'}, ['Uso'])
        ])]),
        ce('tbody', {className: 'divide-y divide-gray-50'}, [
          ['feeder', 'Feeder', 'bg-red-500'],
          ['distribution', 'Distribution', 'bg-blue-500'],
          ['drop', 'Drop', 'bg-green-500']
        ].map(function(item) {
          var t = item[0], n = item[1], bg = item[2];
          var list = fb(t);
          var tot = sf(list);
          var usd = su(list);
          var pct = tot > 0 ? ((usd / tot) * 100).toFixed(1) : '0.0';
          return ce('tr', {key: t, className: 'hover:bg-gray-50'}, [
            ce('td', {className: 'px-4 py-2 font-semibold'}, [n]),
            ce('td', {className: 'px-4 py-2 font-mono'}, [tot + 'f (' + list.length + ')']),
            ce('td', {className: 'px-4 py-2'}, [usd + '/' + tot]),
            ce('td', {className: 'px-4 py-2'}, [
              ce('div', {className: 'flex items-center gap-2'}, [
                ce('div', {className: 'bg-gray-200 h-4 rounded flex-1'}, [
                  ce('div', {className: bg + ' h-4 rounded transition-all', style: {width: pct + '%'}})
                ]),
                ce('span', {className: 'text-xs w-10'}, [pct + '%'])
              ])
            ])
          ]);
        }))
      ])
    ]),
    ce('div', {className: 'bg-white rounded-xl shadow-sm border overflow-hidden'}, [
      ce('div', {className: 'px-4 py-3 border-b font-bold bg-gray-50'}, ['ESTADO POR ZONAS']),
      ce('table', {className: 'w-full text-sm'}, [
        ce('thead', null, [ce('tr', {className: 'bg-gray-50 text-gray-600'}, [
          ce('th', {className: 'px-4 py-2 text-left'}, ['Zona']),
          ce('th', {className: 'px-4 py-2 text-center'}, ['Clientes']),
          ce('th', {className: 'px-4 py-2 text-center'}, ['Afectados'])
        ])]),
        ce('tbody', {className: 'divide-y divide-gray-50'}, (zones || []).map(function(z) {
          return ce('tr', {key: z.id, className: 'hover:bg-gray-50'}, [
            ce('td', {className: 'px-4 py-2 flex items-center gap-2'}, [
              ce('div', {className: 'w-3 h-3 rounded-full', style: {background: ZC[z.code] || '#666'}}),
              ce('span', null, [z.name])
            ]),
            ce('td', {className: 'px-4 py-2 text-center'}, [String(z.client_count || 0)]),
            ce('td', {className: 'px-4 py-2 text-center'}, [
              (z.affected_client_count || 0) > 0 ?
                ce('span', {className: 'bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-bold'}, [String(z.affected_client_count)]) :
                ce('span', {className: 'text-green-600'}, ['0'])
            ])
          ]);
        }))
      ])
    ])
  ]);
}

function NetworkMap() {
  var s1 = React.useState([]); var segs = s1[0], setSegs = s1[1];
  var s2 = React.useState([]); var boxes = s2[0], setBoxes = s2[1];
  var s3 = React.useState([]); var splices = s3[0], setSplices = s3[1];
  var s4 = React.useState([]); var splitters = s4[0], setSplitters = s4[1];
  var s5 = React.useState([]); var olts = s5[0], setOlts = s5[1];
  var s6 = React.useState({feeder: true, distribution: true, drop: true, boxes: true, splices: true, splitters: true, olt: true});
  var ly = s6[0], setLy = s6[1];
  var mapR = React.useRef(null);
  var lm = React.useRef(null);
  var lr = React.useRef({});

  React.useEffect(function() {
    Promise.all([fa('/api/segments/'), fa('/api/boxes/'), fa('/api/splices/'), fa('/api/splitters/'), fa('/api/olts/')]).then(function(r) {
      setSegs(r[0] || []); setBoxes(r[1] || []); setSplices(r[2] || []); setSplitters(r[3] || []); setOlts(r[4] || []);
    });
  }, []);

  React.useEffect(function() {
    if (!lm.current && mapR.current) {
      lm.current = L.map(mapR.current).setView([38.2395, -1.4165], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '&copy; OSM', maxZoom: 19}).addTo(lm.current);
    }
    return function() {
      if (lm.current) { lm.current.remove(); lm.current = null; }
    };
  }, []);

  React.useEffect(function() {
    if (!lm.current) return;
    Object.values(lr.current).forEach(function(l) {
      if (l && lm.current.hasLayer(l)) lm.current.removeLayer(l);
    });
    lr.current = {};
    var gr = {
      feeder: L.layerGroup(), distribution: L.layerGroup(), drop: L.layerGroup(),
      boxes: L.layerGroup(), splices: L.layerGroup(), splitters: L.layerGroup(), olt: L.layerGroup()
    };
    if (ly.olt && olts[0]) {
      var o = olts[0];
      L.marker([o.latitude, o.longitude], {icon: L.divIcon({className: '', html: '<div style="width:14px;height:14px;background:#dc2626;border:2px solid white;border-radius:50%"></div>', iconSize: [14, 14]})})
        .addTo(gr.olt).bindPopup('<b>' + o.code + '</b><br/>' + o.output_power_dbm + ' dBm');
    }
    (segs || []).forEach(function(sg) {
      var st = sg.segment_type || 'drop';
      if (!ly[st]) return;
      var rt = sg.route_as_list || [];
      if (rt.length < 2) return;
      var col = CC[st] || '#666';
      var w = st === 'feeder' ? 4 : st === 'distribution' ? 3 : 2;
      var ds = st === 'feeder' ? '10,5' : st === 'drop' ? '5,5' : null;
      L.polyline(rt, {color: col, weight: w, dashArray: ds, opacity: 0.8})
        .addTo(gr[st]).bindPopup('<b>' + sg.cable_code + '</b><br/>' + st + '<br/>' + sg.length_m + 'm');
    });
    if (ly.splices) {
      (splices || []).forEach(function(sp) {
        if (sp.latitude && sp.longitude)
          L.circleMarker([sp.latitude, sp.longitude], {radius: 6, fillColor: '#111', color: '#fbbf24', weight: 2, fillOpacity: 0.9})
            .addTo(gr.splices).bindPopup('<b>' + sp.code + '</b><br/>' + (sp.zone_name || '') + '<br/>' + (sp.fibers_free || 0) + ' libres');
      });
    }
    if (ly.splitters) {
      (splitters || []).forEach(function(s) {
        if (s.latitude && s.longitude)
          L.circleMarker([s.latitude, s.longitude], {radius: 8, fillColor: '#f97316', color: '#fff', weight: 2, fillOpacity: 0.9})
            .addTo(gr.splitters).bindPopup('<b>' + s.code + '</b><br/>1:' + s.ratio);
      });
    }
    if (ly.boxes) {
      (boxes || []).forEach(function(b) {
        if (!b.latitude || !b.longitude) return;
        var col = ZC[b.zone_code] || '#0ea5e9';
        var aff = (b.affected_count || 0) > 0;
        L.circleMarker([b.latitude, b.longitude], {radius: aff ? 10 : 6, fillColor: col, color: aff ? '#dc2626' : '#fff', weight: aff ? 3 : 1.5, fillOpacity: aff ? 0.95 : 0.7})
          .addTo(gr.boxes).bindPopup('<b>' + b.code + '</b><br/>' + (b.name || '') + '<br/>' + (b.client_count || 0) + ' clientes');
      });
    }
    Object.keys(gr).forEach(function(k) {
      if (ly[k] !== false) { gr[k].addTo(lm.current); lr.current[k] = gr[k]; }
    });
  }, [segs, boxes, splices, splitters, olts, ly]);

  function toggleLayer(k) {
    setLy(function(p) { var n = {}; Object.keys(p).forEach(function(key) { n[key] = p[key]; }); n[k] = !p[k]; return n; });
  }

  var layerBtns = [
    ['feeder', 'Feeder', 'bg-red-100 text-red-700 border-red-300'],
    ['distribution', 'Distribution', 'bg-blue-100 text-blue-700 border-blue-300'],
    ['drop', 'Drop', 'bg-green-100 text-green-700 border-green-300'],
    ['boxes', 'Cajas', 'bg-gray-100 text-gray-700 border-gray-300'],
    ['splices', 'Empalmes', 'bg-yellow-100 text-yellow-700 border-yellow-300'],
    ['splitters', 'Splitters', 'bg-orange-100 text-orange-700 border-orange-300'],
    ['olt', 'OLT', 'bg-red-100 text-red-800 border-red-400']
  ];

  return ce('div', {className: 'max-w-7xl mx-auto px-4 py-4'}, [
    ce('div', {className: 'flex flex-wrap gap-2 mb-3'}, (layerBtns || []).map(function(item) {
      var k = item[0], l = item[1], c = item[2];
      return ce('button', {
        key: k,
        onClick: function() { toggleLayer(k); },
        className: 'px-3 py-1 rounded-lg text-xs font-medium border ' + (ly[k] ? c : 'bg-gray-50 text-gray-400')
      }, [(ly[k] ? '✓ ' : '✗ ') + l]);
    })),
    ce('div', {ref: mapR, style: {height: '75vh'}, className: 'bg-white rounded-xl shadow-sm border'})
  ]);
}

function DiagnoseV2() {
  var s1 = React.useState(1); var step = s1[0], setStep = s1[1];
  var s2 = React.useState(''); var bc = s2[0], setBc = s2[1];
  var s3 = React.useState(null); var box = s3[0], setBox = s3[1];
  var s4 = React.useState([]); var cl = s4[0], setCl = s4[1];
  var s5 = React.useState([]); var sc = s5[0], setSc = s5[1];
  var s6 = React.useState(null); var res = s6[0], setRes = s6[1];
  var s7 = React.useState(false); var ld = s7[0], setLd = s7[1];
  var s8 = React.useState(''); var er = s8[0], setEr = s8[1];

  function searchBox() {
    setLd(true); setEr('');
    fa('/api/boxes/').then(function(b) {
      if (b) {
        var f = b.find(function(x) { return x.code.toUpperCase() === bc.toUpperCase(); });
        if (f) {
          setBox(f);
          fa('/api/boxes/' + f.id + '/clients/').then(function(c) { setCl(c || []); setStep(2); setLd(false); });
        } else { setEr('Caja no encontrada'); setLd(false); }
      } else { setLd(false); }
    });
  }

  function runDiagnosis() {
    if (!sc.length) { setEr('Selecciona al menos un cliente'); return; }
    setLd(true); setEr('');
    var promises = sc.map(function(cid) { return pa('/api/clients/report_outage/', {client_id: cid}); });
    Promise.all(promises).then(function() {
      return pa('/api/diagnose/v2/', {box_code: bc.toUpperCase(), affected_client_ids: sc});
    }).then(function(d) {
      if (d) { setRes(d); setStep(3); }
      else { setEr('Error en diagnostico'); }
      setLd(false);
    });
  }

  function toggleClient(id) {
    setSc(function(p) { return p.includes(id) ? p.filter(function(x) { return x !== id; }) : p.concat([id]); });
  }

  function reset() { setStep(1); setBc(''); setBox(null); setCl([]); setSc([]); setRes(null); setEr(''); }

  var scn = '';
  var scl = '';
  if (res) {
    scn = res.severity === 'critical' ? 'CRITICO' : res.severity === 'high' ? 'ALTO' : res.severity === 'medium' ? 'MEDIO' : 'BAJO';
    scl = res.severity === 'critical' ? 'border-l-4 border-red-500 bg-red-50' : res.severity === 'high' ? 'border-l-4 border-orange-500 bg-orange-50' : res.severity === 'medium' ? 'border-l-4 border-blue-500 bg-blue-50' : 'border-l-4 border-green-500 bg-green-50';
  }

  var stepContent;
  if (step === 1) {
    stepContent = ce('div', {className: 'bg-white rounded-xl shadow-sm border p-6'}, [
      ce('h2', {className: 'text-lg font-bold mb-2'}, ['Codigo de caja']),
      ce('div', {className: 'flex gap-2'}, [
        ce('input', {type: 'text', value: bc, onChange: function(e) { setBc(e.target.value.toUpperCase()); }, placeholder: 'CTO-023', className: 'flex-1 px-4 py-2 border rounded-lg font-mono'}),
        ce('button', {onClick: searchBox, disabled: ld || !bc, className: 'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50'}, [ld ? '...' : 'Buscar'])
      ]),
      er ? ce('p', {className: 'text-red-600 text-sm mt-2'}, [er]) : null,
      ce('div', {className: 'mt-4 flex flex-wrap gap-2'}, ['CTO-001', 'CTO-010', 'CTO-020', 'CTO-023'].map(function(c) {
        return ce('button', {key: c, onClick: function() { setBc(c); }, className: 'text-xs bg-gray-100 border rounded px-2 py-1 hover:bg-blue-100'}, [c]);
      }))
    ]);
  } else if (step === 2 && box) {
    stepContent = ce('div', {className: 'bg-white rounded-xl shadow-sm border p-6'}, [
      ce('h2', {className: 'font-bold mb-1'}, [box.code + ' - ' + box.name]),
      ce('p', {className: 'text-xs text-gray-500 mb-4'}, [box.full_path || '']),
      ce('div', {className: 'space-y-2 max-h-80 overflow-y-auto mb-4 border rounded-lg p-2'}, (cl || []).map(function(c) {
        var selected = sc.includes(c.id);
        return ce('div', {
          key: c.id,
          onClick: function() { toggleClient(c.id); },
          className: 'flex items-center p-2 rounded border-2 cursor-pointer ' + (selected ? 'border-red-400 bg-red-50' : 'border-gray-200')
        }, [
          ce('div', {className: 'w-5 h-5 rounded border-2 mr-2 flex items-center justify-center ' + (selected ? 'bg-red-500 border-red-500' : 'border-gray-300')}, [selected ? '✓' : '']),
          ce('div', {className: 'flex-1'}, [
            ce('p', {className: 'text-sm font-semibold'}, [c.full_name]),
            ce('p', {className: 'text-xs text-gray-500'}, [c.client_code])
          ]),
          c.optical_power_rx ? ce('span', {className: 'text-xs font-mono bg-gray-100 px-2 py-0.5 rounded'}, [c.optical_power_rx + ' dBm']) : null
        ]);
      })),
      ce('div', {className: 'flex gap-2'}, [
        ce('button', {onClick: function() { setStep(1); }, className: 'px-4 py-2 border rounded-lg hover:bg-gray-50'}, ['Atras']),
        ce('button', {onClick: runDiagnosis, disabled: ld, className: 'flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50'}, [ld ? 'Analizando...' : 'Diagnosticar ' + sc.length + ' afectado(s)'])
      ]),
      er ? ce('p', {className: 'text-red-600 text-sm mt-2'}, [er]) : null
    ]);
  } else if (step === 3 && res) {
    var sevBadge = res.severity === 'critical' ? 'bg-red-600' : res.severity === 'high' ? 'bg-orange-500' : res.severity === 'medium' ? 'bg-blue-500' : 'bg-green-500';
    stepContent = ce('div', {className: 'space-y-4'}, [
      ce('div', {className: 'rounded-xl shadow-sm p-6 ' + scl}, [
        ce('div', {className: 'flex justify-between items-center'}, [
          ce('div', null, [
            ce('h2', {className: 'text-xl font-bold'}, ['DIAGNOSTICO: ' + scn]),
            ce('p', {className: 'text-sm'}, ['Confianza: ' + (res.confidence || 0) + '%'])
          ]),
          ce('span', {className: 'px-3 py-1 rounded-full text-sm font-bold text-white ' + sevBadge}, [res.severity.toUpperCase()])
        ])
      ]),
      res.fault_location ? ce('div', {className: 'bg-white rounded-xl shadow-sm border p-4'}, [
        ce('h3', {className: 'font-bold mb-2'}, ['FALLO DETECTADO']),
        ce('div', {className: 'bg-gray-50 rounded p-3'}, [
          ce('p', {className: 'font-semibold text-sm'}, [res.fault_location.description || 'No disponible']),
          res.fault_location.address ? ce('p', {className: 'text-xs text-gray-500 mt-1'}, ['📍 ' + res.fault_location.address]) : null
        ])
      ]) : null,
      res.power_analysis ? ce('div', {className: 'bg-white rounded-xl shadow-sm border p-4'}, [
        ce('h3', {className: 'font-bold mb-2'}, ['ANALISIS DE POTENCIA']),
        ce('div', {className: 'grid grid-cols-3 gap-3'}, [
          {t: 'Esperada', v: res.power_analysis.expected_dbm + ' dBm', bg: 'bg-green-50 border-green-200', tc: 'text-green-800'},
          {t: 'Medida', v: res.power_analysis.measured_dbm + ' dBm', bg: 'bg-red-50 border-red-200', tc: 'text-red-800'},
          {t: 'Perdida', v: res.power_analysis.loss_db + ' dB', bg: 'bg-orange-50 border-orange-200', tc: 'text-orange-800'}
        ].map(function(p, i) {
          return ce('div', {key: i, className: 'p-3 rounded-lg text-center border ' + p.bg}, [
            ce('p', {className: 'text-xs text-gray-500'}, [p.t]),
            ce('p', {className: 'text-lg font-bold ' + p.tc}, [p.v])
          ]);
        }))
      ]) : null,
      res.recommended_action ? ce('div', {className: 'bg-white rounded-xl shadow-sm border p-4'}, [
        ce('h3', {className: 'font-bold mb-2'}, ['ACCION RECOMENDADA']),
        ce('div', {className: 'bg-blue-50 rounded-lg border border-blue-100 p-3 space-y-2'}, [
          ce('p', {className: 'text-sm text-blue-900 whitespace-pre-line'}, [res.recommended_action])
        ])
      ]) : null,
      res.affected_clients && res.affected_clients.length > 0 ? ce('div', {className: 'bg-white rounded-xl shadow-sm border p-4'}, [
        ce('h3', {className: 'font-bold mb-2'}, ['CLIENTES AFECTADOS (' + res.affected_clients.length + ')']),
        ce('div', {className: 'space-y-1'}, (res.affected_clients || []).map(function(c, i) {
          return ce('div', {key: i, className: 'flex justify-between p-2 bg-red-50 rounded text-sm'}, [
            ce('span', null, [(c.client_code || c.code) + ' - ' + (c.full_name || c.name)]),
            ce('span', {className: 'font-mono text-red-600'}, [(c.power_dbm || c.optical_power_rx || '-') + ' dBm'])
          ]);
        }))
      ]) : null,
      ce('button', {onClick: reset, className: 'w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700'}, ['Nuevo diagnostico'])
    ]);
  }

  return ce('div', {className: 'max-w-4xl mx-auto px-4 py-6'}, [
    ce('div', {className: 'flex items-center mb-6 gap-2'}, [
      ce('div', {className: 'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ' + (step > 1 ? 'bg-green-500 text-white' : step === 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500')}, [step > 1 ? '✓' : '1']),
      ce('span', {className: 'text-xs hidden md:inline'}, ['Caja']),
      ce('div', {className: 'flex-1 h-1 ' + (step > 1 ? 'bg-green-500' : 'bg-gray-200')}),
      ce('div', {className: 'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ' + (step > 2 ? 'bg-green-500 text-white' : step === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500')}, [step > 2 ? '✓' : '2']),
      ce('span', {className: 'text-xs hidden md:inline'}, ['Afectados']),
      ce('div', {className: 'flex-1 h-1 ' + (step > 2 ? 'bg-green-500' : 'bg-gray-200')}),
      ce('div', {className: 'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ' + (step === 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500')}, ['3']),
      ce('span', {className: 'text-xs hidden md:inline'}, ['Resultado'])
    ]),
    stepContent
  ]);
}

function Topology() {
  var s1 = React.useState(null);
  var topo = s1[0], setTopo = s1[1];

  React.useEffect(function() {
    fa('/api/topology/').then(function(t) { setTopo(t); });
  }, []);

  if (!topo) return ce('div', {className: 'p-8 text-center text-gray-500'}, ['Cargando topologia...']);
  var zc = topo.zones || [];
  var totalBoxes = zc.reduce(function(s, z) { return s + (z.boxes && z.boxes.length || 0); }, 0);
  var totalClients = zc.reduce(function(s, z) { return s + (z.zone && z.zone.client_count || 0); }, 0);
  var totalCables = zc.reduce(function(s, z) { return s + (z.cables && z.cables.length || 0); }, 0);

  return ce('div', {className: 'max-w-7xl mx-auto px-4 py-6 space-y-6'}, [
    ce('div', {className: 'grid grid-cols-5 gap-3'}, [
      {l: 'OLT', v: '1', c: 'text-red-600'},
      {l: 'Zonas', v: String(zc.length), c: 'text-purple-600'},
      {l: 'Cajas', v: String(totalBoxes), c: 'text-blue-600'},
      {l: 'Clientes', v: String(totalClients), c: 'text-green-600'},
      {l: 'Cables', v: String(totalCables), c: 'text-orange-600'}
    ].map(function(s, i) {
      return ce('div', {key: i, className: 'bg-white rounded-xl shadow-sm p-3 text-center border'}, [
        ce('p', {className: 'text-2xl font-bold ' + s.c}, [s.v]),
        ce('p', {className: 'text-xs text-gray-500'}, [s.l])
      ]);
    })),
    ce('div', {className: 'bg-white rounded-xl shadow-sm border p-4'}, [
      ce('h2', {className: 'font-bold mb-3'}, ['Topologia: ' + (topo.olt && topo.olt.code || 'OLT') + ' (' + (topo.olt && topo.olt.output_power_dbm || '') + ' dBm)']),
      ce('div', {className: 'space-y-2'}, (zc || []).map(function(z) {
        var zone = z.zone || {};
        return ce('div', {key: zone.id, className: 'border rounded-lg p-3'}, [
          ce('div', {className: 'flex items-center gap-2 mb-2'}, [
            ce('div', {className: 'w-3 h-3 rounded-full', style: {background: ZC[zone.code] || '#666'}}),
            ce('span', {className: 'font-bold'}, [zone.name]),
            ce('span', {className: 'text-xs text-gray-400'}, [zone.code]),
            ce('span', {className: 'text-xs bg-blue-100 text-blue-700 px-2 rounded-full ml-auto'}, [(zone.client_count || 0) + ' clientes'])
          ]),
          z.splice ? ce('p', {className: 'text-sm ml-2'}, [
            ce('span', {className: 'text-yellow-600 font-semibold'}, ['● ' + z.splice.code]),
            ce('span', {className: 'text-xs text-gray-400 ml-2'}, [z.splice.address || ''])
          ]) : null,
          (z.splitters || []).map(function(s) {
            return ce('div', {key: s.id, className: 'ml-4'}, [
              ce('p', {className: 'text-sm'}, [
                ce('span', {className: 'text-orange-600 font-semibold'}, ['★ ' + s.code]),
                ' 1:' + s.ratio,
                ce('span', {className: 'text-xs text-gray-400 ml-2'}, [s.output_power_dbm + ' dBm'])
              ])
            ]);
          })
        ]);
      }))
    ])
  ]);
}

function Simulate() {
  var s1 = React.useState([]);
  var boxes = s1[0], setBoxes = s1[1];
  var s2 = React.useState(false);
  var loading = s2[0], setLoading = s2[1];

  React.useEffect(function() {
    fa('/api/boxes/').then(function(b) { setBoxes(b || []); });
  }, []);

  function sim() {
    setLoading(true);
    fa('/api/boxes/').then(function(b) {
      var ab = (b || []).filter(function(x) { return x.client_count > 0; });
      var t = ab[Math.floor(Math.random() * ab.length)];
      if (t) {
        fa('/api/boxes/' + t.id + '/clients/').then(function(c) {
          var n = Math.min(Math.floor(Math.random() * 3) + 1, (c || []).length);
          var ac = (c || []).sort(function() { return 0.5 - Math.random(); }).slice(0, n);
          var promises = ac.map(function(cl) { return pa('/api/clients/report_outage/', {client_id: cl.id}); });
          Promise.all(promises).then(function() {
            fa('/api/boxes/').then(function(u) { setBoxes(u || []); setLoading(false); });
          });
        });
      } else { setLoading(false); }
    });
  }

  function rst() {
    setLoading(true);
    fa('/api/clients/').then(function(a) {
      var affected = (a || []).filter(function(x) { return x.status === 'affected'; });
      var promises = affected.map(function(c) {
        return fetch(API_URL + '/api/clients/' + c.id + '/', {method: 'PATCH', headers: ah(), body: JSON.stringify({status: 'active'})});
      });
      Promise.all(promises).then(function() {
        fa('/api/boxes/').then(function(u) { setBoxes(u || []); setLoading(false); });
      });
    });
  }

  var aff = (boxes || []).filter(function(b) { return (b.affected_count || 0) > 0; });
  var ta = aff.reduce(function(s, b) { return s + (b.affected_count || 0); }, 0);

  return ce('div', {className: 'max-w-4xl mx-auto px-4 py-6'}, [
    ce('div', {className: 'bg-white rounded-xl shadow-sm border p-6'}, [
      ce('h2', {className: 'text-xl font-bold mb-2'}, ['Simulador de Averias']),
      ce('div', {className: 'flex gap-3 mb-4'}, [
        ce('button', {onClick: sim, disabled: loading, className: 'flex-1 py-3 bg-red-500 text-white rounded-lg font-bold disabled:opacity-50'}, [loading ? '...' : 'Simular averia']),
        ce('button', {onClick: rst, disabled: loading, className: 'px-4 py-3 bg-green-500 text-white rounded-lg font-bold disabled:opacity-50'}, ['Restaurar'])
      ]),
      aff.length === 0 ?
        ce('div', {className: 'p-4 bg-green-50 border border-green-200 rounded-lg text-center'}, [
          ce('p', {className: 'text-green-700 font-bold text-lg'}, ['Todo operativo'])
        ]) :
        ce('div', {className: 'space-y-2'}, [
          ce('p', {className: 'text-sm font-semibold text-red-600'}, [ta + ' cliente(s) afectado(s) en ' + aff.length + ' caja(s):']),
          (aff || []).map(function(b) {
            return ce('div', {key: b.id, className: 'flex justify-between p-2 bg-red-50 border border-red-200 rounded'}, [
              ce('span', {className: 'font-mono font-bold text-red-800'}, [b.code]),
              ce('span', {className: 'bg-red-500 text-white px-2 py-0.5 rounded-full text-sm font-bold'}, [String(b.affected_count)])
            ]);
          })
        ])
    ])
  ]);
}

function App() {
  var s1 = React.useState(!!gt());
  var li = s1[0], setLi = s1[1];
  var s2 = React.useState('dashboard');
  var at = s2[0], setAt = s2[1];

  if (!li) return ce(LoginScreen, {onLogin: function() { setLi(true); }});

  function rt() {
    switch(at) {
      case 'dashboard': return ce(Dashboard);
      case 'map': return ce(NetworkMap);
      case 'topology': return ce(Topology);
      case 'diagnose': return ce(DiagnoseV2);
      case 'simulate': return ce(Simulate);
      default: return ce(Dashboard);
    }
  }

  return ce('div', {className: 'min-h-screen bg-gray-100'}, [
    ce(Header, {activeTab: at, setActiveTab: setAt}),
    ce('main', null, [rt()]),
    ce('footer', {className: 'bg-gray-800 text-gray-400 text-center py-3 text-xs mt-8'}, ['FiberTruck v2.0 - TFM Master Full Stack | Cieza, Murcia'])
  ]);
}

// React 18 createRoot API
var rootEl = document.getElementById('root');
if (rootEl && typeof ReactDOM !== 'undefined' && ReactDOM.createRoot) {
  var root = ReactDOM.createRoot(rootEl);
  root.render(React.createElement(App));
} else if (rootEl && typeof ReactDOM !== 'undefined' && ReactDOM.render) {
  ReactDOM.render(React.createElement(App), rootEl);
} else {
  rootEl.innerHTML = '<div style="padding:40px;text-align:center;font-family:sans-serif;"><h2 style="color:#dc2626">Error de carga</h2><p>No se pudieron cargar las librerias React. Verifica tu conexion a internet.</p><p style="color:#666;font-size:12px;margin-top:20px">React: ' + (typeof React) + ' | ReactDOM: ' + (typeof ReactDOM) + '</p></div>';
}