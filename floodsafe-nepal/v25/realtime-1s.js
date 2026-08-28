(()=>{
'use strict';
if(window.__fsRealtime1sV2)return;window.__fsRealtime1sV2=true;window.__fsRealtime1s=true;
const nativeFetch=window.fetch.bind(window),pending=new Map(),microCache=new Map(),TTL=5000;
function keyOf(input,init){try{const method=String(init?.method||input?.method||'GET').toUpperCase();if(method!=='GET')return'';const raw=String(input?.url||input||'');const u=new URL(raw,location.href);for(const k of ['_fs','t','_rt','_human','_district','_roadguard'])u.searchParams.delete(k);return method+' '+u.toString()}catch{return''}}
function responseOf(x,tag){return new Response(x.body,{status:x.status,statusText:x.statusText,headers:{...x.headers,'X-FloodSafe-Realtime':tag}})}
window.fetch=async function(input,init){const key=keyOf(input,init);if(!key)return nativeFetch(input,init);const now=Date.now(),hit=microCache.get(key);if(hit&&now-hit.at<TTL)return responseOf(hit,'COLLAPSED-CACHE');if(pending.has(key)){const x=await pending.get(key);return responseOf(x,'COLLAPSED-PENDING')}const p=(async()=>{const r=await nativeFetch(input,init),body=await r.clone().text(),headers={'Content-Type':r.headers.get('content-type')||'application/json'};const x={at:Date.now(),status:r.status,statusText:r.statusText,headers,body};if(r.ok)microCache.set(key,x);return x})().finally(()=>pending.delete(key));pending.set(key,p);const x=await p;return responseOf(x,'NETWORK')};
function npt(){try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date())+' NPT'}catch{return'—'}}
function tick(){for(const id of ['liveSourceState','appStatus']){const e=document.getElementById(id);if(!e)continue;e.dataset.receiver='ui-1-sec';e.dataset.heartbeat=String(Date.now())}const hb=document.getElementById('fsLiveHeartbeat');if(hb)hb.textContent=npt()}
setInterval(tick,1000);setTimeout(tick,150);
})();
