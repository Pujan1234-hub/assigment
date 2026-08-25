(()=>{
  // Hotfix loader: the installed PWA already loads auto.js, so load the
  // trust/validation layer from here as well. The version query bypasses
  // stale script caches without requiring the user to reinstall the app.
  if(!document.querySelector('script[data-fixcheck-trust]')){
    const s=document.createElement('script');
    s.src='./trust.js?v=8';
    s.async=false;
    s.dataset.fixcheckTrust='1';
    document.head.appendChild(s);
  }

  let wasOffline=!navigator.onLine;
  let reconnectTimer=null;

  function showMessage(message){
    try{
      if(typeof window.toast==='function'){
        window.toast(message);
        return;
      }
    }catch{}
    const pill=document.querySelector('#online span,#onlineText');
    if(pill) pill.textContent=message;
  }

  function hideInstallWhenInstalled(){
    const installed=window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
    const btn=document.querySelector('#install,#installBtn');
    if(btn&&installed) btn.style.display='none';
  }

  hideInstallWhenInstalled();
  window.addEventListener('appinstalled',hideInstallWhenInstalled);

  window.addEventListener('offline',()=>{
    wasOffline=true;
    clearTimeout(reconnectTimer);
  });

  window.addEventListener('online',()=>{
    if(!wasOffline) return;
    wasOffline=false;
    clearTimeout(reconnectTimer);
    showMessage('Connection restored — rechecking automatically…');
    reconnectTimer=setTimeout(()=>{
      if(!navigator.onLine) return;
      const btn=document.querySelector('#run,#runBtn');
      if(btn&&!btn.disabled){
        btn.click();
        return;
      }
      try{
        if(typeof window.runCheck==='function') window.runCheck();
        else if(typeof window.run==='function') window.run();
      }catch{}
    },1500);
  });
})();
