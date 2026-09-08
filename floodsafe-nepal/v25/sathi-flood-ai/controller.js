(()=>{
'use strict';
const $=id=>document.getElementById(id);
let fsWin=null,recognition=null,wakeRecognition=null,wakeEnabled=false,speaking=false;
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;

function addMessage(text,type='ai'){
  const el=document.createElement('div');el.className=`msg ${type}`;el.textContent=String(text||'');$('sathiMessages').appendChild(el);$('sathiMessages').scrollTop=$('sathiMessages').scrollHeight;return el;
}
function setTyping(text=''){$('sathiTyping').textContent=text}
function openPanel(focus=false){$('sathiPanel').classList.add('open');$('sathiPanel').setAttribute('aria-hidden','false');if(focus)setTimeout(()=>$('sathiInput').focus(),80)}
function closePanel(){$('sathiPanel').classList.remove('open');$('sathiPanel').setAttribute('aria-hidden','true');$('sathiInput').blur()}
function answer(q){
  const text=String(q||'').trim();if(!text)return;
  addMessage(text,'user');$('sathiInput').value='';resizeInput();setTyping('SATHI ले FloodSafe को ताजा डेटा पढ्दैछ…');
  setTimeout(()=>{
    let reply;
    try{reply=window.SathiFloodAIEngine.answer(text,fsWin)}catch(e){reply='माफ गर्नुहोस्, FloodSafe को ताजा डेटा पढ्न समस्या भयो। केही क्षणपछि फेरि प्रयास गर्नुहोस्।'}
    setTyping('');addMessage(reply,'ai');speakNepali(reply);
  },60);
}
function speakNepali(text){
  if(!('speechSynthesis'in window)||!text)return;
  try{
    speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(String(text).replace(/[🔴🟠🟡🟢🌊🌧️🌤️⚠️🛟🚗🏠]/g,''));u.lang='ne-NP';u.rate=.95;u.pitch=1;u.onstart=()=>speaking=true;u.onend=u.onerror=()=>speaking=false;speechSynthesis.speak(u)
  }catch{}
}
function resizeInput(){const t=$('sathiInput');t.style.height='auto';t.style.height=Math.min(t.scrollHeight,120)+'px'}
function startOneShotVoice(){
  if(!SpeechRecognition){addMessage('यो ब्राउजरमा voice recognition उपलब्ध छैन। टाइप गरेर सोध्न सक्नुहुन्छ।','status');return}
  recognition?.abort?.();recognition=new SpeechRecognition();recognition.lang='ne-NP';recognition.interimResults=true;recognition.continuous=false;
  const btn=$('sathiListen');btn.classList.add('listening');setTyping('सुन्दैछु…');
  recognition.onresult=e=>{let final='',interim='';for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal)final+=t;else interim+=t}$('sathiInput').value=final||interim;resizeInput();setTyping(final?'बुझेँ…':'सुन्दैछु…');if(final)setTimeout(()=>answer(final),100)};
  recognition.onerror=()=>setTyping('आवाज बुझिएन। फेरि प्रयास गर्नुहोस्।');recognition.onend=()=>{btn.classList.remove('listening');if($('sathiTyping').textContent==='सुन्दैछु…')setTyping('')};
  try{recognition.start()}catch{}
}
function wakeMatch(text){return /(^|\s)(ye|hey|ए|ये)\s+sathi\b|(^|\s)(ए|ये)\s*साथी\b/i.test(String(text||''))}
function startWake(){
  if(!SpeechRecognition){addMessage('यो ब्राउजरमा “Ye Sathi” wake phrase support छैन। Android native versionमा छुट्टै wake service चाहिन्छ।','status');return}
  stopWake();wakeEnabled=true;wakeRecognition=new SpeechRecognition();wakeRecognition.lang='ne-NP';wakeRecognition.interimResults=true;wakeRecognition.continuous=true;
  wakeRecognition.onresult=e=>{for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(wakeMatch(t)){openPanel();setTyping('👂 Ye Sathi — सुन्दैछु…');try{wakeRecognition.stop()}catch{};setTimeout(startOneShotVoice,180);break}}};
  wakeRecognition.onend=()=>{if(wakeEnabled&&!speaking)setTimeout(startWake,600)};wakeRecognition.onerror=()=>{if(wakeEnabled)setTimeout(startWake,1200)};
  try{wakeRecognition.start();$('wakeBtn').textContent='🎙️ Ye Sathi ON';$('wakeBtn').classList.add('on')}catch{}
}
function stopWake(){wakeEnabled=false;try{wakeRecognition?.abort?.()}catch{};wakeRecognition=null;if($('wakeBtn')){$('wakeBtn').textContent='🎙️ Ye Sathi';$('wakeBtn').classList.remove('on')}}
function bindFrame(){
  const f=$('fsFrame');f.addEventListener('load',()=>{
    try{fsWin=f.contentWindow;void fsWin.location.href;setTyping('');$('sathiSource').textContent='FloodSafe V25 • read-only data';}
    catch{$('sathiSource').textContent='FloodSafe data access unavailable';addMessage('FloodSafe को runtime data पढ्न सकिएन।','status')}
  });
}
function keyboardGuard(){
  const vv=window.visualViewport;if(!vv)return;const update=()=>{const open=window.innerHeight-vv.height>140;document.body.classList.toggle('keyboard-open',open);if(open&&$('sathiPanel').classList.contains('open'))setTimeout(()=>$('sathiInput').scrollIntoView({block:'nearest'}),40)};vv.addEventListener('resize',update);vv.addEventListener('scroll',update);update();
}
function boot(){
  bindFrame();keyboardGuard();
  $('sathiFab').onclick=()=>openPanel(true);$('sathiClose').onclick=closePanel;$('sathiSend').onclick=()=>answer($('sathiInput').value);$('sathiListen').onclick=startOneShotVoice;
  $('wakeBtn').onclick=()=>wakeEnabled?stopWake():startWake();
  $('sathiInput').addEventListener('input',resizeInput);$('sathiInput').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();answer(e.currentTarget.value)}});
  document.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{openPanel();answer(b.dataset.q)});
  addMessage('नमस्ते 👋 म FloodSafe Nepal को SATHI हुँ। बाढी, नदी/खोला, जलस्तर, चेतावनी, वर्षा र सुरक्षाबारे नेपालीमा सोध्नुहोस्।','ai');
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
