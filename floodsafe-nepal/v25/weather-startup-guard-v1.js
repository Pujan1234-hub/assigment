(()=>{'use strict';
if(window.__fsWeatherStartupGuardV1)return;window.__fsWeatherStartupGuardV1=true;
const AUTO='fs-auto-current-location-v1';
let waiting=false,resolved=false,observer=null,timer=0;
const lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne';
const tr=(ne,en)=>lang()==='en'?en:ne;
const $=id=>document.getElementById(id);
function wantsCurrent(){try{return localStorage.getItem(AUTO)==='1'}catch{return false}}
function placeholder(){
  if(!waiting||resolved)return;
  const values={temp:'—°',rain:'—',humidity:'—',wind:'—'};
  for(const [id,v] of Object.entries(values)){const e=$(id);if(e&&e.textContent!==v)e.textContent=v}
  const wt=$('weatherText');if(wt)wt.textContent=tr('हालको GPS मौसम जाँच हुँदैछ…','Checking weather for current GPS…');
  const rt=$('rainTiming');if(rt)rt.textContent=tr('हालको GPS स्थान प्राप्त भएपछि वर्षा पूर्वानुमान देखाइन्छ।','Rain forecast will appear after the current GPS location is resolved.');
}
function finish(){if(resolved)return;resolved=true;waiting=false;observer?.disconnect();clearInterval(timer);setTimeout(()=>window.FloodSafeRain?.refresh?.(true),0)}
function fail(){finish()}
function boot(){
  waiting=wantsCurrent()&&!window.FloodSafeCurrentLocation?.last;
  if(!waiting)return;
  placeholder();
  observer=new MutationObserver(placeholder);observer.observe(document.body,{childList:true,subtree:true,characterData:true});
  timer=setInterval(placeholder,120);
  window.addEventListener('fscurrentlocation',finish,{once:true});
  window.addEventListener('fslocationerror',fail,{once:true});
  setTimeout(()=>{if(waiting&&!window.FloodSafeCurrentLocation?.last)fail()},16000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
