(()=>{'use strict';
if(window.__fsTrustedRiverRuntimeV2)return;window.__fsTrustedRiverRuntimeV2=true;
const SNAP='../../data/floodsafe-core.json';
const API='https://bipadportal.gov.np/api/v1/';
const RIVER='river/?limit=2000&ordering=-waterLevelOn';
const META='river-stations/?limit=2000';
const MAX=20*60*1000,FUTURE=5*60*1000,POLL=5000;
let trusted=[],busy=false,last=0,metaCache=[],metaAt=0,lastDirectOk=0;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o;
const rows=j=>Array.isArray(j)?j:(Array.isArray(j?.results)?j.results:(Array.isArray(j?.data)?j.data:[]));
const stamp=o=>val(flat(o),['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);
const level=o=>{const n=Number(val(flat(o),['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level']));return Number.isFinite(n)?n:null};
const key=o=>String(val(flat(o),['stationSeriesId','station_series_id','stationId','station_id','id'])??'');
const title=o=>String(val(flat(o),['title','river_name','riverName','station_name','stationName','name'])||'').trim().toLowerCase().replace(/\s+/g,' ');
function valid(o){o=flat(o);if(!o||typeof o!=='object'||level(o)===null)return false;const t=+new Date(stamp(o)||0);if(!t)return false;const a=Date.now()-t;return a>=-FUTURE&&a<=MAX}
function point(o){const p=flat(o)?.point;if(p&&Array.isArray(p.coordinates)&&p.coordinates.length>=2)return p;return null}
function joinMeta(readings,meta){const byId=new Map(),byName=new Map();for(const raw of meta){const m=flat(raw);const id=key(m);if(id)byId.set(id,m);const n=title(m);if(n)byName.set(n,m)}return readings.map(raw=>{const r=flat(raw);const m=(key(r)&&byId.get(key(r)))||byName.get(title(r));return m?Object.assign({},m,r,{point:point(r)||point(m)}):r})}
async function getJson(url,timeout=6500){const c=new AbortController(),to=setTimeout(()=>c.abort(),timeout);try{const r=await fetch(url,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',headers:{accept:'application/json'},signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(to)}}
async function getMeta(){if(metaCache.length&&Date.now()-metaAt<10*60*1000)return metaCache;const j=await getJson(API+META);const a=rows(j);if(a.length){metaCache=a;metaAt=Date.now()}return metaCache}
function enforce(source){const S=window.FloodSafe?.state;if(!S)return;S.stations=trusted.slice();S.lastPoll=last||Date.now();S.feedSource=`${source||'official'} • ${trusted.length} current ≤20m`;window.dispatchEvent(new CustomEvent('fstrustedriverupdate',{detail:{count:trusted.length,lastFetch:last,source:source||'official'}}));window.dispatchEvent(new CustomEvent('fsriverupdate',{detail:{count:trusted.length,lastFetch:last,source:source||'official'}}))}
async function direct(){const [jr,jm]=await Promise.all([getJson(API+RIVER),getMeta().catch(()=>metaCache)]);const rr=rows(jr);if(!rr.length)throw Error('empty BIPAD river feed');const joined=joinMeta(rr,Array.isArray(jm)?jm:metaCache);const next=joined.filter(valid);if(!next.length)throw Error('no BIPAD observation <=20m');trusted=next;last=Date.now();lastDirectOk=last;enforce('BIPAD/DHM direct');return true}
async function snapshot(){const j=await getJson(SNAP+'?trusted='+Date.now());const all=Array.isArray(j?.rivers)?j.rivers:[];const next=all.filter(valid);if(next.length){trusted=next;last=Date.now();enforce('DHM/BIPAD snapshot');return true}return false}
async function poll(){if(busy||document.hidden||!navigator.onLine)return;busy=true;try{await direct()}catch(e){console.warn('FloodSafe direct river poll failed',e);try{if(!trusted.length||Date.now()-lastDirectOk>15000)await snapshot()}catch(x){console.warn('FloodSafe river snapshot fallback failed',x)}finally{enforce(trusted.length?'last-good official':'official unavailable')}}finally{busy=false}}
function boot(){poll();setInterval(poll,POLL);setInterval(()=>{if(!document.hidden)enforce(lastDirectOk?'BIPAD/DHM direct':'official fallback')},1000);window.addEventListener('online',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();