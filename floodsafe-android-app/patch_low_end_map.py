from pathlib import Path

ROOT = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25')


def read(rel):
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f'missing generated map asset: {rel}')
    return p, p.read_text(encoding='utf-8')


def write(p, text):
    p.write_text(text, encoding='utf-8')


# The old river animation re-applied all MapLibre paint/filter properties every 240 ms.
# On Android that repeatedly invalidated a very large river network and could make the
# whole WebView look frozen after resume. Apply styles only on data/style events and
# animate at a modest rate while the map is idle.
p, text = read('river-line-style-v1.js')
old_start = "function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},240)}"
new_start = "function mapBusy(){const map=window.FloodSafeMap?.map;try{return document.hidden||window.__fsSathiTyping===true||!!map?.isMoving?.()||!!map?.isZooming?.()||!!map?.isRotating?.()}catch{return document.hidden||window.__fsSathiTyping===true}}\nfunction start(){if(anim)return;anim=setInterval(()=>{if(mapBusy())return;animate()},850)}"
if old_start not in text and new_start not in text:
    raise SystemExit('river animation marker missing')
text = text.replace(old_start, new_start, 1)
# Full-network blur is expensive at national zoom. Render it only once the user zooms in.
old_glow = "id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,paint:"
new_glow = "id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,minzoom:7,paint:"
text = text.replace(old_glow, new_glow, 1)
if 'setInterval(()=>{if(mapBusy())return;animate()},850)' not in text:
    raise SystemExit('river low-end animation throttle failed')
write(p, text)

# The permanent station layer had a second unconditional full GeoJSON rebuild every 10 s.
# Real data events still refresh immediately; the watchdog now runs less often and never
# competes with map gestures or SATHI keyboard input.
p, text = read('permanent-281-map-v1.js')
old_interval = 'setInterval(sync,10000);'
new_interval = "setInterval(()=>{const m=window.FloodSafeMap?.map;if(document.hidden||window.__fsSathiTyping===true||m?.isMoving?.()||m?.isZooming?.()||m?.isRotating?.())return;sync()},45000);"
if old_interval not in text and new_interval not in text:
    raise SystemExit('281 station watchdog marker missing')
text = text.replace(old_interval, new_interval, 1)
if new_interval not in text:
    raise SystemExit('281 station watchdog throttle failed')
write(p, text)

# 77 DOM district labels are useful on desktop but expensive while a phone GPU is also
# drawing raster tiles + the national river network. Keep the district polygons, station
# points and all data; omit only the decorative text markers on small Android screens.
p, text = read('map-smooth-v3.js')
mobile_call = 'if(window.innerWidth>=760)addLabels()'
if mobile_call not in text:
    call = 'addLabels()}'
    if call not in text:
        raise SystemExit('district label call marker missing')
    text = text.replace(call, mobile_call + '}', 1)
if mobile_call not in text:
    raise SystemExit('mobile district label throttle failed')
write(p, text)

# Biggest gesture win: while the user is actively dragging/zooming, MapLibre should move
# the raster/district canvas without re-rasterising thousands of national river segments,
# shadows, glow and hit-test lines every frame. Hide only those hydro layers during the
# gesture, then restore them shortly after touch release. Official station data and alert
# calculations remain unchanged; this is presentation-only.
p, text = read('hydro-smooth-v2.js')
old_events = "map.on('movestart',()=>{interaction=true;moveEpoch++;renderToken++;clearTimeout(refreshTimer);clearTimeout(retryTimer)});map.on('moveend',()=>{interaction=false;scheduleViewport(260)});"
new_events = "const __fsGestureLayers=['hydro-complete-shadow','hydro-complete-lines','hydro-complete-status-glow','hydro-complete-live-flow','hydro-complete-flood-glow','hydro-complete-flood-pulse','hydro-complete-selected','hydro-complete-hit'];let __fsRestoreTimer=0;function __fsHydroVisibility(show){for(const id of __fsGestureLayers){try{if(map.getLayer(id))map.setLayoutProperty(id,'visibility',show?'visible':'none')}catch{}}}map.on('movestart',()=>{interaction=true;moveEpoch++;renderToken++;clearTimeout(refreshTimer);clearTimeout(retryTimer);clearTimeout(__fsRestoreTimer);__fsHydroVisibility(false)});map.on('moveend',()=>{interaction=false;clearTimeout(__fsRestoreTimer);__fsRestoreTimer=setTimeout(()=>{__fsHydroVisibility(true);scheduleViewport(90)},90)});"
if '__fsGestureLayers' not in text:
    if old_events not in text:
        raise SystemExit('hydro gesture event marker missing')
    text = text.replace(old_events, new_events, 1)
if "__fsHydroVisibility(false)" not in text or "__fsHydroVisibility(true)" not in text:
    raise SystemExit('hydro gesture visibility patch failed')
write(p, text)

print('Low-end Android map performance patch PASS: gesture mode + mobile labels')