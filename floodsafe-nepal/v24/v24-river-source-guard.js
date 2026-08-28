(()=>{
'use strict';
if(window.__fsRiverSourceGuardV1)return;window.__fsRiverSourceGuardV1=true;
const native=window.fetch.bind(window),BASE='https://bipadportal.gov.np/api/v1/',URLS=[BASE+'river/?limit=700',BASE+'river-stations/?limit=700'];
let cache=null,pending=null,lastAt=0;
const rows=j=>Array.isArray(j)?j:(j?.results||j?.data||j?.objects||[]);
const when=o=>o?.waterLevelOn||o?.measuredOn||o?.modifiedOn||o?.updatedOn||o?.updated_at||o?.createdOn||o?.created_at||o?.date||null;
const level=o=>{for(const k of ['waterLevel','water_level','currentLevel','current_level','level','value']){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return Number(v)}return null};
const coord=o=>{const c=o?.point?.coordinates||o?.location?.coordinates||o?.centroid?.coordinates||o?.geometry?.coordinates;return Array.isArray(c)&&c.length>=2?c:null};
const name=o=>String(o?.river_name||o?.riverName||o?.station_name||o?.stationName||o?.title||o?.name||o?.station?.name||'');
function key(o){const id=o?.stationSeriesId||o?.station_series_id||o?.id||o?.pk||o?.uuid;if(id!==undefined&&id!==null)return'id:'+id;const c=coord(o);return'name:'+name(o).toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim()+'|'+(c?c.map(x=>Number(x).toFixed(4)).join(','):'')}
function ts(o){const n=+new Date(when(o)||0);return Number.isFinite(n)?n:0}
function cleanThresholds(o){if(!o||typeof o!=='object')return o;const x={...o};for(const k of ['warningLevel','warning_level','dangerLevel','danger_level'])if(k in x&&!(Number(x[k])>0))x[k]=null;return x}
async function raw(url,ms=6500){const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);try{const r=await native(url+(url.includes('?')?'&':'?')+'_rguard='+Date.now(),{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',headers:{accept:'application/json'},signal:c.signal});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(to)}}
async function merged(force=false){if(!force&&cache&&Date.now()-lastAt<3500)return cache;if(pending)return pending;pending=(async()=>{const rs=await Promise.allSettled(URLS.map(u=>raw(u))),all=[];for(const r of rs)if(r.status==='fulfilled')all.push(...rows(r.value));const m=new Map();for(const rawO of all){const o=cleanThresholds(rawO),k=key(o),old=m.get(k);if(!old||ts(o)>=ts(old))m.set(k,o)}const now=Date.now(),fresh=[],stale=[];for(const o of m.values()){const t=ts(o),hasLive=Number.isFinite(level(o));if(!t||now-t>2*3600e3){if(hasLive||t)stale.push(o);continue}fresh.push(o)}cache=fresh;lastAt=Date.now();window.__fsRiverSourceHealth={fresh:fresh.length,staleExcluded:stale.length,checkedAt:lastAt,source:'DHM via BIPAD /river + /river-stations'};return fresh})().finally(()=>pending=null);return pending}
window.fetch=async function(input,init){const u=String(input?.url||input||'');if(!/https:\/\/bipadportal\.gov\.np\/api\/v1\/(river|river-stations)\//i.test(u))return native(input,init);try{const data=await merged(false);return new Response(JSON.stringify({results:data}),{status:200,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-FloodSafe-River-Guard':'fresh-merged'}})}catch(e){return native(input,init)}};
window.__fsRiverGuardRefresh=()=>merged(true);
})();