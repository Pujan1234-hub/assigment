(()=>{
'use strict';
if(window.__SATHI_APP_AWARE_V1__)return;
window.__SATHI_APP_AWARE_V1__=true;

const $=s=>document.querySelector(s);
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[?!.:,;()\[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const has=(q,...xs)=>xs.some(x=>q.includes(norm(x)));
const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
const firstText=(o,keys)=>{for(const k of keys){const v=o?.[k];if(v!==undefined&&v!==null&&String(v).trim())return String(v).trim()}return''};
const firstNum=(o,keys)=>{for(const k of keys){const n=num(o?.[k]);if(n!==null)return n}return null};
const esc=s=>String(s||'').replace(/\s+/g,' ').trim();

const DISTRICTS=[
'Achham','Arghakhanchi','Baglung','Baitadi','Bajhang','Bajura','Banke','Bara','Bardiya','Bhaktapur','Bhojpur','Chitwan','Dadeldhura','Dailekh','Dang','Darchula','Dhading','Dhankuta','Dhanusha','Dolakha','Dolpa','Doti','Gorkha','Gulmi','Humla','Ilam','Jajarkot','Jhapa','Jumla','Kailali','Kalikot','Kanchanpur','Kapilvastu','Kaski','Kathmandu','Kavrepalanchok','Khotang','Lalitpur','Lamjung','Mahottari','Makwanpur','Manang','Morang','Mugu','Mustang','Myagdi','Nawalpur','Nawalparasi West','Nuwakot','Okhaldhunga','Palpa','Panchthar','Parbat','Parsa','Pyuthan','Ramechhap','Rasuwa','Rautahat','Rolpa','Rukum East','Rukum West','Rupandehi','Salyan','Sankhuwasabha','Saptari','Sarlahi','Sindhuli','Sindhupalchok','Siraha','Solukhumbu','Sunsari','Surkhet','Syangja','Tanahun','Taplejung','Terhathum','Udayapur'
];
const DISTRICT_ALIASES={
  ktm:'Kathmandu',kathmandu:'Kathmandu','काठमाडौं':'Kathmandu','काठमाण्डौ':'Kathmandu',
  jhapa:'Jhapa','झापा':'Jhapa',chitwan:'Chitwan','चितवन':'Chitwan',
  lalitpur:'Lalitpur',patan:'Lalitpur','ललितपुर':'Lalitpur',
  bhaktapur:'Bhaktapur','भक्तपुर':'Bhaktapur',pokhara:'Kaski',kaski:'Kaski','कास्की':'Kaski',
  morang:'Morang','मोरङ':'Morang',sunsari:'Sunsari','सुनसरी':'Sunsari',
  rupandehi:'Rupandehi','रुपन्देही':'Rupandehi',kailali:'Kailali','कैलाली':'Kailali',
  banke:'Banke','बाँके':'Banke',surkhet:'Surkhet','सुर्खेत':'Surkhet',
  dhanusha:'Dhanusha','धनुषा':'Dhanusha',parsa:'Parsa','पर्सा':'Parsa',
  makwanpur:'Makwanpur','मकवानपुर':'Makwanpur',ilam:'Ilam','इलाम':'Ilam'
};
const FIXED_PLACES={
  kathmandu:{name:'Kathmandu',lat:27.7172,lon:85.3240},
  jhapa:{name:'Jhapa',lat:26.5455,lon:87.8942},
  chitwan:{name:'Chitwan',lat:27.5291,lon:84.3542},
  pokhara:{name:'Pokhara',lat:28.2096,lon:83.9856},
  lalitpur:{name:'Lalitpur',lat:27.6588,lon:85.3247},
  bhaktapur:{name:'Bhaktapur',lat:27.6710,lon:85.4298},
  biratnagar:{name:'Biratnagar',lat:26.4525,lon:87.2718},
  birgunj:{name:'Birgunj',lat:27.0104,lon:84.8774},
  janakpur:{name:'Janakpur',lat:26.7271,lon:85.9407},
  hetauda:{name:'Hetauda',lat:27.4284,lon:85.0322},
  butwal:{name:'Butwal',lat:27.7006,lon:83.4484},
  nepalgunj:{name:'Nepalgunj',lat:28.0500,lon:81.6167},
  dhangadhi:{name:'Dhangadhi',lat:28.7041,lon:80.5819},
  dharan:{name:'Dharan',lat:26.8125,lon:87.2836},
  itahari:{name:'Itahari',lat:26.6631,lon:87.2749},
  damak:{name:'Damak',lat:26.6637,lon:87.7006}
};

function stationRows(){
  const out=[];const s=window.FloodSafe?.state||{};
  const push=v=>{if(Array.isArray(v))for(const x of v)if(x&&typeof x==='object')out.push(x)};
  for(const v of [s.currentRiverStations,s.latestRiverStations,s.allRiverStations,s.stations,s.rivers])push(v);
  const latest=window.__BIPAD_LATEST__;
  if(latest&&typeof latest==='object')for(const k of ['riverRows','rivers','stations','data','results'])push(latest[k]);
  for(const v of [window.__OFFICIAL_RIVER_ROWS__,window.__FLOODSAFE_RIVER_ROWS__,window.__TRUSTED_RIVER_ROWS__])push(v);
  const seen=new Set();return out.filter(r=>{const key=[stationId(r),norm(stationName(r)),measured(r),level(r)].join('|');if(seen.has(key))return false;seen.add(key);return true});
}
const stationName=o=>firstText(o,['river_name','riverName','station_name','stationName','name','title','station','river'])||'नदी स्टेशन';
const stationId=o=>firstText(o,['stationSeriesId','station_series_id','stationId','station_id','stationIndex','station_index','id']);
const district=o=>firstText(o,['district','district_name','districtName','district_title','admin2','county','state_district']);
const placeText=o=>[firstText(o,['municipality','municipality_name','municipalityName','localLevel','local_level','palika']),district(o),firstText(o,['province','province_name','provinceName'])].filter(Boolean).join(', ');
const level=o=>firstNum(o,['_lastWaterLevel','_level','waterLevel','water_level','currentWaterLevel','current_level']);
const warning=o=>firstNum(o,['_lastWarningLevel','_warning','warningLevel','warning_level','warningThreshold','warning_threshold']);
const danger=o=>firstNum(o,['_lastDangerLevel','_danger','dangerLevel','danger_level','dangerThreshold','danger_threshold']);
const measured=o=>firstText(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','timestamp','updatedAt']);
function measuredMs(o){const raw=measured(o);if(!raw)return 0;const n=Number(raw);if(Number.isFinite(n)&&String(raw).trim()!==''){const d=new Date(n<1e12?n*1000:n);return Number.isNaN(d.getTime())?0:d.getTime()}const d=new Date(raw);return Number.isNaN(d.getTime())?0:d.getTime()}
function fresh(o){const ms=measuredMs(o);return !!ms&&Date.now()-ms<=20*60*1000}
function stage(o){
  try{const s=norm(window.FloodSafeRiverRealtime?.stage?.(o));if(['danger','warning','watch','normal','unknown'].includes(s))return fresh(o)||!['danger','warning'].includes(s)?s:'unknown'}catch{}
  const l=level(o),w=warning(o),d=danger(o),raw=norm(firstText(o,['_derivedStatus','_officialStatus','status','status_name','alertStatus','riskLevel']));
  if(!fresh(o)&&(has(raw,'danger','warning','red','orange','खतरा','चेतावनी')||(l!==null&&((d!==null&&l>=d)||(w!==null&&l>=w)))))return'unknown';
  if((l!==null&&d!==null&&d>0&&l>=d)||has(raw,'danger','red','खतरा'))return'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||has(raw,'warning','orange','चेतावनी'))return'warning';
  if(has(raw,'watch','yellow','rising','सतर्क','निगरानी'))return'watch';
  return l!==null?'normal':'unknown';
}
const stageLabel=s=>s==='danger'?'🔴 खतरा':s==='warning'?'🟠 चेतावनी':s==='watch'?'🟡 निगरानी':s==='normal'?'🔵 सामान्य':'⚪ अज्ञात/पुरानो';
function coords(o){const lat=firstNum(o,['latitude','lat','stationLatitude','station_latitude']),lon=firstNum(o,['longitude','lon','lng','stationLongitude','station_longitude']);return lat!==null&&lon!==null?{lat,lon}:null}
function distanceKm(a,b){const R=6371,rad=x=>x*Math.PI/180,dLat=rad(b.lat-a.lat),dLon=rad(b.lon-a.lon),x=Math.sin(dLat/2)**2+Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(dLon/2)**2;return 2*R*Math.asin(Math.sqrt(x))}

function currentPoint(){
  const candidates=[];
  try{candidates.push(window.FloodSafeRain?.state?.point)}catch{}
  try{candidates.push(window.FloodSafe?.state?.monitorPoint,window.FloodSafe?.state?.selectedPoint,window.FloodSafe?.state?.location)}catch{}
  for(const p of candidates){const lat=num(p?.lat??p?.latitude),lon=num(p?.lon??p?.lng??p?.longitude);if(lat!==null&&lon!==null)return{lat,lon,name:esc(p?.name||p?.label||$('#place')?.textContent||'हालको GPS स्थान')}}
  try{const p=JSON.parse(localStorage.getItem('fs-last-device-location-v1')||'null');const lat=num(p?.lat),lon=num(p?.lon);if(lat!==null&&lon!==null)return{lat,lon,name:esc(p?.label||'पछिल्लो GPS स्थान')}}catch{}
  try{const p=JSON.parse(localStorage.getItem('fs-v25-location')||'null');if(Array.isArray(p)&&p.length===2){const lat=num(p[0]),lon=num(p[1]);if(lat!==null&&lon!==null)return{lat,lon,name:esc($('#place')?.textContent||'हालको स्थान')}}}catch{}
  return null;
}
const inNepal=p=>!!p&&p.lat>=26&&p.lat<=31.8&&p.lon>=79.5&&p.lon<=89;

function findDistrict(q){
  const nq=norm(q);
  for(const [a,d] of Object.entries(DISTRICT_ALIASES))if(nq.includes(norm(a)))return d;
  for(const d of DISTRICTS)if(nq.includes(norm(d)))return d;
  const seen=[...new Set(stationRows().map(district).filter(Boolean))];
  for(const d of seen)if(nq.includes(norm(d)))return d;
  return'';
}
function rowsForDistrict(name){
  const nd=norm(name);return stationRows().filter(r=>norm(district(r))===nd||norm(placeText(r)).includes(nd));
}
function districtRiverAnswer(q){
  const d=findDistrict(q);if(!d)return null;
  const rows=rowsForDistrict(d);if(!rows.length)return `🌊 ${d} जिल्लाका official BIPAD/DHM नदी स्टेशन अहिले app data मा लोड भएका छैनन्। Data आएपछि यहीँ सही list देखाउँछु; अर्को जिल्लाको नदी जोडेर उत्तर दिन्नँ।`;
  const best=new Map();for(const r of rows){const n=stationName(r),k=norm(n);const old=best.get(k);if(!old||measuredMs(r)>measuredMs(old))best.set(k,r)}
  const list=[...best.values()].sort((a,b)=>{const rank={danger:0,warning:1,watch:2,normal:3,unknown:4};return rank[stage(a)]-rank[stage(b)]||stationName(a).localeCompare(stationName(b))});
  const lines=list.slice(0,15).map(r=>{const l=level(r),s=stage(r);return `• ${stationName(r)} — ${stageLabel(s)}${l!==null?` • ${l.toFixed(2)} मि.`:''}`});
  return `🌊 ${d} जिल्लामा app ले अहिले ${list.length} official नदी/स्टेशन देखिरहेको छ:\n${lines.join('\n')}${list.length>15?`\n… थप ${list.length-15} स्टेशन app को ७७ जिल्ला सूचीमा छन्।`:''}`;
}
function nationalRiverAnswer(q){
  const rows=stationRows();if(!rows.length)return'Official नदी data अहिले लोड हुँदैछ। केही सेकेन्डपछि फेरि सोध्नुहोस्।';
  const unique=[];const seen=new Set();for(const r of rows){const k=stationId(r)||`${norm(stationName(r))}|${norm(district(r))}`;if(seen.has(k))continue;seen.add(k);unique.push(r)}
  const nq=norm(q);let wanted='all';if(has(nq,'danger','खतरा','red'))wanted='danger';else if(has(nq,'warning','चेतावनी','orange'))wanted='warning';else if(has(nq,'watch','सतर्क','yellow','निगरानी'))wanted='watch';else if(has(nq,'normal','सामान्य','blue'))wanted='normal';
  const filtered=wanted==='all'?unique:unique.filter(r=>stage(r)===wanted);
  if(!filtered.length)return wanted==='all'?`App मा ${unique.length} official नदी स्टेशन data लोड छ।`:`अहिले fresh verified ${wanted} status भएको नदी स्टेशन भेटिएन।`;
  const lines=filtered.slice(0,12).map(r=>`• ${stationName(r)}${district(r)?` (${district(r)})`:''} — ${stageLabel(stage(r))}${level(r)!==null?` • ${level(r).toFixed(2)} मि.`:''}`);
  return `🌊 ${wanted==='all'?'Official नदी स्टेशन':stageLabel(wanted)}: ${filtered.length}\n${lines.join('\n')}${filtered.length>12?`\n… थप ${filtered.length-12} app को सूचीमा छन्।`:''}`;
}
function nearbyAnswer(){
  const p=currentPoint();if(!p)return'📍 हालको/पछिल्लो GPS स्थान उपलब्ध छैन। Location अनुमति दिएपछि नजिकका official नदी स्टेशन मिलाएर देखाउँछु।';
  if(!inNepal(p))return`📍 ${p.name||'तपाईंको GPS'} नेपाल बाहिर छ। FloodSafe को २ किमि नदी warning/danger proximity alert नेपालभित्रको verified GPS मा मात्र लागू हुन्छ।`;
  const rows=stationRows().map(r=>({r,c:coords(r)})).filter(x=>x.c).map(x=>({...x,km:distanceKm(p,x.c)})).sort((a,b)=>a.km-b.km);
  if(!rows.length)return'नजिकका station coordinate data अहिले लोड भएको छैन।';
  const lines=rows.slice(0,5).map(x=>`• ${stationName(x.r)} — ${x.km.toFixed(1)} km • ${stageLabel(stage(x.r))}`);
  const risky=rows.filter(x=>x.km<=2&&['warning','danger'].includes(stage(x.r)));
  return `📍 नजिकका official नदी स्टेशन:\n${lines.join('\n')}\n${risky.length?`⚠️ २ km भित्र fresh verified Warning/Danger: ${risky.length}`:'✅ २ km भित्र fresh verified Warning/Danger भेटिएन।'}`;
}

function newsAnswer(){
  const items=[...document.querySelectorAll('#liveNews .newsItem')];
  if(!items.length)return'📰 नेपालका पछिल्ला समाचार अहिले app मा लोड हुँदैछन्।';
  const lines=items.slice(0,5).map((x,i)=>`${i+1}. ${esc(x.querySelector('h4')?.textContent||x.textContent).slice(0,220)}`);
  return `📰 App मा अहिले देखिएका पछिल्ला समाचार:\n${lines.join('\n')}`;
}
function humanAnswer(){
  const sec=$('#humanStatus');
  if(!sec||sec.hidden||getComputedStyle(sec).display==='none')return'🧑‍🤝‍🧑 अहिले app news feed ले नयाँ विपद् signal detect गरेको छैन, त्यसैले Human Status लुकाइएको छ। नयाँ disaster आएपछि official BIPAD loss data सहित १० दिन देखिन्छ।';
  const d=esc($('#humanDeaths')?.textContent||'—'),i=esc($('#humanInjured')?.textContent||'—'),m=esc($('#humanMissing')?.textContent||'—'),r=esc($('#humanRescued')?.textContent||'—');
  return `🧑‍🤝‍🧑 पछिल्लो विपद् Human Status: मृतक ${d}, घाइते ${i}, बेपत्ता ${m}, उद्धार ${r}। संख्या app मा आएको official BIPAD loss data अनुसार हो।`;
}
function weatherCardAnswer(){
  const place=esc($('#place')?.textContent||'निगरानी स्थान'),temp=esc($('#temp')?.textContent||'—'),txt=esc($('#weatherText')?.textContent||''),rain=esc($('#rain')?.textContent||'—'),hum=esc($('#humidity')?.textContent||'—'),wind=esc($('#wind')?.textContent||'—'),timing=esc($('#rainTiming')?.textContent||'');
  return `🌦️ ${place}: ${temp}${txt?` • ${txt}`:''}। वर्षा ${rain}, आर्द्रता ${hum}, हावा ${wind}.${timing?` ${timing}`:''}`;
}
function mapStatsAnswer(){
  const total=esc($('#stationCount')?.textContent||''),warning=esc($('#warningCount')?.textContent||''),danger=esc($('#dangerCount')?.textContent||''),risk=esc($('#riskValue')?.textContent||''),freshText=esc($('#feedFresh')?.textContent||'');
  return `🗺️ FloodSafe map status: official स्टेशन ${total||stationRows().length||'—'}, चेतावनी ${warning||'—'}, खतरा ${danger||'—'}${risk?`, निगरानी क्षेत्र risk ${risk}`:''}.${freshText?` ${freshText}`:''}`;
}
function alertAnswer(){
  let on=false;try{on=localStorage.getItem('fs-nepal-alerts-on')==='1'}catch{}
  return `🔔 Flood alerts ${on?'ON':'permission/status अनुसार चल्ने'} छन्। Button चाहिँ राखिएको छैन। Android notification/location अनुमति भएपछि app ले background मा monitor गर्छ र नेपालभित्र तपाईंको verified GPS बाट २ km भित्रको fresh verified Warning/Danger मात्र नदी alert का लागि मिलाउँछ।`;
}
function appInfoAnswer(){return'🤖 SATHI ले FloodSafe app भित्रको मौसम/भोलिको forecast, वर्षा समय, GPS/location, नजिकका नदी, ७७ जिल्लाका official नदी स्टेशन, water level/status, Danger/Warning सूची, map counts, news, Human Status, alerts, privacy र app feature सम्बन्धी प्रश्नको उत्तर दिन्छ। Named नदीको reading नभए अर्को नदीको data जोडेर गलत उत्तर दिँदैन।';}
function privacyAnswer(){return'🔒 FloodSafe ले location लाई स्थानीय मौसम र नजिकको flood risk मिलाउन, microphone लाई SATHI voice input/wake feature का लागि, र notification लाई safety alerts का लागि प्रयोग गर्छ। App भित्रको “गोपनीयता नीति” card बाट पूरा policy खोल्न सकिन्छ।';}
function locationAnswer(){const p=currentPoint();return p?`📍 App को हाल/पछिल्लो location: ${p.name||''} (${p.lat.toFixed(4)}, ${p.lon.toFixed(4)})${inNepal(p)?' — नेपालभित्र।':' — नेपाल बाहिर।'}`:'📍 App मा verified GPS location अहिले उपलब्ध छैन।';}

function weatherIntent(q){return has(q,'weather','mausam','mousam','मौसम','temperature','temp','तापक्रम','तापमान','rain','वर्षा','पानी','forecast','पूर्वानुमान');}
function selfWeather(q){return has(q,'mero','my location','near me','here','yaha','yahaa','यहाँ','हालको gps','current gps')&&!findDistrict(q);}
function cleanPlace(raw){
  let s=norm(raw);
  const remove=['tomorrow','today','bholi','voli','भोलि','भोली','आज','aaja','aaj','weather','mausam','mousam','मौसम','temperature','temp','तापक्रम','तापमान','forecast','पूर्वानुमान','rain','वर्षा','पानी','chance','kati','kasto','cha','xa','chha','please','sathi','malai','bhana','tell','me'];
  for(const x of remove)s=s.replace(new RegExp(`(^|\\s)${x.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?=\\s|$)`,'g'),' ');
  s=s.replace(/\b(ko|ma|maa|in|at|of)\b/g,' ').replace(/\s+/g,' ').trim();
  return s;
}
async function geocodeNepal(name){
  const key=norm(name);if(FIXED_PLACES[key])return FIXED_PLACES[key];
  const d=findDistrict(name);if(d&&FIXED_PLACES[norm(d)])return FIXED_PLACES[norm(d)];
  const rs=rowsForDistrict(d||name).map(coords).filter(Boolean);if(rs.length){const lat=rs.reduce((a,b)=>a+b.lat,0)/rs.length,lon=rs.reduce((a,b)=>a+b.lon,0)/rs.length;return{name:d||name,lat,lon}}
  const ctl=new AbortController();const id=setTimeout(()=>ctl.abort(),9000);
  try{const u='https://geocoding-api.open-meteo.com/v1/search?name='+encodeURIComponent(name)+'&count=10&language=en&format=json';const r=await fetch(u,{cache:'no-store',signal:ctl.signal});if(!r.ok)throw new Error('geocode');const j=await r.json();const all=Array.isArray(j?.results)?j.results:[];const p=all.find(x=>String(x.country_code||'').toUpperCase()==='NP'||/nepal/i.test(String(x.country||'')));return p?{name:p.name||name,lat:Number(p.latitude),lon:Number(p.longitude)}:null}finally{clearTimeout(id)}
}
async function forecast(p){
  const ctl=new AbortController();const id=setTimeout(()=>ctl.abort(),10000);
  try{const u=new URL('https://api.open-meteo.com/v1/forecast');u.search=new URLSearchParams({latitude:String(p.lat),longitude:String(p.lon),timezone:'Asia/Kathmandu',forecast_days:'3',current:'temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,precipitation',daily:'temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max'}).toString();const r=await fetch(u,{cache:'no-store',signal:ctl.signal});if(!r.ok)throw new Error('forecast');return r.json()}finally{clearTimeout(id)}
}
function weatherTextFor(p,j,q){
  const tomorrow=has(q,'tomorrow','bholi','voli','भोलि','भोली');
  if(tomorrow){const d=j?.daily||{},i=Math.min(1,(d.time||[]).length-1),lo=num(d.temperature_2m_min?.[i]),hi=num(d.temperature_2m_max?.[i]),fl=num(d.apparent_temperature_min?.[i]),fh=num(d.apparent_temperature_max?.[i]),chance=num(d.precipitation_probability_max?.[i]),sum=num(d.precipitation_sum?.[i]),wind=num(d.wind_speed_10m_max?.[i]);return `🌡️ ${p.name}मा भोलि तापक्रम करिब ${lo!==null?lo.toFixed(1):'—'}°C देखि ${hi!==null?hi.toFixed(1):'—'}°C रहने forecast छ। महसुस हुने तापक्रम ${fl!==null?fl.toFixed(1):'—'}°C–${fh!==null?fh.toFixed(1):'—'}°C, वर्षा सम्भावना अधिकतम ${chance!==null?Math.round(chance):'—'}%, अनुमानित वर्षा ${sum!==null?sum.toFixed(1):'—'} mm र हावा अधिकतम ${wind!==null?wind.toFixed(1):'—'} km/h हुन सक्छ। स्रोत: Open-Meteo ताजा forecast।`}
  const c=j?.current||{},t=num(c.temperature_2m),feel=num(c.apparent_temperature),hum=num(c.relative_humidity_2m),wind=num(c.wind_speed_10m),rain=num(c.precipitation);return `🌦️ ${p.name}मा अहिले तापक्रम ${t!==null?t.toFixed(1):'—'}°C, महसुस ${feel!==null?feel.toFixed(1):'—'}°C, आर्द्रता ${hum!==null?Math.round(hum):'—'}%, हावा ${wind!==null?wind.toFixed(1):'—'} km/h र हालको वर्षा ${rain!==null?rain.toFixed(1):'—'} mm छ। स्रोत: Open-Meteo।`;
}
async function namedWeatherAnswer(raw){
  const q=norm(raw);let p=null;
  if(selfWeather(q)){p=currentPoint();if(!p)return'📍 मौसम बताउन app मा GPS/location उपलब्ध छैन।'}
  else{const place=cleanPlace(raw);if(!place)return weatherCardAnswer();p=await geocodeNepal(place);if(!p)return`🌦️ “${place}” लाई नेपालभित्र सही location सँग match गर्न सकिनँ। जिल्ला/सहरको नाम अलि स्पष्ट लेख्नुहोस्।`}
  try{return weatherTextFor(p,await forecast(p),q)}catch{return`🌦️ ${p.name||'यो स्थान'} को live weather service अहिले response दिन सकेन। App मा cached/गलत data बनाएर उत्तर दिन्नँ।`}
}

function canHandle(raw){
  const q=norm(raw);if(!q)return false;
  if(weatherIntent(q))return true;
  if(has(q,'river list','nadi list','khola list','नदी सूची','खोला सूची','river station list','station list')&&findDistrict(q))return true;
  if((has(q,'danger','warning','watch','normal','खतरा','चेतावनी','सतर्क','सामान्य')&&has(q,'river','nadi','khola','नदी','खोला'))||has(q,'all river','सबै नदी','सबै खोला'))return true;
  if(has(q,'near me','mero najik','मेरो नजिक','nearby river','नजिकको नदी','gps risk'))return true;
  if(has(q,'news','samachar','समाचार'))return true;
  if(has(q,'human status','मृतक','घाइते','बेपत्ता','उद्धार'))return true;
  if(has(q,'map','नक्सा','station count','कति station','कति स्टेशन'))return true;
  if(has(q,'alert','notification','चेतावनी')&&!has(q,'river','nadi','khola','नदी','खोला'))return true;
  if(has(q,'privacy','गोपनीयता','data use','permission'))return true;
  if(has(q,'my location','mero location','मेरो स्थान','हालको gps','current gps'))return true;
  if(has(q,'what can you do','k k garna','k k cha','app ma k','feature','साथी के गर्छ','sathi ke'))return true;
  return false;
}
async function answer(raw){
  const q=norm(raw);
  if(weatherIntent(q))return namedWeatherAnswer(raw);
  if(has(q,'river list','nadi list','khola list','नदी सूची','खोला सूची','river station list','station list')&&findDistrict(q))return districtRiverAnswer(q);
  if((has(q,'danger','warning','watch','normal','खतरा','चेतावनी','सतर्क','सामान्य')&&has(q,'river','nadi','khola','नदी','खोला'))||has(q,'all river','सबै नदी','सबै खोला'))return nationalRiverAnswer(q);
  if(has(q,'near me','mero najik','मेरो नजिक','nearby river','नजिकको नदी','gps risk'))return nearbyAnswer();
  if(has(q,'news','samachar','समाचार'))return newsAnswer();
  if(has(q,'human status','मृतक','घाइते','बेपत्ता','उद्धार'))return humanAnswer();
  if(has(q,'map','नक्सा','station count','कति station','कति स्टेशन'))return mapStatsAnswer();
  if(has(q,'alert','notification','चेतावनी'))return alertAnswer();
  if(has(q,'privacy','गोपनीयता','data use','permission'))return privacyAnswer();
  if(has(q,'my location','mero location','मेरो स्थान','हालको gps','current gps'))return locationAnswer();
  return appInfoAnswer();
}

function openPanel(){$('#sathiFloodOverlay')?.classList.add('open');const p=$('#sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false')}}
function add(text,type='ai'){const box=$('#sathiFloodMsgs');if(!box)return null;const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');box.appendChild(d);box.scrollTop=box.scrollHeight;return d}
async function handle(raw,{voice=false}={}){
  const text=String(raw||'').trim();if(!text||!canHandle(text))return false;
  openPanel();const input=$('#sathiInput');if(input){input.value='';input.style.height='auto'}add(text,'user');const bubble=add('🧠 App को ताजा data हेर्दैछु…','status');
  let out='';try{out=await answer(text)}catch{out='यो प्रश्नको app data अहिले पढ्न सकिनँ। केही सेकेन्डपछि फेरि सोध्नुहोस्।'}
  if(bubble){bubble.className='sathiMsg ai';bubble.textContent=String(out||'उत्तर उपलब्ध छैन।')}
  if(voice&&window.SathiNative){try{window.SathiNative.speak(String(out||''))}catch{}}
  try{window.dispatchEvent(new CustomEvent('sathi-app-aware-answer',{detail:{question:text,answer:String(out||'')}}))}catch{}
  return true;
}

document.addEventListener('click',e=>{
  const send=e.target?.closest?.('#sathiSend'),quick=e.target?.closest?.('#sathiQuick button[data-q]');if(!send&&!quick)return;
  const input=$('#sathiInput'),text=quick?String(quick.getAttribute('data-q')||quick.textContent||''):String(input?.value||'');if(!canHandle(text))return;
  e.preventDefault();e.stopImmediatePropagation();handle(text);
},true);

document.addEventListener('keydown',e=>{if(e.key!=='Enter'||e.shiftKey||!e.target?.matches?.('#sathiInput'))return;const text=String(e.target.value||'');if(!canHandle(text))return;e.preventDefault();e.stopImmediatePropagation();handle(text)},true);
window.addEventListener('sathi-native-transcript',e=>{const text=String(e?.detail?.text||'').trim();if(!canHandle(text))return;e.stopImmediatePropagation();handle(text,{voice:true})},true);

window.SathiAppAwareV1={answer,canHandle,stationRows,districtRiverAnswer,nationalRiverAnswer,nearbyAnswer,newsAnswer,humanAnswer};
})();
