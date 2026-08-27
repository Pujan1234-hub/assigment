(()=>{
'use strict';
if(window.__fsRealtime1s)return;window.__fsRealtime1s=true;
const nativeFetch=window.fetch.bind(window),pending=new Map(),microCache=new Map(),TTL=850;
function keyOf(input,init){try{const method=String(init?.method||input?.method||'GET').toUpperCase();if(method!=='GET')return'';const raw=String(input?.url||input||'');const u=new URL(raw,location.href);for(const k of ['_fs','t','_rt'])u.searchParams.delete(k);return method+' '+u.toString()}catch{return''}}
function responseOf(x,tag){return new Response(x.body,{status:x.status,statusText:x.statusText,headers:{...x.headers,'X-FloodSafe-Realtime':tag}})}
window.fetch=async function(input,init){const key=keyOf(input,init);if(!key)return nativeFetch(input,init);const now=Date.now(),hit=microCache.get(key);if(hit&&now-hit.at<TTL)return responseOf(hit,'1S-HIT');if(pending.has(key)){const x=await pending.get(key);return responseOf(x,'1S-COLLAPSED')}const p=(async()=>{const r=await nativeFetch(input,init),body=await r.clone().text(),headers={'Content-Type':r.headers.get('content-type')||'application/json'};const x={at:Date.now(),status:r.status,statusText:r.statusText,headers,body};if(r.ok)microCache.set(key,x);return x})().finally(()=>pending.delete(key));pending.set(key,p);const x=await p;return responseOf(x,'1S-NET')};
function label(){for(const id of ['appStatus','todayHazardsFresh','closedRoadFresh']){const e=document.getElementById(id);if(!e)continue;e.textContent=String(e.textContent||'').replace(/५\s*sec|5\s*sec|५\s*से\.?|5\s*से\.?/gi,'१ sec')}const s=document.getElementById('liveSourceState');if(s&&s.textContent&&!/1-sec/.test(s.textContent))s.dataset.receiver='1-sec'}
function tick(){if(document.hidden||!navigator.onLine)return;try{window.dispatchEvent(new Event('online'));document.dispatchEvent(new Event('visibilitychange'));setTimeout(label,80)}catch{}}
setInterval(tick,1000);setTimeout(tick,150);
})();
