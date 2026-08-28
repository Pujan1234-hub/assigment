const CACHE='floodsafe-nepal-v25-shell-23';
const SHELL=['./','./index.html','./map.html','./alerts.html','./people.html','./weather.html','./news.html','./sources.html','./shell.css','./live-core.css','./resilience.js','./live-core.js','./national-news.js','./disaster-monitor.js','./today-monitor-v3.js','./human-current-guard.js','./district-road-live.js','./road-current-guard.js','./realtime-1s.js','./weather-live.js','./manifest.webmanifest','../v24/icon.svg'];
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await Promise.allSettled(SHELL.map(async u=>{try{const r=await fetch(u,{cache:'reload'});if(r.ok)await c.put(u,r)}catch(_){}}));await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-v25-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
async function networkFirst(request){const c=await caches.open(CACHE);try{const r=await fetch(request,{cache:'no-store'});if(r&&r.ok)await c.put(request,r.clone());return r}catch(e){const hit=await c.match(request);if(hit)return hit;throw e}}
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  if(u.origin!==location.origin)return;
  if(/\/data\/.*\.json$/.test(u.pathname)){e.respondWith(fetch(e.request,{cache:'no-store'}));return}
  if(/\.(?:js|css)$/.test(u.pathname)||/\.html$|\/v25\/?$/.test(u.pathname)){e.respondWith(networkFirst(e.request));return}
  e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp))}return r})));
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(list=>{for(const c of list){if('focus'in c&&/floodsafe-nepal/.test(c.url))return c.focus()}return clients.openWindow('./alerts.html')}))});
