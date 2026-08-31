(()=>{'use strict';
if(window.__fsTrustedRiverRuntimeV3)return;window.__fsTrustedRiverRuntimeV3=true;
const SNAP='../../data/floodsafe-core.json';
const MAX=20*60*1000,FUTURE=5*60*1000,MIRROR_MAX=5*60*1000,POLL=1000;
let trusted=[],busy=false,last=0,lastGenerated='';
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o;
const stamp=o=>val(flat(o),['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);
const level=o=>{const n=Number(val(flat(o),['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level']));return Number.isFinite(n)?n:null};
function valid(raw){const o=flat(raw);if(!o||typeof o!=='object'||o._measurementTimeTrusted===false||o._current20m===false||level(o)===null)return false;const t=+new Date(stamp(o)||0);if(!t)return false;const a=Date.now()-t;return a>=-FUTURE&&a<=MAX}
function mirrorFresh(g){const t=+new Date(g||0);if(!t)return false;const a=Date.now()-t;return a>=-FUTURE&&a<=MIRROR_MAX}
async function getJson(url,timeout=5000){const c=new AbortController(),to=setTimeout(()=>c.abort(),timeout);try{const r=await fetch(url,{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(to)}}
function enforce(source='official mirror'){trusted=trusted.filter(valid);if(lastGenerated&&!mirrorFresh(lastGenerated)){trusted=[];source='official mirror stale'}const S=window.FloodSafe?.state;if(!S)return;S.stations=trusted.slice();S.lastPoll=last||Date.now();S.feedSource=`${source} • ${trusted.length} current ≤20m`;const detail={count:trusted.length,lastFetch:last,source,generatedAt:lastGenerated,mirrorFresh:mirrorFresh(lastGenerated)};window.dispatchEvent(new CustomEvent('fstrustedriverupdate',{detail}));window.dispatchEvent(new CustomEvent('fsriverupdate',{detail}))}
async function poll(){if(busy||document.hidden||!navigator.onLine)return;busy=true;try{const j=await getJson(SNAP+'?official_mirror='+Date.now()),all=Array.isArray(j?.rivers)?j.rivers:[],generated=String(j?.generated_at||'');last=Date.now();lastGenerated=generated;if(!mirrorFresh(generated)){trusted=[];enforce('official mirror stale');return}trusted=all.filter(valid);enforce('DHM/BIPAD official mirror')}catch(e){console.warn('FloodSafe official river mirror poll failed',e);enforce(trusted.length?'last-good official mirror':'official mirror unavailable')}finally{busy=false}}
function boot(){poll();setInterval(poll,POLL);setInterval(()=>{if(!document.hidden)enforce(trusted.length?'DHM/BIPAD official mirror':'official mirror unavailable')},1000);window.addEventListener('online',poll);document.addEventListener('visibilitychange',()=>{if(!document.hidden)poll()})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
