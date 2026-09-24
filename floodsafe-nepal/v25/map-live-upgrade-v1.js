(()=>{'use strict';
if(window.__fsMapLiveUpgradeV1)return;window.__fsMapLiveUpgradeV1=true;
const NAMED=['==',['get','named'],true];
const ALERT=['in',['get','live_status'],['literal',['warning','danger']]];
const NAMED_ALERT=['all',NAMED,ALERT];
const STATUS_COLOR=['match',['get','live_status'],'danger','#ef2b2d','warning','#f97316','watch','#facc15','normal','#168BFF','#94a3b8'];
let bound=null,pulse=false,pulseTimer=0,radarTimer=0,radarRefresh=0,radarLayers=[];
const mapNow=()=>window.FloodSafeMap?.map||null;
function beforeRiver(map){for(const id of['hydro-complete-shadow','hydro-complete-lines','gauges-live-281','gauges'])if(map.getLayer(id))return id;return undefined}
function setFilter(map,id,filter){if(map.getLayer(id))try{map.setFilter(id,filter)}catch{}}
function namedOnly(map){
  for(const id of['hydro-complete-shadow','hydro-complete-lines','hydro-complete-live-flow','hydro-complete-status-glow','hydro-complete-hit'])setFilter(map,id,NAMED);
  setFilter(map,'hydro-complete-flood-pulse',NAMED_ALERT);
  if(map.getLayer('hydro-complete-selected'))setFilter(map,'hydro-complete-selected',['all',NAMED,['!=',['get','id'],'__none__']]);
}
function ensureGlow(map){
  if(!map.getSource('hydro-complete')||!map.isStyleLoaded?.())return;
  try{
    if(!map.getLayer('fs-named-river-alert-glow'))map.addLayer({id:'fs-named-river-alert-glow',type:'line',source:'hydro-complete',filter:NAMED_ALERT,paint:{'line-color':STATUS_COLOR,'line-width':['interpolate',['linear'],['zoom'],5,4.5,8,7,11,10,15,16],'line-opacity':.42,'line-blur':3.2}},beforeRiver(map));
    if(!map.getLayer('fs-named-river-alert-core'))map.addLayer({id:'fs-named-river-alert-core',type:'line',source:'hydro-complete',filter:NAMED_ALERT,paint:{'line-color':STATUS_COLOR,'line-width':['interpolate',['linear'],['zoom'],5,1.5,8,2.5,11,4,15,6.5],'line-opacity':.95,'line-dasharray':[1,1.6]}});
  }catch{}
}
function animateGlow(){clearInterval(pulseTimer);pulseTimer=setInterval(()=>{const map=mapNow();if(!map||document.hidden||!map.getLayer('fs-named-river-alert-glow'))return;pulse=!pulse;try{map.setPaintProperty('fs-named-river-alert-glow','line-opacity',pulse?.68:.34);map.setPaintProperty('fs-named-river-alert-glow','line-width',['interpolate',['linear'],['zoom'],5,pulse?5.5:4.2,8,pulse?8.5:6.5,11,pulse?12:9,15,pulse?18:14])}catch{}},950)}
function ensurePlaceLabels(map){
  if(!map.isStyleLoaded?.())return;
  try{
    if(!map.getSource('fs-place-labels'))map.addSource('fs-place-labels',{type:'raster',tiles:['https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'],tileSize:256,minzoom:4,maxzoom:19,attribution:'Esri, HERE, Garmin, OpenStreetMap contributors'});
    if(!map.getLayer('fs-place-labels'))map.addLayer({id:'fs-place-labels',type:'raster',source:'fs-place-labels',minzoom:5,paint:{'raster-opacity':['interpolate',['linear'],['zoom'],5,.58,8,.82,12,.95]}} ,beforeRiver(map));
  }catch{}
}
function clearRadar(map){
  for(const id of radarLayers){try{if(map.getLayer(id))map.removeLayer(id)}catch{}try{if(map.getSource(id))map.removeSource(id)}catch{}}
  radarLayers=[];
}
async function radarFrames(){
  const ctrl=new AbortController(),to=setTimeout(()=>ctrl.abort(),8000);
  try{const r=await fetch('https://api.rainviewer.com/public/weather-maps.json?_fs='+Date.now(),{cache:'no-store',signal:ctrl.signal});if(!r.ok)throw Error('radar '+r.status);const j=await r.json();const frames=Array.isArray(j?.radar?.past)?j.radar.past.slice(-6):[];if(!j?.host||!frames.length)throw Error('radar frames unavailable');return{host:j.host,frames}}finally{clearTimeout(to)}}
async function installRadar(map){
  try{
    const {host,frames}=await radarFrames();if(map!==mapNow()||!map.isStyleLoaded?.())return;
    clearRadar(map);
    for(let i=0;i<frames.length;i++){
      const id='fs-radar-'+i,path=frames[i].path;map.addSource(id,{type:'raster',tiles:[`${host}${path}/256/{z}/{x}/{y}/2/1_1.png`],tileSize:256,minzoom:0,maxzoom:7,attribution:'Weather radar: RainViewer'});map.addLayer({id,type:'raster',source:id,maxzoom:8,paint:{'raster-opacity':i===frames.length-1?.24:0,'raster-fade-duration':0}},beforeRiver(map));radarLayers.push(id)
    }
    let frame=Math.max(0,frames.length-1);clearInterval(radarTimer);radarTimer=setInterval(()=>{if(document.hidden||map!==mapNow())return;const next=(frame+1)%radarLayers.length;try{map.setPaintProperty(radarLayers[frame],'raster-opacity',0);map.setPaintProperty(radarLayers[next],'raster-opacity',.24);frame=next}catch{}},1200);
    window.__fsWeatherOverlayState={ok:true,kind:'precipitation-radar',frames:frames.length,latestTime:frames.at(-1)?.time||null,source:'RainViewer',checkedAt:new Date().toISOString()};
    window.dispatchEvent(new CustomEvent('fsweatheroverlay',{detail:window.__fsWeatherOverlayState}));
  }catch(e){window.__fsWeatherOverlayState={ok:false,kind:'precipitation-radar',error:String(e?.message||e),checkedAt:new Date().toISOString()};}
}
function bind(map){if(bound===map)return;bound=map;map.on?.('style.load',()=>setTimeout(apply,120));map.on?.('moveend',()=>setTimeout(apply,60));installRadar(map);clearInterval(radarRefresh);radarRefresh=setInterval(()=>{if(!document.hidden)installRadar(map)},10*60*1000)}
function apply(){const map=mapNow();if(!map||!map.isStyleLoaded?.())return false;bind(map);namedOnly(map);ensurePlaceLabels(map);ensureGlow(map);animateGlow();window.__fsNamedRiverMode={enabled:true,checkedAt:new Date().toISOString()};return true}
for(const ev of['fsmapready','fs281mapready','fsriverlinestatus','fsriverupdate','fstrustedriverupdate'])window.addEventListener(ev,()=>setTimeout(apply,80));
document.addEventListener('visibilitychange',()=>{if(!document.hidden){apply();const map=mapNow();if(map&&!radarLayers.length)installRadar(map)}});
let tries=0,t=setInterval(()=>{if(apply()||++tries>160)clearInterval(t)},180);
window.FloodSafeMapLiveUpgrade={apply,get namedOnly(){return true},get weatherOverlay(){return window.__fsWeatherOverlayState||null}};
})();
