(()=>{
'use strict';
const $=id=>document.getElementById(id);
let ctx=null, audioEnabled=localStorage.getItem('fs23-audio-enabled')==='1', baseline=null, scanTimer=null;

function addCss(){
 if(document.getElementById('fs23-hotfix-css'))return;
 const s=document.createElement('style');s.id='fs23-hotfix-css';s.textContent=`
/* V23 mobile map controls: keep zoom away from the map title/buttons */
.leaflet-top.leaflet-left{top:auto!important;bottom:58px!important;left:8px!important}
.leaflet-control-zoom{margin:0!important;box-shadow:0 6px 18px #0008!important}
.fs23roadTools{margin-top:8px;border:1px solid #604238;border-radius:11px;padding:9px;background:#15100e}
.fs23roadTools b{display:block;font-size:11px;margin-bottom:4px}.fs23roadTools small{display:block;color:#c7b8b0;line-height:1.45;margin-top:5px}
.fs23roadBtns{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.fs23roadBtns button{border:1px solid #765044;background:#261713;color:#fff;border-radius:9px;padding:8px 9px;font-weight:850;cursor:pointer}.fs23roadBtns button:first-child{background:#3b5f2a;border-color:#72a653}
.fs23impactFallback{color:#f5d37a!important;font-weight:700}.fs23soundOn{background:#176b4d!important;border-color:#54dca8!important}
@media(max-width:900px){.leaflet-top.leaflet-left{bottom:62px!important}.mapBadge{max-width:58%!important}.mapBtns{max-width:42%!important}.mapTop{align-items:flex-start!important}}
`;document.head.appendChild(s);
}

async function ensureAudio(){
 try{
  if(!ctx)ctx=new(window.AudioContext||window.webkitAudioContext)();
  if(ctx.state==='suspended')await ctx.resume();
  return ctx.state==='running';
 }catch(e){console.warn('audio unlock',e);return false}
}
async function playStrongChime(){
 const ok=await ensureAudio();
 if(!ok){try{navigator.vibrate?.([110,70,150])}catch{};return false}
 const now=ctx.currentTime;
 const master=ctx.createGain();master.gain.setValueAtTime(.0001,now);master.gain.exponentialRampToValueAtTime(.15,now+.025);master.gain.exponentialRampToValueAtTime(.0001,now+1.35);master.connect(ctx.destination);
 [[0,660,.22],[.28,880,.22],[.62,740,.34]].forEach(([t,f,d])=>{
  const o=ctx.createOscillator(),g=ctx.createGain();o.type='triangle';o.frequency.setValueAtTime(f,now+t);g.gain.setValueAtTime(.0001,now+t);g.gain.exponentialRampToValueAtTime(.42,now+t+.018);g.gain.exponentialRampToValueAtTime(.0001,now+t+d);o.connect(g);g.connect(master);o.start(now+t);o.stop(now+t+d+.04);
 });
 try{navigator.vibrate?.([90,55,135])}catch{}
 return true;
}
function riskSignature(){
 const out=new Set();
 document.querySelectorAll('.fs23stage.danger,.fs23stage.warning,.tag.red,.tag.orange').forEach(n=>{
  const box=n.closest('.fs23station,.item');if(!box)return;const t=(box.innerText||'').replace(/\s+/g,' ').trim().slice(0,220);if(t)out.add(t);
 });
 return out;
}
async function scanNewWarnings(){
 const now=riskSignature();
 if(baseline===null){baseline=now;return}
 if(audioEnabled){const fresh=[...now].filter(x=>!baseline.has(x));if(fresh.length)await playStrongChime()}
 baseline=now;
}
function hookSound(){
 const test=$('soundBtn'), enable=$('alertsBtn');
 if(test&&!test.dataset.fsHot){
  test.dataset.fsHot='1';const old=test.onclick;
  test.onclick=async function(e){try{if(typeof old==='function')old.call(this,e)}catch{};const ok=await playStrongChime();this.textContent=ok?'🔊 ध्वनि चल्यो':'⚠️ आवाज अनुमति चाहियो';setTimeout(()=>this.textContent='♪ ध्वनि परीक्षण',1600)};
 }
 if(enable&&!enable.dataset.fsHot){
  enable.dataset.fsHot='1';const old=enable.onclick;
  enable.onclick=async function(e){try{if(typeof old==='function')await old.call(this,e)}catch{};audioEnabled=true;localStorage.setItem('fs23-audio-enabled','1');baseline=riskSignature();const ok=await playStrongChime();this.classList.add('fs23soundOn');this.textContent=ok?'🔔 सूचना + आवाज सक्रिय':'🔔 सूचना सक्रिय';};
  if(audioEnabled){enable.classList.add('fs23soundOn');enable.textContent='🔔 सूचना + आवाज सक्रिय'}
 }
 if(!scanTimer)scanTimer=setInterval(scanNewWarnings,5000);
}

function patchImpact(){
 const d=$('deadV'),i=$('injuredV'),m=$('missingV'),ev=$('incidentV'),note=$('impactNote');if(!d||!i||!m||!ev||!note)return;
 const blank=x=>!x||x==='—'||x==='-'||x==='0';
 const bipadEmpty=blank(d.textContent.trim())&&blank(i.textContent.trim())&&blank(m.textContent.trim())&&(ev.textContent.trim()==='0'||blank(ev.textContent.trim()));
 if(bipadEmpty){
  d.textContent='९५';i.textContent='—';m.textContent='—';ev.textContent='—';
  note.classList.add('fs23impactFallback');
  note.innerHTML='BIPAD को आजको aggregated loss total अहिले sync भएको छैन। नेपाल प्रहरीले २०८३-०५-१०, १९:१४ सम्म रसुवा बाढीमा <b>९५ मृत्यु</b> पुष्टि गरेको छ। <a href="https://www.nepalpolice.gov.np/news/10245/" target="_blank" rel="noopener" style="color:#9fe6c4">नेपाल प्रहरी स्रोत</a>';
 }else if(note.classList.contains('fs23impactFallback')&&!(d.textContent.trim()==='९५'&&ev.textContent.trim()==='—')){
  note.classList.remove('fs23impactFallback');
 }
}

function getFocus(){try{return window.__fs?.getFocus?.()||null}catch{return null}}
function openGoogle(){const f=getFocus();if(!f){alert('पहिले नक्सामा स्थान छान्नुहोस्।');return}const u='https://www.google.com/maps/@?api=1&map_action=map&center='+encodeURIComponent(f[0]+','+f[1])+'&zoom=14&basemap=roadmap';window.open(u,'_blank','noopener')}
function openWaze(){const f=getFocus();if(!f){alert('पहिले नक्सामा स्थान छान्नुहोस्।');return}const u='https://www.waze.com/live-map/directions?to=ll.'+encodeURIComponent(f[0]+','+f[1]);window.open(u,'_blank','noopener')}
function patchRoadTools(){
 const list=$('roadList');if(!list||$('fs23roadTools'))return;
 const box=document.createElement('div');box.id='fs23roadTools';box.className='fs23roadTools';box.innerHTML='<b>🛣 थप सडक जाँच</b><small>मुख्य in-app closure/partial status DoR/BIPAD बाट ५ सेकेन्डमा refresh हुन्छ। Official record नभएको ठाउँमा community/live traffic छुट्टै जाँच गर्न सकिन्छ।</small><div class="fs23roadBtns"><button id="fsGoogleRoad">Google Maps</button><button id="fsWazeRoad">Waze Live Map</button></div><small>Google/Waze बाह्य स्रोत हुन्; तिनको traffic/route data सरकारी चेतावनी होइन।</small>';
 list.insertAdjacentElement('afterend',box);$('fsGoogleRoad').onclick=openGoogle;$('fsWazeRoad').onclick=openWaze;
}
function clarifyEmptyRoad(){
 const list=$('roadList');if(!list)return;const t=(list.innerText||'');if(/रेकर्ड भेटिएन/.test(t)&&!/Google Maps/.test(t)){const item=list.querySelector('.item small');if(item)item.textContent='छानिएको दूरीभित्र DoR/BIPAD को बन्द/आंशिक सडक record भेटिएन। तल Google Maps/Waze बाट live route context पनि जाँच गर्न सक्नुहुन्छ।'}
}
function boot(){addCss();hookSound();patchRoadTools();patchImpact();clarifyEmptyRoad();setInterval(()=>{hookSound();patchImpact();clarifyEmptyRoad()},5000);const mo=new MutationObserver(()=>{clearTimeout(window.__fsHotMut);window.__fsHotMut=setTimeout(()=>{patchImpact();clarifyEmptyRoad();scanNewWarnings()},350)});mo.observe(document.body,{subtree:true,childList:true,characterData:true});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,300));else setTimeout(boot,300);
})();
