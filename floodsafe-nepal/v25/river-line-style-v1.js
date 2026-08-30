(()=>{'use strict';
if(window.__fsRiverLineStyleV2)return;window.__fsRiverLineStyleV2=true;
const COLOR=['match',['get','live_status'],'danger','#ff2d20','warning','#ff7a00','watch','#ffd166','normal','#22e7ff','#22e7ff'];
const OPACITY=['match',['get','live_status'],'unknown',0.82,0.99];
let applied=false,phase=0;
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.isStyleLoaded?.())return false;try{for(const id of ['river-flow-live','river-base'])if(map.getLayer(id)){map.setPaintProperty(id,'line-color',COLOR);map.setPaintProperty(id,'line-opacity',OPACITY);applied=true}if(map.getLayer('hydro-complete-lines')){map.setPaintProperty('hydro-complete-lines','line-color',COLOR);map.setPaintProperty('hydro-complete-lines','line-opacity',OPACITY);applied=true}return applied}catch{return false}}
function pulse(){const map=window.FloodSafeMap?.map;phase=(phase+1)%4;try{const dash=[[.5,2.6],[1,2.0],[1.5,1.4],[2,1]][phase];if(map?.getLayer('hydro-complete-flood-pulse'))map.setPaintProperty('hydro-complete-flood-pulse','line-dasharray',dash);if(map?.getLayer('river-flood-pulse'))map.setPaintProperty('river-flood-pulse','line-dasharray',dash)}catch{}setTimeout(pulse,260)}
let tries=0;const t=setInterval(()=>{tries++;if(apply()||tries>240)clearInterval(t)},100);window.addEventListener('fsriverlinestatus',apply);window.addEventListener('fslanguage',apply);window.addEventListener('load',()=>setTimeout(apply,0));pulse();
})();