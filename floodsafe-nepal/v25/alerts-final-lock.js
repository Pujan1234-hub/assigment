(()=>{
'use strict';
if(window.__fsAlertsFinalLockV1)return;window.__fsAlertsFinalLockV1=true;
if((document.body.dataset.page||'')!=='alerts')return;
const $=id=>document.getElementById(id),lang=()=>localStorage.getItem('fs23-lang')==='en'?'en':'ne';
let applying=false,queued=false;
function put(id,v){const e=$(id),s=String(v??'—');if(e&&e.textContent!==s)e.textContent=s}
function apply(){if(applying)return;applying=true;try{const f=window.__fsFloodState,r=window.__fsRoadState;if(f){put('alertCount',f.alerts);put('riverAlertCount',f.riverWarnings)}if(r){const c=Number.isFinite(r?.dor?.closed)?r.dor.closed:r?.bipad?.closed;if(Number.isFinite(c))put('roadAlertCount',c)}const s=$('appStatus');if(s&&f&&r){const t=lang()==='en'?'Flood/river and road live sources connected':'बाढी/नदी र सडकका प्रत्यक्ष स्रोत जोडिएका छन्';if(s.textContent!==t)s.textContent=t}}finally{applying=false}}
function repair(){if(applying||queued)return;queued=true;queueMicrotask(()=>{queued=false;apply()})}
function boot(){const roots=['alertCount','riverAlertCount','roadAlertCount','appStatus'].map($).filter(Boolean),ob=new MutationObserver(repair);for(const e of roots)ob.observe(e,{childList:true,subtree:true,characterData:true});window.__fsAlertsCounterObserver=ob;setInterval(apply,500);window.addEventListener('fs-language-change',apply)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
