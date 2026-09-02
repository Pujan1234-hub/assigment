// Notification-only worker: no fetch handler, no page or river-data caching.
const DB='floodsafe-rain-settings-v1';
function settings(value){return new Promise((resolve,reject)=>{const req=indexedDB.open(DB,1);req.onupgradeneeded=()=>req.result.createObjectStore('settings');req.onerror=()=>reject(req.error);req.onsuccess=()=>{const db=req.result,tx=db.transaction('settings',value?'readwrite':'readonly'),store=tx.objectStore('settings');let result;if(value)store.put(value,'current');else{const read=store.get('current');read.onsuccess=()=>{result=read.result}}tx.oncomplete=()=>{db.close();resolve(result)};tx.onerror=()=>{db.close();reject(tx.error)}}})}
self.addEventListener('install',event=>event.waitUntil(self.skipWaiting()));
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('message',event=>{if(event.data?.type==='rain-settings')event.waitUntil(settings(event.data).then(()=>event.ports?.[0]?.postMessage({ok:true})).catch(()=>event.ports?.[0]?.postMessage({ok:false})))});
self.addEventListener('push',event=>event.waitUntil((async()=>{
  let message;try{message=event.data?.json()}catch{return}
  const config=await settings().catch(()=>null),now=Date.now();
  if(!message||!config?.enabled||config.id!==message.id||!Number.isFinite(config.expiresAt)||!Number.isFinite(message.expiresAt)||config.expiresAt<=now||message.expiresAt<=now||message.key!==config.key)return;
  await self.registration.showNotification(String(message.title||'FloodSafe rain forecast').slice(0,160),{body:String(message.body||'').slice(0,700),icon:'../v24/icon.svg',tag:String(message.tag||'rain-forecast').slice(0,100),renotify:false,timestamp:now,data:{url:new URL('./',self.registration.scope).href},vibrate:[100,60,100]});
})()));
self.addEventListener('notificationclick',event=>{event.notification.close();event.waitUntil((async()=>{const url=new URL('./',self.registration.scope).href;for(const client of await self.clients.matchAll({type:'window',includeUncontrolled:true})){if(client.url.startsWith(url)){await client.focus();return}}await self.clients.openWindow(url)})())});
