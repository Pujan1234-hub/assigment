(()=>{'use strict';
if(window.__fsGaugeBridgeV5)return;window.__fsGaugeBridgeV5=true;
const FRESH=24*60*60*1000,EXACT_MAX_KM=120,LOCAL_CONTEXT_KM=20;
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function coord(o){o=flat(o);const c=o?.point?.coordinates||o?.location?.coordinates||o?.centroid?.coordinates||o?.geometry?.coordinates;if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[1],+c[0]];const p=String(o?.point||o?.location||''),m=p.match(/POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i);return m?[+m[2],+m[1]]:null}
const lat=o=>{o=flat(o);return num(val(o,['latitude','lat','stationLatitude','station_latitude'])??o?.station?.latitude??o?.location?.latitude??coord(o)?.[0])};
const lon=o=>{o=flat(o);return num(val(o,['longitude','lon','lng','stationLongitude','station_longitude'])??o?.station?.longitude??o?.location?.longitude??coord(o)?.[1])};
const name=o=>{o=flat(o);return String(val(o,['river_name','riverName','station_name','stationName','title','name'])||o?.station?.name||'River station')};
const basin=o=>String(flat(o)?.basin||'');
const stamp=o=>{o=flat(o);return val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','modifiedOn','modified_on','updatedOn','updated_on','updated_at','updatedAt','createdOn','created_on','date','timestamp','_alert_created_on'])};
const km=(a,b,c,d)=>{const R=6371,p=x=>x*Math.PI/180,q=Math.sin(p(c-a)/2)**2+Math.cos(p(a))*Math.cos(p(c))*Math.sin(p(d-b)/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
function fresh(o){const t=+new Date(stamp(o)||0);return !!t&&Date.now()-t>=-300000&&Date.now()-t<=FRESH}
function stage(o){o=flat(o);const level=num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level'])),warning=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold'])),danger=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold'])),raw=String(val(o,['status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').trim().toUpperCase();let status='normal';if(level!==null&&danger!==null&&danger>0&&level>=danger)status='danger';else if(level!==null&&warning!==null&&warning>0&&level>=warning)status='warning';else if((/ABOVE\s+DANGER|DANGER\s+LEVEL|RED/.test(raw))&&!/BELOW\s+DANGER/.test(raw))status='danger';else if((/ABOVE\s+WARNING|WARNING\s+LEVEL|ORANGE/.test(raw))&&!/BELOW\s+WARNING/.test(raw))status='warning';else if(/WATCH|RISING|INCREASING|YELLOW/.test(raw))status='watch';return{level,warning,danger,status}}
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\b(river|khola|nadi|stream|station|gauge|at|near|bridge|highway|bazar|bazaar|riverbank)\b/g,' ').replace(/[^a-z0-9]+/g,' ').replace(/\s+/g,' ').trim()}
function tokens(s){return norm(s).split(/\s+/).filter(x=>x.length>=3)}
function nameMatch(a,b){const A=tokens(a),B=tokens(b);if(!A.length||!B.length)return false;const common=A.filter(x=>B.includes(x));if(common.length>=1)return true;const na=norm(a),nb=norm(b);return na.length>=4&&nb.length>=4&&(na.includes(nb)||nb.includes(na))}
function statusLabel(k){const en=(window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang'))==='en';return en?({danger:'DANGER',warning:'WARNING',watch:'WATCH',normal:'NORMAL'}[k]||'UNKNOWN'):({danger:'खतरा',warning:'चेतावनी',watch:'निगरानी',normal:'सामान्य'}[k]||'अज्ञात')}
function candidate(o,la,lo){const a=lat(o),b=lon(o);if(a===null||b===null||!fresh(o))return null;const s=stage(o);return{o,name:name(o),basin:basin(o),lat:a,lon:b,distanceKm:km(la,lo,a,b),time:stamp(o),statusLabel:statusLabel(s.status),...s}}
function nearby(la,lo,maxKm=40,limit=100){const stations=window.FloodSafe?.state?.stations||[];return stations.map(o=>candidate(o,la,lo)).filter(Boolean).filter(x=>x.distanceKm<=maxKm).sort((a,b)=>a.distanceKm-b.distanceKm).slice(0,limit)}
function forWaterway(w,la,lo){
 const wn=String(w?.name_en||w?.name||w?.name_ne||w?.name_raw||'').trim();
 const all=nearby(la,lo,EXACT_MAX_KM,250);if(!all.length)return null;
 const direct=wn?all.filter(x=>nameMatch(wn,x.name)&&x.distanceKm<=EXACT_MAX_KM).sort((a,b)=>a.distanceKm-b.distanceKm)[0]||null:null;
 if(direct)return{...direct,sameRiver:true,reference:false,coverage:'exact-name'};
 const wnNorm=norm(wn);
 const basinHit=wnNorm?all.filter(x=>norm(x.basin)===wnNorm&&x.distanceKm<=EXACT_MAX_KM).sort((a,b)=>a.distanceKm-b.distanceKm)[0]||null:null;
 if(basinHit)return{...basinHit,sameRiver:true,reference:false,coverage:'basin-match'};
 const ref=all.find(x=>x.distanceKm<=LOCAL_CONTEXT_KM)||null;
 return ref?{...ref,sameRiver:false,reference:true,coverage:'local-20km'}:null;
}
window.FloodSafeGauge={forWaterway,nearby,nameMatch,statusLabel,EXACT_MAX_KM,LOCAL_CONTEXT_KM};
})();