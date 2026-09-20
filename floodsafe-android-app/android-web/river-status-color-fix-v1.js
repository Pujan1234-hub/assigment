(()=>{
'use strict';
if(window.__fsRiverStatusColorFixV2)return;
window.__fsRiverStatusColorFixV2=true;

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

function installPanelStyle(){
  if(document.getElementById('fsAndroidRiverStatusColorV2'))return;
  const s=document.createElement('style');
  s.id='fsAndroidRiverStatusColorV2';
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

  // The base web style intentionally makes every river blue. Android needs the
  // official status colours requested by the app: normal blue, alert yellow,
  // warning orange, danger red, unknown/stale grey.
  setPaint(map,'hydro-complete-lines','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-live-flow','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-status-glow','line-color',STATUS_COLOR);
  setPaint(map,'hydro-complete-flood-pulse','line-color',[
    'match',['get','live_status'],'danger','#ff2d20','warning','#ff8a00','#ffd43b'
  ]);
  setLayout(map,'hydro-complete-flood-pulse','visibility','visible');

  // Keep all official station markers visible/clickable above the river hit layer.
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

function schedulePaint(delay=220){
  clearTimeout(paintTimer);
  paintTimer=setTimeout(enforceMapStatus,delay);
}

function requestLatest(){
  if(document.hidden)return;
  try{window.FloodSafeRiverRealtime?.refresh?.()}catch{}
  // Rebuild is signature-aware; unchanged readings do not force expensive map work.
  try{window.FloodSafeRiverLine?.rebuild?.(false)}catch{}
  schedulePaint(260);
}

function startFastSync(){
  if(fastTimer)return;
  requestLatest();
  fastTimer=setInterval(requestLatest,ONE_SECOND);
  window.__fsAndroidRiverFastSync={
    intervalMs:ONE_SECOND,
    visiblePolling:true,
    hiddenPolling:false,
    backgroundDelivery:'FCM push + existing WorkManager fallback'
  };
}

installPanelStyle();
scanPanel();
new MutationObserver(()=>scanPanel()).observe(document.documentElement,{subtree:true,childList:true,characterData:true});

for(const ev of ['fsmapready','fs281mapready','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsriverlinestatus']){
  window.addEventListener(ev,()=>schedulePaint(240));
}
window.addEventListener('focus',()=>{requestLatest();schedulePaint(260)});
window.addEventListener('online',()=>{requestLatest();schedulePaint(260)});
document.addEventListener('visibilitychange',()=>{
  if(!document.hidden){requestLatest();schedulePaint(280)}
});

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
