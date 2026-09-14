(()=>{'use strict';
if(window.__fsLatestOfficialDisplayPolicyV1)return;window.__fsLatestOfficialDisplayPolicyV1=true;
const DAY=86400000,NPT=20700000,FUTURE=5*60*1000;
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const num=v=>{if(v===null||v===undefined||v==='')return null;const n=Number(String(v).replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const time=o=>val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','observation_time','observedAt','observed_at','datetime','timestamp']);
const level=o=>num(val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','value']));
const today=t=>{const x=Date.parse(t||'');if(!Number.isFinite(x)||x>Date.now()+FUTURE)return false;return Math.floor((x+NPT)/DAY)===Math.floor((Date.now()+NPT)/DAY)};
function restore(){const S=window.FloodSafe?.state;if(!S)return;const all=Array.isArray(S.allRiverStations)?S.allRiverStations:[];const latest=all.filter(o=>level(o)!==null&&today(time(o)));if(!latest.length)return;S.latestRiverStations=latest;S.currentRiverStations=latest;S.stations=latest;S.riverObservations=latest;S.lastRiverReadings=latest;const old=window.__fsRiverRealtimeState||{};window.__fsRiverRealtimeState={...old,latestCount:latest.length,currentCount:latest.length,withoutObservationCount:Math.max(0,all.length-latest.length),observationPolicy:'latest official reading today (Nepal calendar day)',freshWindowMinutes:null,displayMode:'latest-official-today',checkedAt:new Date().toISOString()};window.dispatchEvent(new CustomEvent('fsriverupdate',{detail:window.__fsRiverRealtimeState}));}
for(const e of['fstrustedriverupdate','fsriverheartbeat','pageshow','online'])window.addEventListener(e,restore);
setInterval(()=>{if(!document.hidden)restore()},5000);
})();
