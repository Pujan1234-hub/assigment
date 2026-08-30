(()=>{'use strict';
if(window.__fsRealtimeGuardV2)return;window.__fsRealtimeGuardV2=true;
const MAX_AGE_MS=60*1000,FUTURE_TOLERANCE_MS=5*60*1000,POLL_MS=1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','updatedOn','updated_on','modifiedOn','modified_on','updated_at','updatedAt','retrievedAt','timestamp','date'])}
function live(o){const t=+new Date(stamp(o)||0),age=Date.now()-t;return !!t&&age>=-FUTURE_TOLERANCE_MS&&age<=MAX_AGE_MS}
function install(){const fs=window.FloodSafe,s=fs?.state;if(!s||s.__strictRealtime1m)return false;let store=Array.isArray(s.stations)?s.stations.filter(live):[];try{Object.defineProperty(s,'stations',{configurable:true,enumerable:true,get(){return store},set(v){store=(Array.isArray(v)?v:[]).filter(live)}});s.__strictRealtime1m=true}catch{return false}window.FloodSafeRealtime={MAX_AGE_MS,POLL_MS,isLive:live,stamp,filter:a=>(Array.isArray(a)?a:[]).filter(live)};return true}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'STRICT REALTIME • official readings ≤ 1 minute • source checked every second':'STRICT REALTIME • १ मिनेटभित्रको official reading मात्र • हरेक सेकेन्ड स्रोत जाँच';if(near)near.textContent=en?'DHM / BIPAD official realtime gauges • >1 minute readings excluded':'DHM / BIPAD official realtime gauge • १ मिनेटभन्दा पुरानो reading हटाइन्छ'}
let installed=false,tries=0,polling=false;
const t=setInterval(()=>{tries++;if(!installed)installed=install();if(installed||tries>100){clearInterval(t);labels()}},20);
setInterval(async()=>{const fs=window.FloodSafe;if(!fs?.poll||polling||document.hidden||!navigator.onLine)return;polling=true;try{await fs.poll()}catch{}finally{polling=false}},POLL_MS);
window.addEventListener('online',()=>window.FloodSafe?.poll?.());
window.addEventListener('focus',()=>window.FloodSafe?.poll?.());
window.addEventListener('fslanguage',labels);
})();