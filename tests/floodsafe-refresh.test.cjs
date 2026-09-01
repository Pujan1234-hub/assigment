const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function runtime(file) {
  let now = Date.parse('2026-09-01T12:00:00Z'), id = 0;
  const timers = new Map(), events = new Map(), nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, {textContent:'', innerHTML:'', style:{}});
    return nodes.get(id);
  };
  class Clock extends Date { constructor(...a) {super(...(a.length?a:[now]));} static now(){return now;} }
  const context = {Date:Clock, URL, Intl, Map, Set, AbortController, console:{warn(){},log(){}},
    setTimeout:(fn,ms=0)=>{timers.set(++id,{fn,at:now+ms});return id;}, clearTimeout:id=>timers.delete(id),
    setInterval:(fn,ms)=>{timers.set(++id,{fn,at:now+ms,repeat:ms});return id;},
    document:{readyState:'loading',hidden:false,getElementById:node,addEventListener:(e,f)=>events.set(e,f)},
    localStorage:{getItem:()=>null}, navigator:{onLine:true},
    CustomEvent:class{constructor(type,options){this.type=type;this.detail=options?.detail;}},
    fetch:async()=>{throw Error('unconfigured request');},
  };
  context.window={FloodSafe:{state:{lang:'en'}},addEventListener(){},dispatchEvent(){}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25',file),'utf8'),context);
  return {context,node,window:context.window,boot:()=>events.get('DOMContentLoaded')?.(),
    now:()=>now, advance:async(ms)=>{now+=ms;const due=[...timers].filter(([,x])=>x.at<=now);for(const[i,x]of due){if(x.repeat)x.at=now+x.repeat;else timers.delete(i);await x.fn();}await new Promise(resolve=>setImmediate(resolve));},
    respond:fn=>{context.fetch=async(url,options)=>({ok:true,json:async()=>fn(url,options)});},timers};
}
const observation=(id,t,level=2)=>({stationSeriesId:id,title:'Station '+id,waterLevel:level,waterLevelOn:t,longitude:85,latitude:28});

test('human parser binds numbers to outcomes, not years or deployed personnel',async()=>{
  const {extract}=await import('../supabase/functions/human-status-safe-live/human-counts.mjs');
  assert.equal(extract('The death toll has reached 1010, with 8791 personnel mobilized.','death'),1010);
  assert.equal(extract('Bodies of 939 people who died in the disaster have been found, including 23 in Rasuwa.','death'),939);
  assert.equal(extract('More than 3,900 people, including security personnel, are still missing.','missing'),3900);
  assert.equal(extract('11,379 people affected by the floods have been rescued.','rescued'),11379);
  assert.equal(extract('In 2026, 8791 personnel searched for missing people.','missing'),null);
  assert.equal(extract('The death toll is 12. The death toll is 15.','death'),null);
});

test('river values, time boundary and per-station preservation',async()=>{
  const r=runtime('trusted-river-runtime-v3.js'),api=r.window.FloodSafeRiverRealtime,t=new Date(r.now()-60000).toISOString();
  for(const value of [null,'','N/A',true,{},'unknown'])assert.equal(api.level({waterLevel:value}),null);
  assert.equal(api.level({waterLevel:0}),0);
  assert.equal(api.hasObservation(observation(1,t)),true);
  assert.equal(api.hasObservation({...observation(1,t),waterLevelOn:null,retrievedAt:t}),false);
  assert.equal(api.isCurrentTime(new Date(r.now()-600001).toISOString()),true);
  assert.equal(api.isCurrentTime(new Date(r.now()+300001).toISOString()),false);
  assert.equal(api.isCurrentTime('2022-09-01T10:00:00Z'),false);
  assert.equal(api.isCurrentTime('2026-08-31T18:14:59Z'),false,'before Nepal midnight is yesterday');
  assert.equal(api.isCurrentTime('2026-08-31T18:15:00Z'),true,'Nepal midnight starts today');
  const old=[observation(1,t),observation(2,t)];
  assert.equal(api.retain(old,[]).length,2);
  const next=api.retain(old,[observation(1,new Date(r.now()).toISOString(),3)]);
  assert.equal(next.length,2);assert.equal(next[0].waterLevel,3);
  assert.equal(api.retain(old,[observation(1,'2026-09-01T10:00:00Z',8)])[0].waterLevel,2);
  const cached=[{...old[0],_measurementTime:t,_lastWaterLevel:2}];
  const updated=api.retain(cached,[observation(1,new Date(r.now()).toISOString(),4)])[0];
  assert.equal(api.level(updated),4,'old derived fields must not shadow a new raw observation');
  assert.equal(api.measureTime(updated),new Date(r.now()).toISOString());
  assert.equal(api.level(api.retain(old,[observation(1,new Date(r.now()+3600000).toISOString(),9)])[0]),2);
  r.respond(url=>url.includes('floodsafe-core')?{river_stations:[],rivers:[]}:{results:old,fetched_at:t});
  r.boot();await r.advance(300);assert.equal(r.window.FloodSafe.state.currentRiverStations.length,2);
  await r.advance(600001);assert.equal(r.window.FloodSafe.state.currentRiverStations.length,2);
  assert.equal(r.window.FloodSafe.state.allRiverStations.length,2);
  assert.equal(r.window.FloodSafe.state.allRiverStations[0]._lastKnownObservation.level,2);
  assert.equal(r.window.FloodSafe.state.allRiverStations[0]._lastKnownObservation.time,t);
  assert.equal(r.window.FloodSafe.state.allRiverStations[0]._lastWaterLevel,2,'today readings remain available');
  await r.advance(24*60*60*1000);
  assert.equal(r.window.FloodSafe.state.currentRiverStations.length,0);
  assert.equal(r.window.FloodSafe.state.allRiverStations[0]._lastKnownObservation,null,'yesterday readings must not leak into panels');
});

