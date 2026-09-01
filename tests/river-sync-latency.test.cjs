const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');

function runtime({fail=false}={}){
  let handler, synced=false;
  const requests=[];
  const old={stationSeriesId:1,title:'Test station',waterLevel:2,waterLevelOn:new Date(Date.now()-1200000).toISOString()};
  const fresh={...old,waterLevel:3,waterLevelOn:new Date().toISOString()};
  const retained={stationSeriesId:2,title:'Retained station',waterLevel:4,waterLevelOn:old.waterLevelOn};
  const db={from(table){return {
    select(){return this},eq(){return this},
    order(){return Promise.resolve({data:[{official_payload:synced?fresh:old},{official_payload:retained}]})},
    maybeSingle(){return Promise.resolve({data:{last_success_at:new Date(synced?Date.now():Date.now()-60000).toISOString()}})},
    async upsert(){if(table==='river_stations')synced=true;return {error:null}}
  }}};
  const context=vm.createContext({URL,Date,Map,Set,Promise,AbortSignal,Response,
    createClient:()=>db,Deno:{env:{get:()=> 'test'},serve:fn=>handler=fn},
    fetch:async url=>{url=String(url);requests.push(url);assert.ok(!url.includes('/api/v1/river/?'),'must not crawl history on live path');
      await new Promise(r=>setTimeout(r,15));
      if(fail&&url.includes('latest=true'))throw Error('upstream unavailable');
      return {ok:true,json:async()=>({results:[fresh],next:null})};}
  });
  let code=fs.readFileSync('supabase/functions/sync-bipad-rivers/index.ts','utf8').replace(/^import .*;\n/gm,'');
  vm.runInContext(stripTypeScriptTypes(code),context);
  return {call:()=>handler({method:'GET'}),requests};
}

test('GET awaits latest feed and returns read-back last-good rows without history crawl',async()=>{
  const r=runtime(),response=await r.call(),body=await response.json();
  assert.equal(response.status,200);
  assert.equal(body.results[0].waterLevel,3);
  assert.equal(body.results[1].waterLevel,4);
  assert.equal(body.fresh_10m_count,1);
  assert.equal(r.requests.length,2);
});
test('upstream failure is explicit, not a successful cached sync',async()=>{
  const response=await runtime({fail:true}).call();
  assert.equal(response.status,502);
});
test('concurrent requests share the in-flight sync within one worker',async()=>{
  const r=runtime();await Promise.all([r.call(),r.call()]);
  assert.equal(r.requests.length,2);
});
