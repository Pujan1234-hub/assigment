(()=>{'use strict';
if(window.__fsGaugeBridgeV1)return;window.__fsGaugeBridgeV1=true;
const FRESH=6*60*60*1000;
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const lat=o=>num(val(o,['latitude','lat','stationLatitude','station_latitude'])??o?.station?.latitude??o?.location?.latitude);
const lon=o=>num(val(o,['longitude','lon','lng','stationLongitude','station_longitude'])??o?.station?.longitude??o?.location?.longitude);
const name=o=>String(val(o,['river_name','riverName','station_name','stationName','title','name'])||o?.station?.name||'River station');
const stamp=o=>val(o,['waterLevelOn','measuredOn','modifiedOn','updatedOn','updated_at','updatedAt','createdOn','date','timestamp']);
const km=(a,b,c,d)=>{const R=6371,p=x=>x*Math.PI/180,q=Math.sin(p(c-a)/2)**2+Math.cos(p(a))*Math.cos(p(c))*Math.sin(p(d-b)/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
function fresh(o){const t=+new Date(stamp(o)||0);return !!t&&Date.now()-t>=-300000&&Date.now()-t<=FRESH}
function stage(o){const level=num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level'])),warning=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold'])),danger=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold'])),raw=String(val(o,['status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').trim().toUpperCase();let status='normal';if(level!==null&&danger!==null&&danger>0&&level>=danger)status='danger';else if(level!==null&&warning!==null&&warning>0&&level>=warning)status='warning';else if(['DANGER','RED','ABOVE DANGER'].includes(raw))status='danger';else if(['WARNING','ORANGE','ABOVE WARNING'].includes(raw))status='warning';else if(['WATCH','RISING','YELLOW'].includes(raw))status='watch';return{level,warning,danger,status}}
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\b(river|khola|khola river|nadi|stream|station|at|gauge)\b/g,' ').replace(/[^a-z0-9]+/g,' ').trim()}
function tokens(s){return norm(s).split(/\s+/).filter(x=>x.length>=3)}
function nameMatch(a,b){const A=tokens(a),B=tokens(b);if(!A.length||!B.length)return false;return A.some(x=>B.includes(x))||norm(a).includes(norm(b))||norm(b).includes(norm(a))}
function candidate(o,la,lo){const a=lat(o),b=lon(o);if(a===null||b===null||!fresh(o))return null;const s=stage(o);return{o,name:name(o),lat:a,lon:b,distanceKm:km(la,lo,a,b),time:stamp(o),...s}}
function forWaterway(w,la,lo){const stations=window.FloodSafe?.state?.stations||[],wn=String(w?.name_en||w?.name||w?.name_ne||'');const all=stations.map(o=>candidate(o,la,lo)).filter(Boolean).sort((a,b)=>a.distanceKm-b.distanceKm);const direct=all.filter(x=>nameMatch(wn,x.name)&&x.distanceKm<=180)[0]||null;if(direct)return{...direct,sameRiver:true,reference:false};const ref=all.find(x=>x.distanceKm<=120)||null;return ref?{...ref,sameRiver:false,reference:true}:null}
window.FloodSafeGauge={forWaterway,nameMatch};
})();