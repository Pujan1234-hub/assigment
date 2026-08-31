(()=>{'use strict';
if(window.__fsStationClickCoherenceV1)return;window.__fsStationClickCoherenceV1=true;
let wired=false,tries=0;
function wire(){const map=window.FloodSafeMap?.map;if(!map||!map.getLayer?.('gauges')){if(tries++<240)setTimeout(wire,250);return}if(wired)return;wired=true;
map.on('click','gauges',e=>{try{e.preventDefault?.();window.FloodSafeRiverDetail?.close?.();setTimeout(()=>window.FloodSafeRiverDetail?.close?.(),0)}catch{}});
window.__fsStationClickCoherenceReady=true}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.addEventListener('fsmapready',wire);
})();