(()=>{
'use strict';
if(window.__FS_FLOOD_WARNING_NOW_V1__)return;
window.__FS_FLOOD_WARNING_NOW_V1__=true;
const MAX_AGE=60*60*1000;
const $=id=>document.getElementById(id);
const n=v=>{const x=Number(v);return Number.isFinite(x)?x:null};
const txt=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&String(v).trim())return String(v).trim()}return''};
const stationName=o=>{try{const x=window.FloodSafeRiverRealtime?.name?.(o);if(x)return String(x)}catch{}return txt(o,['stationName','station_name','riverName','river_name','name','title'])||'नदी स्टेशन'};
const level=o=>{try{const x=window.FloodSafeRiverRealtime?.level?.(o);if(Number.isFinite(x))return x}catch{}return n(o?._lastWaterLevel??o?._level??o?.waterLevel??o?.water_level??o?.level??o?.value)};
const warning=o=>{try{const x=window.FloodSafeRiverRealtime?.warning?.(o);if(Number.isFinite(x))return x}catch{}return n(o?._lastWarningLevel??o?._warning??o?.warningLevel??o?.warning_level)};
const danger=o=>{try{const x=window.FloodSafeRiverRealtime?.danger?.(o);if(Number.isFinite(x))return x}catch{}return n(o?._lastDangerLevel??o?._danger??o?.dangerLevel??o?.danger_level)};
const measured=o=>txt(o,['_measurementTime','measurementTime','measurement_time','waterLevelOn','water_level_on','timestamp','updatedAt']);
function stage(o){
  try{const s=String(window.FloodSafeRiverRealtime?.stage?.(o)||'').toLowerCase();if(['danger','warning','watch','normal','unknown'].includes(s))return s}catch{}
  const l=level(o),w=warning(o),d=danger(o),raw=txt(o,['_derivedStatus','_officialStatus','status','status_name']).toLowerCase();
  if((l!==null&&d!==null&&d>0&&l>=d)||/danger|red|खतरा/.test(raw))return'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||/warning|orange|चेतावनी/.test(raw))return'warning';
  if(/watch|rising|yellow|सतर्क/.test(raw))return'watch';
  return l===null?'unknown':'normal';
}
function fresh(o){const t=Date.parse(measured(o)||'');return Number.isFinite(t)&&Date.now()-t>=-5*60*1000&&Date.now()-t<=MAX_AGE}
function fmtTime(v){const d=new Date(v);if(Number.isNaN(+d))return'';try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'numeric',minute:'2-digit',hour12:true}).format(d)}catch{return''}}
function ensure(){
  if($('fsFloodWarningNow'))return $('fsFloodWarningNow');
  const host=$('alarmBanner');if(!host)return null;
  const style=document.createElement('style');style.id='fsFloodWarningNowStyle';style.textContent=`#fsFloodWarningNow{display:none;margin:12px 0;padding:0;border-radius:20px;overflow:hidden;border:1px solid #ffd2d2;background:#fff;box-shadow:0 10px 26px rgba(95,22,22,.09)}#fsFloodWarningNow.active{display:block}.fsFwnHead{display:flex;gap:12px;align-items:flex-start;padding:15px}.fsFwnIcon{font-size:31px;line-height:1}.fsFwnTitle{font-weight:900;font-size:18px;line-height:1.25}.fsFwnSub{margin-top:4px;font-size:13px;line-height:1.45;color:#425466}.fsFwnRows{border-top:1px solid #eef2f5}.fsFwnRow{padding:11px 15px;border-bottom:1px solid #eef2f5;font-size:13px;line-height:1.45}.fsFwnRow:last-child{border-bottom:0}.fsFwnSource{padding:9px 15px;background:#f8fbfd;font-size:11px;color:#647585}.fsFwnDanger .fsFwnHead{background:#fff2f2}.fsFwnDanger .fsFwnTitle{color:#c51111}.fsFwnWarning .fsFwnHead{background:#fff8eb}.fsFwnWarning .fsFwnTitle{color:#a15b00}`;document.head.appendChild(style);
  const el=document.createElement('section');el.id='fsFloodWarningNow';el.setAttribute('aria-live','polite');host.insertAdjacentElement('afterend',el);return el;
}
function render(){
  const el=ensure();if(!el)return;
  const st=window.FloodSafe?.state||{};const rows=Array.isArray(st.currentRiverStations)?st.currentRiverStations:[];
  const risky=rows.filter(fresh).map(o=>({o,s:stage(o)})).filter(x=>x.s==='danger'||x.s==='warning');
  if(!risky.length){el.className='';el.innerHTML='';return}
  const wt={danger:2,warning:1};risky.sort((a,b)=>wt[b.s]-wt[a.s]);const dangerCount=risky.filter(x=>x.s==='danger').length,warningCount=risky.length-dangerCount;const severe=dangerCount>0;
  const title=severe?'🔴 बाढीको खतरा अहिले सक्रिय':'🟠 बाढी चेतावनी अहिले सक्रिय';
  const sub=severe?'BIPAD/DHM को ताजा नदी मापनमा कम्तीमा एक स्टेशन खतरा तह पुगेको वा नाघेको छ। तल्लो क्षेत्र, नदी किनार र डुबान सम्भावित ठाउँमा तत्काल सतर्कता अपनाउनुहोस्।':'BIPAD/DHM को ताजा नदी मापनमा कम्तीमा एक स्टेशन चेतावनी तह पुगेको वा नाघेको छ। पानी अझ बढ्न सक्ने भएकाले तयारी र निगरानी बढाउनुहोस्।';
  const list=risky.slice(0,5).map(({o,s})=>{const l=level(o),thr=s==='danger'?danger(o):warning(o),t=measured(o);return`<div class="fsFwnRow"><b>${s==='danger'?'🔴 खतरा':'🟠 चेतावनी'} — ${escapeHtml(stationName(o))}</b>${l!==null?` • जलस्तर ${l.toFixed(2)} मि.`:''}${thr!==null?` • ${s==='danger'?'खतरा':'चेतावनी'} तह ${thr.toFixed(2)} मि.`:''}${t?` • मापन ${fmtTime(t)}`:''}</div>`}).join('');
  el.className=`active ${severe?'fsFwnDanger':'fsFwnWarning'}`;el.innerHTML=`<div class="fsFwnHead"><div class="fsFwnIcon">${severe?'⚠️':'🔔'}</div><div><div class="fsFwnTitle">${title}</div><div class="fsFwnSub">${sub}</div><div class="fsFwnSub"><b>${dangerCount}</b> खतरा • <b>${warningCount}</b> चेतावनी</div></div></div><div class="fsFwnRows">${list}</div><div class="fsFwnSource">स्रोत: BIPAD/DHM official realtime नदी मापन • ६० मिनेटभन्दा पुरानो reading यस कार्डमा देखाइँदैन।</div>`;
}
function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function boot(){ensure();render();setInterval(render,12000);for(const ev of['fsriverupdate','fs-river-update','floodsafe-river-update','online','focus'])window.addEventListener(ev,()=>setTimeout(render,120))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
