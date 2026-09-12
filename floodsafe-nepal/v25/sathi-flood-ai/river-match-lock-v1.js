(()=>{
'use strict';
if(window.__SATHI_RIVER_MATCH_LOCK_V2__)return;
window.__SATHI_RIVER_MATCH_LOCK_V2__=true;

const $=s=>document.querySelector(s);
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[?!.:,;()\[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const compact=s=>norm(s).replace(/\s+/g,'');
const GENERIC=new Set(['ko','ma','maa','ka','ki','ke','yo','tyo','aile','ahile','aahele','status','level','water','river','khola','nadi','station','gauge','kati','kasto','cha','xa','chha','mero','malai','bhana','bhan','sathi','ai','the','of','in','at','current','latest','reading','jalastar','awastha','awstha','risk','warning','danger','alert','dangerous','safe','today','now','kun','kunai','kaha','kata','where','which','is','are','what','how','fresh','update','official','bipad','dhm']);
const NAME_GENERIC=new Set(['river','khola','nadi','station','gauge','at','the','of','बाढी','नदी','खोला','जलस्तर','स्थिति','अवस्था','चेतावनी','खतरा','तह','को','मा','के','कति','कस्तो','अहिले','आज']);
const KNOWN=[
  ['bishnumati',['bishnumati','bisnumati','bishnumati river','bishnumati khola','विष्णुमती','बिष्णुमती']],
  ['bagmati',['bagmati','बागमती']],['koshi',['koshi','kosi','कोशी']],['narayani',['narayani','नारायणी']],
  ['gandaki',['gandaki','गण्डकी']],['karnali',['karnali','कर्णाली']],['mahakali',['mahakali','महाकाली']],
  ['babai',['babai','बबई']],['rapti',['rapti','राप्ती']],['kamala',['kamala','कमला']],['trishuli',['trishuli','trisuli','त्रिशूली']],
  ['seti',['seti','सेती']],['tinau',['tinau','तिनाउ']],['manohara',['manohara','manahara','मनोहरा']],
  ['hanumante',['hanumante','हनुमन्ते']],['balkhu',['balkhu','बल्खु']],['dhobi',['dhobi','धोबी']],['nakhu',['nakhu','नख्खु','नखु']],
  ['mechi',['mechi','मेची']],['kanakai',['kanakai','कन्काई']],['west rapti',['west rapti','पश्चिम राप्ती']],['east rapti',['east rapti','पूर्वी राप्ती']]
];
const firstText=(o,keys)=>{for(const k of keys){const v=o?.[k];if(v!==undefined&&v!==null&&String(v).trim())return String(v).trim()}return''};
const firstNum=(o,keys)=>{for(const k of keys){const raw=o?.[k];if(raw===undefined||raw===null||raw==='')continue;const n=Number(raw);if(Number.isFinite(n))return n}return null};
const stationName=o=>firstText(o,['river_name','riverName','station_name','stationName','name','title','station','river'])||'नदी स्टेशन';
const stationId=o=>firstText(o,['stationSeriesId','station_series_id','stationId','station_id','stationIndex','station_index','id']);
const placeText=o=>[firstText(o,['municipality','municipality_name','municipalityName','localLevel','local_level','palika']),firstText(o,['district','district_name','districtName','district_title','admin2','county','state_district']),firstText(o,['province','province_name','provinceName'])].filter(Boolean).filter((x,i,a)=>a.indexOf(x)===i).join(', ');
const level=o=>firstNum(o,['_lastWaterLevel','_level','waterLevel','water_level','currentWaterLevel','current_level','level','value','latestLevel','latest_level']);
const warning=o=>firstNum(o,['_lastWarningLevel','_warning','warningLevel','warning_level','warningThreshold','warning_threshold','warning']);
const danger=o=>firstNum(o,['_lastDangerLevel','_danger','dangerLevel','danger_level','dangerThreshold','danger_threshold','danger']);
const discharge=o=>firstNum(o,['_lastDischarge','_discharge','discharge','currentDischarge','flow','streamflow']);
const measured=o=>firstText(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','timestamp','updatedAt']);
const statusRaw=o=>norm(firstText(o,['_derivedStatus','_officialStatus','status','status_name','alertStatus','alert_status','riskLevel','risk_level']));

function pushRows(out,v){if(Array.isArray(v))for(const row of v)if(row&&typeof row==='object')out.push(row)}
function allRows(){
  const s=window.FloodSafe?.state||{},out=[];
  for(const v of[s.currentRiverStations,s.latestRiverStations,s.allRiverStations,s.stations,s.rivers])pushRows(out,v);
  const latest=window.__BIPAD_LATEST__;
  if(latest&&typeof latest==='object')for(const k of['riverRows','rivers','stations','data','results'])pushRows(out,latest[k]);
  for(const v of[window.__OFFICIAL_RIVER_ROWS__,window.__FLOODSAFE_RIVER_ROWS__,window.__TRUSTED_RIVER_ROWS__])pushRows(out,v);
  const seen=new Set();
  return out.filter(row=>{const key=[stationId(row),norm(stationName(row)),measured(row),level(row)].join('|');if(seen.has(key))return false;seen.add(key);return true});
}
function words(s,set=GENERIC){return norm(s).split(' ').filter(x=>x.length>=2&&!set.has(x))}
function editDistance(a,b){a=String(a||'');b=String(b||'');if(a===b)return 0;if(!a)return b.length;if(!b)return a.length;const p=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let prev=p[0];p[0]=i;for(let j=1;j<=b.length;j++){const tmp=p[j],cost=a[i-1]===b[j-1]?0:1;p[j]=Math.min(p[j]+1,p[j-1]+1,prev+cost);prev=tmp}}return p[b.length]}
function containsAlias(q,alias){const nq=norm(q),na=norm(alias);if(!na)return false;if(/[\u0900-\u097f]/.test(na))return nq.includes(na);return (` ${nq} `).includes(` ${na} `)}
function parseNamedRiver(q){
  const nq=norm(q);if(!nq)return null;
  for(const [canonical,aliases] of KNOWN){for(const a of aliases){if(containsAlias(nq,a))return{named:true,key:canonical,label:a,tokens:words(canonical,NAME_GENERIC)}}}
  const explicit=/(^|\s)(river|khola|nadi)(\s|$)/.test(nq)||/[\u0900-\u097f]*(नदी|खोला)/.test(nq);
  if(!explicit)return null;
  const tokens=words(nq).filter(x=>!NAME_GENERIC.has(x));
  if(!tokens.length)return null;
  const useful=tokens.filter(x=>!GENERIC.has(x));if(!useful.length)return null;
  const key=useful.slice(0,3).join(' ');
  return{named:true,key,label:key,tokens:useful.slice(0,3)};
}
function nameFields(row){return [stationName(row),firstText(row,['river_name','riverName','river','waterway_name','waterwayName']),firstText(row,['station_name','stationName','name','title'])].filter(Boolean)}
function tokenMatch(a,b){if(a===b)return true;if(a.length>=5&&b.length>=5&&editDistance(a,b)<=1)return true;return false}
function rowMatches(req,row){
  if(!req||!row)return false;
  try{if(window.FloodSafeRiverAlias?.riverNameMatches){for(const n of nameFields(row))if(window.FloodSafeRiverAlias.riverNameMatches(req.key,n))return true}}catch{}
  const rt=req.tokens?.length?req.tokens:words(req.key,NAME_GENERIC);if(!rt.length)return false;
  for(const raw of nameFields(row)){
    const n=norm(raw),nt=words(n,NAME_GENERIC),nc=compact(n),rc=compact(req.key);
    if(rc.length>=4&&nc.includes(rc))return true;
    if(rt.every(a=>nt.some(b=>tokenMatch(a,b))))return true;
  }
  return false;
}
function measuredMs(o){const raw=measured(o);if(!raw)return 0;const n=Number(raw);if(Number.isFinite(n)&&String(raw).trim()!==''){const d=new Date(n<1e12?n*1000:n);return Number.isNaN(d.getTime())?0:d.getTime()}const d=new Date(raw);return Number.isNaN(d.getTime())?0:d.getTime()}
function bestNamedStation(req){
  const rows=allRows().filter(row=>rowMatches(req,row));if(!rows.length)return null;
  rows.sort((a,b)=>{const ar=level(a)!==null?1:0,br=level(b)!==null?1:0;if(br!==ar)return br-ar;const at=measuredMs(a),bt=measuredMs(b);if(bt!==at)return bt-at;return String(stationId(a)).localeCompare(String(stationId(b)))});
  return rows[0]||null;
}
function stage(o){
  const l=level(o),w=warning(o),d=danger(o),raw=statusRaw(o);
  if((l!==null&&d!==null&&d>0&&l>=d)||raw.includes('danger')||raw.includes('red')||raw.includes('खतरा'))return'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||raw.includes('warning')||raw.includes('orange')||raw.includes('चेतावनी'))return'warning';
  if(raw.includes('watch')||raw.includes('yellow')||raw.includes('सतर्क')||raw.includes('निगरानी'))return'watch';
  return l!==null?'normal':'unknown';
}
function ageInfo(o){const ms=measuredMs(o);if(!ms)return{text:'मापन समय उपलब्ध छैन',fresh:false};const min=Math.max(0,Math.round((Date.now()-ms)/60000));if(min<2)return{text:'भर्खरै',fresh:true};if(min<=20)return{text:`${min} मिनेटअघि`,fresh:true};if(min<60)return{text:`${min} मिनेटअघि`,fresh:false};const h=Math.round(min/60);if(h<24)return{text:`${h} घण्टाअघि`,fresh:false};return{text:`${Math.max(1,Math.round(h/24))} दिनअघि`,fresh:false}}
function noMatch(req){const n=String(req?.label||req?.key||'यो नदी').replace(/\b(river|khola|nadi)\b/gi,'').trim()||'यो नदी';return`${n} को matching official BIPAD/DHM नदी reading अहिले भेटिएन। अर्को नदीको data जोडेर गलत answer दिन्नँ। Official matching reading आएपछि मात्र यही नदीको status देखाउँछु।`}
function answerRow(row,req){
  if(!row)return noMatch(req);
  const name=stationName(row),place=placeText(row),l=level(row),w=warning(row),d=danger(row),flow=discharge(row),age=ageInfo(row),st=stage(row);
  if(l===null)return`हेरें है 🙂 ${name}${place?` (${place})`:''} matching official station नै भेटियो। तर अहिले यसको water-level reading उपलब्ध छैन, त्यसैले अर्को नदीको data जोडेर गलत answer दिन्नँ।`;
  let text=`हो, ${name} कै official reading भेटियो 🙂 ${age.text} जलस्तर ${l.toFixed(2)} मि. थियो`;
  if(age.fresh){const mood=st==='danger'?'अहिले खतरा तहमा छ 🚨':st==='warning'?'अहिले चेतावनी तहमा छ ⚠️':st==='watch'?'अहिले निगरानीमा छ 👀':st==='normal'?'अहिले सामान्य देखिन्छ 👍':'अहिलेको status स्पष्ट छैन';text+=` र ${mood}`}
  else text+='। यो reading 20 मिनेटभन्दा पुरानो भएकाले अहिलेको risk status भनेर अनुमान गर्दिनँ';
  const th=[];if(w!==null&&w>0)th.push(`warning ${w.toFixed(2)} मि.`);if(d!==null&&d>0)th.push(`danger ${d.toFixed(2)} मि.`);if(th.length)text+=`। Threshold ${th.join(', ')} छ`;
  if(flow!==null&&flow>0)text+=`। बहाव ${flow.toFixed(1)} m³/s छ`;
  text+='। Source BIPAD/DHM हो।';return text;
}
function resolve(text){const req=parseNamedRiver(text);if(!req)return null;const row=bestNamedStation(req);return{handled:true,request:req,row,answer:answerRow(row,req)}}
function add(text,type='ai'){const box=$('#sathiFloodMsgs');if(!box)return;const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');box.appendChild(d);box.scrollTop=box.scrollHeight}
function openPanel(){$('#sathiFloodOverlay')?.classList.add('open');const p=$('#sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false')}}
function handle(text,{voice=false}={}){
  text=String(text||'').trim();const r=resolve(text);if(!r)return false;
  openPanel();const input=$('#sathiInput');if(input){input.value='';input.style.height='auto'}add(text,'user');add(r.answer,'ai');
  if(voice&&window.SathiNative){try{window.SathiNative.speak(r.answer)}catch{}}
  try{window.dispatchEvent(new CustomEvent('sathi-river-match-lock-answer',{detail:{question:text,answer:r.answer,station_id:r.row?stationId(r.row):'',station_name:r.row?stationName(r.row):'',matched:!!r.row}}))}catch{}
  return true;
}

document.addEventListener('click',e=>{const send=e.target?.closest?.('#sathiSend'),quick=e.target?.closest?.('#sathiQuick button[data-q]');if(!send&&!quick)return;const input=$('#sathiInput'),text=quick?String(quick.dataset.q||'').trim():String(input?.value||'').trim();if(!resolve(text))return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();handle(text)},true);
document.addEventListener('keydown',e=>{if(e.key!=='Enter'||e.shiftKey||e.target?.id!=='sathiInput')return;const text=String(e.target.value||'').trim();if(!resolve(text))return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();handle(text)},true);
window.addEventListener('sathi-native-transcript',e=>{const text=String(e?.detail?.text||'').trim();if(!resolve(text))return;e.stopImmediatePropagation();handle(text,{voice:true})},true);

const original=window.SathiFloodAI?.answer;if(typeof original==='function'){window.SathiFloodAI.answer=q=>{const r=resolve(q);return r?r.answer:original(q)}}
window.SathiRiverMatchLock={version:'2.0.0-no-cross-river-fallback',parse:parseNamedRiver,matches:rowMatches,find:q=>{const req=parseNamedRiver(q);return req?bestNamedStation(req):null},resolve,answer:q=>resolve(q)?.answer||null};
})();
