(()=>{
'use strict';
if(window.SathiFloodAIEngine)return;

const DEVANAGARI=/[\u0900-\u097F]/;
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[.,!?;:()[\]{}"'`~]/g,' ').replace(/\s+/g,' ').trim();
const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const now=()=>Date.now();
const neTime=t=>{
  const d=new Date(t||Date.now());
  if(Number.isNaN(+d))return 'समय उपलब्ध छैन';
  try{return new Intl.DateTimeFormat('ne-NP',{timeZone:'Asia/Kathmandu',hour:'numeric',minute:'2-digit',year:'numeric',month:'short',day:'numeric'}).format(d)}catch{return d.toLocaleString()}
};
const minsAgo=t=>{
  const ms=now()-new Date(t||0).getTime();
  if(!Number.isFinite(ms)||ms<0)return null;
  const m=Math.floor(ms/60000);
  if(m<1)return 'भर्खरै';
  if(m<60)return `${m} मिनेटअघि`;
  const h=Math.floor(m/60);return `${h} घण्टा ${m%60} मिनेटअघि`;
};

const FLOOD_WORDS=['flood','badi','baadi','बाढी','khola','kholaa','खोला','nadi','नदी','river','pani','पानी','rain','barsa','barsha','वर्षा','danger','warning','alert','chetawani','चेतावनी','jalastar','जलस्तर','water level','gauge','station','koshi','karnali','gandaki','bagmati','rapti','mahakali','narayani'];
const RAIN_WORDS=['rain','pani par','pani kati','barsa','barsha','वर्षा','पानी प','रोकिन','rok','start','sur','kati baje','कति बजे'];
const SAFETY_WORDS=['ke garne','k garne','kasari bachne','suraksha','safe','safety','bachna','evacu','बच्ने','सुरक्षा','के गर्ने','उद्धार','emergency'];
const LIST_WORDS=['kun khola','kun nadi','kata badi','कुन खोला','कुन नदी','कहाँ बाढी','danger ma','warning ma','खतरामा','चेतावनीमा'];
const NEAR_WORDS=['najik','nजिक','nira','near','mero area','mero ghar','वरिपरि','नजिक','मेरो क्षेत्र','मेरो घर'];

function includesAny(q,list){return list.some(x=>q.includes(x))}
function isFloodQuestion(q){return includesAny(q,FLOOD_WORDS)}

function source(win){
  const w=win||window;
  return {
    w,
    state:w.FloodSafe?.state||{},
    riverApi:w.FloodSafeRiverRealtime||{},
    riverState:w.__fsRiverRealtimeState||{},
    rain:w.FloodSafeRain?.state||{},
    gps:w.FloodSafeCurrentLocation?.last||null
  };
}

function stationName(o,api){
  try{if(api?.name)return String(api.name(o)||'').trim()}catch{}
  return String(o?.river_name||o?.riverName||o?.station_name||o?.stationName||o?.title||o?.name||'अज्ञात नदी स्टेशन').trim();
}
function stationLevel(o,api){
  try{if(api?.level){const x=api.level(o);if(Number.isFinite(x))return x}}catch{}
  return num(o?._lastWaterLevel??o?.waterLevel??o?.water_level??o?.level??o?.value);
}
function stationWarning(o,api){
  try{if(api?.warning){const x=api.warning(o);if(Number.isFinite(x))return x}}catch{}
  return num(o?._lastWarningLevel??o?.warningLevel??o?.warning_level);
}
function stationDanger(o,api){
  try{if(api?.danger){const x=api.danger(o);if(Number.isFinite(x))return x}}catch{}
  return num(o?._lastDangerLevel??o?.dangerLevel??o?.danger_level);
}
function stationTime(o,api){
  try{if(api?.measureTime)return api.measureTime(o)}catch{}
  return o?._measurementTime||o?.measurementTime||o?.waterLevelOn||o?.timestamp||null;
}
function stationStage(o,api){
  const raw=String(o?._derivedStatus||o?._officialStatus||o?.status||'').toLowerCase();
  if(/danger|red|खतरा/.test(raw))return 'danger';
  if(/warning|orange|चेतावनी/.test(raw))return 'warning';
  if(/watch|rising|yellow|बढ/.test(raw))return 'watch';
  const l=stationLevel(o,api),w=stationWarning(o,api),d=stationDanger(o,api);
  if(l!==null&&d!==null&&d>0&&l>=d)return 'danger';
  if(l!==null&&w!==null&&w>0&&l>=w)return 'warning';
  return l===null?'unknown':'normal';
}
function stageNe(st){return st==='danger'?'🔴 खतरा':st==='warning'?'🟠 चेतावनी':st==='watch'?'🟡 निगरानी':'🟢 सामान्य'}

function allStations(src){
  const s=src.state;
  const rows=s?.allRiverStations||s?.latestRiverStations||s?.currentRiverStations||s?.stations||[];
  return Array.isArray(rows)?rows:[];
}
function currentStations(src){
  const s=src.state;
  const rows=s?.currentRiverStations||s?.latestRiverStations||s?.stations||[];
  return Array.isArray(rows)?rows:[];
}
function riskStations(src){
  return currentStations(src).map(o=>({o,name:stationName(o,src.riverApi),stage:stationStage(o,src.riverApi),level:stationLevel(o,src.riverApi),warning:stationWarning(o,src.riverApi),danger:stationDanger(o,src.riverApi),time:stationTime(o,src.riverApi)})).filter(x=>x.stage==='danger'||x.stage==='warning'||x.stage==='watch');
}

function aliases(name){
  const n=norm(name);
  return [n,n.replace(/river|nadi|khola|kholaa|नदी|खोला/g,'').trim()].filter(Boolean);
}
function findStationByQuestion(q,src){
  const nq=norm(q),rows=allStations(src);
  let best=null,bestScore=0;
  for(const o of rows){
    const name=stationName(o,src.riverApi);
    for(const a of aliases(name)){
      if(a.length<3)continue;
      let score=0;
      if(nq.includes(a))score=a.length+20;
      else{
        const toks=a.split(/\s+/).filter(x=>x.length>=3);
        score=toks.reduce((s,t)=>s+(nq.includes(t)?t.length:0),0);
      }
      if(score>bestScore){bestScore=score;best=o}
    }
  }
  return bestScore>=4?best:null;
}

function stationAnswer(o,src){
  const name=stationName(o,src.riverApi),st=stationStage(o,src.riverApi),l=stationLevel(o,src.riverApi),w=stationWarning(o,src.riverApi),d=stationDanger(o,src.riverApi),t=stationTime(o,src.riverApi);
  if(l===null||!t)return `🌊 ${name} को अहिलेको आधिकारिक ताजा जलस्तर उपलब्ध छैन। पुरानो डेटा अनुमान गरेर देखाइएको छैन।`;
  const bits=[`🌊 ${name}: ${stageNe(st)}`];
  bits.push(`जलस्तर ${l.toFixed(2)} मिटर`);
  if(w!==null)bits.push(`चेतावनी तह ${w.toFixed(2)} मि.`);
  if(d!==null)bits.push(`खतरा तह ${d.toFixed(2)} मि.`);
  const age=minsAgo(t);bits.push(`मापन ${neTime(t)}${age?` (${age})`:''}`);
  if(st==='danger')bits.push('⚠️ जोखिम उच्च छ। नदी किनार/तल्लो क्षेत्रमा नजानुहोस् र स्थानीय आधिकारिक निर्देशन पालना गर्नुहोस्।');
  else if(st==='warning')bits.push('⚠️ पानी चेतावनी तहमा वा नजिक छ। सतर्क रहनुहोस् र सुरक्षित स्थानको तयारी गर्नुहोस्।');
  else if(st==='watch')bits.push('पानीको अवस्था निगरानीमा राख्नुहोस्।');
  else bits.push('अहिले उपलब्ध आधिकारिक मापनअनुसार खतरा तह पार गरेको देखिँदैन।');
  return bits.join(' • ');
}

function listRiskAnswer(src){
  const rs=riskStations(src);
  if(!currentStations(src).length)return 'अहिले BIPAD/DHM को ताजा नदी मापन उपलब्ध छैन। ताजा डेटा आएपछि मात्र जोखिम देखाइन्छ।';
  if(!rs.length)return 'अहिले उपलब्ध ताजा आधिकारिक नदी मापनमा चेतावनी वा खतरा तहमा पुगेको स्टेशन भेटिएन।';
  const sorted=rs.sort((a,b)=>({danger:3,warning:2,watch:1}[b.stage]-({danger:3,warning:2,watch:1}[a.stage]));
  const top=sorted.slice(0,8).map(x=>`${stageNe(x.stage)} ${x.name}${x.level!==null?` — ${x.level.toFixed(2)} मि.`:''}`).join('\n');
  const more=sorted.length>8?`\n… थप ${sorted.length-8} स्टेशन निगरानीमा छन्।`:'';
  return `अहिले जोखिम देखिएका नदी/खोला स्टेशनहरू:\n${top}${more}`;
}

function rainAnswer(src){
  const r=src.rain||{},f=r.forecast;
  if(!f)return '🌦️ चयन गरिएको निगरानी क्षेत्रको ताजा वर्षा पूर्वानुमान अहिले उपलब्ध छैन। FloodSafe ले स्वतः पुनः जाँच गरिरहेको छ।';
  const parts=[];
  if(f.wetNow)parts.push('🌧️ पूर्वानुमान अनुसार अहिले वर्षा भइरहेको/देखिएको छ।');
  else parts.push('🌤️ पूर्वानुमान अनुसार अहिले वर्षा देखिएको छैन।');
  if(f.start?.from){
    const m=Math.max(0,Math.ceil((f.start.from-Date.now())/60000));
    parts.push(`वर्षा सुरु हुने अनुमानित समय ${neTime(f.start.from)} हो${m?` — करिब ${m} मिनेटपछि`:''}।`);
  }else if(!f.wetNow)parts.push('हाल उपलब्ध पूर्वानुमानमा नजिकै वर्षा सुरु हुने स्पष्ट समय छैन।');
  if(f.stop?.from)parts.push(`वर्षा रोकिने अनुमानित समय ${neTime(f.stop.from)} हो।`);
  else if(f.wetNow||f.start)parts.push('रोकिने समय अहिले स्पष्ट छैन।');
  parts.push('यो मौसम पूर्वानुमान हो, पक्का स्थानीय मापन होइन।');
  return parts.join(' ');
}

function nearbyAnswer(src){
  const s=src.state,near=s?.nearStations||s?.nearbyStations||[];
  if(Array.isArray(near)&&near.length){
    const rows=near.slice(0,5).map(o=>stationAnswer(o,src));
    return `तपाईंको निगरानी क्षेत्र नजिकका नदी स्टेशन:\n${rows.join('\n')}`;
  }
  return 'तपाईंको निगरानी क्षेत्र नजिकको नदी जोखिम बताउन FloodSafe मा नेपालभित्र आफ्नो घर/निगरानी स्थान छान्नुहोस्। त्यसपछि नजिकका आधिकारिक स्टेशनको अवस्था पढेर म बताउँछु।';
}

function safetyAnswer(q){
  const nq=norm(q);
  if(nq.includes('gaadi')||nq.includes('car')||nq.includes('drive')||nq.includes('सवारी'))return '🚗 बाढीको पानीले ढाकेको सडकमा गाडी नचलाउनुहोस्। पानीको गहिराइ र सडकको अवस्था बाहिरबाट थाहा नहुन सक्छ। सुरक्षित वैकल्पिक बाटो लिनुहोस् र प्रहरी/स्थानीय प्रशासनको निर्देशन पालना गर्नुहोस्।';
  if(nq.includes('ghar')||nq.includes('घर'))return '🏠 बाढीको जोखिम भएमा फोन, कागजात, औषधि, पानी र आवश्यक सामान लिएर सुरक्षित उच्च स्थानतिर जानुहोस्। बिजुली सुरक्षित रूपमा बन्द गर्न सकिन्छ भने मात्र बन्द गर्नुहोस्; बगिरहेको पानीमा नहिँड्नुहोस्।';
  return '🛟 बाढीको बेला नदी/खोला किनारबाट टाढा रहनुहोस्, बगिरहेको पानी पार नगर्नुहोस्, उच्च सुरक्षित स्थानमा जानुहोस्, परिवारलाई खबर गर्नुहोस् र स्थानीय प्रशासन/प्रहरी/उद्धार निकायको निर्देशन पालना गर्नुहोस्।';
}

function freshnessAnswer(src){
  const rs=src.riverState||{};
  const newest=rs.newestMeasurement||rs.newestKnownMeasurement||null;
  if(!newest)return 'अहिले ताजा नदी मापनको समय उपलब्ध छैन।';
  return `सबैभन्दा नयाँ उपलब्ध आधिकारिक नदी मापन ${neTime(newest)} को हो${minsAgo(newest)?` (${minsAgo(newest)})`:''}।`;
}

function unsupportedFloodAnswer(){
  return 'म FloodSafe Nepal को बाढी सहायक हुँ। म ताजा नदी/खोला अवस्था, जलस्तर, चेतावनी/खतरा, वर्षा सुरु–रोकिने अनुमान, नजिकको जोखिम र बाढी सुरक्षा बारे नेपालीमा बताउन सक्छु। तपाईं कुन ठाउँ वा नदीबारे जान्न चाहनुहुन्छ?';
}

function answer(question,sourceWindow){
  const q=norm(question),src=source(sourceWindow);
  if(!q)return 'कृपया बाढी, नदी वा वर्षाबारे प्रश्न सोध्नुहोस्।';
  if(!isFloodQuestion(q))return 'म FloodSafe Nepal को SATHI हुँ। अहिले म बाढी, नदी/खोला, वर्षा र बाढी सुरक्षासम्बन्धी प्रश्नको मात्र उत्तर दिन्छु।';
  if(includesAny(q,SAFETY_WORDS))return safetyAnswer(q);
  if(q.includes('update')||q.includes('fresh')||q.includes('latest')||q.includes('कहिलेको')||q.includes('ताजा'))return freshnessAnswer(src);
  if(includesAny(q,RAIN_WORDS))return rainAnswer(src);
  if(includesAny(q,NEAR_WORDS))return nearbyAnswer(src);
  const station=findStationByQuestion(q,src);
  if(station)return stationAnswer(station,src);
  if(includesAny(q,LIST_WORDS)||q.includes('kun')||q.includes('कुन'))return listRiskAnswer(src);
  if(q.includes('danger')||q.includes('warning')||q.includes('alert')||q.includes('खतरा')||q.includes('चेतावनी'))return listRiskAnswer(src);
  return unsupportedFloodAnswer();
}

window.SathiFloodAIEngine={answer,isFloodQuestion,source,allStations,currentStations,riskStations,findStationByQuestion,stationAnswer,listRiskAnswer,rainAnswer,nearbyAnswer,safetyAnswer,version:'0.1.0-additive'};
})();
