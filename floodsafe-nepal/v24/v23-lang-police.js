(()=>{
'use strict';
if(window.__fsLangPoliceAutoV25)return;
window.__fsLangPoliceAutoV25=true;

const $=id=>document.getElementById(id);
const lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
const POLICE_URL='https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/floodsafe-police.json';
const POLICE_POLL_MS=30000;
const WATCH_MS=15000;
const STRUCTURAL_RELOAD_AFTER_MS=90000;
const RELOAD_COOLDOWN_MS=5*60*1000;
const OFFICIAL_RE=/bipadportal\.gov\.np\/api\/v1\/|hydrology\.gov\.np|dhm\.gov\.np|dor\.gov\.np/i;

let policeData=null,obs=null,applying=false,fetchBusy=false;
let lastPoliceAttempt=0,lastPoliceSuccess=0,lastPoliceSig='',lastRenderSig='';
let lastOfficialSuccess=Date.now(),lastKick=0,bootAt=Date.now();

function css(){if($('fs23LangPoliceCss'))return;const s=document.createElement('style');s.id='fs23LangPoliceCss';s.textContent=`
#fs23PoliceDeaths{margin-top:10px;border:1px solid #6b4539;border-left:5px solid #dc143c;border-radius:15px;padding:12px;background:linear-gradient(145deg,#241815,#17100f);color:#fffaf2}
#fs23PoliceDeaths .pdHead{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}#fs23PoliceDeaths h3{margin:0;font-size:18px;line-height:1.15}#fs23PoliceDeaths .pdBadge{font-size:10px;font-weight:900;padding:5px 8px;border-radius:999px;background:#14543d;color:#b9f0d4;white-space:nowrap}
#fs23PoliceDeaths .pdCause{margin-top:10px;border:1px solid #54382f;border-radius:12px;padding:11px;background:#120c0b}#fs23PoliceDeaths .pdCause small{display:block;color:#cdbab0;font-size:12px}#fs23PoliceDeaths .pdCause b{display:block;font-size:27px;margin-top:4px;color:#fff4dc}
#fs23PoliceDeaths .pdDistricts{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}#fs23PoliceDeaths .pdDistricts span{padding:6px 9px;border-radius:999px;background:#3b241e;border:1px solid #6a473b;font-size:12px;font-weight:800}
#fs23PoliceDeaths .pdMeta{margin-top:10px;color:#d2c1b8;font-size:12px;line-height:1.5}#fs23PoliceDeaths a{color:#8fe4c0;font-weight:800}.pdAuto{color:#8fe4c0;font-weight:800}.pdStale{color:#f6cf73;font-weight:800}
@media(max-width:900px){#fs23PoliceDeaths h3{font-size:21px}#fs23PoliceDeaths .pdCause b{font-size:32px}#fs23PoliceDeaths .pdDistricts span,#fs23PoliceDeaths .pdMeta{font-size:14px}}
`;document.head.appendChild(s)}

function setText(el,v){if(el&&el.textContent!==v)el.textContent=v}
function npClock(ts=Date.now()){try{return new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date(ts))+' NPT'}catch{return'—'}}
function fixDynamic(){
  if(applying)return;applying=true;
  const en=lang()==='en';
  try{
    setText($('gpsBtn'),en?'◎ Use my location':'◎ मेरो स्थान प्रयोग');
    setText($('centerBtn'),en?'✦ Choose location on map':'✦ नक्साको बीच छान्नुहोस्');
    const hero=document.querySelector('.hero');
    if(hero){
      setText(hero.querySelector('.ey'),en?'YOUR AREA FIRST':'तपाईंको क्षेत्र पहिले');
      setText(hero.querySelector('h2'),en?'Flood status around me':'मेरो वरिपरि बाढीको अवस्था');
      setText(hero.querySelector('p'),en?'With GPS, nearby rivers, official gauges, rainfall, alerts and roads are prioritised for your location.':'GPS प्रयोग गर्दा नजिकका खोला/नदी, DHM मापन स्टेशन, वर्षा, BIPAD चेतावनी र Department of Roads सडक अवस्थालाई प्राथमिकता दिइन्छ।');
      const lab=hero.querySelector('.controls label');setText(lab,en?'Radius':'वरिपरि');
    }
    const radius=$('radius');if(radius){[...radius.options].forEach(o=>{const n=parseInt(o.value,10);if(Number.isFinite(n))o.textContent=en?`${n} km`:`${n} किमि`})}
    const loc=$('locState');if(loc){const s=loc.textContent||'';if(en){
      if(/नक्साबाट छानिएको/.test(s))loc.textContent=s.replace(/नक्साबाट छानिएको/g,'Selected from map').replace(/किमि/g,'km');
      else if(/GPS स्थान|स्थान छानिएको/.test(s))loc.textContent='GPS location selected';
      else if(/स्थान छानिएको छैन/.test(s))loc.textContent='No location selected';
    }else{
      if(/Selected from map/i.test(s))loc.textContent=s.replace(/Selected from map/ig,'नक्साबाट छानिएको').replace(/km/g,'किमि');
      else if(/GPS location selected/i.test(s))loc.textContent='GPS स्थान छानिएको';
      else if(/No location selected/i.test(s))loc.textContent='स्थान छानिएको छैन';
    }}
    const gate=$('fs23AlertGate');if(gate&&en){const s=gate.textContent||'';
      if(/GPS\/स्थान छानेपछि/.test(s))gate.innerHTML='🔕 Sound checks start only <b>after GPS/location is selected</b>.';
      else if(/आवाज|बाढी जोखिम|सडक|टाढाको चेतावनी/.test(s))gate.innerHTML='🔕 Sound plays only for a <b>local HIGH ⚠️ / VERY HIGH 🔴 flood risk</b>. Roads, normal/rising rivers and distant warnings do not trigger sound.';
      gate.innerHTML=gate.innerHTML.replace(/नदी\/खोला safety distance/g,'river/stream safety distance').replace(/किमि/g,'km');
    }
    const alerts=$('alertsBtn'),sound=$('soundBtn');
    if(alerts){const on=localStorage.getItem('fs23-audio-enabled')==='1';setText(alerts,en?(on?'🔔 HIGH/VERY HIGH alerts enabled':'🔔 Enable HIGH/VERY HIGH alerts'):(on?'🔔 HIGH/VERY HIGH सूचना सक्रिय':'🔔 सूचना सक्रिय'))}
    if(sound)setText(sound,en?'♪ Test sound':'♪ ध्वनि परीक्षण');
    const back=$('fs23BackMap');if(back)setText(back,en?'🗺️ Back to map':'🗺️ नक्सामा फर्कनुहोस्');
    document.documentElement.lang=en?'en':'ne';
  }finally{applying=false}
}

function syncOldImpact(){
  if(!policeData)return;
  const dead=$('deadV'),note=$('impactNote');if(!dead||!note)return;
  const s=(note.textContent||'')+' '+(dead.textContent||'');
  if(/Nepal Police|नेपाल प्रहरी|९५|95|100|१००/.test(s)){
    dead.textContent=String(policeData.total_deaths);
    const en=lang()==='en';
    note.innerHTML=en
      ?`BIPAD's aggregated loss total may sync later. Nepal Police confirms <b>${policeData.total_deaths} deaths</b> in the ${policeData.event} as of ${policeData.official_update_time}. <a href="${policeData.source_url}" target="_blank" rel="noopener" style="color:#9fe6c4">Nepal Police source</a>`
      :`BIPAD को aggregated loss total ढिलो sync हुन सक्छ। नेपाल प्रहरीले ${policeData.official_update_bs}, ${policeData.official_update_time} सम्म ${policeData.event_ne}मा <b>${policeData.total_deaths} मृत्यु</b> पुष्टि गरेको छ। <a href="${policeData.source_url}" target="_blank" rel="noopener" style="color:#9fe6c4">नेपाल प्रहरी स्रोत</a>`;
  }
}

function updateCheckedLabel(){
  const el=$('fsPoliceChecked');if(!el)return;
  const en=lang()==='en';
  if(!lastPoliceSuccess){el.textContent=en?'waiting for network':'नेटवर्क पर्खिँदै';el.className='pdStale';return}
  const age=Math.max(0,Math.floor((Date.now()-lastPoliceSuccess)/1000));
  el.className=age>90?'pdStale':'pdAuto';
  el.textContent=(en?'checked ':'जाँच ')+(age<5?(en?'just now':'अहिले'):(age<60?age+(en?'s ago':' से. अघि'):Math.floor(age/60)+(en?'m ago':' मिनेट अघि')))+' • '+npClock(lastPoliceSuccess);
}

function policePanel(force=false){
  let p=$('fs23PoliceDeaths');if(!p){p=document.createElement('section');p.id='fs23PoliceDeaths';const anchor=$('fs23hazards')||document.querySelector('.hero');if(anchor)anchor.insertAdjacentElement('afterend',p);else document.querySelector('.side')?.appendChild(p)}
  if(!p)return;
  const en=lang()==='en',d=policeData;
  const sig=(en?'en':'ne')+'|'+(d?`${d.total_deaths}|${d.source_url}|${d.official_update_time}|${JSON.stringify(d.districts||[])}`:'loading');
  if(!force&&sig===lastRenderSig){updateCheckedLabel();return}
  lastRenderSig=sig;
  if(!d){p.innerHTML=`<div class="pdHead"><h3>${en?'Nepal Police • verified fatalities':'नेपाल प्रहरी • पुष्टि मृत्यु'}</h3><span class="pdBadge">${en?'OFFICIAL SOURCE':'आधिकारिक स्रोत'}</span></div><div class="pdMeta">${en?'Loading latest Nepal Police verified bulletin…':'नेपाल प्रहरीको पछिल्लो पुष्टि विवरण लोड हुँदैछ…'}<br><span id="fsPoliceChecked" class="pdStale"></span></div>`;updateCheckedLabel();return}
  const districts=(d.districts||[]).map(x=>`<span>${en?x.name:x.name_ne}: <b>${x.deaths}</b></span>`).join('');
  const sourceTime=(d.official_update_time||'—');
  p.innerHTML=`<div class="pdHead"><h3>${en?'Nepal Police • verified fatalities':'नेपाल प्रहरी • पुष्टि मृत्यु'}</h3><span class="pdBadge">${en?'VERIFIED':'पुष्टि'}</span></div>
  <div class="pdCause"><small>${en?'Cause / event':'कारण / घटना'}</small><b>${en?d.event:d.event_ne} — ${d.total_deaths} ${en?'deaths':'मृत्यु'}</b></div>
  <div class="pdDistricts">${districts}</div>
  <div class="pdMeta">${en?'Official update (Nepal time)':'आधिकारिक अपडेट (नेपाल समय)'}: ${d.official_update_bs||'—'} • ${sourceTime}<br>${en?'App auto-check':'एपको स्वतः जाँच'}: <span id="fsPoliceChecked" class="pdAuto"></span><br>${en?'Source':'स्रोत'}: <a href="${d.source_url}" target="_blank" rel="noopener">Nepal Police</a><br>${en?'The official update time changes only when Nepal Police publishes a newer verified bulletin. The app keeps checking automatically.':'आधिकारिक अपडेट समय नेपाल प्रहरीले नयाँ पुष्टि बुलेटिन प्रकाशित गरेपछि मात्र बदलिन्छ। एपले डेटा स्वतः जाँच गरिरहन्छ।'}</div>`;
  updateCheckedLabel();syncOldImpact();
}

function validPolice(d){return d&&Number.isFinite(Number(d.total_deaths))&&typeof d.source_url==='string'&&d.source_url.includes('nepalpolice')&&typeof d.official_update_time==='string'}
async function fetchPolice(force=false){
  const now=Date.now();if(fetchBusy)return;
  if(!force&&now-lastPoliceAttempt<10000)return;
  fetchBusy=true;lastPoliceAttempt=now;
  try{
    // Shared 30-second cache key: millions of users can reuse the same CDN object instead of a unique URL per phone.
    const bucket=Math.floor(now/POLICE_POLL_MS);
    const r=await fetch(POLICE_URL+'?live='+bucket,{cache:'no-store'});
    if(!r.ok)throw Error('HTTP '+r.status);
    const d=await r.json();if(!validPolice(d))throw Error('invalid verified police payload');
    lastPoliceSuccess=Date.now();
    const sig=`${d.total_deaths}|${d.source_url}|${d.official_update_time}|${JSON.stringify(d.districts||[])}`;
    policeData=d;
    if(sig!==lastPoliceSig){lastPoliceSig=sig;lastRenderSig='';policePanel(true);syncOldImpact()}else{policePanel(false)}
  }catch(e){console.warn('police data',e);updateCheckedLabel()}
  finally{fetchBusy=false}
}

// Track successful official API responses. This sits around the current fetch chain and does not change responses.
const trackedFetch=window.fetch.bind(window);
window.fetch=async function(...args){
  const r=await trackedFetch(...args);
  try{const u=String(args[0]?.url||args[0]||'');if(r.ok&&OFFICIAL_RE.test(u))lastOfficialSuccess=Date.now()}catch{}
  return r;
};

function kick(reason='watchdog'){
  if(document.hidden||!navigator.onLine)return;
  const now=Date.now();if(now-lastKick<10000)return;lastKick=now;
  try{$('refreshBtn')?.click()}catch{}
  fetchPolice(true);
  try{window.__fs?.map?.invalidateSize?.()}catch{}
  try{navigator.serviceWorker?.getRegistration?.().then(r=>r?.update?.()).catch(()=>{})}catch{}
  document.documentElement.dataset.floodsafeLastKick=reason;
}

function safeReload(reason){
  if(document.hidden||!navigator.onLine)return;
  const now=Date.now(),key='fs24-auto-reload-at',last=Number(sessionStorage.getItem(key)||0);
  if(now-last<RELOAD_COOLDOWN_MS)return;
  sessionStorage.setItem(key,String(now));
  console.warn('FloodSafe controlled recovery reload:',reason);
  location.reload();
}

function watchdog(){
  updateCheckedLabel();
  if(document.hidden||!navigator.onLine)return;
  const now=Date.now(),map=!!document.querySelector('.leaflet-container'),loading=$('loading');
  const loadingVisible=!!loading&&getComputedStyle(loading).display!=='none';
  if(now-bootAt>STRUCTURAL_RELOAD_AFTER_MS&&(!map||loadingVisible)){safeReload(!map?'map-missing':'loading-stuck');return}
  if(now-lastOfficialSuccess>120000)kick('official-feed-stale');
  if(!lastPoliceSuccess||now-lastPoliceSuccess>90000)fetchPolice(true);
}

function hook(){
  css();fixDynamic();policePanel(true);fetchPolice(true);
  document.addEventListener('click',e=>{if(e.target.closest?.('.fs23lang'))setTimeout(()=>{fixDynamic();lastRenderSig='';policePanel(true)},80)});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)kick('visible-again')});
  window.addEventListener('online',()=>kick('back-online'));
  window.addEventListener('focus',()=>kick('window-focus'));
  window.addEventListener('pageshow',()=>kick('pageshow'));
  if(!obs){let mutTimer=null;obs=new MutationObserver(()=>{clearTimeout(mutTimer);mutTimer=setTimeout(()=>{fixDynamic();policePanel(false);syncOldImpact()},120)});obs.observe(document.body,{childList:true,subtree:true,characterData:true})}
  setInterval(()=>{fixDynamic();updateCheckedLabel()},2000);
  setInterval(()=>fetchPolice(false),POLICE_POLL_MS);
  setInterval(watchdog,WATCH_MS);
  // Ask the browser to check for a newer service worker periodically; an updated SW can refresh the open app without user action.
  setInterval(()=>{try{navigator.serviceWorker?.getRegistration?.().then(r=>r?.update?.()).catch(()=>{})}catch{}},10*60*1000);
  window.__floodsafeAutoUpdate={fetchPolice:()=>fetchPolice(true),kick,lastPoliceSuccess:()=>lastPoliceSuccess,lastOfficialSuccess:()=>lastOfficialSuccess};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(hook,600));else setTimeout(hook,600);
})();
