import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs';
window.maplibregl = maplibregl;
if(!window.__fsSmoothMapLoadingV11){
  window.__fsSmoothMapLoadingV11=true;
  import('./map-smooth-v3.js?v=11').then(()=>{
    window.__fsSmoothMapLoaded=true;
    return import('./hydro-smooth-v2.js?v=10');
  }).then(()=>{
    window.__fsHydroSmoothLoaded=true;
    return import('./map-core-v4.js?v=2');
  }).then(()=>{
    window.__fsMapCoreV4Loaded=true;
  }).catch((err)=>{
    window.__fsSmoothMapLoadingV11=false;
    console.error('FloodSafe map runtime failed',err);
    const hint=document.getElementById('mapHint');
    if(hint)hint.textContent='नक्सा लोड हुन सकेन — एकपटक reload गर्नुहोस्।';
  });
}
