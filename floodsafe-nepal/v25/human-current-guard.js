(()=>{
'use strict';
if(window.__fsHumanCurrentGuardV8)return;window.__fsHumanCurrentGuardV8=true;
const $=id=>document.getElementById(id);
const PEOPLE='../../data/floodsafe-people-status.json',POLICE='../../data/floodsafe-police.json';
let busy=false,current=null,lastSourceCheck=0,repairQueued=false;
const lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
const pick=(ne,en)=>lang()==='en'?en:ne;
const ts=t=>{const n=+new Date(t||0);return Number.isFinite(n)?n:0};
const value=n=>Number.isFinite(Number(n))&&Number(n)>0?Number(n):null;
async function get(u,ms=6000){
  const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);
  try{
    const sep=u.includes('?')?'&':'?';
    const r=await fetch(u+sep+'_human='+Math.floor(Date.now()/5000),{
      cache:'no-store',credentials:'same-origin',signal:c.signal,headers:{accept:'application/json'}
    });
    if(!r.ok)throw Error('HTTP '+r.status);
    return await r.json();
  }finally{clearTimeout(to)}
}
function installVisibilityGuard(){
  if(document.getElementById('fsHumanVisibleGuard'))return;
  const s=document.createElement('style');s.id='fsHumanVisibleGuard';
  s.textContent='#humanStatsSection[hidden],#peopleStatsSection[hidden]{display:block!important}';
  document.head.appendChild(s);
}
function showSections(){
  installVisibilityGuard();
  for(const id of ['humanStatsSection','peopleStatsSection']){const e=$(id);if(e&&e.hidden)e.hidden=false}
}
function put(id,v){const e=$(id),s=String(v??'—');if(e&&e.textContent!==s)e.textContent=s}
function fmtTime(t){
  if(!ts(t))return'—';
  try{return new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{
    timeZone:'Asia/Kathmandu',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:false
  }).format(new Date(t))+' NPT'}catch{return'—'}
}
function checkTime(){
  if(!lastSourceCheck)return'—';
  try{return new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{
    timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false
  }).format(new Date(lastSourceCheck))+' NPT'}catch{return'—'}
}
function sourceName(s){
  if(lang()==='en')return s||'Verified source';
  return String(s||'पुष्टि स्रोत')
    .replace('Nepal Police via OnlineKhabar','नेपाल प्रहरी मार्फत अनलाइनखबर')
    .replace('Nepal Police','नेपाल प्रहरी')
    .replace('OnlineKhabar','अनलाइनखबर')
    .replace('Radio Nepal','रेडियो नेपाल');
}
function dataTime(st=current){
  if(!st)return null;
  const m=Math.max(ts(st.d?.time),ts(st.m?.time),ts(st.r?.time));
  return m?new Date(m).toISOString():null;
}
function freshness(){
  showSections();
  const dt=dataTime();
  const label=dt
    ?pick('डेटा अपडेट '+fmtTime(dt)+' • mirror जाँच '+checkTime(),
          'Data updated '+fmtTime(dt)+' • mirror checked '+checkTime())
    :pick('पुष्टि भएको मानव स्थिति mirror जाँच हुँदैछ…','Checking verified Human Status mirror…');
  put('humanFresh',label);put('peopleStatsFresh',label);
}
function apply(st=current){
  if(!st)return;
  showSections();
  for(const [id,v] of [
    ['homeDeaths',st.d?.value],['peopleBodies',st.d?.value],
    ['homeMissing',st.m?.value],['peopleMissing',st.m?.value],
    ['homeRescued',st.r?.value],['peopleRescued',st.r?.value]
  ])put(id,v);
  const title=(lang()==='en'?st.eventEn:st.eventNe)+' • '+pick('मानव स्थिति','Human Status');
  for(const id of ['humanStatsTitle','peopleStatsTitle'])put(id,title);
  const br=$('peopleBreakdown');
  if(br){
    const s=lang()==='en'
      ?`Deaths ${st.d?.value??'—'} (${sourceName(st.d?.source)}) • Missing ${st.m?.value??'—'} (${sourceName(st.m?.source)}) • Rescued ${st.r?.value??'—'} (${sourceName(st.r?.source)})`
      :`मृत्यु ${st.d?.value??'—'} (${sourceName(st.d?.source)}) • सम्पर्कविहीन ${st.m?.value??'—'} (${sourceName(st.m?.source)}) • उद्धार ${st.r?.value??'—'} (${sourceName(st.r?.source)})`;
    if(br.textContent!==s)br.textContent=s;
  }
  freshness();
}
function scheduleRepair(){
  if(repairQueued||!current)return;
  repairQueued=true;queueMicrotask(()=>{repairQueued=false;apply(current)});
}
function installHumanLock(){
  const ids=['humanStatsSection','peopleStatsSection','homeDeaths','peopleBodies','homeMissing','peopleMissing',
    'homeRescued','peopleRescued','humanStatsTitle','peopleStatsTitle','humanFresh','peopleStatsFresh','peopleBreakdown'];
  const roots=ids.map($).filter(Boolean);if(!roots.length)return;
  const obs=new MutationObserver(scheduleRepair);
  for(const e of roots)obs.observe(e,{childList:true,subtree:true,characterData:true,
    attributes:e.id==='humanStatsSection'||e.id==='peopleStatsSection',attributeFilter:['hidden']});
  window.__fsHumanLockObserver=obs;
}
function newerDeath(people,police,peopleTrusted){
  const pVal=peopleTrusted?value(people?.recovered_bodies):null;
  const pTime=peopleTrusted?(people?.recovered_update_iso||people?.recovered_update_time):null;
  const poVal=value(police?.total_deaths),poTime=police?.official_update_iso;
  if(pVal!==null&&(!poVal||ts(pTime)>=ts(poTime)))return{value:pVal,time:pTime,source:people?.recovered_source||'Verified source'};
  if(poVal!==null)return{value:poVal,time:poTime,source:police?.source||'Nepal Police'};
  return{value:null,time:null,source:'Verified source'};
}
async function syncLocal(){
  if(busy||document.hidden||!navigator.onLine)return;
  busy=true;
  try{
    const [p,po]=await Promise.allSettled([get(PEOPLE),get(POLICE)]);
    const people=p.status==='fulfilled'?p.value:null,police=po.status==='fulfilled'?po.value:null;
    lastSourceCheck=Date.now();
    const trusted=Number(people?.sync_schema)>=2&&people?.status==='event_scoped_authority_mirror';
    const d=newerDeath(people,police,trusted);
    const m=trusted?{value:value(people?.missing_minimum),time:people?.missing_update_time,source:people?.missing_source||'Verified source'}:{value:null,time:null,source:'Verified source'};
    const r=trusted?{value:value(people?.rescued_alive),time:people?.rescued_update_time,source:people?.rescued_source||'Verified source'}:{value:null,time:null,source:'Verified source'};
    current={d,m,r,eventNe:people?.event_ne||police?.event_ne||'हालको विपद्',eventEn:people?.event||police?.event||'Current disaster',
      syncSchema:Number(people?.sync_schema)||0,status:people?.status||'fallback'};
    window.__fsHumanMirrorState={...current,lastSourceCheck};
    apply(current);
  }catch{
    lastSourceCheck=Date.now();freshness();if(current)apply(current);
  }finally{busy=false}
}
function boot(){
  installVisibilityGuard();showSections();freshness();installHumanLock();syncLocal();
  setInterval(freshness,1000);setInterval(syncLocal,5000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)syncLocal()});
  window.addEventListener('online',syncLocal);
  window.addEventListener('storage',e=>{if(e.key==='fs23-lang'&&current)apply(current)});
  window.addEventListener('fs-language-change',()=>{if(current)apply(current)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();