(()=>{
'use strict';
if(window.__fsV24Realtime1s)return;window.__fsV24Realtime1s=true;
const API='https://bipadportal.gov.np/api/v1/';
const URLS=['river/?limit=650','rain-stations/?limit=650','alert/?limit=250&ordering=-createdOn','highway/?limit=500','river-stations/?limit=650','weather/?limit=100'];
const FAST=/(\/api\/v1\/(river\/|rain-stations\/|alert\/|highway\/|river-stations\/|weather\/))/i;
let ticking=false,lastFingerprint='';
function clearFastCache(){try{const c=window.__floodsafeScaleBridge?.cache;if(!c?.forEach)return;c.forEach((v,k)=>{if(FAST.test(String(k)))c.delete(k)});if(window.__floodsafeScaleBridge)window.__floodsafeScaleBridge.ttl_ms=1000}catch{}}
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return(h>>>0).toString(16)+':'+s.length}
async function probe(path){const r=await fetch(API+path,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',headers:{accept:'application/json'}});if(!r.ok)throw Error(r.status);const t=await r.text();return hash(t)}
async function tick(){if(ticking||document.hidden||!navigator.onLine)return;ticking=true;const feed=document.getElementById('feedState');try{clearFastCache();const r=await Promise.allSettled(URLS.map(probe)),ok=r.filter(x=>x.status==='fulfilled').length,fp=r.map(x=>x.status==='fulfilled'?x.value:'ERR').join('|');const changed=fp!==lastFingerprint;if(changed)lastFingerprint=fp;const c=document.getElementById('countdown');if(c)c.textContent='1';if(feed){feed.dataset.receiver='1-sec';feed.dataset.probe=ok+'/'+URLS.length}if(changed){const b=document.getElementById('refreshBtn');if(b&&typeof b.click==='function')b.click()}}catch{}finally{ticking=false}}
setInterval(tick,1000);setTimeout(tick,250);
})();
