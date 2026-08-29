(()=>{'use strict';
if(window.__fsMapFixV2)return;window.__fsMapFixV2=true;
const NS='http://www.w3.org/2000/svg',B={minLon:80,maxLon:88.35,minLat:26.2,maxLat:30.5},svg=()=>document.getElementById('riverMap'),hint=()=>document.getElementById('mapHint'),detail=()=>document.getElementById('riverDetail');
const xy=(lo,la)=>[(lo-B.minLon)/(B.maxLon-B.minLon)*1000,600-(la-B.minLat)/(B.maxLat-B.minLat)*600];
const inside=(la,lo)=>la>=B.minLat&&la<=B.maxLat&&lo>=B.minLon&&lo<=B.maxLon;
const FALLBACK=[
{name:'Koshi',type:'river',pts:[[87.15,27.85],[87.25,27.55],[87.18,27.25],[87.05,26.95],[86.95,26.72],[86.88,26.45]]},
{name:'Arun',type:'river',pts:[[87.42,28.1],[87.35,27.82],[87.28,27.5],[87.22,27.25],[87.17,27.05]]},
{name:'Tamor',type:'river',pts:[[87.78,27.85],[87.66,27.55],[87.55,27.25],[87.39,27.05],[87.2,26.92]]},
{name:'Kankai',type:'river',pts:[[87.9,27.1],[87.82,26.9],[87.83,26.7],[87.84,26.48]]},
{name:'Mechi',type:'river',pts:[[88.13,27.12],[88.08,26.92],[88.05,26.72],[88.07,26.48]]},
{name:'Bagmati',type:'river',pts:[[85.42,27.78],[85.34,27.66],[85.22,27.42],[85.12,27.05],[85.05,26.72],[85.0,26.45]]},
{name:'Trishuli',type:'river',pts:[[85.31,28.15],[85.2,27.95],[85.08,27.8],[84.96,27.65],[84.83,27.52]]},
{name:'Narayani',type:'river',pts:[[84.82,27.62],[84.58,27.45],[84.4,27.25],[84.32,27.0],[84.28,26.72],[84.25,26.45]]},
{name:'Karnali',type:'river',pts:[[81.3,29.65],[81.35,29.25],[81.25,28.9],[81.12,28.5],[81.08,28.15],[81.02,27.8],[81.0,27.35],[81.02,26.82]]},
{name:'Mahakali',type:'river',pts:[[80.38,30.0],[80.45,29.55],[80.52,29.15],[80.48,28.72],[80.42,28.28],[80.3,27.8],[80.25,27.25],[80.2,26.75]]},
{name:'Rapti',type:'river',pts:[[82.55,28.0],[82.4,27.85],[82.2,27.65],[82.0,27.45],[81.75,27.25],[81.55,27.0]]}
];
async function get(u,ms=8000){const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);try{const r=await fetch(u+(u.includes('?')?'&':'?')+'_mf='+Date.now(),{cache:'no-store',signal:c.signal,credentials:'omit'});if(!r.ok)throw Error(r.status);return await r.json()}finally{clearTimeout(to)}}
function center(f){const g=f.geometry||{},rings=g.type==='Polygon'?[g.coordinates?.[0]]:g.type==='MultiPolygon'?g.coordinates.map(p=>p?.[0]):[];let sx=0,sy=0,n=0;for(const ring of rings)for(const p of ring||[]){if(!p)continue;sx+=p[0];sy+=p[1];n++}return n?[sx/n,sy/n]:null}
function addLabels(geo){const s=svg();if(!s)return;s.querySelectorAll('.districtLabel').forEach(n=>n.remove());for(const f of geo.features||[]){const c=center(f);if(!c)continue;const [x,y]=xy(c[0],c[1]),t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('class','districtLabel');t.setAttribute('text-anchor','middle');t.setAttribute('dominant-baseline','middle');t.textContent=f.properties?.nameEn||'';s.appendChild(t)}}
function paddedView(){svg()?.setAttribute('viewBox','-55 -35 1110 670')}
function focusView(lo,la){const s=svg();if(!s)return;const[x,y]=xy(lo,la),w=520,h=330;s.setAttribute('viewBox',`${x-w/2} ${y-h/2} ${w} ${h}`)}
function clearSmart(){svg()?.querySelectorAll('.riverSmart,.riverFallback').forEach(n=>n.remove())}
const dpath=pts=>pts.map((p,i)=>{const[x,y]=xy(p[0],p[1]);return(i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)}).join(' ');
function drawRivers(rivers,cls='riverSmart'){const s=svg();if(!s)return;for(const r of rivers){const p=document.createElementNS(NS,'path');p.setAttribute('d',dpath(r.pts));p.setAttribute('class',`${cls} ${r.type||'river'}`);p.addEventListener('click',e=>{e.stopPropagation();if(detail())detail().innerHTML=`<strong>${r.name||'नदी / खोला'}</strong><br>${r.type==='stream'?'Stream':'River'} • selected area`});const ti=document.createElementNS(NS,'title');ti.textContent=r.name||'River';p.appendChild(ti);s.appendChild(p)}}
function fallbackFor(la,lo){return FALLBACK.filter(r=>r.pts.some(p=>Math.hypot((p[1]-la)*111,(p[0]-lo)*100)<=85))}
async function queryRivers(la,lo){clearSmart();if(hint())hint().textContent='नदी/खोला लोड हुँदैछ…';const tries=[10,7,5];let els=[];for(const rad of tries){const dl=rad/111,dlo=rad/(111*Math.cos(la*Math.PI/180)),q=`[out:json][timeout:7];way["waterway"~"river|stream"](${la-dl},${lo-dlo},${la+dl},${lo+dlo});out tags geom;`;for(const ep of ['https://overpass.kumi.systems/api/interpreter?data=','https://overpass-api.de/api/interpreter?data=']){try{const j=await get(ep+encodeURIComponent(q),8500);els=(j?.elements||[]).filter(e=>Array.isArray(e.geometry)&&e.geometry.length>1);if(els.length)break}catch{}}if(els.length)break}
let rivers=els.slice(0,140).map(e=>({name:e.tags?.['name:ne']||e.tags?.name||'',type:e.tags?.waterway||'stream',pts:e.geometry.map(g=>[g.lon,g.lat]).filter(p=>inside(p[1],p[0]))})).filter(r=>r.pts.length>1);
if(rivers.length){rivers.sort((a,b)=>(b.type==='river')-(a.type==='river')||Number(Boolean(b.name))-Number(Boolean(a.name)));drawRivers(rivers.slice(0,120));if(hint())hint().textContent=`${Math.min(rivers.length,120)} नदी/खोला देखाइएका छन्। line मा tap गर्नुहोस्।`;return}
const fb=fallbackFor(la,lo);if(fb.length){drawRivers(fb,'riverFallback');if(hint())hint().textContent='Live geometry उपलब्ध नभएकाले यस क्षेत्रका मुख्य नदी fallback रूपमा देखाइएको छ।';return}
if(hint())hint().textContent='यस चयनमा नदी geometry उपलब्ध भएन। नजिकको अर्को जिल्ला/area छान्नुहोस्।'}
async function boot(){let geo=null;try{geo=await get('../v24/nepal-districts.geojson',6500);setTimeout(()=>addLabels(geo),300)}catch{}paddedView();const s=svg();if(!s)return;const obs=new MutationObserver(()=>{if(geo&&!s.querySelector('.districtLabel'))setTimeout(()=>addLabels(geo),0)});obs.observe(s,{childList:true});s.addEventListener('click',e=>{if(e.target.closest?.('.riverSmart,.riverFallback,.gauge'))return;const pt=s.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;const m=s.getScreenCTM();if(!m)return;const p=pt.matrixTransform(m.inverse()),lo=B.minLon+(p.x/1000)*(B.maxLon-B.minLon),la=B.maxLat-(p.y/600)*(B.maxLat-B.minLat);if(!inside(la,lo))return;focusView(lo,la);queryRivers(la,lo)},true);document.getElementById('mapReset')?.addEventListener('click',()=>setTimeout(paddedView,0))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();