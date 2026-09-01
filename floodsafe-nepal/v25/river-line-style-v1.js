(()=>{'use strict';
if(window.__fsRiverLineStyleV10)return;window.__fsRiverLineStyleV10=true;
const FRESH=['==',['get','live_updated_5m'],1];
const KNOWN=['in',['get','live_status'],['literal',['normal','watch','warning','danger']]];
const ALERT=['in',['get','live_status'],['literal',['warning','danger']]];
const FRESH_ALERT=['all',FRESH,ALERT];
const COLOR=['match',['get','live_status'],'danger','#ff1616','warning','#ff7a00','watch','#ffd43b','normal','#12b8ff','#667d88'];
const BASE_OPACITY=['case',KNOWN,['case',FRESH,.98,.72],.42];
function add(map,source){if(!map?.getSource(source))return;try{
 if(!map.getLayer('hydro-complete-status-glow'))map.addLayer({id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,paint:{'line-color':COLOR,'line-width':['interpolate',['linear'],['zoom'],5,5.5,8,8,11,12,16,20],'line-opacity':['case',FRESH,.58,.26],'line-blur':['case',FRESH,4,2.2]}});
 if(!map.getLayer('hydro-complete-live-flow'))map.addLayer({id:'hydro-complete-live-flow',type:'line',source,filter:KNOWN,paint:{'line-color':COLOR,'line-width':['interpolate',['linear'],['zoom'],5,1.7,8,2.5,11,4.2,16,7],'line-opacity':['case',FRESH,.98,.68],'line-blur':.15,'line-dasharray':[.25,2.2]}});
 if(!map.getLayer('hydro-complete-flood-glow'))map.addLayer({id:'hydro-complete-flood-glow',type:'line',source,filter:FRESH_ALERT,paint:{'line-color':['match',['get','live_status'],'danger','#ff0000','#ff7900'],'line-width':['interpolate',['linear'],['zoom'],5,14,8,20,11,28,16,42],'line-opacity':.72,'line-blur':11}});
 if(!map.getLayer('hydro-complete-flood-pulse'))map.addLayer({id:'hydro-complete-flood-pulse',type:'line',source,filter:FRESH_ALERT,paint:{'line-color':['match',['get','live_status'],'danger','#ff0a0a','#ff8a00'],'line-width':['interpolate',['linear'],['zoom'],5,4,8,6.5,11,10,16,16],'line-opacity':1,'line-blur':.35,'line-dasharray':[.45,1.1]}})
}catch(e){console.warn('FloodSafe river glow layer failed',e)}}
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.isStyleLoaded?.())return false;try{
 if(map.getLayer('hydro-complete-lines')){map.setPaintProperty('hydro-complete-lines','line-color',COLOR);map.setPaintProperty('hydro-complete-lines','line-opacity',BASE_OPACITY);map.setPaintProperty('hydro-complete-lines','line-width',['interpolate',['linear'],['zoom'],5,.9,8,1.5,11,2.7,16,5])}
 add(map,'hydro-complete');
 for(const id of['hydro-complete-status-glow','hydro-complete-live-flow'])if(map.getLayer(id))map.setFilter(id,KNOWN);
 for(const id of['hydro-complete-flood-glow','hydro-complete-flood-pulse'])if(map.getLayer(id))map.setFilter(id,FRESH_ALERT);
 return true
}catch(e){console.warn('FloodSafe river colour apply failed',e);return false}}
const FLOW=[[.2,2.4],[.45,2.1],[.75,1.75],[1.05,1.45],[1.35,1.15],[1.05,1.45],[.75,1.75],[.45,2.1]];let frame=0,phase=false,anim=null;
function animate(){const map=window.FloodSafeMap?.map;if(!map)return;frame=(frame+1)%FLOW.length;phase=!phase;try{
 if(map.getLayer('hydro-complete-live-flow')){map.setPaintProperty('hydro-complete-live-flow','line-dasharray',FLOW[frame]);map.setPaintProperty('hydro-complete-live-flow','line-opacity',['case',FRESH,phase?.98:.76,phase?.72:.48])}
 if(map.getLayer('hydro-complete-status-glow'))map.setPaintProperty('hydro-complete-status-glow','line-opacity',['case',FRESH,phase?.66:.42,phase?.32:.18]);
 if(map.getLayer('hydro-complete-flood-glow')){map.setPaintProperty('hydro-complete-flood-glow','line-opacity',phase?.92:.5);map.setPaintProperty('hydro-complete-flood-glow','line-width',['interpolate',['linear'],['zoom'],5,phase?18:12,8,phase?26:18,11,phase?36:26,16,phase?50:38])}
 if(map.getLayer('hydro-complete-flood-pulse')){map.setPaintProperty('hydro-complete-flood-pulse','line-dasharray',phase?[.28,.75]:[1.2,.45]);map.setPaintProperty('hydro-complete-flood-pulse','line-opacity',phase?1:.68)}
}catch{}}
function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},240)}
let timer=0;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{apply();start()},40)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fslanguage','fsmapready'])window.addEventListener(ev,schedule);
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){start();clearInterval(ready)}else if(tries>160)clearInterval(ready)},120);
window.FloodSafeRiverStyle={apply,COLOR,get dangerColor(){return'#ff1616'},get warningColor(){return'#ff7a00'},get watchColor(){return'#ffd43b'},get normalColor(){return'#12b8ff'},get unknownColor(){return'#667d88'}};
})();
