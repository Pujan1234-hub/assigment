(()=>{
'use strict';
if(window.__floodsafeResilience)return;
window.__floodsafeResilience=true;
const nativeFetch=window.fetch.bind(window);
const SNAPSHOT='../../data/floodsafe-core.json';
let cache=null,cacheAt=0,inflight=null;
function sourceFor(url){
  const s=String(url||'');
  if(!/https:\/\/bipadportal\.gov\.np\/api\/v1\//i.test(s))return null;
  if(/\/alert\//i.test(s))return 'alerts';
  if(/\/river\//i.test(s))return 'rivers';
  if(/\/highway\//i.test(s))return 'roads';
  return null;
}
async function snapshot(){
  if(cache&&Date.now()-cacheAt<4000)return cache;
  if(inflight)return inflight;
  inflight=nativeFetch(SNAPSHOT+'?t='+Date.now(),{cache:'no-store',credentials:'omit'})
    .then(r=>{if(!r.ok)throw Error('snapshot HTTP '+r.status);return r.json()})
    .then(j=>{cache=j;cacheAt=Date.now();return j})
    .finally(()=>{inflight=null});
  return inflight;
}
function fallbackResponse(j,key){
  const src=j?.sources?.[key],list=j?.[key];
  if(!src?.ok||!Array.isArray(list))return null;
  return new Response(JSON.stringify({results:list,count:list.length,_floodsafe_fallback:true,_snapshot_generated_at:j.generated_at}),{
    status:200,
    headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-FloodSafe-Fallback':'1'}
  });
}
window.fetch=async function(input,init){
  const url=typeof input==='string'?input:input?.url;
  const key=sourceFor(url);
  if(!key)return nativeFetch(input,init);
  try{
    const r=await nativeFetch(input,init);
    if(r&&r.ok)return r;
    throw Error('official feed HTTP '+(r?.status||0));
  }catch(err){
    try{
      const j=await snapshot(),fb=fallbackResponse(j,key);
      if(fb){
        window.dispatchEvent(new CustomEvent('floodsafe:fallback',{detail:{source:key,generated_at:j.generated_at}}));
        return fb;
      }
    }catch(_){ }
    throw err;
  }
};
window.__floodsafeResilienceState=()=>({snapshotGeneratedAt:cache?.generated_at||null,sources:cache?.sources||null});
})();
