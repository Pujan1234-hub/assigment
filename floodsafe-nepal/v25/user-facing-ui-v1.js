(()=>{'use strict';
if(window.__fsUserFacingUIV2)return;window.__fsUserFacingUIV2=true;
const $=id=>document.getElementById(id),lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne',tr=(ne,en)=>lang()==='en'?en:ne;
let open=true,locking=false,raf=0;
const text=(id,value)=>{const e=$(id),v=String(value??'');if(e&&e.textContent!==v)e.textContent=v};
function style(){if($('fsUserFacingStyle'))return;const s=document.createElement('style');s.id='fsUserFacingStyle';s.textContent=`#fsOpenMapBtn{display:none;width:100%;border:0;border-radius:15px;padding:13px 15px;margin:8px 0 10px;background:#e8f5ff;color:#075985;font:800 15px system-ui;cursor:pointer}.fsMapClosed .mapCanvas{display:none!important}.fsMapClosed .mapTools{display:none!important}.fsTechHide{display:none!important}@media(max-width:720px){#fsOpenMapBtn{display:block}.mapCard{padding-bottom:10px}.mapCard.fsMapOpen #fsOpenMapBtn{background:#eef2f7;color:#334155}.mapCanvas{min-height:62vh}.mapHead .head{align-items:flex-start}.mapHead h3{font-size:1rem}.mapHead .muted{font-size:.8rem}.bottom{z-index:8000}.app{padding-bottom:90px}}`;document.head.appendChild(s)}
function button(){const card=$('map');if(!card)return;let b=$('fsOpenMapBtn');if(!b){b=document.createElement('button');b.id='fsOpenMapBtn';b.type='button';card.querySelector('.mapHead')?.insertAdjacentElement('afterend',b);b.addEventListener('click',()=>open?close():show())}renderButton()}
function renderButton(){const b=$('fsOpenMapBtn'),card=$('map');if(!b||!card)return;if(innerWidth>720){open=true;card.classList.remove('fsMapClosed');card.classList.add('fsMapOpen');if(b.textContent)b.textContent='';return}card.classList.toggle('fsMapClosed',!open);card.classList.toggle('fsMapOpen',open);const v=open?tr('✕ नदी नक्सा बन्द गर्नुहोस्','✕ Close River Map'):tr('🗺️ नदी नक्सा खोल्नुहोस्','🗺️ Open River Map');if(b.textContent!==v)b.textContent=v}
function show(){open=true;renderButton();setTimeout(()=>{window.FloodSafeMap?.map?.resize?.();$('map')?.scrollIntoView?.({behavior:'smooth',block:'start'})},80)}
function close(){open=false;renderButton()}
function friendly(){if(locking)return;locking=true;try{
const r=window.__fsRiverRealtimeState||{},g=window.__fsGaugeRenderState||{},all=Number(r.catalogCount??g.catalog??0),current=Number(r.currentCount??g.current??0);
const fmt=t=>t?new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date(t))+' NPT':'—';
text('mapSub',tr('स्टेशन थिचेर मापन हेर्नुहोस्। निलो: सामान्य • सुन्तला: चेतावनी • रातो: खतरा • खैरो: ताजा मापन छैन।','Tap a station for readings. Blue: normal • orange: warning • red: danger • grey: no fresh reading.'));
const health=r.connected?tr('स्वतः जाँच जारी','Auto-check active'):tr('जडान पुनः प्रयास हुँदैछ','Reconnecting');
const summary=tr(`${all} स्टेशन • ${current} ताजा मापन (१० मिनेटभित्र) • ${health}`,`${all} stations • ${current} fresh readings (within 10 min) • ${health}`);
const availability=current?summary:tr('नयाँ तथ्याङ्क उपलब्ध छैन','No fresh data')+' • '+summary;const badge=$('map')?.querySelector?.('.badge');if(badge){badge.textContent=current?tr('ताजा मापन','Fresh readings'):tr('नयाँ छैन','No fresh data');badge.className='badge '+(current?'green':'amber')}text('mapHint',availability);
text('feedFresh',availability+' • '+tr('अन्तिम सफल जाँच: ','Last successful check: ')+fmt(r.lastGoodAt));
text('nationalRiverFresh',tr('पछिल्लो स्रोत मापन: ','Newest source observation: ')+fmt(r.newestKnownMeasurement||r.newestMeasurement)+' • '+tr('अन्तिम प्रयास: ','Last attempt: ')+fmt(r.checkedAt));
for(const card of [$('nationalRivers'),$('nearTitle')?.closest('.card')]){const b=card?.querySelector('.badge');if(b){b.textContent=tr('स्वतः जाँच','Auto-check');b.className='badge '+(current?'green':'amber')}}
text('nearSub',tr('ताजा मापन भएका नजिकका स्टेशन मात्र यहाँ देखिन्छन्। पुरानो मापन नक्सामा स्टेशन थिचेर हेर्नुहोस्।','Only nearby fresh readings appear here. Tap a map station for its dated last-known reading.'));
text('riverStatusSub',tr('सबै official स्टेशन • ताजा र पुरानो मापन छुट्टाछुट्टै • स्वतः जाँच','All official stations • fresh and last-known readings kept separate • automatic checks'));
const x=$('nationalRealtimeCoverage');if(x)x.style.display='none';text('newsSub','RONB Post • Radio Nepal • News24 Nepal');
}finally{locking=false}}
function queueFriendly(){if(raf)return;raf=requestAnimationFrame(()=>{raf=0;friendly()})}
function bindNav(){for(const a of document.querySelectorAll('.bottom a'))if(a.getAttribute('href')==='#map')a.addEventListener('click',()=>{if(innerWidth<=720)show()},true)}
function boot(){style();button();bindNav();friendly();setInterval(()=>{if(!document.hidden)friendly()},3000);window.addEventListener('resize',renderButton);window.addEventListener('fslanguage',()=>{renderButton();friendly()});for(const ev of['fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsgaugesrendered'])window.addEventListener(ev,queueFriendly);window.FloodSafeMobileMap={open:show,close,get isOpen(){return open}}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
