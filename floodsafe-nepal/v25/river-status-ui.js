(()=>{'use strict';
if(window.__fsRiverStatusUIV4)return;window.__fsRiverStatusUIV4=true;
const MAX=10*60*1000;
function refresh(){window.FloodSafeMap?.refreshGauges?.();window.FloodSafeRiverLatest?.apply?.()}
for(const ev of['fstrustedriverupdate','fsriverupdate','fslanguage','online'])window.addEventListener(ev,()=>requestAnimationFrame(refresh));
window.FloodSafeRiverStatusUI={refresh,MAX_AGE_MS:MAX,get catalogCount(){return window.FloodSafeMap?.stationCatalogCount||0},get currentCount(){return window.FloodSafeMap?.currentStationCount||0}};
})();
