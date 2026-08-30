(()=>{'use strict';
if(window.__fsGaugeBridgeV7)return;window.__fsGaugeBridgeV7=true;
const FRESH=60*60*1000,LOCAL_CONTEXT_KM=20;
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function flat(o){return o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o}
function coord(o){o=flat(o);const c=o?.point?.coordinates||o?.location?.coordinates||o?.centroid?.coordinates||o?.geometry?.coordinates;if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[1],+c[0]];const p=String(o?.point||o?.location||''),m=p.match(/POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i);return m?[+m[2],+m[1]]:null}
const lat=o=>{o=flat(o);return num(val(o,['latitude','lat','stationLatitude','station_latitude'])??o?.station?.latitude??o?.location?.latitude??coord(o)?.[0])};
const lon=o=>{o=flat(o);return num(val(o,['longitude','lon','lng','stationLongitude','station_longitude'])??o?.station?.longitude??o?.location?.longitude??coord(o)?.[1])};
const name=o=>{o=flat(o);return String(val(o,['river_name','riverName','station_name','stationName','title','name'])||o?.station?.name||'River station')};
const basin=o=>String(flat(o)?.basin||'');
const stamp=o=>{o=flat(o);return val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','modifiedOn','modified_on','updatedOn','updated_on','updated_at','updatedAt','retrievedAt','createdOn','created_on','date','timestamp','_alert_created_on'])};
const km=(a,b,c,d)=>{const R=6371,p=x=>x*Math.PI/180,q=Math.sin(p(c-a)/2)**2+Math.cos(p(a))*Math.cos(p(c))*Math.sin(p(d-b)/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
function fresh(o){const t=+new Date(stamp(o)||0),a=Date.now()-t;return !!t&&a>=-300000&&a<=FRESH}
function stage(o){o=flat(o);const level=num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level'])),warning=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold'])),danger=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold'])),raw=String(val(o,['status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').trim().toUpperCase();let status='normal';if(level!==null&&danger!==null&&danger>0&&level>=danger)status='danger';else if(level!==null&&warning!==null&&warning>0&&level>=warning)status='warning';else if((/ABOVE\s+DANGER|DANGER\s+LEVEL|RED/.test(raw))&&!/BELOW\s+DANGER/.test(raw))status='danger';else if((/ABOVE\s+WARNING|WARNING\s+LEVEL|ORANGE/.test(raw))&&!/BELOW\s+WARNING/.test(raw))status='warning';else if(/WATCH|RISING|INCREASING|YELLOW/.test(raw))status='watch';return{level,warning,danger,status}}
function cleanUnicode(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+(?:at|near)\s+.*/i,' ').replace(/(?:नदी|नदि|खोला)/g,' ').replace(/\b(river|khola|nadi|stream|station|gauge|bridge|highway|bazar|bazaar|riverbank)\b/g,' ').replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim()}
function variants(w){const a=[w?.name_en,w?.name_raw,w?.name,w?.name_ne].map(x=>String(x||'').trim()).filter(Boolean),seen=new Set();return a.filter(x=>{const k=cleanUnicode(x);if(!k||seen.has(k))return false;seen.add(k);return true})}
function scoreName(a,b){const A=cleanUnicode(a),B=cleanUnicode(b);if(!A||!B)return 0;if(A===B)return 100;if(A.length>=5&&B.length>=5&&(A.startsWith(B+' ')||B.startsWith(A+' ')||A.endsWith(' '+B)||B.endsWith(' '+A)))return 92;const aa=A.split(' ').filter(x=>x.length>=3),bb=B.split(' ').filter(x=>x.length>=3),common=aa.filter(x=>bb.includes(x));if(common.length>=2&&common.length===Math.min(aa.length,bb.length))return 82;return 0}
function nameMatch(a,b){return scoreName(a,b)>=82}
function statusLabel(k){const en=(window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang'))==='en';return en?({danger:'DANGER',warning:'WARNING',watch:'WATCH',normal:'NORMAL',stale:'STALE'}[k]||'UNKNOWN'):({danger:'खतरा',warning:'चेतावनी',watch:'निगरानी',normal:'सामान्य',stale:'पुरानो मापन'}[k]||'अज्ञात')}
function candidate(o,la,lo){const a=lat(o),b=lon(o);if(a===null||b===null)return null;const fo=flat(o),s=stage(o),isFresh=fresh(o),hasReading=s.level!==null||!!String(fo?.status||'').trim()||!!stamp(o);if(!hasReading)return null;return{o,name:name(o),basin:basin(o),lat:a,lon:b,distanceKm:km(la,lo,a,b),time:stamp(o),fresh:isFresh,status:isFresh?s.status:'stale',currentStatus:s.status,statusLabel:statusLabel(isFresh?s.status:'stale'),level:s.level,warning:s.warning,danger:s.danger,source:String(fo?.dataSource||fo?.data_source||'DHM / BIPAD'),officialLive:!!fo?._officialLive,sourceUrl:String(fo?._officialLivePage||'')}}
function allCandidates(la,lo){const stations=window.FloodSafe?.state?.stations||[];return stations.map(o=>candidate(o,la,lo)).filter(Boolean)}
function nearby(la,lo,maxKm=40,limit=100){return allCandidates(la,lo).filter(x=>x.fresh&&x.distanceKm<=maxKm).sort((a,b)=>a.distanceKm-b.distanceKm).slice(0,limit)}
function bestSameRiver(names,all){const scored=[];for(const x of all){let score=0;for(const n of names)score=Math.max(score,scoreName(n,x.name));if(score>=82)scored.push({...x,_score:score})}scored.sort((a,b)=>(b.fresh?1:0)-(a.fresh?1:0)||b._score-a._score||a.distanceKm-b.distanceKm);return scored[0]||null}
function bestBasin(names,all){const keys=new Set(names.map(cleanUnicode).filter(Boolean)),hits=all.filter(x=>keys.has(cleanUnicode(x.basin)));hits.sort((a,b)=>(b.fresh?1:0)-(a.fresh?1:0)||a.distanceKm-b.distanceKm);return hits[0]||null}
function forWaterway(w,la,lo){
 const names=variants(w),all=allCandidates(la,lo);if(!all.length)return null;
 const direct=bestSameRiver(names,all);if(direct)return{...direct,sameRiver:true,reference:false,coverage:direct.fresh?'same-river-national':'same-river-stale'};
 const basinHit=bestBasin(names,all);if(basinHit)return{...basinHit,sameRiver:true,reference:false,coverage:basinHit.fresh?'basin-national':'basin-stale'};
 const ref=all.filter(x=>x.fresh&&x.distanceKm<=LOCAL_CONTEXT_KM).sort((a,b)=>a.distanceKm-b.distanceKm)[0]||null;
 return ref?{...ref,sameRiver:false,reference:true,coverage:'local-20km'}:null;
}
window.FloodSafeGauge={forWaterway,nearby,nameMatch,statusLabel,LOCAL_CONTEXT_KM,FRESH_MS:FRESH,scoreName,variants};
})();