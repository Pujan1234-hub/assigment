(()=>{'use strict';
if(window.__fsAutoAlertUiV1)return;window.__fsAutoAlertUiV1=true;
try{localStorage.setItem('fs-nepal-alerts-on','1')}catch{}
function syncState(){try{if(window.FloodSafe?.state)window.FloodSafe.state.alertsOn=true}catch{}}
function hideManual(){syncState();const flood=document.getElementById('alertBtn');if(flood)flood.style.display='none';for(const b of document.querySelectorAll('button')){const t=(b.textContent||'').trim().toLowerCase();if(t.includes('वर्षा सूचना सक्रिय')||t.includes('enable rain alert')||t.includes('enable rain notification')||t.includes('बाढी चेतावनी')){if(b.id!=='locateBtn')b.style.display='none'}}}
function boot(){hideManual();new MutationObserver(hideManual).observe(document.documentElement,{childList:true,subtree:true,characterData:true});window.addEventListener('floodsafe-alerts-status',e=>{if(e?.detail?.enabled){try{localStorage.setItem('fs-nepal-alerts-on','1')}catch{}syncState()}hideManual()});setInterval(hideManual,2000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
