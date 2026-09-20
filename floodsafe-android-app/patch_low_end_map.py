from pathlib import Path

ROOT = Path('floodsafe-android-app/app/build/generated/floodsafe-assets/floodsafe-nepal/v25')


def read(rel):
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f'missing generated map asset: {rel}')
    return p, p.read_text(encoding='utf-8')


def write(p, text):
    p.write_text(text, encoding='utf-8')


# Current v18 already uses a single adaptive setTimeout, pauses during gestures,
# slows down on low-power devices, and hides expensive glow at national zoom.
# Keep backwards compatibility with older generated assets if a historical build
# is rebuilt, but do not rewrite the modern scheduler.
p, text = read('river-line-style-v1.js')
if '__fsRiverLineStyleV18' in text:
    required = ['function cadence(map)', 'setTimeout(animateOnce', "map.on('movestart',stopAnimation)", 'GLOW_MIN_ZOOM=9.5']
    for marker in required:
        if marker not in text:
            raise SystemExit('v18 adaptive river performance marker missing: ' + marker)
else:
    old_starts = [
        "function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},240)}",
        "function start(){if(anim)return;anim=setInterval(()=>{if(document.hidden)return;if(apply())animate()},280)}",
    ]
    new_start = "function mapBusy(){const map=window.FloodSafeMap?.map;try{return document.hidden||window.__fsSathiTyping===true||!!map?.isMoving?.()||!!map?.isZooming?.()||!!map?.isRotating?.()}catch{return document.hidden||window.__fsSathiTyping===true}}\nfunction start(){if(anim)return;anim=setInterval(()=>{if(mapBusy())return;animate()},850)}"
    if new_start not in text:
        matched = False
        for old_start in old_starts:
            if old_start in text:
                text = text.replace(old_start, new_start, 1)
                matched = True
                break
        if not matched:
            raise SystemExit('river animation marker missing')
    old_glow = "id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,paint:"
    new_glow = "id:'hydro-complete-status-glow',type:'line',source,filter:KNOWN,minzoom:7,paint:"
    text = text.replace(old_glow, new_glow, 1)
    if 'setInterval(()=>{if(mapBusy())return;animate()},850)' not in text:
        raise SystemExit('river low-end animation throttle failed')
write(p, text)

# Preserve the source's last official observation for station detail, even when it is
# too old to be treated as the current safety state. Current status remains strict:
# stale readings are still unknown/grey and never become a live warning/danger.
p, text = read('trusted-river-runtime-v3.js')
old_known = "_lastKnownObservation:rawHas&&isCurrentTime(t)?{time:t,level:level(o),warning:warning(o),danger:danger(o),discharge:discharge(o),status:rawStage(o)}:null"
new_known = "_lastKnownObservation:rawHas?{time:t,level:level(o),warning:warning(o),danger:danger(o),discharge:discharge(o),status:rawStage(o)}:null"
if old_known in text:
    text = text.replace(old_known, new_known, 1)
elif new_known not in text:
    raise SystemExit('last official river observation marker missing')
if new_known not in text:
    raise SystemExit('last official river observation retention failed')
write(p, text)

# The permanent station layer had a second unconditional full GeoJSON rebuild every 10 s.
# Real data-change events still refresh immediately; unchanged one-second heartbeats do not
# redraw the map, and the watchdog never competes with gestures or SATHI keyboard input.
p, text = read('permanent-281-map-v1.js')
old_interval = 'setInterval(sync,10000);'
new_interval = "setInterval(()=>{const m=window.FloodSafeMap?.map;if(document.hidden||window.__fsSathiTyping===true||m?.isMoving?.()||m?.isZooming?.()||m?.isRotating?.())return;sync()},45000);"
if old_interval not in text and new_interval not in text:
    raise SystemExit('281 station watchdog marker missing')
text = text.replace(old_interval, new_interval, 1)
if new_interval not in text:
    raise SystemExit('281 station watchdog throttle failed')

old_events = "for(const ev of['fstrustedriverupdate','fsriverupdate','fsriverheartbeat','fslanguage'])"
new_events = "for(const ev of['fstrustedriverupdate','fsriverupdate','fslanguage'])"
if old_events in text:
    text = text.replace(old_events, new_events, 1)
elif new_events not in text:
    raise SystemExit('281 station event listener marker missing')

