(()=>{
'use strict';
if(window.__FS_WEATHER_NEARLIVE_V1__)return;window.__FS_WEATHER_NEARLIVE_V1__=true;
const API='https://api.open-meteo.com/v1/forecast',POLL=120000;
let timer=0,busy=false,state=null,lastKey='';
const $=id=>document.getElementById(id),n=v=>{const x=Number(v);return Number.isFinite(x)?x:null};
const rainCode=c=>[51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99].includes(Number(c));
const codeNe=c=>{c=Number(c);if(c===0)return'खुला';if([1,2].includes(c))return'आंशिक बादल';if(c===3)return'बादल';if([45,48].includes(c))return'कुहिरो';if([51,53,55,56,57].includes(c))return'सिमसिमे वर्षा';if([61,63,65,66,67,80,81,82].includes(c))return'वर्षा';if([95,96,99].includes(c))return'मेघगर्जन/चट्याङ';return'मौसम'};
function point(){try{const p=window.FloodSafeRain?.state?.point;if(p&&Number.isFinite(+p.lat)&&Number.isFinite(+p.lon))return{lat:+p.lat,lon:+p.lon,kind:p.kind||'monitor'}}catch{}return null}
function insideNepal(p){return !!p&&p.lat>=26&&p.lat<=31&&p.lon>=79.5&&p.lon<=89}
function clock(v,zone){const d=new Date(v);if(Number.isNaN(+d))return'—';try{return new Intl.DateTimeFormat('ne-NP',{timeZone:zone||'UTC',hour:'numeric',minute:'2-digit',hour12:true}).format(d)}catch{return d.toLocaleTimeString()}}
async function json(url){const c=new AbortController(),to=setTimeout(()=>c.abort(),9000);try{const r=await fetch(url,{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(to)}}
function assess(j,p){
  const c=j?.current||{},h=j?.hourly||{},times=Array.isArray(h.time)?h.time:[],probs=Array.isArray(h.precipitation_probability)?h.precipitation_probability:[];
  const amount=Math.max(0,n(c.precipitation)||0,n(c.rain)||0,n(c.showers)||0),code=n(c.weather_code),now=Date.now();
  let idx=-1,bestDelta=Infinity;for(let i=0;i<times.length;i++){const t=Date.parse(times[i]);if(!Number.isFinite(t))continue;const d=Math.abs(t-now);if(d<bestDelta){bestDelta=d;idx=i}}
  const prob=idx>=0?n(probs[idx]):null,observedLike=rainCode(code)||amount>=.01;
  let band='dry';if(observedLike)band='rain';else if(prob!==null&&prob>=70)band='likely';else if(prob!==null&&prob>=35)band='possible';
  return {lat:p.lat,lon:p.lon,insideNepal:insideNepal(p),amount,code,prob,band,temp:n(c.temperature_2m),humidity:n(c.relative_humidity_2m),wind:n(c.wind_speed_10m),time:c.time||new Date().toISOString(),zone:j?.timezone||'UTC',checkedAt:Date.now(),source:'Open-Meteo current/near-term model'};
}
function label(s){
  if(s.band==='rain')return`🌧️ ${codeNe(s.code)} संकेत छ${s.amount>0?` • ${s.amount.toFixed(1)} mm`:''}`;
  if(s.band==='likely')return`🌦️ नजिकको घण्टामा वर्षाको उच्च सम्भावना ${Math.round(s.prob)}%`;
  if(s.band==='possible')return`☁️ नजिकको घण्टामा वर्षा सम्भावना ${Math.round(s.prob)}%`;
  return`🌤️ अहिलेको model मा वर्षा संकेत छैन${s.prob!==null?` • नजिकको घण्टा ${Math.round(s.prob)}%`:''}`;
}
function apply(){
  const s=state;if(!s)return;
  const wt=$('weatherText'),rt=$('rainTiming');
  if(wt){
    if(s.band==='rain')wt.textContent='अहिलेको मौसम संकेत: '+codeNe(s.code);
    else if(s.band==='likely')wt.textContent=`अहिले/छिट्टै वर्षाको उच्च सम्भावना (${Math.round(s.prob)}%)`;
    else if(s.band==='possible'&&/अहिले वर्षा छैन|no rain now/i.test(wt.textContent||''))wt.textContent=`अहिले वर्षा पुष्टि छैन • सम्भावना ${Math.round(s.prob)}%`;
  }
  if(rt){
    const old=rt.textContent||'';
    if(s.band==='rain'&&/वर्षा देखिएको छैन|अहिले वर्षा छैन|no rain/i.test(old))rt.textContent='🌧️ current weather code/precipitation ले अहिले वर्षाको संकेत दिएको छ। सुरु/रोकिने ठ्याक्कै समय १५-मिनेट forecast बाट अपडेट हुँदैछ।';
    else if(s.band==='likely'&&/वर्षा देखिएको छैन|अहिले वर्षा छैन|no rain/i.test(old))rt.textContent=`🌦️ नजिकको घण्टामा वर्षाको सम्भावना ${Math.round(s.prob)}% छ। local drizzle सुरु भइसकेको हुन सक्छ; १५-मिनेट start/stop signal स्पष्ट भएपछि समय देखाइन्छ।`;
  }
  let meta=$('weatherTruthMeta');if(!meta){meta=document.createElement('div');meta.id='weatherTruthMeta';meta.style.cssText='font-size:.74rem;line-height:1.45;margin-top:7px;opacity:.9';($('rainForecastMeta')||rt)?.after?.(meta)}
  if(meta)meta.textContent=`${label(s)} • जाँच ${clock(s.time,s.zone)} • ${s.insideNepal?'नेपालमा नदी/वर्षा जोखिमका लागि BIPAD/DHM official observation छुट्टै प्रयोग हुन्छ।':'यो current weather model check हो; ground rain-gauge observation होइन।'}`;
}
async function refresh(force=false){
  const p=point();if(!p){state=null;schedule();return}const key=`${p.lat.toFixed(3)},${p.lon.toFixed(3)}`;if(!force&&busy)return;if(!force&&key===lastKey&&state&&Date.now()-state.checkedAt<90000){apply();schedule();return}busy=true;lastKey=key;
  try{const q=new URLSearchParams({latitude:String(p.lat),longitude:String(p.lon),timezone:'auto',forecast_days:'1',current:'temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m',hourly:'precipitation_probability'});state=assess(await json(API+'?'+q),p);window.FloodSafeWeatherNearLive={get state(){return state},refresh:()=>refresh(true)};apply();window.dispatchEvent(new CustomEvent('fsweathernearlive',{detail:state}))}catch(e){window.FloodSafeWeatherNearLive={get state(){return state},refresh:()=>refresh(true),error:String(e?.message||e)}}finally{busy=false;schedule()}
}
function schedule(){clearTimeout(timer);timer=setTimeout(()=>refresh(),POLL)}
function boot(){
  const target=$('rainTiming');if(target)new MutationObserver(()=>setTimeout(apply,0)).observe(target,{childList:true,characterData:true,subtree:true});
  for(const ev of['fscurrentlocation','fsfocuschange','online','focus','pageshow'])window.addEventListener(ev,()=>setTimeout(()=>refresh(true),100));
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(true)});refresh(true);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
