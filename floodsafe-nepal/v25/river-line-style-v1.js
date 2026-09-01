(()=>{'use strict';
if(window.__fsRiverLineStyleV9)return;window.__fsRiverLineStyleV9=true;
const CURRENT=['==',['get','live_updated_5m'],1];
const COLOR=['case',CURRENT,['match',['get','live_status'],'danger','#ff1515','warning','#ff7a00','watch','#ffd166','normal','#22b8ff','#557b8b'],'#607887'];
const OPACITY=['case',CURRENT,['match',['get','live_status'],'unknown',0.55,0.99],0.46];
const ALERT_FILTER=['all',CURRENT,['in',['get','live_status'],['literal',['warning','danger']]]];
const LIVE_FILTER=['all',CURRENT,['in',['get','live_status'],['literal',['normal','watch','warning','danger']]]];
function addLayers(map,source){if(!map?.getSource(source))return;try{
 if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,filter:LIVE_FILTER,paint:{'line-color':COLOR,'line-width':['interpolate',['linear'],['zoom'],5,1.7,10,3.2,16,5.8],'line-opacity':0.72,'line-blur':0.25,'line-dasharray':[0.25,2.2]}});
 if(!map.getLayer('hydro-complete-flood-glow'))map.addLayer({id:'hydro-complete-flood-glow',type:'line',source,filter:ALERT_FILTER,paint:{'line-color':['match',['get','live_status'],'danger','#ff0000','#ff7a00'],'line-width':['interpolate',['linear'],['zoom'],5,10,10,18,16,30],'line-opacity':0.56,'line-blur':9}});
 if(!map.getLayer('hydro-complete-flood-pulse'))map.addLayer({id:'hydro-complete-flood-pulse',type:'line',source,filter:ALERT_FILTER,paint:{'line-color':['match',['get','live_status'],'danger','#ff1b1b','#ff8a00'],'line-width':['interpolate',['linear'],['zoom'],5,3.2,10,7.2,16,13],'line-opacity':1,'line-blur':0.6,'line-dasharray':[0.45,1.25]}})
}catch(e){console.warn('FloodSafe river animation layer failed',e)}}
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.isStyleLoaded?.())return false;try{
 if(map.getLayer('hydro-complete-lines')){map.setPaintProperty('hydro-complete-lines','line-color',COLOR);map.setPaintProperty('hydro-complete-lines','line-opacity',OPACITY)}
 addLayers(map,'hydro-complete');
 if(map.getLayer('hydro-complete-live-flow'))map.setFilter('hydro-complete-live-flow',LIVE_FILTER);
 for(const id of['hydro-complete-flood-glow','hydro-complete-flood-pulse'])if(map.getLayer(id))map.setFilter(id,ALERT_FILTER);
 return true
}catch(e){console.warn('FloodSafe river colour apply failed',e);return false}}
const FLOW_PATTERNS=[[0.2,2.4],[0.55,2.0],[0.95,1.6],[1.35,1.2],[0.95,1.6],[0.55,2.0]];let frame=0,phase=false,anim=null;
function animate(){const map=window.FloodSafeMap?.map;if(!map)return;frame=(frame+1)%FLOW_PATTERNS.length;phase=!phase;try{
 if(map.getLayer('hydro-complete-live-flow')){map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW_PATTERNS[frame]);map.setPaintProperty('hydro-complete-live-flow','line-opacity',phase?0.9:0.58)}
 if(map.getLayer('hydro-complete-flood-glow')){map.setPaintProperty('hydro-complete-flood-glow','line-opacity',phase?0.82:0.38);map.setPaintProperty('hydro-complete-flood-glow','line-width',['interpolate',['linear'],['zoom'],5,phase?14:9,10,phase?24:17,16,phase?38:28])}
 if(map.getLayer('hydro-complete-flood-pulse')){map.setPaintProperty('hydro-complete-flood-pulse','line-dasharray',phase?[0.35,1.0]:[1.15,0.55]);map.setPaintProperty('hydro-complete-flood-pulse','line-opacity',phase?1:0.72)}
}catch{}}
function startAnim(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(!apply())return;animate()},280)}
let timer=0;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{apply();startAnim()},80)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fslanguage','fsmapready'])window.addEventListener(ev,schedule);
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){startAnim();clearInterval(ready)}else if(tries>100)clearInterval(ready)},160);
window.FloodSafeRiverStyle={apply,COLOR,get dangerColor(){return'#ff1515'},get warningColor(){return'#ff7a00'},get normalColor(){return'#22b8ff'},get unknownColor(){return'#607887'}};
})();
