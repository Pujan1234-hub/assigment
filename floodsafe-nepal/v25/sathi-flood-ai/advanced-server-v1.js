(()=>{
'use strict';
if(window.__SATHI_FLOOD_ADVANCED_V1__)return;
window.__SATHI_FLOOD_ADVANCED_V1__=true;

const ROOT='https://camkoacuokffryyrygda.supabase.co/functions/v1';
const DEVICE_ID_KEY='floodsafe_sathi_device_id_v1';
const DEVICE_TOKEN_KEY='floodsafe_sathi_device_token_v1';
const HISTORY_KEY='floodsafe_sathi_history_v1';
const VERSION='2.1.3-context-safe';
const history=(()=>{
  try{
    const a=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');
    return Array.isArray(a)?a.filter(x=>x&&['user','assistant'].includes(x.role)&&typeof x.content==='string').slice(-12):[];
  }catch{return[]}
})();
const saveHistory=()=>{try{localStorage.setItem(HISTORY_KEY,JSON.stringify(history.slice(-12)))}catch{}};
const $=s=>document.querySelector(s);
const add=(text,type='ai')=>{
  const box=$('#sathiFloodMsgs');if(!box)return null;
  const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');box.appendChild(d);box.scrollTop=box.scrollHeight;return d;
};
const open=()=>{
  $('#sathiFloodOverlay')?.classList.add('open');
  const p=$('#sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false')}
};
const setAdvancedLabels=()=>{
  const input=$('#sathiInput');if(input)input.placeholder='जिल्ला, तापक्रम, वर्षा, नदी/खोला, खतरा वा नजिकको जोखिम सोध्नुहोस्…';
  const small=$('#sathiFloodPanel .sathiHeadText small');if(small)small.textContent='Advanced live AI • BIPAD/DHM नदी • जिल्ला मौसम • GPS risk';
  const q=$('#sathiQuick');if(q&&!q.dataset.advanced){
    q.dataset.advanced='1';
    q.innerHTML='<button data-q="अहिले नेपालमा कुन कुन खोला danger वा warning मा छन्?">🔴 खतरा नदी</button><button data-q="चितवनको अहिले तापक्रम कति छ र पानी कहिले पर्छ?">🌦️ जिल्ला मौसम</button><button data-q="मेरो नजिक २५ किमिभित्र कुन नदी जोखिममा छ?">📍 मेरो नजिक</button><button data-q="अहिले कुन जिल्लामा active flood वा heavy rain alert छ?">🚨 जिल्ला alert</button>';
  }
};

async function post(path,body,timeout=22000){
  const ctl=new AbortController();const id=setTimeout(()=>ctl.abort(),timeout);
  try{
    const r=await fetch(`${ROOT}/${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store',signal:ctl.signal});
    const j=await r.json().catch(()=>({}));
    if(!r.ok||j?.ok===false)throw new Error(j?.error||`HTTP ${r.status}`);
    return j;
  }finally{clearTimeout(id)}
}
async function ensureDevice(){
  let id='';let token='';
  try{id=localStorage.getItem(DEVICE_ID_KEY)||'';token=localStorage.getItem(DEVICE_TOKEN_KEY)||''}catch{}
  if(id&&token)return{device_id:id,device_token:token};
  const j=await post('sathi-api',{action:'register_device',device_name:'FloodSafe Nepal SATHI',platform:window.SathiNative?'android':'web',app_version:'0.5.0'},12000);
  id=String(j?.device_id||'');token=String(j?.device_token||'');
  if(!id||!token)throw new Error('device_registration_failed');
  try{localStorage.setItem(DEVICE_ID_KEY,id);localStorage.setItem(DEVICE_TOKEN_KEY,token)}catch{}
  return{device_id:id,device_token:token};
}
function currentLocation(){
  const candidates=[];
  try{candidates.push(window.FloodSafeRain?.state?.point)}catch{}
  try{candidates.push(window.FloodSafe?.state?.monitorPoint,window.FloodSafe?.state?.selectedPoint,window.FloodSafe?.state?.location)}catch{}
  for(const p of candidates){
    const lat=Number(p?.lat??p?.latitude),lon=Number(p?.lon??p?.lng??p?.longitude);
    if(Number.isFinite(lat)&&Number.isFinite(lon)&&lat>=26&&lat<=31.8&&lon>=79.5&&lon<=89){
      const label=String(p?.name||p?.label||($('#place')?.textContent||'')).replace(/^📍\s*/,'').trim();
      return{lat,lon,label:label||'निगरानी स्थान'};
    }
  }
  return null;
}
function remember(role,content){
  const t=String(content||'').trim();if(!t)return;
  history.push({role,content:t.slice(0,1400)});if(history.length>12)history.splice(0,history.length-12);saveHistory();
}
function localFallback(q){
  try{return window.SathiFloodAI?.__localAnswer?.(q)||'AI server जोडिन सकेन। उपलब्ध local FloodSafe data बाट फेरि प्रयास गर्नुहोस्।'}catch{return'AI server जोडिन सकेन।'}
}
async function advanced(q,{voice=false,placeholder=null}={}){
  q=String(q||'').trim();if(!q)return'';
  try{
    const cred=await ensureDevice();
    const body={...cred,question:q,recent_messages:history.slice(-10),location:currentLocation(),nearby_radius_km:25,client:'floodsafe-nepal-v25',client_ai_version:VERSION};
    const j=await post('sathi-flood-answer',body,24000);
    const answer=String(j?.answer_ne||'').trim();
    const spoken=String(j?.spoken_text||answer).trim();
    if(!answer)throw new Error('empty_ai_answer');
    remember('user',q);remember('assistant',answer);
    if(placeholder){placeholder.className='sathiMsg ai';placeholder.textContent=answer;placeholder.scrollIntoView({block:'nearest'})}
    if(voice&&window.SathiNative&&spoken){try{window.SathiNative.speak(spoken)}catch{}}
    window.dispatchEvent(new CustomEvent('sathi-advanced-answer',{detail:{question:q,answer,spoken,meta:j?.facts_meta||{},sources:j?.sources||[]}}));
    return answer;
  }catch(err){
    const fallback=localFallback(q);
    remember('user',q);remember('assistant',fallback);
    if(placeholder){placeholder.className='sathiMsg ai';placeholder.textContent=`${fallback}\n\n⚠️ Advanced AI server उपलब्ध नभएकाले local basic mode प्रयोग भयो।`}
    if(voice&&window.SathiNative){try{window.SathiNative.speak(fallback)}catch{}}
    return fallback;
  }
}

function installWrapper(){
  const ai=window.SathiFloodAI;
  if(!ai||typeof ai.answer!=='function'){setTimeout(installWrapper,120);return}
  if(ai.__advancedInstalled)return;
  const original=ai.answer.bind(ai);
  ai.__localAnswer=original;
  ai.askAdvanced=(q,opts={})=>advanced(q,opts);
  ai.answer=q=>{
    const text=String(q||'').trim();
    if(!text)return original(q);
    setTimeout(()=>{
      const box=$('#sathiFloodMsgs');if(!box)return;
      const bubbles=[...box.querySelectorAll('.sathiMsg.ai')];
      const placeholder=[...bubbles].reverse().find(x=>x.dataset?.sathiPending==='1'||x.textContent==='🧠 ताजा official data मिलाउँदैछु…');
      if(placeholder)advanced(text,{placeholder});
    },0);
    return'🧠 ताजा official data मिलाउँदैछु…';
  };
  ai.__advancedInstalled=true;ai.version=VERSION;
  setAdvancedLabels();
  const box=$('#sathiFloodMsgs');if(box){
    new MutationObserver(ms=>{for(const m of ms)for(const n of m.addedNodes){if(n?.nodeType===1&&n.classList?.contains('ai')&&n.textContent==='🧠 ताजा official data मिलाउँदैछु…')n.dataset.sathiPending='1'}}).observe(box,{childList:true});
  }
}

window.addEventListener('sathi-native-transcript',event=>{
  const text=String(event?.detail?.text||'').trim();if(!text)return;
  event.stopImmediatePropagation();
  open();setAdvancedLabels();
  const input=$('#sathiInput');if(input)input.value='';
  add(text,'user');
  const p=add('🧠 ताजा official data मिलाउँदैछु…','status');
  advanced(text,{voice:true,placeholder:p});
},true);

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{installWrapper();setTimeout(setAdvancedLabels,300)},{once:true});
else{installWrapper();setTimeout(setAdvancedLabels,300)}
window.addEventListener('online',()=>{if(window.SathiFloodAI?.__advancedInstalled)setAdvancedLabels()});
})();
