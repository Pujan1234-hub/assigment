const hint=t=>{const e=document.getElementById('mapHint');if(e&&t)e.textContent=t};
function ensureCss(){if(document.querySelector('link[data-fs-maplibre-css]'))return;const l=document.createElement('link');l.rel='stylesheet';l.href='https://cdn.jsdelivr.net/npm/maplibre-gl@6.6.0/dist/maplibre-gl.css';l.media='print';l.dataset.fsMaplibreCss='1';l.onload=()=>{l.media='all'};document.head.appendChild(l)}
async function ensureMapLibre(){
  ensureCss();if(window.maplibregl?.Map)return true;
  if(window.__fsMapLibreModulePromise)return window.__fsMapLibreModulePromise;
  window.__fsMapLibreModulePromise=(async()=>{
    for(const url of ['https://cdn.jsdelivr.net/npm/maplibre-gl@6.6.0/dist/maplibre-gl.mjs','https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs']){
      let timer;try{const m=await Promise.race([import(url),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Map module timeout')),7000)})]);if(m?.Map){window.maplibregl=m;return true}}catch{}finally{clearTimeout(timer)}
    }return false;
  })();
  const ok=await window.__fsMapLibreModulePromise;if(!ok)window.__fsMapLibreModulePromise=null;return ok;
}
window.FloodSafeEnsureMapLibre=ensureMapLibre;
if(!window.__fsSmoothMapLoadingV17){
  window.__fsSmoothMapLoadingV17=true;
  (async()=>{
    try{
      hint('🇳🇵 नक्सा जोडिँदैछ…');
      if(!await ensureMapLibre())throw Error('MapLibre unavailable');
      await import('./map-smooth-v3.js?v=13');
      window.__fsSmoothMapLoaded=true;
      await import('./hydro-smooth-v2.js?v=13');
      window.__fsHydroSmoothLoaded=true;
      await import('./map-core-v4.js?v=9');
      window.__fsMapCoreV4Loaded=true;
      await import('./river-rain-fallback-v1.js?v=2').catch(()=>{});
      window.__fsRiverRainFallbackLoaded=true;
    }catch(err){
      window.__fsSmoothMapLoadingV17=false;
      console.error('FloodSafe map runtime failed',err);
      hint('नक्सा जोडिँदैछ…');
      window.dispatchEvent(new CustomEvent('fsmaploadfailed',{detail:{message:String(err?.message||err)}}));
    }
  })();
}
