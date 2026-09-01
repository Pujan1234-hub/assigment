const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

function runtime(file, transform=code=>code) {
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
  vm.runInContext(transform(fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25',file),'utf8')),context);
  return {context,node,window:context.window,boot:()=>events.get('DOMContentLoaded')?.(),
    now:()=>now, advance:async(ms)=>{now+=ms;const due=[...timers].filter(([,x])=>x.at<=now);for(const[i,x]of due){if(x.repeat)x.at=now+x.repeat;else timers.delete(i);await x.fn();}await new Promise(resolve=>setImmediate(resolve));},
    respond:fn=>{context.fetch=async(url,options)=>({ok:true,json:async()=>fn(url,options)});},timers};
}
const observation=(id,t,level=2)=>({stationSeriesId:id,title:'Station '+id,waterLevel:level,waterLevelOn:t,longitude:85,latitude:28});

test('map starts closed; only explicit open changes state; refresh starts closed again',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/user-facing-ui-v1.js'),'utf8');
  const create=()=>{
    const classes=new Set(['fsMapClosed']),attrs={},button={textContent:'',setAttribute:(k,v)=>attrs[k]=v};
    const nodes={fsOpenMapBtn:button,map:{classList:{toggle:(k,on)=>on?classes.add(k):classes.delete(k)},scrollIntoView(){}}};
    const c={document:{getElementById:id=>nodes[id]},window:{FloodSafe:{state:{lang:'en'}}},setTimeout:fn=>fn(),localStorage:{getItem:()=>null}};
    vm.createContext(c);
    const helpers=source.match(/const \$=[^\n]+/)[0]+'\n'+source.match(/let open=[^\n]+/)[0]+'\n'+['renderButton','show','close'].map(n=>source.match(new RegExp('function '+n+'\\([^\\n]+'))[0]).join('\n');
    vm.runInContext(helpers,c);c.renderButton();return{c,classes,attrs,button};
  };
  const r=create();assert.ok(r.classes.has('fsMapClosed'));assert.equal(r.attrs['aria-expanded'],'false');
  r.c.renderButton();assert.ok(r.classes.has('fsMapClosed'),'re-render does not auto-open');
  r.c.show();assert.ok(r.classes.has('fsMapOpen'));assert.equal(r.attrs['aria-expanded'],'true');
  r.c.close();r.c.renderButton();assert.ok(r.classes.has('fsMapClosed'));
  r.c.show();assert.ok(create().classes.has('fsMapClosed'),'fresh page does not remember open state');
  assert.doesNotMatch(source,/function bindNav|addEventListener\('click',\(\)=>\{show\(\)/);
  assert.match(fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/index.html'),'utf8'),/<section class="card mapCard fsMapClosed" id="map">/);
});

function hydroRuntime() {
  const r=runtime('hydro-smooth-v2.js',code=>code.replace(/\}\)\(\);\s*$/, 'window.__hydroTest={loadTile,bootData,json,visibleData,FAILURES,CACHE};})();'));
  const sources=new Map(),layers=new Map(),events=new Map();let zoom=9;
  r.bounds={west:80.1,east:81.8,south:26.1,north:26.8};
  r.map={isStyleLoaded:()=>true,getZoom:()=>zoom,getBounds:()=>({getWest:()=>r.bounds.west,getEast:()=>r.bounds.east,getSouth:()=>r.bounds.south,getNorth:()=>r.bounds.north}),
    getSource:k=>sources.get(k),addSource:(k,v)=>sources.set(k,{data:v.data,setData(data){this.data=data}}),
    getLayer:k=>layers.get(k),addLayer:v=>layers.set(v.id,v),on:(e,f)=>events.set(e,f),once:(e,f)=>events.set(e,f)};
  r.window.FloodSafeMap={map:r.map};r.api=r.window.__hydroTest;
  r.manifest={minLon:80,minLat:26,stepLon:1,stepLat:1,nx:2,ny:1,tiles:{'0-0':{},'1-0':{}}};
  r.water=id=>({id,pts:[[80.2,26.2],[80.4,26.4]],type:'stream',name:'Stream '+id});
  r.payload=url=>url.includes('manifest')?r.manifest:{waterways:[r.water(url.includes('overview')?'overview':url.includes('0-0')?'left':'right')]};
  r.data=()=>sources.get('hydro-complete')?.data?.features||[];
  r.move=z=>{events.get('movestart')?.();zoom=z;events.get('moveend')?.()};
  return r;
}

test('river tiles retry automatically, retain overview, and render recovered detail',async()=>{
  const r=hydroRuntime();let failedCalls=0;
  r.respond(url=>{if(url.includes('0-0')&&++failedCalls===1)throw Error('temporary outage');return r.payload(url)});
  r.boot();await r.advance(100);await r.advance(100);
  assert.equal(r.api.CACHE.has('0-0'),false,'failed fetch must not be cached as empty');
  assert.equal(r.window.FloodSafeHydroSmooth.loadingState.failedVisibleTiles,1);
  assert.ok(r.data().some(f=>f.properties.id==='overview'),'overview remains during partial failure');
  assert.ok(r.data().some(f=>f.properties.id==='right'),'successful neighbour remains visible');
  await r.advance(3000);await r.advance(100);await r.advance(100);
  assert.equal(failedCalls,2,'retry occurs without moving or reloading');
  assert.equal(r.window.FloodSafeHydroSmooth.loadingState.failedVisibleTiles,0);
  assert.deepEqual(Array.from(r.data(),f=>f.properties.id).sort(),['left','right']);
  assert.ok(r.data().every(f=>f.properties.live_status==='unknown'),'geometry must not invent a reading');
});

test('river metadata retries and returning from overview still loads local detail',async()=>{
  const r=hydroRuntime();let calls=0;
  r.respond(url=>{if(url.includes('manifest')&&++calls===1)throw Error('manifest offline');return r.payload(url)});
  r.boot();await r.advance(100);
  await r.advance(5100);await r.advance(100);await r.advance(100);
  assert.equal(calls,2);assert.equal(r.data().length,2);
  r.move(6);await r.advance(300);await r.advance(100);
  assert.equal(r.data()[0].properties.id,'overview');
  r.move(9);await r.advance(300);await r.advance(100);
  assert.equal(r.data().length,2);assert.equal(r.window.FloodSafeHydroSmooth.loadingState.loadedVisibleTiles,2);
});

test('river detail does not wait for satellite or other map sources to finish loading',async()=>{
  const r=hydroRuntime();r.respond(r.payload);r.move(6);r.boot();
  await r.advance(100);await r.advance(100);assert.equal(r.data()[0].properties.id,'overview');
  r.map.isStyleLoaded=()=>false; // Own layers exist; background tiles are still loading.
  r.move(9);await r.advance(300);await r.advance(100);
  assert.equal(r.window.FloodSafeHydroSmooth.loadingState.loadedVisibleTiles,2);
  assert.deepEqual(Array.from(r.data(),f=>f.properties.id).sort(),['left','right']);
});

test('valid empty tiles cache, malformed tiles back off, and requests time out',async()=>{
  const r=hydroRuntime();let calls=0;
  r.respond(()=>{calls++;return{waterways:[]}});
  await r.api.loadTile('empty');await r.api.loadTile('empty');assert.equal(calls,1);
  r.respond(()=>({error:'not a tile'}));await r.api.loadTile('bad');
  assert.equal(r.api.CACHE.has('bad'),false);assert.equal(r.api.FAILURES.get('bad').attempts,1);
  await r.api.loadTile('bad');assert.equal(r.api.FAILURES.get('bad').attempts,1);
  await r.advance(3000);await r.api.loadTile('bad');
  assert.equal(r.api.FAILURES.get('bad').retryAt-r.now(),6000,'exponential retry avoids a request storm');
  r.context.fetch=(_url,{signal})=>new Promise((_,reject)=>signal.addEventListener('abort',()=>reject(Error('timeout'))));
  const hanging=r.api.loadTile('slow');await r.advance(12001);await hanging;
  assert.equal(r.api.CACHE.has('slow'),false);assert.match(r.api.FAILURES.get('slow').error,/timeout/);
});

test('overlapping river refreshes share a two-request limit and reject stale pan results',async()=>{
  const r=hydroRuntime();let active=0,maxActive=0;const release=[];
  r.context.fetch=async url=>{
    if(/manifest|overview/.test(url))return{ok:true,json:async()=>r.payload(url)};
    active++;maxActive=Math.max(maxActive,active);
    await new Promise(resolve=>release.push(resolve));active--;
    return{ok:true,json:async()=>r.payload(url)};
  };
  r.boot();const initial=r.advance(100);await new Promise(resolve=>setImmediate(resolve));
  assert.equal(active,2);const api=r.window.FloodSafeHydroSmooth;
  await Promise.all([api.refresh(),api.refresh(),api.refresh()]);assert.equal(maxActive,2);
  r.move(6);release.splice(0).forEach(fn=>fn());
  await initial;await r.advance(400);await r.advance(100);
  assert.equal(r.data().length,1);assert.equal(r.data()[0].properties.id,'overview','old local response cannot overwrite zoomed-out view');
});

test('river flow events coalesce and never rebroadcast themselves forever',async()=>{
  const listeners=new Map();let rebuilds=0,now=0;const timers=[];
  const c={document:{readyState:'complete'},setTimeout:fn=>timers.push(fn),window:{
    addEventListener:(name,fn)=>listeners.set(name,fn),
    FloodSafeRiverLine:{rebuild:()=>{rebuilds++;listeners.get('fsriverlinestatus')?.()}},
    FloodSafeRiverStyle:{apply(){}},FloodSafeStaleSafety:{apply(){}}
  }};
  vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/river-flow-freshness-v1.js'),'utf8'),c);
  while(timers.length&&now++<10)timers.shift()();
  assert.equal(rebuilds,1);assert.equal(timers.length,0,'no self-triggered loop');
  for(const e of ['fsriverupdate','fstrustedriverupdate','fsriverheartbeat'])listeners.get(e)();
  assert.equal(timers.length,1);timers.shift()();assert.equal(rebuilds,2);assert.equal(timers.length,0);
});

test('unmeasured streams are visible grey, and static recovery reads the real waterways format',()=>{
  const code=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/river-line-style-v1.js'),'utf8');
  assert.match(code,/'#cbd5e1'/);assert.match(code,/BASE_OPACITY=\['case',KNOWN,\['case',FRESH,.98,.72\],.88\]/);
  for(const colour of ['#ff1616','#ff7a00','#ffd43b','#12b8ff'])assert.ok(code.includes(colour));
  const recovery=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/map-mobile-recovery-v1.js'),'utf8');
  const c={};vm.createContext(c);vm.runInContext(recovery.match(/function waterways[^\n]+/)[0],c);
  const list=[{id:'stream',pts:[[84,28],[84.1,28.1]]}];assert.equal(c.waterways({waterways:list}),list);
});

test('tips rotate every ten minutes, never repeat before a full cycle and yield to all news',async()=>{
  const r=runtime('news-live-v5.js');r.respond(()=>({items:[]}));r.boot();
  assert.match(r.node('liveNews').innerHTML,/id="newsTip"/);
  const seen=new Set([r.window.__fsNewsLiveState.tipIndex]);
  await r.advance(599999);assert.equal(r.window.__fsNewsLiveState.tipIndex,0);
  await r.advance(100);assert.equal(r.window.__fsNewsLiveState.tipIndex,1);seen.add(1);
  for(let i=2;i<16;i++){await r.advance(600100);seen.add(r.window.__fsNewsLiveState.tipIndex)}
  assert.equal(seen.size,16);await r.advance(600100);assert.equal(r.window.__fsNewsLiveState.tipIndex,0);
  const published_at=new Date(r.now()).toISOString();
  r.respond(()=>({items:[{title:'New report',source:'Radio Nepal',url:'https://example.com/report',published_at}]}));
  await r.advance(10000);assert.equal(r.window.__fsNewsLiveState.tipsVisible,false);
  assert.doesNotMatch(r.node('liveNews').innerHTML,/id="newsTip"/);
  await r.advance(11*60000);assert.equal(r.window.__fsNewsLiveState.archiveCount,1);
  assert.equal(r.window.__fsNewsLiveState.tipsVisible,false,'older displayable news also hides tips');
  r.context.fetch=async()=>{throw Error('offline')};
  await r.advance(20*60000);assert.equal(r.window.__fsNewsLiveState.tipsVisible,true);
  assert.match(r.node('liveNews').innerHTML,/Source:/);
  const index=r.window.__fsNewsLiveState.tipIndex;
  await r.advance(600100);assert.notEqual(r.window.__fsNewsLiveState.tipIndex,index);
});

test('nearby updates coalesce and unchanged list preserves its DOM',()=>{
  const code=fs.readFileSync(path.join(__dirname,'../floodsafe-nepal/v25/flood-only.js'),'utf8');
  let queued, renders=0, checks=0, writes=0,value='same';
  const c={requestAnimationFrame:fn=>{queued=fn;return 1},renderStations:()=>renders++,nearbyCheck:()=>checks++,risk(){},tick(){}};
  vm.createContext(c);
  vm.runInContext(code.match(/function writeStationList[^\n]+/)[0]+'\n'+code.match(/let nearbyFrame=0;\nfunction riverChanged[^\n]+/)[0],c);
  c.riverChanged();c.riverChanged();c.riverChanged();queued();
  assert.equal(renders,1);assert.equal(checks,1);
  const out={get innerHTML(){return value},set innerHTML(v){writes++;value=v}};
  c.writeStationList(out,'same');assert.equal(writes,0);
  c.writeStationList(out,'new source reading');assert.equal(writes,1);
});

test('river clicks choose nearest geometry and never borrow Bagmati gauge name',()=>{
  const r=runtime('map-side-panel-v1.js'),api=r.window.FloodSafeMapPanel;
  const line=(name,y)=>({properties:{name,live_station:'Bagmati at Khokana'},geometry:{type:'LineString',coordinates:[[0,y],[100,y]]}});
  const bagmati=line('Bagmati',10),bishnumati=line('Bishnumati',0),dhobikhola=line('Dhobi Khola',20);
  const map={project:([x,y])=>({x,y})};
  for(const [y,name]of [[0,'Bishnumati'],[10,'Bagmati'],[20,'Dhobi Khola']]){
    assert.equal(api.riverName(api.pickFeature([bagmati,dhobikhola,bishnumati],{x:50,y},map)),name);
  }
  assert.equal(api.riverName(line('',0)),'Unnamed river/stream');
  assert.equal(api.riverName({properties:{name_ne:'विष्णुमती',live_station:'Bagmati'}}),'विष्णुमती');
});

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
  const color=p=>evaluate(paint['circle-color'],{observed_ms:r.now()-Number(p.age_ms||0),...p});
  for(const p of [{has_latest:0,age_ms:'',status:'normal'},{has_latest:1,age_ms:'',status:'normal'},{has_latest:1,status:'normal'},{has_latest:1,age_ms:86400000,status:'normal'},{has_latest:1,age_ms:-300001,status:'normal'},{has_latest:1,age_ms:0,status:'unknown'}])assert.equal(color(p),'#94a3b8',JSON.stringify(p));
  assert.equal(color({has_latest:1,age_ms:60000,status:'normal'}),'#20b8ff');
  assert.equal(color({has_latest:1,age_ms:1200000,status:'normal'}),'#20b8ff','today reading over 10 minutes must remain coloured');
  assert.equal(color({has_latest:1,age_ms:3600000,status:'warning'}),'#ff8a00');
  assert.equal(color({has_latest:1,age_ms:3600000,status:'watch'}),'#ffd43b');
  assert.equal(color({has_latest:1,age_ms:3600000,status:'danger'}),'#ff2d20');
  assert.equal(color({has_latest:1,age_ms:60000,observed_ms:0,status:'normal'}),'#94a3b8');
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
