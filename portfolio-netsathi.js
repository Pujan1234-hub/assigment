(()=>{
  // Legacy compatibility shim only.
  // The current PJBUILTS NetSathi card/detail/screens are owned by the
  // LifeOS-Android portfolio scripts loaded through auto-update.js.
  // Keeping this file from rebuilding #netsathi-showcase prevents the old
  // always-visible gallery from overriding the intended "See screenshots"
  // toggle experience on mobile and desktop.
  if(window.__pjNetSathiLegacyShimV3) return;
  window.__pjNetSathiLegacyShimV3=true;
})();
