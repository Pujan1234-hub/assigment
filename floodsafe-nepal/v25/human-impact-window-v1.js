(()=>{
'use strict';
if(window.__FS_HUMAN_IMPACT_WINDOW_V1__)return;
window.__FS_HUMAN_IMPACT_WINDOW_V1__=true;
const DAYS=13,DAY=86400000,FALLBACK='../../data/floodsafe-people-status.json',LIVE='https://camkoacuokffryyrygda.supabase.co/functions/v1/human-status-safe-live';
const $=id=>document.getElementById(id);let timer=0;
const t=v=>{const x=Date.parse(v||'');return Number.isFinite(x)?x:null};
const num=v=>{const x=Number(v);return Number.isFinite(x)&&x>0?x:null};
function metrics(j){return [num(j?.recovered_bodies),num(j?.missing_minimum),num(j?.rescued_alive)].some(Boolean)}
function eventKey(j){return String(j?.event||j?.event_ne||'').trim().toLowerCase()}
function startTime(j){
  const explicit=t(j?.event_start_iso||j?.event_start||j?.started_at);if(explicit)return explicit;
  const reports=[t(j?.recovered_update_iso||j?.recovered_update_time),t(j?.missing_update_time),t(j?.rescued_update_time),t(j?.official_update_iso)].filter(Boolean).sort((a,b)=>a-b);
  return reports[0]||null;
}
async function get(url){const c=new AbortController(),to=setTimeout(()=>c.abort(),7000);try{const r=await fetch(url+(url.includes('?')?'&':'?')+'_impactwindow='+Date.now(),{cache:'no-store',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(to)}}
function setVisible(show,reason=''){
  const el=$('impact');if(!el)return;
  el.classList.toggle('fsImpactExpired',!show);el.hidden=!show;
  el.dataset.windowReason=reason;
}
function installStyle(){if($('fsImpactWindowStyle'))return;const s=document.createElement('style');s.id='fsImpactWindowStyle';s.textContent='#impact.fsImpactExpired{display:none!important}';document.head.appendChild(s)}
async function check(){
  installStyle();if(!$('impact'))return;
  const results=await Promise.allSettled([get(LIVE),get(FALLBACK)]);const live=results[0].status==='fulfilled'?results[0].value:null,fb=results[1].status==='fulfilled'?results[1].value:null;
  let j=null;
  if(live&&metrics(live))j=live;else if(fb&&metrics(fb))j=fb;
  if(!j){setVisible(false,'no-human-impact');return}
  let start=startTime(j);if(fb&&eventKey(fb)&&eventKey(j)===eventKey(fb)&&t(fb.event_start_iso))start=t(fb.event_start_iso);
  const windowDays=Number(j?.display_window_days||fb?.display_window_days||DAYS)||DAYS;
  if(!start){setVisible(true,'recent-event-start-unknown');return}
  const age=Math.max(0,Date.now()-start);const show=age<windowDays*DAY;
  setVisible(show,show?'within-display-window':`older-than-${windowDays}-days`);
  window.__fsHumanImpactWindow={show,event:eventKey(j),start:new Date(start).toISOString(),ageDays:age/DAY,windowDays,checkedAt:new Date().toISOString()};
}
function schedule(){clearTimeout(timer);timer=setTimeout(async()=>{try{await check()}catch{}schedule()},60000)}
function boot(){check().catch(()=>{}).finally(schedule);for(const ev of['online','focus','pageshow','fshumanupdate'])window.addEventListener(ev,()=>setTimeout(()=>check().catch(()=>{}),150))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
