(()=>{
'use strict';
const $=id=>document.getElementById(id);
const API_RE=/bipadportal\.gov\.np\/api\/v1\/(river|river-stations)/i;
let ctx=null,audioEnabled=localStorage.getItem('fs23-audio-enabled')==='1',riskBaseline=null,scanTimer=null,riverFeed=[],lastFocusKey='';

function addCss(){
 if(document.getElementById('fs23-hotfix-css'))return;
 const s=document.createElement('style');s.id='fs23-hotfix-css';s.textContent=`
.leaflet-top.leaflet-left{top:auto!important;bottom:58px!important;left:8px!important}.leaflet-control-zoom{margin:0!important;box-shadow:0 6px 18px #0008!important}
.fs23roadTools{margin-top:8px;border:1px solid #604238;border-radius:11px;padding:9px;background:#15100e}.fs23roadTools b{display:block;font-size:11px;margin-bottom:4px}.fs23roadTools small{display:block;color:#c7b8b0;line-height:1.45;margin-top:5px}.fs23roadBtns{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.fs23roadBtns button{border:1px solid #765044;background:#261713;color:#fff;border-radius:9px;padding:8px 9px;font-weight:850;cursor:pointer}.fs23roadBtns button:first-child{background:#3b5f2a;border-color:#72a653}
.fs23impactFallback{color:#f5d37a!important;font-weight:700}.fs23soundOn{background:#176b4d!important;border-color:#54dca8!important}.fs23AlertGate{margin-top:8px;border:1px solid #604238;border-radius:10px;padding:8px 9px;background:#15100e;color:#d7c8c0;font-size:10px;line-height:1.45}.fs23AlertGate.high{border-color:#e79a35;color:#ffe0ac}.fs23AlertGate.very{border-color:#ff5570;color:#ffd7de;background:#2c1116}.fs23AlertGate b{color:#fff}
@media(max-width:900px){.leaflet-top.leaflet-left{bottom:62px!important}.mapBadge{max-width:58%!important}.mapBtns{max-width:42%!important}.mapTop{align-items:flex-start!important}}
`;document.head.appendChild(s);
}

function rows(j){return Array.isArray(j)?j:(j?.results||j?.data||j?.objects||[])}
function coord(o){const c=o?.point?.coordinates||o?.location?.coordinates||o?.centroid?.coordinates||o?.geometry?.coordinates;if(Array.isArray(c)&&c.length>=2&&Number.isFinite(+c[0])&&Number.isFinite(+c[1]))return[+c[1],+c[0]];return null}
function km(a,b){if(!a||!b)return Infinity;const R=6371,p=Math.PI/180,d1=(b[0]-a[0])*p,d2=(b[1]-a[1])*p,s=Math.sin(d1/2)**2+Math.cos(a[0]*p)*Math.cos(b[0]*p)*Math.sin(d2/2)**2;return 2*R*Math.asin(Math.sqrt(s))}
function val(o,keys){for(const k of keys){const v=o?.[k];if(v!==undefined&&v!==null&&v!=='')return v}return null}
function titleOf(o){return String(val(o,['title','name','station_name','river_name','location_name'])||val(o?.station||{},['name','station_name'])||'DHM river station')}
function statusOf(o){return String(val(o,['status','steady','trend','state','warning_status','alert_status'])||'').trim().toUpperCase()}
function num(v){const n=Number(v);return Number.isFinite(n)?n:null}
function threshold(v){const n=num(v);return n!==null&&n>0?n:null}
function stage(o){const wl=num(val(o,['waterLevel','water_level','level','waterlevel'])),w=threshold(val(o,['warningLevel','warning_level','warning'])),d=threshold(val(o,['dangerLevel','danger_level','danger'])),st=statusOf(o);const below=/BELOW\s+(WARNING|DANGER)|NORMAL|SAFE/.test(st);if(!below&&((d!==null&&wl!==null&&wl>=d)||/ABOVE\s+DANGER|DANGER\s+LEVEL\s+EXCEEDED|^DANGER$|RED\s+ALERT|VERY\s+HIGH/.test(st)))return'very';if(!below&&((w!==null&&wl!==null&&wl>=w)||/ABOVE\s+WARNING|WARNING\s+LEVEL\s+EXCEEDED|ORANGE\s+ALERT|HIGH\s+ALERT/.test(st)))return'high';return'none'}
function when(o){return val(o,['waterLevelOn','measuredOn','modifiedOn','createdOn','recordedDate','date'])}
function fresh(o,h=6){const t=+new Date(when(o)||0);return Number.isFinite(t)&&Date.now()-t>=-3600e3&&Date.now()-t<=h*3600e3}
function getFocus(){try{const f=window.__fs?.getFocus?.();return Array.isArray(f)&&f.length===2?f:null}catch{return null}}
function focusKey(){const f=getFocus();return f?f.map(x=>(+x).toFixed(4)).join(','):''}

function captureRiverFeed(){
 if(window.__fs23FloodCapture)return;
 window.__fs23FloodCapture=true;
 const native=window.fetch.bind(window);
 window.fetch=async(...args)=>{const r=await native(...args);try{const u=String(args[0]?.url||args[0]||'');if(API_RE.test(u)){const j=await r.clone().json(),list=rows(j);if(list.length){const seen=new Map();[...riverFeed,...list].forEach(o=>{const c=coord(o),k=titleOf(o).toLowerCase()+'|'+(c?c.map(v=>v.toFixed(4)).join(','):'');seen.set(k,o)});riverFeed=[...seen.values()].slice(-1400)}}}catch(e){console.warn('river capture',e)}return r};
}
async function seedRiverFeed(){try{const rs=await Promise.allSettled([fetch('https://bipadportal.gov.np/api/v1/river-stations/?limit=650',{cache:'no-store'}),fetch('https://bipadportal.gov.np/api/v1/river/?limit=650',{cache:'no-store'})]);for(const x of rs)if(x.status==='fulfilled'){try{const j=await x.value.clone().json();riverFeed.push(...rows(j))}catch{}}}catch{}}

function normName(s){return String(s||'').toLowerCase().replace(/[()\[\],./_-]+/g,' ').replace(/\b(river|khola|nadi|nadi|station|gauge|at|the|near|bridge)\b/g,' ').replace(/\s+/g,' ').trim()}
function tokens(s){return normName(s).split(' ').filter(x=>x.length>=3)}
function sameRiver(a,b){const A=tokens(a),B=tokens(b);return A.some(x=>B.some(y=>x===y||x.length>=5&&y.length>=5&&(x.includes(y)||y.includes(x))))}
function parseKm(s){const m=String(s||'').match(/([0-9]+(?:\.[0-9]+)?)\s*(?:किमि|km)/i);return m?+m[1]:Infinity}
function waterways(){return [...document.querySelectorAll('#waterwayList .item')].map(n=>{const b=n.querySelector('b'),sm=[...n.querySelectorAll('small')],meta=sm.map(x=>x.textContent||'').join(' '),type=/\briver\b/i.test(meta)?'river':/\bstream\b/i.test(meta)?'stream':/\bcanal\b/i.test(meta)?'canal':'waterway';return{name:b?.textContent?.trim()||'',d:parseKm(meta),type}}).filter(x=>Number.isFinite(x.d))}
function corridorLimit(sev,type){if(type==='river')return sev==='very'?1.6:.9;if(type==='stream')return sev==='very'?.85:.45;if(type==='canal')return sev==='very'?.65:.35;return sev==='very'?1.2:.7}
function sourceDistanceLimit(sev,matched){if(matched)return sev==='very'?50:30;return sev==='very'?5:3}
function collectRisks(){
 const f=getFocus();if(!f)return[];
 const ws=waterways(),nearestW=ws.sort((a,b)=>a.d-b.d)[0]||null,out=[],seen=new Set();
 for(const o of riverFeed){const c=coord(o),sev=stage(o);if(!c||sev==='none'||!fresh(o,6))continue;const sd=km(f,c);let matched=null;for(const w of ws){if(w.name&&sameRiver(titleOf(o),w.name)&&(matched===null||w.d<matched.d))matched=w}const w=matched||nearestW;if(!w)continue;const allowedCorridor=corridorLimit(sev,w.type),allowedSource=sourceDistanceLimit(sev,!!matched);if(w.d>allowedCorridor||sd>allowedSource)continue;const key=normName(titleOf(o))+'|'+sev;if(seen.has(key))continue;seen.add(key);out.push({key,sev,title:titleOf(o),waterDist:w.d,sourceDist:sd,matched:!!matched,waterName:w.name||'',waterType:w.type})}
 return out.sort((a,b)=>(a.sev==='very'?-2:-1)-(b.sev==='very'?-2:-1)||a.waterDist-b.waterDist||a.sourceDist-b.sourceDist);
}

async function ensureAudio(){try{if(!ctx)ctx=new(window.AudioContext||window.webkitAudioContext)();if(ctx.state==='suspended')await ctx.resume();return ctx.state==='running'}catch(e){console.warn('audio unlock',e);return false}}
async function playStrongChime(){const ok=await ensureAudio();if(!ok){try{navigator.vibrate?.([110,70,150])}catch{};return false}const now=ctx.currentTime,master=ctx.createGain();master.gain.setValueAtTime(.0001,now);master.gain.exponentialRampToValueAtTime(.15,now+.025);master.gain.exponentialRampToValueAtTime(.0001,now+1.35);master.connect(ctx.destination);[[0,660,.22],[.28,880,.22],[.62,740,.34]].forEach(([t,f,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type='triangle';o.frequency.setValueAtTime(f,now+t);g.gain.setValueAtTime(.0001,now+t);g.gain.exponentialRampToValueAtTime(.42,now+t+.018);g.gain.exponentialRampToValueAtTime(.0001,now+t+d);o.connect(g);g.connect(master);o.start(now+t);o.stop(now+t+d+.04)});try{navigator.vibrate?.([90,55,135])}catch{}return true}
async function notifyRisk(r){try{if(Notification.permission!=='granted')return;const title=r.sev==='very'?'🔴 VERY HIGH बाढी ALERT':'⚠️ HIGH बाढी ALERT',body='तपाईं नदी/खोला जोखिम buffer भित्र हुनुहुन्छ • '+r.waterDist.toFixed(1)+' km नदीबाट • '+r.title;const reg=await navigator.serviceWorker?.ready;if(reg)reg.showNotification(title,{body,icon:'./icon.svg',badge:'./icon.svg',tag:'fs23-'+r.key,renotify:false});else new Notification(title,{body,icon:'./icon.svg',tag:'fs23-'+r.key})}catch{}}
function hist(){try{return JSON.parse(localStorage.getItem('fs23-risk-history')||'{}')}catch{return{}}}
function canSound(key){const h=hist();return !h[key]||Date.now()-h[key]>30*60*1000}
function rememberSound(key){const h=hist();h[key]=Date.now();for(const k of Object.keys(h))if(Date.now()-h[k]>24*3600e3)delete h[k];localStorage.setItem('fs23-risk-history',JSON.stringify(h))}
async function scanNewWarnings(forceCurrent=false){
 const fk=focusKey();if(fk!==lastFocusKey){lastFocusKey=fk;riskBaseline=null}
 const risks=collectRisks(),now=new Map(risks.map(r=>[r.key,r]));renderAlertGate(risks);
 if(riskBaseline===null){riskBaseline=forceCurrent?new Map():now;if(!forceCurrent)return}
 const freshRisks=risks.filter(r=>!riskBaseline.has(r.key)).sort((a,b)=>(a.sev==='very'?-2:-1)-(b.sev==='very'?-2:-1));
 if(audioEnabled&&freshRisks.length){const r=freshRisks[0];if(canSound(r.key)){await playStrongChime();rememberSound(r.key);await notifyRisk(r)}}
 riskBaseline=now;
}
function renderAlertGate(risks=collectRisks()){
 let el=$('fs23AlertGate');if(!el){const hero=document.querySelector('.hero .actions');if(!hero)return;el=document.createElement('div');el.id='fs23AlertGate';el.className='fs23AlertGate';hero.insertAdjacentElement('afterend',el)}
 const f=getFocus();el.className='fs23AlertGate';if(!f){el.innerHTML='🔕 आवाज <b>GPS/स्थान छानेपछि</b> मात्र जाँच हुन्छ।';return}
 const r=risks[0];if(!r){el.innerHTML='🔕 आवाज केवल <b>HIGH ⚠️ / VERY HIGH 🔴 स्थानीय बाढी जोखिम</b> मा मात्र बज्छ। सडक, सामान्य/बढ्दो नदी वा टाढाको चेतावनीले आवाज बज्दैन।';return}
 el.classList.add(r.sev==='very'?'very':'high');el.innerHTML=(r.sev==='very'?'🔴 <b>VERY HIGH ALERT</b>':'⚠️ <b>HIGH ALERT</b>')+' • नदी/खोलाबाट '+r.waterDist.toFixed(1)+' km • DHM स्टेशन '+r.sourceDist.toFixed(1)+' km'+(r.matched?' • एउटै नदी नाम मिलेको':' • नजिकको नदी buffer');
 const rv=$('riskV');if(rv){rv.textContent=r.sev==='very'?'VERY HIGH ALERT':'HIGH ALERT';rv.className=r.sev==='very'?'bad':'warn'}
}
function hookSound(){
 const test=$('soundBtn'),enable=$('alertsBtn');
 if(test&&!test.dataset.fsRisk){test.dataset.fsRisk='1';test.onclick=async function(){const ok=await playStrongChime();this.textContent=ok?'🔊 ध्वनि चल्यो':'⚠️ आवाज अनुमति चाहियो';setTimeout(()=>this.textContent='♪ ध्वनि परीक्षण',1600)}}
 if(enable&&!enable.dataset.fsRisk){enable.dataset.fsRisk='1';enable.onclick=async function(){audioEnabled=true;localStorage.setItem('fs23-audio-enabled','1');await ensureAudio();try{if('Notification'in window&&Notification.permission==='default')await Notification.requestPermission()}catch{};this.classList.add('fs23soundOn');this.textContent='🔔 HIGH/VERY HIGH सूचना सक्रिय';riskBaseline=new Map();await scanNewWarnings(true)};}
 if(enable&&audioEnabled){enable.classList.add('fs23soundOn');enable.textContent='🔔 HIGH/VERY HIGH सूचना सक्रिय'}
 if(!scanTimer)scanTimer=setInterval(()=>scanNewWarnings(false),5000);
}

function patchImpact(){const d=$('deadV'),i=$('injuredV'),m=$('missingV'),ev=$('incidentV'),note=$('impactNote');if(!d||!i||!m||!ev||!note)return;const blank=x=>!x||x==='—'||x==='-'||x==='0';const bipadEmpty=blank(d.textContent.trim())&&blank(i.textContent.trim())&&blank(m.textContent.trim())&&(ev.textContent.trim()==='0'||blank(ev.textContent.trim()));if(bipadEmpty){d.textContent='९५';i.textContent='—';m.textContent='—';ev.textContent='—';note.classList.add('fs23impactFallback');note.innerHTML='BIPAD को आजको aggregated loss total अहिले sync भएको छैन। नेपाल प्रहरीले २०८३-०५-१०, १९:१४ सम्म रसुवा बाढीमा <b>९५ मृत्यु</b> पुष्टि गरेको छ। <a href="https://www.nepalpolice.gov.np/news/10245/" target="_blank" rel="noopener" style="color:#9fe6c4">नेपाल प्रहरी स्रोत</a>'}else if(note.classList.contains('fs23impactFallback')&&!(d.textContent.trim()==='९५'&&ev.textContent.trim()==='—'))note.classList.remove('fs23impactFallback')}
function openGoogle(){const f=getFocus();if(!f){alert('पहिले नक्सामा स्थान छान्नुहोस्।');return}window.open('https://www.google.com/maps/@?api=1&map_action=map&center='+encodeURIComponent(f[0]+','+f[1])+'&zoom=14&basemap=roadmap','_blank','noopener')}
function openWaze(){const f=getFocus();if(!f){alert('पहिले नक्सामा स्थान छान्नुहोस्।');return}window.open('https://www.waze.com/live-map/directions?to=ll.'+encodeURIComponent(f[0]+','+f[1]),'_blank','noopener')}
function patchRoadTools(){const list=$('roadList');if(!list||$('fs23roadTools'))return;const box=document.createElement('div');box.id='fs23roadTools';box.className='fs23roadTools';box.innerHTML='<b>🛣 थप सडक जाँच</b><small>मुख्य in-app closure/partial status DoR/BIPAD बाट ५ सेकेन्डमा refresh हुन्छ।</small><div class="fs23roadBtns"><button id="fsGoogleRoad">Google Maps</button><button id="fsWazeRoad">Waze Live Map</button></div><small>Google/Waze बाह्य स्रोत हुन्; तिनको traffic/route data सरकारी चेतावनी होइन।</small>';list.insertAdjacentElement('afterend',box);$('fsGoogleRoad').onclick=openGoogle;$('fsWazeRoad').onclick=openWaze}
function clarifyEmptyRoad(){const list=$('roadList');if(!list)return;const t=list.innerText||'';if(/रेकर्ड भेटिएन/.test(t)){const item=list.querySelector('.item small');if(item)item.textContent='छानिएको दूरीभित्र DoR/BIPAD को बन्द/आंशिक सडक record भेटिएन। तल Google Maps/Waze बाट live route context पनि जाँच गर्न सक्नुहुन्छ।'}}
function boot(){addCss();captureRiverFeed();hookSound();patchRoadTools();patchImpact();clarifyEmptyRoad();renderAlertGate();seedRiverFeed().then(()=>setTimeout(()=>scanNewWarnings(false),600));setInterval(()=>{hookSound();patchImpact();clarifyEmptyRoad();renderAlertGate()},5000);const mo=new MutationObserver(()=>{clearTimeout(window.__fsHotMut);window.__fsHotMut=setTimeout(()=>{patchImpact();clarifyEmptyRoad();renderAlertGate();scanNewWarnings(false)},450)});mo.observe(document.body,{subtree:true,childList:true,characterData:true})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,350));else setTimeout(boot,350);
})();
