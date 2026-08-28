(()=>{
'use strict';
if(window.__fsV24Realtime1sV2)return;window.__fsV24Realtime1sV2=true;window.__fsV24Realtime1s=true;
const API='https://bipadportal.gov.np/api/v1/',POLL_MS=15000;
const URLS=['river/?limit=650','rain-stations/?limit=650','alert/?limit=250&ordering=-createdOn','highway/?limit=500','river-stations/?limit=650','weather/?limit=100'];
const FAST=/(\/api\/v1\/(river\/|rain-stations\/|alert\/|highway\/|river-stations\/|weather\/))/i;
let ticking=false,lastFingerprint='',nextAt=0,lastGood=0;
function clearFastCache(){try{const c=window.__floodsafeScaleBridge?.cache;if(!c?.forEach)return;c.forEach((v,k)=>{if(FAST.test(String(k)))c.delete(k)});if(window.__floodsafeScaleBridge)window.__floodsafeScaleBridge.ttl_ms=5000}catch{}}
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(16)+':'+s.length}
async function probe(path){const c=new AbortController(),to=setTimeout(()=>c.abort(),6000);try{const r=await fetch(API+path,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',headers:{accept:'application/json'},signal:c.signal});if(!r.ok)throw Error(r.status);const t=await r.text();return hash(t)}finally{clearTimeout(to)}}
async function sourceTick(){if(ticking||document.hidden||!navigator.onLine)return;ticking=true;nextAt=Date.now()+POLL_MS;const feed=document.getElementById('feedState');try{clearFastCache();const r=await Promise.allSettled(URLS.map(probe)),ok=r.filter(x=>x.status==='fulfilled').length,fp=r.map(x=>x.status==='fulfilled'?x.value:'ERR').join('|');const changed=fp!==lastFingerprint;if(changed)lastFingerprint=fp;if(ok)lastGood=Date.now();if(feed){feed.dataset.receiver='15-sec-source';feed.dataset.probe=ok+'/'+URLS.length}if(changed&&lastGood){const b=document.getElementById('refreshBtn');if(b&&typeof b.click==='function')b.click()}}catch{}finally{ticking=false}}
function uiTick(){const c=document.getElementById('countdown'),feed=document.getElementById('feedState'),left=Math.max(0,Math.ceil((nextAt-Date.now())/1000));if(c)c.textContent=String(left);if(feed){feed.dataset.uiHeartbeat='1-sec';feed.dataset.lastGood=String(lastGood||'')}}
setInterval(uiTick,1000);setInterval(sourceTick,POLL_MS);setTimeout(()=>{sourceTick();uiTick()},250);document.addEventListener('visibilitychange',()=>{if(!document.hidden)sourceTick()});window.addEventListener('online',sourceTick);
})();