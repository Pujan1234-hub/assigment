(()=>{
'use strict';
// The old Vercel gateway was never deployed and caused CORS/network errors.
// Keep this file as a compatibility shim only. A production gateway must be
// explicitly configured before any request is routed through it.
const configured=String(window.__FLOODSAFE_GATEWAY_URL||'').trim();
if(!configured){
  window.__floodsafeGateway={enabled:false,status:()=>({enabled:false,reason:'production gateway not configured'})};
  return;
}
const GATEWAY=configured.replace(/\/$/,'')+'/api/live';
const nativeFetch=window.fetch.bind(window);
const TTL=15000;
let cache=null,cacheAt=0,pending=null;
const routeKey=u=>{
  const s=String(u||'');
  if(/bipadportal\.gov\.np\/api\/v1\/(river-stations|river)\//i.test(s))return'rivers';
  if(/bipadportal\.gov\.np\/api\/v1\/rain-stations\//i.test(s))return'rain';
  if(/bipadportal\.gov\.np\/api\/v1\/alert\//i.test(s))return'alerts';
  if(/bipadportal\.gov\.np\/api\/v1\/highway\//i.test(s))return'roads';
  if(/bipadportal\.gov\.np\/api\/v1\/incident\//i.test(s))return'incidents';
  return null;
};
async function snapshot(){
  if(cache&&Date.now()-cacheAt<TTL)return cache;
  if(pending)return pending;
  pending=nativeFetch(GATEWAY,{cache:'no-store'})
    .then(r=>{if(!r.ok)throw Error('gateway '+r.status);return r.json()})
    .then(j=>{if(!j?.ok||!j?.data)throw Error('bad gateway payload');cache=j;cacheAt=Date.now();return j})
    .finally(()=>pending=null);
  return pending;
}
window.fetch=async function(input,init){
  const url=String(input?.url||input||'');
  const key=routeKey(url);
  if(!key)return nativeFetch(input,init);
  try{
    const s=await snapshot();
    const body=s.data?.[key];
    if(body!==undefined&&body!==null)return new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json','X-FloodSafe-Gateway':'1'}});
  }catch(e){console.warn('FloodSafe gateway fallback to official source',e)}
  return nativeFetch(input,init);
};
window.__floodsafeGateway={enabled:true,url:GATEWAY,status:()=>({enabled:true,cached:!!cache,age_ms:cache?Date.now()-cacheAt:null,generated_at:cache?.generated_at||null})};
})();
