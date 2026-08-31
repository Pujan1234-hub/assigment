(()=>{'use strict';
if(window.__fsRealtimeGuardV6)return;window.__fsRealtimeGuardV6=true;
const CURRENT_MS=5*60*1000,FUTURE_TOLERANCE_MS=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime'])}
function ageMs(o){const t=+new Date(stamp(o)||0);return t?Date.now()-t:Infinity}
function current(o){const a=ageMs(o);return a>=-FUTURE_TOLERANCE_MS&&a<=CURRENT_MS}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'All official BIPAD/DHM stations shown • live/current only when official observation ≤5 minutes':'सबै official BIPAD/DHM station देखाइन्छ • official observation ≤५ मिनेट भए मात्र live/current';if(near)near.textContent=en?'All official gauges stay visible • readings older than 5 minutes are reference only':'सबै official gauge mapमा रहन्छन् • ५ मिनेटभन्दा पुरानो reading reference मात्र, live colour बदल्दैन'}
window.FloodSafeRealtime={CURRENT_MS,LIVE_MS:CURRENT_MS,RECENT_MS:CURRENT_MS,isLive:current,isRecent:current,stamp,ageMs,filterLive:a=>(Array.isArray(a)?a:[]).filter(current)};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',labels,{once:true});else labels();window.addEventListener('online',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('focus',()=>window.FloodSafeRiverRealtime?.refresh?.());window.addEventListener('fslanguage',labels);
})();