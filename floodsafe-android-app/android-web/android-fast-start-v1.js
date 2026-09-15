(()=>{'use strict';
if(window.__fsAndroidFastStartV1)return;window.__fsAndroidFastStartV1=true;
const scripts=[
 './official-live-fetch-fix-v1.js?v=1',
 './trusted-river-runtime-v3.js?v=37',
 './trusted-rain-runtime-v1.js?v=4',
 './river-current-20m-v1.js?v=8',
 './realtime-guard-v1.js?v=8',
 './gauge-bridge.js?v=24',
 './river-name-alias-v1.js?v=1',
 './streamflow-gauge-patch-v1.js?v=1',
 './river-line-status-v1.js?v=10',
 './river-status-ui.js?v=4',
 './live-official-label-lock.js?v=2',
 './map-loader-v3.js?v=31',
 './map-mobile-recovery-v1.js?v=4',
 './permanent-281-map-v1.js?v=6',
 './station-click-coherence-v1.js?v=1',
 './river-line-style-v1.js?v=12',
 './river-flow-freshness-v1.js?v=2',
 './map-side-panel-v1.js?v=12',
 './user-facing-ui-v1.js?v=10',
 './clean-user-lines-v1.js?v=1',
 './sathi-flood-ai/live.js?v=1',
 './sathi-flood-ai/floating-ui-v2.js?v=2',
 './sathi-app-aware-v1.js?v=1',
 './sathi-flood-ai/place-weather-v1.js?v=1',
 './sathi-flood-ai/river-match-lock-v1.js?v=1',
 './sathi-flood-ai/advanced-server-v1.js?v=1'
];
function loadAt(i){if(i>=scripts.length){window.dispatchEvent(new Event('fsandroidfaststartcomplete'));return}const s=document.createElement('script');s.src=scripts[i];s.async=false;s.onload=()=>loadAt(i+1);s.onerror=()=>loadAt(i+1);document.body.appendChild(s)}
function start(){requestAnimationFrame(()=>requestAnimationFrame(()=>setTimeout(()=>loadAt(0),80)))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
