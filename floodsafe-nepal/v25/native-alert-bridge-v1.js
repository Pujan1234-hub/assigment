(()=>{'use strict';
if(window.__fsNativeAlertBridgeV1)return;window.__fsNativeAlertBridgeV1=true;
const MAX_KM=15;
const point=()=>{const s=window.FloodSafe?.state;return s&&Number.isFinite(s.lat)&&Number.isFinite(s.lon)?{lat:s.lat,lon:s.lon}:null};
function syncFromUserAction(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state;if(!native||!s)return;
  if(s.alertsOn){
    native.setRainAlerts?.(true);
    const p=point();if(p)native.setBackgroundRainAlerts?.(p.lat,p.lon);
  }else{
    native.setRainAlerts?.(false);
    native.disableBackgroundRainAlerts?.();
  }
}
function syncPoint(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state,p=point();
  if(!native||!s?.alertsOn||!p)return;
  native.setBackgroundRainAlerts?.(p.lat,p.lon);
}
function boot(){
  const btn=document.getElementById('alertBtn');
  if(btn)btn.addEventListener('click',()=>setTimeout(syncFromUserAction,0));
  window.addEventListener('fsfocuschange',()=>setTimeout(syncPoint,0));
  // Existing users who already opted in keep their native subscription without
  // opening a new permission prompt on startup.
  if(window.FloodSafe?.state?.alertsOn){
    window.FloodSafeNative?.syncRainAlertsStatus?.();
    window.FloodSafeNative?.syncBackgroundRainAlerts?.();
  }
  window.FloodSafeNearbyAlertPolicy={radiusKm:MAX_KM};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
