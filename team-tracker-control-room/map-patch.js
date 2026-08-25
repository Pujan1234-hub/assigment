/* Team Tracker Control Room — dependency-free live map patch.
   Uses OpenStreetMap raster tiles only; login/auth remains direct-fetch and independent. */
(() => {
  const SITE = { lat: 50.72474, lon: -3.52792, label: 'Princesshay' };

  const style = document.createElement('style');
  style.textContent = `
    #mapbox.tt-live-map{position:relative;height:340px;overflow:hidden;padding:0;background:#d7e0e5;border:1px solid #2b465d;border-radius:14px;touch-action:pan-y}
    .tt-map-tiles{position:absolute;inset:0;overflow:hidden}
    .tt-map-tile{position:absolute;width:256px;height:256px;max-width:none;user-select:none;-webkit-user-drag:none}
    .tt-map-shade{position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
    .tt-map-chip{position:absolute;top:10px;left:10px;z-index:25;background:rgba(5,18,30,.92);color:#fff;border:1px solid #3b5d76;border-radius:10px;padding:7px 9px;font:700 11px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;box-shadow:0 3px 12px rgba(0,0,0,.22)}
    .tt-map-chip span{display:block;color:#9fb2c3;font-weight:600;margin-top:2px}
    .tt-map-attrib{position:absolute;right:6px;bottom:5px;z-index:25;background:rgba(255,255,255,.9);color:#283845;border-radius:5px;padding:2px 5px;font:10px system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
    .tt-map-attrib a{color:#245b83;text-decoration:none}
    .tt-pin{position:absolute;z-index:30;transform:translate(-50%,-100%);text-decoration:none;color:#fff;filter:drop-shadow(0 3px 5px rgba(0,0,0,.35))}
    .tt-pin-dot{width:30px;height:30px;border-radius:50% 50% 50% 8px;transform:rotate(-45deg);background:#efb632;border:3px solid #fff;display:grid;place-items:center}
    .tt-pin-dot:after{content:'';width:8px;height:8px;border-radius:50%;background:#102235}
    .tt-pin.site .tt-pin-dot{width:24px;height:24px;background:#48a9e6;opacity:.95}
    .tt-pin-label{position:absolute;left:50%;top:-34px;transform:translateX(-50%);white-space:nowrap;background:#071826;color:#fff;border:1px solid #577792;border-radius:7px;padding:3px 6px;font:800 10px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;letter-spacing:.02em}
    .tt-pin.site .tt-pin-label{top:-30px;color:#dcefff}
    @media(max-width:700px){#mapbox.tt-live-map{height:315px}.tt-pin-label{max-width:120px;overflow:hidden;text-overflow:ellipsis}}
  `;
  document.head.appendChild(style);

  const worldPoint = (lat, lon, z) => {
    const size = 256 * Math.pow(2, z);
    const x = (lon + 180) / 360 * size;
    const s = Math.sin(lat * Math.PI / 180);
    const y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * size;
    return { x, y };
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

  window.renderLocations = function renderLocationsPatched(){
    const box = document.getElementById('mapbox');
    if(!box) return;
    const source = (typeof rows !== 'undefined' && Array.isArray(rows)) ? rows : [];
    const gps = source.map(r=>({r,lat:safeNum(r.latitude),lon:safeNum(r.longitude)})).filter(p=>p.lat!==null&&p.lon!==null);
    const zoom = chooseZoom(gps);
    const center = gps.length ? {
      lat:gps.reduce((a,p)=>a+p.lat,0)/gps.length,
      lon:gps.reduce((a,p)=>a+p.lon,0)/gps.length
    } : SITE;

    box.className='mapbox tt-live-map';
    box.innerHTML='';
    const tiles=document.createElement('div'); tiles.className='tt-map-tiles'; box.appendChild(tiles);
    const w=Math.max(box.clientWidth||320,280), h=Math.max(box.clientHeight||315,260);
    const c=worldPoint(center.lat,center.lon,zoom), left=c.x-w/2, top=c.y-h/2;
    const n=Math.pow(2,zoom);
    const minTx=Math.floor(left/256)-1,maxTx=Math.floor((left+w)/256)+1;
    const minTy=Math.max(0,Math.floor(top/256)-1),maxTy=Math.min(n-1,Math.floor((top+h)/256)+1);
    for(let tx=minTx;tx<=maxTx;tx++) for(let ty=minTy;ty<=maxTy;ty++){
      const wrap=((tx%n)+n)%n;
      const img=document.createElement('img');
      img.className='tt-map-tile'; img.alt=''; img.decoding='async'; img.loading='eager';
      img.src=`https://tile.openstreetmap.org/${zoom}/${wrap}/${ty}.png`;
      img.style.left=`${tx*256-left}px`; img.style.top=`${ty*256-top}px`;
      tiles.appendChild(img);
    }

    const addPin=(lat,lon,label,site=false,href='')=>{
      const p=worldPoint(lat,lon,zoom); const a=document.createElement(href?'a':'div');
      a.className='tt-pin'+(site?' site':''); a.style.left=`${p.x-left}px`; a.style.top=`${p.y-top}px`;
      if(href){a.href=href;a.target='_blank';a.rel='noopener';}
      a.innerHTML=`<span class="tt-pin-label">${typeof esc==='function'?esc(label):label}</span><span class="tt-pin-dot"></span>`;
      box.appendChild(a);
    };

    addPin(SITE.lat,SITE.lon,SITE.label,true,'https://www.openstreetmap.org/?mlat=50.72474&mlon=-3.52792#map=18/50.72474/-3.52792');
    gps.forEach(p=>{
      let label='STAFF';
      try{ label=(typeof badge==='function'?badge(p.r):'STAFF')+(p.r.real_name?` • ${p.r.real_name}`:''); }catch{}
      addPin(p.lat,p.lon,label,false,`https://www.google.com/maps?q=${encodeURIComponent(p.lat+','+p.lon)}`);
    });

    const chip=document.createElement('div'); chip.className='tt-map-chip';
    chip.innerHTML=gps.length?`LIVE MAP • ${gps.length} GPS<span>Tap a staff marker to open exact location</span>`:`PRINCESSHAY LIVE MAP<span>No on-shift GPS coordinates yet</span>`;
    box.appendChild(chip);
    const attr=document.createElement('div'); attr.className='tt-map-attrib'; attr.innerHTML='© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';
    box.appendChild(attr);
    const shade=document.createElement('div'); shade.className='tt-map-shade'; box.appendChild(shade);
  };

  // If Control Room is already open when this patch loads, draw immediately.
  try { if(document.getElementById('app') && !document.getElementById('app').classList.contains('hidden')) window.renderLocations(); } catch {}
})();