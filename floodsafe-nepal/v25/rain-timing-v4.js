import {forecastUrl,parseForecast,pointKey,range,clock} from './rain-forecast-v1.mjs';
import {setupRainAlerts} from './rain-push-v1.js';
const $=id=>document.getElementById(id),POLL=5*60000,TTL=10*60000;
let point=null,raw=null,forecast=null,fetchedAt=0,lastAttempt=0,controller=null,serial=0,timer=0,error='';
const lang=()=>window.FloodSafe?.state?.lang||'ne',tr=(ne,en)=>lang()==='en'?en:ne;
function pickPoint(){
  const gps=window.FloodSafeCurrentLocation?.last,s=window.FloodSafe?.state;
  // Never move current-location weather to a river merely because it was tapped.
  if(gps)return {...gps,kind:'gps'};
  if(typeof s?.lat==='number'&&typeof s?.lon==='number')return {lat:s.lat,lon:s.lon,kind:'monitor'};
  return null;
}
function render(){
  const el=$('rainTiming');if(!el)return;
  renderWeather();
  if($('rainForecastMeta'))$('rainForecastMeta').textContent='';
  if(!point){el.textContent=tr('वर्षा सुरु/रोकिने अनुमानका लागि “मेरो हालको स्थान” थिच्नुहोस् वा नेपालमा निगरानी क्षेत्र छान्नुहोस्।','Tap “My Current Location” or choose a Nepal monitoring point for rain timing.');return}
  const stale=forecast&&Date.now()-fetchedAt>TTL;
  if(!forecast){el.textContent=tr('वर्षाको ताजा पूर्वानुमान उपलब्ध छैन • स्वतः पुनः जाँच हुँदैछ','Fresh rain forecast unavailable • retrying automatically');return}
  if(stale) el.textContent=tr('पछिल्लो मौसम पूर्वानुमान देखाइँदैछ • नयाँ डेटा स्वतः पुनः जाँच हुँदैछ','Showing the last weather forecast • checking for a fresh update automatically');
  const f=forecast,zone=f.timeZone,parts=[];
  if(f.wetNow)parts.push(tr('🌧️ पूर्वानुमानमा अहिले वर्षा देखिएको छ','🌧️ Forecast indicates rain now'));
  else if(f.rainMm>=.05)parts.push(tr(`💧 हल्का वर्षाको सम्भावना मात्र (${f.rainMm.toFixed(1)} mm) • अहिले वर्षा पुष्टि भएको छैन`,`💧 Light rain possibility only (${f.rainMm.toFixed(1)} mm) • rain is not confirmed now`));
  else if(f.start){const m=Math.max(0,Math.ceil((f.start.from-Date.now())/60000));parts.push(tr(`🌧️ अनुमानित सुरु: ${range(f.start,zone,lang())} • करिब ${m} मिनेटपछि`,`🌧️ Expected start: ${range(f.start,zone,lang())} • in about ${m} min`))}
  else parts.push(f.unknown?tr('🌤️ अहिले वर्षा छैन • विस्तृत वर्षा-समय स्वतः अद्यावधिक हुँदैछ','🌤️ No rain right now • detailed rain timing is updating automatically'):tr(`${clock(f.coverageUntil,zone,lang())} सम्मको पूर्वानुमानमा वर्षा देखिएको छैन`,`No rain indicated in the forecast through ${clock(f.coverageUntil,zone,lang())}`));
  if(f.wetNow||f.start)parts.push(f.stop?tr(`🌤️ अनुमानित रोकिने: ${range(f.stop,zone,lang())}`,`🌤️ Expected end: ${range(f.stop,zone,lang())}`):tr('रोकिने समय उपलब्ध छैन','End time unavailable'));
  el.textContent=parts.join(' · ');
  const gpsFresh=window.FloodSafeCurrentLocation?.fresh;
  $('rainForecastMeta').textContent=tr(`${point.kind==='gps'?(gpsFresh?'हालको GPS':'पछिल्लो GPS'):'छानिएको निगरानी'} क्षेत्र • Open-Meteo पूर्वानुमान • ${zone} • जाँच ${clock(fetchedAt,zone,lang())}। यी अनुमान हुन्; ठ्याक्कै १५-मिनेटको स्थानीय मापन होइन।`,`${point.kind==='gps'?(gpsFresh?'Current GPS':'Last GPS'):'Selected monitoring'} area • Open-Meteo forecast • ${zone} • checked ${clock(fetchedAt,zone,lang())}. Estimates, not exact local 15-minute observations.`)+(error?tr(' पछिल्लो जाँच असफल भयो।',' Latest check failed.'):'');
}
function renderWeather(){
  if(!forecast){for(const id of ['temp','rain','humidity','wind'])if($(id))$(id).textContent='—';if($('weatherText'))$('weatherText').textContent=tr('ताजा मौसम पूर्वानुमान उपलब्ध छैन','Fresh weather forecast unavailable');return}const c=forecast.current;
  for(const [id,value] of Object.entries({temp:Number.isFinite(c.temperature_2m)?Math.round(c.temperature_2m)+'°':'—°',rain:forecast.rainMm.toFixed(1)+' mm',humidity:Number.isFinite(c.relative_humidity_2m)?Math.round(c.relative_humidity_2m)+'%':'—',wind:Number.isFinite(c.wind_speed_10m)?Math.round(c.wind_speed_10m)+' km/h':'—'}))if($(id))$(id).textContent=value;
  if($('weatherText'))$('weatherText').textContent=forecast.wetNow
    ?tr('पूर्वानुमान: वर्षा','Forecast: rain')
    :forecast.rainMm>=.05
      ?tr('पूर्वानुमान: हल्का वर्षाको सम्भावना','Forecast: slight rain possibility')
      :tr('पूर्वानुमान: अहिले वर्षा छैन','Forecast: no rain now');
}
function toMillis(value){
  if(typeof value==='number'&&Number.isFinite(value))return value>1e12?value:value*1000;
  const parsed=Date.parse(String(value));return Number.isFinite(parsed)?parsed:NaN;
}
function basicForecast(j){
  const c=j?.current||{},precip=Number(c.precipitation??c.rain??0);
  if(!Number.isFinite(Number(c.temperature_2m))) throw Error('Incomplete basic weather forecast');
  const hourly=j?.hourly||{},times=Array.isArray(hourly.time)?hourly.time:[],rain=Array.isArray(hourly.rain)?hourly.rain:[],showers=Array.isArray(hourly.showers)?hourly.showers:[],total=Array.isArray(hourly.precipitation)?hourly.precipitation:[];
  const now=Date.now(),wetNow=Number.isFinite(precip)&&precip>=.5;
  let start=null,stop=null,sawWet=wetNow,coverageUntil=now+60*60000;
  for(let i=0;i<times.length;i++){
    const end=toMillis(times[i]);if(!Number.isFinite(end)||end<=now)continue;
    coverageUntil=Math.max(coverageUntil,end);
    const values=[rain[i],showers[i],total[i]].map(Number).filter(Number.isFinite);if(!values.length)continue;
    const amount=Math.max(...values);
    if(amount>=.5){if(!sawWet){start={from:end-60*60000,to:end};sawWet=true}}
    else if(sawWet&&!stop){stop={from:end-60*60000,to:end};break}
  }
  return {
    current:{temperature_2m:Number(c.temperature_2m),relative_humidity_2m:Number(c.relative_humidity_2m),
      wind_speed_10m:Number(c.wind_speed_10m),rain:precip,showers:0,weather_code:Number(c.weather_code)},
    rainMm:Number.isFinite(precip)?precip:0,wetNow,start,stop,unknown:false,coverageUntil,
    timeZone:j?.timezone||'UTC',resolutionMinutes:60,source:'Open-Meteo hourly fallback',notRadar:true
  };
}
async function fetchBasicForecast(next,signal){
  const u=new URL('https://api.open-meteo.com/v1/forecast');
  u.search=new URLSearchParams({latitude:String(next.lat),longitude:String(next.lon),
    current:'temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m',
    hourly:'rain,showers,precipitation',timezone:'auto',timeformat:'unixtime',forecast_days:'2'}).toString();
  const response=await fetch(u,{cache:'no-store',credentials:'omit',signal});
  if(!response.ok) throw Error('Basic weather HTTP '+response.status);
  return basicForecast(await response.json());
}
function schedule(ms=POLL){clearTimeout(timer);timer=setTimeout(()=>void refresh(),ms)}
async function refresh(force=false){
  const next=pickPoint();if(!next){render();schedule();return}
  const key=pointKey(next.lat,next.lon),changed=!point||key!==pointKey(point.lat,point.lon);point=next;
  if(controller&&!changed)return;
  if(changed){raw=forecast=null;fetchedAt=0;controller?.abort();controller=null;serial++;render();alerts.locationChanged()}
  const interval=error?60000:POLL;
  if(!changed&&!force&&Date.now()-lastAttempt<interval){render();schedule(interval-(Date.now()-lastAttempt));return}
  const generation=++serial;lastAttempt=Date.now();controller=new AbortController();const active=controller,to=setTimeout(()=>active.abort(),12000);
  try{
    const response=await fetch(forecastUrl(next.lat,next.lon),{cache:'no-store',credentials:'omit',signal:active.signal});if(!response.ok)throw Error('Weather HTTP '+response.status);
    const j=await response.json(),parsed=parseForecast(j);if(generation!==serial)return;
    raw=j;forecast=parsed;fetchedAt=Date.now();error='';render();await alerts.check();
  }catch(e){
    // The 15-minute endpoint can be temporarily unavailable on some mobile
    // networks. Keep the weather card useful with the smaller current-weather request.
    if(generation===serial) try {
      forecast=await fetchBasicForecast(next,active.signal);fetchedAt=Date.now();
      error='';render();
    } catch(fallbackError) { error=String(fallbackError);render(); }
  }
  finally{clearTimeout(to);if(generation===serial){controller=null;schedule(error?60000:POLL)}}
}
function tick(){
  if(raw&&Date.now()-fetchedAt<=TTL)try{forecast=parseForecast(raw);if(!document.hidden){render();void alerts.check()}}catch{forecast=null;render()}
  else render();
}
const alerts=setupRainAlerts({getPoint:()=>point,getLanguage:lang,refresh:()=>refresh(true)});
function boot(){
  const meta=document.createElement('div');meta.id='rainForecastMeta';meta.style.cssText='font-size:.75rem;line-height:1.5;margin-top:8px';$('rainTiming')?.after(meta);alerts.mount(meta);
  window.FloodSafeRain={refresh,request:()=>window.FloodSafeCurrentLocation?.locate?.(),get state(){return {lat:point?.lat,lon:point?.lon,point,forecast,fetchedAt,error}}};
  for(const event of ['fscurrentlocation','fsfocuschange'])window.addEventListener(event,()=>void refresh());
  for(const event of ['fslanguage','fspurelanguage'])window.addEventListener(event,()=>{render();alerts.render()});
  for(const event of ['online','focus','pageshow'])window.addEventListener(event,()=>void refresh());
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){void refresh();tick()}});
  setInterval(tick,15000);void refresh();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
