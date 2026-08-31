(()=>{'use strict';
if(window.__fsMapCoreV8)return;window.__fsMapCoreV8=true;
const isEn=()=>((window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne')==='en');
const rt=()=>window.FloodSafeRiverRealtime;
function ensureUI(){
  const host=document.querySelector('.mapCanvas');
  if(!host)return null;
  let box=document.getElementById('fsMapSimpleStatus');
  if(!box){
    box=document.createElement('div');
    box.id='fsMapSimpleStatus';
    box.innerHTML='<div class="fs-live-title">🌊 BIPAD नदी Official Live Feed</div><div id="fsMapSimpleCounts">Official river data जोडिँदैछ…</div><div class="fs-live-legend"><span>🔵 latest सामान्य</span><span>🟡 सतर्क</span><span>🟠 चेतावनी</span><span>🔴 खतरा</span><span>⚪ latest छैन</span></div>';
    host.appendChild(box);
  }else{
    const title=box.querySelector('.fs-live-title');
    if(title)title.textContent=isEn()?'🌊 BIPAD River Official Live Feed':'🌊 BIPAD नदी Official Live Feed';
    let legend=box.querySelector('.fs-live-legend');
    if(legend)legend.innerHTML=isEn()?'<span>🔵 latest normal</span><span>🟡 watch</span><span>🟠 warning</span><span>🔴 danger</span><span>⚪ no latest</span>':'<span>🔵 latest सामान्य</span><span>🟡 सतर्क</span><span>🟠 चेतावनी</span><span>🔴 खतरा</span><span>⚪ latest छैन</span>';
  }
  return box;
}
function updateUI(){
  ensureUI();
  const el=document.getElementById('fsMapSimpleCounts');
  if(!el)return;
  const s=window.__fsRiverRealtimeState||{};
  const g=window.__fsGaugeRenderState||{};
  const total=Number(g.catalog||s.catalogWithCoordinates||s.catalogCount||0);
  const latest=Number(g.latest||s.latestCount||s.currentCount||0);
  const noLatest=Number(g.noLatest||s.withoutObservationCount||Math.max(0,total-latest));
  const ok=s.connected!==false;
  el.textContent=isEn()
    ?`${total} official stations • ${latest} latest readings • ${noLatest} no latest • ${ok?'official feed connected':'reconnecting'}`
    :`${total} official स्टेशन • ${latest} latest reading • ${noLatest} latest छैन • ${ok?'official feed connected':'पुनः जडान हुँदैछ'}`;
}
function boot(){
  ensureUI();updateUI();
  ['fstrustedriverupdate','fsriverupdate','fsriverheartbeat','fsgaugesrendered','fs281mapready','fslanguage'].forEach(n=>window.addEventListener(n,updateUI));
  setInterval(updateUI,10000);
}
window.FloodSafeMapCoreV4={sync:()=>rt()?.refresh?.(),refresh:updateUI};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
