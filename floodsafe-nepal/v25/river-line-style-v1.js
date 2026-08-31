(()=>{'use strict';
if(window.__fsRiverLineStyleV7)return;window.__fsRiverLineStyleV7=true;
const COLOR=['match',['get','live_status'],'danger','#ff1f1f','warning','#ff7a00','watch','#ffd166','normal','#22a7ff','#557b8b'];
const OPACITY=['match',['get','live_status'],'unknown',0.62,0.99];
const ALERT_FILTER=['in',['get','live_status'],['literal',['warning','danger']]];
function addAlertLayers(map,source){if(!map?.getSource(source))return;
  try{
    if(!map.getLayer('hydro-complete-flood-glow'))map.addLayer({id:'hydro-complete-flood-glow',type:'line',source,filter:ALERT_FILTER,paint:{'line-color':['match',['get','live_status'],'danger','#ff2a2a','#ff8a00'],'line-width':['interpolate',['linear'],['zoom'],5,7,10,13,16,22],'line-opacity':0.38,'line-blur':7}});
    if(!map.getLayer('hydro-complete-flood-pulse'))map.addLayer({id:'hydro-complete-flood-pulse',type:'line',source,filter:ALERT_FILTER,paint:{'line-color':['match',['get','live_status'],'danger','#ff1010','#ff7a00'],'line-width':['interpolate',['linear'],['zoom'],5,2.8,10,6.4,16,11.5],'line-opacity':0.98,'line-blur':1.1}});
  }catch(e){console.warn('FloodSafe alert river glow layer failed',e)}
}
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.isStyleLoaded?.())return false;try{
  if(map.getLayer('hydro-complete-lines')){map.setPaintProperty('hydro-complete-lines','line-color',COLOR);map.setPaintProperty('hydro-complete-lines','line-opacity',OPACITY)}
  addAlertLayers(map,'hydro-complete');
  for(const id of['hydro-complete-flood-glow','hydro-complete-flood-pulse'])if(map.getLayer(id))map.setFilter(id,ALERT_FILTER);
  return true;
}catch(e){console.warn('FloodSafe river colour apply failed',e);return false}}
let phase=false,anim=null;
function animate(){const map=window.FloodSafeMap?.map;if(!map?.getLayer('hydro-complete-flood-glow')||!map?.getLayer('hydro-complete-flood-pulse'))return;
  phase=!phase;
  try{
    map.setPaintProperty('hydro-complete-flood-glow','line-opacity',phase?0.68:0.26);
    map.setPaintProperty('hydro-complete-flood-glow','line-width',['interpolate',['linear'],['zoom'],5,phase?10:7,10,phase?17:13,16,phase?27:22]);
    map.setPaintProperty('hydro-complete-flood-pulse','line-opacity',phase?1:0.78);
  }catch{}
}
function startAnim(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;apply();animate()},700)}
let timer=0;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{apply();startAnim()},120)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fslanguage','fsmapready'])window.addEventListener(ev,schedule);
let tries=0;const ready=setInterval(()=>{tries++;if(apply()){startAnim();clearInterval(ready)}else if(tries>80)clearInterval(ready)},200);
window.FloodSafeRiverStyle={apply,COLOR,get dangerColor(){return'#ff1f1f'},get warningColor(){return'#ff7a00'},get normalColor(){return'#22a7ff'},get unknownColor(){return'#557b8b'}};
})();