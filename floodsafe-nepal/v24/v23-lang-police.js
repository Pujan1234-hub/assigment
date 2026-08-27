(()=>{
'use strict';
const $=id=>document.getElementById(id);
const lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
const t=(ne,en)=>lang()==='en'?en:ne;
let policeData=null,obs=null,applying=false;

function css(){if($('fs23LangPoliceCss'))return;const s=document.createElement('style');s.id='fs23LangPoliceCss';s.textContent=`
#fs23PoliceDeaths{margin-top:10px;border:1px solid #6b4539;border-left:5px solid #dc143c;border-radius:15px;padding:12px;background:linear-gradient(145deg,#241815,#17100f);color:#fffaf2}
#fs23PoliceDeaths .pdHead{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}#fs23PoliceDeaths h3{margin:0;font-size:18px;line-height:1.15}#fs23PoliceDeaths .pdBadge{font-size:10px;font-weight:900;padding:5px 8px;border-radius:999px;background:#14543d;color:#b9f0d4;white-space:nowrap}
#fs23PoliceDeaths .pdCause{margin-top:10px;border:1px solid #54382f;border-radius:12px;padding:11px;background:#120c0b}#fs23PoliceDeaths .pdCause small{display:block;color:#cdbab0;font-size:12px}#fs23PoliceDeaths .pdCause b{display:block;font-size:27px;margin-top:4px;color:#fff4dc}
#fs23PoliceDeaths .pdDistricts{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}#fs23PoliceDeaths .pdDistricts span{padding:6px 9px;border-radius:999px;background:#3b241e;border:1px solid #6a473b;font-size:12px;font-weight:800}
#fs23PoliceDeaths .pdMeta{margin-top:10px;color:#d2c1b8;font-size:12px;line-height:1.5}#fs23PoliceDeaths a{color:#8fe4c0;font-weight:800}
@media(max-width:900px){#fs23PoliceDeaths h3{font-size:21px}#fs23PoliceDeaths .pdCause b{font-size:32px}#fs23PoliceDeaths .pdDistricts span,#fs23PoliceDeaths .pdMeta{font-size:14px}}
`;document.head.appendChild(s)}

function setText(el,v){if(el&&el.textContent!==v)el.textContent=v}
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
      else if(/GPS|स्थान/.test(s)&&!/Selected|GPS location|No location/i.test(s))loc.textContent='GPS location selected';
    }else{
      if(/Selected from map/i.test(s))loc.textContent=s.replace(/Selected from map/ig,'नक्साबाट छानिएको').replace(/km/g,'किमि');
      else if(/GPS location selected/i.test(s))loc.textContent='GPS स्थान छानिएको';
    }}
    const gate=$('fs23AlertGate');if(gate&&en){const s=gate.textContent||'';
      if(/आवाज|बाढी जोखिम|सडक|टाढाको चेतावनी/.test(s))gate.innerHTML='🔕 Sound plays only for a <b>local HIGH ⚠️ / VERY HIGH 🔴 flood risk</b>. Roads, normal/rising rivers and distant warnings do not trigger sound.';
      if(/GPS\/स्थान छानेपछि/.test(s))gate.innerHTML='🔕 Sound checks start only <b>after GPS/location is selected</b>.';
      gate.innerHTML=gate.innerHTML.replace(/नदी\/खोला safety distance/g,'river/stream safety distance').replace(/किमि/g,'km');
    }
    const alerts=$('alertsBtn'),sound=$('soundBtn');
    if(alerts){const on=localStorage.getItem('fs23-audio-enabled')==='1';setText(alerts,en?(on?'🔔 HIGH/VERY HIGH alerts enabled':'🔔 Enable HIGH/VERY HIGH alerts'):(on?'🔔 HIGH/VERY HIGH सूचना सक्रिय':'🔔 सूचना सक्रिय'))}
    if(sound)setText(sound,en?'♪ Test sound':'♪ ध्वनि परीक्षण');
    const back=$('fs23BackMap');if(back)setText(back,en?'🗺️ Back to map':'🗺️ नक्सामा फर्कनुहोस्');
    document.querySelectorAll('.side [data-ux-ne]').forEach(()=>{});
    document.documentElement.lang=en?'en':'ne';
  }finally{applying=false}
}

function policePanel(){
  let p=$('fs23PoliceDeaths');if(!p){p=document.createElement('section');p.id='fs23PoliceDeaths';const anchor=$('fs23hazards')||document.querySelector('.hero');if(anchor)anchor.insertAdjacentElement('afterend',p);else document.querySelector('.side')?.appendChild(p)}
  if(!p)return;
  const en=lang()==='en',d=policeData;
  if(!d){p.innerHTML=`<div class="pdHead"><h3>${en?'Nepal Police • verified fatalities':'नेपाल प्रहरी • पुष्टि मृत्यु'}</h3><span class="pdBadge">${en?'OFFICIAL SOURCE':'आधिकारिक स्रोत'}</span></div><div class="pdMeta">${en?'Loading latest Nepal Police verified bulletin…':'नेपाल प्रहरीको पछिल्लो पुष्टि विवरण लोड हुँदैछ…'}</div>`;return}
  const districts=(d.districts||[]).map(x=>`<span>${en?x.name:x.name_ne}: <b>${x.deaths}</b></span>`).join('');
  p.innerHTML=`<div class="pdHead"><h3>${en?'Nepal Police • verified fatalities':'नेपाल प्रहरी • पुष्टि मृत्यु'}</h3><span class="pdBadge">${en?'VERIFIED':'पुष्टि'}</span></div>
  <div class="pdCause"><small>${en?'Cause / event':'कारण / घटना'}</small><b>${en?d.event:d.event_ne} — ${d.total_deaths} ${en?'deaths':'मृत्यु'}</b></div>
  <div class="pdDistricts">${districts}</div>
  <div class="pdMeta">${en?'Official update':'आधिकारिक अपडेट'}: ${d.official_update_bs||'—'} • ${d.official_update_time||'—'}<br>${en?'Source':'स्रोत'}: <a href="${d.source_url}" target="_blank" rel="noopener">Nepal Police</a><br>${en?'This panel shows only figures explicitly confirmed in the cited Nepal Police bulletin; it does not invent totals for causes not published there.':'यो कार्डमा नेपाल प्रहरीले स्रोतमा स्पष्ट पुष्टि गरेको संख्या मात्र देखाइन्छ; नछापिएको कारणको संख्या बनावटी रूपमा देखाइँदैन।'}</div>`;
}
async function fetchPolice(){try{const u='https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/floodsafe-police.json?t='+Date.now();const r=await fetch(u,{cache:'no-store'});if(r.ok){policeData=await r.json();policePanel()}}catch(e){console.warn('police data',e)}}

function hook(){
  css();fixDynamic();policePanel();fetchPolice();
  document.addEventListener('click',e=>{if(e.target.closest?.('.fs23lang'))setTimeout(()=>{fixDynamic();policePanel()},80)});
  if(!obs){obs=new MutationObserver(()=>{requestAnimationFrame(()=>{fixDynamic();policePanel()})});obs.observe(document.body,{childList:true,subtree:true,characterData:true})}
  setInterval(()=>{fixDynamic();policePanel()},700);
  setInterval(fetchPolice,5000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(hook,600));else setTimeout(hook,600);
})();
