(()=>{
'use strict';
const FS_MAP_ONLY=new URLSearchParams(location.search).get('mapOnly')==='1';
function loadDirectAuthority(){
  if(FS_MAP_ONLY||window.__fsAuthorityWatchV1||document.getElementById('fsAuthorityWatchScript'))return;
  const s=document.createElement('script');s.id='fsAuthorityWatchScript';s.src='./v24-authority-watch.js?v=2';s.async=true;document.head.appendChild(s);
}
function applyMapOnly(){
  if(!FS_MAP_ONLY)return;
  const run=()=>{
    document.documentElement.classList.add('fs-map-only');
    const st=document.createElement('style');st.id='fsMapOnlyCss';st.textContent=`html.fs-map-only,html.fs-map-only body{overflow:hidden!important}html.fs-map-only .side{display:none!important}html.fs-map-only .app{grid-template-columns:1fr!important;height:100vh!important;min-height:100vh!important}html.fs-map-only .mapWrap{height:100vh!important;min-height:100vh!important}html.fs-map-only .mapTop{left:112px!important}.fsMapBack{position:fixed;z-index:5000;left:10px;top:12px;padding:9px 11px;border-radius:11px;border:1px solid #f0b64b;background:#17100fee;color:#fff8e8;text-decoration:none;font-size:11px;font-weight:950;box-shadow:0 8px 22px #0008;backdrop-filter:blur(7px)}@media(max-width:600px){html.fs-map-only .mapTop{left:98px!important}.fsMapBack{left:8px;top:9px;padding:8px 9px;font-size:10px}}`;
    document.head.appendChild(st);
    const back=document.createElement('a');back.className='fsMapBack';back.href='../v25/';back.textContent='‹ Home';back.setAttribute('aria-label','Back to FloodSafe Nepal home');document.body.appendChild(back);
    setTimeout(()=>{try{window.__fs?.map?.invalidateSize?.()}catch{}},300);
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
}
loadDirectAuthority();applyMapOnly();
const $=id=>document.getElementById(id);
let selectedRiver=null;

// Collapse duplicate reads only inside the same five-second receiver window.
// This keeps the live map responsive to upstream changes on the next poll.
const fs24PreviousFetch=window.fetch.bind(window);
const FS24_API_CACHE_MS=5000;
const fs24ApiCache=new Map();
const fs24Pending=new Map();
const fs24Health=new Map();
function markHealth(url,ok,status,error){fs24Health.set(url,{ok:!!ok,status:Number(status)||0,at:Date.now(),error:error?String(error):''})}
window.fetch=async function(input,init){
  const url=String(input?.url||input||'');
  if(!/https:\/\/bipadportal\.gov\.np\/api\/v1\//i.test(url)||String(init?.method||input?.method||'GET').toUpperCase()!=='GET')return fs24PreviousFetch(input,init);
  const hit=fs24ApiCache.get(url);
  if(hit&&Date.now()-hit.at<FS24_API_CACHE_MS){
    markHealth(url,true,hit.status,'');
    return new Response(hit.body,{status:hit.status,headers:{...hit.headers,'X-FloodSafe-Device-Cache':'HIT'}});
  }
  if(fs24Pending.has(url)){
    const p=await fs24Pending.get(url);markHealth(url,p.status>=200&&p.status<300,p.status,'');
    return new Response(p.body,{status:p.status,headers:{...p.headers,'X-FloodSafe-Device-Cache':'COLLAPSED'}});
  }
  const pending=(async()=>{
    try{
      const r=await fs24PreviousFetch(input,init);const body=await r.clone().text();const headers={'Content-Type':r.headers.get('content-type')||'application/json'};
      const entry={at:Date.now(),body,status:r.status,headers};markHealth(url,r.ok,r.status,'');if(r.ok)fs24ApiCache.set(url,entry);return entry;
    }catch(e){markHealth(url,false,0,e);throw e}
  })().finally(()=>fs24Pending.delete(url));
  fs24Pending.set(url,pending);
  const out=await pending;return new Response(out.body,{status:out.status,headers:out.headers});
};
window.__floodsafeScaleBridge={mode:'device-collapse',ttl_ms:FS24_API_CACHE_MS,cache:fs24ApiCache,health:fs24Health};

const tr={
 ne:{title:'🌊 छानिएको खोला / नदीको अवस्था',choose:'नक्सामा नीलो खोला/नदीमा क्लिक गर्नुहोस्।',river:'खोला / नदी',type:'प्रकार',distance:'तपाईंको स्थानबाट',station:'नजिकको आधिकारिक DHM स्टेशन',level:'पानी सतह',warning:'चेतावनी सीमा',danger:'खतरा सीमा',trend:'बहाव प्रवृत्ति',measured:'अन्तिम मापन',source:'स्रोत',normal:'सामान्य / चेतावनी सीमाभन्दा तल',watch:'निगरानी आवश्यक',warn:'चेतावनी',dangerous:'खतरा',stale:'पुरानो मापन — अहिलेको अवस्था पुष्टि छैन',unknown:'Official gauge भेटिएन — अहिलेको अवस्था पुष्टि गर्न सकिँदैन',nearest:'नजिकको स्टेशन; यही खोलाको station हो भन्ने पुष्टि छैन',same:'नाम मिलेको/सम्बन्धित नजिकको स्टेशन',auto:'स्थान अनुमति पाएपछि वरिपरिका खोला/नदी स्वतः देखाइन्छन्।',partial:'आंशिक लाइभ डेटा — अवस्था पुष्टि गर्नुहोस्',offline:'लाइभ डेटा उपलब्ध छैन — अवस्था पुष्टि भएको छैन'},
 en:{title:'🌊 Selected river / stream status',choose:'Click a blue river or stream on the map.',river:'River / stream',type:'Type',distance:'From your location',station:'Nearest official DHM station',level:'Water level',warning:'Warning level',danger:'Danger level',trend:'Trend',measured:'Last measured',source:'Source',normal:'Normal / below warning level',watch:'Watch closely',warn:'Warning',dangerous:'Danger',stale:'Stale measurement — current status not confirmed',unknown:'No official gauge found — current status cannot be confirmed',nearest:'Nearest station; not confirmed to be on the same river',same:'Name-matched/related nearby station',auto:'Allow location to show nearby rivers and streams automatically.',partial:'Partial live data — verify current conditions',offline:'Live data unavailable — current conditions unconfirmed'}
};
function lang(){return document.documentElement.lang==='en'?'en':'ne'}
function T(k){return tr[lang()][k]}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]))}
function n(v){const x=Number(v);return Number.isFinite(x)?x:null}
function when(o){return o?.waterLevelOn||o?.measuredOn||o?.modifiedOn||o?.createdOn||null}
function ageHours(d){if(!d)return Infinity;const x=+new Date(d);return Number.isFinite(x)?Math.max(0,(Date.now()-x)/36e5):Infinity}
function fmt(d){if(!d)return '—';try{return new Date(d).toLocaleString(lang()==='ne'?'ne-NP':'en-GB',{timeZone:'Asia/Kathmandu',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',second:'2-digit'})}catch{return '—'}}
function norm(s){return String(s||'').toLowerCase().replace(/river|khola|nadi|नदी|खोला|river at|at/g,'').replace(/\s+/g,' ').trim()}
function classify(o){
 const wl=n(o?.waterLevel),w=n(o?.warningLevel),d=n(o?.dangerLevel),st=String(o?.status||'').toUpperCase(),trend=String(o?.steady||'').toUpperCase(),stale=ageHours(when(o))>6;
 if(stale)return['stale',T('stale')];
 if((d!==null&&wl!==null&&wl>=d)||st.includes('DANGER'))return['danger',T('dangerous')];
 if((w!==null&&wl!==null&&wl>=w)||st.includes('ABOVE WARNING'))return['warning',T('warn')];
 if(trend==='RISING'||(w!==null&&wl!==null&&wl>=w*.8))return['watch',T('watch')];
 return['normal',T('normal')];
}
function inject(){
 if($('fs24riverFloat'))return;
 const st=document.createElement('style');st.textContent=`
#fs24riverFloat{position:absolute;z-index:1150;left:14px;bottom:14px;width:min(360px,calc(100% - 28px));background:#17100ff2;border:1px solid #f0b64b;border-left:5px solid #dc143c;border-radius:14px;padding:11px;box-shadow:0 14px 34px #0009;color:#fff8e8;display:none;backdrop-filter:blur(6px)}
#fs24riverFloat h3{font-size:14px;margin:0 28px 7px 0}.fs24close{position:absolute;right:8px;top:7px;background:#2d1a17;border:1px solid #70463d;color:#fff;border-radius:8px;width:26px;height:26px;cursor:pointer}.fs24status{display:inline-block;border-radius:99px;padding:5px 8px;font-size:9px;font-weight:900;margin-bottom:7px}.fs24status.normal{background:#164c39;color:#c6f4dc}.fs24status.watch{background:#6c5619;color:#ffe79e}.fs24status.warning{background:#7c4618;color:#ffe0ad}.fs24status.danger{background:#7b1d30;color:#ffd4dc}.fs24status.stale{background:#4f4641;color:#f1ded4}.fs24grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.fs24cell{background:#211512;border:1px solid #51362e;border-radius:9px;padding:7px}.fs24cell small{display:block;color:#cbb9af;font-size:8.5px}.fs24cell b{display:block;margin-top:3px;font-size:11px;line-height:1.25}.fs24note{font-size:9px;line-height:1.4;color:#d3c2b9;margin-top:7px}.fs24hint{position:absolute;z-index:1110;left:50%;top:76px;transform:translateX(-50%);background:#17100feb;border:1px solid #f0b64b;color:#fff8e8;border-radius:10px;padding:7px 10px;font-size:10px;font-weight:800;pointer-events:none;box-shadow:0 8px 22px #0007}
@media(max-width:900px){#fs24riverFloat{position:fixed;left:8px;right:8px;bottom:8px;width:auto;max-height:46vh;overflow:auto}.fs24hint{top:70px;max-width:72%;text-align:center}}
`;
 document.head.appendChild(st);
 const wrap=document.querySelector('.mapWrap');if(!wrap)return;
 const box=document.createElement('div');box.id='fs24riverFloat';box.innerHTML='<button class="fs24close" aria-label="close">×</button><h3>'+T('title')+'</h3><div id="fs24riverBody" class="fs24note">'+T('choose')+'</div>';wrap.appendChild(box);box.querySelector('.fs24close').onclick=()=>box.style.display='none';
 const hint=document.createElement('div');hint.id='fs24hint';hint.className='fs24hint';hint.textContent=T('auto');wrap.appendChild(hint);setTimeout(()=>{if(hint)hint.style.display='none'},10000);
}
function render(w=selectedRiver){
 selectedRiver=w;if(!w)return;inject();const box=$('fs24riverFloat'),body=$('fs24riverBody'),fs=window.__fs;if(!box||!body)return;box.style.display='block';
 const dist=Number.isFinite(w.d)?w.d:null,g=fs?.nearestGauge?.(w);
 let html='<div class="fs24grid"><div class="fs24cell"><small>'+T('river')+'</small><b>'+esc(w.name)+'</b></div><div class="fs24cell"><small>'+T('type')+'</small><b>'+esc(w.type||'—')+'</b></div><div class="fs24cell"><small>'+T('distance')+'</small><b>'+(dist!==null?dist.toFixed(1)+' km':'—')+'</b></div><div class="fs24cell"><small>'+T('source')+'</small><b>OpenStreetMap geometry</b></div></div>';
 if(!g||!g.o){body.innerHTML='<span class="fs24status stale">'+T('unknown')+'</span>'+html+'<div class="fs24note">'+T('unknown')+'</div>';return;}
 const o=g.o,[cl,label]=classify(o),wl=n(o.waterLevel),warn=n(o.warningLevel),danger=n(o.dangerLevel),nm=String(fs?.name?.(o)||o.title||'DHM station'),rn=norm(w.name),gn=norm(nm),same=rn&&gn&&(rn.includes(gn)||gn.includes(rn));
 html='<span class="fs24status '+cl+'">'+esc(label)+'</span>'+html+'<div class="fs24grid"><div class="fs24cell"><small>'+T('station')+'</small><b>'+esc(nm)+'</b></div><div class="fs24cell"><small>'+T('distance')+'</small><b>'+((g.d??Infinity)<Infinity?Number(g.d).toFixed(1)+' km':'—')+'</b></div><div class="fs24cell"><small>'+T('level')+'</small><b>'+(wl!==null?wl+' m':'—')+'</b></div><div class="fs24cell"><small>'+T('trend')+'</small><b>'+esc(o.steady||o.status||'—')+'</b></div><div class="fs24cell"><small>'+T('warning')+'</small><b>'+(warn!==null?warn+' m':'—')+'</b></div><div class="fs24cell"><small>'+T('danger')+'</small><b>'+(danger!==null?danger+' m':'—')+'</b></div><div class="fs24cell"><small>'+T('measured')+'</small><b>'+fmt(when(o))+'</b></div><div class="fs24cell"><small>'+T('source')+'</small><b>DHM via BIPAD</b></div></div><div class="fs24note">'+(same?T('same'):T('nearest'))+(ageHours(when(o))>6?'. '+T('stale'):'')+'</div>';
 body.innerHTML=html;
}
function applyFeedSafety(){
 const feed=$('feedState'),risk=$('riskV');if(!feed||!risk)return;
 const m=String(feed.textContent||'').match(/(\d+)\s*\/\s*(\d+)/);if(!m)return;
 const ok=Number(m[1]),total=Number(m[2]);if(!Number.isFinite(ok)||!Number.isFinite(total)||ok>=total)return;
 const current=String(risk.textContent||'').trim();
 const noWarning=/ठूलो चेतावनी भेटिएन|no major warning|no major alert/i.test(current);
 if(noWarning||!current||current==='—'){
   risk.textContent=ok===0?T('offline'):T('partial');risk.className='warn';
 }
 if(ok===0){['riverV','roadV','rainV'].forEach(id=>{const el=$(id);if(el)el.textContent='—'});}
}
function expose(){let tries=0;const t=setInterval(()=>{const fs=window.__fs;if(!fs?.map||!fs?.setFocus){if(++tries>80)clearInterval(t);return}clearInterval(t);fs.showRiverStatus=render;inject();
  if(!fs.getFocus?.()&&navigator.geolocation){navigator.geolocation.getCurrentPosition(p=>{const c=[p.coords.latitude,p.coords.longitude];if(fs.insideNepal?.(c)){fs.setFocus(c,'gps');setTimeout(()=>{const w=fs.waterways?.slice?.().sort((a,b)=>a.d-b.d)?.[0];if(w)render(w)},1800)}},()=>{}, {enableHighAccuracy:true,timeout:12000,maximumAge:5000})}
},250)}
setInterval(()=>{if(selectedRiver)render(selectedRiver);applyFeedSafety()},1000);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',expose);else expose();
})();