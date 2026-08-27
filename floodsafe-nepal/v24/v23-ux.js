(()=>{
'use strict';
const $=id=>document.getElementById(id);
const rows=j=>Array.isArray(j)?j:(j?.results||j?.data||j?.objects||[]);
let incidentFeed=[];
let mapHooked=false;

function lang(){return localStorage.getItem('fs23-lang')==='en'?'en':'ne'}
function recent24(o){const raw=o?.incidentOn||o?.createdOn||o?.modifiedOn||o?.date||o?.recordedDate;const t=+new Date(raw||0);return Number.isFinite(t)&&Date.now()-t>=-3600000&&Date.now()-t<=86400000}
function text(o){try{return JSON.stringify(o||{}).toLowerCase()}catch{return''}}
function isRoadAccident(o){return /road accident|traffic accident|vehicle accident|car accident|bus accident|truck accident|jeep accident|motorcycle accident|सवारी दुर्घटना|सडक दुर्घटना|यातायात दुर्घटना/.test(text(o))}
function deathCount(o){
  const vals=[];
  const walk=(x,depth=0)=>{
    if(!x||depth>5)return;
    if(Array.isArray(x)){x.forEach(v=>walk(v,depth+1));return}
    if(typeof x!=='object')return;
    for(const [k,v] of Object.entries(x)){
      const key=String(k).toLowerCase();
      if(/death|deceased|dead|मृत/.test(key)&&!/date|rate|reason|cause/.test(key)){
        const n=Number(v);if(Number.isFinite(n)&&n>=0&&n<10000)vals.push(n);
      }
      if(v&&typeof v==='object')walk(v,depth+1);
    }
  };
  walk(o);
  return vals.length?Math.max(...vals):null;
}
function captureIncidents(){
  if(window.__fs23UxFetch)return;window.__fs23UxFetch=true;
  const native=window.fetch.bind(window);
  window.fetch=async(...args)=>{
    const r=await native(...args);
    try{
      const u=String(args[0]?.url||args[0]||'');
      if(/bipadportal\.gov\.np\/api\/v1\/incident\//i.test(u)){
        const a=rows(await r.clone().json());
        if(a.length)incidentFeed=a;
      }
    }catch{}
    return r;
  };
}
async function seedIncidents(){
  try{
    const r=await fetch('https://bipadportal.gov.np/api/v1/incident/?limit=500&ordering=-incidentOn',{cache:'no-store'});
    if(r.ok){const a=rows(await r.json());if(a.length)incidentFeed=a}
  }catch{}
}

function css(){
  if($('fs23-ux-css'))return;
  const s=document.createElement('style');s.id='fs23-ux-css';s.textContent=`
  .fs23hazard[data-h="accident"]{box-shadow:inset 0 3px 0 #c8d1dd}
  .fs23accNote{display:block;margin-top:4px;font-size:10px;color:#c9b6ad;line-height:1.35}
  .fs23Jump{outline:3px solid #f0b64b!important;box-shadow:0 0 0 7px #f0b64b28!important;transition:.25s}
  #fs23BackMap{margin-top:10px;min-height:48px;width:100%;border:1px solid #8c6150;border-radius:12px;background:#2b1a16;color:#fff;font-weight:900;font-size:16px}
  @media(max-width:900px){
    .side{font-size:16px!important}.btn,.fs23lang,.controls select,.districtRow select{min-height:48px!important;font-size:16px!important}
    .fs23head h3{font-size:20px!important}.fs23cell small,.fs23hazard small{font-size:13px!important}.fs23cell b{font-size:19px!important}
    .fs23meta,.fs23note,.fs23accNote{font-size:14px!important;line-height:1.55!important}.fs23stationTop b{font-size:19px!important}
    .fs23stage{font-size:12px!important;padding:6px 9px!important}.hero h2{font-size:32px!important;line-height:1.05!important}
    .hero p{font-size:16px!important;line-height:1.55!important}.fs23hazard b{font-size:25px!important}
  }
  `;document.head.appendChild(s);
}

function ensureAccidentCard(){
  const grid=document.querySelector('#fs23hazards .fs23hazardGrid');if(!grid)return;
  let card=$('fs23accidentCard');
  if(!card){
    card=document.createElement('div');card.id='fs23accidentCard';card.className='fs23hazard';card.dataset.h='accident';
    card.innerHTML='<small id="fs23accidentLabel">सवारी दुर्घटना मृत्यु</small><b id="fs23accidentN">—</b><span class="fs23accNote" id="fs23accidentNote">BIPAD 24h</span>';
    grid.appendChild(card);
  }
  renderAccident();
}
function renderAccident(){
  if(!$('fs23accidentN'))return;
  const aa=incidentFeed.filter(x=>recent24(x)&&isRoadAccident(x));
  const known=aa.map(deathCount).filter(x=>x!==null);
  const deaths=known.reduce((a,b)=>a+b,0);
  const en=lang()==='en';
  $('fs23accidentLabel').textContent=en?'Car accident deaths':'सवारी दुर्घटना मृत्यु';
  $('fs23accidentN').textContent=known.length?String(deaths):'—';
  $('fs23accidentNote').textContent=known.length
    ?(en?`${aa.length} road-accident records • BIPAD 24h`:`${aa.length} दुर्घटना रेकर्ड • BIPAD २४ घण्टा`)
    :(en?`${aa.length} road-accident records • death total not published in this feed`:`${aa.length} दुर्घटना रेकर्ड • यो feed मा मृत्यु संख्या प्रकाशित छैन`);
}

const exactEn=new Map([
  ['मेरो वरिपरि बाढीको अवस्था','Flood status around me'],
  ['मेरो स्थान प्रयोग','Use my location'],
  ['नक्साका बीच छान्नुहोस्','Choose location on map'],
  ['वरिपरि','Radius'],
  ['नक्साबाट छानिएको','Selected from map'],
  ['स्थानीय जोखिम','Local risk'],
  ['ठूलो चेतावनी भेटिएन','No major warning'],
  ['नजिकका नदी स्टेशन','Nearby river stations'],
  ['सडक समस्या','Road issues'],
  ['वर्षा स्टेशन','Rain stations'],
  ['नजिकको सडक अवस्था','Nearby road status'],
  ['अहिलेको जानकारी','Latest information'],
  ['लाइभ सूचना','Live information'],
  ['७७ जिल्ला स्थिति','77 district status'],
  ['जिल्ला छान्नुहोस्','Choose district'],
  ['बाढी चेतावनी ध्वनि','Flood alert sound'],
  ['सूचना सक्रिय','Enable alerts'],
  ['ध्वनि परीक्षण','Test sound'],
  ['उपग्रह','Satellite'],
  ['सडक','Street'],
  ['NASA वर्षा','NASA rain'],
  ['लाइभ','Live'],
  ['१ घण्टा','1 hour'],
  ['६ घण्टा','6 hours'],
  ['२४ घण्टा','24 hours']
]);
const startsEn=[
  ['GPS प्रयोग गर्दा','With GPS, nearby rivers, official gauges, rainfall, alerts and roads are prioritised for your location.'],
  ['आवाज केवल HIGH','Sound plays only for a local HIGH or VERY HIGH flood risk.'],
  ['नक्सामा स्थान छानेपछि','After choosing a location on the map, nearby official data is shown.'],
  ['छानिएको दूरीभित्र','No closed or partially-open DoR/BIPAD road record was found inside the selected radius.'],
  ['नजिकको आधिकारिक चेतावनी','Nearby official alerts and road disruptions'],
  ['सार्वजनिक live numerical','No fabricated value is shown where a public live numerical reading is unavailable.']
];
function translateLeaf(el){
  if(el.children.length)return;
  const t=(el.textContent||'').trim();if(!t)return;
  if(lang()==='ne'){
    if(el.dataset.uxNe!==undefined){el.textContent=el.dataset.uxNe;delete el.dataset.uxNe}
    return;
  }
  let out=exactEn.get(t)||null;
  if(!out){for(const [a,b] of startsEn)if(t.startsWith(a)){out=b;break}}
  if(out){if(el.dataset.uxNe===undefined)el.dataset.uxNe=t;el.textContent=out}
}
function translateKnown(){
  const en=lang()==='en';
  document.documentElement.lang=en?'en':'ne';
  const h1=document.querySelector('.brand h1');if(h1){if(en){if(!h1.dataset.uxNe)h1.dataset.uxNe=h1.textContent;h1.textContent='FloodSafe Nepal'}else if(h1.dataset.uxNe){h1.textContent=h1.dataset.uxNe;delete h1.dataset.uxNe}}
  document.querySelectorAll('.side button,.side label,.side small,.side p,.side h1,.side h2,.side h3,.side h4,.side span,.side option,.mapBtns button').forEach(translateLeaf);
  const one=$('fs23r1')?.previousElementSibling,six=$('fs23r6')?.previousElementSibling,day=$('fs23r24')?.previousElementSibling;
  if(one)one.textContent=en?'1 hour':'१ घण्टा';if(six)six.textContent=en?'6 hours':'६ घण्टा';if(day)day.textContent=en?'24 hours':'२४ घण्टा';
  renderAccident();
}
function langHooks(){
  document.addEventListener('click',e=>{
    const b=e.target.closest?.('.fs23lang');if(!b)return;
    setTimeout(translateKnown,80);setTimeout(translateKnown,400);setTimeout(translateKnown,1200);
  });
  setInterval(()=>{if(lang()==='en')translateKnown();renderAccident()},1500);
}

function addBackToMap(){
  const hero=document.querySelector('.hero');if(!hero||$('fs23BackMap'))return;
  const b=document.createElement('button');b.id='fs23BackMap';b.type='button';b.textContent=lang()==='en'?'🗺️ Back to map':'🗺️ नक्सामा फर्कनुहोस्';
  b.onclick=()=>document.querySelector('.mapWrap')?.scrollIntoView({behavior:'smooth',block:'start'});
  hero.appendChild(b);
}
function jumpToDetails(){
  const t=document.querySelector('.hero')||$('fs23weather');if(!t)return;
  t.scrollIntoView({behavior:'smooth',block:'start'});t.classList.add('fs23Jump');setTimeout(()=>t.classList.remove('fs23Jump'),1800);
  addBackToMap();
}
function hookMapJump(){
  let tries=0;const t=setInterval(()=>{
    const m=window.__fs?.map;if(!m){if(++tries>100)clearInterval(t);return}
    clearInterval(t);if(mapHooked)return;mapHooked=true;
    m.on('click',()=>setTimeout(jumpToDetails,350));
    const gps=[...document.querySelectorAll('button')].find(b=>/मेरो स्थान प्रयोग|use my location/i.test(b.textContent||''));if(gps)gps.addEventListener('click',()=>setTimeout(jumpToDetails,1500));
  },200);
}

function init(){css();captureIncidents();seedIncidents();ensureAccidentCard();langHooks();translateKnown();hookMapJump();addBackToMap();setInterval(ensureAccidentCard,5000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,500));else setTimeout(init,500);
})();
