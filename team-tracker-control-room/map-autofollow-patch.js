/* Keep active staff visible on the Control Room map regardless of Princesshay geofence. */
(() => {
  let lastAuto = 0;
  function ensureActiveStaffVisible(){
    const box = document.getElementById('mapbox');
    if (!box || box.offsetParent === null) return;
    const liveRows = (typeof rows !== 'undefined' && Array.isArray(rows))
      ? rows.filter(r => r && r.is_on_shift === true && Number.isFinite(Number(r.latitude)) && Number.isFinite(Number(r.longitude)))
      : [];
    if (!liveRows.length) return;
    const pins = [...box.querySelectorAll('.tt-staff-layer .tt-pin:not(.site)')];
    const b = box.getBoundingClientRect();
    const visible = pins.some(pin => {
      const p = pin.getBoundingClientRect();
      return p.right >= b.left + 8 && p.left <= b.right - 8 && p.bottom >= b.top + 8 && p.top <= b.bottom - 8;
    });
    if (visible) return;
    const now = Date.now();
    if (now - lastAuto < 3000) return;
    lastAuto = now;
    const home = box.querySelector('[data-a="home"]');
    if (home) home.click();
  }

  const install = () => {
    if (typeof window.renderLocations !== 'function') return setTimeout(install, 50);
    const original = window.renderLocations;
    window.renderLocations = function(){
      const result = original.apply(this, arguments);
      requestAnimationFrame(() => requestAnimationFrame(ensureActiveStaffVisible));
      return result;
    };
    setTimeout(ensureActiveStaffVisible, 250);
  };
  install();
})();