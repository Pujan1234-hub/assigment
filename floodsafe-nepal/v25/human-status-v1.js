(()=>{'use strict';
if(window.__fsHumanStatusV1)return;window.__fsHumanStatusV1=true;
const DAY=86400000,WINDOW=10*DAY,POLL=5*60*1000,API='https://bipadportal.gov.np/api/v1/';
const $=id=>document.getElementById(id), rows=j=>Array.isArray(j)?j:(j?.results||j?.data||[]);
const text=o=>JSON.stringify(o||{}).toLowerCase();
const hazardRx=/(flood|flash flood|landslide|earthquake|avalanche|glacial|glof|fire|wildfire|lightning|storm|windstorm|heavy rain|inundation|बाढी|पहिरो|भूकम्प|हिमपहिरो|डढेलो|आगलागी|चट्याङ|डुबान|अविरल वर्षा)/i;
const nonDisasterRx=/(road accident|vehicle accident|traffic accident|दुर्घटना|राजनीति|खेलकुद|निर्वाचन)/i;
const when=o=>o?.incidentOn||o?.incident_on||o?.createdOn||o?.created_at||o?.modifiedOn||o?.updated_at||o?.date||o?.published_at||null;
const ts=o=>{const n=+new Date(when(o)||0);return Number.isFinite(n)?n:0};
const id=o=>String(o?.id??o?.pk??o?.incident_id??o?.incidentId??o?.incident?.id??'');
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function recent(o){const t=ts(o),age=Date.now()-t;return t>0&&age>=-3600000&&age<=WINDOW}
function isDisaster(o){const t=text(o);return hazardRx.test(t)&&!nonDisasterRx.test(t)}
function lossKind(o){const t=text(o);if(/dead|death|deceased|fatal|मृत|मृत्यु/.test(t))return'dead';if(/injur|घाइते/.test(t))return'injured';if(/missing|बेपत्ता/.test(t))return'missing';if(/rescued|rescue|उद्धार/.test(t))return'rescued';return''}
function count(o){for(const k of ['count','people','peopleCount','people_count','number','total','value','noOfPeople','no_of_people']){const n=Number(o?.[k]);if(Number.isFinite(n)&&n>=0)return n}return null}
function rel(o){for(const k of ['incident','incident_id','incidentId']){let v=o?.[k];if(v&&typeof v==='object')v=v.id??v.pk;if(v!==undefined&&v!==null&&String(v))return String(v)}return''}
async function get(url){const c=new AbortController(),to=setTimeout(()=>c.abort(),10000);try{const r=await fetch(url+(url.includes('?')?'&':'?')+'_hs='+Date.now(),{cache:'no-store',credentials:'omit',signal:c.signal});if(!r.ok)throw Error(String(r.status));return await r.json()}finally{clearTimeout(to)}}
async function newsSignal(){try{const j=await get('../../data/floodsafe-news.json'),items=rows(j?.items||j);return items.filter(x=>recent(x)&&isDisaster(x))}catch{return[]}}
function title(o){return o?.titleNe||o?.title||o?.nameNe||o?.name||o?.hazard?.titleNe||o?.hazard?.title||'विपद् घटना'}
function place(o){return o?.district?.titleNe||o?.district?.title||o?.districtName||o?.district_name||o?.municipality?.titleNe||o?.municipality?.title||''}
function fmt(t){if(!t)return'—';try{return new Intl.DateTimeFormat(document.documentElement.lang==='en'?'en-GB':'ne-NP',{timeZone:'Asia/Kathmandu',dateStyle:'medium',timeStyle:'short'}).format(new Date(t))}catch{return new Date(t).toISOString()}}
function num(v){return Number.isFinite(v)?String(v):'—'}
function render(active,incidents,losses,signal){const el=$('humanStatus');if(!el)return;if(!active){el.hidden=true;window.__fsHumanStatus={active:false,incidents:0,totals:{dead:0,injured:0,missing:0,rescued:0},checkedAt:new Date().toISOString(),windowDays:10};return}el.hidden=false;const ids=new Set(incidents.map(id).filter(Boolean));const totals={dead:0,injured:0,missing:0,rescued:0},seen={dead:false,injured:false,missing:false,rescued:false};for(const l of losses){const rid=rel(l);if(rid&&ids.size&&!ids.has(rid))continue;if(!rid&&!recent(l))continue;const k=lossKind(l),n=count(l);if(!k||n===null)continue;totals[k]+=n;seen[k]=true}
 const latest=[...incidents].sort((a,b)=>ts(b)-ts(a))[0];
 $('humanDeaths').textContent=seen.dead?num(totals.dead):'—';$('humanInjured').textContent=seen.injured?num(totals.injured):'—';$('humanMissing').textContent=seen.missing?num(totals.missing):'—';$('humanRescued').textContent=seen.rescued?num(totals.rescued):'—';
 $('humanStatusFresh').textContent=`BIPAD official • ${incidents.length} घटना • १० दिन window • जाँच ${fmt(Date.now())}`;
 const lead=latest?`${esc(title(latest))}${place(latest)?' • '+esc(place(latest)):''}`:(signal[0]?esc(signal[0].title||'विपद् समाचार'):'विपद् समाचार');
 $('humanStatusDetail').innerHTML=`<b>${lead}</b><br>${seen.dead||seen.injured||seen.missing||seen.rescued?'आधिकारिक human-impact records मात्र जोडिएका छन्।':'BIPAD मा पुष्टि human-impact संख्या अझ उपलब्ध छैन; कुनै संख्या अनुमान गरिएको छैन।'}`;
 const link=$('humanStatusLink');if(signal[0]?.url){link.href=signal[0].url;link.hidden=false}else link.hidden=true;
 window.__fsHumanStatus={active:true,incidents:incidents.length,totals,checkedAt:new Date().toISOString(),windowDays:10};
}
async function poll(){try{const [sig,incR,lossR]=await Promise.allSettled([newsSignal(),get(API+'incident/?limit=500&ordering=-incidentOn'),get(API+'loss-people/?limit=1000&ordering=-createdOn')]);const signal=sig.status==='fulfilled'?sig.value:[];const incidents=incR.status==='fulfilled'?rows(incR.value).filter(x=>recent(x)&&isDisaster(x)):[];const losses=lossR.status==='fulfilled'?rows(lossR.value):[];const active=signal.length>0||incidents.length>0;render(active,incidents,losses,signal)}catch{const e=$('humanStatusFresh');if(e)e.textContent='Human Status अहिले refresh हुन सकेन; पुरानो data लाई live भनिएको छैन।'}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{poll();setInterval(poll,POLL)},{once:true});else{poll();setInterval(poll,POLL)}})();
