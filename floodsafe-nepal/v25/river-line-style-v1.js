(()=>{'use strict';
if(window.__fsRiverLineStyleV16)return;window.__fsRiverLineStyleV16=true;
const RIVER_BLUE='#168BFF';
const FRESH=['==',['get','live_updated_5m'],1];
const FLOW_MIN_ZOOM=5.0;
const hw=Number(navigator.hardwareConcurrency||0),mem=Number(navigator.deviceMemory||0);
const LOW_POWER=(hw>0&&hw<=4)||(mem>0&&mem<=4);
const FLOW=[[.22,2.7],[.48,2.42],[.76,2.12],[1.05,1.82],[1.34,1.54],[1.05,1.82],[.76,2.12],[.48,2.42]];
let frame=0,animTimer=0,applyTimer=0,boundMap=null;
function mapNow(){return window.FloodSafeMap?.map||null}
function add(map,source){if(!map?.getSource(source))return false;try{
 if(!map.getLayer('hydro-complete-status-glow'))map.addLayer({id:'hydro-complete-status-glow',type:'line',source,minzoom:FLOW_MIN_ZOOM,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,1.7,7,2.8,9,5.4,12,8.4,16,12],'line-opacity':['case',FRESH,.22,.08],'line-blur':['case',FRESH,2,1]}});
 if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,minzoom:FLOW_MIN_ZOOM,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,.55,7,.9,9,1.7,12,3.1,16,5.4],'line-opacity':['case',FRESH,.90,.58],'line-blur':0,'line-dasharray':FLOW[0]}});
 return true
 }catch(e){console.warn('FloodSafe river flow layer failed',e);return false}}
function setIfDifferent(map,id,prop,value){try{const cur=map.getPaintProperty(id,prop);if(typeof value==='string'&&cur===value)return;map.setPaintProperty(id,prop,value)}catch{}}
function apply(){const map=mapNow();if(!map||!map.getSource('hydro-complete')||!map.getLayer('hydro-complete-lines'))return false;try{
 setIfDifferent(map,'hydro-complete-lines','line-color',RIVER_BLUE);
 if(!map.getLayer('hydro-complete-live-flow')||!map.getLayer('hydro-complete-status-glow'))add(map,'hydro-complete');
 if(map.getLayer('hydro-complete-live-flow'))setIfDifferent(map,'hydro-complete-live-flow','line-color',RIVER_BLUE);
 if(map.getLayer('hydro-complete-status-glow'))setIfDifferent(map,'hydro-complete-status-glow','line-color',RIVER_BLUE);
 bindMap(map);return true
 }catch(e){console.warn('FloodSafe river style apply failed',e);return false}}
function cadence(map){const z=map?.getZoom?.()||0;if(LOW_POWER){if(z<7)return 1400;if(z<8.5)return 980;return 760}if(z<7)return 1100;if(z<8.5)return 720;return 520}
function canAnimate(map){return !!map&&!document.hidden&&!map.isMoving?.()&&!map.isZooming?.()&&!map.isRotating?.()&&(map.getZoom?.()||0)>=FLOW_MIN_ZOOM&&map.getLayer?.('hydro-complete-live-flow')}
function animateOnce(){animTimer=0;const map=mapNow();if(!canAnimate(map)){scheduleAnimation(500);return}frame=(frame+1)%FLOW.length;try{map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW[frame])}catch{}scheduleAnimation(cadence(map))}
function scheduleAnimation(ms){if(animTimer||document.hidden)return;animTimer=setTimeout(animateOnce,Math.max(220,ms||cadence(mapNow())))}
function stopAnimation(){if(animTimer){clearTimeout(animTimer);animTimer=0}}
function restartAnimation(delay=140){stopAnimation();scheduleAnimation(delay)}
function bindMap(map){if(boundMap===map)return;boundMap=map;try{
 map.on('movestart',stopAnimation);
 map.on('zoomstart',stopAnimation);
 map.on('rotatestart',stopAnimation);
 map.on('moveend',()=>restartAnimation(220));
 map.on('zoomend',()=>restartAnimation(220));
 map.on('style.load',()=>scheduleApply(120));
 }catch{}}
function scheduleApply(ms=70){clearTimeout(applyTimer);applyTimer=setTimeout(()=>{applyTimer=0;if(apply())restartAnimation(150)},ms)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fslanguage','fsmapready'])window.addEventListener(ev,()=>scheduleApply(80));
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();else scheduleApply(100)});
window.addEventListener('focus',()=>scheduleApply(100));
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){clearInterval(ready);restartAnimation(220)}else if(tries>120)clearInterval(ready)},180);
window.FloodSafeRiverStyle={apply:()=>scheduleApply(0),COLOR:RIVER_BLUE,FLOW_MIN_ZOOM,LOW_POWER,get dangerColor(){return RIVER_BLUE},get warningColor(){return RIVER_BLUE},get watchColor(){return RIVER_BLUE},get normalColor(){return RIVER_BLUE},get unknownColor(){return RIVER_BLUE}};
})();
