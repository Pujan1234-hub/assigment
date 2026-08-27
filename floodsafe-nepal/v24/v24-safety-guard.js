(()=>{
'use strict';
const $=id=>document.getElementById(id);
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
function markGateway(){
  const g=window.__floodsafeGateway;
  if(g&&g.enabled===false)document.documentElement.dataset.floodsafeGateway='direct-official-cache';
}
function run(){removeHardcodedImpact();markGateway()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
setInterval(run,1000);
new MutationObserver(()=>requestAnimationFrame(run)).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();
