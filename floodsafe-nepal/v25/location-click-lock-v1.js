(()=>{'use strict';
if(window.__fsLocationClickLockV3)return;window.__fsLocationClickLockV3=true;
// The old capture-phase click blocker is permanently removed. Load the
// dedicated high-accuracy GPS runtime; it now restores a previous Current Location
// choice automatically without opening the map on app startup.
if(!document.querySelector('script[data-fs-location-runtime]')){const s=document.createElement('script');s.src='./location-runtime-v3.js?v=5';s.defer=true;s.dataset.fsLocationRuntime='1';document.head.appendChild(s)}
})();
