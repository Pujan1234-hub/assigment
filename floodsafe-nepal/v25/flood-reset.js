(()=>{'use strict';
try{
  if('serviceWorker'in navigator) navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>{if((r.scope||'').includes('/floodsafe-nepal/'))r.unregister()}));
  if('caches'in window) caches.keys().then(ks=>ks.filter(k=>/floodsafe|v25|shell/i.test(k)).forEach(k=>caches.delete(k)));
}catch{}

async function recoverMap(){
  try{
    if(!window.maplibregl){
      const mod=await import('https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs');
      window.maplibregl=mod;
    }
    const api=window.FloodSafeMap;
    if(api?.map && api?.initialized) return;
    await import('./map-stable-v2.js?fallback=4');
  }catch(e){
    console.error('FloodSafe map recovery failed',e);
    const hint=document.getElementById('mapHint');
    if(hint) hint.textContent='नक्सा लोड हुन सकेन — पेज फेरि खोल्नुहोस्।';
  }
}

setTimeout(()=>{
  const api=window.FloodSafeMap;
  if(!api?.map || !api?.initialized) recoverMap();
},700);

let tries=0;
const timer=setInterval(()=>{
  tries++;
  try{
    const api=window.FloodSafeMap,m=api?.map;
    if(!m){if(tries>100)clearInterval(timer);return}
    if(!api?.initialized){if(tries>100)clearInterval(timer);return}
    api.set3D?.(false);
    m.stop?.();m.setPitch?.(0);m.setBearing?.(0);
    m.fitBounds?.([[80.0,26.2],[88.35,30.5]],{padding:window.innerWidth<620?16:34,pitch:0,bearing:0,duration:0});
    const hint=document.getElementById('mapHint');
    if(hint && api.districtCount>=70) hint.textContent=(window.FloodSafe?.state?.lang==='en')?'🇳🇵 Nepal • 77 districts • live river gauges':'🇳🇵 नेपाल • ७७ जिल्ला • प्रत्यक्ष नदी मापन केन्द्र';
    clearInterval(timer);
  }catch(e){if(tries>100)clearInterval(timer)}
},250);
})();