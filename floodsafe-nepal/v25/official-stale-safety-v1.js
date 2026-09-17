(()=>{'use strict';
if(window.__fsOfficialStaleSafetyV5)return;window.__fsOfficialStaleSafetyV5=true;
const CURRENT_MS=10*60*1000,FUTURE_MS=5*60*1000;
const lang=()=>window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne';
const tr=(ne,en)=>lang()==='en'?en:ne;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const num=v=>{if(v===null||v===undefined||v==='')return null;const n=Number(String(v).replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const put=(e,v)=>{v=String(v);if(e&&e.textContent!==v)e.textContent=v};
const timeOf=o=>val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime','time']);
const ageMs=t=>{const x=+new Date(t||0);return x?Date.now()-x:Infinity};
const isCurrent=t=>{const a=ageMs(t);return Number.isFinite(a)&&a>=-FUTURE_MS&&a<=CURRENT_MS};
function stage(o){const l=num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','level','_lastWaterLevel'])),w=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold','_lastWarningLevel'])),d=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold','_lastDangerLevel'])),raw=String(val(o,['_officialStatus','official_status','status','status_name','alertStatus','riskLevel'])||'').toUpperCase();if((l!==null&&d!==null&&d>0&&l>=d)||(/DANGER|RED/.test(raw)&&!/BELOW\s+DANGER/.test(raw)))return'danger';if((l!==null&&w!==null&&w>0&&l>=w)||(/WARNING|ORANGE/.test(raw)&&!/BELOW\s+WARNING/.test(raw)))return'warning';if(/WATCH|ALERT|RISING|INCREASING|YELLOW/.test(raw))return'watch';return l===null?'unknown':'normal'}
function safeResult(x){if(Array.isArray(x))return x.map(safeResult);if(!x||typeof x!=='object')return x;const t=x.time||timeOf(x),current=isCurrent(t);if(current)return{...x,current:true,isCurrent:true};return{...x,current:false,isCurrent:false,updated5m:false,has_latest:0,live_has_latest:0,status:'unknown',level:'',waterLevel:null,discharge:'',time:'',official_status:'NO_CURRENT_OFFICIAL_READING'}}
function wrapGauge(){const g=window.FloodSafeGauge;if(!g||g.__staleSafetyWrappedV5)return false;for(const k of['forWaterway','forWaterwayCatalog','nearby','nearbyCatalog']){if(typeof g[k]!=='function')continue;const fn=g[k].bind(g);g[k]=(...a)=>safeResult(fn(...a))}g.__staleSafetyWrappedV5=true;try{window.FloodSafeRiverLine?.rebuild?.(true);window.FloodSafeRiverStyle?.apply?.()}catch{}return true}
function currentRows(){const S=window.FloodSafe?.state||{},rows=Array.isArray(S.currentRiverStations)?S.currentRiverStations:(Array.isArray(S.latestRiverStations)?S.latestRiverStations:[]);return rows.filter(o=>num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','level','_lastWaterLevel']))!==null&&isCurrent(timeOf(o)))}
function fixCounters(){const rows=currentRows(),warning=rows.filter(o=>stage(o)==='warning').length,danger=rows.filter(o=>stage(o)==='danger').length;put(document.getElementById('warningCount'),warning);put(document.getElementById('dangerCount'),danger);window.__fsCurrentOfficialRisk={current:rows.length,warning,danger,checkedAt:new Date().toISOString(),windowMinutes:10}}
function injectStyle(){if(document.getElementById('fsStaleSafetyStyle'))return;const s=document.createElement('style');s.id='fsStaleSafetyStyle';s.textContent='.fsStaleCurrentGuard{font-size:.86rem;font-weight:800;color:#334155;background:#f8fafc;border:1px solid #cbd5e1;padding:12px;border-radius:12px;margin:8px 0}.fsStaleCurrentGuard strong{display:block;color:#0f172a;margin-bottom:4px}.fsStaleCurrentGuard small{display:block;margin-top:5px;color:#64748b;font-weight:700}';document.head.appendChild(s)}
function hideOldText(){for(const e of document.querySelectorAll('.riverMeta,.stationMeta,.fresh')){const t=e.textContent||'';if(/(?:\b(?:1[1-9]|[2-9]\d+)\s*(?:min|मिनेट)|\b\d+\s*(?:hr|घण्टा|day|दिन)\b)/i.test(t)&&/(?:official|reading|नदी|river)/i.test(t)&&e.style.display!=='none')e.style.display='none'}}
let queued=false;function apply(){queued=false;wrapGauge();fixCounters();hideOldText()}
function queueApply(){if(queued)return;queued=true;requestAnimationFrame(apply)}
for(const ev of['fs281mapready','fsriverupdate','fstrustedriverupdate','fsriverheartbeat','fsriverlinestatus','fslanguage','fsmapready'])window.addEventListener(ev,queueApply);
function boot(){injectStyle();apply();const mo=new MutationObserver(queueApply);mo.observe(document.body,{childList:true,subtree:true});window.__fsStaleSafetyObserver=mo;setInterval(()=>{if(!document.hidden)queueApply()},2000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.FloodSafeStaleSafety={CURRENT_MS,isCurrent,ageMs,apply};
})();
