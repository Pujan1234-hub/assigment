(()=>{'use strict';
if(window.__fsNativeAlertBridgeV1)return;window.__fsNativeAlertBridgeV1=true;
const MAX_KM=2;
const devicePoint=()=>{const d=window.FloodSafeCurrentLocation?.last;return d&&Number.isFinite(d.lat)&&Number.isFinite(d.lon)?{lat:d.lat,lon:d.lon}:null};
const gpsPoint=()=>{const s=window.FloodSafe?.state;return s?.kind==='gps'&&Number.isFinite(s.lat)&&Number.isFinite(s.lon)&&window.FloodSafe?.insideNepal?.(s.lat,s.lon)?{lat:s.lat,lon:s.lon}:null};
function syncFromUserAction(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state;if(!native||!s)return;
  if(s.alertsOn){
    // User opt-in is persistent. Never turn it back off merely because the WebView
    // is hidden, GPS is warming up, or a network/FCM request is temporarily unavailable.
    native.setRainAlerts?.(true);
    const p=devicePoint()||gpsPoint();
    if(p)native.setBackgroundRainAlerts?.(p.lat,p.lon);
    else setTimeout(()=>window.FloodSafeCurrentLocation?.locate?.(),0);
    native.requestBackgroundLocationForAlerts?.();
  }else{
    native.setRainAlerts?.(false);
    native.disableBackgroundRainAlerts?.();
  }
}
function syncPoint(){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state;if(!native||!s?.alertsOn)return;
  const p=devicePoint()||gpsPoint();
  if(p)native.setBackgroundRainAlerts?.(p.lat,p.lon);
  else native.syncBackgroundRainAlerts?.();
}
function currentLocationChanged(event){
  const native=window.FloodSafeNative,s=window.FloodSafe?.state,d=event?.detail;
  if(!native||!s?.alertsOn||!d||!Number.isFinite(d.lat)||!Number.isFinite(d.lon))return;
  // Native code stores device location for rain everywhere, but only retains a
  // Nepal river-proximity target when the fix is actually inside Nepal.
  native.setBackgroundRainAlerts?.(d.lat,d.lon);
}
function boot(){
  const btn=document.getElementById('alertBtn');
  if(btn)btn.addEventListener('click',()=>setTimeout(syncFromUserAction,0));
  window.addEventListener('fsfocuschange',()=>setTimeout(syncPoint,0));
  window.addEventListener('fscurrentlocation',currentLocationChanged);
  if(window.FloodSafe?.state?.alertsOn){
    // Native saved state + foreground location service continue after app close.
    // A missing fresh WebView GPS point is not a reason to disable monitoring.
    window.FloodSafeNative?.syncRainAlertsStatus?.();
    window.FloodSafeNative?.syncBackgroundRainAlerts?.();
    const p=devicePoint()||gpsPoint();
    if(p)window.FloodSafeNative?.setBackgroundRainAlerts?.(p.lat,p.lon);
  }else{
    window.FloodSafeNative?.setRainAlerts?.(false);
    window.FloodSafeNative?.disableBackgroundRainAlerts?.();
  }
  window.FloodSafeNearbyAlertPolicy={radiusKm:MAX_KM,currentGpsOnly:true,backgroundNative:true};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();