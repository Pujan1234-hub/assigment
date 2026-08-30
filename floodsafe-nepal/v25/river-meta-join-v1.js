(()=>{'use strict';
if(window.__fsRiverMetaJoinV1)return;window.__fsRiverMetaJoinV1=true;
const URL='https://bipadportal.gov.np/api/v1/river-stations/?limit=2000';
let meta=[],busy=false,lastFetch=0,patching=false;
const rows=j=>Array.isArray(j)?j:(j?.results||j?.data||j?.objects||[]);
const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+(?:at|near)\s+.*/i,'').replace(/\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b/g,' ').replace(/[^a-z0-9]+/g,' ').replace(/\s+/g,' ').trim();
function ids(o){o=flat(o);const a=[val(o,['station','stationId','station_id','stationSeriesId','station_series_id','id']),o?.station?.id,o?.station?.stationSeriesId].filter(v=>v!==null&&v!==undefined&&v!=='');return [...new Set(a.map(String))]}
function name(o){o=flat(o);return String(val(o,['title','river_name','riverName','station_name','stationName','name'])||o?.station?.name||'')}
function point(o){o=flat(o);if(o?.point||o?.latitude||o?.lat||o?.location)return true;return false}
function build(){const byId=new Map(),byName=new Map();for(const raw of meta){const m=flat(raw);for(const id of ids(m))if(!byId.has(id))byId.set(id,m);const n=norm(name(m));if(n&&!byName.has(n))byName.set(n,m)}return{byId,byName}}
async function fetchMeta(force=false){if(busy)return;if(!force&&Date.now()-lastFetch<60000&&meta.length)return;busy=true;try{const r=await fetch(URL+(URL.includes('?')?'&':'?')+'_rmj='+Date.now(),{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error(r.status);meta=rows(await r.json()).map(flat);lastFetch=Date.now()}catch{}finally{busy=false}}
async function patch(){if(patching)return;patching=true;try{await fetchMeta(false);const S=window.FloodSafe?.state;if(!S||!Array.isArray(S.stations)||!meta.length)return;const {byId,byName}=build();let changed=0;S.stations=S.stations.map(raw=>{const r=flat(raw);let m=null;for(const id of ids(r)){if(byId.has(id)){m=byId.get(id);break}}if(!m){const n=norm(name(r));if(n)m=byName.get(n)||null}if(!m)return r;const joined=Object.assign({},m,r);if(!point(r)&&point(m))changed++;return joined});if(changed)window.dispatchEvent(new CustomEvent('fsgaugemeta',{detail:{changed,total:S.stations.length}}))}finally{patching=false}}
function boot(){fetchMeta(true).then(patch);window.addEventListener('fsriverupdate',()=>setTimeout(patch,0));setInterval(()=>fetchMeta(true).then(patch),60000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();