(()=>{
'use strict';
const $=id=>document.getElementById(id);
function feedHealth(){
  const s=String($('feedState')?.textContent||'');
  const m=s.match(/(\d+)\s*\/\s*(\d+)/);
  if(!m)return null;
  const ok=Number(m[1]),total=Number(m[2]);
  return Number.isFinite(ok)&&Number.isFinite(total)?{ok,total,partial:ok<total}:null;
}
function removeHardcodedImpact(){
  const d=$('deadV'),i=$('injuredV'),m=$('missingV'),ev=$('incidentV'),note=$('impactNote');
  if(!d||!note)return;
  const text=(note.textContent||'')+' '+(d.textContent||'');
  const legacy=/९५\s*मृत्यु|95\s*(?:death|deaths)|रसुवा बाढीमा\s*९५/i.test(text);
  if(!legacy)return;
  d.textContent='—';if(i)i.textContent='—';if(m)m.textContent='—';if(ev)ev.textContent='—';
  note.classList.add('fs23impactFallback');
  note.textContent='आजको BIPAD incident/loss data sync उपलब्ध छैन। संख्या पुष्टि नभएसम्म यहाँ अनुमान वा पुरानो संख्या देखाइँदैन।';
}
function guardIncompleteFeeds(){
  const h=feedHealth();if(!h?.partial)return;
  const districts=$('districtList');
  if(districts){
    for(const tag of districts.querySelectorAll('.tag')){
      if(/ठूलो चेतावनी छैन|no major warning/i.test(tag.textContent||'')){
        tag.textContent='डेटा अपूर्ण';tag.classList.remove('green');tag.classList.add('orange');
      }
    }
  }
  const ticker=$('tickerMsg');
  if(ticker&&/ठूलो सक्रिय चेतावनी भेटिएन|no major active warning/i.test(ticker.textContent||'')){
    ticker.textContent='⚠️ आंशिक लाइभ डेटा — चेतावनी नभएको पुष्टि गर्न सकिँदैन।';
    const meta=$('tickerMeta');if(meta)meta.textContent='DHM / BIPAD / DoR • data incomplete';
  }
  const risk=$('riskV');
  if(risk&&/ठूलो चेतावनी भेटिएन|no major warning|no major alert/i.test(risk.textContent||'')){
    risk.textContent=h.ok===0?'लाइभ डेटा उपलब्ध छैन':'आंशिक डेटा — पुष्टि गर्नुहोस्';risk.className='warn';
  }
}
function markGateway(){
  const g=window.__floodsafeGateway;
  if(g&&g.enabled===false)document.documentElement.dataset.floodsafeGateway='direct-official-cache';
}
function run(){removeHardcodedImpact();guardIncompleteFeeds();markGateway()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
setInterval(run,1000);
new MutationObserver(()=>requestAnimationFrame(run)).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();
