(()=>{'use strict';
if(window.__fsRiverFlowFreshnessV1)return;window.__fsRiverFlowFreshnessV1=true;
function apply(){try{window.FloodSafeRiverLine?.rebuild?.(true);window.FloodSafeRiverStyle?.apply?.();window.FloodSafeStaleSafety?.apply?.()}catch{}}
for(const ev of['fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsriverlinestatus','fsmapready'])window.addEventListener(ev,()=>setTimeout(apply,0));
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(apply,0),{once:true});else setTimeout(apply,0);
})();
