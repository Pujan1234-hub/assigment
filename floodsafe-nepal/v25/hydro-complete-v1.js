(()=>{
'use strict';
if(window.__fsHydroCompleteV3)return;window.__fsHydroCompleteV3=true;

const MANIFEST='../../data/nepal-waterways-tiles/manifest.json';
const OVERVIEW='../../data/nepal-waterways-tiles/overview.json';
const TILE_BASE='../../data/nepal-waterways-tiles/';
const RAW_BASE='https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/nepal-waterways-tiles/';
const CACHE=new Map();
const PENDING=new Map();
let manifest=null,overview=null,overviewP=null,map=null,started=false,renderTimer=0,lastZoom=-1;
const LOCAL_ZOOM=6.9;
const lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne';
const tr=(ne,en)=>lang()==='en'?en:ne;

async function getJSON(url,timeout=12000){
  const c=new AbortController(),t=setTimeout(()=>c.abort(),timeout);
  try{const r=await fetch(url+(url.includes('?')?'&':'?')+'hc='+Date.now(),{cache:'no-store',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}
}
async function loadManifest(){
  if(manifest)return manifest;
  try{manifest=await getJSON(MANIFEST,9000)}catch{manifest=await getJSON(RAW_BASE+'manifest.json',12000)}
  return manifest;
}
async function loadOverview(){
  if(overview)return overview;if(overviewP)return overviewP;
  overviewP=(async()=>{let j=null;try{j=await getJSON(OVERVIEW,12000)}catch{try{j=await getJSON(RAW_BASE+'overview.json',16000)}catch{j=null}}overviewP=null;if(j?.waterways?.length){overview=j;return j}return null})();
  return overviewP;
}
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
function tileRange(bounds,m){
  const w=bounds.getWest()-0.12,e=bounds.getEast()+0.12,s=bounds.getSouth()-0.10,n=bounds.getNorth()+0.10;
  const x0=clamp(Math.floor((w-m.minLon)/m.stepLon),0,m.nx-1),x1=clamp(Math.floor((e-m.minLon)/m.stepLon),0,m.nx-1);
  const y0=clamp(Math.floor((s-m.minLat)/m.stepLat),0,m.ny-1),y1=clamp(Math.floor((n-m.minLat)/m.stepLat),0,m.ny-1);
  const out=[];for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){const k=`${x}-${y}`;if(m.tiles?.[k])out.push(k)}return out;
}
function sourceName(w){return String(lang()==='en'?(w.name_en||w.name||w.name_ne||''):(w.name_ne||w.name||w.name_en||''))}
function feature(w){
  const id=String(w.id||`${w.type||'stream'}|${w.pts?.[0]||''}|${w.pts?.[w.pts.length-1]||''}`);
  return{type:'Feature',geometry:{type:'LineString',coordinates:w.pts},properties:{
    id,key:'hydro:'+id,name:sourceName(w),name_raw:String(w.name||''),name_ne:String(w.name_ne||''),name_en:String(w.name_en||''),
    type:w.type||'stream',named:!!(w.name||w.name_en||w.name_ne),geometry_source:'OpenStreetMap via Overpass',license:'ODbL'
  }};
}
function fcFrom(list){
  const seen=new Set(),features=[];
  for(const w of list||[]){if(!Array.isArray(w?.pts)||w.pts.length<2)continue;const id=String(w.id||`${w.type}|${w.pts?.[0]}|${w.pts?.[w.pts.length-1]}`);if(seen.has(id))continue;seen.add(id);features.push(feature(w))}
  return{type:'FeatureCollection',features};
}
function fcForTiles(keys){
  const seen=new Set(),features=[];
  for(const k of keys){for(const w of CACHE.get(k)||[]){if(!Array.isArray(w?.pts)||w.pts.length<2)continue;const id=String(w.id||`${w.type}|${w.pts?.[0]}|${w.pts?.[w.pts.length-1]}`);if(seen.has(id))continue;seen.add(id);features.push(feature(w))}}
  return{type:'FeatureCollection',features};
}
function ensureLayers(){
  if(!map||!map.isStyleLoaded())return false;
  if(!map.getSource('hydro-complete'))map.addSource('hydro-complete',{type:'geojson',data:{type:'FeatureCollection',features:[]},promoteId:'id'});
  if(!map.getLayer('hydro-complete-shadow'))map.addLayer({id:'hydro-complete-shadow',type:'line',source:'hydro-complete',paint:{'line-color':'#003847','line-width':['interpolate',['linear'],['zoom'],5,1.0,8,1.7,11,3.0,15,5.0],'line-opacity':['interpolate',['linear'],['zoom'],5,0.46,7,0.56,10,0.68,15,0.76]}});
  if(!map.getLayer('hydro-complete-lines'))map.addLayer({id:'hydro-complete-lines',type:'line',source:'hydro-complete',paint:{'line-color':['match',['get','type'],'river','#18dff5','#52d9ef'],'line-width':['interpolate',['linear'],['zoom'],5,0.55,7,0.85,10,1.55,13,2.5,16,3.8],'line-opacity':['interpolate',['linear'],['zoom'],5,0.78,7,0.86,10,0.92,15,0.96]}});
  if(!map.getLayer('hydro-complete-labels'))map.addLayer({id:'hydro-complete-labels',type:'symbol',source:'hydro-complete',minzoom:5.7,filter:['==',['get','named'],true],layout:{'symbol-placement':'line','text-field':['get','name'],'text-size':['interpolate',['linear'],['zoom'],5.7,8,10,10.5,14,12.5],'symbol-spacing':360,'text-allow-overlap':false,'text-ignore-placement':false},paint:{'text-color':'#eaffff','text-halo-color':'#062f38','text-halo-width':1.4,'text-halo-blur':0.5}});
  if(!map.getLayer('hydro-complete-hit'))map.addLayer({id:'hydro-complete-hit',type:'line',source:'hydro-complete',paint:{'line-color':'rgba(0,0,0,0)','line-width':['interpolate',['linear'],['zoom'],5,7,10,12,16,18]}});
  try{if(map.getLayer('river-shadow'))map.setPaintProperty('river-shadow','line-opacity',0.12);if(map.getLayer('river-base'))map.setPaintProperty('river-base','line-opacity',0.14)}catch{}
  return true;
}
function setData(fc){if(!ensureLayers())return;map.getSource('hydro-complete')?.setData(fc);lastZoom=map.getZoom()}
function overviewStatus(fc){const h=document.getElementById('mapHint');if(!h)return;const source=overview?.source||manifest?.source||'OpenStreetMap via Overpass',all=manifest?.count||overview?.source_count||'';h.textContent=tr(`🇳🇵 ७७ जिल्ला • ${fc.features.length.toLocaleString()} देशव्यापी नदी/खोला • स्रोत ${source}${all?` • पूर्ण स्रोत ${Number(all).toLocaleString()}`:''} • zoom गर्दा सबै स्थानीय खोला खुल्छन्`,`🇳🇵 77 districts • ${fc.features.length.toLocaleString()} nationwide rivers/streams • ${source}${all?` • ${Number(all).toLocaleString()} in full source`:''} • zoom in for all local waterways`)}
function tileStatus(keys,fc){const h=document.getElementById('mapHint');if(!h)return;const loaded=keys.filter(k=>CACHE.has(k)).length,total=keys.length;h.textContent=tr(`📍 स्थानीय विस्तृत नक्सा • ${fc.features.length.toLocaleString()} स्रोत नदी/खोला • ${loaded}/${total} भाग लोड • OpenStreetMap via Overpass`,`📍 Detailed local map • ${fc.features.length.toLocaleString()} source rivers/streams • ${loaded}/${total} tiles loaded • OpenStreetMap via Overpass`)}
async function renderOverview(){const j=await loadOverview();if(!j?.waterways?.length)return false;const fc=fcFrom(j.waterways);setData(fc);overviewStatus(fc);return true}
function renderTiles(keys){const fc=fcForTiles(keys);setData(fc);tileStatus(keys,fc);return fc}
async function loadTile(k){
  if(CACHE.has(k))return CACHE.get(k);if(PENDING.has(k))return PENDING.get(k);
  const p=(async()=>{let j=null;try{j=await getJSON(TILE_BASE+k+'.json',14000)}catch{try{j=await getJSON(RAW_BASE+k+'.json',18000)}catch{j=null}}const a=Array.isArray(j?.waterways)?j.waterways:[];CACHE.set(k,a);PENDING.delete(k);return a})();PENDING.set(k,p);return p;
}
async function refresh(){
  if(!map||!map.isStyleLoaded())return;await loadManifest();const z=map.getZoom();
  if(z<LOCAL_ZOOM){const ok=await renderOverview();if(!ok){const h=document.getElementById('mapHint');if(h)h.textContent=tr('देशव्यापी नदी नक्सा तयार हुँदैछ…','Nationwide river overview is being prepared…')}return}
  const keys=tileRange(map.getBounds(),manifest),ready=keys.some(k=>CACHE.has(k));if(ready)renderTiles(keys);else await renderOverview();
  const missing=keys.filter(k=>!CACHE.has(k));let i=0;
  const workers=Array.from({length:Math.min(5,missing.length)},async()=>{while(i<missing.length){const k=missing[i++];await loadTile(k);clearTimeout(renderTimer);renderTimer=setTimeout(()=>renderTiles(keys),90)}});
  await Promise.all(workers);renderTiles(keys);
}
function boot(){
  if(started)return;const f=window.FloodSafeMap,m=f?.map;if(!m){setTimeout(boot,120);return}map=m;started=true;
  const go=()=>{refresh().catch(e=>console.warn('FloodSafe complete hydrography failed',e))};
  if(map.loaded())go();else map.once('load',go);
  map.on('moveend',go);map.on('zoomend',()=>{if(Math.abs(map.getZoom()-lastZoom)>0.18)go()});
  window.addEventListener('fslanguage',go);
  window.FloodSafeHydroComplete={refresh,get loadedTiles(){return CACHE.size},get overviewCount(){return overview?.waterways?.length||0},get manifest(){return manifest},get localZoom(){return LOCAL_ZOOM}};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();