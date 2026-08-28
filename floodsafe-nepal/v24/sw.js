const CACHE='floodsafe-nepal-v24-shell-24';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg','./v23-hotfix.js','./v23-lang-police.js','./v23-river-map-v3.js','./v24-river-source-guard.js','./v24-river-display.js','./v24-my-area-weather.js','./v24-authority-watch.js','./v24-map-alert.js','./v24-realtime-1s.js','./v24-safety-guard.js','./v24-upgrade.js'];
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(CACHE);await Promise.allSettled(SHELL.map(async u=>{try{const r=await fetch(u,{cache:'reload'});if(r.ok)await c.put(u,r)}catch(_){}}));await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{const keys=await caches.keys();await Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-v24-')&&k!==CACHE).map(k=>caches.delete(k)));await self.clients.claim()})()));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  if(u.origin!==location.origin)return;
  if(/\/v2[34]\/v23-upgrade\.js$/.test(u.pathname)){
    e.respondWith(Promise.all([
      fetch('./v24-river-source-guard.js?v=1',{cache:'no-store'}),
      fetch(e.request,{cache:'no-store'}),
      fetch('./v23-hotfix.js?v=4',{cache:'no-store'}),
      fetch('./v24-safety-guard.js?v=2',{cache:'no-store'}),
      fetch('./v23-lang-police.js?v=5',{cache:'no-store'}),
      fetch('./v23-river-map-v3.js?v=4',{cache:'no-store'}),
      fetch('./v24-river-display.js?v=4',{cache:'no-store'}),
      fetch('./v24-my-area-weather.js?v=1',{cache:'no-store'}),
      fetch('./v24-authority-watch.js?v=4',{cache:'no-store'}),
      fetch('./v24-map-alert.js?v=1',{cache:'no-store'}),
      fetch('./v24-realtime-1s.js?v=4',{cache:'no-store'})
    ]).then(async([riverGuard,base,hot,guard,live,riverV3,riverDisplay,myWeather,authorityWatch,mapAlert,realtime])=>{
      if(!base.ok)throw Error('base '+base.status);
      const parts=[];
      if(riverGuard.ok)parts.push(await riverGuard.text());
      parts.push(await base.text());
      for(const r of [hot,guard,live,riverV3,riverDisplay,myWeather,authorityWatch,mapAlert,realtime])if(r.ok)parts.push(await r.text());
      return new Response(parts.join('\n;\n'),{status:200,headers:{'Content-Type':'application/javascript; charset=utf-8','Cache-Control':'no-store'}});
    }).catch(()=>fetch(e.request,{cache:'no-store'})));
    return;
  }
  e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(new Request(u.origin+u.pathname),cp))}return r}).catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('./index.html'))));
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(ws=>ws[0]?ws[0].focus():clients.openWindow('./')))});