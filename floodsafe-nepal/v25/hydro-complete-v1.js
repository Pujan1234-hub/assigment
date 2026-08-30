(()=>{
'use strict';
if(window.__fsHydroCompleteV2)return;window.__fsHydroCompleteV2=true;

const MANIFEST='../../data/nepal-waterways-tiles/manifest.json';
const TILE_BASE='../../data/nepal-waterways-tiles/';
const RAW_BASE='https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/nepal-waterways-tiles/';
const CACHE=new Map();
const PENDING=new Map();
let manifest=null,map=null,started=false,renderTimer=0,lastZoom=-1;
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
function clamp(n,a,b){return Math.max(a,Math.min(b,n))}
function tileRange(bounds,m){
  const w=bounds.getWest()-0.12,e=bounds.getEast()+0.12,s=bounds.getSouth()-0.10,n=bounds.getNorth()+0.10;
  const x0=clamp(Math.floor((w-m.minLon)/m.stepLon),0,m.nx-1),x1=clamp(Math.floor((e-m.minLon)/m.stepLon),0,m.nx-1);
  const y0=clamp(Math.floor((s-m.minLat)/m.stepLat),0,m.ny-1),y1=clamp(Math.floor((n-m.minLat)/m.stepLat),0,m.ny-1);
  const out=[];for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){const k=`${x}-${y}`;if(m.tiles?.[k])out.push(k)}return out;
}
function score(w){const named=!!(w?.name||w?.name_en||w?.name_ne),pts=w?.pts?.length||0;return (w?.type==='river'?500:0)+(named?260:0)+Math.min(220,pts*3)}
function keepForZoom(w,z){
  if(!Array.isArray(w?.pts)||w.pts.length<2)return false;
  const named=!!(w.name||w.name_en||w.name_ne);
  if(z<5.8)return w.type==='river'||named||w.pts.length>=34;
  if(z<7.2)return w.type==='river'||named||w.pts.length>=18;
  if(z<8.8)return w.type==='river'||named||w.pts.length>=8;
  return true;
}
function sourceName(w){return String(lang()==='en'?(w.name_en||w.name||w.name_ne||''):(w.name_ne||w.name||w.name_en||''))}
function feature(w){
  const id=String(w.id||`${w.type||'stream'}|${w.pts?.[0]||''}|${w.pts?.[w.pts.length-1]||''}`);
  return{type:'Feature',geometry:{type:'LineString',coordinates:w.pts},properties:{
    id,key:'hydro:'+id,name:sourceName(w),name_raw:String(w.name||''),name_ne:String(w.name_ne||''),name_en:String(w.name_en||''),
    type:w.type||'stream',named:!!(w.name||w.name_en||w.name_ne),geometry_source:'OpenStreetMap via Overpass',license:'ODbL'
  }};
}
function fcFor(keys,z){
  const seen=new Set(),features=[];
  for(const k of keys){const a=CACHE.get(k)||[];let list=a;
    if(z<6.2&&a.length>450)list=[...a].sort((x,y)=>score(y)-score(x)).slice(0,450);
    else if(z<7.4&&a.length>900)list=[...a].sort((x,y)=>score(y)-score(x)).slice(0,900);
    for(const w of list){if(!keepForZoom(w,z))continue;const id=String(w.id||`${w.type}|${w.pts?.[0]}|${w.pts?.[w.pts.length-1]}`);if(seen.has(id))continue;seen.add(id);features.push(feature(w))}
  }
  return{type:'FeatureCollection',features};
}
function ensureLayers(){
  if(!map||!map.isStyleLoaded())return false;
  if(!map.getSource('hydro-complete'))map.addSource('hydro-complete',{type:'geojson',data:{type:'FeatureCollection',features:[]},promoteId:'id'});
  if(!map.getLayer('hydro-complete-shadow'))map.addLayer({id:'hydro-complete-shadow',type:'line',source:'hydro-complete',paint:{'line-color':'#003847','line-width':['interpolate',['linear'],['zoom'],5,1.0,8,1.7,11,3.0,15,5.0],'line-opacity':['interpolate',['linear'],['zoom'],5,0.46,7,0.56,10,0.68,15,0.76]}});
  if(!map.getLayer('hydro-complete-lines'))map.addLayer({id:'hydro-complete-lines',type:'line',source:'hydro-complete',paint:{'line-color':['match',['get','type'],'river','#18dff5','#52d9ef'],'line-width':['interpolate',['linear'],['zoom'],5,0.55,7,0.85,10,1.55,13,2.5,16,3.8],'line-opacity':['interpolate',['linear'],['zoom'],5,0.78,7,0.86,10,0.92,15,0.96]}});
  if(!map.getLayer('hydro-complete-labels'))map.addLayer({id:'hydro-complete-labels',type:'symbol',source:'hydro-complete',minzoom:6.2,filter:['==',['get','named'],true],layout:{'symbol-placement':'line','text-field':['get','name'],'text-size':['interpolate',['linear'],['zoom'],6.2,8,10,10.5,14,12.5],'symbol-spacing':360,'text-allow-overlap':false,'text-ignore-placement':false},paint:{'text-color':'#eaffff','text-halo-color':'#062f38','text-halo-width':1.4,'text-halo-blur':0.5}});
  if(!map.getLayer('hydro-complete-hit'))map.addLayer({id:'hydro-complete-hit',type:'line',source:'hydro-complete',paint:{'line-color':'rgba(0,0,0,0)','line-width':['interpolate',['linear'],['zoom'],5,7,10,12,16,18]}});
  try{if(map.getLayer('river-shadow'))map.setPaintProperty('river-shadow','line-opacity',0.16);if(map.getLayer('river-base'))map.setPaintProperty('river-base','line-opacity',0.18)}catch{}
  return true;
}
function statusText(keys,fc){
  const h=document.getElementById('mapHint');if(!h)return;
  const loaded=keys.filter(k=>CACHE.has(k)).length,total=keys.length;
  const src=manifest?.source||'OpenStreetMap via Overpass';
  h.textContent=tr(`🇳🇵 ७७ जिल्ला • ${fc.features.length.toLocaleString()} नदी/खोला • ${loaded}/${total} जल-नक्सा भाग • ${src}`,`🇳🇵 77 districts • ${fc.features.length.toLocaleString()} rivers/streams • ${loaded}/${total} hydro tiles • ${src}`);
}
function render(keys){
  if(!ensureLayers())return;
  const z=map.getZoom(),fc=fcFor(keys,z),src=map.getSource('hydro-complete');if(src)src.setData(fc);lastZoom=z;statusText(keys,fc);
}
async function loadTile(k){
  if(CACHE.has(k))return CACHE.get(k);if(PENDING.has(k))return PENDING.get(k);
  const p=(async()=>{let j=null;try{j=await getJSON(TILE_BASE+k+'.json',14000)}catch{try{j=await getJSON(RAW_BASE+k+'.json',18000)}catch{j=null}}const a=Array.isArray(j?.waterways)?j.waterways:[];CACHE.set(k,a);PENDING.delete(k);return a})();PENDING.set(k,p);return p;
}
async function refresh(){
  if(!map||!map.isStyleLoaded())return;const m=await loadManifest();const keys=tileRange(map.getBounds(),m);render(keys);
  const missing=keys.filter(k=>!CACHE.has(k));let i=0;
  const workers=Array.from({length:Math.min(6,missing.length)},async()=>{while(i<missing.length){const k=missing[i++];await loadTile(k);clearTimeout(renderTimer);renderTimer=setTimeout(()=>render(keys),80)}});
  await Promise.all(workers);render(keys);
}
function boot(){
  if(started)return;const f=window.FloodSafeMap,m=f?.map;if(!m){setTimeout(boot,120);return}map=m;started=true;
  const go=()=>{refresh().catch(e=>console.warn('FloodSafe complete hydrography failed',e))};
  if(map.loaded())go();else map.once('load',go);
  map.on('moveend',go);map.on('zoomend',()=>{if(Math.abs(map.getZoom()-lastZoom)>0.18)go()});
  window.addEventListener('fslanguage',()=>{if(manifest)go()});
  window.FloodSafeHydroComplete={refresh,get loadedTiles(){return CACHE.size},get manifest(){return manifest}};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();