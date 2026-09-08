(()=>{
'use strict';
if(window.__SATHI_FLOATING_UI_V3__) return;
window.__SATHI_FLOATING_UI_V3__=true;

const norm=s=>String(s||'').toLowerCase().normalize('NFKC')
  .replace(/[?!.:,;()[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const firstText=(o,keys)=>{
  for(const k of keys){
    const v=o?.[k];
    if(v===undefined||v===null)continue;
    if(typeof v==='object'){
      const n=v.name||v.title||v.label||v.name_en||v.name_ne;
      if(n!==undefined&&n!==null&&String(n).trim())return String(n).trim();
    }else if(String(v).trim())return String(v).trim();
  }
  return '';
};
const firstNum=(o,keys)=>{
  for(const k of keys){
    const n=Number(o?.[k]);
    if(Number.isFinite(n))return n;
  }
  return null;
};
const stationName=o=>firstText(o,['stationName','station_name','riverName','river_name','name','title'])||'नदी स्टेशन';
const locationText=o=>{
  const parts=[
    firstText(o,['municipality','municipality_name','municipalityName','localLevel','local_level','palika']),
    firstText(o,['district','district_name','districtName','district_title']),
    firstText(o,['province','province_name','provinceName'])
  ].filter(Boolean);
  return [...new Set(parts)].join(', ');
};
const level=o=>firstNum(o,['_lastWaterLevel','_level','waterLevel','water_level','level','value','latestLevel']);
const warning=o=>firstNum(o,['_lastWarningLevel','_warning','warningLevel','warning_level','warningThreshold']);
const danger=o=>firstNum(o,['_lastDangerLevel','_danger','dangerLevel','danger_level','dangerThreshold']);
const measured=o=>firstText(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measurementTime','timestamp','updatedAt']);
const stage=o=>{
  try{
    const s=String(window.FloodSafeRiverRealtime?.stage?.(o)||'').toLowerCase();
    if(['danger','warning','watch','normal','unknown'].includes(s))return s;
  }catch{}
  const raw=norm(firstText(o,['_derivedStatus','_officialStatus','status','status_name']));
  if(raw.includes('danger')||raw.includes('खतरा'))return'danger';
  if(raw.includes('warning')||raw.includes('चेतावनी'))return'warning';
  if(raw.includes('watch')||raw.includes('rising')||raw.includes('सतर्क'))return'watch';
  return level(o)!==null?'normal':'unknown';
};
const stageNe=s=>s==='danger'?'🔴 खतरा':s==='warning'?'🟠 चेतावनी':s==='watch'?'🟡 निगरानी':s==='normal'?'🟢 सामान्य':'⚪ अवस्था अस्पष्ट';
const timeText=v=>{
  if(!v)return'';
  const d=new Date(v);
  if(Number.isNaN(d.getTime()))return'';
  try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'numeric',minute:'2-digit',hour12:true}).format(d)}
  catch{return''}
};

function detailedPlaceAnswer(rawQuestion){
  const q=norm(rawQuestion);
  const wantsPlaces=['jilla','district','जिल्ला','kata kata','कता कता','कहाँ कहाँ','kun thau','कुन ठाउँ','kun jaga','कुन ठाउ','कुन स्थान']
    .some(x=>q.includes(x));
  if(!wantsPlaces)return'';

  const state=window.FloodSafe?.state||{};
  const all=[state.currentRiverStations,state.latestRiverStations,state.allRiverStations,state.stations]
    .find(Array.isArray)||[];
  if(!all.length)return'अहिले BIPAD/DHM को ताजा आधिकारिक नदी मापन उपलब्ध छैन। डेटा नआएसम्म म जिल्ला वा स्थान अनुमान गर्दिनँ।';

  const placeMatches=all.filter(s=>{
    const place=locationText(s);
    return place && place.split(',').some(p=>{
      const n=norm(p);
      return n.length>=3 && q.includes(n);
    });
  });

  const base=placeMatches.length?placeMatches:all;
  const risky=base.map(s=>({s,st:stage(s)}))
    .filter(x=>['danger','warning','watch'].includes(x.st));
  const selected=risky.length?risky:(placeMatches.length?base.map(s=>({s,st:stage(s)})):[]);
  if(!selected.length){
    return placeMatches.length
      ?'त्यो स्थानसँग मिल्ने ताजा official स्टेशन भेटियो, तर उपलब्ध मापनमा चेतावनी/खतरा देखिएको छैन।'
      :'अहिले उपलब्ध ताजा official मापनमा चेतावनी वा खतरा तहमा पुगेको स्टेशन भेटिएन।';
  }

  const weight={danger:3,warning:2,watch:1,normal:0,unknown:-1};
  selected.sort((a,b)=>(weight[b.st]??-1)-(weight[a.st]??-1));
  const lines=selected.slice(0,10).map(({s,st})=>{
    const bits=[`${stageNe(st)} ${stationName(s)}`];
    const place=locationText(s);if(place)bits.push(place);
    const l=level(s),w=warning(s),d=danger(s);
    if(l!==null)bits.push(`जलस्तर ${l.toFixed(2)} मि.`);
    if(st==='danger'&&d!==null)bits.push(`खतरा तह ${d.toFixed(2)} मि.`);
    else if((st==='warning'||st==='watch')&&w!==null)bits.push(`चेतावनी तह ${w.toFixed(2)} मि.`);
    const t=timeText(measured(s));if(t)bits.push(`मापन ${t}`);
    return bits.join(' • ');
  });
  const intro=placeMatches.length
    ?'तपाईंले सोधेको स्थानसँग मिल्ने official स्टेशन विवरण:'
    :'अहिले जोखिम/निगरानीमा रहेका official नदी स्टेशन र स्थान:';
  return `${intro}\n${lines.join('\n')}${selected.length>10?`\n… थप ${selected.length-10} स्टेशन छन्।`:''}\nस्रोत: BIPAD/DHM official realtime data।`;
}

function installAnswerUpgrade(){
  if(!window.SathiFloodAI||typeof window.SathiFloodAI.answer!=='function'){
    setTimeout(installAnswerUpgrade,120);return;
  }
  if(window.SathiFloodAI.__placeUpgrade)return;
  const original=window.SathiFloodAI.answer.bind(window.SathiFloodAI);
  window.SathiFloodAI.answer=q=>detailedPlaceAnswer(q)||original(q);
  window.SathiFloodAI.__placeUpgrade=true;
}

function addMessage(text,type='ai'){
  const msgs=document.getElementById('sathiFloodMsgs');
  if(!msgs)return;
  const d=document.createElement('div');
  d.className=`sathiMsg ${type}`;
  d.textContent=String(text||'');
  msgs.appendChild(d);
  msgs.scrollTop=msgs.scrollHeight;
}

function openPanel(){
  document.getElementById('sathiFloodOverlay')?.classList.add('open');
  const panel=document.getElementById('sathiFloodPanel');
  if(panel){
    panel.classList.add('open');
    panel.setAttribute('aria-hidden','false');
  }
}

function installNativeVoice(){
  const mic=document.getElementById('sathiMic');
  const panel=document.getElementById('sathiFloodPanel');
  if(!mic||!panel){setTimeout(installNativeVoice,120);return}
  if(window.__SATHI_NATIVE_UI_READY__)return;
  window.__SATHI_NATIVE_UI_READY__=true;

  const quick=document.getElementById('sathiQuick');
  const wake=document.createElement('button');
  wake.id='sathiAlwaysBtn';
  wake.type='button';
  wake.className='sathiAlwaysBtn';
  wake.setAttribute('aria-pressed','false');
  if(quick)quick.appendChild(wake);

  const status=document.createElement('div');
  status.id='sathiNativeStatus';
  status.setAttribute('role','status');
  status.textContent=window.SathiNative
    ?'🎙️ माइक थिचेर बोल्नुहोस्। पहिलो पटक अनुमति दिएपछि “Ye Sathi” background wake पनि सक्रिय हुन्छ।'
    :'Voice सुविधा Android APK मा native रूपमा चल्छ।';
  const composer=document.getElementById('sathiComposer');
  if(composer)composer.before(status);

  const renderWake=()=>{
    let on=false;
    try{on=Boolean(window.SathiNative?.isAlwaysOn?.())}catch{}
    wake.setAttribute('aria-pressed',String(on));
    wake.textContent=on?'🎙️ Ye Sathi: सक्रिय':'🎙️ Ye Sathi: सक्रिय गर्नुहोस्';
  };
  renderWake();

  wake.addEventListener('click',()=>{
    if(!window.SathiNative){
      status.textContent='Always-on “Ye Sathi” Android APK मा मात्र उपलब्ध छ।';
      return;
    }
    let on=false;
    try{on=Boolean(window.SathiNative.isAlwaysOn())}catch{}
    try{window.SathiNative.setAlwaysOn(!on)}catch{}
    setTimeout(renderWake,500);
  });

  // WebView's Web Speech API is not dependable. On Android, stop the old
  // browser handler before it runs and use the native SpeechRecognizer bridge.
  document.addEventListener('click',event=>{
    const target=event.target?.closest?.('#sathiMic');
    if(!target||!window.SathiNative)return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    mic.classList.add('on');
    status.textContent='🎤 सुन्दैछु…';
    try{window.SathiNative.startVoiceInput()}catch{
      mic.classList.remove('on');
      status.textContent='माइक सुरु हुन सकेन।';
    }
  },true);

  const seen=new Set();
  window.addEventListener('sathi-native-transcript',event=>{
    const text=String(event?.detail?.text||'').trim();
    if(!text)return;
    const id=String(event?.detail?.id||text+'|'+Math.floor(Date.now()/3000));
    if(seen.has(id))return;
    seen.add(id);
    if(seen.size>40){const first=seen.values().next().value;seen.delete(first)}
    openPanel();
    mic.classList.remove('on');
    status.textContent=event?.detail?.wake?'🤖 “Ye Sathi” बाट प्रश्न प्राप्त भयो।':'✅ आवाज बुझियो।';
    addMessage(text,'user');
    let reply='अहिले उत्तर तयार गर्न सकिनँ।';
    try{reply=window.SathiFloodAI?.answer?.(text)||reply}catch{}
    addMessage(reply,'ai');
    try{window.SathiNative?.speak?.(reply)}catch{}
    renderWake();
  });

  window.addEventListener('sathi-native-partial',event=>{
    const text=String(event?.detail?.text||'').trim();
    if(text)status.textContent=`🎤 ${text}`;
  });

  window.addEventListener('sathi-native-state',event=>{
    const d=event?.detail||{};
    if(d.message)status.textContent=String(d.message);
    if(d.kind==='mic'&&!d.active)mic.classList.remove('on');
    renderWake();
  });

  // Keep the native rain monitor synced to the current FloodSafe point. GPS
  // points are marked followDevice=true so the foreground service can refresh
  // coordinates while the app UI is closed.
  const syncPoint=()=>{
    if(!window.SathiNative)return;
    try{
      const state=window.FloodSafeRain?.state;
      const point=state?.point;
      if(point&&Number.isFinite(Number(point.lat))&&Number.isFinite(Number(point.lon))){
        window.SathiNative.updateMonitoringPoint(Number(point.lat),Number(point.lon),point.kind==='gps');
      }
    }catch{}
  };
  for(const ev of['fscurrentlocation','fsfocuschange'])window.addEventListener(ev,()=>setTimeout(syncPoint,200));
  setTimeout(syncPoint,900);
}

function applyFloatingSathi(){
  const btn=document.getElementById('sathiFloodBtn');
  const panel=document.getElementById('sathiFloodPanel');
  if(!btn){setTimeout(applyFloatingSathi,120);return;}

  if(btn.parentElement!==document.body) document.body.appendChild(btn);
  btn.classList.add('sathiFloatingFab');

  if(!document.getElementById('sathiFloatingV3Style')){
    const style=document.createElement('style');
    style.id='sathiFloatingV3Style';
    style.textContent=`
#sathiFloodBtn.sathiFloatingFab{
  position:fixed!important;
  right:max(18px,env(safe-area-inset-right))!important;
  bottom:max(96px,calc(env(safe-area-inset-bottom) + 84px))!important;
  left:auto!important;
  top:auto!important;
  z-index:2147482998!important;
  margin:0!important;
  order:unset!important;
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:8px!important;
  min-height:48px!important;
  padding:12px 16px!important;
  border:1px solid rgba(255,255,255,.42)!important;
  border-radius:999px!important;
  background:linear-gradient(135deg,#0b6ff4,#315cf4)!important;
  color:#fff!important;
  box-shadow:0 14px 34px rgba(11,70,170,.34),0 4px 10px rgba(0,0,0,.12)!important;
  backdrop-filter:blur(10px);
  -webkit-backdrop-filter:blur(10px);
  font:800 13px/1.1 system-ui,-apple-system,Segoe UI,sans-serif!important;
  white-space:nowrap!important;
  transform:translateZ(0);
  transition:transform .18s ease,box-shadow .18s ease,opacity .18s ease!important;
}
#sathiFloodBtn.sathiFloatingFab:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 18px 40px rgba(11,70,170,.4),0 5px 12px rgba(0,0,0,.14)!important}
#sathiFloodBtn.sathiFloatingFab:active{transform:scale(.97)}
#sathiFloodBtn.sathiFloatingFab>span:first-child{font-size:18px;line-height:1}
#sathiFloodBtn.sathiFloatingFab .sathiDot{width:8px!important;height:8px!important;flex:0 0 8px!important;background:#67e8a5!important;box-shadow:0 0 0 3px rgba(103,232,165,.22),0 0 12px rgba(103,232,165,.75)!important}
#sathiFloodPanel.open~#sathiFloodBtn.sathiFloatingFab{opacity:0;pointer-events:none}
#sathiNativeStatus{padding:7px 11px;background:#f5fbff;border-top:1px solid #e4eef5;color:#31536b;font:600 11px/1.35 system-ui,-apple-system,Segoe UI,sans-serif}
#sathiQuick .sathiAlwaysBtn{border-color:#b8d8f2;background:#edf8ff;color:#0b5e9b;font-weight:800}
#sathiQuick .sathiAlwaysBtn[aria-pressed="true"]{background:#e7fff1;border-color:#9cd9b5;color:#176b3a}
@media(max-width:620px){
  #sathiFloodBtn.sathiFloatingFab{
    right:max(12px,env(safe-area-inset-right))!important;
    bottom:max(88px,calc(env(safe-area-inset-bottom) + 78px))!important;
    min-height:46px!important;
    padding:11px 14px!important;
    font-size:12px!important;
    max-width:calc(100vw - 24px)!important;
  }
}
@media(max-width:380px){
  #sathiFloodBtn.sathiFloatingFab{padding:11px 12px!important}
  #sathiFloodBtn.sathiFloatingFab>span:nth-child(2){max-width:118px;overflow:hidden;text-overflow:ellipsis}
}
`;
    document.head.appendChild(style);
  }

  const bottomNav=document.querySelector('nav.bottom,.bottom');
  const placeFab=()=>{
    if(!bottomNav)return;
    const r=bottomNav.getBoundingClientRect();
    if(r.height>0 && r.top<innerHeight){
      const gap=14;
      const lift=Math.max(84,Math.ceil(innerHeight-r.top)+gap);
      btn.style.setProperty('bottom',`max(${lift}px, calc(env(safe-area-inset-bottom) + ${lift-10}px))`,'important');
    }
  };
  placeFab();
  addEventListener('resize',placeFab,{passive:true});
  addEventListener('orientationchange',()=>setTimeout(placeFab,120),{passive:true});

  if(panel){
    const observer=new MutationObserver(()=>{
      btn.style.opacity=panel.classList.contains('open')?'0':'1';
      btn.style.pointerEvents=panel.classList.contains('open')?'none':'auto';
    });
    observer.observe(panel,{attributes:true,attributeFilter:['class']});
  }

  installAnswerUpgrade();
  installNativeVoice();
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyFloatingSathi,{once:true});
else applyFloatingSathi();
})();