test('missing and expired observations never paint blue',()=>{
  const r=runtime('official-stale-safety-v1.js'),paint={};
  r.window.FloodSafeMap={map:{getLayer:()=>true,setPaintProperty:(_,key,value)=>{paint[key]=value}}};
  r.window.FloodSafeStaleSafety.apply();
  function evaluate(x,p){
    if(!Array.isArray(x))return x;
    const [op,...a]=x,ev=v=>evaluate(v,p);
    if(op==='get')return p[a[0]];
    if(op==='has')return Object.hasOwn(p,a[0]);
    if(op==='all')return a.every(ev);
    if(op==='==')return ev(a[0])===ev(a[1]);
    if(op==='!=')return ev(a[0])!==ev(a[1]);
    if(op==='>=')return ev(a[0])>=ev(a[1]);
    if(op==='<=')return ev(a[0])<=ev(a[1]);
    if(op==='to-number'){const n=Number(ev(a[0]));return Number.isFinite(n)?n:ev(a[1]);}
    if(op==='case')return ev(a[0])?ev(a[1]):ev(a[2]);
    if(op==='match'){for(let i=1;i<a.length-1;i+=2)if(ev(a[0])===a[i])return a[i+1];return a.at(-1);}
    throw Error(op);
  }
  const color=p=>evaluate(paint['circle-color'],p);
  for(const p of [{has_latest:0,age_ms:'',status:'normal'},{has_latest:1,age_ms:'',status:'normal'},{has_latest:1,status:'normal'},{has_latest:1,age_ms:600001,status:'normal'},{has_latest:1,age_ms:-300001,status:'normal'},{has_latest:1,age_ms:0,status:'unknown'}])assert.equal(color(p),'#94a3b8',JSON.stringify(p));
  assert.equal(color({has_latest:1,age_ms:60000,status:'normal'}),'#20b8ff');
  assert.equal(color({has_latest:1,age_ms:60000,status:'danger'}),'#ff2d20');
});

test('station panel shows last known level and date without claiming current safety',()=>{
  const r=runtime('map-side-panel-v1.js'),panel=r.node('fsMapSidePanel');
  panel.classList={add(){},remove(){},contains(){return true}};panel.querySelector=()=>null;
  r.context.document.querySelector=()=>({style:{}});r.context.document.querySelectorAll=()=>[];
  r.context.getComputedStyle=()=>({position:'relative'});
  r.window.FloodSafeRiverRealtime={findStation:()=>({_catalogueOnly:true,_lastKnownObservation:{time:'2026-09-01T10:00:00Z',level:2.5,status:'normal'},_lastWarningLevel:5,_lastDangerLevel:6})};
  r.window.FloodSafeMapPanel.show('Test river',{station_id:'1',has_latest:0},28,85);
  assert.match(panel.innerHTML,/2.5 m/);assert.match(panel.innerHTML,/Last known observation — not current/);
  assert.match(panel.innerHTML,/01 Sept 2026|01 Sep 2026/);
  assert.doesNotMatch(panel.innerHTML,/Current official river status/);
});

