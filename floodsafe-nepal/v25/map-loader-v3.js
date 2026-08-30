import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.6.0/dist/maplibre-gl.mjs';

window.maplibregl = maplibregl;

import('./map-stable-v2.js?v=3').catch((err)=>{
  console.error('FloodSafe stable map runtime failed', err);
  const hint=document.getElementById('mapHint');
  if(hint) hint.textContent='नक्सा runtime लोड हुन सकेन — फेरि reload गर्नुहोस्।';
});
