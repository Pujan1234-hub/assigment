(()=>{
'use strict';
if(window.__fsImpactFreshV11)return;window.__fsImpactFreshV11=true;
const $=id=>document.getElementById(id);
const PEOPLE='../../data/floodsafe-people-status.json',POLL=5000;
let current=null,lastSignature='',busy=false,repairQueued=false,lastMirrorCheck=0;
const lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne';
const tr=(ne,en)=>lang()==='en'?en:ne;
const ts=v=>{const n=+new Date(v||0);return Number.isFinite(n)?n:0};
const positive=v=>Number.isInteger(Number(v))&&Number(v)>0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const put=(id,v)=>{const e=$(id),s=String(v??'—');if(e&&e.textContent!==s)e.textContent=s};
const signature=j=>JSON.stringify([
  j?.sync_schema,j?.status,j?.recovered_bodies,j?.missing_minimum,j?.rescued_alive,
  j?.recovered_update_time,j?.missing_update_time,j?.rescued_update_time,
  j?.recovered_source,j?.missing_source,j?.rescued_source
]);
function validUrl(u){try{const x=new URL(String(u||''),location.href);return x.protocol==='http:'||x.protocol==='https:'}catch{return false}}
function validSnapshot(j){
  if(!j||typeof j!=='object'||Number(j.sync_schema)<2||j.status!=='event_scoped_authority_mirror')return false;
  const metrics=[
    ['recovered_bodies','recovered_source','recovered_source_url','recovered_update_time','death_time_basis'],
    ['missing_minimum','missing_source','missing_source_url','missing_update_time','missing_time_basis'],
    ['rescued_alive','rescued_source','rescued_source_url','rescued_update_time','rescued_time_basis']
  ];
  for(const [v,s,u,t,b] of metrics){
    if(!positive(j[v])||!String(j[s]||'').trim()||!validUrl(j[u])||!ts(j[t])||!String(j[b]||'').trim())return false;
    if(String(j[t])===String(j.last_checked_utc||''))return false;
  }
  return true;
}
function metricScore(j){return Math.max(ts(j?.recovered_update_time),ts(j?.missing_update_time),ts(j?.rescued_update_time))}
async function get(ms=8000){
  const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);
  try{
    const r=await fetch(PEOPLE+'?human_live='+Date.now()+'_'+Math.random().toString(36).slice(2),{
      cache:'no-store',credentials:'same-origin',signal:c.signal,
      headers:{'Cache-Control':'no-cache','Pragma':'no-cache','Accept':'application/json'}
    });
    if(!r.ok)throw Error('HTTP '+r.status);
    const j=await r.json();
    if(!validSnapshot(j))throw Error('Human Status mirror contract rejected');
    return j;
  }finally{clearTimeout(to)}
}
function fmt(t){
  if(!ts(t))return'—';
  try{return new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{
    timeZone:'Asia/Kathmandu',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false
  }).format(new Date(t))+' NPT'}catch{return String(t)}
}
function sourceBox(parentId,source,url,time){
  const p=$(parentId)?.closest('.impactStat');if(!p)return;
  let e=p.querySelector('.impactSource');if(!e){e=document.createElement('div');e.className='impactSource';p.appendChild(e)}
  const label=tr('स्रोत','Source'),timeLabel=tr('समय','Time');
  const link=validUrl(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(source||'—')}</a>`:esc(source||'—');
  const h=`${label}: ${link}${time?`<br>${timeLabel}: ${esc(fmt(time))}`:''}`;
  if(e.innerHTML!==h)e.innerHTML=h;
}
function apply(j){
  current=j;
  const d=j.recovered_bodies,m=j.missing_minimum,r=j.rescued_alive;
  put('impactDeaths',d);put('impactMissing',m);put('impactRescued',r);
  put('impactEvent',lang()==='en'?(j.event||'Bhotekoshi flash flood'):(j.event_ne||j.event||'भोटेकोशी आकस्मिक बाढी'));
  const newest=metricScore(j),checked=ts(j.last_checked_utc),delayed=checked?Date.now()-checked>15*60*1000:true;
  put('impactFresh',tr(
    `पछिल्लो प्रमाणित आँकडा: ${fmt(newest)} • mirror जाँच: ${checked?fmt(checked):'—'} • हरेक ५ सेकेन्डमा स्वतः जाँच${delayed?' • server sync ढिलो':''}`,
    `Latest verified figures: ${fmt(newest)} • mirror checked: ${checked?fmt(checked):'—'} • auto-check every 5 seconds${delayed?' • server sync delayed':''}`
  ));
  sourceBox('impactDeaths',j.recovered_source,j.recovered_source_url,j.recovered_update_time);
  sourceBox('impactMissing',j.missing_source,j.missing_source_url,j.missing_update_time);
  sourceBox('impactRescued',j.rescued_source,j.rescued_source_url,j.rescued_update_time);
  put('impactDetail',tr(
    'Server-side पुष्टि mirror मात्र • मृत्यु/उद्धार cumulative guard • सम्पर्कविहीन संख्या नयाँ authoritative report अनुसार घट्न वा बढ्न सक्छ • browserबाट बाहिरी Human Status API direct call हुँदैन।',
    'Verified server-side mirror only • cumulative guards for deaths/rescued • missing may rise or fall with a newer authoritative report • no direct external Human Status API call from the browser.'
  ));
  lastMirrorCheck=Date.now();lastSignature=signature(j);
  window.__fsImpactHumanMirrorState={
    schema:Number(j.sync_schema),status:j.status,deaths:d,missing:m,rescued:r,
    deathTime:j.recovered_update_time,missingTime:j.missing_update_time,rescuedTime:j.rescued_update_time,
    deathSource:j.recovered_source,missingSource:j.missing_source,rescuedSource:j.rescued_source,
    lastChecked:j.last_checked_utc,mirrorCheckedAt:new Date(lastMirrorCheck).toISOString()
  };
}
function scheduleRepair(){if(repairQueued||!current)return;repairQueued=true;queueMicrotask(()=>{repairQueued=false;apply(current)})}
function installLock(){
  const roots=['impactDeaths','impactMissing','impactRescued','impactEvent','impactFresh'].map($).filter(Boolean);
  if(!roots.length)return;
  const obs=new MutationObserver(scheduleRepair);
  for(const e of roots)obs.observe(e,{childList:true,subtree:true,characterData:true});
  window.__fsImpactHumanLockObserver=obs;
}
async function sync(){
  if(busy||document.hidden||!navigator.onLine)return;busy=true;
  try{
    const j=await get(),sig=signature(j);
    if(!current||metricScore(j)>=metricScore(current)||sig!==lastSignature){apply(j);window.dispatchEvent(new CustomEvent('fshumanupdate',{detail:{current:j}}))}
  }catch{
    if(!current)put('impactFresh',tr(
      'पुष्टि Human Status mirror अहिले उपलब्ध छैन • गलत/पुरानो संख्या देखाइँदैन • फेरि स्वतः जाँच हुँदैछ',
      'Verified Human Status mirror unavailable • stale/untrusted figures are hidden • retrying automatically'
    ));
  }finally{busy=false}
}
function boot(){
  installLock();sync();setInterval(sync,POLL);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync()});
  window.addEventListener('online',sync);window.addEventListener('focus',sync);
  window.addEventListener('fslanguage',()=>{if(current)apply(current)});
  window.FloodSafeImpact={sync,get current(){return current},get score(){return metricScore(current)},validSnapshot};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();