test('human data rejects nulls and old fallback cannot overwrite newer report',()=>{
  const r=runtime('impact-live-v1.js'),api=r.window.FloodSafeImpact;
  const row={event:'Bhotekoshi flash flood',recovered_bodies:12,recovered_source:'Radio Nepal',recovered_source_url:'https://radionepalonline.com/report',recovered_update_time:'2026-09-01T10:00:00Z'};
  assert.equal(api.metric({...row,recovered_bodies:null},'death'),null);
  assert.equal(api.metric({...row,recovered_source_url:'javascript:alert(1)'},'death'),null);
  api.accept(row);api.accept({...row,recovered_bodies:10,recovered_update_time:'2026-09-01T09:00:00Z'});
  assert.equal(api.current.death.value,12);
  api.accept({...row,recovered_bodies:11,recovered_update_time:'2026-09-01T11:00:00Z'});
  assert.equal(api.current.death.value,11);
  assert.throws(()=>api.accept({...row,event:'Different event'}));
});

test('news retains dated recent stories, dedupes and refreshes without page reload',async()=>{
  const r=runtime('news-live-v5.js');let count=0;
  const item={title:'नदीको नयाँ समाचार',source:'Radio Nepal',url:'https://radionepalonline.com/report',published_at:'2026-09-01T11:40:00Z'};
  r.respond(()=>({items:++count>1?[item,{...item,title:'अर्को समाचार',url:item.url+'2',published_at:'2026-09-01T11:59:00Z'}]:[item,item],sources:{}}));
  r.boot();await r.advance(300);
  assert.equal(r.window.FloodSafeNews.items.length,1);
  assert.match(r.node('liveNews').innerHTML,/No fresh data/);
  assert.match(r.node('liveNews').innerHTML,/<details class="lastKnownData"/);
  assert.equal(r.window.FloodSafeNews.state.freshCount,0);
  assert.match(r.node('liveNews').innerHTML,/Latest published story/);
  assert.doesNotMatch(r.node('liveNews').innerHTML,/>NEW</);
  await r.advance(10001);assert.equal(r.window.FloodSafeNews.items.length,2);
  assert.equal(r.window.FloodSafeNews.state.freshCount,1);
  assert.doesNotMatch(r.node('liveNews').innerHTML,/No fresh data/);
  r.context.fetch=async()=>{throw Error('offline');};await r.advance(10001);
  assert.equal(r.window.FloodSafeNews.items.length,2);assert.equal(r.window.FloodSafeNews.state.connected,false);
});

test('one human renderer and no competing map lock are loaded',()=>{
  const html=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/index.html'),'utf8');
  assert.match(html,/impact-live-v1.js\?v=\d+/);
  for(const file of ['trusted-river-runtime-v3.js','trusted-rain-runtime-v1.js','news-live-v5.js','impact-live-v1.js','official-stale-safety-v1.js']){
    assert.equal(html.split('src="./'+file+'?v=').length-1,1,file+' must be loaded exactly once');
  }
  assert.doesNotMatch(html,/flood-freshness.js|final-map-lock-v1.js|map-hint-sync-v1.js/);
});

test('human reports remain visible without expiry; newer source report updates them',async()=>{
  const r=runtime('impact-live-v1.js');
  let row={event:'Bhotekoshi flash flood',recovered_bodies:12,recovered_source:'Radio Nepal',recovered_source_url:'https://radionepalonline.com/report',recovered_update_time:'2026-09-01T10:00:00Z'};
  r.respond(()=>row);r.boot();await r.advance(0);
  assert.equal(r.node('impactDeaths').textContent,'12');
  assert.match(r.node('impactFresh').textContent,/Latest reported figures/);
  assert.match(r.node('impactDetail').innerHTML,/Radio Nepal/);
  row={...row,recovered_bodies:13,recovered_update_time:new Date(r.now()).toISOString()};
  await r.window.FloodSafeImpact.sync();
  assert.equal(r.node('impactDeaths').textContent,'13');
  assert.equal(r.window.__fsImpactLiveState.freshCount,1);
  await r.advance(600001);
  assert.equal(r.node('impactDeaths').textContent,'13','published figures must not expire');
  assert.match(r.node('impactFresh').textContent,/Latest reported figures/);
});
test('news moves below at 10 minutes and disappears at 30 minutes',async()=>{
  const r=runtime('news-live-v5.js');
  const item={title:'Boundary story',source:'Radio Nepal',url:'https://radionepalonline.com/boundary',published_at:new Date(r.now()-9*60000).toISOString()};
  r.respond(()=>({items:[item],sources:{}}));r.boot();await r.advance(300);
  assert.equal(r.window.FloodSafeNews.state.freshCount,1);
  await r.advance(60001);
  assert.equal(r.window.FloodSafeNews.state.freshCount,0);
  assert.equal(r.window.FloodSafeNews.state.archiveCount,1);
  await r.advance(20*60000);
  assert.equal(r.window.FloodSafeNews.items.length,0);
});
