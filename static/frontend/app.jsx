const {useState,useEffect}=React;
const API_URL='';
const ZC={'Z-ERA':'#dc2626','Z-SJOR':'#2563eb','Z-SJOA':'#16a34a','Z-SJBO':'#f59e0b','Z-HORT':'#8b5cf6'};
const CC={feeder:'#dc2626',distribution:'#2563eb',drop:'#16a34a'};
const gt=()=>localStorage.getItem('token');
const ah=()=>({'Authorization':'Bearer '+gt(),'Content-Type':'application/json'});
const fa=async(p)=>{const r=await fetch(API_URL+p,{headers:ah()});return r.ok?r.json():null};
const pa=async(p,b)=>{const r=await fetch(API_URL+p,{method:'POST',headers:ah(),body:JSON.stringify(b)});return r.ok?r.json():null};
const lo=()=>{localStorage.removeItem('token');window.location.reload()};

function LoginScreen({onLogin}){
  const[u,setU]=useState('');const[pw,setPw]=useState('');const[er,setEr]=useState('');
  const hl=async(e)=>{e.preventDefault();try{const r=await fetch(API_URL+'/api/auth/login/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:pw})});const d=await r.json();if(r.ok&&d.access){localStorage.setItem('token',d.access);onLogin()}else setEr('Credenciales incorrectas')}catch{setEr('Error de conexion')}};
  return React.createElement('div',{className:'min-h-screen bg-gradient-to-br from-blue-800 to-blue-900 flex items-center justify-center px-4'},
    React.createElement('div',{className:'bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md'},
      React.createElement('div',{className:'text-center mb-6'},
        React.createElement('span',{className:'text-4xl'},'\u{1F69B}'),
        React.createElement('h1',{className:'text-2xl font-bold text-gray-800 mt-2'},'FiberTruck'),
        React.createElement('p',{className:'text-gray-500 text-sm'},'Diagnostico FTTH - Cieza, Murcia'),
        React.createElement('p',{className:'text-xs text-blue-500 mt-1'},'v2.0')
      ),
      React.createElement('form',{onSubmit:hl,className:'space-y-4'},
        React.createElement('input',{type:'text',value:u,onChange:e=>setU(e.target.value),placeholder:'Usuario',className:'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        React.createElement('input',{type:'password',value:pw,onChange:e=>setPw(e.target.value),placeholder:'Contrasena',className:'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        er&&React.createElement('p',{className:'text-red-600 text-sm bg-red-50 p-2 rounded'},'⚠ '+er),
        React.createElement('button',{type:'submit',className:'w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700'},'Entrar')
      ),
      React.createElement('div',{className:'mt-4 p-3 bg-gray-50 rounded-lg'},
        React.createElement('p',{className:'text-xs text-gray-500 mb-2 font-semibold'},'Usuarios de prueba:'),
        React.createElement('div',{className:'grid grid-cols-3 gap-2'},[['admin','admin123'],['tecnico1','tecno123'],['supervisor1','super123']].map(([user,pwd])=>
          React.createElement('button',{key:user,onClick:()=>{setU(user);setPw(pwd)},className:'text-xs bg-white border rounded px-2 py-1 hover:border-blue-400'},user)
        ))
      )
    )
  );
}

function Header({activeTab,setActiveTab}){
  const tabs=[{id:'dashboard',l:'Dashboard',i:'📊'},{id:'map',l:'Mapa',i:'🗺️'},{id:'topology',l:'Red',i:'🌐'},{id:'diagnose',l:'Diagnostico',i:'🔍'},{id:'simulate',l:'Simular',i:'⚡'}];
  return React.createElement('header',{className:'bg-blue-800 text-white shadow-lg'},
    React.createElement('div',{className:'max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-2'},
      React.createElement('div',{className:'flex items-center gap-2'},
        React.createElement('span',{className:'text-2xl'},'\u{1F69B}'),
        React.createElement('div',null,React.createElement('h1',{className:'text-xl font-bold'},'FiberTruck'),React.createElement('p',{className:'text-xs text-blue-200'},'v2.0 - Cieza, Murcia'))
      ),
      React.createElement('nav',{className:'flex gap-1 flex-wrap'},tabs.map(t=>React.createElement('button',{key:t.id,onClick:()=>setActiveTab(t.id),className:'px-3 py-2 rounded-lg text-sm font-medium transition '+(activeTab===t.id?'bg-blue-600 text-white':'text-blue-200 hover:bg-blue-700')},t.i+' '+t.l))),
      React.createElement('button',{onClick:lo,className:'text-xs text-blue-300 hover:text-white'},'Salir')
    )
  );
}

function Dashboard(){
  const[stats,setStats]=useState(null);const[zones,setZones]=useState([]);const[cables,setCables]=useState([]);const[loading,setLoading]=useState(true);
  useEffect(()=>{const load=async()=>{const[s,z,c]=await Promise.all([fa('/api/incidents/stats/'),fa('/api/zones/'),fa('/api/cables/')]);setStats(s);setZones(z||[]);setCables(c||[]);setLoading(false)};load()},[]);
  if(loading)return React.createElement('div',{className:'p-8 text-center text-gray-500'},'Cargando...');
  const fb=c=>cables.filter(x=>x.cable_type===c);
  const sf=l=>l.reduce((s,x)=>s+(x.fiber_count||0),0);
  const su=l=>l.reduce((s,x)=>s+(x.fibers_used||0),0);
  return React.createElement('div',{className:'max-w-7xl mx-auto px-4 py-6 space-y-6'},
    React.createElement('div',{className:'text-center bg-white rounded-xl p-4 shadow-sm'},React.createElement('h1',{className:'text-2xl font-bold tracking-wide'},'FIBERTRUCK DASHBOARD')),
    React.createElement('div',{className:'grid grid-cols-2 md:grid-cols-4 gap-4'},
      [{t:'OLT',v:'+3.0 dBm',c:'text-blue-700'},{t:'Zonas',v:zones.length,c:'text-purple-700'},{t:'Cajas CTO',v:stats?.active_boxes||29,c:'text-blue-700'},{t:'Clientes',v:stats?.total_clients||161,c:'text-green-700'}].map((s,i)=>
        React.createElement('div',{key:i,className:'bg-white rounded-xl shadow-sm p-4 text-center border'},React.createElement('p',{className:'text-2xl font-bold '+s.c},s.v),React.createElement('p',{className:'text-xs text-gray-500'},s.t))
      )
    ),
    React.createElement('div',{className:'bg-white rounded-xl shadow-sm border overflow-hidden'},
      React.createElement('div',{className:'px-4 py-3 border-b font-bold'},'🔌 CABLES DE RED'),
      React.createElement('table',{className:'w-full text-sm'},
        React.createElement('thead',null,React.createElement('tr',{className:'bg-gray-50 text-gray-600'},['Tipo','Capacidad','Usadas','Uso'].map(h=>React.createElement('th',{key:h,className:'px-4 py-2 text-left'},h)))),
        React.createElement('tbody',{className:'divide-y divide-gray-50'},[['feeder','Feeder','bg-red-500'],['distribution','Distribution','bg-blue-500'],['drop','Drop','bg-green-500']].map(([t,n,bg])=>{const l=fb(t);const tot=sf(l);const usd=su(l);const pct=tot>0?((usd/tot)*100).toFixed(1):'0.0';return React.createElement('tr',{key:t,className:'hover:bg-gray-50'},React.createElement('td',{className:'px-4 py-2 font-semibold'},n),React.createElement('td',{className:'px-4 py-2 font-mono'},tot+'f ('+l.length+')'),React.createElement('td',{className:'px-4 py-2'},usd+'/'+tot),React.createElement('td',{className:'px-4 py-2'},React.createElement('div',{className:'flex items-center gap-2'},React.createElement('div',{className:'bg-gray-200 h-4 rounded flex-1'},React.createElement('div',{className:bg+' h-4 rounded transition-all',style:{width:pct+'%'}})),React.createElement('span',{className:'text-xs w-10'},pct+'%'))))}))
      )
    ),
    React.createElement('div',{className:'bg-white rounded-xl shadow-sm border overflow-hidden'},
      React.createElement('div',{className:'px-4 py-3 border-b font-bold'},'🏠 ESTADO DE LA RED'),
      React.createElement('table',{className:'w-full text-sm'},
        React.createElement('thead',null,React.createElement('tr',{className:'bg-gray-50 text-gray-600'},['Zona','Clientes','Afectados'].map(h=>React.createElement('th',{key:h,className:'px-4 py-2 text-left'},h)))),
        React.createElement('tbody',{className:'divide-y divide-gray-50'},zones.map(z=>React.createElement('tr',{key:z.id,className:'hover:bg-gray-50'},React.createElement('td',{className:'px-4 py-2 flex items-center gap-2'},React.createElement('div',{className:'w-3 h-3 rounded-full',style:{background:ZC[z.code]||'#666'}}),React.createElement('span',null,z.name)),React.createElement('td',{className:'px-4 py-2 text-center'},z.client_count||0),React.createElement('td',{className:'px-4 py-2 text-center'},(z.affected_client_count||0)>0?React.createElement('span',{className:'bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-bold'},z.affected_client_count):React.createElement('span',{className:'text-green-600'},'0')))))
      )
    )
  );
}

function NetworkMap(){
  const[segs,setSegs]=useState([]);const[boxes,setBoxes]=useState([]);const[splices,setSplices]=useState([]);const[splitters,setSplitters]=useState([]);const[olts,setOlts]=useState([]);const[ly,setLy]=useState({feeder:true,distribution:true,drop:true,boxes:true,splices:true,splitters:true,olt:true});
  const mapR=React.useRef(null);const lm=React.useRef(null);const lr=React.useRef({});
  useEffect(()=>{const l=async()=>{const[s,b,sp,sl,o]=await Promise.all([fa('/api/segments/'),fa('/api/boxes/'),fa('/api/splices/'),fa('/api/splitters/'),fa('/api/olts/')]);setSegs(s||[]);setBoxes(b||[]);setSplices(sp||[]);setSplitters(sl||[]);setOlts(o||[])};l()},[]);
  useEffect(()=>{if(!lm.current&&mapR.current){lm.current=L.map(mapR.current).setView([38.2395,-1.4165],15);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OSM',maxZoom:19}).addTo(lm.current)}return()=>{if(lm.current){lm.current.remove();lm.current=null}}},[]);
  useEffect(()=>{if(!lm.current)return;Object.values(lr.current).forEach(l=>{if(l&&lm.current.hasLayer(l))lm.current.removeLayer(l)});lr.current={};const gr={feeder:L.layerGroup(),distribution:L.layerGroup(),drop:L.layerGroup(),boxes:L.layerGroup(),splices:L.layerGroup(),splitters:L.layerGroup(),olt:L.layerGroup()};
    if(ly.olt&&olts[0]){const o=olts[0];L.marker([o.latitude,o.longitude],{icon:L.divIcon({className:'',html:'<div style="width:14px;height:14px;background:#dc2626;border:2px solid white;"></div>',iconSize:[14,14]})}).addTo(gr.olt).bindPopup('<b>'+o.code+'</b><br/>'+o.output_power_dbm+' dBm');}
    (segs||[]).forEach(sg=>{const st=sg.segment_type||'drop';if(!ly[st])return;const rt=sg.route_as_list||[];if(rt.length<2)return;const col=CC[st]||'#666';const w=st==='feeder'?4:st==='distribution'?3:2;const ds=st==='feeder'?'10,5':st==='drop'?'5,5':null;L.polyline(rt,{color:col,weight:w,dashArray:ds,opacity:0.8}).addTo(gr[st]).bindPopup('<b>'+sg.cable_code+'</b><br/>'+st+'<br/>'+sg.length_m+'m');});
    if(ly.splices){(splices||[]).forEach(sp=>{if(sp.latitude&&sp.longitude)L.circleMarker([sp.latitude,sp.longitude],{radius:6,fillColor:'#111',color:'#fbbf24',weight:2,fillOpacity:0.9}).addTo(gr.splices).bindPopup('<b>'+sp.code+'</b><br/>'+sp.zone_name+'<br/>'+sp.fibers_free+' free');});}
    if(ly.splitters){(splitters||[]).forEach(s=>{if(s.latitude&&s.longitude)L.circleMarker([s.latitude,s.longitude],{radius:8,fillColor:'#f97316',color:'#fff',weight:2,fillOpacity:0.9}).addTo(gr.splitters).bindPopup('<b>'+s.code+'</b><br/>1:'+s.ratio);});}
    if(ly.boxes){(boxes||[]).forEach(b=>{if(!b.latitude||!b.longitude)return;const col=ZC[b.zone_code]||'#0ea5e9';const aff=(b.affected_count||0)>0;L.circleMarker([b.latitude,b.longitude],{radius:aff?10:6,fillColor:col,color:aff?'#dc2626':'#fff',weight:aff?3:1.5,fillOpacity:aff?0.95:0.7}).addTo(gr.boxes).bindPopup('<b>'+b.code+'</b><br/>'+(b.client_count||0)+' clientes');});}
    Object.entries(gr).forEach(([k,g])=>{if(ly[k]!==false)g.addTo(lm.current);lr.current[k]=g;});
  },[segs,boxes,splices,splitters,olts,ly]);
  const tl=(k)=>setLy(p=>({...p,[k]:!p[k]}));
  return React.createElement('div',{className:'max-w-7xl mx-auto px-4 py-4'},
    React.createElement('div',{className:'flex flex-wrap gap-2 mb-3'},Object.entries({feeder:['Feeder','bg-red-100 text-red-700 border-red-300'],distribution:['Distribution','bg-blue-100 text-blue-700 border-blue-300'],drop:['Drop','bg-green-100 text-green-700 border-green-300'],boxes:['Cajas','bg-gray-100 text-gray-700 border-gray-300'],splices:['Empalmes','bg-yellow-100 text-yellow-700 border-yellow-300'],splitters:['Splitters','bg-orange-100 text-orange-700 border-orange-300'],olt:['OLT','bg-red-100 text-red-800 border-red-400']}).map(([k,[l,c]])=>React.createElement('button',{key:k,onClick:()=>tl(k),className:'px-3 py-1 rounded-lg text-xs font-medium border '+(ly[k]?c:'bg-gray-50 text-gray-400')},(ly[k]?'✓':'✗')+' '+l))),
    React.createElement('div',{ref:mapR,style:{height:'75vh'},className:'bg-white rounded-xl shadow-sm border'})
  );
}

function DiagnoseV2(){
  const[step,setStep]=useState(1);const[bc,setBc]=useState('');const[box,setBox]=useState(null);const[cl,setCl]=useState([]);const[sc,setSc]=useState([]);const[res,setRes]=useState(null);const[ld,setLd]=useState(false);const[er,setEr]=useState('');
  const sb=async()=>{setLd(true);setEr('');const b=await fa('/api/boxes/');if(b){const f=b.find(x=>x.code.toUpperCase()===bc.toUpperCase());if(f){setBox(f);const c=await fa('/api/boxes/'+f.id+'/clients/');setCl(c||[]);setStep(2)}else setEr('Caja no encontrada')}setLd(false)};
  const rdg=async()=>{if(!sc.length){setEr('Selecciona al menos un cliente');return}setLd(true);setEr('');for(const cid of sc)await pa('/api/clients/report_outage/',{client_id:cid});const d=await pa('/api/diagnose/v2/',{box_code:bc.toUpperCase(),affected_client_ids:sc});if(d){setRes(d);setStep(3)}else setEr('Error en diagnostico');setLd(false)};
  const tc=(id)=>setSc(p=>p.includes(id)?p.filter(x=>x!==id):[...p,id]);
  const reset=()=>{setStep(1);setBc('');setBox(null);setCl([]);setSc([]);setRes(null);setEr('');};
  const scn=res?res.severity==='critical'?'CRITICO':res.severity==='high'?'ALTO':res.severity==='medium'?'MEDIO':'BAJO':'';
  const scl=res?res.severity==='critical'?'border-l-4 border-red-500 bg-red-50':res.severity==='high'?'border-l-4 border-orange-500 bg-orange-50':res.severity==='medium'?'border-l-4 border-blue-500 bg-blue-50':'border-l-4 border-green-500 bg-green-50':'';
  return React.createElement('div',{className:'max-w-4xl mx-auto px-4 py-6'},
    React.createElement('div',{className:'flex items-center mb-6 gap-2'},['Caja','Afectados','Resultado'].map((s,i)=>React.createElement(React.Fragment,{key:i},React.createElement('div',{className:'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold '+(step>i+1?'bg-green-500 text-white':step===i+1?'bg-blue-600 text-white':'bg-gray-200 text-gray-500')},step>i+1?'✓':i+1),React.createElement('span',{className:'text-xs hidden md:inline'},s),i<2&&React.createElement('div',{className:'flex-1 h-1 '+(step>i+1?'bg-green-500':'bg-gray-200')})))),
    step===1&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-6'},
      React.createElement('h2',{className:'text-lg font-bold mb-2'},'Codigo de caja'),
      React.createElement('div',{className:'flex gap-2'},
        React.createElement('input',{type:'text',value:bc,onChange:e=>setBc(e.target.value.toUpperCase()),placeholder:'CTO-023',className:'flex-1 px-4 py-2 border rounded-lg font-mono'}),
        React.createElement('button',{onClick:sb,disabled:ld||!bc,className:'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50'},ld?'...':'Buscar')
      ),
      er&&React.createElement('p',{className:'text-red-600 text-sm mt-2'},er),
      React.createElement('div',{className:'mt-4 flex flex-wrap gap-2'},['CTO-001','CTO-010','CTO-020','CTO-023'].map(c=>React.createElement('button',{key:c,onClick:()=>setBc(c),className:'text-xs bg-gray-100 border rounded px-2 py-1 hover:bg-blue-100'},c)))
    ),
    step===2&&box&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-6'},
      React.createElement('h2',{className:'font-bold mb-1'},box.code+' - '+box.name),
      React.createElement('p',{className:'text-xs text-gray-500 mb-4'},box.full_path),
      React.createElement('div',{className:'space-y-2 max-h-80 overflow-y-auto mb-4 border rounded-lg p-2'},cl.map(c=>React.createElement('div',{key:c.id,onClick:()=>tc(c.id),className:'flex items-center p-2 rounded border-2 cursor-pointer '+(sc.includes(c.id)?'border-red-400 bg-red-50':'border-gray-200')},
        React.createElement('div',{className:'w-5 h-5 rounded border-2 mr-2 flex items-center justify-center '+(sc.includes(c.id)?'bg-red-500 border-red-500':'border-gray-300')},sc.includes(c.id)&&'✓'),
        React.createElement('div',{className:'flex-1'},React.createElement('p',{className:'text-sm font-semibold'},c.full_name),React.createElement('p',{className:'text-xs text-gray-500'},c.client_code)),
        c.optical_power_rx&&React.createElement('span',{className:'text-xs font-mono bg-gray-100 px-2 py-0.5 rounded'},c.optical_power_rx+' dBm')
      ))),
      React.createElement('div',{className:'flex gap-2'},
        React.createElement('button',{onClick:()=>setStep(1),className:'px-4 py-2 border rounded-lg hover:bg-gray-50'},'Atras'),
        React.createElement('button',{onClick:rdg,disabled:ld,className:'flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50'},ld?'Analizando...':'Diagnosticar '+sc.length+' afectado(s)')
      ),
      er&&React.createElement('p',{className:'text-red-600 text-sm mt-2'},er)
    ),
    step===3&&res&&React.createElement('div',{className:'space-y-4'},
      React.createElement('div',{className:'rounded-xl shadow-sm p-6 '+scl},
        React.createElement('div',{className:'flex justify-between items-center'},
          React.createElement('div',null,React.createElement('h2',{className:'text-xl font-bold'},'🚨 DIAGNOSTICO: '+scn),React.createElement('p',{className:'text-sm'},'Confianza: '+(res.confidence||0)+'%')),
          React.createElement('span',{className:'px-3 py-1 rounded-full text-sm font-bold text-white '+(res.severity==='critical'?'bg-red-600':res.severity==='high'?'bg-orange-500':res.severity==='medium'?'bg-blue-500':'bg-green-500')},res.severity.toUpperCase())
        )
      ),
      res.fault_location&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-4'},
        React.createElement('h3',{className:'font-bold mb-2'},'📍 FALLO DETECTADO'),
        React.createElement('div',{className:'bg-gray-50 rounded p-3'},React.createElement('p',{className:'font-semibold text-sm'},res.fault_location.description||'No disponible'),res.fault_location.address&&React.createElement('p',{className:'text-xs text-gray-500 mt-1'},'📍 '+res.fault_location.address))
      ),
      res.power_analysis&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-4'},
        React.createElement('h3',{className:'font-bold mb-2'},'📊 ANALISIS DE POTENCIA'),
        React.createElement('div',{className:'grid grid-cols-3 gap-3'},
          [{t:'Esperada',v:res.power_analysis.expected_dbm+' dBm',bg:'bg-green-50 border-green-200',tc:'text-green-800'},{t:'Medida',v:res.power_analysis.measured_dbm+' dBm',bg:'bg-red-50 border-red-200',tc:'text-red-800'},{t:'Perdida',v:res.power_analysis.loss_db+' dB',bg:'bg-orange-50 border-orange-200',tc:'text-orange-800'}].map((p,i)=>React.createElement('div',{key:i,className:'p-3 rounded-lg text-center border '+p.bg},React.createElement('p',{className:'text-xs text-gray-500'},p.t),React.createElement('p',{className:'text-lg font-bold '+p.tc},p.v)))
      ),
      res.recommended_action&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-4'},
        React.createElement('h3',{className:'font-bold mb-2'},'🔧 ACCION RECOMENDADA'),
        React.createElement('div',{className:'bg-blue-50 rounded-lg border border-blue-100 p-3 space-y-2'},res.recommended_action.split('\n').map((line,i)=>{const m=line.match(/^(\d+)\.\s*(.+)$/);return m?React.createElement('div',{key:i,className:'flex items-start gap-2'},React.createElement('div',{className:'w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0'},m[1]),React.createElement('p',{className:'text-sm text-blue-900 pt-0.5'},m[2])):React.createElement('p',{key:i,className:'text-sm text-blue-900'},line);}))
      ),
      res.affected_clients&&res.affected_clients.length>0&&React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-4'},
        React.createElement('h3',{className:'font-bold mb-2'},'👥 CLIENTES AFECTADOS ('+res.affected_clients.length+')'),
        React.createElement('div',{className:'space-y-1'},res.affected_clients.map((c,i)=>React.createElement('div',{key:i,className:'flex justify-between p-2 bg-red-50 rounded text-sm'},React.createElement('span',null,(c.client_code||c.code)+' - '+(c.full_name||c.name)),React.createElement('span',{className:'font-mono text-red-600'},(c.power_dbm||c.optical_power_rx||'-')+' dBm'))))
      ),
      React.createElement('button',{onClick:reset,className:'w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700'},'Nuevo diagnostico')
    )
  );
}

function Topology(){
  const[topo,setTopo]=useState(null);
  useEffect(()=>{fa('/api/topology/').then(t=>setTopo(t))},[]);
  if(!topo)return React.createElement('div',{className:'p-8 text-center text-gray-500'},'Cargando...');
  const zc=topo.zones||[];
  return React.createElement('div',{className:'max-w-7xl mx-auto px-4 py-6 space-y-6'},
    React.createElement('div',{className:'grid grid-cols-5 gap-3'},[{l:'OLT',v:1,c:'text-red-600'},{l:'Zonas',v:zc.length,c:'text-purple-600'},{l:'Cajas',v:zc.reduce((s,z)=>s+(z.boxes?.length||0),0),c:'text-blue-600'},{l:'Clientes',v:zc.reduce((s,z)=>s+(z.zone?.client_count||0),0),c:'text-green-600'},{l:'Cables',v:zc.reduce((s,z)=>s+(z.cables?.length||0),0),c:'text-orange-600'}].map((s,i)=>React.createElement('div',{key:i,className:'bg-white rounded-xl shadow-sm p-3 text-center border'},React.createElement('p',{className:'text-2xl font-bold '+s.c},s.v),React.createElement('p',{className:'text-xs text-gray-500'},s.l)))),
    React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-4'},
      React.createElement('h2',{className:'font-bold mb-3'},'🌐 Topologia: '+topo.olt?.code+' ('+topo.olt?.output_power_dbm+' dBm)'),
      React.createElement('div',{className:'space-y-2'},zc.map(z=>React.createElement('div',{key:z.zone?.id,className:'border rounded-lg p-3'},
        React.createElement('div',{className:'flex items-center gap-2 mb-2'},React.createElement('div',{className:'w-3 h-3 rounded-full',style:{background:ZC[z.zone?.code]||'#666'}}),React.createElement('span',{className:'font-bold'},z.zone?.name),React.createElement('span',{className:'text-xs text-gray-400'},z.zone?.code),React.createElement('span',{className:'text-xs bg-blue-100 text-blue-700 px-2 rounded-full ml-auto'},(z.zone?.client_count||0)+' clientes')),
        React.createElement('div',{className:'ml-4 space-y-1 text-sm'},
          z.splice&&React.createElement('p',null,React.createElement('span',{className:'text-yellow-600 font-semibold'},'● '+z.splice.code),React.createElement('span',{className:'text-xs text-gray-400 ml-2'},z.splice.address)),
          (z.splitters||[]).map(s=>React.createElement('div',{key:s.id,className:'ml-4'},
            React.createElement('p',null,React.createElement('span',{className:'text-orange-600 font-semibold'},'★ '+s.code),' 1:',s.ratio,React.createElement('span',{className:'text-xs text-gray-400 ml-2'},s.output_power_dbm,' dBm')),
            (z.cables||[]).filter(c=>c.cable_type==='drop').map(d=>{
              const db=(z.boxes||[]).filter(b=>b.input_cable_code===d.code);
              return db.length>0&&React.createElement('div',{key:d.id,className:'ml-4 text-xs'},
                React.createElement('p',{className:'text-green-600'},'├ '+d.code+' ('+d.fiber_count+'f)'),
                React.createElement('div',{className:'ml-3 space-y-0.5'},db.map(b=>React.createElement('p',{key:b.id,className:'text-blue-700'},'└ '+b.code+' - '+b.name+' ('+(b.client_count||0)+'cli, fibra#'+b.input_fiber_number+')')))
              );
            })
          ))
        )
      )))
    )
  );
}

function Simulate(){
  const[boxes,setBoxes]=useState([]);const[loading,setLoading]=useState(false);
  useEffect(()=>{fa('/api/boxes/').then(b=>setBoxes(b||[]))},[]);
  const sim=async()=>{setLoading(true);const b=await fa('/api/boxes/');const ab=(b||[]).filter(x=>x.client_count>0);const t=ab[Math.floor(Math.random()*ab.length)];if(t){const c=await fa('/api/boxes/'+t.id+'/clients/');const n=Math.min(Math.floor(Math.random()*3)+1,(c||[]).length);const ac=(c||[]).sort(()=>0.5-Math.random()).slice(0,n);for(const cl of ac)await pa('/api/clients/report_outage/',{client_id:cl.id})}const u=await fa('/api/boxes/');setBoxes(u||[]);setLoading(false)};
  const rst=async()=>{setLoading(true);const a=await fa('/api/clients/');for(const c of(a||[]).filter(x=>x.status==='affected')){await fetch(API_URL+'/api/clients/'+c.id+'/',{method:'PATCH',headers:ah(),body:JSON.stringify({status:'active'})})}const u=await fa('/api/boxes/');setBoxes(u||[]);setLoading(false)};
  const aff=boxes.filter(b=>(b.affected_count||0)>0);const ta=aff.reduce((s,b)=>s+(b.affected_count||0),0);
  return React.createElement('div',{className:'max-w-4xl mx-auto px-4 py-6'},
    React.createElement('div',{className:'bg-white rounded-xl shadow-sm border p-6'},
      React.createElement('h2',{className:'text-xl font-bold mb-2'},'Simulador de Averias'),
      React.createElement('div',{className:'flex gap-3 mb-4'},
        React.createElement('button',{onClick:sim,disabled:loading,className:'flex-1 py-3 bg-red-500 text-white rounded-lg font-bold disabled:opacity-50'},loading?'...':'Simular averia'),
        React.createElement('button',{onClick:rst,disabled:loading,className:'px-4 py-3 bg-green-500 text-white rounded-lg font-bold disabled:opacity-50'},'Restaurar')
      ),
      aff.length===0?React.createElement('div',{className:'p-4 bg-green-50 border border-green-200 rounded-lg text-center'},React.createElement('p',{className:'text-green-700 font-bold text-lg'},'✅ Todo operativo')):
      React.createElement('div',{className:'space-y-2'},React.createElement('p',{className:'text-sm font-semibold text-red-600'},ta+' cliente(s) afectado(s) en '+aff.length+' caja(s):'),aff.map(b=>React.createElement('div',{key:b.id,className:'flex justify-between p-2 bg-red-50 border border-red-200 rounded'},React.createElement('span',{className:'font-mono font-bold text-red-800'},b.code),React.createElement('span',{className:'bg-red-500 text-white px-2 py-0.5 rounded-full text-sm font-bold'},b.affected_count))))
    )
  );
}

function App(){
  const[li,setLi]=useState(!!gt());const[at,setAt]=useState('dashboard');
  if(!li)return React.createElement(LoginScreen,{onLogin:()=>setLi(true)});
  const rt=()=>{switch(at){case'dashboard':return React.createElement(Dashboard);case'map':return React.createElement(NetworkMap);case'topology':return React.createElement(Topology);case'diagnose':return React.createElement(DiagnoseV2);case'simulate':return React.createElement(Simulate);default:return React.createElement(Dashboard)}};
  return React.createElement('div',{className:'min-h-screen bg-gray-100'},React.createElement(Header,{activeTab:at,setActiveTab:setAt}),React.createElement('main',null,rt()),React.createElement('footer',{className:'bg-gray-800 text-gray-400 text-center py-3 text-xs mt-8'},'FiberTruck v2.0 - TFM Master Full Stack | Cieza, Murcia'));
}
// Use ReactDOM.render for UMD compatibility
ReactDOM.render(React.createElement(App),document.getElementById('root'));
