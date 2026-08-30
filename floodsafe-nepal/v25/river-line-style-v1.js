(()=>{'use strict';
if(window.__fsRiverLineStyleV1)return;window.__fsRiverLineStyleV1=true;
const COLOR=['match',['get','live_status'],'danger','#e63946','warning','#ff8c32','watch','#f4c542','normal','#19b56b','#22e7ff'];
const OPACITY=['match',['get','live_status'],'unknown',0.30,0.98];
let applied=false;
function apply(){const map=window.FloodSafeMap?.map;if(!map||!map.isStyleLoaded?.())return false;try{if(map.getLayer('river-flow-live')){map.setPaintProperty('river-flow-live','line-color',COLOR);map.setPaintProperty('river-flow-live','line-opacity',OPACITY);applied=true}if(map.getLayer('river-base')){map.setPaintProperty('river-base','line-color',COLOR);map.setPaintProperty('river-base','line-opacity',['match',['get','live_status'],'unknown',0.72,0.98])}return applied}catch{return false}}
let tries=0;const t=setInterval(()=>{tries++;if(apply()||tries>200)clearInterval(t)},100);window.addEventListener('fsriverlinestatus',apply);window.addEventListener('fslanguage',apply);window.addEventListener('load',()=>setTimeout(apply,0));
})();