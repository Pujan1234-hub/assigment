(()=>{'use strict';
if(window.__fsRealtimeGuardV1)return;window.__fsRealtimeGuardV1=true;
const MAX_AGE_MS=60*60*1000,FUTURE_TOLERANCE_MS=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function stamp(o){o=flat(o);return val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','updatedOn','updated_on','modifiedOn','modified_on','updated_at','updatedAt','retrievedAt','timestamp','date'])}
function live(o){const t=+new Date(stamp(o)||0),age=Date.now()-t;return !!t&&age>=-FUTURE_TOLERANCE_MS&&age<=MAX_AGE_MS}
function install(){const fs=window.FloodSafe,s=fs?.state;if(!s||s.__strictRealtime)return false;let store=Array.isArray(s.stations)?s.stations.filter(live):[];try{Object.defineProperty(s,'stations',{configurable:true,enumerable:true,get(){return store},set(v){store=(Array.isArray(v)?v:[]).filter(live)}});s.__strictRealtime=true}catch{return false}window.FloodSafeRealtime={MAX_AGE_MS,isLive:live,stamp,filter:a=>(Array.isArray(a)?a:[]).filter(live)};return true}
function labels(){const en=window.FloodSafe?.state?.lang==='en',sub=document.getElementById('riverStatusSub'),near=document.getElementById('nearSub');if(sub)sub.textContent=en?'Only official readings no older than 60 minutes • checked every 5 seconds':'६० मिनेटभन्दा पुरानो data नदेखाइने • official reading मात्र • हरेक ५ सेकेन्डमा जाँच';if(near)near.textContent=en?'DHM / BIPAD official live gauges • readings older than 60 minutes excluded':'DHM / BIPAD official live gauge • ६० मिनेटभन्दा पुरानो reading हटाइन्छ'}
let tries=0,t=setInterval(()=>{tries++;if(install()||tries>100){clearInterval(t);labels()}},20);
window.addEventListener('fslanguage',labels);
})();