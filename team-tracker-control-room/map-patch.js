/* Team Tracker Control Room — dependency-free interactive live map patch.
   Uses OpenStreetMap raster tiles only; auth/login stays independent. */
(() => {
  const SITE = { lat: 50.72474, lon: -3.52792, label: 'Princesshay' };
  let view = { lat: SITE.lat, lon: SITE.lon, zoom: 17, manual: false };
  let lastGpsKey = '';

  const style = document.createElement('style');
  style.textContent = `
    #mapbox.tt-live-map{position:relative;height:360px;overflow:hidden;padding:0;background:#d7e0e5;border:1px solid #2b465d;border-radius:14px;touch-action:none;cursor:grab}
    #mapbox.tt-live-map.dragging{cursor:grabbing}
    .tt-map-tiles{position:absolute;inset:0;overflow:hidden;pointer-events:none}
    .tt-map-tile{position:absolute;width:256px;height:256px;max-width:none;user-select:none;-webkit-user-drag:none}
    .tt-map-shade{position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
    .tt-map-chip{position:absolute;top:10px;left:10px;z-index:25;background:rgba(5,18,30,.94);color:#fff;border:1px solid #3b5d76;border-radius:10px;padding:7px 9px;font:700 11px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;box-shadow:0 3px 12px rgba(0,0,0,.22);pointer-events:none}
    .tt-map-chip span{display:block;color:#9fb2c3;font-weight:600;margin-top:2px}
    .tt-map-controls{position:absolute;right:10px;top:10px;z-index:35;display:grid;gap:6px}
    .tt-map-btn{width:38px;height:38px;border-radius:10px;border:1px solid #48667d;background:rgba(7,24,38,.94);color:#fff;font:900 20px/1 system-ui;box-shadow:0 3px 10px rgba(0,0,0,.22);cursor:pointer}
    .tt-map-btn.home{font-size:15px}
    .tt-map-attrib{position:absolute;right:6px;bottom:5px;z-index:25;background:rgba(255,255,255,.9);color:#283845;border-radius:5px;padding:2px 5px;font:10px system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
    .tt-map-attrib a{color:#245b83;text-decoration:none}
    .tt-pin{position:absolute;z-index:30;transform:translate(-50%,-100%);text-decoration:none;color:#fff;filter:drop-shadow(0 3px 5px rgba(0,0,0,.35))}
    .tt-pin-dot{width:31px;height:31px;border-radius:50% 50% 50% 8px;transform:rotate(-45deg);background:#efb632;border:3px solid #fff;display:grid;place-items:center}
    .tt-pin-dot:after{content:'';width:8px;height:8px;border-radius:50%;background:#102235}
    .tt-pin.site .tt-pin-dot{width:25px;height:25px;background:#48a9e6;opacity:.95}
    .tt-pin-label{position:absolute;left:50%;top:-35px;transform:translateX(-50%);white-space:nowrap;background:#071826;color:#fff;border:1px solid #577792;border-radius:7px;padding:3px 6px;font:800 10px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;letter-spacing:.02em}
    .tt-pin.site .tt-pin-label{top:-31px;color:#dcefff}
    @media(max-width:700px){#mapbox.tt-live-map{height:330px}.tt-pin-label{max-width:125px;overflow:hidden;text-overflow:ellipsis}}
  `;
  document.head.appendChild(style);

  const worldPoint = (lat, lon, z) => {
    const size = 256 * Math.pow(2, z);
    const x = (lon + 180) / 360 * size;
    const s = Math.sin(lat * Math.PI / 180);
    const y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * size;
    return { x, y };
  };
  const pointToLatLon = (x, y, z) => {
    const size = 256 * Math.pow(2, z);
    const lon = x / size * 360 - 180;
    const n = Math.PI - 2 * Math.PI * y / size;
    const lat = 180 / Math.PI * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
    return { lat, lon };
  };
  const chooseZoom = pts => {
    if (!pts.length) return 17;
    let minLat=pts[0].lat,maxLat=pts[0].lat,minLon=pts[0].lon,maxLon=pts[0].lon;
    pts.forEach(p=>{minLat=Math.min(minLat,p.lat);maxLat=Math.max(maxLat,p.lat);minLon=Math.min(minLon,p.lon);maxLon=Math.max(maxLon,p.lon)});
    const span=Math.max(maxLat-minLat, (maxLon-minLon)*0.65);
    if(span < 0.00055) return 19;
    if(span < 0.0011) return 18;
    if(span < 0.0024) return 17;
    if(span < 0.005) return 16;
    if(span < 0.011) return 15;
    return 14;
  };
  const safeNum = v => { const n=Number(v); return Number.isFinite(n)?n:null; };

  function getGps(){
    const source = (typeof rows !== 'undefined' && Array.isArray(rows)) ? rows : [];
    return source.map(r=>({r,lat:safeNum(r.latitude),lon:safeNum(r.longitude)})).filter(p=>p.lat!==null&&p.lon!==null);
  }

  function fitToGps(gps){
    const key = gps.map(p=>`${p.r.staff_id}:${p.lat.toFixed(5)},${p.lon.toFixed(5)}`).join('|');
    if (key !== lastGpsKey) {
      lastGpsKey = key;
      view.manual = false;
    }
    if(view.manual) return;
    if(gps.length){
      view.lat=gps.reduce((a,p)=>a+p.lat,0)/gps.length;
      view.lon=gps.reduce((a,p)=>a+p.lon,0)/gps.length;
      view.zoom=chooseZoom(gps);
    } else {
      view.lat=SITE.lat; view.lon=SITE.lon; view.zoom=17;
    }
  }

  function draw(){
    const box=document.getElementById('mapbox'); if(!box) return;
    const gps=getGps();
    box.className='mapbox tt-live-map'; box.innerHTML='';
    const tiles=document.createElement('div'); tiles.className='tt-map-tiles'; box.appendChild(tiles);
    const w=Math.max(box.clientWidth||320,280), h=Math.max(box.clientHeight||330,270);
    const z=view.zoom, c=worldPoint(view.lat,view.lon,z), left=c.x-w/2, top=c.y-h/2;
    const n=Math.pow(2,z), minTx=Math.floor(left/256)-1,maxTx=Math.floor((left+w)/256)+1;
    const minTy=Math.max(0,Math.floor(top/256)-1),maxTy=Math.min(n-1,Math.floor((top+h)/256)+1);
    for(let tx=minTx;tx<=maxTx;tx++) for(let ty=minTy;ty<=maxTy;ty++){
      const wrap=((tx%n)+n)%n;
      const img=document.createElement('img'); img.className='tt-map-tile'; img.alt=''; img.decoding='async'; img.loading='eager';
      img.src=`https://tile.openstreetmap.org/${z}/${wrap}/${ty}.png`;
      img.style.left=`${tx*256-left}px`; img.style.top=`${ty*256-top}px`; tiles.appendChild(img);
    }
    const addPin=(lat,lon,label,site=false,href='')=>{
      const p=worldPoint(lat,lon,z); const a=document.createElement(href?'a':'div');
      a.className='tt-pin'+(site?' site':''); a.style.left=`${p.x-left}px`; a.style.top=`${p.y-top}px`;
      if(href){a.href=href;a.target='_blank';a.rel='noopener';a.addEventListener('pointerdown',e=>e.stopPropagation())}
      a.innerHTML=`<span class="tt-pin-label">${typeof esc==='function'?esc(label):label}</span><span class="tt-pin-dot"></span>`; box.appendChild(a);
    };
    addPin(SITE.lat,SITE.lon,SITE.label,true,'https://www.openstreetmap.org/?mlat=50.72474&mlon=-3.52792#map=18/50.72474/-3.52792');
    gps.forEach(p=>{let label='STAFF';try{label=(typeof badge==='function'?badge(p.r):'STAFF')+(p.r.real_name?` • ${p.r.real_name}`:'')}catch{};addPin(p.lat,p.lon,label,false,`https://www.google.com/maps?q=${encodeURIComponent(p.lat+','+p.lon)}`)});

    const chip=document.createElement('div'); chip.className='tt-map-chip'; chip.innerHTML=gps.length?`LIVE MAP • ${gps.length} GPS<span>Drag map • tap marker for exact location</span>`:`PRINCESSHAY LIVE MAP<span>No on-shift GPS coordinates yet</span>`; box.appendChild(chip);
    const controls=document.createElement('div'); controls.className='tt-map-controls';
    controls.innerHTML='<button class="tt-map-btn" data-a="in" aria-label="Zoom in">+</button><button class="tt-map-btn" data-a="out" aria-label="Zoom out">−</button><button class="tt-map-btn home" data-a="home" aria-label="Recenter">◎</button>';
    controls.addEventListener('pointerdown',e=>e.stopPropagation());
    controls.addEventListener('click',e=>{const a=e.target?.dataset?.a;if(!a)return;if(a==='in')view.zoom=Math.min(20,view.zoom+1);if(a==='out')view.zoom=Math.max(13,view.zoom-1);if(a==='home'){view.manual=false;fitToGps(getGps())}else view.manual=true;draw()}); box.appendChild(controls);
    const attr=document.createElement('div'); attr.className='tt-map-attrib'; attr.innerHTML='© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'; box.appendChild(attr);
    const shade=document.createElement('div'); shade.className='tt-map-shade'; box.appendChild(shade);

    let drag=null;
    box.onpointerdown=e=>{if(e.button!==undefined&&e.button!==0)return;drag={x:e.clientX,y:e.clientY,c:worldPoint(view.lat,view.lon,view.zoom)};box.classList.add('dragging');box.setPointerCapture?.(e.pointerId)};
    box.onpointermove=e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;const ll=pointToLatLon(drag.c.x-dx,drag.c.y-dy,view.zoom);view.lat=ll.lat;view.lon=ll.lon;view.manual=true;draw()};
    const end=()=>{drag=null;box.classList.remove('dragging')}; box.onpointerup=end; box.onpointercancel=end;
  }

  window.renderLocations = function renderLocationsPatched(){fitToGps(getGps());draw()};
  try { if(document.getElementById('app') && !document.getElementById('app').classList.contains('hidden')) window.renderLocations(); } catch {}
})();