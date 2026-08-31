(()=>{'use strict';
if(window.__fsRiverStatusUIV3)return;window.__fsRiverStatusUIV3=true;
const MAX=5*60*1000;
function refresh(){window.FloodSafeMap?.refreshGauges?.();window.FloodSafeRiverCurrent5?.apply?.()}
for(const ev of['fstrustedriverupdate','fsriverupdate','fslanguage','online'])window.addEventListener(ev,()=>requestAnimationFrame(refresh));
window.FloodSafeRiverStatusUI={refresh,MAX_AGE_MS:MAX,get catalogCount(){return window.FloodSafeMap?.stationCatalogCount||0},get currentCount(){return window.FloodSafeMap?.currentStationCount||0}};
})();