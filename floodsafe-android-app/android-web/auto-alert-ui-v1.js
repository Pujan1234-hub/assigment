(()=>{'use strict';
if(window.__fsAutoAlertUiV1)return;window.__fsAutoAlertUiV1=true;
const markOn=()=>{
  try{localStorage.setItem('fs-nepal-alerts-on','1')}catch{}
  try{if(window.FloodSafe?.state)window.FloodSafe.state.alertsOn=true}catch{}
};
function boot(){
  markOn();
  // The alert button is removed from source HTML. Do not scan the whole DOM or
  // attach a subtree MutationObserver: map/station rendering mutates heavily and
  // the old observer caused repeated full-page button scans during startup/reopen.
  const legacy=document.getElementById('alertBtn');
  if(legacy)legacy.remove();
  window.addEventListener('floodsafe-alerts-status',e=>{
    if(e?.detail?.enabled)markOn();
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
