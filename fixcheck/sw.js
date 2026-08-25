const CACHE='fixcheck-v05';
const ASSETS=['./','./index.html','./manifest.webmanifest','./favicon.svg','./auto.js','./trust.js'];

self.addEventListener('install',e=>e.waitUntil(
  caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())
));

self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))
));

async function enhanceHtml(response){
  const type=response.headers.get('content-type')||'';
  if(!type.includes('text/html')) return response;
  let html=await response.text();
  if(!html.includes('auto.js')) html=html.replace('</body>','<script src="./auto.js?v=5"></script></body>');
  if(!html.includes('trust.js')) html=html.replace('</body>','<script src="./trust.js?v=5"></script></body>');
  const headers=new Headers(response.headers);
  headers.delete('content-length');
  headers.delete('content-encoding');
  return new Response(html,{status:response.status,statusText:response.statusText,headers});
}

self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  if(e.request.mode==='navigate'){
    e.respondWith((async()=>{
      try{
        const network=await fetch(e.request,{cache:'no-store'});
        const page=await enhanceHtml(network.clone());
        const cache=await caches.open(CACHE);
        cache.put('./index.html',page.clone()).catch(()=>{});
        return page;
      }catch{
        const cached=await caches.match('./index.html');
        return cached?enhanceHtml(cached):Response.error();
      }
    })());
    return;
  }
  e.respondWith(fetch(e.request).then(r=>{
    const copy=r.clone();
    caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});
    return r;
  }).catch(()=>caches.match(e.request)));
});
