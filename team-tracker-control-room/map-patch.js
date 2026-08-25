/* Team Tracker Control Room — single detailed satellite map, Aug 2026.
   Satellite imagery stays visible while road/place reference layers and the official
   Princesshay June 2026 shop directory are drawn directly on top. No map-mode selector. */
(() => {
  const SITE={lat:50.72474,lon:-3.52792,label:'Princesshay'};
  let view={lat:SITE.lat,lon:SITE.lon,zoom:18,manual:false};
  let lastStaffSet='',lastBaseSig='',drag=null;

  // Current store names cross-checked against Princesshay's JUN 2026 centre map.
  // Coordinates are local storefront-label anchors aligned to the centre layout.
  const SHOPS=[
    {n:'Waterstones',lat:50.725571,lon:-3.527912,m:true},{n:'Halifax',lat:50.725468,lon:-3.527868},{n:'Boots',lat:50.725399,lon:-3.527838,m:true},{n:'HSBC',lat:50.725322,lon:-3.528028},{n:'Card Factory',lat:50.725266,lon:-3.528140},
    {n:'Artigiano Café',lat:50.725190,lon:-3.528305},{n:'Specsavers',lat:50.725150,lon:-3.528437},{n:'Hotel Chocolat',lat:50.725223,lon:-3.528345,m:true},{n:'itsu',lat:50.725193,lon:-3.528232},{n:'Pret',lat:50.725155,lon:-3.528291},
    {n:'Lush',lat:50.724968,lon:-3.528172,m:true},{n:'Charles Tyrwhitt',lat:50.725076,lon:-3.528070},{n:'Sweaty Betty',lat:50.725027,lon:-3.527987},{n:"Fulford's",lat:50.724961,lon:-3.527860},
    {n:'Build-A-Bear',lat:50.724811,lon:-3.527683,m:true},{n:'Starbucks',lat:50.724718,lon:-3.527829,m:true},{n:'Suit Direct',lat:50.724611,lon:-3.527882},{n:'Lucy & Yak',lat:50.724660,lon:-3.527990},
    {n:'Sports Direct',lat:50.724836,lon:-3.526975,m:true},{n:'River Island',lat:50.724908,lon:-3.527415,m:true},{n:'Zara',lat:50.724955,lon:-3.527088,m:true},{n:'Next',lat:50.725219,lon:-3.527016,m:true},
    {n:'New Look',lat:50.724840,lon:-3.527430,m:true},{n:'FatFace',lat:50.724660,lon:-3.527260,m:true},{n:'Salt Rock',lat:50.724613,lon:-3.528316},{n:'Pandora',lat:50.724552,lon:-3.527584,m:true},
    {n:'Rituals',lat:50.724391,lon:-3.528159,m:true},{n:"Victoria's Secret",lat:50.724512,lon:-3.527715,m:true},{n:"Levi's",lat:50.724543,lon:-3.527828,m:true},{n:'Lloyds Bank',lat:50.724558,lon:-3.528380},
    {n:'Apple',lat:50.724470,lon:-3.527920,m:true},{n:'Clarks',lat:50.724600,lon:-3.528199,m:true},{n:'Beaverbrooks',lat:50.724404,lon:-3.527817},{n:'Vision Express',lat:50.724490,lon:-3.528325},
    {n:'JD Sports',lat:50.724546,lon:-3.528238,m:true},{n:'ProCook',lat:50.724251,lon:-3.528173,m:true},{n:'Schuh',lat:50.724221,lon:-3.528036,m:true},{n:'Smiggle',lat:50.724172,lon:-3.527952},
    {n:'AllSaints',lat:50.724154,lon:-3.528441},{n:'Oliver Bonas',lat:50.724030,lon:-3.528474},{n:'Reiss',lat:50.723926,lon:-3.528454},{n:'Moss',lat:50.724206,lon:-3.527484,m:true},
    {n:'HMV',lat:50.724234,lon:-3.527694,m:true},{n:'Hollister',lat:50.724038,lon:-3.527795,m:true},{n:'Superdry',lat:50.724350,lon:-3.527700,m:true},{n:'Crew Clothing',lat:50.724476,lon:-3.527266},
    {n:'Clarendon Fine Art',lat:50.724420,lon:-3.527378},{n:'Chandos Deli',lat:50.724376,lon:-3.527148},{n:'Coffee #1',lat:50.724069,lon:-3.527400},{n:'Slim Chickens',lat:50.724534,lon:-3.527129,m:true},
    {n:'EE',lat:50.723987,lon:-3.528703},{n:'Hotter Shoes',lat:50.724073,lon:-3.528753},{n:'Nationwide',lat:50.724123,lon:-3.528811},{n:"Lloyd's Lounge",lat:50.723978,lon:-3.528947},
    {n:'YO! Sushi',lat:50.723875,lon:-3.528903},{n:'Costa Coffee',lat:50.723826,lon:-3.528795},{n:'Wagamama',lat:50.723667,lon:-3.528862,m:true},{n:'Bravissimo',lat:50.723593,lon:-3.528012},
    {n:'Hanlees',lat:50.723819,lon:-3.527564},{n:'Pop Kitchen',lat:50.723787,lon:-3.527476},{n:'12 Bar Music & Social',lat:50.725213,lon:-3.526704},{n:'Space NK',lat:50.724503,lon:-3.527500,m:true},
    {n:'Goldsmiths',lat:50.724575,lon:-3.527420},{n:'Accessorizе',lat:50.724590,lon:-3.527500},{n:'Saks',lat:50.724440,lon:-3.527870},{n:'The Watch Lab',lat:50.724445,lon:-3.527760}
  ];

  const ROADS=[
    {n:'HIGH STREET',lat:50.724840,lon:-3.528328,r:-22},{n:'PRINCESSHAY',lat:50.724489,lon:-3.527866,r:-25},{n:'EASTGATE',lat:50.725019,lon:-3.527240,r:58},
    {n:'ROMAN WALK',lat:50.724428,lon:-3.527158,r:-82},{n:'SOUTHERNHAY WEST',lat:50.723930,lon:-3.526906,r:-79},{n:'CHAPEL STREET',lat:50.723561,lon:-3.527924,r:0},
    {n:'CATHERINE SQUARE',lat:50.723765,lon:-3.529029,r:-38},{n:'PARIS STREET',lat:50.725291,lon:-3.526489,r:55},{n:'SIDWELL STREET',lat:50.725720,lon:-3.526228,r:50},
    {n:'NEW NORTH ROAD',lat:50.725647,lon:-3.527263,r:47},{n:'BEDFORD STREET',lat:50.724373,lon:-3.528671,r:-35},{n:'BLUE BOY SQUARE',lat:50.724697,lon:-3.526964,r:0},
    {n:'PRINCESSHAY SQUARE',lat:50.723785,lon:-3.528492,r:0}
  ];

  const css=document.createElement('style');
  css.textContent=`
  #mapbox.tt-live-map{position:relative;height:400px;overflow:hidden;padding:0;background:#111;border:1px solid #2b465d;border-radius:14px;touch-action:none;cursor:grab}
  #mapbox.tt-live-map.dragging{cursor:grabbing}.tt-pan{position:absolute;inset:0;will-change:transform}.tt-layer{position:absolute;inset:0;pointer-events:none}.tt-tile{position:absolute;width:256px;height:256px;max-width:none;user-select:none;-webkit-user-drag:none}
  .tt-osm-detail{opacity:.30;mix-blend-mode:multiply;filter:grayscale(1) contrast(2.1) brightness(1.32)}
  .tt-chip{position:absolute;top:10px;left:10px;z-index:70;background:rgba(4,15,25,.92);color:#fff;border:1px solid #526c7f;border-radius:10px;padding:7px 9px;font:800 11px/1.2 system-ui;pointer-events:none;box-shadow:0 3px 12px rgba(0,0,0,.35)}.tt-chip span{display:block;color:#c8d4dc;font-weight:650;margin-top:2px}
  .tt-controls{position:absolute;right:10px;top:10px;z-index:75;display:flex;gap:5px}.tt-map-btn{width:38px;height:38px;border:1px solid #5a7183;background:rgba(5,21,34,.94);color:#fff;border-radius:9px;font:900 19px/1 system-ui;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.3)}
  .tt-road{position:absolute;z-index:26;transform:translate(-50%,-50%);color:#fff;font:900 9px/1 system-ui;letter-spacing:.09em;text-shadow:0 1px 2px #000,0 0 4px #000,0 0 7px #000;white-space:nowrap;pointer-events:none;opacity:.92}
  .tt-shop{position:absolute;z-index:32;transform:translate(-50%,-50%);white-space:nowrap;padding:2px 4px;border-radius:4px;background:rgba(5,14,23,.76);border:1px solid rgba(255,255,255,.42);color:#fff;font:800 8px/1.05 system-ui;letter-spacing:.01em;text-shadow:0 1px 1px #000;box-shadow:0 1px 3px rgba(0,0,0,.35);pointer-events:none}
  .tt-shop.major{background:rgba(4,16,27,.88);border-color:rgba(239,182,50,.9);color:#fff;font-size:8.5px}.tt-shop.major:before{content:'•';color:#efb632;margin-right:3px}
  .tt-pin{position:absolute;z-index:55;transform:translate(-50%,-100%);text-decoration:none;color:#fff;filter:drop-shadow(0 4px 6px rgba(0,0,0,.7))}.tt-pin-dot{width:32px;height:32px;border-radius:50% 50% 50% 8px;transform:rotate(-45deg);background:#efb632;border:3px solid #fff}.tt-pin-dot:after{content:'';position:absolute;width:8px;height:8px;border-radius:50%;background:#102235;left:9px;top:9px}.tt-pin.site .tt-pin-dot{width:25px;height:25px;background:#48a9e6}.tt-pin-label{position:absolute;left:50%;top:-37px;transform:translateX(-50%);white-space:nowrap;background:rgba(5,20,32,.96);color:#fff;border:1px solid #6c879b;border-radius:7px;padding:3px 6px;font:800 10px system-ui}.tt-pin.site .tt-pin-label{top:-31px}
  .tt-attrib{position:absolute;right:6px;bottom:5px;z-index:72;background:rgba(255,255,255,.9);color:#263844;border-radius:5px;padding:2px 5px;font:9px system-ui}.tt-attrib a{color:#245b83;text-decoration:none}
  @media(max-width:700px){#mapbox.tt-live-map{height:380px}.tt-shop{font-size:7px;padding:2px 3px}.tt-shop.major{font-size:7.5px}.tt-road{font-size:8px}.tt-chip{max-width:190px}.tt-controls{right:8px;top:8px}.tt-map-btn{width:36px;height:36px}}
  `;
  document.head.appendChild(css);

  const wp=(lat,lon,z)=>{const size=256*2**z,x=(lon+180)/360*size,s=Math.sin(lat*Math.PI/180),y=(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*size;return{x,y}};
  const ll=(x,y,z)=>{const size=256*2**z,lon=x/size*360-180,n=Math.PI-2*Math.PI*y/size,lat=180/Math.PI*Math.atan(.5*(Math.exp(n)-Math.exp(-n)));return{lat,lon}};
  const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
  const getGps=()=>((typeof rows!=='undefined'&&Array.isArray(rows))?rows:[]).map(r=>({r,lat:num(r.latitude),lon:num(r.longitude)})).filter(p=>p.lat!==null&&p.lon!==null);
  const staffSet=g=>g.map(p=>p.r.staff_id).sort().join('|');

  function chooseZoom(g){if(!g.length)return 18;let a=g[0].lat,b=a,c=g[0].lon,d=c;g.forEach(p=>{a=Math.min(a,p.lat);b=Math.max(b,p.lat);c=Math.min(c,p.lon);d=Math.max(d,p.lon)});const s=Math.max(b-a,(d-c)*.65);return s<.00045?19:s<.001?18:s<.0024?17:s<.005?16:15}
  function fitWhenStaffChanges(g){const k=staffSet(g);if(k===lastStaffSet)return;lastStaffSet=k;if(view.manual)return;if(g.length){view.lat=g.reduce((a,p)=>a+p.lat,0)/g.length;view.lon=g.reduce((a,p)=>a+p.lon,0)/g.length;view.zoom=chooseZoom(g)}else{view.lat=SITE.lat;view.lon=SITE.lon;view.zoom=18}}
  function tile(layer,px,py,src,cls=''){const im=document.createElement('img');im.className='tt-tile '+cls;im.alt='';im.decoding='async';im.loading='eager';im.src=src;im.style.left=px+'px';im.style.top=py+'px';layer.appendChild(im)}

  function addTiles(parent,left,top,w,h,z){const n=2**z,minX=Math.floor(left/256)-1,maxX=Math.floor((left+w)/256)+1,minY=Math.max(0,Math.floor(top/256)-1),maxY=Math.min(n-1,Math.floor((top+h)/256)+1);
    const imagery=document.createElement('div');imagery.className='tt-layer';parent.appendChild(imagery);
    const transport=document.createElement('div');transport.className='tt-layer';parent.appendChild(transport);
    const places=document.createElement('div');places.className='tt-layer';parent.appendChild(places);
    const osm=document.createElement('div');osm.className='tt-layer';parent.appendChild(osm);
    for(let tx=minX;tx<=maxX;tx++)for(let ty=minY;ty<=maxY;ty++){const x=((tx%n)+n)%n,px=tx*256-left,py=ty*256-top;
      tile(imagery,px,py,`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${ty}/${x}`);
      tile(transport,px,py,`https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/${z}/${ty}/${x}`);
      tile(places,px,py,`https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/${z}/${ty}/${x}`);
      if(z>=18)tile(osm,px,py,`https://tile.openstreetmap.org/${z}/${x}/${ty}.png`,'tt-osm-detail');
    }
  }

  function placeText(parent,item,left,top,z,cls,rotate=0){const p=wp(item.lat,item.lon,z),d=document.createElement('div');d.className=cls;d.style.left=(p.x-left)+'px';d.style.top=(p.y-top)+'px';if(rotate)d.style.transform=`translate(-50%,-50%) rotate(${rotate}deg)`;d.textContent=item.n;parent.appendChild(d)}
  function addReferenceLabels(parent,left,top,z){
    if(z>=17)ROADS.forEach(r=>placeText(parent,r,left,top,z,'tt-road',r.r||0));
    SHOPS.forEach(s=>{if((z>=19)||(z>=18&&s.m))placeText(parent,s,left,top,z,'tt-shop'+(s.m?' major':''),0)});
  }
  function addPin(parent,lat,lon,label,left,top,z,site=false){const p=wp(lat,lon,z),a=document.createElement('div');a.className='tt-pin'+(site?' site':'');a.style.left=(p.x-left)+'px';a.style.top=(p.y-top)+'px';a.innerHTML=`<span class="tt-pin-label">${typeof esc==='function'?esc(label):label}</span><span class="tt-pin-dot"></span>`;parent.appendChild(a)}

  function updateStaffLayer(box,left,top,z,g){let layer=box.querySelector('.tt-staff-layer');if(!layer){layer=document.createElement('div');layer.className='tt-layer tt-staff-layer';const pan=box.querySelector('.tt-pan');pan&&pan.appendChild(layer)}layer.innerHTML='';addPin(layer,SITE.lat,SITE.lon,SITE.label,left,top,z,true);g.forEach(p=>{let label='STAFF';try{label=(typeof badge==='function'?badge(p.r):'STAFF')+(p.r.real_name?` • ${p.r.real_name}`:'')}catch{}addPin(layer,p.lat,p.lon,label,left,top,z,false)})}

  function draw(force=false){if(drag&&!force)return;const box=document.getElementById('mapbox');if(!box)return;const g=getGps();fitWhenStaffChanges(g);const w=Math.max(box.clientWidth||320,280),h=Math.max(box.clientHeight||380,300),z=view.zoom,c=wp(view.lat,view.lon,z),left=c.x-w/2,top=c.y-h/2;const baseSig=`${view.lat.toFixed(6)}|${view.lon.toFixed(6)}|${z}|${w}|${h}`;
    if(force||baseSig!==lastBaseSig||!box.querySelector('.tt-pan')){lastBaseSig=baseSig;box.className='mapbox tt-live-map';box.innerHTML='';const pan=document.createElement('div');pan.className='tt-pan';box.appendChild(pan);addTiles(pan,left,top,w,h,z);addReferenceLabels(pan,left,top,z);const staff=document.createElement('div');staff.className='tt-layer tt-staff-layer';pan.appendChild(staff);
      const chip=document.createElement('div');chip.className='tt-chip';chip.innerHTML=g.length?`SATELLITE LIVE • ${g.length} GPS<span>2026 Princesshay shops + roads</span>`:`SATELLITE • PRINCESSHAY<span>2026 shops + roads • no on-shift GPS</span>`;box.appendChild(chip);
      const controls=document.createElement('div');controls.className='tt-controls';controls.innerHTML='<button class="tt-map-btn" data-a="in" aria-label="Zoom in">+</button><button class="tt-map-btn" data-a="out" aria-label="Zoom out">−</button><button class="tt-map-btn" data-a="home" aria-label="Recenter">◎</button>';box.appendChild(controls);controls.onpointerdown=e=>e.stopPropagation();controls.onclick=e=>{const a=e.target?.dataset?.a;if(!a)return;if(a==='in')view.zoom=Math.min(20,view.zoom+1);if(a==='out')view.zoom=Math.max(15,view.zoom-1);if(a==='home'){view.manual=false;lastStaffSet='';fitWhenStaffChanges(getGps())}else view.manual=true;lastBaseSig='';draw(true)};
      const at=document.createElement('div');at.className='tt-attrib';at.innerHTML='Imagery/roads © Esri • shop detail: Princesshay JUN 2026 + © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';box.appendChild(at);
      box.onpointerdown=e=>{if(e.target.closest('.tt-controls'))return;const panEl=box.querySelector('.tt-pan');drag={x:e.clientX,y:e.clientY,c:wp(view.lat,view.lon,view.zoom),pan:panEl,pid:e.pointerId};box.classList.add('dragging');box.setPointerCapture?.(e.pointerId)};box.onpointermove=e=>{if(!drag||e.pointerId!==drag.pid)return;drag.pan.style.transform=`translate(${e.clientX-drag.x}px,${e.clientY-drag.y}px)`};const end=e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y,p=ll(drag.c.x-dx,drag.c.y-dy,view.zoom);view.lat=p.lat;view.lon=p.lon;view.manual=true;drag=null;box.classList.remove('dragging');lastBaseSig='';draw(true)};box.onpointerup=end;box.onpointercancel=end;
    }
    // Live poll only moves staff markers; it does not rebuild satellite tiles or shop labels.
    const c2=wp(view.lat,view.lon,view.zoom),left2=c2.x-w/2,top2=c2.y-h/2;updateStaffLayer(box,left2,top2,view.zoom,g);
  }

  window.renderLocations=()=>draw(false);
  try{if(document.getElementById('app')&&!document.getElementById('app').classList.contains('hidden'))draw(true)}catch{}
})();