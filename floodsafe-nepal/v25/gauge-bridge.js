(()=>{'use strict';
if(window.__fsGaugeBridgeV17)return;window.__fsGaugeBridgeV17=true;
const LIVE=60*1000,RECENT=20*60*1000,FUTURE=5*60*1000;
const SAME_RIVER_LOCAL_KM=35,REGIONAL_KM=70,LINE_EXACT_KM=2.2;
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
const flat=o=>o&&typeof o==='object'&&o.fields&&typeof o.fields==='object'?Object.assign({},o.fields,o):o;
function coord(o){o=flat(o);const c=o?.point?.coordinates||o?.location?.coordinates||o?.geometry?.coordinates;if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[1],+c[0]];const p=String(o?.point||o?.location||''),m=p.match(/POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i);if(m)return[+m[2],+m[1]];const la=num(val(o,['latitude','lat','stationLatitude','station_latitude'])),lo=num(val(o,['longitude','lon','lng','stationLongitude','station_longitude']));return la!==null&&lo!==null?[la,lo]:null}
const name=o=>String(val(flat(o),['river_name','riverName','station_name','stationName','title','name'])||flat(o)?.station?.name||'River station');
const basin=o=>String(val(flat(o),['basin','basin_name','basinName'])||'');
const district=o=>String(val(flat(o),['districtName','district_name','district'])||'');
const stationId=o=>String(val(flat(o),['stationSeriesId','station_series_id','stationId','station_id','stationIndex','id'])||'');
const discharge=o=>num(val(flat(o),['discharge','currentDischarge','current_discharge','flow','flowRate','flow_rate']));
// Hydrological observation time only. Fetch/retrieval/created timestamps never count.
const stamp=o=>val(flat(o),['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);
const km=(a,b,c,d)=>{const R=6371,p=x=>x*Math.PI/180,q=Math.sin(p(c-a)/2)**2+Math.cos(p(a))*Math.cos(p(c))*Math.sin(p(d-b)/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
function ageMs(o){const t=+new Date(stamp(o)||0);return t?Date.now()-t:Infinity}
function trusted(o){o=flat(o);if(o?._measurementTimeTrusted===false||o?._current20m===false)return false;const a=ageMs(o);return Number.isFinite(a)&&a>=-FUTURE&&a<=RECENT}
function isLive(o){return trusted(o)&&ageMs(o)<=LIVE}
function clean(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+(?:at|near)\s+.*/i,' ').replace(/(?:नदी|नदि|खोला)/g,' ').replace(/\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b/g,' ').replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim()}
const ALIAS=new Map([
 ['भोटेकोशी','bhotekoshi'],['भोटेकोसी','bhotekoshi'],['bhote koshi','bhotekoshi'],['bhote kosi','bhotekoshi'],['bhotekoshi','bhotekoshi'],
 ['सुनकोशी','sunkoshi'],['sun koshi','sunkoshi'],['sun kosi','sunkoshi'],['sunkoshi','sunkoshi'],
 ['सप्तकोशी','saptakoshi'],['sapta koshi','saptakoshi'],['sapta kosi','saptakoshi'],['saptakoshi','saptakoshi'],
 ['कालीगण्डकी','kaligandaki'],['kali gandaki','kaligandaki'],['kali gandki','kaligandaki'],['kaligandaki','kaligandaki'],
 ['बुढीगण्डकी','budhigandaki'],['बूढीगण्डकी','budhigandaki'],['budi gandaki','budhigandaki'],['budhi gandaki','budhigandaki'],['budhigandaki','budhigandaki'],
 ['मर्स्याङ्दी','marsyangdi'],['मर्स्यांग्दी','marsyangdi'],['marsyangdi','marsyangdi'],['marshyangdi','marsyangdi'],
 ['त्रिशूली','trishuli'],['त्रिशुली','trishuli'],['trishuli','trishuli'],
 ['नारायणी','narayani'],['narayani','narayani'],['कर्णाली','karnali'],['karnali','karnali'],['महाकाली','mahakali'],['mahakali','mahakali'],
 ['बागमती','bagmati'],['bagmati','bagmati'],['बबई','babai'],['babai','babai'],['अरुण','arun'],['arun','arun'],['तमोर','tamor'],['tamor','tamor'],
 ['कन्काई','kankai'],['कन्काइ','kankai'],['kankai','kankai'],['कमला','kamala'],['kamala','kamala'],['मेची','mechi'],['mechi','mechi'],
 ['तिनाउ','tinau'],['tinau','tinau'],['सेती','seti'],['seti','seti']
]);
function canonical(s){const c=clean(s);return ALIAS.get(c)||c}
function variants(w){const a=[w?.name_en,w?.name_raw,w?.name,w?.name_ne].map(x=>String(x||'').trim()).filter(Boolean),seen=new Set();return a.filter(x=>{const k=canonical(x);if(!k||seen.has(k))return false;seen.add(k);return true})}
function editDistance(a,b){a=canonical(a);b=canonical(b);if(!a||!b)return 99;const m=a.length,n=b.length,prev=Array.from({length:n+1},(_,i)=>i),cur=new Array(n+1);for(let i=1;i<=m;i++){cur[0]=i;for(let j=1;j<=n;j++)cur[j]=Math.min(cur[j-1]+1,prev[j]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));for(let j=0;j<=n;j++)prev[j]=cur[j]}return prev[n]}
function scoreName(a,b){const A=canonical(a),B=canonical(b);if(!A||!B)return 0;if(A===B)return 100;if(A.length>=4&&B.length>=4&&(A.startsWith(B+' ')||B.startsWith(A+' ')||A.endsWith(' '+B)||B.endsWith(' '+A)))return 96;const aa=A.split(' ').filter(x=>x.length>=3),bb=B.split(' ').filter(x=>x.length>=3),common=aa.filter(x=>bb.includes(x));if(common.length>=1){const ratio=common.length/Math.max(aa.length,bb.length);if(ratio>=.75)return 93;if(ratio>=.5)return 88}const mx=Math.max(A.length,B.length),ed=mx<=24?editDistance(A,B):99;if(mx>=5&&ed<=1)return 94;if(mx>=7&&ed<=2)return 91;return 0}
function stage(o){o=flat(o);const level=num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level'])),warning=num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold'])),danger=num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold'])),raw=String(val(o,['_officialStatus','status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').trim().toUpperCase();let status='normal';if(level!==null&&danger!==null&&danger>0&&level>=danger)status='danger';else if(level!==null&&warning!==null&&warning>0&&level>=warning)status='warning';else if(/DANGER|RED/.test(raw)&&!/BELOW\s+DANGER/.test(raw))status='danger';else if(/WARNING|ORANGE/.test(raw)&&!/BELOW\s+WARNING/.test(raw))status='warning';else if(/WATCH|RISING|INCREASING|YELLOW/.test(raw))status='watch';return{level,warning,danger,status,raw}}
function baseCandidate(o){o=flat(o);const c=coord(o),s=stage(o),t=stamp(o);if(!c||!trusted(o)||s.level===null)return null;return{o,name:name(o),basin:basin(o),district:district(o),stationId:stationId(o),lat:c[0],lon:c[1],time:t,ageMs:ageMs(o),fresh:isLive(o),recent:true,status:s.status,rawStatus:s.raw,level:s.level,warning:s.warning,danger:s.danger,discharge:discharge(o),source:String(o?.dataSource||o?.data_source||'DHM / BIPAD'),sourceUrl:String(o?._officialLivePage||o?.source_url||o?.sourceUrl||'')}}
function allBase(){return(window.FloodSafe?.state?.stations||[]).map(baseCandidate).filter(Boolean)}
function points(w){if(Array.isArray(w?.pts))return w.pts.filter(p=>Array.isArray(p)&&Number.isFinite(+p[0])&&Number.isFinite(+p[1])).map(p=>[+p[0],+p[1]]);if(Array.isArray(w?.geometry_points))return w.geometry_points;return[]}
function pointSegKm(la,lo,a,b){const lat0=la*Math.PI/180,sc=Math.cos(lat0),x1=(a[0]-lo)*111.32*sc,y1=(a[1]-la)*110.574,x2=(b[0]-lo)*111.32*sc,y2=(b[1]-la)*110.574,dx=x2-x1,dy=y2-y1,den=dx*dx+dy*dy,t=den?Math.max(0,Math.min(1,-(x1*dx+y1*dy)/den)):0,x=x1+t*dx,y=y1+t*dy;return Math.sqrt(x*x+y*y)}
function lineDistanceKm(la,lo,pts){if(!Array.isArray(pts)||pts.length<2)return Infinity;let best=Infinity;for(let i=1;i<pts.length;i++)best=Math.min(best,pointSegKm(la,lo,pts[i-1],pts[i]));return best}
function enrich(c,la,lo,names,pts){let ns=0;for(const n of names)ns=Math.max(ns,scoreName(n,c.name));const distanceKm=km(la,lo,c.lat,c.lon),lineKm=lineDistanceKm(c.lat,c.lon,pts);return{...c,distanceKm,lineDistanceKm:lineKm,nameScore:ns}}
function confidence(x,method){if(method==='name+geometry'||x.nameScore>=98&&x.lineDistanceKm<=LINE_EXACT_KM)return'high';if(method==='geometry'&&x.lineDistanceKm<=1)return'high';if(x.nameScore>=93)return'high';return'medium'}
function forWaterway(w,la,lo){const names=variants(w),pts=points(w);if((!Number.isFinite(la)||!Number.isFinite(lo))&&pts.length){const p=pts[Math.floor((pts.length-1)/2)];lo=p[0];la=p[1]}if(!Number.isFinite(la)||!Number.isFinite(lo))return null;const all=allBase().map(x=>enrich(x,la,lo,names,pts));if(!all.length)return null;
  const local=[];for(const x of all){const byName=x.nameScore>=91,byGeom=x.lineDistanceKm<=LINE_EXACT_KM;if(!byName&&!byGeom)continue;const method=byName&&byGeom?'name+geometry':byGeom?'geometry':'name';const localEnough=x.distanceKm<=SAME_RIVER_LOCAL_KM||byGeom;local.push({...x,_method:method,_local:localEnough})}
  local.sort((a,b)=>(b._local-a._local)||(b.nameScore-a.nameScore)||(a.lineDistanceKm-b.lineDistanceKm)||(a.distanceKm-b.distanceKm)||(a.ageMs-b.ageMs));const best=local[0]||null;
  if(best){return{...best,sameRiver:true,local:!!best._local,reference:!best._local,sameRiverRemote:!best._local,archived:false,matchMethod:best._method,matchConfidence:confidence(best,best._method),coverage:best._local?(best.fresh?'same-river-live':'same-river-current'):'same-river-remote-reference'}}
  const regional=all.filter(x=>x.distanceKm<=REGIONAL_KM).sort((a,b)=>a.distanceKm-b.distanceKm||a.ageMs-b.ageMs)[0]||null;
  return regional?{...regional,sameRiver:false,local:false,reference:true,sameRiverRemote:false,archived:false,matchMethod:'regional-nearest',matchConfidence:'reference-only',coverage:'regional-reference'}:null
}
function nearby(la,lo,maxKm=40,limit=100){return allBase().map(x=>({...x,distanceKm:km(la,lo,x.lat,x.lon)})).filter(x=>x.distanceKm<=maxKm).sort((a,b)=>a.distanceKm-b.distanceKm||a.ageMs-b.ageMs).slice(0,limit)}
window.FloodSafeGauge={forWaterway,nearby,SAME_RIVER_LOCAL_KM,REGIONAL_KM,LINE_EXACT_KM,LIVE_MS:LIVE,RECENT_MS:RECENT,scoreName,canonical,variants,lineDistanceKm};
})();