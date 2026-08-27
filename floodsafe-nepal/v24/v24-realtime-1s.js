(()=>{
'use strict';
if(window.__fsV24Realtime1s)return;window.__fsV24Realtime1s=true;
const FAST=/(\/api\/v1\/(river\/|rain-stations\/|alert\/|highway\/|river-stations\/|weather\/))/i;
let ticking=false;
function clearFastCache(){try{const c=window.__floodsafeScaleBridge?.cache;if(!c?.forEach)return;c.forEach((v,k)=>{if(FAST.test(String(k)))c.delete(k)});if(window.__floodsafeScaleBridge)window.__floodsafeScaleBridge.ttl_ms=1000}catch{}}
async function tick(){if(ticking||document.hidden||!navigator.onLine)return;const feed=document.getElementById('feedState');if(feed&&/अपडेट हुँदैछ|updating/i.test(feed.textContent||''))return;ticking=true;try{clearFastCache();const b=document.getElementById('refreshBtn');if(b&&typeof b.click==='function')b.click();const c=document.getElementById('countdown');if(c)c.textContent='1';if(feed)feed.dataset.receiver='1-sec'}finally{setTimeout(()=>{ticking=false},850)}}
setInterval(tick,1000);setTimeout(tick,250);
})();
