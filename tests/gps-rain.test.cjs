const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const base=path.join(__dirname,'../floodsafe-nepal/v25');
const helper=()=>import('../supabase/functions/rain-alerts/rain-forecast.mjs');
test('published browser and server use the exact same forecast parser',()=>{
  assert.equal(fs.readFileSync(path.join(base,'rain-forecast-v1.mjs'),'utf8'),fs.readFileSync(path.join(__dirname,'../supabase/functions/rain-alerts/rain-forecast.mjs'),'utf8'));
  assert.match(fs.readFileSync(path.join(base,'rain-timing-v4.js'),'utf8'),/from '\.\/rain-forecast-v1\.mjs'/);
});
function gpsRuntime(){
  let now=Date.parse('2026-09-02T08:00:00Z'),callback,fail,watchCount=0,cleared=[],next=0;
  const events=new Map(),nodes=new Map(),timers=[];
  const on=(type,fn)=>{if(!events.has(type))events.set(type,[]);events.get(type).push(fn)},emit=(type,detail)=>{for(const fn of events.get(type)||[])fn({detail})};
  const node=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',hidden:true,addEventListener:on});return nodes.get(id)};
  const source=new Map(),layers=new Map(),flights=[];
  const map={getSource:k=>source.get(k),addSource:(k,o)=>source.set(k,{data:o.data,setData(data){this.data=data}}),getLayer:k=>layers.get(k),addLayer:o=>layers.set(o.id,o),moveLayer(){},flyTo:o=>flights.push(o),on};
  const state={lang:'en',kind:null},focus=[];
  class Clock extends Date{constructor(...a){super(...(a.length?a:[now]))}static now(){return now}}
  const window={FloodSafe:{state,setFocus(la,lo,kind){focus.push({la,lo,kind});state.kind=kind;return new Promise(()=>{})}},FloodSafeMobileMap:{isOpen:false},addEventListener:on,dispatchEvent:e=>emit(e.type,e.detail)};
  const document={readyState:'complete',hidden:false,getElementById:node,addEventListener:on};
  const context={window,document,localStorage:{getItem:()=>null},navigator:{geolocation:{watchPosition(ok,bad){callback=ok;fail=bad;watchCount++;return++next},clearWatch:id=>cleared.push(id)}},Date:Clock,Intl,Math,Number,CustomEvent:class{constructor(type,o){this.type=type;this.detail=o?.detail}},setInterval:fn=>timers.push(fn)};
  vm.runInNewContext(fs.readFileSync(path.join(base,'location-runtime-v3.js'),'utf8'),context);
  return {window,document,node,source,layers,flights,focus,emit,map,timers,cleared,count:()=>watchCount,advance:ms=>{now+=ms;timers.forEach(fn=>fn())},fix:(lat,lon,extra={})=>callback({timestamp:now,coords:{latitude:lat,longitude:lon,accuracy:12},...extra}),fail:e=>fail(e)};
}
test('GPS starts only on click, one watcher, marker does not wait for weather',()=>{
  const r=gpsRuntime();assert.equal(r.count(),0);r.window.FloodSafeMap={map:r.map};r.emit('click');assert.equal(r.count(),1);
  r.fix(27.7,85.3);assert.equal(r.source.get('fs-user-location').data.features.length,2);assert.equal(r.focus.length,1);
  assert.equal(r.window.FloodSafeMobileMap.isOpen,false);assert.equal(r.flights.length,0);
  assert.match(r.node('place').textContent,/My current location/);
  r.fix(27.71,85.31);assert.equal(r.source.get('fs-user-location').data.features[1].geometry.coordinates[0],85.31);
  r.window.FloodSafeMobileMap.isOpen=true;r.emit('fsmapvisibility');assert.equal(r.flights.length,1);assert.equal(r.flights[0].center[0],85.31);
  r.fix(27.72,85.32);assert.equal(r.flights.length,1,'moving GPS does not keep stealing pan/zoom');
});
test('GPS received before map ready is displayed on later open; old data is labelled',()=>{
  const r=gpsRuntime();r.emit('click');r.fix(27.7,85.3);r.window.FloodSafeMap={map:r.map};r.emit('fsmapready');
  assert.equal(r.source.get('fs-user-location').data.features[1].properties.fresh,true);
  r.advance(121000);assert.equal(r.source.get('fs-user-location').data.features[1].properties.fresh,false);assert.match(r.node('place').textContent,/Last GPS location/);
});
test('GPS outside Nepal never appears as a Nepal marker and permission failure is not abroad',()=>{
  const r=gpsRuntime();r.window.FloodSafeMap={map:r.map};r.emit('click');r.fail({code:1,message:'Denied'});assert.equal(r.node('outsideNotice').hidden,true);
  r.emit('click');r.fix(51.5,-.12);assert.equal(r.node('outsideNotice').hidden,false);assert.equal(r.source.get('fs-user-location').data.features.length,0);
  r.fix(27.7,85.3);assert.equal(r.node('outsideNotice').hidden,true);assert.equal(r.source.get('fs-user-location').data.features.length,2);
});
test('GPS pauses in hidden tabs and resumes without adding duplicate watchers',()=>{
  const r=gpsRuntime();r.emit('click');r.document.hidden=true;r.emit('visibilitychange');assert.equal(r.cleared.length,1);assert.equal(r.window.FloodSafeCurrentLocation.tracking,false);
  r.document.hidden=false;r.emit('visibilitychange');r.emit('pageshow');assert.equal(r.count(),2);
});
test('one GPS owner and notification-only worker survive reload cleanup',()=>{
  const core=fs.readFileSync(path.join(base,'flood-only.js'),'utf8'),rain=fs.readFileSync(path.join(base,'rain-timing-v4.js'),'utf8'),reset=fs.readFileSync(path.join(base,'flood-reset.js'),'utf8');
  assert.doesNotMatch(core,/addEventListener\('click',locate\)/);assert.doesNotMatch(rain,/watchPosition|getCurrentPosition|MobileMap.*open/);
  assert.match(reset,/rain-alert-sw\.js/);assert.doesNotMatch(fs.readFileSync(path.join(base,'rain-alert-sw.js'),'utf8'),/addEventListener\('fetch'/);
});
function data(now,values){return {timezone:'Asia/Kathmandu',current_units:{time:'unixtime'},minutely_15_units:{time:'unixtime',rain:'mm',showers:'mm'},current:{time:now/1000,rain:0,showers:0},minutely_15:{time:values.map((_,i)=>(now+i*900000)/1000),rain:values,showers:values.map(()=>0)}}}
test('forecast uses interval START and pairs start/end; showers count as rain',async()=>{
  const {parseForecast,rainAlert}=await helper(),now=Date.parse('2026-09-02T08:00:00Z'),j=data(now,[0,0,.2,.3,0,0]);
  const f=parseForecast(j,now);assert.equal(f.start.from,now+900000);assert.equal(f.start.to,now+1800000);assert.equal(f.stop.to,now+2700000);assert.equal(rainAlert(f,now).minutes,15);
  j.minutely_15.rain=j.minutely_15.rain.map(()=>0);j.minutely_15.showers=[0,0,.2,.3,0,0];assert.equal(parseForecast(j,now).start.from,f.start.from);
});
test('15-minute alert expires and does not fire early or after onset',async()=>{
  const {parseForecast,rainAlert}=await helper(),now=Date.parse('2026-09-02T08:00:00Z'),f=parseForecast(data(now,[0,0,.3,.3,0,0]),now);
  assert.equal(rainAlert(f,now-60000),null);assert.equal(rainAlert(f,now).minutes,15);assert.equal(rainAlert(f,now+840000).minutes,1);assert.equal(rainAlert(f,now+900000),null);
});
test('unknown, stale, wrong units, time gaps and snow cannot invent rain alerts',async()=>{
  const {parseForecast,rainAlert}=await helper(),now=Date.parse('2026-09-02T08:00:00Z');
  let j=data(now,[0,0,null,.3,0,0]);assert.equal(parseForecast(j,now).unknown,true);assert.equal(rainAlert(parseForecast(j,now),now),null);
  j=data(now,[0,0,0,0]);j.current.precipitation=1;j.current.snowfall=1;assert.equal(parseForecast(j,now).start,null);
  j=data(now,[0,0,.3,0]);j.current.rain=null;assert.throws(()=>parseForecast(j,now),/Incomplete/);
  j=data(now,[0,0,.3,0]);assert.throws(()=>parseForecast(j,now+3600000),/stale/);
  j.minutely_15.time[2]+=1;assert.throws(()=>parseForecast(j,now),/interval gap/);
  j=data(now,[0,0,.3,0]);j.minutely_15_units.rain='inch';assert.throws(()=>parseForecast(j,now),/units/);
});
test('notification copy labels forecast times and current rain does not trigger pre-rain alert',async()=>{
  const {parseForecast,alertMessage}=await helper(),now=Date.parse('2026-09-02T08:00:00Z'),j=data(now,[0,0,.3,0]);
  const m=alertMessage(parseForecast(j,now),now,'en');assert.match(m.title,/expected/);assert.match(m.body,/Forecast timing may change/);assert.match(m.body,/14:00–14:15/);
  j.current.showers=.3;assert.equal(alertMessage(parseForecast(j,now),now,'ne'),null);
});
test('push requests require scoped capability; URLs are allowlisted and secrets are not in clients',()=>{
  const backend=fs.readFileSync(path.join(__dirname,'../supabase/functions/rain-alerts/index.ts'),'utf8');
  assert.match(backend,/token_hash=\$\{tokenHash\}/);assert.match(backend,/x-rain-cron-key/);assert.match(backend,/redirect:'error'/);assert.match(backend,/expires_at>now\(\)/);assert.match(backend,/vault\.decrypted_secrets/);
  const client=fs.readFileSync(path.join(base,'rain-push-v1.js'),'utf8');assert.doesNotMatch(client,/service_role|privateKey/);assert.match(client,/window\.confirm/);assert.match(client,/Notification\.requestPermission/);
});
test('rain UI retries failed requests, rejects old-location responses, and clears expired weather',async()=>{
  const h=await helper(),events=new Map(),nodes=new Map(),requests=[],timers=new Map();let now=Date.now(),timerId=0;
  const node=id=>{if(!nodes.has(id))nodes.set(id,{textContent:'',style:{},after(){}});return nodes.get(id)};
  class Clock extends Date{static now(){return now}}
  const on=(e,f)=>events.set(e,f),state={lat:27.7,lon:85.3,lang:'en'};
  const window={FloodSafe:{state},addEventListener:on};
  const context={...h,window,document:{readyState:'complete',hidden:false,getElementById:node,createElement:()=>({style:{},after(){}}),addEventListener:on},Date:Clock,Number,Math,AbortController,
    setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId},clearTimeout:id=>timers.delete(id),setInterval:fn=>events.set('tick',fn),
    setupRainAlerts:()=>({mount(){},locationChanged(){},check:async()=>{},render(){}}),fetch:()=>new Promise((resolve,reject)=>requests.push({resolve,reject}))};
  vm.runInNewContext(fs.readFileSync(path.join(base,'rain-timing-v4.js'),'utf8').replace(/^import .*;\n/gm,''),context);
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  requests[0].reject(Error('offline'));await settle();assert.ok([...timers.values()].some(t=>t.ms===60000));
  now+=60000;const retry=window.FloodSafeRain.refresh(false);assert.equal(requests.length,2,'retry must not stop at the normal five-minute throttle');
  const response=temp=>{const j=data(now,[0,0,0,0]);j.current.temperature_2m=temp;return {ok:true,json:async()=>j}};
  requests[1].resolve(response(20));await retry;assert.equal(node('temp').textContent,'20°');
  state.lat=28;const old=window.FloodSafeRain.refresh();assert.equal(node('temp').textContent,'—','clear old area immediately');
  state.lat=29;const latest=window.FloodSafeRain.refresh();requests[3].resolve(response(23));await latest;
  requests[2].resolve(response(99));await old;assert.equal(node('temp').textContent,'23°');
  now+=600001;events.get('tick')();assert.equal(node('temp').textContent,'—');assert.match(node('rainTiming').textContent,/unavailable/);
});
test('push worker acknowledges stored settings and rejects disabled, expired or wrong-area messages',async()=>{
  const handlers=new Map(),shown=[],replies=[];let stored=null;
  const self={addEventListener:(name,fn)=>handlers.set(name,fn),registration:{scope:'https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/',showNotification:async(...args)=>shown.push(args)}};
  const source=fs.readFileSync(path.join(base,'rain-alert-sw.js'),'utf8').replace(/^function settings\(value\).*\n/m,'');
  vm.runInNewContext(source,{self,URL,Date,Number,String,settings:async value=>value?(stored=value):stored});
  let work;const emit=async(type,extra)=>{handlers.get(type)({...extra,waitUntil:p=>{work=p}});await work};
  const config={type:'rain-settings',id:'test',key:'27.70,85.30',enabled:true,expiresAt:Date.now()+60000};
  await emit('message',{data:config,ports:[{postMessage:r=>replies.push(r)}]});assert.equal(replies[0].ok,true);
  const message={id:'test',key:config.key,expiresAt:Date.now()+30000,title:'Forecast test'};
  const push=body=>emit('push',{data:{json:()=>body}});
  await push(message);assert.equal(shown.length,1);
  for(const change of [{key:'28.00,85.00'},{id:'another'},{expiresAt:0},{expiresAt:undefined}])await push({...message,...change});
  stored={...config,enabled:false};await push(message);assert.equal(shown.length,1);
});
