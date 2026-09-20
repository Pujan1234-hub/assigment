(()=>{
'use strict';
if(window.__fsAndroidAllStationsRealtimeV1)return;
window.__fsAndroidAllStationsRealtimeV1=true;

const API='https://bipadportal.gov.np/api/v1';
const MAX_AGE=10*60*1000;
const FUTURE=5*60*1000;
const LAKE_PROBE_INTERVAL=15*60*1000;
const LAKE_ENDPOINTS=[
  `${API}/lake-stations/?limit=2000`,
  `${API}/reservoir-stations/?limit=2000`,
  `${API}/lake/?limit=2000`,
  `${API}/reservoir/?limit=2000`
];
const COLORS={danger:'#ff2d20',warning:'#ff8a00',watch:'#ffd43b',alert:'#ffd43b',normal:'#20a9ff',unknown:'#94a3b8'};
let rainSig='';
let extraSig='';
let rainBound=false;
let extraBound=false;
let lakeEndpoint='';
let nextLakeProbe=0;
let lakeBusy=false;
let lastLakeRows=[];

const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?{...o.fields,...o}:o;
const val=(o,ks)=>{o=flat(o);for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const num=v=>{if(typeof v==='number')return Number.isFinite(v)?v:null;if(v===null||v===undefined)return null;const n=Number(String(v).replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne';
const tr=(ne,en)=>lang()==='en'?en:ne;
const rows=j=>Array.isArray(j)?j:Array.isArray(j?.results)?j.results:Array.isArray(j?.data)?j.data:Array.isArray(j?.features)?j.features:[];

function coord(raw){
  const o=flat(raw);
  for(const c of[o?._stationCoordinate,o?.point?.coordinates,o?.location?.coordinates,o?.geometry?.coordinates,o?.centroid?.coordinates]){
    if(!Array.isArray(c)||c.length<2)continue;
    const a=+c[0],b=+c[1];
    if(a>=79&&a<=90&&b>=25&&b<=32)return[a,b];
    if(b>=79&&b<=90&&a>=25&&a<=32)return[b,a];
  }
  const lo=num(val(o,['longitude','lon','lng','long','stationLongitude','station_longitude']));
  const la=num(val(o,['latitude','lat','stationLatitude','station_latitude']));
  return lo!==null&&la!==null?[lo,la]:null;
}
function stamp(o){return val(o,['rainfallOn','rainfall_on','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','observation_time','observedAt','observed_at','updatedOn','updated_at','timestamp','datetime','dateTime'])}
function current(o){const t=+new Date(stamp(o)||0);if(!t)return false;const age=Date.now()-t;return age>=-FUTURE&&age<=MAX_AGE}
function stationId(o){return String(val(o,['stationSeriesId','station_series_id','stationId','station_id','stationIndex','station_index','id'])??'')}
function stationName(o,fallback){return String(val(o,['title','station_name','stationName','river_name','riverName','name','locationName','location_name'])||fallback||'Official station')}
function fmtTime(v){if(!v)return'—';const d=new Date(v);if(!Number.isFinite(+d))return String(v);try{return new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(d)+' NPT'}catch{return String(v)}}
function averageRows(o){return window.FloodSafeRainRealtime?.averageRows?.(o)||[]}
function rainStatus(o){return window.FloodSafeRainRealtime?.riskStage?.(o)||'normal'}
function rainValue(o,interval){const a=averageRows(o).find(x=>Number(x.interval)===interval);return a&&Number.isFinite(+a.value)?+a.value:null}
function latestRain(o){const x=window.FloodSafeRainRealtime?.rainAt?.(o,1);return Number.isFinite(+x)?+x:null}

function rainFeature(raw){
  const o=flat(raw),c=coord(o);if(!c)return null;
  const av=averageRows(o),status=rainStatus(o),t=stamp(o);
  return{type:'Feature',geometry:{type:'Point',coordinates:c},properties:{
    kind:'rain',name:stationName(o,'Rain station'),station_id:stationId(o),status,
    time:String(t||''),basin:String(val(o,['basin','basin_name','basinName'])||''),
    district:String(val(o,['districtName','district_name','district'])||''),
    r1:rainValue(o,1)??'',r3:rainValue(o,3)??'',r6:rainValue(o,6)??'',
    r12:rainValue(o,12)??'',r24:rainValue(o,24)??'',rainfall:latestRain(o)??'',
    intervals:JSON.stringify(av),source:'BIPAD / DHM official realtime'
  }};
}
function rainCollection(){
  const list=window.FloodSafeRainRealtime?.current||[];
  return{type:'FeatureCollection',features:list.map(rainFeature).filter(Boolean)};
}
function signature(fc){return fc.features.map(f=>`${f.properties.station_id}|${f.properties.time}|${f.properties.status}|${f.properties.r1}|${f.properties.r3}|${f.properties.r6}|${f.properties.r12}|${f.properties.r24}`).sort().join('~')}

function ensureRain(map){
  if(!map||!map.isStyleLoaded?.())return false;
  if(!map.getSource('rain-live-all-src'))map.addSource('rain-live-all-src',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  if(!map.getLayer('rain-live-all'))map.addLayer({id:'rain-live-all',type:'circle',source:'rain-live-all-src',paint:{
    'circle-radius':['interpolate',['linear'],['zoom'],5,3.5,8,5,11,7,14,9],
    'circle-color':['match',['get','status'],'danger',COLORS.danger,'warning',COLORS.warning,'watch',COLORS.watch,'alert',COLORS.alert,COLORS.normal],
    'circle-stroke-color':'#ffffff','circle-stroke-width':['interpolate',['linear'],['zoom'],5,1,10,1.7,14,2.2],'circle-opacity':.94
  }});
  if(!rainBound){
    rainBound=true;
    map.on('click','rain-live-all',e=>{const f=e.features?.[0];if(f)showRain(f.properties,f.geometry.coordinates)});
    map.on('mouseenter','rain-live-all',()=>{map.getCanvas().style.cursor='pointer'});
    map.on('mouseleave','rain-live-all',()=>{map.getCanvas().style.cursor=''})
  }
  try{map.moveLayer('rain-live-all')}catch{}
  return true;
}
function renderRain(force=false){
  const map=window.FloodSafeMap?.map;if(!ensureRain(map))return false;
  const fc=rainCollection(),sig=signature(fc);
  if(force||sig!==rainSig){
    rainSig=sig;
    map.getSource('rain-live-all-src')?.setData(fc);
    window.__fsAndroidRainMapState={count:fc.features.length,checkedAt:new Date().toISOString(),source:'BIPAD / DHM official realtime'};
  }
  return true;
}
function rainLine(label,v){return v!==undefined&&v!==null&&v!==''?`<div><span style="opacity:.72">${esc(label)}</span><br><b>${esc(v)} mm</b></div>`:''}
function showRain(p,ll){
  const map=window.FloodSafeMap?.map;if(!map||!window.maplibregl)return;
  const status=String(p.status||'normal').toUpperCase();
  new maplibregl.Popup({maxWidth:'370px',closeButton:true,closeOnClick:true}).setLngLat(ll).setHTML(`<div style="font-family:system-ui;line-height:1.45;min-width:250px"><b style="font-size:16px">🌧️ ${esc(p.name)}</b><div style="margin:6px 0 8px;font-weight:900">${esc(status)}</div><div><b>${tr('स्टेशन ID','Station ID')}:</b> ${esc(p.station_id||'—')}</div><div><b>${tr('जिल्ला','District')}:</b> ${esc(p.district||'—')}</div><div><b>Basin:</b> ${esc(p.basin||'—')}</div><div><b>${tr('आधिकारिक observation','Official observation')}:</b> ${esc(fmtTime(p.time))}</div><hr style="border:0;border-top:1px solid #ddd"><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px">${rainLine('1 HR',p.r1)}${rainLine('3 HR',p.r3)}${rainLine('6 HR',p.r6)}${rainLine('12 HR',p.r12)}${rainLine('24 HR',p.r24)}</div><div style="margin-top:9px;font-size:12px"><b>Source:</b> BIPAD / DHM official realtime</div></div>`).addTo(map)
}

function hydroStatus(o){
  const raw=String(val(o,['status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').toUpperCase();
  const l=num(val(o,['waterLevel','water_level','currentWaterLevel','current_level','level','value']));
  const w=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold']));
  const d=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold']));
  if((l!==null&&d!==null&&d>0&&l>=d)||/DANGER|RED/.test(raw))return'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||/WARNING|ORANGE/.test(raw))return'warning';
  if(/WATCH|ALERT|YELLOW|RISING/.test(raw))return'watch';
  return'normal';
}
function extraFeature(raw){
  const o=flat(raw),c=coord(o);if(!c||!current(o))return null;
  const level=num(val(o,['waterLevel','water_level','currentWaterLevel','current_level','level','value']));
  return{type:'Feature',geometry:{type:'Point',coordinates:c},properties:{kind:'lake',name:stationName(o,'Lake / reservoir station'),station_id:stationId(o),status:hydroStatus(o),time:String(stamp(o)||''),level:level??'',warning:num(val(o,['warningLevel','warning_level','warningThreshold']))??'',danger:num(val(o,['dangerLevel','danger_level','dangerThreshold']))??'',basin:String(val(o,['basin','basin_name','basinName'])||''),district:String(val(o,['districtName','district_name','district'])||''),source:'BIPAD official realtime'}}
}
function ensureExtra(map){
  if(!map||!map.isStyleLoaded?.())return false;
  if(!map.getSource('hydro-extra-live-src'))map.addSource('hydro-extra-live-src',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  if(!map.getLayer('hydro-extra-live'))map.addLayer({id:'hydro-extra-live',type:'circle',source:'hydro-extra-live-src',paint:{'circle-radius':['interpolate',['linear'],['zoom'],5,4,10,7,14,9],'circle-color':['match',['get','status'],'danger',COLORS.danger,'warning',COLORS.warning,'watch',COLORS.watch,COLORS.normal],'circle-stroke-color':'#dbeafe','circle-stroke-width':2,'circle-opacity':.95}});
  if(!extraBound){extraBound=true;map.on('click','hydro-extra-live',e=>{const f=e.features?.[0];if(f)showExtra(f.properties,f.geometry.coordinates)});map.on('mouseenter','hydro-extra-live',()=>{map.getCanvas().style.cursor='pointer'});map.on('mouseleave','hydro-extra-live',()=>{map.getCanvas().style.cursor=''})}
  try{map.moveLayer('hydro-extra-live')}catch{}
  return true;
}
function renderExtra(force=false){
  const map=window.FloodSafeMap?.map;if(!ensureExtra(map))return false;
  const fc={type:'FeatureCollection',features:lastLakeRows.map(extraFeature).filter(Boolean)},sig=signature(fc);
  if(force||sig!==extraSig){extraSig=sig;map.getSource('hydro-extra-live-src')?.setData(fc);window.__fsAndroidHydroExtraMapState={count:fc.features.length,endpoint:lakeEndpoint||null,checkedAt:new Date().toISOString()}}
  return true;
}
function showExtra(p,ll){
  const map=window.FloodSafeMap?.map;if(!map||!window.maplibregl)return;
  new maplibregl.Popup({maxWidth:'360px'}).setLngLat(ll).setHTML(`<div style="font-family:system-ui;line-height:1.45;min-width:240px"><b style="font-size:16px">💧 ${esc(p.name)}</b><div style="margin:6px 0;font-weight:900">${esc(String(p.status||'normal').toUpperCase())}</div><div><b>${tr('स्टेशन ID','Station ID')}:</b> ${esc(p.station_id||'—')}</div><div><b>${tr('जिल्ला','District')}:</b> ${esc(p.district||'—')}</div><div><b>Basin:</b> ${esc(p.basin||'—')}</div><div><b>${tr('पानीको सतह','Water level')}:</b> ${p.level!==''?esc(p.level)+' m':'—'}</div><div><b>${tr('चेतावनी तह','Warning level')}:</b> ${p.warning!==''?esc(p.warning)+' m':'—'}</div><div><b>${tr('खतरा तह','Danger level')}:</b> ${p.danger!==''?esc(p.danger)+' m':'—'}</div><div><b>${tr('आधिकारिक observation','Official observation')}:</b> ${esc(fmtTime(p.time))}</div><div style="margin-top:8px;font-size:12px"><b>Source:</b> BIPAD official realtime</div></div>`).addTo(map)
}
async function getJson(url,timeout=9000){const c=new AbortController(),to=setTimeout(()=>c.abort(),timeout);try{const r=await fetch(url+(url.includes('?')?'&':'?')+'_fs='+Date.now(),{cache:'no-store',credentials:'omit',mode:'cors',signal:c.signal,headers:{Accept:'application/json'}});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(to)}}
async function discoverLakeEndpoint(){
  if(Date.now()<nextLakeProbe||lakeBusy)return;
  nextLakeProbe=Date.now()+LAKE_PROBE_INTERVAL;
  for(const url of LAKE_ENDPOINTS){
    try{const j=await getJson(url),a=rows(j);if(a.length){lakeEndpoint=url;lastLakeRows=a;renderExtra(true);window.dispatchEvent(new CustomEvent('fshydroextraupdate',{detail:{count:a.length,endpoint:url}}));return}}catch{}
  }
  lakeEndpoint='';lastLakeRows=[];renderExtra(true)
}
async function refreshLake(){
  if(lakeBusy)return;
  if(!lakeEndpoint){discoverLakeEndpoint();return}
  lakeBusy=true;
  try{const j=await getJson(lakeEndpoint),a=rows(j);if(a.length){const old=extraSig;lastLakeRows=a;renderExtra(false);if(extraSig!==old)window.dispatchEvent(new CustomEvent('fshydroextraupdate',{detail:{count:a.length,endpoint:lakeEndpoint}}))}}
  catch{lakeEndpoint='';nextLakeProbe=Date.now()+60000}
  finally{lakeBusy=false}
}

function refreshAll(){renderRain(false);refreshLake()}
for(const ev of['fsmapready','fs281mapready','fsrainupdate','fslanguage'])window.addEventListener(ev,()=>setTimeout(()=>{renderRain(ev==='fslanguage');renderExtra(ev==='fslanguage')},0));
window.addEventListener('fsandroidlivetick',refreshAll);
window.addEventListener('focus',()=>{renderRain(true);refreshLake()});
window.addEventListener('online',()=>{renderRain(true);refreshLake()});
let tries=0;const boot=setInterval(()=>{const map=window.FloodSafeMap?.map;if(map&&map.isStyleLoaded?.()){clearInterval(boot);renderRain(true);renderExtra(true);discoverLakeEndpoint()}else if(++tries>240)clearInterval(boot)},250);

window.FloodSafeHydroExtraRealtime={refresh:refreshLake,get endpoint(){return lakeEndpoint||null},get current(){return lastLakeRows.slice()}};
window.FloodSafeAndroidAllStations={refresh:refreshAll,renderRain,renderExtra,get rainCount(){return window.__fsAndroidRainMapState?.count||0},get lakeCount(){return window.__fsAndroidHydroExtraMapState?.count||0}};
})();
