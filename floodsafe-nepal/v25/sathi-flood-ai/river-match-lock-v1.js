(()=>{
'use strict';
if(window.__SATHI_RIVER_MATCH_LOCK_V1__)return;
window.__SATHI_RIVER_MATCH_LOCK_V1__=true;

const $=s=>document.querySelector(s);
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[?!.:,;()\[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const GENERIC=new Set(['ko','ma','maa','ka','ki','ke','yo','tyo','aile','ahile','aahele','status','level','water','river','khola','nadi','station','gauge','kati','kasto','cha','xa','chha','mero','malai','bhana','bhan','sathi','ai','the','of','in','at','current','latest','reading']);
const NAME_GENERIC=new Set(['river','khola','nadi','station','gauge','at','the','of']);
const firstText=(o,keys)=>{for(const k of keys){const v=o?.[k];if(v!==undefined&&v!==null&&String(v).trim())return String(v).trim()}return''};
const firstNum=(o,keys)=>{for(const k of keys){const raw=o?.[k];if(raw===undefined||raw===null||raw==='')continue;const n=Number(raw);if(Number.isFinite(n))return n}return null};
const stationName=o=>firstText(o,['river_name','riverName','station_name','stationName','name','title'])||'नदी स्टेशन';
const stationId=o=>firstText(o,['stationSeriesId','station_series_id','stationId','station_id','stationIndex','station_index','id']);
const placeText=o=>[firstText(o,['municipality','municipality_name','municipalityName','localLevel','local_level','palika']),firstText(o,['district','district_name','districtName','district_title','admin2','county','state_district']),firstText(o,['province','province_name','provinceName'])].filter(Boolean).filter((x,i,a)=>a.indexOf(x)===i).join(', ');
const level=o=>firstNum(o,['_lastWaterLevel','_level','waterLevel','water_level','currentWaterLevel','current_level','level','value','latestLevel']);
const warning=o=>firstNum(o,['_lastWarningLevel','_warning','warningLevel','warning_level','warningThreshold','warning_threshold']);
const danger=o=>firstNum(o,['_lastDangerLevel','_danger','dangerLevel','danger_level','dangerThreshold','danger_threshold']);
const discharge=o=>firstNum(o,['_lastDischarge','_discharge','discharge','currentDischarge','flow','streamflow']);
const measured=o=>firstText(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','timestamp','updatedAt']);
const statusRaw=o=>norm(firstText(o,['_derivedStatus','_officialStatus','status','status_name','alertStatus','riskLevel']));

function allRows(){
  const s=window.FloodSafe?.state||{};
  const arrays=[s.currentRiverStations,s.latestRiverStations,s.allRiverStations,s.stations].filter(Array.isArray);
  const out=[];
  for(const arr of arrays)for(const row of arr||[])if(row&&typeof row==='object')out.push(row);
  return out;
}
function words(s,set=GENERIC){return norm(s).split(' ').filter(x=>x.length>=3&&!set.has(x))}
function editDistance(a,b){a=String(a||'');b=String(b||'');if(a===b)return 0;if(!a)return b.length;if(!b)return a.length;const p=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let prev=p[0];p[0]=i;for(let j=1;j<=b.length;j++){const tmp=p[j],cost=a[i-1]===b[j-1]?0:1;p[j]=Math.min(p[j]+1,p[j-1]+1,prev+cost);prev=tmp}}return p[b.length]}
function lexicalScore(q,row){
  const qt=words(q),name=norm(stationName(row)),nt=words(name,NAME_GENERIC);
  if(!qt.length||!nt.length)return 0;
  let best=0,total=0;
  for(const a of qt){
    let one=0;
    for(const b of nt){
      if(a===b)one=Math.max(one,120);
      else if(a.length>=4&&b.length>=4&&(a.includes(b)||b.includes(a)))one=Math.max(one,95);
      else if(a.length>=5&&b.length>=5){const d=editDistance(a,b);if(d<=1)one=Math.max(one,85);else if(d<=2&&Math.max(a.length,b.length)>=8)one=Math.max(one,70)}
    }
    best=Math.max(best,one);total+=one;
  }
  const coreQ=qt.join(' '),coreN=nt.join(' ');
  if(coreQ.length>=4&&(coreN.includes(coreQ)||coreQ.includes(coreN)))total+=160;
  return best>=70?total:0;
}
function measuredMs(o){const d=new Date(measured(o)||'');return Number.isNaN(d.getTime())?0:d.getTime()}
function bestNamedStation(q){
  const rows=allRows();if(!rows.length)return null;
  let topLex=0,candidates=[];
  for(const row of rows){const lex=lexicalScore(q,row);if(!lex)continue;if(lex>topLex){topLex=lex;candidates=[row]}else if(lex===topLex)candidates.push(row)}
  if(topLex<70||!candidates.length)return null;
  candidates.sort((a,b)=>{
    const ar=level(a)!==null?1:0,br=level(b)!==null?1:0;if(br!==ar)return br-ar;
    const at=measuredMs(a),bt=measuredMs(b);if(bt!==at)return bt-at;
    const aid=stationId(a),bid=stationId(b);return String(aid).localeCompare(String(bid));
  });
  return candidates[0]||null;
}
function stage(o){
  const l=level(o),w=warning(o),d=danger(o),raw=statusRaw(o);
  if((l!==null&&d!==null&&d>0&&l>=d)||raw.includes('danger')||raw.includes('red')||raw.includes('खतरा'))return'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||raw.includes('warning')||raw.includes('orange')||raw.includes('चेतावनी'))return'warning';
  if(raw.includes('watch')||raw.includes('yellow')||raw.includes('सतर्क')||raw.includes('निगरानी'))return'watch';
  return l!==null?'normal':'unknown';
}
function ageText(o){const ms=measuredMs(o);if(!ms)return'';const min=Math.max(0,Math.round((Date.now()-ms)/60000));if(min<2)return'भर्खरै';if(min<60)return`${min} मिनेटअघि`;const h=Math.round(min/60);if(h<24)return`${h} घण्टाअघि`;return'पुरानो उपलब्ध reading'}
function answer(row){
  const name=stationName(row),place=placeText(row),l=level(row),w=warning(row),d=danger(row),flow=discharge(row),age=ageText(row),st=stage(row);
  if(l===null)return`हेरें है 🙂 ${name}${place?` (${place})`:''} सही official station नै भेटियो। तर अहिले यसको water-level reading आएको छैन, त्यसैले अर्को नदीको data जोडेर गलत answer दिन्नँ। Reading आएपछि यही station को update दिन्छु।`;
  const mood=st==='danger'?'अहिले खतरा तहमा छ 🚨':st==='warning'?'अहिले चेतावनी तहमा छ ⚠️':st==='watch'?'अहिले निगरानीमा छ 👀':'अहिले सामान्य देखिन्छ 👍';
  let text=`हो, ${name} कै latest official reading भेटियो 🙂 ${age?`${age} `:''}जलस्तर ${l.toFixed(2)} मि. थियो र ${mood}`;
  const th=[];if(w!==null&&w>0)th.push(`warning ${w.toFixed(2)} मि.`);if(d!==null&&d>0)th.push(`danger ${d.toFixed(2)} मि.`);if(th.length)text+=`। Threshold ${th.join(', ')} छ`;
  if(flow!==null&&flow>0)text+=`। बहाव ${flow.toFixed(1)} m³/s छ`;
  text+='। Source BIPAD/DHM हो।';
  return text;
}
function add(text,type='ai'){const box=$('#sathiFloodMsgs');if(!box)return;const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');box.appendChild(d);box.scrollTop=box.scrollHeight}
function openPanel(){
  $('#sathiFloodOverlay')?.classList.add('open');
  const p=$('#sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false')}
}
function handle(text,{voice=false}={}){
  text=String(text||'').trim();if(!text)return false;
  const row=bestNamedStation(text);if(!row)return false;
  openPanel();const input=$('#sathiInput');if(input){input.value='';input.style.height='auto'}
  add(text,'user');const out=answer(row);add(out,'ai');
  if(voice&&window.SathiNative){try{window.SathiNative.speak(out)}catch{}}
  window.dispatchEvent(new CustomEvent('sathi-river-match-lock-answer',{detail:{question:text,answer:out,station_id:stationId(row),station_name:stationName(row)}}));
  return true;
}

document.addEventListener('click',e=>{
  const send=e.target?.closest?.('#sathiSend'),quick=e.target?.closest?.('#sathiQuick button[data-q]');if(!send&&!quick)return;
  const input=$('#sathiInput'),text=quick?String(quick.dataset.q||'').trim():String(input?.value||'').trim();
  if(!bestNamedStation(text))return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();handle(text);
},true);
document.addEventListener('keydown',e=>{
  if(e.key!=='Enter'||e.shiftKey||e.target?.id!=='sathiInput')return;const text=String(e.target.value||'').trim();
  if(!bestNamedStation(text))return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();handle(text);
},true);
window.addEventListener('sathi-native-transcript',e=>{
  const text=String(e?.detail?.text||'').trim();if(!bestNamedStation(text))return;
  e.stopImmediatePropagation();handle(text,{voice:true});
},true);

window.SathiRiverMatchLock={version:'1.0.0-strict-name-first',find:bestNamedStation,answer:q=>{const r=bestNamedStation(q);return r?answer(r):null}};
})();
