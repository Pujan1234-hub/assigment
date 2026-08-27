const CACHE='floodsafe-nepal-v24-shell-7';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg','./v23-hotfix.js','./v23-lang-police.js','./v23-river-map-v3.js','./v24-safety-guard.js','./v24-upgrade.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()).then(()=>self.clients.matchAll({type:'window',includeUncontrolled:true})).then(ws=>Promise.all(ws.map(w=>{try{return w.navigate(w.url)}catch{return null}})))));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  if(u.origin!==location.origin)return;
  if(/\/v2[34]\/v23-upgrade\.js$/.test(u.pathname)){
    e.respondWith(Promise.all([
      fetch(e.request,{cache:'no-store'}),
      fetch('./v23-hotfix.js?v=4',{cache:'no-store'}),
      fetch('./v24-safety-guard.js?v=2',{cache:'no-store'}),
      fetch('./v23-lang-police.js?v=5',{cache:'no-store'})
    ]).then(async([base,hot,guard,live])=>{
      if(!base.ok)throw Error('base '+base.status);
      const a=await base.text(),b=hot.ok?await hot.text():'',c=guard.ok?await guard.text():'',d=live.ok?await live.text():'';
      return new Response(a+'\n;'+b+'\n;'+c+'\n;'+d,{status:200,headers:{'Content-Type':'application/javascript; charset=utf-8','Cache-Control':'no-store'}});
    }).catch(()=>fetch(e.request)));
    return;
  }
  e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html'))));
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(ws=>ws[0]?ws[0].focus():clients.openWindow('./')))});
