(()=>{'use strict';
if(window.__fsAutoAlertUiV1)return;window.__fsAutoAlertUiV1=true;
try{localStorage.setItem('fs-nepal-alerts-on','1')}catch{}
function syncState(){try{if(window.FloodSafe?.state)window.FloodSafe.state.alertsOn=true}catch{}}
function lockAlertButton(){
  syncState();
  const flood=document.getElementById('alertBtn');
  if(flood){
    flood.style.display='';
    flood.textContent='🔔 बाढी चेतावनी ON';
    flood.setAttribute('aria-pressed','true');
    flood.dataset.fsLockedOn='1';
  }
  for(const b of document.querySelectorAll('button')){
    const t=(b.textContent||'').trim().toLowerCase();
    if(t.includes('वर्षा सूचना सक्रिय')||t.includes('enable rain alert')||t.includes('enable rain notification')) b.style.display='none';
  }
}
function capture(e){const b=e.target?.closest?.('#alertBtn');if(!b)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();try{localStorage.setItem('fs-nepal-alerts-on','1')}catch{}syncState();b.textContent='🔔 बाढी चेतावनी ON';window.dispatchEvent(new CustomEvent('floodsafe-alerts-status',{detail:{enabled:true,locked:true}}))}
function boot(){lockAlertButton();document.addEventListener('click',capture,true);new MutationObserver(lockAlertButton).observe(document.documentElement,{childList:true,subtree:true,characterData:true});window.addEventListener('floodsafe-alerts-status',()=>lockAlertButton());setInterval(lockAlertButton,2000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
