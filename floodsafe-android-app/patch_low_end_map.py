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

print('Low-end Android map performance patch PASS')
