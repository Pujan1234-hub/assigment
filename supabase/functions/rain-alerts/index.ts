import postgres from 'npm:postgres@3.4.9';
import webpush from 'npm:web-push@3.6.7';
import {forecastUrl,parseForecast,pointKey,alertMessage} from './rain-forecast.mjs';

// No anonymous access to these tables. Browser requests carry a random,
// per-subscription capability; only its hash is stored. Keys live in Vault.
const sql=postgres(Deno.env.get('SUPABASE_DB_URL')!,{prepare:false,max:1,idle_timeout:20,connect_timeout:8,ssl:'require'});
const ORIGIN='https://pujan1234-hub.github.io',APP=ORIGIN+'/assigment/floodsafe-nepal/v25/';
const headers={'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Headers':'content-type','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Cache-Control':'no-store','Content-Type':'application/json','Vary':'Origin'};
const json=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status,headers});
const hash=async(s:string)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),b=>b.toString(16).padStart(2,'0')).join('');
class RequestError extends Error{constructor(message:string,public status=400){super(message)}}
function validSubscription(s:any){
  if(!s||typeof s.endpoint!=='string'||s.endpoint.length>3000)throw new RequestError('Invalid push subscription');
  let u;try{u=new URL(s.endpoint)}catch{throw new RequestError('Invalid push endpoint')}const host=u.hostname;
  if(u.protocol!=='https:'||u.port||u.username||u.password||u.hash||!(host==='fcm.googleapis.com'||host==='updates.push.services.mozilla.com'||host==='web.push.apple.com'||/^[a-z0-9-]+\.notify\.windows\.com$/.test(host)))throw new RequestError('Unsupported push provider');
  for(const [key,length] of [['auth',16],['p256dh',65]] as const){
    const v=s.keys?.[key];if(typeof v!=='string'||!/^[\w-]+={0,2}$/.test(v))throw new RequestError('Invalid subscription key');
    let b;try{b=atob(v.replace(/-/g,'+').replace(/_/g,'/'))}catch{throw new RequestError('Invalid subscription key')}
    if(b.length!==length||(key==='p256dh'&&b.charCodeAt(0)!==4))throw new RequestError('Invalid subscription key');
  }
  return {endpoint:s.endpoint,keys:{p256dh:s.keys.p256dh,auth:s.keys.auth}};
}
async function keys(){
  return await sql.begin(async tx=>{
    await tx`select pg_advisory_xact_lock(88463102)`;
    let [config]=await tx`select public_key,private_secret_id from floodsafe_rain_private.config where id=1`;
    if(!config.public_key){
      const generated=webpush.generateVAPIDKeys();
      const [secret]=await tx`select vault.create_secret(${generated.privateKey},'floodsafe-rain-vapid-v1','Rain Web Push signing key') as id`;
      [config]=await tx`update floodsafe_rain_private.config set public_key=${generated.publicKey},private_secret_id=${secret.id} where id=1 returning public_key,private_secret_id`;
    }
    return config;
  });
}
async function send(sub:any,payload:any,config:any){
  const subscription=validSubscription(sub.subscription),[secret]=await sql`select decrypted_secret from vault.decrypted_secrets where id=${config.private_secret_id}`;
  const request=webpush.generateRequestDetails(subscription,JSON.stringify({...payload,id:sub.id,key:sub.point_key}),{vapidDetails:{subject:APP,publicKey:config.public_key,privateKey:secret.decrypted_secret},TTL:Math.max(0,Math.min(900,Math.floor((payload.expiresAt-Date.now())/1000))),urgency:'normal'});
  const response=await fetch(request.endpoint,{method:request.method,headers:request.headers,body:request.body,redirect:'error',signal:AbortSignal.timeout(6000)});
  if(response.status===404||response.status===410){await sql`delete from floodsafe_rain_private.subscriptions where id=${sub.id}`;return false}
  if(!response.ok)throw new RequestError('Push provider temporarily unavailable',503);
  await response.body?.cancel();return true;
}
async function subscribe(body:any){
  if(typeof body.token!=='string'||!/^[a-zA-Z0-9-]{64,100}$/.test(body.token))throw new RequestError('Invalid subscription token');
  if(typeof body.lat!=='number'||typeof body.lon!=='number'||!Number.isFinite(body.lat)||!Number.isFinite(body.lon)||Math.abs(body.lat)>90||Math.abs(body.lon)>180)throw new RequestError('Invalid location');
  const subscription=validSubscription(body.subscription),tokenHash=await hash(body.token),endpointHash=await hash(subscription.endpoint),key=pointKey(body.lat,body.lon),[lat,lon]=key.split(',').map(Number),language=body.lang==='en'?'en':'ne';
  return await sql.begin(async tx=>{
    await tx`select pg_advisory_xact_lock(88463103)`;
    const [old]=await tx`select id,token_hash from floodsafe_rain_private.subscriptions where endpoint_hash=${endpointHash}`;
    if(old&&old.token_hash!==tokenHash)throw new RequestError('Subscription ownership mismatch',403);
    if(!old){
      const [limits]=await tx`select count(*)::int as total,count(*) filter(where created_at>now()-interval '1 minute')::int as recent,count(distinct point_key)::int as places,bool_or(point_key=${key}) as known_place from floodsafe_rain_private.subscriptions where expires_at>now()`;
      if(limits.total>=500||limits.recent>=20||(!limits.known_place&&limits.places>=50))throw new RequestError('Rain push capacity reached; please retry later',503);
    }
    const [row]=await tx`insert into floodsafe_rain_private.subscriptions(endpoint_hash,subscription,token_hash,lat,lon,point_key,lang,expires_at) values (${endpointHash},${tx.json(subscription)},${tokenHash},${lat},${lon},${key},${language},now()+interval '7 days') on conflict(endpoint_hash) do update set subscription=excluded.subscription,lat=excluded.lat,lon=excluded.lon,point_key=excluded.point_key,lang=excluded.lang,updated_at=now(),expires_at=excluded.expires_at returning id,expires_at`;
    return {id:row.id,expiresAt:new Date(row.expires_at).getTime()};
  });
}
async function authenticated(body:any){
  if(typeof body.id!=='string'||!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(body.id)||typeof body.token!=='string'||body.token.length>100)throw new RequestError('Invalid subscription',403);
  const tokenHash=await hash(body.token),[sub]=await sql`select * from floodsafe_rain_private.subscriptions where id=${body.id} and token_hash=${tokenHash} and expires_at>now()`;
  if(!sub)throw new RequestError('Subscription expired or not authorized',403);return sub;
}
async function tick(config:any){
  const deadline=Date.now()+45000;
  const lease=await sql`update floodsafe_rain_private.config set last_tick=now() where id=1 and (last_tick is null or last_tick<now()-interval '50 seconds') returning id`;
  if(!lease.length)return {skipped:'already checking'};
  await sql`delete from floodsafe_rain_private.subscriptions where expires_at<=now()`;
  await sql`delete from floodsafe_rain_private.deliveries where attempted_at<now()-interval '1 day'`;
  await sql`delete from floodsafe_rain_private.forecasts where attempted_at<now()-interval '1 day'`;
  const due=await sql`select s.point_key,min(s.lat) as lat,min(s.lon) as lon from floodsafe_rain_private.subscriptions s left join floodsafe_rain_private.forecasts f on f.point_key=s.point_key where s.expires_at>now() and (f.fetched_at is null or f.fetched_at<now()-interval '10 minutes') group by s.point_key,f.attempted_at order by f.attempted_at nulls first limit 5`;
  await Promise.all(due.map(async point=>{
    try{
      const response=await fetch(forecastUrl(point.lat,point.lon),{signal:AbortSignal.timeout(9000)});if(!response.ok)throw Error('Forecast unavailable');
      const data=await response.json();parseForecast(data);
      await sql`insert into floodsafe_rain_private.forecasts(point_key,payload,fetched_at,attempted_at) values(${point.point_key},${sql.json(data)},now(),now()) on conflict(point_key) do update set payload=excluded.payload,fetched_at=now(),attempted_at=now()`;
    }catch{await sql`insert into floodsafe_rain_private.forecasts(point_key,attempted_at) values(${point.point_key},now()) on conflict(point_key) do update set attempted_at=now()`}
  }));
  const subs=await sql`select s.*,f.payload from floodsafe_rain_private.subscriptions s join floodsafe_rain_private.forecasts f using(point_key) where s.expires_at>now() and f.fetched_at>now()-interval '12 minutes' and (s.last_sent_at is null or s.last_sent_at<now()-interval '30 minutes') order by s.last_sent_at nulls first limit 500`;
  let submitted=0,failed=0,attempts=0;
  for(let i=0;i<subs.length&&Date.now()<deadline&&attempts<100;i+=5){
    await Promise.all(subs.slice(i,i+5).map(async sub=>{
      let payload;try{payload=alertMessage(parseForecast(sub.payload),Date.now(),sub.lang)}catch{return}if(!payload)return;
      const claimed=await sql`insert into floodsafe_rain_private.deliveries(subscription_id,tag,attempted_at,status,attempts) values(${sub.id},${payload.tag},now(),'pending',1) on conflict(subscription_id,tag) do update set attempted_at=now(),status='pending',attempts=floodsafe_rain_private.deliveries.attempts+1 where floodsafe_rain_private.deliveries.status<>'sent' and floodsafe_rain_private.deliveries.attempted_at<now()-interval '90 seconds' and floodsafe_rain_private.deliveries.attempts<3 returning tag`;
      if(!claimed.length)return;attempts++;
      try{
        if(await send(sub,payload,config)){submitted++;await sql`update floodsafe_rain_private.subscriptions set last_sent_at=now() where id=${sub.id}`;await sql`update floodsafe_rain_private.deliveries set status='sent' where subscription_id=${sub.id} and tag=${payload.tag}`}
      }catch{failed++;await sql`update floodsafe_rain_private.deliveries set status='failed' where subscription_id=${sub.id} and tag=${payload.tag}`}
    }));
  }
  await sql`update floodsafe_rain_private.config set last_success=now(),last_result=${sql.json({refreshed:due.length,checked:subs.length,submitted,failed})} where id=1`;
  return {refreshed:due.length,checked:subs.length,submitted,failed};
}
Deno.serve(async req=>{
  try{
    if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
    if(req.method==='GET'){const config=await keys();return json({publicKey:config.public_key,version:1,leadMinutes:15,forecast:'estimate',retentionDays:7})}
    if(req.method!=='POST')return json({error:'Method not allowed'},405);
    const text=await req.text();if(text.length>10000)return json({error:'Request too large'},413);let body;try{body=JSON.parse(text)}catch{throw new RequestError('Invalid JSON')}
    if(!body||typeof body!=='object'||Array.isArray(body))throw new RequestError('Invalid request');
    if(body.action==='tick'){
      const value=req.headers.get('x-rain-cron-key');if(!value)return json({error:'Not authorized'},401);
      const [secret]=await sql`select decrypted_secret from vault.decrypted_secrets where name='floodsafe-rain-cron-v1'`;
      if(!secret||await hash(value)!==await hash(secret.decrypted_secret))return json({error:'Not authorized'},401);
      return json(await tick(await keys()));
    }
    if(req.headers.get('origin')!==ORIGIN)return json({error:'Origin not allowed'},403);
    if(body.action==='subscribe')return json(await subscribe(body));
    if(body.action==='unsubscribe'){const sub=await authenticated(body);await sql`delete from floodsafe_rain_private.subscriptions where id=${sub.id}`;return json({removed:true})}
    if(body.action==='test'){
      const sub=await authenticated(body);const rate=await sql`update floodsafe_rain_private.subscriptions set last_test_at=now() where id=${sub.id} and (last_test_at is null or last_test_at<now()-interval '1 minute') returning id`;
      if(!rate.length)return json({error:'Wait one minute before another test'},429);
      const ok=await send(sub,{title:sub.lang==='ne'?'🔔 FloodSafe परीक्षण सूचना':'🔔 FloodSafe test notification',body:sub.lang==='ne'?'यो परीक्षण हो, वर्षा चेतावनी होइन।':'This is a test, not a rain warning.',tag:'rain-push-test',expiresAt:Date.now()+120000},await keys());return json({submitted:ok},ok?200:410);
    }
    return json({error:'Unknown action'},400);
  }catch(e){if(e instanceof RequestError)return json({error:e.message},e.status);console.error('Rain push request failed',e?.name||'Error');return json({error:'Rain notification service temporarily unavailable'},503)}
});
