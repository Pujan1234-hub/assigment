(()=>{'use strict';
if(window.__fsRiverFreshnessStyleV1)return;window.__fsRiverFreshnessStyleV1=true;
const FRESH=30*60*1000,RECENT=2*60*60*1000,DELAYED=24*60*60*1000;
const tr=(ne,en)=>(window.FloodSafe?.state?.lang||localStorage.getItem('fs-flood-lang')||'ne')==='en'?en:ne;
function classify(t){const x=+new Date(t||0);if(!x)return'none';const a=Math.max(0,Date.now()-x);if(a<=FRESH)return'fresh';if(a<=RECENT)return'recent';if(a<=DELAYED)return'delayed';return'stale'}
function setStates(map){if(!map?.getSource?.('hydro-complete'))return false;let fs=[];try{fs=map.querySourceFeatures('hydro-complete')||[]}catch{return false}const seen=new Set();for(const f of fs){const id=f?.id??f?.properties?.id;if(id===undefined||id===null||seen.has(String(id)))continue;seen.add(String(id));const fresh=classify(f?.properties?.live_time);try{map.setFeatureState({source:'hydro-complete',id},{freshness:fresh})}catch{}}return seen.size>0}
const freshExpr=['coalesce',['feature-state','freshness'],'none'];
const riskColor=['match',['get','live_status'],'danger','#ff2d20','warning','#ff7a00','watch','#ffd166','normal','#22a7ff','#64748b'];
const lineColor=['case',['==',freshExpr,'stale'],'#64748b',['==',freshExpr,'none'],'#64748b',riskColor];
const lineOpacity=['match',freshExpr,'fresh',.99,'recent',.9,'delayed',.66,'stale',.42,.55];
function style(map){if(!map?.isStyleLoaded?.())return false;setStates(map);try{if(map.getLayer('hydro-complete-lines')){map.setPaintProperty('hydro-complete-lines','line-color',lineColor);map.setPaintProperty('hydro-complete-lines','line-opacity',lineOpacity)}if(map.getLayer('hydro-complete-flood-pulse')){map.setFilter('hydro-complete-flood-pulse',['all',['in',['get','live_status'],['literal',['warning','danger']]],['in',freshExpr,['literal',['fresh','recent']]]]);map.setPaintProperty('hydro-complete-flood-pulse','line-color',['match',['get','live_status'],'danger','#ff2d20','#ff7a00']);map.setPaintProperty('hydro-complete-flood-pulse','line-opacity',['match',freshExpr,'fresh',.98,'recent',.72,0])}return true}catch(e){console.warn('FloodSafe freshness river style failed',e);return false}}
function legend(){const box=document.getElementById('fsMapSimpleStatus');if(!box||box.querySelector('.fs-freshness-legend'))return;const d=document.createElement('div');d.className='fs-freshness-legend';d.style.cssText='margin-top:5px;font-size:11px;line-height:1.45;opacity:.92';d.innerHTML=`<span style="color:#22c55e">●</span> ${tr('ताजा ≤30m','fresh ≤30m')} &nbsp; <span style="color:#facc15">●</span> ${tr('हालसालै ≤2h','recent ≤2h')} &nbsp; <span style="color:#fb923c">●</span> ${tr('ढिलो ≤24h','delayed ≤24h')} &nbsp; <span style="color:#94a3b8">●</span> ${tr('पुरानो >24h','stale >24h')}`;box.appendChild(d)}
function apply(){const map=window.FloodSafeMap?.map;if(!map)return false;legend();return style(map)}
for(const ev of['fsriverlinestatus','fsriverupdate','fstrustedriverupdate','fs281mapready','fsmapready','fslanguage'])window.addEventListener(ev,()=>setTimeout(apply,120));
let tries=0;const ready=setInterval(()=>{tries++;if(apply()||tries>120)clearInterval(ready)},250);setInterval(()=>{if(!document.hidden)apply()},10000);
window.FloodSafeFreshness={classify,apply,FRESH,RECENT,DELAYED};
})();
