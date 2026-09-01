(()=>{'use strict';
if(window.__fsLocationClickLockV2)return;window.__fsLocationClickLockV2=true;
// Keep the location button fully interactive. The previous capture-phase lock
// stopped FloodSafe's own geolocation handler from ever receiving the click.
// Geolocation safety/inside-Nepal checks remain in flood-only.js.
})();
