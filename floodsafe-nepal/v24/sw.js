const CACHE='floodsafe-nepal-v24-shell-20';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg','./v23-hotfix.js','./v23-lang-police.js','./v23-river-map-v3.js','./v24-river-display.js','./v24-my-area-weather.js','./v24-authority-watch.js','./v24-map-alert.js','./v24-realtime-1s.js','./v24-safety-guard.js','./v24-upgrade.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('floodsafe-nepal-v24-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  if(u.origin!==location.origin)return;
  if(/\/v2[34]\/v23-upgrade\.js$/.test(u.pathname)){
    e.respondWith(Promise.all([
      fetch(e.request,{cache:'no-store'}),
      fetch('./v23-hotfix.js?v=4',{cache:'no-store'}),
      fetch('./v24-safety-guard.js?v=2',{cache:'no-store'}),
      fetch('./v23-lang-police.js?v=5',{cache:'no-store'}),
      fetch('./v24-river-display.js?v=2',{cache:'no-store'}),
      fetch('./v24-my-area-weather.js?v=1',{cache:'no-store'}),
      fetch('./v24-authority-watch.js?v=4',{cache:'no-store'}),
      fetch('./v24-map-alert.js?v=1',{cache:'no-store'}),
      fetch('./v24-realtime-1s.js?v=2',{cache:'no-store'})
    ]).then(async([base,hot,guard,live,riverDisplay,myWeather,authorityWatch,mapAlert,realtime])=>{
      if(!base.ok)throw Error('base '+base.status);
      const a=await base.text(),b=hot.ok?await hot.text():'',c=guard.ok?await guard.text():'',d=live.ok?await live.text():'',e=riverDisplay.ok?await riverDisplay.text():'',f=myWeather.ok?await myWeather.text():'',g=authorityWatch.ok?await authorityWatch.text():'',h=mapAlert.ok?await mapAlert.text():'',i=realtime.ok?await realtime.text():'';
      return new Response(a+'\n;'+b+'\n;'+c+'\n;'+d+'\n;'+e+'\n;'+f+'\n;'+g+'\n;'+h+'\n;'+i,{status:200,headers:{'Content-Type':'application/javascript; charset=utf-8','Cache-Control':'no-store'}});
    }).catch(()=>fetch(e.request)));
    return;
  }
  e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html'))));
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(ws=>ws[0]?ws[0].focus():clients.openWindow('./')))});