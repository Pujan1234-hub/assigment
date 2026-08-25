/* Team Tracker Control Room — smooth HYBRID / SATELLITE / STREET live map.
   Hybrid = satellite imagery + detailed OpenStreetMap labels/roads/POIs. */
(() => {
  const SITE={lat:50.72474,lon:-3.52792,label:'Princesshay'};
  let view={lat:SITE.lat,lon:SITE.lon,zoom:18,manual:false};
  let mode='hybrid', lastGpsKey='', lastSig='', drag=null;

  const style=document.createElement('style');
  style.textContent=`
  #mapbox.tt-live-map{position:relative;height:380px;overflow:hidden;padding:0;background:#111;border:1px solid #2b465d;border-radius:14px;touch-action:none;cursor:grab}
  #mapbox.tt-live-map.dragging{cursor:grabbing}.tt-pan{position:absolute;inset:0;will-change:transform}.tt-layer{position:absolute;inset:0;pointer-events:none}.tt-tile{position:absolute;width:256px;height:256px;max-width:none;user-select:none;-webkit-user-drag:none}.tt-hybrid-detail{opacity:.56;filter:saturate(.9) contrast(1.08)}
  .tt-chip{position:absolute;top:10px;left:10px;z-index:50;background:rgba(4,15,25,.92);color:#fff;border:1px solid #46647a;border-radius:10px;padding:7px 9px;font:800 11px/1.2 system-ui;pointer-events:none}.tt-chip span{display:block;color:#b9c7d2;font-weight:600;margin-top:2px}
  .tt-controls{position:absolute;right:10px;top:10px;z-index:60;display:flex;flex-direction:column;gap:6px;align-items:flex-end}.tt-mode{display:flex;gap:4px;background:rgba(4,15,25,.92);padding:4px;border:1px solid #46647a;border-radius:10px}.tt-mode button,.tt-map-btn{border:1px solid #48667d;background:#0a1b29;color:#fff;border-radius:8px;font-weight:800;cursor:pointer}.tt-mode button{padding:7px 8px;font-size:10px}.tt-mode button.active{background:#efb632;color:#171105;border-color:#efb632}.tt-zoom{display:flex;gap:5px}.tt-map-btn{width:38px;height:38px;font-size:19px}
  .tt-pin{position:absolute;z-index:40;transform:translate(-50%,-100%);text-decoration:none;color:#fff;filter:drop-shadow(0 3px 5px rgba(0,0,0,.55))}.tt-pin-dot{width:31px;height:31px;border-radius:50% 50% 50% 8px;transform:rotate(-45deg);background:#efb632;border:3px solid #fff}.tt-pin-dot:after{content:'';position:absolute;width:8px;height:8px;border-radius:50%;background:#102235;left:8px;top:8px}.tt-pin.site .tt-pin-dot{width:25px;height:25px;background:#48a9e6}.tt-label{position:absolute;left:50%;top:-36px;transform:translateX(-50%);white-space:nowrap;background:rgba(5,20,32,.94);color:#fff;border:1px solid #66839a;border-radius:7px;padding:3px 6px;font:800 10px system-ui}.tt-pin.site .tt-label{top:-31px}.tt-attrib{position:absolute;right:6px;bottom:5px;z-index:55;background:rgba(255,255,255,.9);color:#263844;border-radius:5px;padding:2px 5px;font:10px system-ui}.tt-attrib a{color:#245b83;text-decoration:none}
  @media(max-width:700px){#mapbox.tt-live-map{height:350px}.tt-controls{top:8px;right:8px}.tt-mode button{padding:6px 6px;font-size:9px}.tt-label{max-width:125px;overflow:hidden;text-overflow:ellipsis}}
  `;
  document.head.appendChild(style);

  const wp=(lat,lon,z)=>{const size=256*2**z,x=(lon+180)/360*size,s=Math.sin(lat*Math.PI/180),y=(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*size;return{x,y}};
  const ll=(x,y,z)=>{const size=256*2**z,lon=x/size*360-180,n=Math.PI-2*Math.PI*y/size,lat=180/Math.PI*Math.atan(.5*(Math.exp(n)-Math.exp(-n)));return{lat,lon}};
  const num=v=>{const n=Number(v);return Number.isFinite(n)?n:null};
  const gps=()=>((typeof rows!=='undefined'&&Array.isArray(rows))?rows:[]).map(r=>({r,lat:num(r.latitude),lon:num(r.longitude)})).filter(p=>p.lat!==null&&p.lon!==null);
  const gpsKey=g=>g.map(p=>`${p.r.staff_id}:${p.lat.toFixed(5)},${p.lon.toFixed(5)}`).join('|');
  const chooseZoom=g=>{if(!g.length)return 18;let a=g[0].lat,b=a,c=g[0].lon,d=c;g.forEach(p=>{a=Math.min(a,p.lat);b=Math.max(b,p.lat);c=Math.min(c,p.lon);d=Math.max(d,p.lon)});const s=Math.max(b-a,(d-c)*.65);return s<.00045?19:s<.001?18:s<.0024?17:s<.005?16:15};
  function fit(g){const k=gpsKey(g);if(k!==lastGpsKey){lastGpsKey=k;if(!view.manual){if(g.length){view.lat=g.reduce((a,p)=>a+p.lat,0)/g.length;view.lon=g.reduce((a,p)=>a+p.lon,0)/g.length;view.zoom=chooseZoom(g)}else{view.lat=SITE.lat;view.lon=SITE.lon;view.zoom=18}}}}

  function tile(layer,z,x,y,src,cls=''){const im=document.createElement('img');im.className='tt-tile '+cls;im.alt='';im.decoding='async';im.loading='eager';im.src=src;im.style.left=x+'px';im.style.top=y+'px';layer.appendChild(im)}
  function addTiles(parent,left,top,w,h,z){const n=2**z,minX=Math.floor(left/256)-1,maxX=Math.floor((left+w)/256)+1,minY=Math.max(0,Math.floor(top/256)-1),maxY=Math.min(n-1,Math.floor((top+h)/256)+1);
    const base=document.createElement('div');base.className='tt-layer';parent.appendChild(base);
    const detail=document.createElement('div');detail.className='tt-layer';parent.appendChild(detail);
    for(let tx=minX;tx<=maxX;tx++)for(let ty=minY;ty<=maxY;ty++){const x=((tx%n)+n)%n,px=tx*256-left,py=ty*256-top;
      if(mode!=='street')tile(base,z,px,py,`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${ty}/${x}`);
      if(mode==='street')tile(base,z,px,py,`https://tile.openstreetmap.org/${z}/${x}/${ty}.png`);
      if(mode==='hybrid')tile(detail,z,px,py,`https://tile.openstreetmap.org/${z}/${x}/${ty}.png`,'tt-hybrid-detail');
    }
  }
  function pin(parent,lat,lon,label,left,top,z,site=false){const p=wp(lat,lon,z),a=document.createElement('div');a.className='tt-pin'+(site?' site':'');a.style.left=(p.x-left)+'px';a.style.top=(p.y-top)+'px';a.innerHTML=`<span class="tt-label">${typeof esc==='function'?esc(label):label}</span><span class="tt-pin-dot"></span>`;parent.appendChild(a)}

  function draw(force=false){if(drag&&!force)return;const box=document.getElementById('mapbox');if(!box)return;const g=gps();fit(g);const sig=`${mode}|${view.lat.toFixed(6)}|${view.lon.toFixed(6)}|${view.zoom}|${gpsKey(g)}`;if(!force&&sig===lastSig)return;lastSig=sig;
    box.className='mapbox tt-live-map';box.innerHTML='';const pan=document.createElement('div');pan.className='tt-pan';box.appendChild(pan);
    const w=Math.max(box.clientWidth||320,280),h=Math.max(box.clientHeight||350,280),z=view.zoom,c=wp(view.lat,view.lon,z),left=c.x-w/2,top=c.y-h/2;addTiles(pan,left,top,w,h,z);
    pin(pan,SITE.lat,SITE.lon,SITE.label,left,top,z,true);g.forEach(p=>{let label='STAFF';try{label=(typeof badge==='function'?badge(p.r):'STAFF')+(p.r.real_name?` • ${p.r.real_name}`:'')}catch{}pin(pan,p.lat,p.lon,label,left,top,z,false)});
    const chip=document.createElement('div');chip.className='tt-chip';chip.innerHTML=g.length?`LIVE ${mode.toUpperCase()} • ${g.length} GPS<span>Shop/road labels • drag map • zoom for detail</span>`:`PRINCESSHAY ${mode.toUpperCase()}<span>Shop/road labels visible • no on-shift GPS yet</span>`;box.appendChild(chip);
    const controls=document.createElement('div');controls.className='tt-controls';controls.innerHTML=`<div class="tt-mode"><button data-m="hybrid" class="${mode==='hybrid'?'active':''}">HYBRID</button><button data-m="satellite" class="${mode==='satellite'?'active':''}">SATELLITE</button><button data-m="street" class="${mode==='street'?'active':''}">STREET</button></div><div class="tt-zoom"><button class="tt-map-btn" data-a="in">+</button><button class="tt-map-btn" data-a="out">−</button><button class="tt-map-btn" data-a="home">◎</button></div>`;box.appendChild(controls);
    controls.onpointerdown=e=>e.stopPropagation();controls.onclick=e=>{const m=e.target?.dataset?.m,a=e.target?.dataset?.a;if(m){mode=m;lastSig='';draw(true);return}if(!a)return;if(a==='in')view.zoom=Math.min(20,view.zoom+1);if(a==='out')view.zoom=Math.max(13,view.zoom-1);if(a==='home'){view.manual=false;lastGpsKey='';fit(gps())}else view.manual=true;lastSig='';draw(true)};
    const at=document.createElement('div');at.className='tt-attrib';at.innerHTML=mode==='street'?'© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>':mode==='hybrid'?'Imagery © Esri • labels © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>':'Imagery © Esri';box.appendChild(at);
    box.onpointerdown=e=>{if(e.target.closest('.tt-controls'))return;drag={x:e.clientX,y:e.clientY,c:wp(view.lat,view.lon,view.zoom),pan,pid:e.pointerId};box.classList.add('dragging');box.setPointerCapture?.(e.pointerId)};
    box.onpointermove=e=>{if(!drag||e.pointerId!==drag.pid)return;drag.pan.style.transform=`translate(${e.clientX-drag.x}px,${e.clientY-drag.y}px)`};
    const end=e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y,p=ll(drag.c.x-dx,drag.c.y-dy,view.zoom);view.lat=p.lat;view.lon=p.lon;view.manual=true;drag=null;box.classList.remove('dragging');lastSig='';draw(true)};box.onpointerup=end;box.onpointercancel=end;
  }
  window.renderLocations=()=>draw(false);
  try{if(document.getElementById('app')&&!document.getElementById('app').classList.contains('hidden'))draw(true)}catch{}
})();