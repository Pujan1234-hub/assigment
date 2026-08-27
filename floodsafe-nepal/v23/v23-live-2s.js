(()=>{
'use strict';
const API='https://bipadportal.gov.np/api/v1/';
const POLL=2000;
const $=id=>document.getElementById(id);
const lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
const T=(ne,en)=>lang()==='en'?en:ne;
const rows=j=>Array.isArray(j)?j:(j?.results||j?.data||j?.objects||[]);
let busy=false,lastCheck=null,incidents=[];

function when(o){return o?.incidentOn||o?.createdOn||o?.modifiedOn||o?.recordedDate||o?.date||null}
function recent24(o){const t=+new Date(when(o)||0);return Number.isFinite(t)&&Date.now()-t>=-3600000&&Date.now()-t<=86400000}
function hazard(o){let s='';try{s=JSON.stringify(o||{}).toLowerCase()}catch{};if(/landslide|पहिरो|भूस्खलन/.test(s))return'landslide';if(/flash flood|flood|बाढी|डुबान/.test(s))return'flood';if(/lightning|thunderbolt|चट्याङ|बज्रपात/.test(s))return'lightning';if(/forest fire|wildfire|डढेलो|वन आगलागी/.test(s))return'fire';return'other'}
function setText(id,v){const e=$(id);if(e&&e.textContent!==v)e.textContent=v}
function refreshLabels(){
  setText('fs23hazardAge',T('२ से. refresh','2s refresh'));
  if(lastCheck){const sec=Math.max(0,Math.floor((Date.now()-lastCheck)/1000));setText('fs23check',T(`हरेक २ से. • ${sec} से. अघि`,`Every 2s • ${sec}s ago`))}
  const cd=$('countdown');if(cd)cd.textContent='2';
}
function renderHazardCounts(){
  const rec=incidents.filter(recent24),count=h=>rec.filter(x=>hazard(x)===h).length;
  setText('fs23landN',String(count('landslide')));
  setText('fs23floodN',String(count('flood')));
  setText('fs23lightN',String(count('lightning')));
  setText('fs23fireN',String(count('fire')));
  refreshLabels();
}
async function updatePolice(){
  try{
    const r=await fetch('https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/floodsafe-police.json?t='+Date.now(),{cache:'no-store'});
    if(!r.ok)return;const d=await r.json(),p=$('fs23PoliceDeaths');if(!p||!d?.total_deaths)return;
    const en=lang()==='en';
    const districts=(d.districts||[]).map(x=>`<span>${en?x.name:x.name_ne}: <b>${x.deaths}</b></span>`).join('');
    p.innerHTML=`<div class="pdHead"><h3>${en?'Nepal Police • verified fatalities':'नेपाल प्रहरी • पुष्टि मृत्यु'}</h3><span class="pdBadge">${en?'VERIFIED':'पुष्टि'}</span></div><div class="pdCause"><small>${en?'Cause / event':'कारण / घटना'}</small><b>${en?d.event:d.event_ne} — ${d.total_deaths} ${en?'deaths':'मृत्यु'}</b></div><div class="pdDistricts">${districts}</div><div class="pdMeta">${en?'Official update':'आधिकारिक अपडेट'}: ${d.official_update_bs||'—'} • ${d.official_update_time||'—'}<br>${en?'Source':'स्रोत'}: <a href="${d.source_url}" target="_blank" rel="noopener">Nepal Police</a><br><span style="color:#9fe6c4">${en?'App source check: every 2 seconds':'App स्रोत जाँच: हरेक २ सेकेन्ड'}</span></div>`;
    const dead=$('deadV');if(dead)dead.textContent=String(d.total_deaths);
  }catch(e){console.warn('2s police sync',e)}
}
async function poll(){
  if(busy||document.hidden)return;busy=true;
  try{
    const urls=[
      API+'river-stations/?limit=650',API+'rain-stations/?limit=650',API+'alert/?limit=250&ordering=-createdOn',API+'highway/?limit=500',API+'incident/?limit=500&ordering=-incidentOn'
    ];
    const res=await Promise.allSettled(urls.map(u=>fetch(u,{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(r.status))));
    if(res[4]?.status==='fulfilled'){incidents=rows(res[4].value);renderHazardCounts()}
    const refresh=$('refreshBtn');if(refresh&&typeof refresh.click==='function')refresh.click();
    lastCheck=Date.now();refreshLabels();updatePolice();
  }catch(e){console.warn('2s live sync',e)}finally{busy=false}
}
function init(){
  refreshLabels();updatePolice();poll();
  setInterval(refreshLabels,500);
  setInterval(poll,POLL);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,900));else setTimeout(init,900);
})();
