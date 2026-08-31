(()=>{'use strict';
if(window.__fsRealtimeGuardV7)return;window.__fsRealtimeGuardV7=true;
const FRESH5_MS=5*60*1000,FUTURE_TOLERANCE_MS=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime'])}
function level(o){o=flat(o);const v=val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','_lastWaterLevel']),n=Number(v);return Number.isFinite(n)?n:null}
function ageMs(o){const t=+new Date(stamp(o)||0);return t?Date.now()-t:Infinity}
function hasObservation(o){return !!(+new Date(stamp(o)||0))&&level(o)!==null}
function updated5(o){const a=ageMs(o);return hasObservation(o)&&a>=-FUTURE_TOLERANCE_MS&&a<=FRESH5_MS}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'All official BIPAD/DHM stations • live sync • latest official status and observation time':'सबै official BIPAD/DHM station • live sync • latest official status र observation time';if(near)near.textContent=en?'Official gauges mirror the latest BIPAD/DHM reading; source is rechecked continuously':'Official gauge मा BIPAD/DHM को latest reading/status जस्ताको तस्तै • source लगातार recheck हुन्छ'}
window.FloodSafeRealtime={FRESH5_MS,isLive:hasObservation,isRecent:hasObservation,isUpdatedWithin5m:updated5,hasObservation,stamp,ageMs,filterLive:a=>(Array.isArray(a)?a:[]).filter(hasObservation)};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',labels,{once:true});else labels();window.addEventListener('online',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('focus',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('fslanguage',labels);
})();