(()=>{
'use strict';
let installed=false;
function install(){
  const fs=window.__fs,m=fs?.map;if(!m||installed)return false;installed=true;
  const el=m.getContainer();
  el.addEventListener('click',e=>{
    const target=e.target;
    if(target?.closest?.('.leaflet-control,.leaflet-popup,.leaflet-marker-icon,.leaflet-tooltip'))return;
    if(target?.closest?.('path.leaflet-interactive'))return;
    e.stopImmediatePropagation();
    e.stopPropagation();
    const ll=m.mouseEventToLatLng(e);
    if(!ll||!fs.insideNepal?.([ll.lat,ll.lng]))return;
    fs.setFocus([ll.lat,ll.lng],'map');
    const badge=document.getElementById('waterwayBadge');
    if(badge)badge.textContent=localStorage.getItem('fs23-lang')==='en'?'Loading local rivers…':'वरिपरिका नदी/खोला लोड हुँदैछन्…';
  },true);
  return true;
}
let tries=0;const t=setInterval(()=>{if(install()||++tries>100)clearInterval(t)},200);
})();