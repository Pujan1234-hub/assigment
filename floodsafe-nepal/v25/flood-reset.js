(()=>{'use strict';
if(window.__fsFloodResetV16)return;window.__fsFloodResetV16=true;
// A location dialog must only follow the user's "My Current Location" tap.
// This guard runs before the weather/map runtimes and blocks any startup GPS
// call left behind by an older runtime.
const geo=navigator.geolocation;
if(geo&&!window.__fsLocationConsentGate){
  window.__fsLocationConsentGate=true;
  let locationTapUntil=0;
  document.addEventListener('click',event=>{
    if(event.target?.closest?.('#locateBtn'))locationTapUntil=Date.now()+5000;
  },true);
  const deny=error=>{if(typeof error==='function')queueMicrotask(()=>error({code:1,message:'Tap My Current Location to allow GPS'}));};
  for(const name of ['getCurrentPosition','watchPosition']){
    const original=geo[name].bind(geo);
    Object.defineProperty(geo,name,{configurable:true,value(success,error,options){
      if(Date.now()>locationTapUntil){deny(error);return name==='watchPosition'?-1:undefined;}
      return original(success,error,options);
    }});
  }
}
try{
  if('serviceWorker'in navigator) navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>{const workers=[r.active,r.installing,r.waiting];if((r.scope||'').includes('/floodsafe-nepal/')&&!workers.some(w=>w&&new URL(w.scriptURL).pathname.endsWith('/rain-alert-sw.js')))r.unregister()}));
  if('caches'in window) caches.keys().then(ks=>ks.filter(k=>/floodsafe|v25|shell/i.test(k)).forEach(k=>caches.delete(k)));
}catch{}

async function recoverMap(){
  try{
    if(window.FloodSafeMap?.map || window.__fsSmoothMapLoadingV9 || window.__fsSmoothMapLoaded || window.__fsStableMapLoading) return;
    window.__fsStableMapLoading=true;
    if(!window.maplibregl){
      const mod=await import('https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs');
      window.maplibregl=mod;
    }
    if(window.FloodSafeMap?.map){window.__fsStableMapLoading=false;return}
    await import('./map-stable-v2.js?fallback=8');
    window.__fsStableMapLoaded=true;
  }catch(e){
    window.__fsStableMapLoading=false;
    console.error('FloodSafe map recovery failed',e);
    const hint=document.getElementById('mapHint');
    if(hint) hint.textContent='नक्सा लोड हुन सकेन — पेज फेरि खोल्नुहोस्।';
  }
}

setTimeout(()=>{
  if(!window.FloodSafeMap?.map && !window.__fsSmoothMapLoadingV9 && !window.__fsSmoothMapLoaded) recoverMap();
},10000);

let tries=0;
const timer=setInterval(()=>{
  tries++;
  try{
    const api=window.FloodSafeMap,m=api?.map;
    if(!m){if(tries>120)clearInterval(timer);return}
    if(!api?.initialized){if(tries>120)clearInterval(timer);return}
    api.set3D?.(false);
    m.stop?.();m.setPitch?.(0);m.setBearing?.(0);
    if(!window.FloodSafeCurrentLocation?.last)m.fitBounds?.([[80.0,26.2],[88.35,30.5]],{padding:window.innerWidth<620?16:34,pitch:0,bearing:0,duration:0});
    const hint=document.getElementById('mapHint');
    if(hint && api.districtCount>=70 && !window.FloodSafeHydroSmooth) hint.textContent=(window.FloodSafe?.state?.lang==='en')?'🇳🇵 Nepal • 77 districts • live river gauges':'🇳🇵 नेपाल • ७७ जिल्ला • प्रत्यक्ष नदी मापन केन्द्र';
    clearInterval(timer);
  }catch(e){if(tries>120)clearInterval(timer)}
},250);
})();
