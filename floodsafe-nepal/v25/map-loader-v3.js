import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs';

window.maplibregl = maplibregl;

if(!window.__fsSmoothMapLoadingV4){
  window.__fsSmoothMapLoadingV4=true;
  import('./map-smooth-v3.js?v=2').then(()=>{
    window.__fsSmoothMapLoaded=true;
    return import('./hydro-smooth-v2.js?v=3');
  }).then(()=>{
    window.__fsHydroSmoothLoaded=true;
  }).catch((err)=>{
    window.__fsSmoothMapLoadingV4=false;
    console.error('FloodSafe smooth map runtime failed', err);
    const hint=document.getElementById('mapHint');
    if(hint) hint.textContent='नक्सा runtime लोड हुन सकेन — फेरि reload गर्नुहोस्।';
  });
}
