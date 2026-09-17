(()=>{'use strict';
if(window.__fsRiverLineStyleV11)return;window.__fsRiverLineStyleV11=true;
const RIVER_BLUE='#168BFF';
const FRESH=['==',['get','live_updated_5m'],1];
const KNOWN=['in',['get','live_status'],['literal',['normal','watch','warning','danger']]];
const COLOR=RIVER_BLUE;
function add(map,source){if(!map?.getSource(source))return;try{
 if(!map.getLayer('hydro-complete-status-glow'))map.addLayer({id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,4.2,8,6.2,11,9.5,16,15],'line-opacity':['case',FRESH,.34,.18],'line-blur':['case',FRESH,3.5,2]}});
 if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,filter:KNOWN,paint:{'line-color':RIVER_BLUE,'line-width':['interpolate',['linear'],['zoom'],5,1.7,8,2.5,11,4.2,16,7],'line-opacity':['case',FRESH,.98,.76],'line-blur':.12,'line-dasharray':[.25,2.2]}});
 for(const id of['hydro-complete-flood-glow','hydro-complete-flood-pulse'])if(map.getLayer(id))map.setLayoutProperty(id,'visibility','none');
}catch(e){console.warn('FloodSafe river blue layer failed',e)}}
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.getSource('hydro-complete')||!map.getLayer('hydro-complete-lines'))return false;try{
 map.setPaintProperty('hydro-complete-lines','line-color',RIVER_BLUE);
 map.setPaintProperty('hydro-complete-lines','line-opacity',.92);
 map.setPaintProperty('hydro-complete-lines','line-width',['interpolate',['linear'],['zoom'],5,1.05,8,1.7,11,2.9,16,5.2]);
 add(map,'hydro-complete');
 for(const id of['hydro-complete-status-glow','hydro-complete-live-flow'])if(map.getLayer(id)){map.setFilter(id,KNOWN);map.setPaintProperty(id,'line-color',RIVER_BLUE)}
 for(const id of['hydro-complete-flood-glow','hydro-complete-flood-pulse'])if(map.getLayer(id))map.setLayoutProperty(id,'visibility','none');
 return true
}catch(e){console.warn('FloodSafe river blue apply failed',e);return false}}
const FLOW=[[.2,2.4],[.45,2.1],[.75,1.75],[1.05,1.45],[1.35,1.15],[1.05,1.45],[.75,1.75],[.45,2.1]];let frame=0,phase=false,anim=null;
function animate(){const map=window.FloodSafeMap?.map;if(!map)return;frame=(frame+1)%FLOW.length;phase=!phase;try{
 if(map.getLayer('hydro-complete-live-flow')){map.setPaintProperty('hydro-complete-live-flow','line-color',RIVER_BLUE);map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW[frame]);map.setPaintProperty('hydro-complete-live-flow','line-opacity',['case',FRESH,phase?.98:.78,phase?.76:.56])}
 if(map.getLayer('hydro-complete-status-glow')){map.setPaintProperty('hydro-complete-status-glow','line-color',RIVER_BLUE);map.setPaintProperty('hydro-complete-status-glow','line-opacity',['case',FRESH,phase?.42:.28,phase?.24:.14])}
}catch{}}
function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},280)}
let timer=0;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{apply();start()},40)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fslanguage','fsmapready'])window.addEventListener(ev,schedule);
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){start();clearInterval(ready)}else if(tries>160)clearInterval(ready)},120);
window.FloodSafeRiverStyle={apply,COLOR:RIVER_BLUE,get dangerColor(){return RIVER_BLUE},get warningColor(){return RIVER_BLUE},get watchColor(){return RIVER_BLUE},get normalColor(){return RIVER_BLUE},get unknownColor(){return RIVER_BLUE}};
})();
