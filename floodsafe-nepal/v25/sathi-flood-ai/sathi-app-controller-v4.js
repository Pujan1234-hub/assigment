(()=>{
'use strict';
if(window.__SATHI_APP_CONTROLLER_V4__)return;
window.__SATHI_APP_CONTROLLER_V4__=true;

const norm=s=>String(s||'').toLowerCase().normalize('NFKC')
  .replace(/[?!.:,;()[\]{}"'`।]/g,' ').replace(/\s+/g,' ').trim();
const has=(q,...xs)=>xs.some(x=>q.includes(x));
const WEATHER_WORDS=['weather','mausam','मौसम','temperature','temp','tapkram','तापक्रम','rain','pani','पानी','वर्षा','barsa','barsha','parcha','parxa','पर्छ','रोकिन','rokcha','humidity','आर्द्रता','wind','hawa','हावा','gust','cloud','badal','बादल','fog','kuhiro','कुहिरो','visibility','दृश्यता','uv','sunrise','sunset','सूर्योदय','सूर्यास्त','thunder','चट्याङ','snow','हिउँ','forecast','पूर्वानुमान','bholi','भोलि','aaja','आज','week','हप्ता','umbrella','छाता'];

const PLACES=[
['Taplejung','ताप्लेजुङ'],['Panchthar','पाँचथर'],['Ilam','इलाम'],['Jhapa','झापा'],['Morang','मोरङ'],['Sunsari','सुनसरी'],['Dhankuta','धनकुटा'],['Terhathum','तेह्रथुम'],['Sankhuwasabha','संखुवासभा'],['Bhojpur','भोजपुर'],['Solukhumbu','सोलुखुम्बु'],['Okhaldhunga','ओखलढुङ्गा'],['Khotang','खोटाङ'],['Udayapur','उदयपुर'],['Saptari','सप्तरी'],['Siraha','सिराहा'],['Dhanusha','धनुषा'],['Mahottari','महोत्तरी'],['Sarlahi','सर्लाही'],['Rautahat','रौतहट'],['Bara','बारा'],['Parsa','पर्सा'],['Dolakha','दोलखा'],['Sindhupalchok','सिन्धुपाल्चोक'],['Rasuwa','रसुवा'],['Dhading','धादिङ'],['Nuwakot','नुवाकोट'],['Kathmandu','काठमाडौं'],['Bhaktapur','भक्तपुर'],['Lalitpur','ललितपुर'],['Kavrepalanchok','काभ्रेपलाञ्चोक'],['Ramechhap','रामेछाप'],['Sindhuli','सिन्धुली'],['Makwanpur','मकवानपुर'],['Chitwan','चितवन'],['Gorkha','गोरखा'],['Manang','मनाङ'],['Mustang','मुस्ताङ'],['Myagdi','म्याग्दी'],['Kaski','कास्की'],['Lamjung','लमजुङ'],['Tanahun','तनहुँ'],['Nawalpur','नवलपुर'],['Syangja','स्याङ्जा'],['Parbat','पर्वत'],['Baglung','बागलुङ'],['Rupandehi','रुपन्देही'],['Kapilvastu','कपिलवस्तु'],['Parasi','परासी'],['Palpa','पाल्पा'],['Arghakhanchi','अर्घाखाँची'],['Gulmi','गुल्मी'],['Rukum East','रुकुम पूर्व'],['Rolpa','रोल्पा'],['Pyuthan','प्युठान'],['Dang','दाङ'],['Banke','बाँके'],['Bardiya','बर्दिया'],['Dolpa','डोल्पा'],['Mugu','मुगु'],['Humla','हुम्ला'],['Jumla','जुम्ला'],['Kalikot','कालिकोट'],['Dailekh','दैलेख'],['Jajarkot','जाजरकोट'],['Rukum West','रुकुम पश्चिम'],['Salyan','सल्यान'],['Surkhet','सुर्खेत'],['Bajura','बाजुरा'],['Bajhang','बझाङ'],['Darchula','दार्चुला'],['Baitadi','बैतडी'],['Dadeldhura','डडेलधुरा'],['Doti','डोटी'],['Achham','अछाम'],['Kailali','कैलाली'],['Kanchanpur','कञ्चनपुर'],
['Pokhara','पोखरा'],['Biratnagar','विराटनगर'],['Bharatpur','भरतपुर'],['Janakpur','जनकपुर'],['Hetauda','हेटौंडा'],['Dharan','धरान'],['Butwal','बुटवल'],['Nepalgunj','नेपालगन्ज'],['Dhangadhi','धनगढी'],['Itahari','इटहरी'],['Birtamod','बिर्तामोड'],['Damak','दमक']
];
const EXTRA_ALIASES={
  Kathmandu:['काठमाण्डौ','काठमाण्डौं','काठमाडौँ','काठमांडू','काठमांडौ','ktm','kathmandau','kathmandu'],
  Jhapa:['झापा','jhapa','japa'],
  Pokhara:['पोखरा','pokhara','pokhra'],
  Lalitpur:['ललितपुर','patan','पाटन'],
  Bhaktapur:['भक्तपुर','bhaktapur','bkt'],
  Chitwan:['चितवन','chitwan','chitawan'],
  Morang:['मोरङ','morang'],
  Sunsari:['सुनसरी','sunsari'],
  Kaski:['कास्की','kaski'],
  Rupandehi:['रुपन्देही','rupandehi'],
  Banke:['बाँके','banke'],
  Kailali:['कैलाली','kailali'],
  Kanchanpur:['कञ्चनपुर','kanchanpur']
};
const suffixes=['बाट','देखि','सम्म','तिर','तिरको','मा','को','का','की','माै','जिल्ला','district'];
const trimSuffix=s=>{let x=String(s||'').trim();for(const suf of suffixes){if(x.endsWith(suf)&&x.length>suf.length+2)x=x.slice(0,-suf.length)}return x};
function edit(a,b){a=[...String(a||'')];b=[...String(b||'')];const n=b.length,row=Array.from({length:n+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let prev=row[0];row[0]=i;for(let j=1;j<=n;j++){const old=row[j];row[j]=Math.min(row[j]+1,row[j-1]+1,prev+(a[i-1]===b[j-1]?0:1));prev=old}}return row[n]}
function placeIn(raw){
  const q=norm(raw),tokens=q.split(' ').map(trimSuffix).filter(Boolean);let best=null,bestScore=Infinity;
  for(const [en,ne] of PLACES){
    const aliases=[en.toLowerCase(),ne,...(EXTRA_ALIASES[en]||[])].map(norm);
    for(const a of aliases){
      if(!a)continue;
      if(q.includes(a))return en;
      if(a.includes(' '))continue;
      for(const t of tokens){
        if(t.length<4||a.length<4)continue;
        const d=edit(t,a),allow=Math.max(1,Math.floor(Math.max(t.length,a.length)*.22));
        if(d<=allow&&d<bestScore){best=en;bestScore=d}
      }
    }
  }
  return best;
}
function rewritePlace(raw){const p=placeIn(raw);return p?`${raw} ${p}`:raw}

function appAnswer(raw){
  const q=norm(raw);
  const aboutApp=has(q,'यो app','yo app','app le','appले','floodsafe','sathi ai','साथी ai','के गर्छ','k garxa','k garcha','feature','काम के','काम के हो','के के गर्छ','ke ke garxa','what can','help me');
  if(aboutApp&&has(q,'के गर्छ','k garxa','k garcha','के के','feature','काम','what can','help me')){
    return 'FloodSafe Nepal को SATHI ले app भित्रका यी कामबारे उत्तर दिन्छ:\n• नेपालका ७७ जिल्लाको मौसम, तापक्रम, महसुस हुने तापक्रम, आर्द्रता, हावा/झोँका, बादल, कुहिरो/visibility, UV, सूर्योदय/सूर्यास्त।\n• आज/भोलि/७-दिने forecast, वर्षा कति बजे सुरु हुन सक्छ, कहिले रोकिन सक्छ, कति सम्भावना छ र छाता चाहिन्छ कि छैन।\n• BIPAD/DHM का ताजा official नदी स्टेशन, जलस्तर, चेतावनी तह, खतरा तह, बहाव र मापन समय।\n• अहिले कुन नदी/खोलामा warning/danger/watch छ, नजिकको station र स्थानीय flood risk।\n• बाढी बेला के गर्ने/के नगर्ने, सडक, पुल, बिजुली, पिउने पानी, बालबालिका/वृद्ध र evacuation सुरक्षा।\n• वर्षा/flood notifications, GPS/निगरानी location, नदी नक्सा, नेपाल समाचार र मानवीय असरको status।\n• “Ye Sathi” voice बाट यही FloodSafe सम्बन्धी प्रश्न सोध्न सकिन्छ।\nम unrelated general-knowledge assistant होइन; FloodSafe Nepal ले गर्ने कामभित्रको प्रश्नमा केन्द्रित छु।';
  }
  if(has(q,'real time','realtime','रियल टाइम','रियलटाइम','live data','लाइभ डेटा','source','स्रोत','data kata','डेटा कहाँ')){
    return 'FloodSafe मा “live/realtime” शब्द दुई किसिमले प्रयोग हुन्छ। नदी/खोला र उपलब्ध वर्षा स्टेशनको observation BIPAD/DHM official measurement हो, त्यसमा म measurement time देखाउँछु। तापक्रम र rain start/stop चाहिँ forecast/model data हो; त्यसलाई ground sensor ले यही सेकेन्डमा नापेको भनेर कहिल्यै भन्नु हुँदैन। SATHI ले observed data र forecast छुट्टाछुट्टै भनेर बताउनुपर्छ।';
  }
  if(has(q,'map','नक्सा','station click','स्टेशन थिच'))return 'नदी नक्सामा official station थिच्दा station नाम, हालको जलस्तर, warning/danger threshold, status र उपलब्ध measurement time देखिन्छ। Risk colour/label ताजा official reading बाट आउनुपर्छ; पुरानो reading लाई live भनेर देखाउनु हुँदैन।';
  if(has(q,'notification','सूचना','alert','अलर्ट','चेतावनी पठ','rain alert','वर्षा सूचना'))return 'FloodSafe notification दुई कामका लागि हो: official flood/river खतरा देखिएमा जोखिम सूचना, र छानिएको/GPS क्षेत्रमा forecast अनुसार वर्षा नजिकिँदा rain alert। Notification ले source र समय स्पष्ट देखाउनुपर्छ; पुरानो data मा नयाँ खतरा बनाउनु हुँदैन।';
  if(has(q,'human status','मानवीय असर','मृत्यु','missing','सम्पर्कविहीन','rescued','उद्धार'))return 'मानवीय असर card नयाँ पुष्टि भएको disaster event हुँदा मात्र देखिन्छ। Event सुरु भएको मितिबाट १३ दिनसम्म मृत्यु, सम्पर्कविहीन र उद्धार/सुरक्षित भेटिएका verified totals देखाइन्छ; १३ दिनपछि card आफैं hide हुन्छ। नयाँ verified event आएमा फेरि सक्रिय हुन्छ।';
  if(has(q,'news','समाचार'))return 'नेपाल समाचार section ले flood/disaster सम्बन्धी ताजा feed देखाउँछ। SATHI ले समाचारलाई river gauge measurement जस्तो नबनाई अलग source/status भनेर बुझाउनुपर्छ।';
  if(has(q,'gps','location','स्थान','निगरानी क्षेत्र'))return 'GPS/निगरानी location weather र local risk का लागि प्रयोग हुन्छ। नेपाल बाहिर हुँदा FloodSafe ले त्यहाँको मौसम test/forecast देखाउन सक्छ, तर Nepal flood monitoring चाहिँ नेपालका BIPAD/DHM stationsमै सीमित हुन्छ।';
  if(has(q,'voice','आवाज','ye sathi','hey sathi','ए साथी','माइक'))return 'Voice mode मा माइक थिचेर प्रश्न सोध्न सकिन्छ। Android APK मा “Ye Sathi” background wake user ले सक्रिय गर्न सक्छ; Force Stop गरेपछि Android ले service बन्द गर्ने भएकाले app फेरि खोलेपछि मात्र wake फर्किन्छ।';
  if(has(q,'warning','danger','चेतावनी तह','खतरा तह')&&has(q,'मतलब','के हो','farak','फरक'))return 'Warning तह भनेको सतर्कता बढाउने threshold हो। Danger तह पुगे/नाघेपछि जोखिम उच्च मानिन्छ। SATHI ले station को वास्तविक current level सँग threshold तुलना गरेर मात्र status भन्नुपर्छ।';
  return null;
}

function upgradeGreeting(){
  const m=document.getElementById('sathiFloodMsgs');if(!m)return;
  const first=m.querySelector('.sathiMsg.ai');if(!first)return;
  if(/FloodSafe Nepal को SATHI AI/.test(first.textContent||''))first.textContent='नमस्ते 👋 म FloodSafe Nepal को SATHI AI हुँ। मौसम, तापक्रम, वर्षा सुरु/रोकिने समय, नदी/खोला जलस्तर, warning/danger, नक्सा, alerts, सुरक्षा र app ले गर्ने कामबारे नेपालीमा सोध्नुहोस्।';
}

function installPanelGeometry(){
  if(document.getElementById('sathiV4LayoutStyle'))return;
  const st=document.createElement('style');st.id='sathiV4LayoutStyle';st.textContent=`
#sathiFloodPanel{box-sizing:border-box!important}
#sathiFloodMsgs{min-height:0!important;overscroll-behavior:contain!important}
#sathiQuick,#sathiNativeStatus,#sathiComposer{flex:0 0 auto!important}
#sathiComposer{position:relative!important;z-index:5!important;background:#fff!important;padding-bottom:max(12px,env(safe-area-inset-bottom))!important}
#sathiInput{box-sizing:border-box!important;min-width:0!important;max-height:104px!important}
@media(max-width:620px){#sathiFloodPanel.open{left:6px!important;right:6px!important;width:auto!important;max-height:none!important;border-radius:20px!important}}
`;document.head.appendChild(st);
}
function fitPanel(){
  const p=document.getElementById('sathiFloodPanel');if(!p||!p.classList.contains('open'))return;
  const vv=window.visualViewport;
  const top=Math.max(4,Math.round(vv?.offsetTop||0)+6),h=Math.max(320,Math.round(vv?.height||innerHeight)-12);
  p.style.setProperty('top',top+'px','important');
  p.style.setProperty('bottom','auto','important');
  p.style.setProperty('height',h+'px','important');
  p.style.setProperty('max-height',h+'px','important');
  const msgs=document.getElementById('sathiFloodMsgs');if(msgs)requestAnimationFrame(()=>{msgs.scrollTop=msgs.scrollHeight});
}
function installViewportFix(){
  installPanelGeometry();
  const go=()=>requestAnimationFrame(fitPanel);
  window.visualViewport?.addEventListener('resize',go,{passive:true});
  window.visualViewport?.addEventListener('scroll',go,{passive:true});
  addEventListener('resize',go,{passive:true});
  document.addEventListener('focusin',e=>{if(e.target?.id==='sathiInput')setTimeout(go,40)});
  const p=document.getElementById('sathiFloodPanel');if(p)new MutationObserver(go).observe(p,{attributes:true,attributeFilter:['class']});
  go();
}

let baseAsync=null,baseSync=null,busy=false,micWakeWasOn=false,micSession=false;
const add=(text,type='ai')=>{const m=document.getElementById('sathiFloodMsgs');if(!m)return;const d=document.createElement('div');d.className=`sathiMsg ${type}`;d.textContent=String(text||'');m.appendChild(d);m.scrollTop=m.scrollHeight};
const status=text=>{const e=document.getElementById('sathiNativeStatus');if(e)e.textContent=text};
const openPanel=()=>{document.getElementById('sathiFloodOverlay')?.classList.add('open');const p=document.getElementById('sathiFloodPanel');if(p){p.classList.add('open');p.setAttribute('aria-hidden','false');setTimeout(fitPanel,0)}};
function cleanForVoice(s){return String(s||'').replace(/स्रोत:[^\n]+/g,'').replace(/[•|]/g,', ').replace(/\n+/g,'. ').replace(/\s+/g,' ').trim()}
function speak(s){try{window.SathiNative?.speak?.(cleanForVoice(s))}catch{}}
async function smart(raw){
  const direct=appAnswer(raw);if(direct)return direct;
  const rewritten=WEATHER_WORDS.some(x=>norm(raw).includes(x))?rewritePlace(raw):raw;
  if(baseAsync){const r=await baseAsync(rewritten);const p=placeIn(raw);if(p&&/GPS स्थान नेपाल बाहिर|current gps.*outside nepal/i.test(String(r||'')))return baseAsync(`${p} मौसम तापक्रम आज`);return r}
  if(baseSync)return baseSync(rewritten);
  return 'SATHI अहिले तयार हुँदैछ। केही क्षणपछि फेरि सोध्नुहोस्।';
}
async function run(q,voice=false){
  q=String(q||'').trim();if(!q||busy)return;busy=true;openPanel();add(q,'user');const i=document.getElementById('sathiInput');if(i){i.value='';i.style.height='auto'}status('SATHI ले ताजा app data जाँच्दैछ…');
  try{const r=await smart(q);add(r,'ai');status('✅ उत्तर तयार भयो।');if(voice)speak(r)}catch{add('ताजा data जाँच्दा समस्या भयो। केही क्षणपछि फेरि प्रयास गर्नुहोस्।','status');status('⚠️ अहिले data जाँच्न सकिएन।')}finally{busy=false;setTimeout(fitPanel,0)}
}
function bindInputs(){
  const oi=document.getElementById('sathiInput'),os=document.getElementById('sathiSend');if(!oi||!os){setTimeout(bindInputs,120);return}
  if(document.getElementById('sathiFloodPanel')?.dataset.sathiV4==='1')return;
  const i=oi.cloneNode(true),s=os.cloneNode(true);oi.replaceWith(i);os.replaceWith(s);
  i.placeholder='मौसम, वर्षा, नदी/खोला, warning, नक्सा वा FloodSafe बारे सोध्नुहोस्…';
  const resize=()=>{i.style.height='auto';i.style.height=Math.min(i.scrollHeight,104)+'px';fitPanel()};
  s.addEventListener('click',()=>run(i.value));i.addEventListener('input',resize);i.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();run(i.value)}});
  document.getElementById('sathiFloodPanel')?.setAttribute('data-sathi-v4','1');
  const small=document.querySelector('#sathiFloodPanel .sathiHeadText small');if(small)small.textContent='नेपाल मौसम • official नदी/वर्षा data • FloodSafe assistant';
  const msgs=document.getElementById('sathiFloodMsgs');if(msgs&&!msgs.dataset.v4hello){msgs.dataset.v4hello='1';}
  installViewportFix();
}
function install(){
  const ai=window.SathiFloodAI;if(!ai){setTimeout(install,120);return}
  baseAsync=typeof ai.answerAsync==='function'?ai.answerAsync.bind(ai):null;
  baseSync=typeof ai.answer==='function'?ai.answer.bind(ai):null;
  ai.answer=q=>appAnswer(q)||(baseSync?baseSync(rewritePlace(q)):'SATHI तयार हुँदैछ।');
  ai.answerAsync=smart;ai.version='4.0-app-controller';ai.run=run;
  setTimeout(bindInputs,0);
}

document.addEventListener('click',e=>{
  if(e.target?.closest?.('#sathiFloodBtn'))setTimeout(upgradeGreeting,0);
  const b=e.target?.closest?.('#sathiQuick button[data-q]');if(!b)return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();run(b.dataset.q);
},true);
window.addEventListener('sathi-native-transcript',e=>{
  const q=String(e.detail?.text||'').trim();if(!q)return;
  e.stopImmediatePropagation();status(e.detail?.wake?'🤖 “Ye Sathi” बाट प्रश्न सुनियो।':'✅ आवाज बुझियो।');run(q,true);
},true);
document.addEventListener('click',e=>{
  const m=e.target?.closest?.('#sathiMic');if(!m||!window.SathiNative)return;
  e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();m.classList.add('on');status('🎤 सुन्दैछु…');
  try{micWakeWasOn=Boolean(window.SathiNative.isAlwaysOn?.());micSession=true;window.SathiNative.startVoiceInput()}catch{micSession=false;m.classList.remove('on');status('माइक सुरु हुन सकेन।')}
},true);
window.addEventListener('sathi-native-state',e=>{
  if(e.detail?.message)status(String(e.detail.message));
  if(e.detail?.kind==='mic'&&!e.detail?.active){
    document.getElementById('sathiMic')?.classList.remove('on');
    if(micSession&&!micWakeWasOn){try{window.SathiNative?.setAlwaysOn?.(false)}catch{}}
    micSession=false;
  }
},true);

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(install,0),{once:true});else setTimeout(install,0);
})();
