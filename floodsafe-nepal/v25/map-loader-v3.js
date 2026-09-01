const hint=t=>{const e=document.getElementById('mapHint');if(e&&t)e.textContent=t};
function ensureCss(){if(document.querySelector('link[data-fs-maplibre-css]'))return;const l=document.createElement('link');l.rel='stylesheet';l.href='https://cdn.jsdelivr.net/npm/maplibre-gl@6.6.0/dist/maplibre-gl.css';l.media='print';l.dataset.fsMaplibreCss='1';l.onload=()=>{l.media='all'};document.head.appendChild(l)}
function loadScript(url,timeout=7000){return new Promise((resolve,reject)=>{const s=document.createElement('script');let done=false;const finish=(ok,e)=>{if(done)return;done=true;clearTimeout(to);s.onload=s.onerror=null;ok?resolve():reject(e||Error('map library failed'))};const to=setTimeout(()=>finish(false,Error('map library timeout')),timeout);s.src=url;s.async=true;s.crossOrigin='anonymous';s.onload=()=>finish(true);s.onerror=()=>finish(false,Error('map library network error'));document.head.appendChild(s)})}
async function ensureMapLibre(){ensureCss();if(window.maplibregl?.Map)return true;for(const url of['https://cdn.jsdelivr.net/npm/maplibre-gl@6.6.0/dist/maplibre-gl.js','https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.js']){try{await loadScript(url);if(window.maplibregl?.Map)return true}catch{}}try{const m=await import('https://cdn.jsdelivr.net/npm/maplibre-gl@6.6.0/dist/maplibre-gl.mjs');window.maplibregl=m;if(window.maplibregl?.Map)return true}catch{}try{const m=await import('https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs');window.maplibregl=m;if(window.maplibregl?.Map)return true}catch{}return false}
if(!window.__fsSmoothMapLoadingV17){
  window.__fsSmoothMapLoadingV17=true;
  (async()=>{
    try{
      hint('🇳🇵 नक्सा जोडिँदैछ…');
      if(!await ensureMapLibre())throw Error('MapLibre unavailable');
      await import('./map-smooth-v3.js?v=13');
      window.__fsSmoothMapLoaded=true;
      await import('./hydro-smooth-v2.js?v=11');
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
