(()=>{'use strict';
if(window.__fsNewsV9)return;window.__fsNewsV9=true;
const MAX=10*60*1000,ARCHIVE=30*60*1000,FUTURE=5*60*1000,POLL_FRESH=10000,POLL_STALE=3000,POLL_HIDDEN=60000;
const LIVE='https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three';
const SNAP=['https://raw.githubusercontent.com/Pujan1234-hub/assigment/main/data/floodsafe-news.json','../../data/floodsafe-news.json'];
const ALLOWED=new Set(['RONB Post','Radio Nepal','News24 Nepal']);
let live=[],fallback=[],sourceState={},lastChecked=0,lastError='',lastOk=0,busy=false,timer=0,expiryTimer=0,lastHtml='';
const $=id=>document.getElementById(id),lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne',tr=(ne,en)=>lang()==='en'?en:ne,ts=t=>+new Date(t||0)||0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]||c));
const titleKey=s=>String(s??'').normalize('NFKC').toLocaleLowerCase('ne-NP').replace(/\s+/g,' ').trim();
function age(t){const m=Math.max(0,Math.floor((Date.now()-ts(t))/60000));if(m<1)return tr('अहिले','Now');return tr(`${m} मिनेट अघि`,`${m} min ago`)}
function safeUrl(u){try{return /^https?:$/.test(new URL(u).protocol)}catch{return false}}
function valid(x){const t=ts(x?.published_at),d=Date.now()-t;return ALLOWED.has(x?.source)&&!!x?.title&&safeUrl(x?.url)&&t&&d>=-FUTURE&&d<ARCHIVE}
function merged(){const out=[],seenUrl=new Set(),seenTitle=new Set();for(const x of[...live,...fallback].filter(valid).sort((a,b)=>ts(b.published_at)-ts(a.published_at))){const u=String(x.url||'').split('#')[0],k=titleKey(x.title);if(!k||seenUrl.has(u)||seenTitle.has(k))continue;seenUrl.add(u);seenTitle.add(k);out.push(x)}return out.slice(0,30)}
function card(x){return `<article class="newsItem"><h4>${esc(x.title)}</h4><div class="meta">${esc(x.source)} • ${esc(age(x.published_at))} • ${Date.now()-ts(x.published_at)<MAX?'<b class="liveDot">NEW</b>':tr('पछिल्लो प्रकाशित समाचार','Latest published story')}</div><a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${tr('खोल्नुहोस्','Open')} ↗</a></article>`}
// Curated bilingual summaries, reviewed 2026-09-01. Local fallback, not a live advice feed.
const TIP_SOURCES=[
['PrepareCenter / IFRC','https://preparecenter.org/topic/hazard/flood/'],
['Ready Scotland','https://ready.campaign.gov.scot/emergency-kit'],
['Ready.gov','https://www.ready.gov/floods'],
['National Weather Service','https://www.weather.gov/safety/flood-turn-around-dont-drown'],
['GOV.UK','https://www.gov.uk/help-during-flood']
];
const TIPS=[
  [
    "कागजात जोगाउनुहोस्",
    "नागरिकता र महत्वपूर्ण कागजात जलरोधी खोलमा, सम्भावित बाढीभन्दा माथि राख्नुहोस्।",
    "Protect documents",
    "Keep important documents waterproof and above potential flood levels.",
    0
  ],
  [
    "सुरक्षित बाटो",
    "पैदल जान मिल्ने सुरक्षित निकास बाटो पहिल्यै पहिचान गर्नुहोस्।",
    "Plan an exit",
    "Identify safe evacuation routes, including routes on foot.",
    0
  ],
  [
    "परिवारको योजना",
    "छुट्टिएमा कहाँ भेट्ने र कसरी सम्पर्क गर्ने, परिवारसँग तय गर्नुहोस्।",
    "Plan to reconnect",
    "Agree how your family will contact and reunite after separation.",
    0
  ],
  [
    "पाल्तु जनावर",
    "पाल्तु जनावर र पशुधनलाई सुरक्षित सार्ने योजना पहिल्यै बनाउनुहोस्।",
    "Include animals",
    "Plan safe evacuation for pets and livestock in advance.",
    0
  ],
  [
    "स्थानीय जोखिम",
    "आफ्नो क्षेत्रको बाढी जोखिमबारे स्थानीय निकाय र छिमेकीसँग बुझ्नुहोस्।",
    "Know local risks",
    "Ask local authorities and neighbours about flood risk.",
    0
  ],
  [
    "विद्यालय र काम",
    "घरबाहेक विद्यालय र कार्यस्थलबाट सुरक्षित पुग्ने योजना पनि बनाउनुहोस्।",
    "Plan beyond home",
    "Plan safe evacuation from school and work too.",
    0
  ],
  [
    "टर्च तयार",
    "आपत्कालीन झोलामा टर्च र अतिरिक्त ब्याट्री राख्नुहोस्।",
    "Pack a torch",
    "Include a torch and spare batteries in your emergency kit.",
    1
  ],
  [
    "चार्जको तयारी",
    "फोनको चार्जर र आवश्यक उपकरणका अतिरिक्त चार्जर तयार राख्नुहोस्।",
    "Charging essentials",
    "Keep phone and essential-device chargers ready.",
    1
  ],
  [
    "औषधिको तयारी",
    "नियमित आवश्यक औषधि, स्वास्थ्य विवरण र प्रेस्क्रिप्सन तयार राख्नुहोस्।",
    "Medication essentials",
    "Keep essential medication, medical information and prescriptions ready.",
    1
  ],
  [
    "खानेकुराको तयारी",
    "नबिग्रने, पकाउन नपर्ने खाना र बोतलको पानी तयार राख्नुहोस्।",
    "Food and water",
    "Store bottled water and long-lasting food needing no cooking.",
    1
  ],
  [
    "सबैको आवश्यकता",
    "आपत्कालीन झोलामा शिशु, अपाङ्गता भएका सदस्य र पाल्तु जनावरको आवश्यकता समेट्नुहोस्।",
    "Include everyone",
    "Adapt your emergency kit for babies, disabilities and pets.",
    1
  ],
  [
    "एकैपटक किन्नुपर्दैन",
    "घरमै भएका उपयोगी सामानबाट सुरु गरेर आपत्कालीन झोला विस्तारै तयार गर्नुहोस्।",
    "Build gradually",
    "Build your emergency kit gradually using useful items already at home.",
    1
  ],
  [
    "बाढीको पानी नपार्नुहोस्",
    "बाढीको पानीमा हिँड्ने, पौडिने वा गाडी चलाउने प्रयास नगर्नुहोस्।",
    "Avoid floodwater",
    "Do not attempt to walk, swim or drive through floodwater.",
    2
  ],
  [
    "अवरोध ननाघ्नुहोस्",
    "डुबेको सडक बन्द गर्ने अवरोध ननाघ्नुहोस्; तलको सडक भत्किएको हुन सक्छ।",
    "Respect road barriers",
    "Never bypass flood-road barriers; the road underneath may have collapsed.",
    3
  ],
  [
    "पानीले खतरा लुकाउँछ",
    "बाढीको पानीले खुला ढल, फोहोर र बिग्रिएको बाटो लुकाउन सक्छ।",
    "Hidden hazards",
    "Floodwater can conceal open drains, debris and damaged roads.",
    4
  ],
  [
    "सम्पर्क नम्बर",
    "आपत्कालीन सम्पर्क नम्बर फोनमा मात्र होइन, झोलामा पनि राख्नुहोस्।",
    "Keep contact numbers",
    "Keep emergency contact numbers in your bag as well as your phone.",
    1
  ]
];
const TIP_MS=10*60*1000,TIP_KEY='fs-news-tip-v1';
let tipIndex=0,tipUntil=0,tipVisible=false;
try{const saved=JSON.parse(localStorage.getItem(TIP_KEY)||'null');if(Number.isInteger(saved?.index)&&saved.index>=0&&saved.index<TIPS.length){tipIndex=saved.index;tipUntil=Number(saved.until)||0}}catch{}
function saveTip(){try{localStorage.setItem(TIP_KEY,JSON.stringify({index:tipIndex,until:tipUntil}))}catch{}}
function tipCard(){
 const now=Date.now();
 if(!tipUntil||tipUntil>now+TIP_MS){tipUntil=now+TIP_MS}
 else if(now>=tipUntil){tipIndex=(tipIndex+1)%TIPS.length;tipUntil=now+TIP_MS}
 tipVisible=true;saveTip();
 const t=TIPS[tipIndex],s=TIP_SOURCES[t[4]];
 return `<article class="newsItem" id="newsTip" data-tip-index="${tipIndex}"><div class="meta">${tr('💡 उपयोगी ज्ञान • हरेक १० मिनेटमा अर्को','💡 Useful tips • changes every 10 minutes')}</div><h4>${esc(tr(t[0],t[2]))}</h4><p>${esc(tr(t[1],t[3]))}</p><a href="${s[1]}" target="_blank" rel="noopener noreferrer">${tr('स्रोत','Source')}: ${esc(s[0])} ↗</a><div class="meta">${tr('सामान्य तयारीका सुझाव — प्रत्यक्ष चेतावनी होइन','General preparedness advice — not a live alert')}</div></article>`
}
function armExpiry(items){clearTimeout(expiryTimer);let wait=tipVisible?Math.min(60000,Math.max(0,tipUntil-Date.now())):60000;for(const x of items){const expiry=ts(x.published_at)+(isFresh(x)?MAX:ARCHIVE),left=expiry-Date.now();if(left>0&&left<wait)wait=left}if(Number.isFinite(wait))expiryTimer=setTimeout(()=>{render();schedule(0)},Math.max(80,wait+40))}
function isFresh(x){return valid(x)&&Date.now()-ts(x.published_at)<MAX}
function render(){const host=$('liveNews');if(!host)return;if($('newsSub'))$('newsSub').textContent='RONB Post • Radio Nepal • News24 Nepal';const all=merged(),fresh=all.filter(isFresh),older=all.filter(x=>!isFresh(x)),html=!all.length?tipCard():fresh.length?`<div class="newsFreshBox"><div class="newsBoxTitle"><strong>${tr('पछिल्ला समाचार • प्रकाशन समय सहित','Latest news • publication time shown')}</strong></div><div class="fresh">${tr('नयाँ: पछिल्लो १० मिनेट • बाँकी: १०–३० मिनेट','New: last 10 minutes • Recent: 10–30 minutes')}</div>${fresh.map(card).join('')}</div>`:`<div class="noFreshData" role="status"><strong>${tr('नयाँ तथ्याङ्क उपलब्ध छैन','No fresh data')}</strong></div>`;if(all.length&&tipVisible){tipVisible=false;tipUntil=0;saveTip()}const archive=older.length?`<details class="lastKnownData" id="newsArchive" open><summary>${tr('पुराना समाचार हेर्नुहोस् — १०–३० मिनेट','View older news — 10–30 minutes')} (${older.length})</summary>${older.map(card).join('')}</details>`:'';const checked=lastOk?new Date(lastOk).toLocaleTimeString(lang()==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',hour12:false}):'—';const status=checked+' NPT';if(html+archive!==lastHtml){const wasOpen=host.querySelector?.('#newsArchive')?.open??true;lastHtml=html+archive;host.innerHTML='<div id="newsCheck" class="fresh"></div>'+html+archive;if(host.querySelector?.('#newsArchive'))host.querySelector('#newsArchive').open=wasOpen}const badge=$('bulletin')?.querySelector?.('.badge');if(badge){badge.textContent=!all.length?tr('उपयोगी ज्ञान','Useful tips'):fresh.length?tr('नयाँ समाचार','Fresh news'):tr('नयाँ छैन','No fresh data');badge.className='badge '+(fresh.length?'green':'amber')}if(document.getElementById('newsCheck'))document.getElementById('newsCheck').textContent=status;window.__fsNewsLiveState={connected:!!lastOk&&!lastError,checkedAt:lastChecked?new Date(lastChecked).toISOString():null,error:lastError,lastSuccess:lastOk?new Date(lastOk).toISOString():null,tipsVisible:!all.length,tipIndex:!all.length?tipIndex:null,tipCount:TIPS.length,count:all.length,freshCount:fresh.length,archiveCount:older.length,freshWindowMinutes:10,sources:sourceState,mode:'smooth-adaptive-live'};armExpiry(all)}
async function get(url){const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const r=await fetch(url+(url.includes('?')?'&':'?')+'_fsnews='+Date.now(),{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error(String(r.status));return await r.json()}finally{clearTimeout(t)}}
async function fetchLive(){try{const j=await get(LIVE);if(j?.status==='error')throw Error(j.error||'news live error');if(!Array.isArray(j?.items))throw Error('Invalid news payload');live=[...new Map([...live,...j.items].filter(valid).map(x=>[String(x.url).split('#')[0],x])).values()].sort((a,b)=>ts(b.published_at)-ts(a.published_at)).slice(0,100);sourceState=j?.sources||{};lastOk=Date.now();lastError='';return true}catch(e){lastError=String(e);console.warn('FloodSafe live news',e);return false}}
async function snapshot(){for(const u of SNAP)try{const j=await get(u);if(Array.isArray(j?.items)){fallback=j.items.filter(x=>ALLOWED.has(x.source));return true}}catch{}return false}
function nextDelay(){if(document.hidden)return POLL_HIDDEN;return merged().length?POLL_FRESH:POLL_STALE}
function schedule(ms=nextDelay()){clearTimeout(timer);timer=setTimeout(sync,Math.max(250,ms))}
function kick(ms=0){clearTimeout(timer);if(!busy)schedule(ms)}
async function sync(){if(busy)return;busy=true;try{lastChecked=Date.now();const ok=await fetchLive();if(!ok||!live.length)await snapshot();render()}finally{busy=false;schedule()}}
function boot(){render();kick(0);window.addEventListener('online',()=>kick(0));window.addEventListener('focus',()=>kick(0));window.addEventListener('fslanguage',()=>{lastHtml='';render()});document.addEventListener('visibilitychange',()=>{if(!document.hidden)kick(0);else schedule(POLL_HIDDEN)});window.FloodSafeNews={refresh:()=>kick(0),get items(){return merged()},get state(){return window.__fsNewsLiveState||null},FRESH_WINDOW_MS:MAX,STALE_POLL_MS:POLL_STALE}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
