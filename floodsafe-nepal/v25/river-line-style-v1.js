(()=>{'use strict';
if(window.__fsRiverLineStyleV18)return;window.__fsRiverLineStyleV18=true;
const RIVER_BLUE='#168BFF';
const FRESH=['==',['get','live_updated_5m'],1];
const HOT=['in',['get','live_status'],['literal',['watch','warning','danger','alert']]];
const FLOW_MIN_ZOOM=5.0,SHADOW_MIN_ZOOM=8.4,GLOW_MIN_ZOOM=9.5,FULL_DETAIL_ZOOM=9.4;
const hw=Number(navigator.hardwareConcurrency||0),mem=Number(navigator.deviceMemory||0);
const LOW_POWER=(hw>0&&hw<=4)||(mem>0&&mem<=4);
const FLOW=[[.18,3.2],[.38,3.0],[.58,2.8],[.80,2.58],[1.02,2.36],[.80,2.58],[.58,2.8],[.38,3.0]];
const BASE_WIDTH=['interpolate',['linear'],['zoom'],5,.18,6.4,.24,7.2,.30,8.2,.38,9.4,.52,12,.92,16,1.75];
const FLOW_WIDTH=['interpolate',['linear'],['zoom'],5,.08,6.4,.11,7.2,.14,8.2,.18,9.4,.25,12,.45,16,.82];
const SHADOW_WIDTH=['interpolate',['linear'],['zoom'],8.4,.48,10,.68,12,1.12,16,2.05];
const GLOW_WIDTH=['interpolate',['linear'],['zoom'],9.5,.58,11,.86,13,1.35,16,2.25];
let frame=0,animTimer=0,applyTimer=0,boundMap=null,lastBand='';
function mapNow(){return window.FloodSafeMap?.map||null}
function same(a,b){if(a===b)return true;try{return JSON.stringify(a)===JSON.stringify(b)}catch{return false}}
function setPaint(map,id,prop,value){try{const cur=map.getPaintProperty(id,prop);if(same(cur,value))return;map.setPaintProperty(id,prop,value)}catch{}}
function setLayout(map,id,prop,value){try{const cur=map.getLayoutProperty(id,prop);if(cur===value)return;map.setLayoutProperty(id,prop,value)}catch{}}
function named(){return['==',['get','named'],true]}
function river(){return['==',['get','type'],'river']}
function major(){return['==',['get','fs_major'],1]}
function visibilityFilter(z){if(z<6.4)return['any',HOT,major()];if(z<7.2)return['any',HOT,['all',river(),named()]];if(z<8.2)return['any',HOT,named()];if(z<FULL_DETAIL_ZOOM)return['any',HOT,river(),named()];return null}
function band(z){return z<6.4?'major':z<7.2?'named-river':z<8.2?'named':z<FULL_DETAIL_ZOOM?'river':'full'}
function combine(base,extra){if(!base)return extra||null;if(!extra)return base;return['all',base,extra]}
function applyFilters(map,force=false){const z=map?.getZoom?.()||5,b=band(z);if(!force&&b===lastBand)return;lastBand=b;const base=visibilityFilter(z),status=['in',['get','live_status'],['literal',['warning','danger']]];for(const id of['hydro-complete-shadow','hydro-complete-lines','hydro-complete-live-flow','hydro-complete-status-glow','hydro-complete-hit'])if(map.getLayer(id)){try{map.setFilter(id,base)}catch{}}if(map.getLayer('hydro-complete-flood-pulse')){try{map.setFilter('hydro-complete-flood-pulse',combine(base,status))}catch{}}setLayout(map,'hydro-complete-shadow','visibility',z>=SHADOW_MIN_ZOOM?'visible':'none');setLayout(map,'hydro-complete-status-glow','visibility',z>=GLOW_MIN_ZOOM?'visible':'none')}
function add(map,source){if(!map?.getSource(source))return false;try{if(!map.getLayer('hydro-complete-status-glow'))map.addLayer({id:'hydro-complete-status-glow',type:'line',source,minzoom:GLOW_MIN_ZOOM,paint:{'line-color':RIVER_BLUE,'line-width':GLOW_WIDTH,'line-opacity':['case',FRESH,.11,.025],'line-blur':0}});if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,minzoom:FLOW_MIN_ZOOM,paint:{'line-color':RIVER_BLUE,'line-width':FLOW_WIDTH,'line-opacity':['case',FRESH,.52,.22],'line-blur':0,'line-dasharray':FLOW[0]}});return true}catch(e){console.warn('FloodSafe river flow layer failed',e);return false}}
function applyPaint(map){setPaint(map,'hydro-complete-lines','line-color',RIVER_BLUE);setPaint(map,'hydro-complete-lines','line-width',BASE_WIDTH);setPaint(map,'hydro-complete-lines','line-opacity',['match',['get','live_status'],'unknown',.56,.88]);setPaint(map,'hydro-complete-shadow','line-width',SHADOW_WIDTH);setPaint(map,'hydro-complete-shadow','line-opacity',.10);setPaint(map,'hydro-complete-hit','line-width',['interpolate',['linear'],['zoom'],5,3,8,4,10,6,16,10]);if(map.getLayer('hydro-complete-live-flow')){setPaint(map,'hydro-complete-live-flow','line-color',RIVER_BLUE);setPaint(map,'hydro-complete-live-flow','line-width',FLOW_WIDTH);setPaint(map,'hydro-complete-live-flow','line-opacity',['case',FRESH,.52,.22])}if(map.getLayer('hydro-complete-status-glow')){setPaint(map,'hydro-complete-status-glow','line-color',RIVER_BLUE);setPaint(map,'hydro-complete-status-glow','line-width',GLOW_WIDTH);setPaint(map,'hydro-complete-status-glow','line-opacity',['case',FRESH,.11,.025]);setPaint(map,'hydro-complete-status-glow','line-blur',0)}}
function apply(){const map=mapNow();if(!map||!map.getSource('hydro-complete')||!map.getLayer('hydro-complete-lines'))return false;try{if(!map.getLayer('hydro-complete-live-flow')||!map.getLayer('hydro-complete-status-glow'))add(map,'hydro-complete');applyPaint(map);applyFilters(map,true);bindMap(map);return true}catch(e){console.warn('FloodSafe river style apply failed',e);return false}}
function cadence(map){const z=map?.getZoom?.()||0;if(LOW_POWER){if(z<7)return 1900;if(z<8.8)return 1350;return 920}if(z<7)return 1500;if(z<8.8)return 980;return 680}
function canAnimate(map){return !!map&&!document.hidden&&!map.isMoving?.()&&!map.isZooming?.()&&!map.isRotating?.()&&(map.getZoom?.()||0)>=FLOW_MIN_ZOOM&&map.getLayer?.('hydro-complete-live-flow')}
function animateOnce(){animTimer=0;const map=mapNow();if(!canAnimate(map)){scheduleAnimation(650);return}frame=(frame+1)%FLOW.length;try{map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW[frame])}catch{}scheduleAnimation(cadence(map))}
function scheduleAnimation(ms){if(animTimer||document.hidden)return;animTimer=setTimeout(animateOnce,Math.max(360,ms||cadence(mapNow())))}
function stopAnimation(){if(animTimer){clearTimeout(animTimer);animTimer=0}}
function restartAnimation(delay=220){stopAnimation();scheduleAnimation(delay)}
function refreshAfterMove(){const map=mapNow();if(map)applyFilters(map);restartAnimation(320)}
function bindMap(map){if(boundMap===map)return;boundMap=map;try{map.on('movestart',stopAnimation);map.on('zoomstart',stopAnimation);map.on('rotatestart',stopAnimation);map.on('moveend',refreshAfterMove);map.on('zoomend',refreshAfterMove);map.on('style.load',()=>{lastBand='';scheduleApply(160)})}catch{}}
function scheduleApply(ms=100){clearTimeout(applyTimer);applyTimer=setTimeout(()=>{applyTimer=0;if(apply())restartAnimation(220)},ms)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fslanguage','fsmapready'])window.addEventListener(ev,()=>scheduleApply(100));
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();else scheduleApply(140)});
window.addEventListener('focus',()=>scheduleApply(140));
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){clearInterval(ready);restartAnimation(320)}else if(tries>120)clearInterval(ready)},180);
window.FloodSafeRiverStyle={apply:()=>scheduleApply(0),COLOR:RIVER_BLUE,FLOW_MIN_ZOOM,LOW_POWER,FULL_DETAIL_ZOOM,get dangerColor(){return RIVER_BLUE},get warningColor(){return RIVER_BLUE},get watchColor(){return RIVER_BLUE},get normalColor(){return RIVER_BLUE},get unknownColor(){return RIVER_BLUE}};
})();