# Let a station popup show the source's last official values/timestamp when there is no
# current reading. has_latest remains false, status remains unknown, and the marker stays
# grey, so an old DANGER value can never masquerade as a current danger state.
old_stamp = "const stamp=o=>val(flat(o),['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']);"
new_stamp = "const lastKnown=o=>flat(o)?._lastKnownObservation&&typeof flat(o)._lastKnownObservation==='object'?flat(o)._lastKnownObservation:null;\nconst stamp=o=>val(flat(o),['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime'])||lastKnown(o)?.time||null;"
if old_stamp in text:
    text = text.replace(old_stamp, new_stamp, 1)
elif 'const lastKnown=o=>' not in text:
    raise SystemExit('281 station time helper marker missing')

replacements = [
    ("const level=o=>num(val(flat(o),['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','_lastWaterLevel']));",
     "const level=o=>num(val(flat(o),['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','_lastWaterLevel']))??num(lastKnown(o)?.level);"),
    ("const warning=o=>num(val(flat(o),['warningLevel','warning_level','warningThreshold','warning_threshold','_lastWarningLevel']));",
     "const warning=o=>num(val(flat(o),['warningLevel','warning_level','warningThreshold','warning_threshold','_lastWarningLevel']))??num(lastKnown(o)?.warning);"),
    ("const danger=o=>num(val(flat(o),['dangerLevel','danger_level','dangerThreshold','danger_threshold','_lastDangerLevel']));",
     "const danger=o=>num(val(flat(o),['dangerLevel','danger_level','dangerThreshold','danger_threshold','_lastDangerLevel']))??num(lastKnown(o)?.danger);"),
    ("const discharge=o=>num(val(flat(o),['discharge','currentDischarge','current_discharge','flow','flowRate','flow_rate','_lastDischarge']));",
     "const discharge=o=>num(val(flat(o),['discharge','currentDischarge','current_discharge','flow','flowRate','flow_rate','_lastDischarge']))??num(lastKnown(o)?.discharge);"),
    ("function hasObs(o){return !!stamp(o)&&level(o)!==null}",
     "function hasObs(o){const x=flat(o);if(x?._hasLatestOfficialObservation===false)return false;const t=val(x,['_measurementTime','waterLevelOn','water_level_on','measuredOn','measured_on','measurementTime','observationTime']),l=num(val(x,['waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','_lastWaterLevel']));return !!t&&l!==null}"),
    ("function statusLabel(p){if(Number(p.has_latest)!==1)return tr('पढाइ उपलब्ध छैन','NO LATEST READING');",
     "function statusLabel(p){if(Number(p.has_latest)!==1)return p.time?tr('पछिल्लो official पढाइ — अहिलेको अवस्था होइन','LAST OFFICIAL READING — NOT CURRENT'):tr('पढाइ उपलब्ध छैन','NO LATEST READING');"),
    ("const has=Number(p.has_latest)===1,when=has?fmtTime(p.time):'—',ago=has&&p.time?age(p.time):'',fresh=p.freshness||'none';",
     "const has=Number(p.has_latest)===1,when=p.time?fmtTime(p.time):'—',ago=p.time?age(p.time):'',fresh=p.freshness||'none';"),
    ("<b>${tr('पानीको सतह','Water level')}:</b> ${has&&p.level!==''?esc(p.level)+' m':'—'}",
     "<b>${has?tr('पानीको सतह','Water level'):tr('पछिल्लो official पानीको सतह','Last official water level')}:</b> ${p.level!==''?esc(p.level)+' m':'—'}"),
    ("${!has?`<div style=\"margin-top:7px;font-weight:700\">${tr('यो official station हो, तर अहिले latest reading उपलब्ध छैन।','This is an official station, but no latest reading is currently available.')}</div>`:''}",
     "${!has?`<div style=\"margin-top:7px;padding:7px;border-radius:8px;background:#f1f5f9;font-weight:800\">${p.time?tr('माथिको मान पछिल्लो official observation हो; अहिलेको live अवस्था होइन।','The values above are the last official observation, not the current live condition.'):tr('यो official station हो, तर latest observation उपलब्ध छैन।','This is an official station, but no latest observation is available.')}</div>`:''}")
]
for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit('281 last-observation popup marker missing: ' + old[:70])

required_281 = [
    new_interval,
    new_events,
    'const lastKnown=o=>',
    'LAST OFFICIAL READING — NOT CURRENT',
    'Last official water level',
]
for marker in required_281:
    if marker not in text:
        raise SystemExit('281 last-observation/detail patch failed: ' + marker)
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

print('Low-end Android map performance patch PASS: adaptive rivers + change-only station redraw + last official detail + gesture mode + mobile labels')
