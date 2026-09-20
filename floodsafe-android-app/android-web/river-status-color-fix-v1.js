(()=>{
'use strict';
if(window.__fsRiverStatusColorFixV3)return;
window.__fsRiverStatusColorFixV3=true;

const ONE_SECOND=1000;
const STATUS_COLOR=['match',['get','live_status'],
  'danger','#ff2d20',
  'warning','#ff8a00',
  'watch','#ffd43b',
  'alert','#ffd43b',
  'normal','#20a9ff',
  '#94a3b8'
];
const GAUGE_COLOR=['case',['==',['get','has_latest'],0],'#94a3b8',
  ['match',['get','status'],
    'danger','#ff2d20',
    'warning','#ff8a00',
    'watch','#ffd43b',
    'alert','#ffd43b',
    'normal','#20a9ff',
    '#94a3b8'
  ]
];
let paintTimer=0;
let fastTimer=0;
let tickBusy=false;

function loadAllStationsModule(){
  if(window.__fsAndroidAllStationsRealtimeV1||document.querySelector('script[data-fs-all-stations]'))return;
  const s=document.createElement('script');
  s.src='./all-stations-realtime-v1.js?v=1';
  s.defer=true;
  s.dataset.fsAllStations='1';
  document.head.appendChild(s);
}

function installPanelStyle(){
  if(document.getElementById('fsAndroidRiverStatusColorV3'))return;
  const s=document.createElement('style');
  s.id='fsAndroidRiverStatusColorV3';
  s.textContent='#fsMapSidePanel .fsTimelineItem.current{border-color:#60a5fa!important;background:#eff6ff!important}#fsMapSidePanel .fsTimelineItem.fs-watch{border-color:#facc15!important;background:#fefce8!important}#fsMapSidePanel .fsTimelineItem.fs-warning{border-color:#fb923c!important;background:#fff7ed!important}#fsMapSidePanel .fsTimelineItem.fs-danger{border-color:#fb7185!important;background:#fff1f2!important}#fsMapSidePanel .fsTimelineItem.fs-stale{border-color:#94a3b8!important;background:#f1f5f9!important}#fsMapSidePanel .fsTimelineItem.fs-unknown{border-color:#cbd5e1!important;background:#f8fafc!important}';
  document.head.appendChild(s);
}

function classifyTimeline(x){
  if(!x||!x.classList.contains('fsTimelineItem'))return;
  x.classList.remove('fs-watch','fs-warning','fs-danger','fs-stale','fs-unknown');
  const t=(x.textContent||'').toLowerCase();
  if(/पछिल्लो उपलब्ध|अहिलेको अवस्था होइन|last known observation|not current|पुरानो|stale|ढिलो/.test(t))x.classList.add('fs-stale');
  else if(/खतरा|danger|red/.test(t))x.classList.add('fs-danger');
  else if(/चेतावनी|warning|orange/.test(t))x.classList.add('fs-warning');
  else if(/निगरानी|सतर्क|watch|alert|yellow|rising/.test(t))x.classList.add('fs-watch');
  else if(/पढाइ छैन|no reading|unknown/.test(t))x.classList.add('fs-unknown');
}

function scanPanel(root=document){
  root.querySelectorAll?.('#fsMapSidePanel .fsTimelineItem').forEach(classifyTimeline);
}

function setPaint(map,id,prop,value){
  try{if(map.getLayer(id))map.setPaintProperty(id,prop,value)}catch{}
}

function setLayout(map,id,prop,value){
  try{if(map.getLayer(id))map.setLayoutProperty(id,prop,value)}catch{}
}

function enforceMapStatus(){
  paintTimer=0;
  const map=window.FloodSafeMap?.map;
  if(!map||!map.isStyleLoaded?.())return false;
  setPaint(map,'hydro-complete-lines','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-live-flow','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-status-glow','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-flood-pulse','line-color',[
    'match',['get','live_status'],'danger','#ff2d20','warning','#ff8a00','#ffd43b'
  ]);
  setLayout(map,'hydro-complete-flood-pulse','visibility','visible');
  setPaint(map,'gauges-live-281','circle-color',GAUGE_COLOR);
  try{if(map.getLayer('gauges-live-281'))map.moveLayer('gauges-live-281')}catch{}
  try{if(map.getLayer('gauges'))map.setLayoutProperty('gauges','visibility','none')}catch{}
  window.__fsAndroidRiverPaint={
    checkedAt:new Date().toISOString(),
    mode:'official-status-colours',
    colors:{normal:'blue',alert:'yellow',warning:'orange',danger:'red',unknown:'grey'}
  };
  return true;
}

function schedulePaint(delay=160){
  clearTimeout(paintTimer);
  paintTimer=setTimeout(enforceMapStatus,delay);
}

function requestLatest(){
  if(tickBusy||navigator.onLine===false)return;
  tickBusy=true;
  try{
    // Background data refresh only: never reload the page, move the camera or change scroll.
    window.FloodSafeRiverRealtime?.refresh?.();
    window.FloodSafeRainRealtime?.poll?.();
    window.FloodSafeHydroExtraRealtime?.refresh?.();
    window.FloodSafeRiverLine?.rebuild?.(false);
    schedulePaint(120);
    window.dispatchEvent(new CustomEvent('fsandroidlivetick',{detail:{checkedAt:new Date().toISOString()}}));
  }catch{}finally{
    setTimeout(()=>{tickBusy=false},180);
  }
}

function startFastSync(){
  if(fastTimer)return;
  requestLatest();
  fastTimer=setInterval(requestLatest,ONE_SECOND);
  window.__fsAndroidRiverFastSync={
    intervalMs:ONE_SECOND,
    visiblePolling:true,
    hiddenPollingBestEffort:true,
    uiReloads:false,
    backgroundDelivery:'1s in-process checker + FCM/foreground-service/WorkManager safety path'
  };
}

loadAllStationsModule();
installPanelStyle();
scanPanel();
new MutationObserver(()=>scanPanel()).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
for(const ev of ['fsmapready','fs281mapready','fsriverupdate','fstrustedriverupdate','fsrainupdate','fshydroextraupdate','fsriverlinestatus']){
  window.addEventListener(ev,()=>schedulePaint(90));
}
window.addEventListener('focus',()=>{requestLatest();schedulePaint(80)});
window.addEventListener('online',()=>{requestLatest();schedulePaint(80)});
document.addEventListener('visibilitychange',()=>{requestLatest();schedulePaint(100)});

startFastSync();
let tries=0;
const ready=setInterval(()=>{
  if(enforceMapStatus()||++tries>180)clearInterval(ready);
},250);

window.FloodSafeAndroidRiverFix={
  refresh:requestLatest,
  repaint:()=>schedulePaint(0),
  intervalMs:ONE_SECOND
};
})();
