(()=>{
'use strict';
if(window.__SATHI_PLACE_WEATHER_V1__) return;
window.__SATHI_PLACE_WEATHER_V1__=true;

const NEPAL_TZ='Asia/Kathmandu';
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[?!.:,;()\[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const has=(q,...xs)=>xs.some(x=>q.includes(x));
const $=s=>document.querySelector(s);

const FIXED_PLACES=[
  {keys:['chitwan','चितवन','bharatpur','भरतपुर'],name:'चितवन',en:'Chitwan',lat:27.5291,lon:84.3542},
  {keys:['kathmandu','ktm','काठमाडौं','काठमाण्डौ'],name:'काठमाडौं',en:'Kathmandu',lat:27.7172,lon:85.3240},
  {keys:['lalitpur','patan','ललितपुर','पाटन'],name:'ललितपुर',en:'Lalitpur',lat:27.6588,lon:85.3247},
  {keys:['bhaktapur','भक्तपुर'],name:'भक्तपुर',en:'Bhaktapur',lat:27.6710,lon:85.4298},
  {keys:['pokhara','पोखरा'],name:'पोखरा',en:'Pokhara',lat:28.2096,lon:83.9856},
  {keys:['biratnagar','विराटनगर'],name:'विराटनगर',en:'Biratnagar',lat:26.4525,lon:87.2718},
  {keys:['birgunj','birganj','वीरगञ्ज','वीरगंज'],name:'वीरगञ्ज',en:'Birgunj',lat:27.0104,lon:84.8774},
  {keys:['janakpur','janakpurdham','जनकपुर','जनकपुरधाम'],name:'जनकपुर',en:'Janakpur',lat:26.7271,lon:85.9407},
  {keys:['hetauda','हेटौंडा','हेटौँडा'],name:'हेटौंडा',en:'Hetauda',lat:27.4284,lon:85.0322},
  {keys:['butwal','बुटवल'],name:'बुटवल',en:'Butwal',lat:27.7006,lon:83.4484},
  {keys:['nepalgunj','nepalganj','नेपालगञ्ज','नेपालगंज'],name:'नेपालगञ्ज',en:'Nepalgunj',lat:28.0500,lon:81.6167},
  {keys:['dhangadhi','धनगढी'],name:'धनगढी',en:'Dhangadhi',lat:28.7041,lon:80.5819},
  {keys:['dharan','धरान'],name:'धरान',en:'Dharan',lat:26.8125,lon:87.2836},
  {keys:['itahari','इटहरी'],name:'इटहरी',en:'Itahari',lat:26.6631,lon:87.2749},
  {keys:['damak','दमक'],name:'दमक',en:'Damak',lat:26.6637,lon:87.7006}
];

function weatherIntent(raw){
  const q=norm(raw);
  const temperature=has(q,'temperature','temp','taapman','tapman','तापक्रम','तापमान');
  const weather=has(q,'weather','mausam','mousam','मौसम');
  const explicitRain=has(q,'वर्षा','rain','barsa','barsha');
  const rainTiming=(has(q,'पानी','pani')&&has(q,'कहिले','kahile','kati baje','कति बजे','parcha','parxa','पर्छ','rok','रोकिन','start','stop'));
  return temperature?'temperature':(explicitRain||rainTiming)?'rain':weather?'weather':'';
}
function selfLocation(q){
  return has(q,'mero area','mero location','my location','near me','yaha','yahaa','eta','here','मेरो स्थान','मेरो ठाउँ','मेरो क्षेत्र','यहाँ','यता','हालको gps','current gps');
}
function fixedPlace(q){
  for(const p of FIXED_PLACES){
    if(p.keys.some(k=>q.includes(norm(k)))) return {...p,source:'fixed'};
  }
  return null;
}
function cleanCandidate(s){
  return String(s||'')
    .replace(/\b(hey|ye|sathi|ai|please|plz|malai|bhana|bhan|vana|van|tell|me)\b/gi,' ')
    .replace(/\b(aaj|aaja|aja|aahele|aile|ahile|now|today|currently)\b/gi,' ')
    .replace(/\b(kati|kasto|cha|xa|chha|ho|ra|ani|please)\b/gi,' ')
    .replace(/\s+/g,' ').trim();
}
function explicitPlaceText(raw){
  const q=norm(raw);
  if(selfLocation(q))return'';
  const fp=fixedPlace(q);if(fp)return fp.en;
  const patterns=[
    /^(.+?)\s+(?:ko|ma|maa)\s+(?:temperature|temp|weather|mausam|mousam|rain|barsa|barsha|pani)\b/i,
    /^(?:temperature|temp|weather|mausam|mousam|rain)\s+(?:in|at|of)\s+(.+?)(?:\s+(?:kati|kasto|cha|xa|chha|now|today|aahele|aile|ahile)\b|$)/i,
    /^(.+?)\s+(?:ma|maa)\s+pani\s+(?:kahile|kati|parcha|parxa|rok)/i,
    /^(.+?)(?:को|मा)\s*(?:तापक्रम|तापमान|मौसम|वर्षा|पानी)/,
    /^(?:तापक्रम|तापमान|मौसम|वर्षा)\s*(?:कति|कस्तो)?\s*(?:छ)?\s*(?:भन्नुहोस्)?\s*(.+)$/
  ];
  for(const re of patterns){
    const m=String(raw||'').trim().match(re);
    if(m?.[1]){
      const c=cleanCandidate(m[1]);
      if(c.length>=2&&!selfLocation(norm(c)))return c;
    }
  }
  return'';
}
function shouldHandle(raw){
  const kind=weatherIntent(raw);if(!kind)return null;
  const q=norm(raw);if(selfLocation(q))return null;
  const fixed=fixedPlace(q);
  const text=fixed?fixed.en:explicitPlaceText(raw);
  return text?{kind,text,fixed}:null;
}

async function geocodeNepal(name){
  const fixed=FIXED_PLACES.find(p=>p.keys.some(k=>norm(name).includes(norm(k)))||norm(name)===norm(p.en));
  if(fixed)return {...fixed,source:'fixed'};
  const u='https://geocoding-api.open-meteo.com/v1/search?name='+encodeURIComponent(name)+'&count=10&language=en&format=json';
  const r=await fetch(u,{cache:'no-store'});if(!r.ok)throw new Error('geocode '+r.status);
  const j=await r.json();
  const rs=Array.isArray(j?.results)?j.results:[];
  const np=rs.find(x=>String(x.country_code||'').toUpperCase()==='NP'||/nepal/i.test(String(x.country||'')));
  if(!np)return null;
  return {name:np.name_ne||np.name||name,en:np.name||name,lat:Number(np.latitude),lon:Number(np.longitude),district:np.admin2||np.admin1||'',source:'geocoder'};
}
async function forecast(p){
  const params=new URLSearchParams({
    latitude:String(p.lat),longitude:String(p.lon),timezone:NEPAL_TZ,forecast_days:'2',
    current:'temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,precipitation',
    hourly:'precipitation_probability,precipitation,temperature_2m'
  });
  const r=await fetch('https://api.open-meteo.com/v1/forecast?'+params.toString(),{cache:'no-store'});
  if(!r.ok)throw new Error('forecast '+r.status);
  return r.json();
}
function neNum(v,d=1){
  const n=Number(v);if(!Number.isFinite(n))return'—';
  try{return new Intl.NumberFormat('ne-NP',{maximumFractionDigits:d,minimumFractionDigits:d}).format(n)}catch{return n.toFixed(d)}
}
function neTime(localIso){
  const m=String(localIso||'').match(/T(\d{2}):(\d{2})/);if(!m)return String(localIso||'');
  let h=Number(m[1]),min=Number(m[2]);const ap=h>=12?'अपराह्न':'पूर्वाह्न';h=h%12||12;
  const digits=x=>String(x).replace(/\d/g,d=>'०१२३४५६७८९'[Number(d)]);
  return `${digits(h)}:${digits(String(min).padStart(2,'0'))} ${ap}`;
}
function nepalHourKey(){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:NEPAL_TZ,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23'}).formatToParts(new Date());
  const o={};for(const x of parts)o[x.type]=x.value;
  return `${o.year}-${o.month}-${o.day}T${o.hour}:00`;
}
function hourlyIndex(j){
  const times=j?.hourly?.time||[];const key=nepalHourKey();
  let i=times.findIndex(t=>String(t)>=key);if(i<0)i=0;return i;
}
function rainWindow(j){
  const h=j?.hourly||{},times=h.time||[],pp=h.precipitation_probability||[],pr=h.precipitation||[];
  const i0=hourlyIndex(j),limit=Math.min(times.length,i0+30);
  const wet=i=>(Number(pr[i])>=0.1)||(Number(pp[i])>=40);
  const nowWet=Number(j?.current?.precipitation)>=0.1||wet(i0);
  let start=nowWet?i0:-1;
  if(start<0)for(let i=i0;i<limit;i++){if(wet(i)){start=i;break}}
  let stop=-1;if(start>=0)for(let i=start+1;i<limit;i++){if(!wet(i)){stop=i;break}}
  let maxP=0,total=0;for(let i=i0;i<limit;i++){maxP=Math.max(maxP,Number(pp[i])||0);total+=Number(pr[i])||0}
  return {nowWet,start:start>=0?times[start]:null,stop:stop>=0?times[stop]:null,maxP,total};
}
function label(p){return p.district&&norm(p.district)!==norm(p.en)?`${p.name||p.en} (${p.district})`:(p.name||p.en)}
function temperatureReply(p,j){
  const c=j?.current||{},i=hourlyIndex(j),chance=Number(j?.hourly?.precipitation_probability?.[i]);
  const bits=[`🌡️ ${label(p)}मा अहिले करिब ${neNum(c.temperature_2m)}°C छ।`];
  if(Number.isFinite(Number(c.apparent_temperature)))bits.push(`महसुस हुने तापक्रम ${neNum(c.apparent_temperature)}°C।`);
  if(Number.isFinite(Number(c.relative_humidity_2m)))bits.push(`आर्द्रता ${neNum(c.relative_humidity_2m,0)}%।`);
  if(Number.isFinite(Number(c.wind_speed_10m)))bits.push(`हावा ${neNum(c.wind_speed_10m)} km/h।`);
  if(Number.isFinite(chance))bits.push(`नजिकको घण्टामा वर्षा सम्भावना करिब ${neNum(chance,0)}%।`);
  bits.push('स्रोत: Open-Meteo ताजा मौसम पूर्वानुमान।');
  return bits.join(' ');
}
function rainReply(p,j){
  const w=rainWindow(j),bits=[`🌧️ ${label(p)}को ताजा पूर्वानुमान अनुसार`];
  bits.push(w.nowWet?'अहिले वर्षा भइरहेको/देखिएको छ।':'अहिले वर्षा देखिएको छैन।');
  if(w.start){
    if(!w.nowWet)bits.push(`वर्षा सुरु हुने सम्भावित समय ${neTime(w.start)} हो।`);
    if(w.stop)bits.push(`वर्षा रोकिने सम्भावित समय ${neTime(w.stop)} हो।`);else bits.push('रोकिने स्पष्ट समय अहिलेको ३० घण्टे window मा भेटिएन।');
  }else bits.push('अर्को करिब ३० घण्टामा वर्षा सुरु हुने स्पष्ट signal भेटिएन।');
  bits.push(`उच्चतम वर्षा सम्भावना करिब ${neNum(w.maxP,0)}%।`);
  bits.push('यो पूर्वानुमान हो, समय केही अगाडि/पछि सर्न सक्छ। स्रोत: Open-Meteo।');
  return bits.join(' ');
}
function weatherReply(p,j){
  const c=j?.current||{},w=rainWindow(j);
  return `🌤️ ${label(p)}मा अहिले करिब ${neNum(c.temperature_2m)}°C छ, महसुस हुने ${neNum(c.apparent_temperature)}°C, आर्द्रता ${neNum(c.relative_humidity_2m,0)}% र हावा ${neNum(c.wind_speed_10m)} km/h छ। नजिकको समयमा वर्षा सम्भावना अधिकतम करिब ${neNum(w.maxP,0)}% छ। स्रोत: Open-Meteo ताजा मौसम पूर्वानुमान।`;
}
async function answerNamed(raw){
  const req=shouldHandle(raw);if(!req)return null;
  let p=req.fixed||await geocodeNepal(req.text);
  if(!p)return `📍 “${req.text}” नेपालभित्र स्पष्ट रूपमा भेटिएन। जिल्ला वा सहरको नाम अलि स्पष्ट लेख्नुहोस्। म यस्तो अवस्थामा GPS मा चुपचाप fallback गर्दिनँ।`;
  const j=await forecast(p);
  if(req.kind==='temperature')return temperatureReply(p,j);
  if(req.kind==='rain')return rainReply(p,j);
  return weatherReply(p,j);
}
function add(text,type='ai'){
  const msgs=$('#sathiFloodMsgs');if(!msgs)return;
  const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;
}
function openPanel(){
  $('#sathiFloodOverlay')?.classList.add('open');const p=$('#sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false')}
}
async function handleUiQuestion(text,{alreadyAdded=false,speak=false}={}){
  const req=shouldHandle(text);if(!req)return false;
  openPanel();if(!alreadyAdded)add(text,'user');
  const status=document.createElement('div');status.className='sathiMsg status';status.textContent=`📍 ${req.text}को मौसम खोज्दैछु…`;$('#sathiFloodMsgs')?.appendChild(status);
  try{
    const reply=await answerNamed(text);status.remove();add(reply,'ai');
    if(speak)try{window.SathiNative?.speak?.(reply)}catch{}
  }catch(e){
    status.remove();const msg=`🌦️ ${req.text}को ताजा मौसम अहिले ल्याउन सकिनँ। इन्टरनेट जाँचेर फेरि प्रयास गर्नुहोस्।`;add(msg,'ai');if(speak)try{window.SathiNative?.speak?.(msg)}catch{}
  }
  return true;
}

// Capture typed named-place weather questions before the original GPS-first handler.
document.addEventListener('click',e=>{
  const send=e.target?.closest?.('#sathiSend');
  const quick=e.target?.closest?.('#sathiQuick button[data-q]');
  if(!send&&!quick)return;
  const input=$('#sathiInput');const text=quick?String(quick.dataset.q||'').trim():String(input?.value||'').trim();
  if(!text||!shouldHandle(text))return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
  if(input){input.value='';input.style.height='auto'}
  handleUiQuestion(text);
},true);
document.addEventListener('keydown',e=>{
  if(e.key!=='Enter'||e.shiftKey||e.target?.id!=='sathiInput')return;
  const text=String(e.target.value||'').trim();if(!text||!shouldHandle(text))return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();e.target.value='';e.target.style.height='auto';handleUiQuestion(text);
},true);

// Native transcript events are dispatched on window. Capture phase runs before
// the existing generic handler, so named-place weather never falls back to GPS.
window.addEventListener('sathi-native-transcript',e=>{
  const text=String(e?.detail?.text||'').trim();if(!text||!shouldHandle(text))return;
  e.stopImmediatePropagation();
  const status=$('#sathiNativeStatus');if(status)status.textContent='✅ स्थानसहित प्रश्न बुझियो।';
  handleUiQuestion(text,{speak:true});
},true);

window.SathiPlaceWeather={answerNamed,extract:explicitPlaceText,shouldHandle,version:'1.0'};
})();