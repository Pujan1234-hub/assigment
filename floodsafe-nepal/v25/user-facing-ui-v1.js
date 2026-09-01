(()=>{'use strict';
if(window.__fsUserFacingUIV2)return;window.__fsUserFacingUIV2=true;
const $=id=>document.getElementById(id),lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne',tr=(ne,en)=>lang()==='en'?en:ne;
let open=false,locking=false,raf=0;
const text=(id,value)=>{const e=$(id),v=String(value??'');if(e&&e.textContent!==v)e.textContent=v};
function style(){if($('fsUserFacingStyle'))return;const s=document.createElement('style');s.id='fsUserFacingStyle';s.textContent=`#fsOpenMapBtn{display:block;width:100%;border:0;border-radius:15px;padding:13px 15px;margin:8px 0 10px;background:#e8f5ff;color:#075985;font:800 15px system-ui;cursor:pointer}.fsMapClosed .mapCanvas{display:none!important}.fsMapClosed .mapTools{display:none!important}.fsTechHide{display:none!important}@media(max-width:720px){#fsOpenMapBtn{display:block}.mapCard{padding-bottom:10px}.mapCard.fsMapOpen #fsOpenMapBtn{background:#eef2f7;color:#334155}.mapCanvas{min-height:62vh}.mapHead .head{align-items:flex-start}.mapHead h3{font-size:1rem}.mapHead .muted{font-size:.8rem}.bottom{z-index:8000}.app{padding-bottom:90px}}`;document.head.appendChild(s)}
function button(){const card=$('map');if(!card)return;let b=$('fsOpenMapBtn');if(!b){b=document.createElement('button');b.id='fsOpenMapBtn';b.type='button';card.querySelector('.mapHead')?.insertAdjacentElement('afterend',b);b.addEventListener('click',()=>open?close():show())}renderButton()}
function renderButton(){const b=$('fsOpenMapBtn'),card=$('map');if(!b||!card)return;card.classList.toggle('fsMapClosed',!open);card.classList.toggle('fsMapOpen',open);b.setAttribute('aria-expanded',String(open));b.setAttribute('aria-controls','riverMapGL');const v=open?tr('✕ नदी नक्सा बन्द गर्नुहोस्','✕ Close River Map'):tr('🗺️ नदी नक्सा खोल्नुहोस्','🗺️ Open River Map');if(b.textContent!==v)b.textContent=v}
function show(){open=true;renderButton();setTimeout(()=>{window.FloodSafeMap?.map?.resize?.();$('map')?.scrollIntoView?.({behavior:'smooth',block:'start'})},80)}
function close(){open=false;renderButton()}
function friendly(){if(locking)return;locking=true;try{
const r=window.__fsRiverRealtimeState||{},g=window.__fsGaugeRenderState||{},all=Number(r.catalogCount??g.catalog??0),current=Number(r.currentCount??g.current??0);
const fmt=t=>t?new Intl.DateTimeFormat(lang()==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date(t))+' NPT':'—';
text('mapSub',tr('स्टेशन थिचेर मापन हेर्नुहोस्। निलो: सामान्य • सुन्तला: चेतावनी • रातो: खतरा • खैरो: ताजा मापन छैन।','Tap a station for readings. Blue: normal • orange: warning • red: danger • grey: no fresh reading.'));
const health=r.connected?tr('स्वतः जाँच जारी','Auto-check active'):tr('जडान पुनः प्रयास हुँदैछ','Reconnecting');
const available=current;
$('sourceReadingList')?.remove();
const summary=tr(`${all} स्टेशन • ${current} आजको मापन • ${health}`,`${all} stations • ${current} today’s readings • ${health}`);
const availability=tr(`${all} स्टेशन • ${available} उपलब्ध मापन • ${health}`,`${all} stations • ${available} available readings • ${health}`);const badge=$('map')?.querySelector?.('.badge');if(badge){badge.textContent=available?tr('मापन उपलब्ध','Readings available'):tr('मापन छैन','No readings');badge.className='badge '+(current?'green':'amber')}text('mapHint',availability);
text('feedFresh',availability+' • '+tr('अन्तिम सफल जाँच: ','Last successful check: ')+fmt(r.lastGoodAt));
text('nationalRiverFresh',tr('पछिल्लो स्रोत मापन: ','Newest source observation: ')+fmt(r.newestMeasurement)+' • '+tr('अन्तिम प्रयास: ','Last attempt: ')+fmt(r.checkedAt));
for(const card of [$('nationalRivers'),$('nearTitle')?.closest('.card')]){const b=card?.querySelector('.badge');if(b){b.textContent=tr('स्वतः जाँच','Auto-check');b.className='badge '+(current?'green':'amber')}}
text('nearSub',tr('नजिकका स्टेशनको आजको पछिल्लो मापन। स्रोत समय र विवरणका लागि स्टेशन थिच्नुहोस्।','Today’s latest nearby readings. Tap a station for source time and details.'));
text('riverStatusSub',tr('सबै official स्टेशन • आजको पछिल्लो मापन • स्वतः जाँच','All official stations • today’s latest reading per station • automatic checks'));
const x=$('nationalRealtimeCoverage');if(x)x.style.display='none';text('newsSub','RONB Post • Radio Nepal • News24 Nepal');
}finally{locking=false}}
function queueFriendly(){if(raf)return;raf=requestAnimationFrame(()=>{raf=0;friendly()})}
function boot(){style();button();friendly();setInterval(()=>{if(!document.hidden)friendly()},3000);window.addEventListener('resize',renderButton);window.addEventListener('fslanguage',()=>{renderButton();friendly()});for(const ev of['fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsgaugesrendered'])window.addEventListener(ev,queueFriendly);window.FloodSafeMobileMap={open:show,close,get isOpen(){return open}}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
