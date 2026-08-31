import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs';

window.maplibregl = maplibregl;

if(!window.__fsSmoothMapLoadingV8){
  window.__fsSmoothMapLoadingV8=true;
  import('./map-smooth-v3.js?v=6').then(()=>{
    window.__fsSmoothMapLoaded=true;
    return import('./hydro-smooth-v2.js?v=7');
  }).then(()=>{
    window.__fsHydroSmoothLoaded=true;
  }).catch((err)=>{
    window.__fsSmoothMapLoadingV8=false;
    console.error('FloodSafe smooth map runtime failed', err);
    const hint=document.getElementById('mapHint');
    if(hint) hint.textContent='नक्सा runtime लोड हुन सकेन — फेरि reload गर्नुहोस्।';
  });
}
