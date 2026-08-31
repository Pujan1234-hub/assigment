(()=>{'use strict';
if(window.__fsTrustedRiverRuntimeV1)return;window.__fsTrustedRiverRuntimeV1=true;
const SNAP='../../data/floodsafe-core.json',MAX=20*60*1000,FUTURE=5*60*1000;
let trusted=[],busy=false,last=0;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const stamp=o=>val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);
const level=o=>{const n=Number(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level']));return Number.isFinite(n)?n:null};
function valid(o){if(!o||typeof o!=='object'||o._measurementTimeTrusted===false||o._current20m===false||level(o)===null)return false;const t=+new Date(stamp(o)||0);if(!t)return false;const a=Date.now()-t;return a>=-FUTURE&&a<=MAX}
function enforce(){const S=window.FloodSafe?.state;if(!S)return;S.stations=trusted.slice();S.lastPoll=last||Date.now();S.feedSource=`trusted DHM/BIPAD snapshot • ${trusted.length} current ≤20m`;window.dispatchEvent(new CustomEvent('fstrustedriverupdate',{detail:{count:trusted.length,lastFetch:last}}))}
async function poll(){if(busy)return;busy=true;try{const r=await fetch(SNAP+'?trusted='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const j=await r.json(),src=j?.sources?.rivers||{},all=Array.isArray(j?.rivers)?j.rivers:[];const next=all.filter(valid);if(Number.isFinite(+src.current_20m_count)&&+src.current_20m_count!==next.length)console.warn('FloodSafe trusted count mismatch',src.current_20m_count,next.length);trusted=next;last=Date.now();enforce()}catch(e){console.warn('FloodSafe trusted snapshot poll failed',e);enforce()}finally{busy=false}}
function boot(){poll();setInterval(poll,5000);setInterval(()=>{if(!document.hidden)enforce()},1000);window.addEventListener('online',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();