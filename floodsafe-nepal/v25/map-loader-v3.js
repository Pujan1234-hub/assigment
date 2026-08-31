import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs';

window.maplibregl = maplibregl;

if(!window.__fsStableMapLoading){
  window.__fsStableMapLoading=true;
  import('./map-stable-v2.js?v=5').then(()=>{
    window.__fsStableMapLoaded=true;
    return import('./hydro-complete-v1.js?v=4');
  }).then(()=>{
    window.__fsHydroCompleteLoaded=true;
    return import('./map-runtime-fix-v1.js?v=2');
  }).then(()=>{
    window.__fsMapRuntimeGuardLoaded=true;
  }).catch((err)=>{
    window.__fsStableMapLoading=false;
    console.error('FloodSafe stable map runtime failed', err);
    const hint=document.getElementById('mapHint');
    if(hint) hint.textContent='नक्सा runtime लोड हुन सकेन — फेरि reload गर्नुहोस्।';
  });
}