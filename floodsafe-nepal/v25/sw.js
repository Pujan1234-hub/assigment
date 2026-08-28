const CACHE='floodsafe-nepal-v25-shell-24';
const SHELL=['./','./index.html','./map.html','./alerts.html','./people.html','./weather.html','./news.html','./sources.html','./shell.css','./live-core.css','./resilience.js','./live-core.js','./national-news.js','./disaster-monitor.js','./today-monitor-v3.js','./human-current-guard.js','./district-road-live.js','./road-current-guard.js','./realtime-1s.js','./weather-live.js','./manifest.webmanifest','../v24/icon.svg'];
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await Promise.allSettled(SHELL.map(async u=>{try{const r=await fetch(u,{cache:'reload'});if(r.ok)await c.put(u,r)}catch(_){}}));await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-v25-')&&k!==CACHE).map(k=>caches.delete(k)));await self.clients.claim();const list=await self.clients.matchAll({type:'window',includeUncontrolled:true});for(const c of list){try{const u=new URL(c.url);if(u.origin===self.location.origin&&/\/floodsafe-nepal\/v25\//.test(u.pathname))c.navigate(c.url)}catch(_){}}})()));
async function fetchWithTimeout(request,ms=4000){const c=new AbortController(),to=setTimeout(()=>c.abort(),ms);try{return await fetch(request,{cache:'no-store',signal:c.signal})}finally{clearTimeout(to)}}
async function staticAsset(request){const c=await caches.open(CACHE),hit=await c.match(request,{ignoreSearch:true});const net=fetchWithTimeout(request,3500).then(async r=>{if(r&&r.ok){const key=new Request(new URL(request.url).origin+new URL(request.url).pathname);await c.put(key,r.clone())}return r}).catch(()=>null);if(hit){net.catch(()=>{});return hit}const r=await net;if(r)return r;throw Error('static unavailable')}
async function networkFirst(request,ms=4000){const c=await caches.open(CACHE);try{const r=await fetchWithTimeout(request,ms);if(r&&r.ok){const u=new URL(request.url),key=new Request(u.origin+u.pathname);await c.put(key,r.clone())}return r}catch(e){const hit=await c.match(request,{ignoreSearch:true});if(hit)return hit;throw e}}
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  if(u.origin!==location.origin)return;
  if(/\/data\/.*\.json$/.test(u.pathname)){e.respondWith(networkFirst(e.request,4500));return}
  if(/\.(?:js|css)$/.test(u.pathname)){e.respondWith(staticAsset(e.request));return}
  if(e.request.mode==='navigate'||/\.html$|\/v25\/?$/.test(u.pathname)){e.respondWith(networkFirst(e.request,3500));return}
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(hit=>hit||fetchWithTimeout(e.request,4500).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(new Request(u.origin+u.pathname),cp))}return r})));
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c&&/floodsafe-nepal/.test(c.url))return c.focus()}return clients.openWindow('./alerts.html')}))});
