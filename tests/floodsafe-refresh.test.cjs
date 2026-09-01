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
    document:{readyState:'loading',hidden:false,getElementById:node,addEventListener:(e,f)=>events.set(e,f)},
    localStorage:{getItem:()=>null}, navigator:{onLine:true},
    CustomEvent:class{constructor(type,options){this.type=type;this.detail=options?.detail;}},
    fetch:async()=>{throw Error('unconfigured request');},
  };
  context.window={FloodSafe:{state:{lang:'en'}},addEventListener(){},dispatchEvent(){}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25',file),'utf8'),context);
  return {context,node,window:context.window,boot:()=>events.get('DOMContentLoaded')?.(),
    now:()=>now, advance:async(ms)=>{now+=ms;const due=[...timers].filter(([,x])=>x.at<=now);for(const[i,x]of due){timers.delete(i);await x.fn();}await new Promise(resolve=>setImmediate(resolve));},
    respond:fn=>{context.fetch=async(url,options)=>({ok:true,json:async()=>fn(url,options)});},timers};
}
const observation=(id,t,level=2)=>({stationSeriesId:id,title:'Station '+id,waterLevel:level,waterLevelOn:t,longitude:85,latitude:28});

test('river values, time boundary and per-station preservation',async()=>{
  const r=runtime('trusted-river-runtime-v3.js'),api=r.window.FloodSafeRiverRealtime,t=new Date(r.now()-60000).toISOString();
  for(const value of [null,'','N/A',true,{},'unknown'])assert.equal(api.level({waterLevel:value}),null);
  assert.equal(api.level({waterLevel:0}),0);
  assert.equal(api.hasObservation(observation(1,t)),true);
  assert.equal(api.hasObservation({...observation(1,t),waterLevelOn:null,retrievedAt:t}),false);
  assert.equal(api.isCurrentTime(new Date(r.now()-600001).toISOString()),false);
  assert.equal(api.isCurrentTime(new Date(r.now()+300001).toISOString()),false);
  const old=[observation(1,t),observation(2,t)];
  assert.equal(api.retain(old,[]).length,2);
  const next=api.retain(old,[observation(1,new Date(r.now()).toISOString(),3)]);
  assert.equal(next.length,2);assert.equal(next[0].waterLevel,3);
  assert.equal(api.retain(old,[observation(1,'2026-09-01T10:00:00Z',8)])[0].waterLevel,2);
  r.respond(url=>url.includes('floodsafe-core')?{river_stations:[],rivers:[]}:{results:old,fetched_at:t});
  r.boot();await r.advance(300);assert.equal(r.window.FloodSafe.state.currentRiverStations.length,2);
  await r.advance(600001);assert.equal(r.window.FloodSafe.state.currentRiverStations.length,0);
  assert.equal(r.window.FloodSafe.state.allRiverStations.length,2);
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
  const item={title:'नदीको नयाँ समाचार',source:'Radio Nepal',url:'https://radionepalonline.com/report',published_at:'2026-09-01T11:30:00Z'};
  r.respond(()=>({items:++count>1?[item,{...item,title:'अर्को समाचार',url:item.url+'2',published_at:'2026-09-01T11:59:00Z'}]:[item,item],sources:{}}));
  r.boot();await r.advance(300);
  assert.equal(r.window.FloodSafeNews.items.length,1);
  assert.match(r.node('liveNews').innerHTML,/Latest published story/);
  assert.doesNotMatch(r.node('liveNews').innerHTML,/>NEW</);
  await r.advance(10001);assert.equal(r.window.FloodSafeNews.items.length,2);
  r.context.fetch=async()=>{throw Error('offline');};await r.advance(10001);
  assert.equal(r.window.FloodSafeNews.items.length,2);assert.equal(r.window.FloodSafeNews.state.connected,false);
});

test('one human renderer and no competing map lock are loaded',()=>{
  const html=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/index.html'),'utf8');
  assert.match(html,/impact-live-v1.js\?v=3/);
  assert.doesNotMatch(html,/flood-freshness.js|final-map-lock-v1.js|map-hint-sync-v1.js/);
});
