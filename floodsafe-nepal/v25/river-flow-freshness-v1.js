(()=>{'use strict';
if(window.__fsRiverFlowFreshnessV1)return;window.__fsRiverFlowFreshnessV1=true;
function apply(){try{window.FloodSafeRiverLine?.rebuild?.(true);window.FloodSafeRiverStyle?.apply?.();window.FloodSafeStaleSafety?.apply?.()}catch{}}
// rebuild emits fsriverlinestatus itself. Listening to that event here creates
// an endless rebuild -> event -> rebuild loop that starves map rendering.
let queued=false;
function queue(){if(queued)return;queued=true;setTimeout(()=>{queued=false;apply()},40)}
for(const ev of['fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsmapready'])window.addEventListener(ev,queue);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(apply,0),{once:true});else setTimeout(apply,0);
})();
