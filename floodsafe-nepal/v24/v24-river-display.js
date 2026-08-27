(()=>{
'use strict';
let applying=false;
const lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
function prettyMeter(text){
  const m=String(text||'').trim().match(/^(-?\d+(?:\.\d+)?)\s*m$/i);
  if(!m)return text;
  const x=Number(m[1]);if(!Number.isFinite(x))return text;
  const rounded=Math.round(x*1000)/1000;
  return String(rounded)+' m';
}
function apply(){
  if(applying)return;applying=true;
  try{
    const sheet=document.getElementById('fsRiver3Sheet');
    if(!sheet)return;
    sheet.querySelectorAll('.r3cell').forEach(cell=>{
      const label=(cell.querySelector('small')?.textContent||'').trim();
      const value=cell.querySelector('b');
      if(!value)return;
      if(/Water level|Warning level|Danger level|पानीको सतह|चेतावनी सीमा|खतरा सीमा/i.test(label)){
        const next=prettyMeter(value.textContent);
        if(next!==value.textContent)value.textContent=next;
      }
    });
    const note=(document.getElementById('r3Body')?.innerText||'');
    const status=document.getElementById('r3Status');
    if(status){
      const nearby=/nearby-gauge context|नजिकको station\s*\(/i.test(note);
      const current=(status.textContent||'').trim();
      if(nearby){
        const next=lang()==='en'
          ?current.replace(/^Status:\s*/i,'Nearby gauge: ')
          :current.replace(/^स्थिति:\s*/,'नजिकको स्टेशन: ');
        if(next!==current)status.textContent=next;
      }
    }
  }finally{applying=false}
}
function boot(){
  apply();
  const target=document.querySelector('.mapWrap')||document.body;
  const obs=new MutationObserver(()=>requestAnimationFrame(apply));
  obs.observe(target,{childList:true,subtree:true,characterData:true});
  setInterval(apply,1500);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
