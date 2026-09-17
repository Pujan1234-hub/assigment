(()=>{'use strict';
if(window.__fsRiverLineStyleV14)return;window.__fsRiverLineStyleV14=true;
const RIVER_BLUE='#168BFF';
const FRESH=['==',['get','live_updated_5m'],1];
const COLOR=RIVER_BLUE;
function add(map,source){if(!map?.getSource(source))return;try{
 if(!map.getLayer('hydro-complete-status-glow'))map.addLayer({id:'hydro-complete-status-glow',type:'line',source,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,3.6,8,5.4,11,8.2,16,13],'line-opacity':['case',FRESH,.30,.14],'line-blur':['case',FRESH,3,1.8]}});
 if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,1.1,8,1.8,11,3.1,16,5.6],'line-opacity':['case',FRESH,.96,.68],'line-blur':.08,'line-dasharray':[.25,2.4]}});
}catch(e){console.warn('FloodSafe river flow layer failed',e)}}
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.getSource('hydro-complete')||!map.getLayer('hydro-complete-lines'))return false;try{
 map.setPaintProperty('hydro-complete-lines','line-color',RIVER_BLUE);
 map.setPaintProperty('hydro-complete-lines','line-opacity',.88);
 map.setPaintProperty('hydro-complete-lines','line-width',['interpolate',['linear'],['zoom'],5,.8,8,1.35,11,2.5,16,4.9]);
 add(map,'hydro-complete');
 if(map.getLayer('hydro-complete-live-flow')){map.setFilter('hydro-complete-live-flow',null);map.setPaintProperty('hydro-complete-live-flow','line-color',RIVER_BLUE)}
 if(map.getLayer('hydro-complete-status-glow')){map.setFilter('hydro-complete-status-glow',null);map.setPaintProperty('hydro-complete-status-glow','line-color',RIVER_BLUE)}
 return true
}catch(e){console.warn('FloodSafe river blue apply failed',e);return false}}
const FLOW=[[.2,2.6],[.4,2.35],[.6,2.1],[.8,1.85],[1.0,1.6],[1.2,1.4],[1.0,1.6],[.8,1.85],[.6,2.1],[.4,2.35]];let frame=0,phase=false,anim=null;
function animate(){const map=window.FloodSafeMap?.map;if(!map||map.isMoving?.()||map.isZooming?.()||map.isRotating?.())return;frame=(frame+1)%FLOW.length;phase=!phase;try{
 if(map.getLayer('hydro-complete-live-flow')){map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW[frame]);map.setPaintProperty('hydro-complete-live-flow','line-opacity',['case',FRESH,phase?.98:.82,phase?.72:.54])}
 if(map.getLayer('hydro-complete-status-glow'))map.setPaintProperty('hydro-complete-status-glow','line-opacity',['case',FRESH,phase?.34:.22,phase?.20:.10]);
}catch{}}
function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},320)}
let timer=0;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{apply();start()},40)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fslanguage','fsmapready'])window.addEventListener(ev,schedule);
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){start();clearInterval(ready)}else if(tries>160)clearInterval(ready)},120);
window.FloodSafeRiverStyle={apply,COLOR:RIVER_BLUE,get dangerColor(){return RIVER_BLUE},get warningColor(){return RIVER_BLUE},get watchColor(){return RIVER_BLUE},get normalColor(){return RIVER_BLUE},get unknownColor(){return RIVER_BLUE}};
})();
