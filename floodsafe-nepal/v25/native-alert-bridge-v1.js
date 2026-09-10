(()=>{'use strict';
if(window.__fsNativeAlertBridgeV1)return;window.__fsNativeAlertBridgeV1=true;
const MAX_KM=2;
const gpsPoint=()=>{const s=window.FloodSafe?.state;return s?.kind==='gps'&&Number.isFinite(s.lat)&&Number.isFinite(s.lon)&&window.FloodSafe?.insideNepal?.(s.lat,s.lon)?{lat:s.lat,lon:s.lon}:null};
function syncFromUserAction(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state;if(!native||!s)return;
  if(s.alertsOn){
    native.setRainAlerts?.(true);
    const p=gpsPoint();
    if(p)native.setBackgroundRainAlerts?.(p.lat,p.lon);
    else{
      native.disableBackgroundRainAlerts?.();
      // Nearby warnings are current-GPS only. Ask for GPS when the user turns alerts on.
      setTimeout(()=>window.FloodSafeCurrentLocation?.locate?.(),0);
    }
  }else{
    native.setRainAlerts?.(false);
    native.disableBackgroundRainAlerts?.();
  }
}
function syncPoint(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state,p=gpsPoint();
  if(!native||!s?.alertsOn)return;
  if(p)native.setBackgroundRainAlerts?.(p.lat,p.lon);
  else native.disableBackgroundRainAlerts?.();
}
function currentLocationChanged(event){
  const native=window.FloodSafeNative,d=event?.detail;
  if(!native||!d||!Number.isFinite(d.lat)||!Number.isFinite(d.lon))return;
  // Being outside Nepal must never leave an old Nepal proximity target active.
  if(!window.FloodSafe?.insideNepal?.(d.lat,d.lon))native.disableBackgroundRainAlerts?.();
}
function boot(){
  const btn=document.getElementById('alertBtn');
  if(btn)btn.addEventListener('click',()=>setTimeout(syncFromUserAction,0));
  window.addEventListener('fsfocuschange',()=>setTimeout(syncPoint,0));
  window.addEventListener('fscurrentlocation',currentLocationChanged);
  // Migrate old saved/map-based proximity targets safely: only a verified current GPS
  // point may keep background nearby-river monitoring enabled.
  if(window.FloodSafe?.state?.alertsOn){
    window.FloodSafeNative?.syncRainAlertsStatus?.();
    if(gpsPoint())window.FloodSafeNative?.syncBackgroundRainAlerts?.();
    else window.FloodSafeNative?.disableBackgroundRainAlerts?.();
  }
  window.FloodSafeNearbyAlertPolicy={radiusKm:MAX_KM,currentGpsOnly:true};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();