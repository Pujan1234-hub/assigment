const CACHE='fixcheck-v13';
const ASSETS=['./','./index.html','./manifest.webmanifest','./favicon.svg','./ping.txt'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  if(e.request.mode==='navigate'){
    e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{const c=r.clone();caches.open(CACHE).then(x=>x.put('./index.html',c)).catch(()=>{});return r}).catch(()=>caches.match('./index.html')));
    return;
  }
  const noStore=e.request.url.includes('ping.txt');
  e.respondWith(fetch(e.request,{cache:noStore?'no-store':'default'}).then(r=>{const c=r.clone();if(!noStore)caches.open(CACHE).then(x=>x.put(e.request,c)).catch(()=>{});return r}).catch(()=>caches.match(e.request)));
});
