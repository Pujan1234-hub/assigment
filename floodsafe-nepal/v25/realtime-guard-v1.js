(()=>{'use strict';
if(window.__fsRealtimeGuardV8)return;window.__fsRealtimeGuardV8=true;
const FRESH10_MS=10*60*1000,FUTURE_TOLERANCE_MS=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','observation_time','observedAt','observed_at','datetime','timestamp'])}
function level(o){o=flat(o);const v=val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','value']),n=Number(v);return Number.isFinite(n)?n:null}
function ageMs(o){const t=+new Date(stamp(o)||0);return t?Date.now()-t:Infinity}
function hasRawObservation(o){return !!(+new Date(stamp(o)||0))&&level(o)!==null}
function current(o){const a=ageMs(o);return hasRawObservation(o)&&Number.isFinite(a)&&a>=-FUTURE_TOLERANCE_MS&&a<=FRESH10_MS}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'All official BIPAD/DHM stations • only readings ≤10 min are treated as current':'सबै official BIPAD/DHM station • १० मिनेटभित्रको reading मात्र current मानिन्छ';if(near)near.textContent=en?'Official gauges refresh silently; readings older than 10 minutes are hidden until a new verified update arrives':'Official gauge background मा smooth refresh हुन्छ • १० मिनेटभन्दा पुरानो reading नयाँ verified update नआएसम्म लुकाइन्छ'}
window.FloodSafeRealtime={FRESH10_MS,FRESH5_MS:FRESH10_MS,isLive:current,isRecent:current,isCurrent:current,isUpdatedWithin10m:current,isUpdatedWithin5m:current,hasObservation:current,hasRawObservation,stamp,ageMs,filterLive:a=>(Array.isArray(a)?a:[]).filter(current)};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',labels,{once:true});else labels();window.addEventListener('online',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('focus',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('fslanguage',labels);
})();