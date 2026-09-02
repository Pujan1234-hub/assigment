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
  if(!forecast||Date.now()-fetchedAt>TTL){el.textContent=tr('वर्षाको ताजा पूर्वानुमान उपलब्ध छैन • स्वतः पुनः जाँच हुँदैछ','Fresh rain forecast unavailable • retrying automatically');return}
  const f=forecast,zone=f.timeZone,parts=[];
  if(f.wetNow)parts.push(tr('🌧️ पूर्वानुमानमा अहिले वर्षा देखिएको छ','🌧️ Forecast indicates rain now'));
  else if(f.start){const m=Math.max(0,Math.ceil((f.start.from-Date.now())/60000));parts.push(tr(`🌧️ अनुमानित सुरु: ${range(f.start,zone,lang())} • करिब ${m} मिनेटपछि`,`🌧️ Expected start: ${range(f.start,zone,lang())} • in about ${m} min`))}
  else parts.push(f.unknown?tr('वर्षा सुरु हुने समय निर्धारण गर्न पर्याप्त data छैन','Not enough data to estimate rain onset'):tr(`${clock(f.coverageUntil,zone,lang())} सम्मको पूर्वानुमानमा वर्षा देखिएको छैन`,`No rain indicated in the forecast through ${clock(f.coverageUntil,zone,lang())}`));
  if(f.wetNow||f.start)parts.push(f.stop?tr(`🌤️ अनुमानित रोकिने: ${range(f.stop,zone,lang())}`,`🌤️ Expected end: ${range(f.stop,zone,lang())}`):tr('रोकिने समय उपलब्ध छैन','End time unavailable'));
  el.textContent=parts.join(' · ');
  const gpsFresh=window.FloodSafeCurrentLocation?.fresh;
  $('rainForecastMeta').textContent=tr(`${point.kind==='gps'?(gpsFresh?'हालको GPS':'पछिल्लो GPS'):'छानिएको निगरानी'} क्षेत्र • Open-Meteo पूर्वानुमान • ${zone} • जाँच ${clock(fetchedAt,zone,lang())}। यी अनुमान हुन्; ठ्याक्कै १५-मिनेटको स्थानीय मापन होइन।`,`${point.kind==='gps'?(gpsFresh?'Current GPS':'Last GPS'):'Selected monitoring'} area • Open-Meteo forecast • ${zone} • checked ${clock(fetchedAt,zone,lang())}. Estimates, not exact local 15-minute observations.`)+(error?tr(' पछिल्लो जाँच असफल भयो।',' Latest check failed.'):'');
}
function renderWeather(){
  if(!forecast||Date.now()-fetchedAt>TTL){for(const id of ['temp','rain','humidity','wind'])if($(id))$(id).textContent='—';if($('weatherText'))$('weatherText').textContent=tr('ताजा मौसम पूर्वानुमान उपलब्ध छैन','Fresh weather forecast unavailable');return}const c=forecast.current;
  for(const [id,value] of Object.entries({temp:Number.isFinite(c.temperature_2m)?Math.round(c.temperature_2m)+'°':'—°',rain:forecast.rainMm.toFixed(1)+' mm',humidity:Number.isFinite(c.relative_humidity_2m)?Math.round(c.relative_humidity_2m)+'%':'—',wind:Number.isFinite(c.wind_speed_10m)?Math.round(c.wind_speed_10m)+' km/h':'—'}))if($(id))$(id).textContent=value;
  if($('weatherText'))$('weatherText').textContent=forecast.wetNow?tr('पूर्वानुमान: वर्षा','Forecast: rain'):tr('पूर्वानुमान: अहिले वर्षा छैन','Forecast: no rain now');
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
  }catch(e){if(generation===serial){error=String(e);render()}}
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
