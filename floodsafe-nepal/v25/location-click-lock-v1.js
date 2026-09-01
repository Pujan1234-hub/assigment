(()=>{'use strict';
if(window.__fsLocationClickLockV3)return;window.__fsLocationClickLockV3=true;
// The old capture-phase click blocker is permanently removed. Load the
// dedicated high-accuracy Nepal GPS runtime without blocking FloodSafe core.
if(!document.querySelector('script[data-fs-location-runtime]')){const s=document.createElement('script');s.src='./location-runtime-v2.js?v=2';s.defer=true;s.dataset.fsLocationRuntime='1';document.head.appendChild(s)}
})();
