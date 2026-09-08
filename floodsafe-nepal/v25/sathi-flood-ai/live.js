(()=>{
'use strict';
if(window.__SATHI_FLOOD_LIVE__) return;
window.__SATHI_FLOOD_LIVE__=true;

const NEPAL_TZ='Asia/Kathmandu';
const $=s=>document.querySelector(s);
const norm=s=>String(s||'').toLowerCase().normalize('NFKC').replace(/[?!.:,;()\[\]{}"'`]/g,' ').replace(/\s+/g,' ').trim();
const has=(q,...xs)=>xs.some(x=>q.includes(x));
const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
const firstNum=(o,keys)=>{for(const k of keys){const n=num(o?.[k]);if(n!==null)return n}return null};
const firstText=(o,keys)=>{for(const k of keys){const v=o?.[k];if(v!==undefined&&v!==null&&String(v).trim())return String(v).trim()}return ''};
const riverName=o=>firstText(o,['stationName','station_name','name','title','riverName','river_name','station','river']);
const level=o=>firstNum(o,['_level','waterLevel','water_level','level','value','latestLevel','latest_level']);
const warning=o=>firstNum(o,['_warning','warningLevel','warning_level','warning','warningThreshold','warning_threshold']);
const danger=o=>firstNum(o,['_danger','dangerLevel','danger_level','danger','dangerThreshold','danger_threshold']);
const discharge=o=>firstNum(o,['_discharge','discharge','flow','streamflow']);
const measured=o=>firstText(o,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','measurement_time','observationTime','timestamp','updatedAt']);

function stage(o){
  try{
    if(window.FloodSafeRiverRealtime&&typeof window.FloodSafeRiverRealtime.stage==='function'){
      const s=String(window.FloodSafeRiverRealtime.stage(o)||'').toLowerCase();
      if(['danger','warning','watch','normal','unknown'].includes(s))return s;
    }
  }catch{}
  const l=level(o),w=warning(o),d=danger(o),raw=norm(firstText(o,['_officialStatus','status','status_name','alertStatus','alert_status','riskLevel','risk_level']));
  if((l!==null&&d!==null&&d>0&&l>=d)||has(raw,'danger','red','खतरा'))return 'danger';
  if((l!==null&&w!==null&&w>0&&l>=w)||has(raw,'warning','orange','चेतावनी'))return 'warning';
  if(has(raw,'watch','yellow','सतर्क'))return 'watch';
  if(l!==null)return 'normal';
  return 'unknown';
}
function stageNe(s){return s==='danger'?'🔴 खतरा':s==='warning'?'🟠 चेतावनी':s==='watch'?'🟡 निगरानी':s==='normal'?'🟢 सामान्य':'⚪ अवस्था अस्पष्ट'}
function source(){
  const fs=window.FloodSafe||{};
  const st=fs.state||{};
  const all=[st.currentRiverStations,st.latestRiverStations,st.allRiverStations,st.stations].find(Array.isArray)||[];
  const current=Array.isArray(st.currentRiverStations)?st.currentRiverStations:all;
  let rain=null;
  try{rain=window.FloodSafeRain?.state||null}catch{}
  return {fs,st,all,current,rain};
}
function stationKey(s){return norm(riverName(s)).replace(/\b(river|khola|nadi|station|at|gauge)\b/g,' ').replace(/\s+/g,' ').trim()}
function questionKey(q){return norm(q).replace(/\b(ye|hey|sathi|flood|badi|baadi|khola|nadi|river|station|ko|ma|maa|kasto|awastha|awstha|status|cha|xa|chha|k|ke|kati|level|jalastar|water)\b/g,' ').replace(/[कोमाखोलानदीबाढीजलस्तरअवस्थाछकेकति]/g,' ').replace(/\s+/g,' ').trim()}
function findStation(q,src){
  const nq=norm(q), qk=questionKey(q);
  let best=null,score=0;
  for(const s of src.all){
    const name=riverName(s);if(!name)continue;
    const nk=stationKey(s), nn=norm(name);
    let sc=0;
    if(nn&&nq.includes(nn))sc=100+nn.length;
    else if(nk&&qk&&qk.includes(nk))sc=80+nk.length;
    else if(nk&&qk&&nk.includes(qk)&&qk.length>=3)sc=60+qk.length;
    else if(qk){
      const qt=qk.split(' ').filter(x=>x.length>2), nt=nk.split(' ');
      sc=qt.filter(x=>nt.some(y=>y.includes(x)||x.includes(y))).length*10;
    }
    if(sc>score){score=sc;best=s}
  }
  return score>=10?best:null;
}
function formatTime(v){
  if(!v)return '';
  let d;
  if(typeof v==='number')d=new Date(v<1e12?v*1000:v);else d=new Date(v);
  if(Number.isNaN(d.getTime()))return String(v);
  return new Intl.DateTimeFormat('ne-NP',{timeZone:NEPAL_TZ,hour:'numeric',minute:'2-digit',hour12:true}).format(d);
}
function timeAgo(v){
  const d=new Date(v);if(Number.isNaN(d.getTime()))return '';
  const m=Math.max(0,Math.round((Date.now()-d.getTime())/60000));
  if(m<1)return 'अहिले';if(m<60)return `${m} मिनेटअघि`;const h=Math.floor(m/60);if(h<24)return `${h} घण्टा ${m%60} मिनेटअघि`;return `${Math.floor(h/24)} दिनअघि`;
}
function stationAnswer(s){
  const name=riverName(s)||'यो स्टेशन',l=level(s),w=warning(s),d=danger(s),flow=discharge(s),st=stage(s),t=measured(s);
  const bits=[`${stageNe(st)} — ${name}`];
  if(l!==null)bits.push(`हालको जलस्तर ${l.toFixed(2)} मि.`);
  if(w!==null)bits.push(`चेतावनी तह ${w.toFixed(2)} मि.`);
  if(d!==null)bits.push(`खतरा तह ${d.toFixed(2)} मि.`);
  if(flow!==null)bits.push(`बहाव ${flow.toFixed(1)}`);
  if(t)bits.push(`मापन ${formatTime(t)}${timeAgo(t)?` (${timeAgo(t)})`:''}`);
  if(st==='danger')bits.push('⚠️ जोखिम उच्च छ। नदी/खोला किनार र तल्लो क्षेत्रबाट टाढा रहनुहोस् र स्थानीय आधिकारिक निर्देशन पालना गर्नुहोस्।');
  else if(st==='warning')bits.push('⚠️ पानी चेतावनी तहमा वा माथि छ। सतर्क रहनुहोस् र सुरक्षित स्थानतर्फ जाने तयारी गर्नुहोस्।');
  else if(st==='watch')bits.push('पानीको अवस्था निगरानीमा राख्नुहोस्।');
  else if(st==='normal')bits.push('अहिले उपलब्ध आधिकारिक मापनअनुसार खतरा तह पार गरेको देखिँदैन।');
  else bits.push('ताजा आधिकारिक अवस्था स्पष्ट छैन, त्यसैले म अनुमान गर्दिनँ।');
  return bits.join(' • ');
}
function riskList(src){
  if(!src.current.length)return 'अहिले BIPAD/DHM को ताजा नदी मापन उपलब्ध छैन। ताजा आधिकारिक डेटा आएपछि मात्र जोखिम बताउँछु।';
  const rs=src.current.map(s=>({s,st:stage(s)})).filter(x=>x.st==='danger'||x.st==='warning'||x.st==='watch');
  if(!rs.length)return 'अहिले उपलब्ध ताजा आधिकारिक नदी मापनमा चेतावनी वा खतरा तहमा पुगेको स्टेशन भेटिएन।';
  const weight={danger:3,warning:2,watch:1};rs.sort((a,b)=>weight[b.st]-weight[a.st]);
  const top=rs.slice(0,8).map(x=>`${stageNe(x.st)} ${riverName(x.s)||'स्टेशन'}${level(x.s)!==null?` — ${level(x.s).toFixed(2)} मि.`:''}`).join('\n');
  return `अहिले जोखिम/निगरानीमा देखिएका नदी स्टेशनहरू:\n${top}${rs.length>8?`\n… थप ${rs.length-8} स्टेशन पनि निगरानीमा छन्।`:''}`;
}
function rainAnswer(src){
  const f=src.rain?.forecast;
  const place=($('#place')?.textContent||'छानिएको निगरानी क्षेत्र').replace(/^📍\s*/,'');
  if(!f)return '🌦️ ताजा वर्षा पूर्वानुमान अहिले उपलब्ध छैन। FloodSafe मा नेपालभित्र आफ्नो निगरानी स्थान छान्नुहोस् वा केही क्षणपछि फेरि सोध्नुहोस्।';
  const parts=[`🌦️ ${place}को पूर्वानुमान अनुसार`];
  if(f.wetNow)parts.push('अहिले वर्षा भइरहेको/देखिएको छ।');else parts.push('अहिले वर्षा देखिएको छैन।');
  const sv=f.start?.from??f.start;const ev=f.stop?.from??f.stop;
  if(sv){const sd=new Date(typeof sv==='number'&&sv<1e12?sv*1000:sv);const mins=Math.max(0,Math.ceil((sd.getTime()-Date.now())/60000));parts.push(`वर्षा सुरु हुने अनुमानित समय ${formatTime(sv)} हो${mins>0?` — करिब ${mins} मिनेटपछि`:''}।`)}
  else if(!f.wetNow)parts.push('हालको पूर्वानुमानमा नजिकै वर्षा सुरु हुने स्पष्ट समय छैन।');
  if(ev)parts.push(`वर्षा रोकिने अनुमानित समय ${formatTime(ev)} हो।`);else if(f.wetNow||sv)parts.push('रोकिने समय अहिले स्पष्ट छैन।');
  parts.push('यो मौसम पूर्वानुमान हो, पक्का स्थानीय मापन होइन।');
  return parts.join(' ');
}
function freshness(src){
  const vals=src.current.map(measured).filter(Boolean).map(v=>new Date(v)).filter(d=>!Number.isNaN(d.getTime())).sort((a,b)=>b-a);
  if(!vals.length)return 'अहिले ताजा नदी मापनको समय उपलब्ध छैन।';
  const d=vals[0];return `सबैभन्दा नयाँ उपलब्ध आधिकारिक नदी मापन ${formatTime(d)} को हो (${timeAgo(d)}).`;
}
function knowledge(q){
  if(has(q,'बाढी भनेको','बाढी के हो','flood vaneko','badi vaneko','what is flood'))return 'बाढी भनेको नदी, खोला वा वर्षाको पानी सामान्य सीमाभन्दा बढेर बस्ती, खेत, सडक वा अन्य भूभागमा फैलिने अवस्था हो।';
  if(has(q,'किन आउ','कारण','kina auxa','kina aau','cause'))return 'बाढीका मुख्य कारण धेरै/लगातार वर्षा, नदीको बहाव अचानक बढ्नु, पहिरोले नदी थुनिनु, हिमताल वा बाँध फुट्नु, निकास बन्द हुनु र कमजोर भू-व्यवस्थापन हुन्।';
  if(has(q,'warning ra danger','warning danger','चेतावनी तह','खतरा तह','danger level'))return 'चेतावनी तह पुगेपछि सतर्कता बढाउनुपर्छ। खतरा तह पुगे वा नाघेपछि जोखिम उच्च मानिन्छ र स्थानीय निकासी/सुरक्षा निर्देशन तुरुन्त पालना गर्नुपर्छ।';
  if(has(q,'गाडी','car','bike','drive','सवारी','road','सडक'))return '🚗 बाढीको पानीले ढाकेको सडकमा गाडी नचलाउनुहोस्। पानीको गहिराइ र सडकको अवस्था बाहिरबाट ठ्याक्कै थाहा हुँदैन र बहावले सवारी बगाउन सक्छ।';
  if(has(q,'बिजुली','electric','current','करन्ट'))return '⚡ बाढीको पानी नजिक बिजुलीको तार, पोल, इनभर्टर, जनरेटर वा भिजेको स्विच नछुनुहोस्। मुख्य स्विच सुरक्षित ठाउँबाट बन्द गर्न मिल्छ भने मात्र बन्द गर्नुहोस्।';
  if(has(q,'पिउने पानी','drinking water','खानेपानी','पानी पिउ'))return '🥤 बाढीपछि दूषित पानी नपिउनुहोस्। सुरक्षित बोतलको पानी वा आधिकारिक रूपमा सुरक्षित भनिएको पानी प्रयोग गर्नुहोस्; आवश्यक परे उमालेर प्रयोग गर्नुहोस्।';
  if(has(q,'बच्चा','बालबालिका','child','वृद्ध','elder','गर्भवती','disabled','अपाङ्ग'))return '👨‍👩‍👧 बालबालिका, वृद्ध, गर्भवती, बिरामी र अपाङ्ग व्यक्तिलाई पहिला सुरक्षित उच्च स्थानतिर सार्नुहोस् र परिवारको भेट्ने स्थान/सम्पर्क योजना तयार राख्नुहोस्।';
  if(has(q,'पशु','livestock','गाई','भैंसी','बाख्रा'))return '🐄 पशुचौपायालाई सम्भव भएसम्म बाढी आउनुअघि उचाइ र सुरक्षित खुला स्थानतिर सार्नुहोस्। मान्छेको ज्यान जोखिममा पारेर पशु बचाउन बगिरहेको पानीमा नछिर्नुहोस्।';
  if(has(q,'घर','घरमा','ghar','evacuate','निकासी','बच्ने','safe','सुरक्षा','के गर्ने','k garne','emergency'))return '🛟 बाढीको जोखिम हुँदा नदी/खोला किनारबाट टाढा जानुहोस्, तल्लो ठाउँ छोडेर उचाइतिर जानुहोस्, फोन/कागजात/औषधि/पानी लिएर निस्कनुहोस्, बगिरहेको पानी पार नगर्नुहोस् र स्थानीय प्रशासन/प्रहरी/उद्धार निकायको निर्देशन पालना गर्नुहोस्।';
  if(has(q,'पुल','bridge'))return '🌉 बाढीको बेला पुलमुनि, नदी किनार वा कटान भइरहेको पुलमा नबस्नुहोस्। पुल सुरक्षित देखिए पनि तीव्र बहावले संरचना कमजोर बनाएको हुन सक्छ।';
  if(has(q,'पहिरो','landslide'))return '⛰️ लगातार वर्षा वा बाढीसँगै पहिरोको जोखिम पनि बढ्न सक्छ। चिरा परेको जमिन, ढुंगा खस्नु, रुख ढल्नु वा असामान्य आवाज सुनिएमा ढलानबाट टाढा सुरक्षित स्थानतिर जानुहोस्।';
  return null;
}
function isFloodTopic(q){return has(q,'बाढी','बाडी','flood','badi','baadi','नदी','nadi','river','खोला','khola','जलस्तर','water level','warning','danger','चेतावनी','खतरा','वर्षा','rain','पानी','pani','मौसम','weather','पहिरो','landslide','सडक','road','evacuat','सुरक्षा','safe')}
function answer(question){
  const q=norm(question),src=source();
  if(!q)return 'कृपया बाढी, नदी/खोला वा वर्षाबारे प्रश्न सोध्नुहोस्।';
  if(!isFloodTopic(q))return 'म FloodSafe Nepal को SATHI AI हुँ। अहिले म बाढी, नदी/खोला, वर्षा, जलस्तर, चेतावनी र बाढी सुरक्षासम्बन्धी प्रश्नको नेपालीमा उत्तर दिन्छु।';
  const k=knowledge(q);if(k)return k;
  if(has(q,'कहिलेको','ताजा','latest','fresh','update time','updated'))return freshness(src);
  if(has(q,'वर्षा','rain','पानी','pani','मौसम','weather','कति बजे','kati baje','रोकिन','rokcha','parcha'))return rainAnswer(src);
  const st=findStation(q,src);if(st)return stationAnswer(st);
  if(has(q,'कुन','kun','कहाँ','kata','where','risk','जोखिम','warning','danger','चेतावनी','खतरा'))return riskList(src);
  return 'म बाढी/नदीबारे जवाफ दिन सक्छु। उदाहरण: “अहिले कुन खोलामा जोखिम छ?”, “कोशीको जलस्तर कति छ?”, “आज पानी कति बजे पर्छ?” वा “बाढी आए के गर्ने?”';
}

function inject(){
  if($('#sathiFloodBtn'))return;
  const style=document.createElement('style');style.id='sathiFloodStyle';style.textContent=`
#sathiFloodBtn{appearance:none;border:0;cursor:pointer;display:inline-flex;align-items:center;gap:7px;padding:10px 13px;border-radius:999px;font:800 13px/1.1 system-ui,-apple-system,Segoe UI,sans-serif;background:#0b6ff4;color:#fff;box-shadow:0 6px 18px rgba(11,111,244,.25);white-space:nowrap}
#sathiFloodBtn .sathiDot{width:8px;height:8px;border-radius:50%;background:#67e8a5;box-shadow:0 0 0 3px rgba(103,232,165,.2)}
#sathiFloodOverlay{position:fixed;inset:0;background:rgba(4,18,34,.32);backdrop-filter:blur(2px);z-index:2147483000;display:none}
#sathiFloodOverlay.open{display:block}
#sathiFloodPanel{position:fixed;right:14px;bottom:14px;width:min(430px,calc(100vw - 20px));height:min(680px,82dvh);max-height:calc(100dvh - 20px);background:#fff;border:1px solid rgba(15,69,120,.14);border-radius:24px;box-shadow:0 24px 70px rgba(3,27,54,.28);z-index:2147483001;display:none;overflow:hidden;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#102538}
#sathiFloodPanel.open{display:flex;flex-direction:column}
.sathiHead{display:flex;align-items:center;gap:10px;padding:13px 14px;background:linear-gradient(135deg,#eaf6ff,#f8fcff);border-bottom:1px solid #dbeaf5}.sathiAvatar{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:#0b6ff4;color:#fff;font-size:21px}.sathiHeadText{min-width:0;flex:1}.sathiHeadText b{display:block;font-size:15px}.sathiHeadText small{display:block;color:#587084;font-size:11px;margin-top:2px}.sathiIconBtn{border:0;background:#edf5fb;border-radius:12px;width:38px;height:38px;cursor:pointer;font-size:17px}
#sathiFloodMsgs{flex:1;overflow:auto;padding:14px;background:#f7fbfe;overscroll-behavior:contain}.sathiMsg{max-width:88%;padding:10px 12px;border-radius:16px;margin:0 0 10px;white-space:pre-wrap;line-height:1.45;font-size:14px}.sathiMsg.ai{background:#fff;border:1px solid #e1edf5;border-bottom-left-radius:5px}.sathiMsg.user{margin-left:auto;background:#0b6ff4;color:#fff;border-bottom-right-radius:5px}.sathiMsg.status{margin-inline:auto;background:#eaf6ff;color:#31536f;font-size:12px;text-align:center}
#sathiQuick{display:flex;gap:7px;overflow:auto;padding:8px 11px;background:#fff;border-top:1px solid #edf3f7}#sathiQuick button{border:1px solid #dceaf4;background:#f6fbff;color:#1d4869;border-radius:999px;padding:8px 10px;white-space:nowrap;font-size:12px;cursor:pointer}
#sathiComposer{display:flex;align-items:flex-end;gap:8px;padding:10px;background:#fff;border-top:1px solid #e3edf4;padding-bottom:max(10px,env(safe-area-inset-bottom))}#sathiInput{flex:1;resize:none;min-height:42px;max-height:120px;border:1px solid #cedfe9;border-radius:14px;padding:10px 11px;font:16px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;outline:none;background:#fbfdff;color:#102538}#sathiInput:focus{border-color:#0b6ff4;box-shadow:0 0 0 3px rgba(11,111,244,.1)}.sathiSend,.sathiMic{border:0;width:42px;height:42px;border-radius:14px;cursor:pointer;font-size:17px}.sathiSend{background:#0b6ff4;color:#fff}.sathiMic{background:#eaf6ff;color:#0b6ff4}.sathiMic.on{background:#ffe8e8;color:#c62828}
@media(max-width:620px){header.top{gap:8px;flex-wrap:wrap}.brand{flex:1 1 auto}#sathiFloodBtn{order:3;margin-left:auto;padding:9px 11px;font-size:12px}#sathiFloodPanel{left:5px;right:5px;bottom:5px;width:auto;height:min(760px,92dvh);border-radius:22px}.sathiHead{padding-top:max(12px,env(safe-area-inset-top))}}
`;document.head.appendChild(style);
  const header=$('header.top')||$('.top');if(!header)return;
  const btn=document.createElement('button');btn.id='sathiFloodBtn';btn.type='button';btn.innerHTML='<span>🤖</span><span>तपाईंको SATHI AI</span><span class="sathiDot" aria-hidden="true"></span>';btn.setAttribute('aria-label','FloodSafe SATHI AI खोल्नुहोस्');
  const lang=$('#langBtn');if(lang)header.insertBefore(btn,lang);else header.appendChild(btn);
  const overlay=document.createElement('div');overlay.id='sathiFloodOverlay';document.body.appendChild(overlay);
  const panel=document.createElement('section');panel.id='sathiFloodPanel';panel.setAttribute('aria-hidden','true');panel.innerHTML=`<div class="sathiHead"><div class="sathiAvatar">🤖</div><div class="sathiHeadText"><b>तपाईंको SATHI AI</b><small>BIPAD/DHM नदी डेटा • FloodSafe वर्षा पूर्वानुमान</small></div><button class="sathiIconBtn" id="sathiClose" type="button" aria-label="बन्द">×</button></div><div id="sathiFloodMsgs" aria-live="polite"></div><div id="sathiQuick"><button data-q="अहिले कुन खोलामा बाढीको जोखिम छ?">अहिले कहाँ जोखिम?</button><button data-q="आज पानी कति बजे पर्छ र कहिले रोकिन्छ?">आज पानी कहिले?</button><button data-q="बाढी आए के गर्ने?">बाढी आए के गर्ने?</button></div><div id="sathiComposer"><button class="sathiMic" id="sathiMic" type="button" aria-label="आवाजबाट सोध्नुहोस्">🎤</button><textarea id="sathiInput" rows="1" placeholder="बाढी, नदी/खोला वा वर्षाबारे सोध्नुहोस्…" enterkeyhint="send"></textarea><button class="sathiSend" id="sathiSend" type="button" aria-label="पठाउनुहोस्">➤</button></div>`;document.body.appendChild(panel);
  const msgs=$('#sathiFloodMsgs'),input=$('#sathiInput');let rec=null;
  const add=(text,type='ai')=>{const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight};
  const open=()=>{overlay.classList.add('open');panel.classList.add('open');panel.setAttribute('aria-hidden','false');if(!msgs.children.length)add('नमस्ते 👋 म FloodSafe Nepal को SATHI AI हुँ। बाढी, नदी/खोला, जलस्तर, चेतावनी, वर्षा र सुरक्षा बारे नेपालीमा सोध्नुहोस्।')};
  const close=()=>{overlay.classList.remove('open');panel.classList.remove('open');panel.setAttribute('aria-hidden','true');input.blur()};
  const resize=()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px'};
  const ask=()=>{const q=input.value.trim();if(!q)return;add(q,'user');input.value='';resize();setTimeout(()=>add(answer(q),'ai'),45)};
  btn.addEventListener('click',open);$('#sathiClose').addEventListener('click',close);overlay.addEventListener('click',close);$('#sathiSend').addEventListener('click',ask);input.addEventListener('input',resize);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask()}});$('#sathiQuick').addEventListener('click',e=>{const b=e.target.closest('button[data-q]');if(!b)return;open();input.value=b.dataset.q;ask()});
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;$('#sathiMic').addEventListener('click',()=>{if(!SR){add('यो ब्राउजरमा voice recognition उपलब्ध छैन। टाइप गरेर सोध्न सक्नुहुन्छ।','status');return}try{rec?.abort?.()}catch{}rec=new SR();rec.lang='ne-NP';rec.interimResults=true;rec.continuous=false;const mic=$('#sathiMic');mic.classList.add('on');add('सुन्दैछु…','status');rec.onresult=e=>{let text='';for(let i=e.resultIndex;i<e.results.length;i++)text+=e.results[i][0].transcript;input.value=text;resize();if(e.results[e.results.length-1].isFinal)setTimeout(ask,100)};rec.onerror=()=>add('आवाज बुझिएन। फेरि प्रयास गर्नुहोस्।','status');rec.onend=()=>mic.classList.remove('on');try{rec.start()}catch{}});
  if(window.visualViewport){const adjust=()=>{if(!panel.classList.contains('open'))return;const vv=visualViewport;const keyboard=Math.max(0,innerHeight-vv.height-vv.offsetTop);panel.style.bottom=(keyboard+5)+'px';panel.style.maxHeight=Math.max(320,vv.height-10)+'px'};visualViewport.addEventListener('resize',adjust);visualViewport.addEventListener('scroll',adjust);panel.addEventListener('transitionend',adjust)}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',inject,{once:true});else inject();
window.SathiFloodAI={answer,version:'1.0-live-additive'};
})();
