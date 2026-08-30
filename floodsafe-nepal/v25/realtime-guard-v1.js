(()=>{'use strict';
if(window.__fsRealtimeGuardV3)return;window.__fsRealtimeGuardV3=true;
const LIVE_MS=60*1000,RECENT_MS=24*60*60*1000,FUTURE_TOLERANCE_MS=5*60*1000,POLL_MS=1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','updatedOn','updated_on','modifiedOn','modified_on','updated_at','updatedAt','retrievedAt','timestamp','date'])}
function ageMs(o){const t=+new Date(stamp(o)||0);return t?Date.now()-t:Infinity}
function live(o){const a=ageMs(o);return a>=-FUTURE_TOLERANCE_MS&&a<=LIVE_MS}
function recent(o){const a=ageMs(o);return a>=-FUTURE_TOLERANCE_MS&&a<=RECENT_MS}
function install(){if(!window.FloodSafe)return false;window.FloodSafeRealtime={LIVE_MS,RECENT_MS,POLL_MS,isLive:live,isRecent:recent,stamp,ageMs,filterLive:a=>(Array.isArray(a)?a:[]).filter(live)};return true}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'Official DHM/BIPAD readings • LIVE badge only when ≤1 minute • otherwise latest official reading with age':'DHM/BIPAD आधिकारिक मापन • ≤१ मिनेट भए LIVE • नत्र पछिल्लो official reading र उमेर स्पष्ट';if(near)near.textContent=en?'Official gauges • source checked every second • old readings are never called LIVE':'आधिकारिक gauge • स्रोत हरेक सेकेन्ड जाँच • पुरानो reading लाई LIVE भनिँदैन'}
let ready=false,tries=0,busy=false;const boot=setInterval(()=>{tries++;if(!ready)ready=install();if(ready||tries>100){clearInterval(boot);labels()}},20);
setInterval(async()=>{const fs=window.FloodSafe;if(!fs?.poll||busy||document.hidden||!navigator.onLine)return;busy=true;try{await fs.poll()}catch{}finally{busy=false}},POLL_MS);
window.addEventListener('online',()=>window.FloodSafe?.poll?.());window.addEventListener('focus',()=>window.FloodSafe?.poll?.());window.addEventListener('fslanguage',labels);
})();