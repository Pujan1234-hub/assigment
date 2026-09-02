// Shared by the browser and push worker. Open-Meteo amounts cover the PRECEDING
// 15 minutes. In Nepal these are interpolated hourly forecasts, not radar nowcasts.
export const STEP=15*60*1000, WET_MM=.05, MAX_CURRENT_AGE=45*60*1000;
const amount=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0?v:null;
export function liquid(rain,showers){const a=amount(rain),b=amount(showers);return a===null||b===null?null:a+b}
export function pointKey(lat,lon){return `${Number(lat).toFixed(2)},${Number(lon).toFixed(2)}`}
export function forecastUrl(lat,lon){
  const u=new URL('https://api.open-meteo.com/v1/forecast');
  u.search=new URLSearchParams({latitude:String(lat),longitude:String(lon),current:'temperature_2m,relative_humidity_2m,rain,showers,weather_code,wind_speed_10m',minutely_15:'rain,showers',forecast_minutely_15:'48',timeformat:'unixtime',timezone:'auto'}).toString();return u.href;
}
export function parseForecast(j,now=Date.now()){
  const c=j?.current,series=j?.minutely_15,time=Number(c?.time)*1000;
  if(j?.current_units?.time!=='unixtime'||j?.minutely_15_units?.time!=='unixtime'||j?.minutely_15_units?.rain!=='mm'||j?.minutely_15_units?.showers!=='mm'||!Number.isFinite(time)||time>now+STEP||now-time>MAX_CURRENT_AGE)throw Error('Forecast time or units are unavailable/stale');
  const current=liquid(c.rain,c.showers),times=series?.time, rain=series?.rain,showers=series?.showers;
  if(current===null||!Array.isArray(times)||!Array.isArray(rain)||!Array.isArray(showers)||times.length!==rain.length||times.length!==showers.length||times.length<2)throw Error('Incomplete rainfall forecast');
  const slots=times.map((t,i)=>({start:Number(t)*1000-STEP,end:Number(t)*1000,mm:liquid(rain[i],showers[i])}));
  if(slots.some((s,i)=>!Number.isFinite(s.end)||(i>0&&s.end-slots[i-1].end!==STEP)))throw Error('Forecast interval gap');
  if(!slots.some(s=>s.start<=now&&s.end>=now)||slots.at(-1).end<=now)throw Error('Forecast does not cover the current time');
  const wetNow=current>=WET_MM;let start=null,stop=null,sawWet=wetNow,unknown=false;
  for(const slot of slots){
    if(slot.end<=now)continue;
    if(slot.mm===null){unknown=true;break}
    if(slot.mm>=WET_MM){
      if(!sawWet){start={from:slot.start,to:slot.end};sawWet=true}
    }else if(sawWet){stop={from:slot.start-STEP,to:slot.start};break}
  }
  return {current:c,rainMm:current,wetNow,start,stop,unknown,sourceTime:time,coverageUntil:slots.at(-1).end,timeZone:j.timezone||'UTC',resolutionMinutes:15,source:'Open-Meteo forecast',notRadar:true};
}
export function rainAlert(f,now=Date.now()){
  const at=f?.start?.from,lead=at-now;
  if(f?.wetNow||!Number.isFinite(at)||lead<=0||lead>STEP)return null;
  return {key:`rain-${at}`,minutes:Math.ceil(lead/60000),at,expiresAt:at};
}
export function clock(ms,zone='Asia/Kathmandu',lang='en'){
  try{return new Intl.DateTimeFormat(lang==='ne'?'ne-NP':'en-GB',{timeZone:zone,hour:'2-digit',minute:'2-digit',hour12:false}).format(ms)}catch{return new Date(ms).toISOString().slice(11,16)}
}
export function range(window,zone,lang){return window?`${clock(window.from,zone,lang)}–${clock(window.to,zone,lang)}`:'—'}
export function alertMessage(f,now,lang='ne'){
  const a=rainAlert(f,now);if(!a)return null;
  const ne=lang==='ne',zone=f.timeZone||'Asia/Kathmandu';
  return {title:ne?`🌧️ करिब ${a.minutes} मिनेटपछि वर्षाको सम्भावना`:`🌧️ Rain expected in about ${a.minutes} min`,body:ne?`अन्तिम छानिएको क्षेत्रमा अनुमानित सुरु ${range(f.start,zone,lang)}; रोक्ने ${range(f.stop,zone,lang)} (${zone})। मौसमअनुसार समय फेरिन सक्छ।`:`Last selected area: expected start ${range(f.start,zone,lang)}; end ${range(f.stop,zone,lang)} (${zone}). Forecast timing may change.`,tag:a.key,expiresAt:a.expiresAt};
}
