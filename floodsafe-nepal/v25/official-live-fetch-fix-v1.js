(()=>{'use strict';
if(window.__fsOfficialLiveFetchFixV2)return;window.__fsOfficialLiveFetchFixV2=true;
const original=window.fetch.bind(window);
const OFFICIAL_HOSTS=new Set(['camkoacuokffryyrygda.supabase.co','bipadportal.gov.np','www.bipadportal.gov.np']);
const SNAPSHOT='../../data/floodsafe-core.json';
let canonical=[],snapshotLatest=[],snapshotReady=false,loading=false;
function urlOf(input){try{return new URL(typeof input==='string'?input:input?.url,location.href)}catch{return null}}
function cleanHeaders(raw){const h=new Headers(raw||{});h.delete('Cache-Control');h.delete('cache-control');h.delete('Pragma');h.delete('pragma');return h}
window.fetch=function(input,init){
  const u=urlOf(input);
  if(!u||!OFFICIAL_HOSTS.has(u.hostname))return original(input,init);
  const next={...(init||{})};
  next.headers=cleanHeaders(next.headers);
  next.cache='no-store';
  if(!('credentials' in next))next.credentials='omit';
  return original(input,next);
};
const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?{...o.fields,...o}:o;
const val=(o,ks)=>{o=flat(o);for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const ids=o=>{const rt=window.FloodSafeRiverRealtime?.ids?.(o);if(Array.isArray(rt)&&rt.length)return rt.map(String);o=flat(o);const out=[];for(const src of[o,o?.station,o?.riverStation,o?.river_station])if(src&&typeof src==='object')for(const k of['stationSeriesId','station_series_id','stationId','station_id','stationIndex','station_index','id']){const v=src?.[k];if(v!==undefined&&v!==null&&v!=='')out.push(String(v))}return[...new Set(out)]};
const stamp=o=>window.FloodSafeRiverRealtime?.measureTime?.(o)||val(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','observation_time','observedAt','observed_at','datetime','timestamp']);
const level=o=>{const rt=window.FloodSafeRiverRealtime?.level?.(o);if(rt!==undefined&&rt!==null)return rt;const v=val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','value']);if(v===null)return null;const n=Number(String(v).replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const hasObs=o=>!!stamp(o)&&level(o)!==null;
const name=o=>String(val(o,['river_name','riverName','station_name','stationName','title','name'])||flat(o)?.station?.name||'').trim().toLowerCase();
const coords=o=>window.FloodSafeRiverRealtime?.coords?.(o)||flat(o)?._stationCoordinate||null;
function key(o){const x=ids(o);if(x.length)return'id:'+x[0];const c=coords(o);return'name:'+name(o)+'|'+(Array.isArray(c)?c.join(','):'')}
function isNewer(a,b){const at=Date.parse(stamp(a)||''),bt=Date.parse(stamp(b)||'');if(Number.isFinite(at)&&Number.isFinite(bt))return at>=bt;if(Number.isFinite(at))return true;return !Number.isFinite(bt)}
function mergeRows(base,incoming){const out=[],byKey=new Map(),byId=new Map();const put=(row,prefer)=>{if(!row||typeof row!=='object')return;const rowIds=ids(row);let idx=-1;for(const id of rowIds)if(byId.has(id)){idx=byId.get(id);break}if(idx<0&&byKey.has(key(row)))idx=byKey.get(key(row));if(idx<0){idx=out.length;out.push(row);byKey.set(key(row),idx);for(const id of rowIds)byId.set(id,idx);return}const old=out[idx],oldObs=hasObs(old),newObs=hasObs(row);let merged;if(oldObs&&(!newObs||!isNewer(row,old)))merged={...row,...old};else if(newObs&&(!oldObs||isNewer(row,old)))merged={...old,...row};else merged=prefer?{...old,...row}:{...row,...old};out[idx]=merged;byKey.set(key(merged),idx);for(const id of ids(merged))byId.set(id,idx)};for(const r of base||[])put(r,false);for(const r of incoming||[])put(r,true);return out}
function enforce(){if(!snapshotReady)return false;const S=window.FloodSafe?.state;if(!S)return false;const remoteAll=Array.isArray(S.allRiverStations)?S.allRiverStations:[];const remoteLatest=Array.isArray(S.latestRiverStations)?S.latestRiverStations:(Array.isArray(S.stations)?S.stations:[]);const stableLatest=mergeRows(snapshotLatest,remoteLatest).filter(hasObs);const stableAll=mergeRows(canonical,mergeRows(stableLatest,remoteAll));S.allRiverStations=stableAll;S.latestRiverStations=stableLatest;S.stations=stableLatest;S.riverObservations=stableLatest;S.lastRiverReadings=stableLatest;const rt=window.__fsRiverRealtimeState;if(rt){rt.catalogCount=stableAll.length;rt.catalogWithCoordinates=stableAll.filter(x=>{const c=coords(x);return Array.isArray(c)&&c.length>=2}).length;rt.latestCount=stableLatest.length;rt.withoutObservationCount=Math.max(0,stableAll.length-stableLatest.length);rt.stationRetention='canonical-snapshot+last-known-good'}window.__fsStationRetentionState={ready:true,catalogCount:stableAll.length,latestCount:stableLatest.length,checkedAt:new Date().toISOString()};return true}
async function loadSnapshot(){if(loading||snapshotReady)return;loading=true;try{const r=await original(SNAPSHOT+(SNAPSHOT.includes('?')?'&':'?')+'_fs_catalog='+Date.now(),{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error('snapshot HTTP '+r.status);const j=await r.json();canonical=Array.isArray(j?.river_stations)?j.river_stations:[];snapshotLatest=Array.isArray(j?.rivers)?j.rivers.filter(hasObs):[];if(!canonical.length&&!snapshotLatest.length)throw Error('snapshot river catalogue empty');snapshotReady=true;if(enforce())window.dispatchEvent(new CustomEvent('fsriverupdate',{detail:{source:'canonical-retention',catalogCount:window.FloodSafe?.state?.allRiverStations?.length||0}}))}catch(e){window.__fsStationRetentionState={ready:false,error:String(e?.message||e),checkedAt:new Date().toISOString()}}finally{loading=false}}
for(const ev of['fstrustedriverupdate','fsriverupdate','fsriverheartbeat'])window.addEventListener(ev,()=>{if(snapshotReady)enforce();else loadSnapshot()});
function boot(){loadSnapshot();setInterval(()=>{if(snapshotReady)enforce();else loadSnapshot()},10000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.__fsOfficialLiveFetchPolicy={hosts:[...OFFICIAL_HOSTS],cache:'no-store',corsSimpleHeadersOnly:true,stationRetention:'canonical-snapshot+last-known-good'};
})();
