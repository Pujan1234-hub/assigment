(()=>{'use strict';
if(window.__fsImpactFreshV3)return;window.__fsImpactFreshV3=true;
const $=id=>document.getElementById(id),PEOPLE='../../data/floodsafe-people-status.json';let last=0;
const ts=v=>{const n=+new Date(v||0);return Number.isFinite(n)?n:0};
async function get(u,ms=7000){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(u+(u.includes('?')?'&':'?')+'_if3='+Date.now(),{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(t)}}
function fmt(t){if(!ts(t))return'—';try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(t))+' NPT'}catch{return String(t)}}
function apply(j){const d=j?.recovered_bodies??null,m=j?.missing_minimum??null,r=j?.rescued_alive??null,newest=[j?.recovered_update_time,j?.missing_update_time,j?.rescued_update_time,j?.updated_date].map(ts).filter(Boolean).sort((a,b)=>b-a)[0]||0;if($('impactDeaths'))$('impactDeaths').textContent=d??'—';if($('impactMissing'))$('impactMissing').textContent=m??'—';if($('impactRescued'))$('impactRescued').textContent=r??'—';if($('impactEvent'))$('impactEvent').textContent=j?.event_ne||j?.event||'बाढी';if($('impactFresh'))$('impactFresh').textContent=newest?'Updated • '+fmt(newest):'Latest update';if($('impactDetail'))$('impactDetail').textContent=''}
async function sync(force=false){if(!force&&Date.now()-last<10000)return;last=Date.now();try{apply(await get(PEOPLE))}catch{if($('impactFresh'))$('impactFresh').textContent='Impact data refresh unavailable'}}
function boot(){sync(true);setInterval(sync,12000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync(true)});window.addEventListener('online',()=>sync(true))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();