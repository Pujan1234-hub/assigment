const UPSTREAM='https://bipadportal.gov.np/api/v1/';
const FEEDS={
  rivers:'river/?limit=650',
  riverStations:'river-stations/?limit=650',
  rain:'rain-stations/?limit=650',
  alerts:'alert/?limit=250&ordering=-createdOn',
  roads:'highway/?limit=500',
  weather:'weather/?limit=100',
  incidents:'incident/?limit=200',
  losses:'loss-people/?limit=400',
  bulletins:'bipad-bulletin/?limit=5&ordering=-createdOn',
  affected:'geohazard/affected-area-geojson/'
};
const SNAPSHOT_KEY='floodsafe:nepal:snapshot:v1';
const CLIENT_CACHE_SECONDS=15;
const STALE_SECONDS=300;

function cors(){return {
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Methods':'GET,OPTIONS',
  'Access-Control-Allow-Headers':'Content-Type,If-None-Match',
  'Access-Control-Max-Age':'86400',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer'
}}
function json(body,status=200,extra={}){
  return new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json; charset=utf-8',...cors(),...extra}})
}
async function fetchJson(path,timeoutMs=9000){
  const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),timeoutMs);
  try{
    const r=await fetch(UPSTREAM+path,{headers:{accept:'application/json','user-agent':'FloodSafe-Nepal/1.0'},signal:ctrl.signal,cf:{cacheTtl:0,cacheEverything:false}});
    if(!r.ok)throw new Error('upstream '+r.status);
    return await r.json();
  }finally{clearTimeout(timer)}
}
async function buildSnapshot(){
  const started=Date.now();const entries=Object.entries(FEEDS);
  const settled=await Promise.allSettled(entries.map(async([key,path])=>[key,await fetchJson(path)]));
  const data={},sources={};let ok=0;
  for(let i=0;i<settled.length;i++){
    const key=entries[i][0],r=settled[i];
    if(r.status==='fulfilled'){
      data[key]=r.value[1];sources[key]={ok:true};ok++;
    }else{
      data[key]=null;sources[key]={ok:false,error:String(r.reason?.message||r.reason||'failed')};
    }
  }
  if(ok===0)throw new Error('all upstream feeds failed');
  return {
    ok:true,
    schema:1,
    generated_at:new Date().toISOString(),
    generated_ms:Date.now(),
    duration_ms:Date.now()-started,
    source:'BIPAD/DHM/DoR via FloodSafe Nepal gateway',
    feed_health:{ok,total:entries.length,partial:ok<entries.length},
    sources,
    data
  };
}
async function saveSnapshot(env,snapshot){
  if(env.SNAPSHOT_KV)await env.SNAPSHOT_KV.put(SNAPSHOT_KEY,JSON.stringify(snapshot),{expirationTtl:86400});
}
async function loadSnapshot(env){
  if(!env.SNAPSHOT_KV)return null;
  try{return await env.SNAPSHOT_KV.get(SNAPSHOT_KEY,{type:'json'})}catch{return null}
}
async function refresh(env){
  const snapshot=await buildSnapshot();await saveSnapshot(env,snapshot);return snapshot;
}
async function live(request,env,ctx){
  const cache=caches.default;
  const cacheKey=new Request('https://floodsafe-cache.local/api/live-v1',{method:'GET'});
  const hit=await cache.match(cacheKey);
  if(hit)return hit;

  let snap=await loadSnapshot(env);
  const age=snap?.generated_ms?Date.now()-Number(snap.generated_ms):Infinity;
  if(!snap||age>STALE_SECONDS*1000){
    try{snap=await refresh(env)}catch(e){
      if(!snap)return json({ok:false,error:'live data temporarily unavailable',verified:false},503,{'Cache-Control':'no-store'});
      snap={...snap,stale:true,verified:false,gateway_warning:'refresh failed; serving last known snapshot'};
    }
  }
  const etag='W/"'+String(snap.generated_ms||0)+'"';
  if(request.headers.get('if-none-match')===etag)return new Response(null,{status:304,headers:{...cors(),'ETag':etag,'Cache-Control':`public,max-age=0,s-maxage=${CLIENT_CACHE_SECONDS},stale-while-revalidate=${STALE_SECONDS}`}});
  const response=json(snap,200,{
    'ETag':etag,
    'Cache-Control':`public,max-age=0,s-maxage=${CLIENT_CACHE_SECONDS},stale-while-revalidate=${STALE_SECONDS}`,
    'X-FloodSafe-Cache':'edge'
  });
  ctx.waitUntil(cache.put(cacheKey,response.clone()));
  return response;
}
async function feed(request,env,ctx,key){
  if(!(key in FEEDS))return json({ok:false,error:'unknown feed'},404,{'Cache-Control':'no-store'});
  const r=await live(request,env,ctx);if(!r.ok)return r;
  const snap=await r.clone().json();
  return json({ok:true,generated_at:snap.generated_at,verified:snap.verified!==false,feed_health:snap.feed_health,data:snap.data?.[key]??null},200,{'Cache-Control':`public,max-age=0,s-maxage=${CLIENT_CACHE_SECONDS},stale-while-revalidate=${STALE_SECONDS}`});
}
export default {
  async fetch(request,env,ctx){
    if(request.method==='OPTIONS')return new Response(null,{status:204,headers:cors()});
    if(request.method!=='GET')return json({ok:false,error:'method not allowed'},405,{'Cache-Control':'no-store'});
    const u=new URL(request.url);
    if(u.pathname==='/health'){
      const snap=await loadSnapshot(env);const age=snap?.generated_ms?Date.now()-Number(snap.generated_ms):null;
      return json({ok:true,service:'FloodSafe Nepal Scale Gateway',snapshot:!!snap,age_ms:age,generated_at:snap?.generated_at||null,feed_health:snap?.feed_health||null},200,{'Cache-Control':'no-store'});
    }
    if(u.pathname==='/api/live'||u.pathname==='/api/v1/live')return live(request,env,ctx);
    if(u.pathname.startsWith('/api/v1/feed/'))return feed(request,env,ctx,u.pathname.split('/').pop());
    return json({ok:true,service:'FloodSafe Nepal Scale Gateway',endpoints:['/api/live','/api/v1/feed/:key','/health']},200,{'Cache-Control':'public,max-age=300'});
  },
  async scheduled(event,env,ctx){ctx.waitUntil(refresh(env));}
};
