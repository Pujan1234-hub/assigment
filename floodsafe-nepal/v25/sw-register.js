(()=>{'use strict';if(window.__fsSwRegister)return;window.__fsSwRegister=true;
// Stability mode: never intercept taps/clicks. Native <a href> navigation must remain untouched.
// Remove any old V25 service worker/cache quietly in the background.
const cleanup=async()=>{
  try{
    if('serviceWorker' in navigator){
      const regs=await navigator.serviceWorker.getRegistrations();
      for(const r of regs){
        if(String(r.scope||'').includes('/floodsafe-nepal/v25/')) await r.unregister();
      }
    }
  }catch(_){}
  try{
    if('caches' in window){
      const keys=await caches.keys();
      await Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-v25-')).map(k=>caches.delete(k)));
    }
  }catch(_){}
};
if('requestIdleCallback' in window) requestIdleCallback(()=>cleanup(),{timeout:1500});
else setTimeout(cleanup,400);
})();
