(()=>{'use strict';
if(window.__fsFloodCoreV11)return;window.__fsFloodCoreV11=true;
const $=id=>document.getElementById(id);
const B={minLon:80,maxLon:88.35,minLat:26.2,maxLat:30.5},FRESH_MS=6*60*60*1000;
const S={lat:null,lon:null,kind:null,stations:[],lastPoll:0,alertsOn:false,lastRisk:-1,feedSource:'',lang:localStorage.getItem('fs-flood-lang')==='en'?'en':'ne'};
const tr=(ne,en)=>S.lang==='en'?en:ne;
const rows=j=>Array.isArray(j)?j:(Array.isArray(j?.results)?j.results:Array.isArray(j?.data)?j.data:Array.isArray(j?.objects)?j.objects:[]);
const num=v=>{const n=Number(String(v??'').replace(/[^0-9.+-]/g,''));return Number.isFinite(n)?n:null};
const val=(o,ks)=>{for(const k of ks){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null};
function coords(o){
 const c=o?.point?.coordinates||o?.location?.coordinates||o?.centroid?.coordinates||o?.geometry?.coordinates;
 if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[1],+c[0]];
 const p=String(o?.point||o?.location||'');
 const m=p.match(/POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i);
 return m?[+m[2],+m[1]]:null;
}
const lat=o=>num(val(o,['latitude','lat','stationLatitude','station_latitude'])??o?.station?.latitude??o?.location?.latitude??coords(o)?.[0]);
const lon=o=>num(val(o,['longitude','lon','lng','stationLongitude','station_longitude'])??o?.station?.longitude??o?.location?.longitude??coords(o)?.[1]);
const name=o=>String(val(o,['river_name','riverName','station_name','stationName','title','name'])||o?.station?.name||tr('नदी स्टेशन','River station'));
const stamp=o=>val(o,['waterLevelOn','water_level_on','measuredOn','measured_on','modifiedOn','modified_on','updatedOn','updated_on','updated_at','updatedAt','createdOn','created_on','date','timestamp']);
const level=o=>num(val(o,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level']));
const warning=o=>num(val(o,['warningLevel','warning_level','warningThreshold','warning_threshold']));
const danger=o=>num(val(o,['dangerLevel','danger_level','dangerThreshold','danger_threshold']));
const rawStatus=o=>String(val(o,['status','status_name','alertStatus','alert_status','riskLevel','risk_level'])||'').trim().toUpperCase();
const inside=(la,lo)=>Number.isFinite(la)&&Number.isFinite(lo)&&la>=B.minLat&&la<=B.maxLat&&lo>=B.minLon&&lo<=B.maxLon;
const km=(a,b,c,d)=>{const R=6371,p=x=>x*Math.PI/180,q=Math.sin(p(c-a)/2)**2+Math.cos(p(a))*Math.cos(p(c))*Math.sin(p(d-b)/2)**2;return 2*R*Math.asin(Math.sqrt(q))};
async function get(url,ms=8000){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(url+(url.includes('?')?'&':'?')+'_fs11='+Date.now(),{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(t)}}
function fresh(o){const t=+new Date(stamp(o)||0),a=Date.now()-t;return !!t&&a>=-300000&&a<=FRESH_MS}
function stage(o){
 const wl=level(o),w=warning(o),d=danger(o),raw=rawStatus(o);
 if(!fresh(o))return{key:'unknown',rank:-1,wl,w,d,fresh:false};
 if(wl!==null&&d!==null&&d>0&&wl>=d)return{key:'danger',rank:3,wl,w,d,fresh:true};
 if(wl!==null&&w!==null&&w>0&&wl>=w)return{key:'warning',rank:2,wl,w,d,fresh:true};
 if((/ABOVE\s+DANGER|DANGER\s+LEVEL|RED/.test(raw))&&!/BELOW\s+DANGER/.test(raw))return{key:'danger',rank:3,wl,w,d,fresh:true};
 if((/ABOVE\s+WARNING|WARNING\s+LEVEL|ORANGE/.test(raw))&&!/BELOW\s+WARNING/.test(raw))return{key:'warning',rank:2,wl,w,d,fresh:true};
 if(/WATCH|RISING|INCREASING|YELLOW/.test(raw))return{key:'watch',rank:1,wl,w,d,fresh:true};
 if(/BELOW\s+WARNING|NORMAL|GREEN|SAFE|STEADY/.test(raw)||wl!==null)return{key:'normal',rank:0,wl,w,d,fresh:true};
 return{key:'unknown',rank:-1,wl,w,d,fresh:true};
}
function age(t){const x=+new Date(t||0);if(!x)return tr('समय उपलब्ध छैन','Time unavailable');const s=Math.max(0,Math.floor((Date.now()-x)/1000));if(s<60)return tr(`${s} सेकेन्ड अघि`,`${s}s ago`);const m=Math.floor(s/60);if(m<60)return tr(`${m} मिनेट अघि`,`${m}m ago`);return tr(`${Math.floor(m/60)} घण्टा अघि`,`${Math.floor(m/60)}h ago`)}
function statusLabel(k){return S.lang==='en'?({danger:'DANGER',warning:'WARNING',watch:'WATCH',normal:'NORMAL',unknown:'UNKNOWN'}[k]||'UNKNOWN'):({danger:'खतरा',warning:'चेतावनी',watch:'निगरानी',normal:'सामान्य',unknown:'अज्ञात'}[k]||'अज्ञात')}
function tick(){
 if($('clock'))$('clock').textContent=new Intl.DateTimeFormat(S.lang==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date())+' NPT';
 if($('feedFresh')&&S.lastPoll){const src=S.feedSource?` • ${S.feedSource}`:'';$('feedFresh').textContent=tr(`आधिकारिक नदी data ${Math.floor((Date.now()-S.lastPoll)/1000)} सेकेन्ड अघि जाँचियो${src}`,`Official river data checked ${Math.floor((Date.now()-S.lastPoll)/1000)}s ago${src}`)}
}
function applyLanguage(){
 document.documentElement.lang=S.lang==='en'?'en':'ne';if($('langBtn'))$('langBtn').textContent=S.lang==='ne'?'English':'नेपाली';
 const T={weatherSupport:['स्थानीय वर्षा/मौसम + आधिकारिक नदी gauge जोखिम','Local rain/weather + official river gauge risk'],locateBtn:['◎ मेरो हालको स्थान','◎ My Current Location'],alertBtn:[S.alertsOn?'🔔 चेतावनी सक्रिय':'🔔 बाढी चेतावनी',S.alertsOn?'🔔 Warning Alert ON':'🔔 Flood Warning Alert'],localRiskTitle:['🛡️ स्थानीय बाढी जोखिम','🛡️ Local Flood Risk'],stationLabel:['ताजा आधिकारिक स्टेशन','Fresh official stations'],warningLabel:['चेतावनी','Warning'],dangerLabel:['खतरा','Danger'],nearTitle:['🌊 नजिकका नदी / Gauge','🌊 Nearby Rivers / Gauges'],nearSub:['DHM / BIPAD आधिकारिक मापन • ३० किमि स्थानीय निगरानी','Official DHM / BIPAD readings • 30 km local monitoring'],impactTitle:['🆘 बाढी मानवीय असर','🆘 Flood Human Impact'],deathLabel:['मृत्यु','Deaths'],missingLabel:['सम्पर्कविहीन','Missing'],rescuedLabel:['उद्धार / सुरक्षित भेटिएका','Rescued / Found safe'],mapTitle:['🇳🇵 प्रत्यक्ष नदी प्रवाह नक्सा','🇳🇵 Live River Flow Map'],mapSub:['नदी/खोला छान्दा उपलब्ध official gauge data देखिन्छ','Tap a river/stream to see available official gauge data'],riverStatusTitle:['🌊 नेपालभरि प्रत्यक्ष नदी स्थिति','🌊 Nepal Realtime River Status'],riverStatusSub:['DHM / BIPAD बाट उपलब्ध ताजा water-level/status मात्र','Fresh water-level/status available from DHM / BIPAD'],newsTitle:['📰 नेपालका पछिल्ला समाचार • LIVE','📰 Latest Nepal News • LIVE'],newsSub:['RONB + प्रमाणित राष्ट्रिय मिडिया • पछिल्लो ३० मिनेटका नयाँ पोस्ट मात्र','RONB + verified national media • only new posts from the last 30 minutes'],navHome:['बाढी गृह','Flood Home'],navMap:['नदी नक्सा','River Map'],navNews:['नेपाल समाचार','Nepal News']};
 for(const[id,a]of Object.entries(T)){if($(id))$(id).textContent=a[S.lang==='en'?1:0]}
 if($('outsideNoticeText'))$('outsideNoticeText').textContent=tr('नेपालको बाढी अवस्था हेर्न नक्साबाट निगरानी क्षेत्र छान्नुहोस्।','Choose a monitoring area on the map to view Nepal flood conditions.');
 renderStations();risk();renderNational();window.dispatchEvent(new CustomEvent('fslanguage',{detail:{lang:S.lang}}));
}
function clearWeather(){if($('temp'))$('temp').textContent='—°';for(const id of['rain','humidity','wind'])if($(id))$(id).textContent='—';if($('weatherText'))$('weatherText').textContent=tr('नेपालको निगरानी स्थान छान्नुहोस्','Choose a Nepal monitoring location')}
async function weather(){if(!inside(S.lat,S.lon))return clearWeather();try{const j=await get(`https://api.open-meteo.com/v1/forecast?latitude=${S.lat}&longitude=${S.lon}&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m&timezone=Asia%2FKathmandu`,7000),c=j.current||{};$('temp').textContent=c.temperature_2m!=null?Math.round(c.temperature_2m)+'°':'—°';$('rain').textContent=(c.rain??c.precipitation)!=null?Number(c.rain??c.precipitation).toFixed(1)+' mm':'—';$('humidity').textContent=c.relative_humidity_2m!=null?Math.round(c.relative_humidity_2m)+'%':'—';$('wind').textContent=c.wind_speed_10m!=null?Math.round(c.wind_speed_10m)+' km/h':'—';$('weatherText').textContent=(c.precipitation??0)>2?tr('अहिले वर्षा भइरहेको छ','Rain now'):(c.precipitation??0)>0?tr('हल्का वर्षा','Light rain'):tr('अहिले वर्षा कम वा छैन','Little or no rain now')}catch{if($('weatherText'))$('weatherText').textContent=tr('मौसम feed अहिले उपलब्ध छैन','Weather feed unavailable')}}
function nearestFrom(la,lo,max=100){return S.stations.map(o=>{const a=lat(o),b=lon(o);return{o,s:stage(o),d:a!==null&&b!==null?km(la,lo,a,b):Infinity}}).filter(x=>Number.isFinite(x.d)).sort((a,b)=>a.d-b.d).slice(0,max)}
function nearest(max=50){return inside(S.lat,S.lon)?nearestFrom(S.lat,S.lon,max):[]}
function infoFor(o,distanceKm=0){if(!o)return null;const s=stage(o);if(!s.fresh)return null;return{name:name(o),distanceKm,status:s.key,statusLabel:statusLabel(s.key),level:s.wl,warning:s.w,danger:s.d,time:stamp(o),age:age(stamp(o)),lat:lat(o),lon:lon(o),source:'DHM / BIPAD'} }
function stationInfoAt(la,lo,maxKm=35){const x=nearestFrom(la,lo,30).find(q=>q.d<=maxKm&&q.s.fresh);return x?infoFor(x.o,x.d):null}
function noLocal(msg,badge='LOCATION'){if($('riskValue')){$('riskValue').className='risk unknown';$('riskValue').textContent='—'}if($('riskBadge')){$('riskBadge').className='badge';$('riskBadge').textContent=badge}if($('riskText'))$('riskText').textContent=msg;if($('nearStations'))$('nearStations').innerHTML=`<div class="empty">${msg}</div>`;S.lastRisk=-1}
function renderStations(){const out=$('nearStations');if(!out)return;if(!inside(S.lat,S.lon)){out.innerHTML=`<div class="empty">${tr('नेपाल नक्सामा क्षेत्र छान्नुहोस्।','Choose an area on the Nepal map.')}</div>`;return}const n=nearest().filter(x=>x.d<=30&&x.s.fresh&&x.s.rank>=0).slice(0,6);out.innerHTML='';if(!n.length){out.innerHTML=`<div class="empty">${tr('३० किमि भित्र ताजा आधिकारिक gauge reading भेटिएन।','No fresh official gauge reading within 30 km.')}</div>`;return}for(const x of n){const d=document.createElement('div');d.className='station';d.innerHTML=`<strong>${name(x.o)}</strong><span>${x.d.toFixed(1)} km • ${statusLabel(x.s.key)} • ${x.s.wl??'—'} m • ${age(stamp(x.o))}</span>`;out.appendChild(d)}}
function renderNational(){const out=$('nationalRiverList');if(!out)return;const a=S.stations.map(o=>({o,s:stage(o),t:+new Date(stamp(o)||0)})).filter(x=>x.s.fresh&&x.s.rank>=0).sort((a,b)=>b.s.rank-a.s.rank||b.t-a.t).slice(0,40);out.innerHTML='';if(!a.length){out.innerHTML=`<div class="empty">${tr('ताजा आधिकारिक नदी water-level/status उपलब्ध छैन।','No fresh official river water-level/status available.')}</div>`;return}for(const x of a){const d=document.createElement('div');d.className='station nationalRiver';d.innerHTML=`<strong>${name(x.o)}</strong><span>${statusLabel(x.s.key)} • ${x.s.wl!=null?x.s.wl+' m':'level —'} • W ${x.s.w!=null?x.s.w+' m':'—'} • D ${x.s.d!=null?x.s.d+' m':'—'} • ${age(stamp(x.o))}</span>`;out.appendChild(d)}if($('nationalRiverFresh'))$('nationalRiverFresh').textContent=tr(`${a.length} ताजा official gauge reading देखाइएका छन्`,`Showing ${a.length} fresh official gauge readings`)}
function risk(){if(!inside(S.lat,S.lon))return noLocal(tr('नेपालभित्र location वा map area छानेपछि मात्र स्थानीय जोखिम देखाइन्छ।','Local risk appears after selecting a Nepal location or map area.'));const n=nearest().filter(x=>x.d<=30&&x.s.rank>=0&&x.s.fresh);if(!n.length){if($('riskValue')){$('riskValue').className='risk unknown';$('riskValue').textContent=tr('अज्ञात','UNKNOWN')}if($('riskBadge')){$('riskBadge').className='badge';$('riskBadge').textContent=tr('ताजा GAUGE छैन','NO FRESH GAUGE')}if($('riskText'))$('riskText').textContent=tr('३० किमि भित्र ताजा प्रमाणित gauge reading छैन।','No fresh verified gauge reading within 30 km.');S.lastRisk=-1;return}const top=n.sort((a,b)=>b.s.rank-a.s.rank||a.d-b.d)[0],r=top.s.rank,key=top.s.key;$('riskValue').className='risk '+key;$('riskValue').textContent=statusLabel(key);$('riskBadge').className='badge '+(r>=3?'red':r>=1?'amber':'green');$('riskBadge').textContent=statusLabel(key);$('riskText').textContent=`${name(top.o)} • ${top.d.toFixed(1)} km • ${top.s.wl??'—'} m • ${age(stamp(top.o))}`;if(r>=2&&S.alertsOn&&r>S.lastRisk)alarm(top);S.lastRisk=r}
function chime(){try{const C=window.AudioContext||window.webkitAudioContext,a=new C(),g=a.createGain();g.gain.setValueAtTime(.0001,a.currentTime);g.gain.exponentialRampToValueAtTime(.1,a.currentTime+.04);g.gain.exponentialRampToValueAtTime(.0001,a.currentTime+1.4);g.connect(a.destination);[0,.38,.76].forEach((q,i)=>{const o=a.createOscillator();o.type='sine';o.frequency.value=[700,850,700][i];o.connect(g);o.start(a.currentTime+q);o.stop(a.currentTime+q+.23)});setTimeout(()=>a.close(),1700)}catch{}}
function alarm(x){chime();if($('alarmBanner'))$('alarmBanner').classList.add('show');if($('alarmTitle'))$('alarmTitle').textContent=x.s.rank>=3?tr('🚨 उच्च खतरा','🚨 DANGER'):tr('⚠️ चेतावनी','⚠️ WARNING');if($('alarmText'))$('alarmText').textContent=`${name(x.o)} • ${x.d.toFixed(1)} km • ${x.s.wl??'—'} m`;if('Notification'in window&&Notification.permission==='granted')new Notification('FloodSafe Nepal',{body:$('alarmText')?.textContent||'Flood warning',icon:'../v24/icon.svg'})}
async function alerts(){S.alertsOn=!S.alertsOn;if(S.alertsOn&&'Notification'in window&&Notification.permission==='default'){try{await Notification.requestPermission()}catch{}}applyLanguage()}
const normName=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\b(river|khola|nadi|stream|station|gauge|at|near|bridge)\b/g,' ').replace(/[^a-z0-9]+/g,' ').replace(/\s+/g,' ').trim();
function stationKey(o){const id=val(o,['stationSeriesId','station_series_id','stationId','station_id'])??o?.station?.stationSeriesId??o?.station?.id;if(id!==null&&id!==undefined&&id!=='')return'id:'+String(id);const n=normName(name(o)),la=lat(o),lo=lon(o);if(n)return'name:'+n;return`xy:${la??'x'}|${lo??'x'}`}
function measured(o){return level(o)!==null||!!rawStatus(o)}
function newest(a,b){const ta=+new Date(stamp(a)||0),tb=+new Date(stamp(b)||0);if(tb>ta)return b;if(ta>tb)return a;return measured(b)&&!measured(a)?b:a}
function mergeRows(readings,meta){
 const metas=new Map();for(const o of meta||[]){metas.set(stationKey(o),o);const n=normName(name(o));if(n)metas.set('name:'+n,o)}
 const out=new Map();for(const r of readings||[]){const k=stationKey(r),n=normName(name(r)),m=metas.get(k)||metas.get('name:'+n)||null;const joined=m?Object.assign({},m,r):r;const prev=out.get(k);out.set(k,prev?newest(prev,joined):joined)}
 return[...out.values()];
}
let localCore={at:0,rows:[]};
async function localRiverRows(){if(localCore.rows.length&&Date.now()-localCore.at<60000)return localCore.rows;try{const j=await get('../../data/floodsafe-core.json',9000),a=Array.isArray(j?.rivers)?j.rivers:[];localCore={at:Date.now(),rows:a};return a}catch{return localCore.rows}}
async function poll(){
 const base='https://bipadportal.gov.np/api/v1/';
 try{
  const [river,trimmed,stations]=await Promise.allSettled([get(base+'river/?limit=1000'),get(base+'river-trimed/?limit=1000'),get(base+'river-stations/?limit=1000')]);
  const primary=river.status==='fulfilled'?rows(river.value):[],secondary=trimmed.status==='fulfilled'?rows(trimmed.value):[],meta=stations.status==='fulfilled'?rows(stations.value):[];
  let readingRows=primary.filter(measured);let source='DHM / BIPAD river';
  if(!readingRows.length){readingRows=secondary.filter(measured);source='DHM / BIPAD river-trimed'}
  if(!readingRows.length){readingRows=(await localRiverRows()).filter(measured);source='BIPAD official 5-min snapshot'}
  S.stations=mergeRows(readingRows,meta).filter(o=>stamp(o)||measured(o));S.feedSource=source;S.lastPoll=Date.now();
  const st=S.stations.map(stage),freshCount=st.filter(x=>x.fresh&&x.rank>=0).length;
  if($('stationCount'))$('stationCount').textContent=freshCount;if($('warningCount'))$('warningCount').textContent=st.filter(x=>x.rank===2).length;if($('dangerCount'))$('dangerCount').textContent=st.filter(x=>x.rank===3).length;
  renderStations();renderNational();risk();tick();window.dispatchEvent(new CustomEvent('fsriverupdate',{detail:{stations:S.stations.length,fresh:freshCount,source:S.feedSource}}));
 }catch{if($('feedFresh'))$('feedFresh').textContent=tr('आधिकारिक नदी data उपलब्ध छैन','Official river data unavailable')}
}
async function setFocus(la,lo,kind='map'){if(!inside(la,lo))return;S.lat=la;S.lon=lo;S.kind=kind;if($('outsideNotice'))$('outsideNotice').hidden=true;if($('place'))$('place').textContent=kind==='gps'?tr('📍 नेपालमा हालको स्थान सक्रिय','📍 Current Nepal location active'):tr(`📍 नक्साबाट क्षेत्र चयन • ${la.toFixed(3)}, ${lo.toFixed(3)}`,`📍 Map area selected • ${la.toFixed(3)}, ${lo.toFixed(3)}`);await weather();renderStations();risk()}
function outside(){S.lat=S.lon=null;S.kind=null;if($('outsideNotice'))$('outsideNotice').hidden=false;if($('place'))$('place').textContent=tr('🌍 तपाईं अहिले नेपाल बाहिर हुनुहुन्छ','🌍 You are currently outside Nepal');clearWeather();noLocal(tr('नेपाल नक्सामा निगरानी गर्न चाहेको क्षेत्र छान्नुहोस्।','Choose an area on the Nepal map to monitor.'))}
function locate(){if(!navigator.geolocation)return outside();if($('place'))$('place').textContent=tr('📍 GPS स्थान खोजिँदैछ…','📍 Finding GPS location…');navigator.geolocation.getCurrentPosition(p=>inside(p.coords.latitude,p.coords.longitude)?setFocus(p.coords.latitude,p.coords.longitude,'gps'):outside(),()=>{if($('place'))$('place').textContent=tr('📍 स्थान अनुमति उपलब्ध छैन','📍 Location permission unavailable')},{enableHighAccuracy:true,timeout:12000,maximumAge:30000})}
function toggleLang(){S.lang=S.lang==='ne'?'en':'ne';localStorage.setItem('fs-flood-lang',S.lang);applyLanguage();tick();if(inside(S.lat,S.lon))setFocus(S.lat,S.lon,S.kind||'map');else clearWeather()}
window.FloodSafe={setFocus,poll,state:S,stationInfoAt,stationInfoFor:infoFor,tr,statusLabel,age};
function boot(){if($('locateBtn'))$('locateBtn').addEventListener('click',locate);if($('alertBtn'))$('alertBtn').addEventListener('click',alerts);if($('langBtn'))$('langBtn').addEventListener('click',toggleLang);applyLanguage();tick();setInterval(tick,1000);poll();setInterval(poll,5000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();