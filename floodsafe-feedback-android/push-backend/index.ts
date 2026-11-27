
const origins=new Set(['https://pjbuilts.com','https://www.pjbuilts.com']);
const cats=new Set(['bug','wrong_data','notification','suggestion','other']);
const statuses=new Set(['new','reviewing','fixed','closed']);
const table='floodsafe_website_feedback';
const fields='id,created_at,category,message,contact,screenshot_url,app_version,page_url,user_agent,status,admin_note';
const enc=new TextEncoder();
const hex=(a:ArrayBuffer)=>Array.from(new Uint8Array(a),v=>v.toString(16).padStart(2,'0')).join('');
const str=(v:unknown,n:number)=>typeof v==='string'?v.trim().slice(0,n):'';
const base=Deno.env.get('SUPABASE_URL')||'';
let key=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')||'';
try{key=JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS')||'{}').default||key}catch{}
async function db(path:string,method='GET',body?:unknown){
 const headers:Record<string,string>={apikey:key,'Content-Type':'application/json',Accept:'application/json'};
 if(!key.startsWith('sb_secret_'))headers.Authorization='Bearer '+key;
 if(method==='PATCH')headers.Prefer='return=representation';
 const r=await fetch(base+'/rest/v1/'+path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error('DB HTTP '+r.status);
 return await r.json();
}
async function admin(token:string){
 if(!token||token.length>256)return false;
 const rows=await db('fs_feedback_admin_credentials?select=token_sha256&slot=eq.true&limit=1');
 const expected=rows[0]?.token_sha256||'';
 const actual=hex(await crypto.subtle.digest('SHA-256',enc.encode(token)));
 if(expected.length!==64)return false;
 let diff=0;for(let i=0;i<64;i++)diff|=expected.charCodeAt(i)^actual.charCodeAt(i);
 return diff===0;
}
async function pushFeedback(id:string){
 const secret=Deno.env.get('FEEDBACK_FCM_SERVICE_ACCOUNT');
 if(!secret)return;
 const account=JSON.parse(secret);
 if(account.project_id!=='floodsafe-nepal')throw Error('FCM project mismatch');
 const rows=await db('fs_feedback_push_device?select=fcm_token,admin_hash&slot=eq.true');
 const adminRows=await db('fs_feedback_admin_credentials?select=token_sha256&slot=eq.true');
 if(!rows[0]||rows[0].admin_hash!==adminRows[0]?.token_sha256)return;
 const reports=await db(table+'?id=eq.'+id+'&select=created_at');
 if(!reports[0])return;
 const b64=(s:Uint8Array)=>btoa(String.fromCharCode(...s)).replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
 const now=Math.floor(Date.now()/1000);
 const part=b64(enc.encode(JSON.stringify({alg:'RS256',typ:'JWT'})))+'.'+b64(enc.encode(JSON.stringify({iss:account.client_email,scope:'https://www.googleapis.com/auth/firebase.messaging',aud:'https://oauth2.googleapis.com/token',iat:now,exp:now+3600})));
 const der=Uint8Array.from(atob(account.private_key.replace(/-----[^-]+-----|\s/g,'')),(c:string)=>c.charCodeAt(0));
 const signing=await crypto.subtle.importKey('pkcs8',der,{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['sign']);
 const assertion=part+'.'+b64(new Uint8Array(await crypto.subtle.sign('RSASSA-PKCS1-v1_5',signing,enc.encode(part))));
 const auth=await fetch('https://oauth2.googleapis.com/token',{method:'POST',body:new URLSearchParams({grant_type:'urn:ietf:params:oauth:grant-type:jwt-bearer',assertion}),signal:AbortSignal.timeout(8000)});
 if(!auth.ok)throw Error('FCM OAuth failed');
 const access=(await auth.json()).access_token;
 const response=await fetch('https://fcm.googleapis.com/v1/projects/floodsafe-nepal/messages:send',{method:'POST',headers:{Authorization:'Bearer '+access,'Content-Type':'application/json'},body:JSON.stringify({message:{token:rows[0].fcm_token,data:{kind:'website_feedback',id,created_at:reports[0].created_at},android:{priority:'HIGH',ttl:'3600s',restricted_package_name:'com.pjbuilts.floodsafefeedback'}}}),signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw Error('FCM send HTTP '+response.status);
}
async function limitedBody(req:Request){
 if(Number(req.headers.get('content-length')||0)>16000)throw Error('body');
 const reader=req.body?.getReader();if(!reader)throw Error('body');
 const chunks:Uint8Array[]=[];let size=0;
 while(true){const {value,done}=await reader.read();if(done)break;size+=value.byteLength;if(size>16000){await reader.cancel();throw Error('body')}chunks.push(value)}
 const all=new Uint8Array(size);let offset=0;for(const x of chunks){all.set(x,offset);offset+=x.byteLength}
 const b=JSON.parse(new TextDecoder().decode(all));if(!b||typeof b!=='object'||Array.isArray(b))throw Error('body');return b;
}
Deno.serve(async(req)=>{
 const origin=req.headers.get('origin')||'';
 const headers:Record<string,string>={'Content-Type':'application/json','Cache-Control':'no-store, private','Vary':'Origin','X-Content-Type-Options':'nosniff'};
 if(origins.has(origin)){headers['Access-Control-Allow-Origin']=origin;headers['Access-Control-Allow-Methods']='GET, POST, PATCH, OPTIONS';headers['Access-Control-Allow-Headers']='content-type, x-admin-token, authorization, apikey';}
 const reply=(status:number,body:unknown)=>new Response(JSON.stringify(body),{status,headers});
 if(origin&&!origins.has(origin))return reply(403,{ok:false,error:'Origin not allowed'});
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
 if(!base||!key)return reply(503,{ok:false,error:'Service unavailable'});
 const method=req.method;
 if(!['GET','POST','PATCH'].includes(method))return reply(405,{ok:false,error:'Method not allowed'});
 try{
  if(method!=='POST'&&!await admin(req.headers.get('x-admin-token')||''))return reply(401,{ok:false,error:'Invalid admin token'});
  if(method==='GET'){const items=await db(table+'?select='+fields+'&order=created_at.desc&limit=500');return reply(200,{ok:true,items})}
  let b;try{b=await limitedBody(req)}catch{return reply(400,{ok:false,error:'Invalid request'})}
  if(method==='PATCH'){
   if(b.action==='register_push'||b.action==='unregister_push'){
    const authHash=hex(await crypto.subtle.digest('SHA-256',enc.encode(req.headers.get('x-admin-token')||'')));
    if(b.action==='unregister_push'){
     const resp=await fetch(base+'/rest/v1/fs_feedback_push_device?slot=eq.true&admin_hash=eq.'+authHash,{method:'DELETE',headers:{apikey:key,...(key.startsWith('sb_secret_')?{}:{Authorization:'Bearer '+key})},signal:AbortSignal.timeout(8000)});
     if(!resp.ok)throw Error('Unregister failed');
     return reply(200,{ok:true});
    }
    const device=typeof b.fcm_token==='string'?b.fcm_token.trim():'';
    if(device.length<20||device.length>4096||!(/^[A-Za-z0-9_:\-]+$/).test(device))return reply(400,{ok:false,error:'Invalid device token'});
    const resp=await fetch(base+'/rest/v1/fs_feedback_push_device?on_conflict=slot',{method:'POST',headers:{apikey:key,...(key.startsWith('sb_secret_')?{}:{Authorization:'Bearer '+key}),'Content-Type':'application/json',Prefer:'resolution=merge-duplicates'},body:JSON.stringify({slot:true,fcm_token:device,admin_hash:authHash}),signal:AbortSignal.timeout(8000)});
    if(!resp.ok)throw Error('Registration failed');
    return reply(200,{ok:true,push_configured:Boolean(Deno.env.get('FEEDBACK_FCM_SERVICE_ACCOUNT'))});
   }
   if(typeof b.id!=='string'||!(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i).test(b.id)||!statuses.has(b.status))return reply(400,{ok:false,error:'Invalid ID or status'});
   const items=await db(table+'?id=eq.'+b.id+'&select='+fields,'PATCH',{status:b.status,admin_note:str(b.admin_note,4000)});
   return items.length?reply(200,{ok:true,item:items[0]}):reply(404,{ok:false,error:'Feedback not found'});
  }
  if(b.website)return reply(400,{ok:false,error:'Invalid submission'});
  const message=typeof b.message==='string'?b.message.trim():'';
  if(!cats.has(b.category)||message.length<3||message.length>4000)return reply(400,{ok:false,error:'Please check category and message'});
  const raw=typeof b.screenshot_url==='string'?b.screenshot_url.trim():'';let ss='';
  if(raw){try{const u=new URL(raw);if(!['http:','https:'].includes(u.protocol)||u.username||u.password||u.href.length>1000)throw Error('link');ss=u.href}catch{return reply(400,{ok:false,error:'Invalid screenshot link'})}}
  const ip=(req.headers.get('cf-connecting-ip')||req.headers.get('x-forwarded-for')||'unknown').split(',').pop()!.trim();
  const hmac=await crypto.subtle.importKey('raw',enc.encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);
  const rate=hex(await crypto.subtle.sign('HMAC',hmac,enc.encode(ip)));
  const id=await db('rpc/fs_submit_website_feedback','POST',{p_category:b.category,p_message:message,p_contact:str(b.contact,200),p_screenshot:ss,p_version:str(b.app_version,100),p_page:'https://pjbuilts.com/floodsafe-nepal/feedback.html',p_agent:str(req.headers.get('user-agent'),500),p_rate:rate});
  if(id){
   const task=pushFeedback(id).catch(e=>console.error('Feedback push failed',e instanceof Error?e.message:'unknown'));
   const runtime=(globalThis as any).EdgeRuntime;
   if(runtime?.waitUntil)runtime.waitUntil(task);else await task;
   return reply(201,{ok:true,id});
  }
  return reply(429,{ok:false,error:'Too many submissions. Try later.'});
 }catch(e){console.error('Feedback request failed',e instanceof Error?e.message:'unknown');return reply(503,{ok:false,error:'Feedback service temporarily unavailable'});}
});
