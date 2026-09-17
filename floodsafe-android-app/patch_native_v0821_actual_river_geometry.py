from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.21 user lock:
# - the blue/cyan flow must follow the real bundled OSM river/stream geometry;
# - once the user zooms to local level, never drop a local waterway merely because
#   Kathmandu (or another dense area) has more than an arbitrary top-N routes;
# - fresh same-river official BIPAD/DHM status overrides that exact river geometry:
#   normal blue, alert yellow, warning orange, danger red;
# - Nepal-only mask, no rain markers, and strict same-river gauge semantics remain.

old='int keep=Math.min(zoom>=10.0?160:(zoom>=8.0?120:72),candidates.size());chosen.addAll(candidates.subList(0,keep));'
new='int keep=zoom>=10.0?candidates.size():Math.min(zoom>=8.0?900:320,candidates.size());chosen.addAll(candidates.subList(0,keep));'
if old in m:
    m=m.replace(old,new,1)
elif new not in m:
    raise SystemExit('v0.8.21 local-all-waterways anchor missing')

# At local zoom the tile is the truth source. Keeping all candidates means small
# urban rivers such as Dhobi Khola cannot disappear behind a top-160 ranking cap.
# Flow particles remain bounded separately, so this does not multiply animation work.

# Make default/no-severe-state water geometry unmistakably blue-cyan while preserving
# the verified status overlays created by earlier patches.
m=re.sub(
    r'style\.addLayer\(new LineLayer\("fs-rivers-layer", "fs-rivers"\)\.withProperties\(\s*lineColor\("#[0-9A-Fa-f]{6}"\), lineWidth\(([0-9.]+)f\), lineOpacity\(([0-9.]+)f\), lineCap\(LINE_CAP_ROUND\), lineJoin\(LINE_JOIN_ROUND\)\)\);',
    'style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#22e7ff"), lineWidth(2.20f), lineOpacity(0.98f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));',
    m,count=1,flags=re.S)

# Re-assert exact risk colours on the official same-river overlays. These are only
# populated when the existing fresh/current gauge matcher succeeds.
for layer,color in [
    ('fs-river-normal-status-layer','#2d8cff'),
    ('fs-river-alert-status-layer','#ffc928'),
    ('fs-river-warning-status-layer','#ff8a1f'),
    ('fs-river-danger-status-layer','#f22f4b')]:
    pat=r'new LineLayer\("'+re.escape(layer)+r'",sourceId\)\.withProperties\(lineColor\(color\),lineWidth\(3\.55f\),lineOpacity\(1\.0f\),lineCap\(LINE_CAP_ROUND\),lineJoin\(LINE_JOIN_ROUND\)\)'
    # ensureRiverStatusLayer is generic; exact colours are passed at call sites.

# Version bump.
if "versionName '0.8.21'" not in g:
    g=g.replace('versionCode 40','versionCode 41',1)
    g=g.replace("versionName '0.8.20'","versionName '0.8.21'",1)
if 'versionCode 41' not in g or "versionName '0.8.21'" not in g:
    raise SystemExit('v0.8.21 version bump failed')

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

# Hard gates: local actual geometry cannot be arbitrarily truncated again.
m2=m_path.read_text(encoding='utf-8')
a2=a_path.read_text(encoding='utf-8')
for marker in [
    'zoom>=10.0?candidates.size():Math.min(zoom>=8.0?900:320,candidates.size())',
    'readRiverTile','data/nepal-waterways-tiles/','trimRiverToNepal',
    'fs-nepal-outside-mask-layer','lineColor("#22e7ff")',
    'ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#2d8cff")',
    'ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#ffc928")',
    'ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#ff8a1f")',
    'ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#f22f4b")',
    'sameRiverGaugeFor','setGeo("fs-rain-stale",e)']:
    if marker not in m2: raise SystemExit('v0.8.21 marker missing: '+marker)
if 'zoom>=10.0?160:(zoom>=8.0?120:72)' in m2:
    raise SystemExit('old top-160 local river cap remained')
if 'river-stations/?latest=true' not in a2:
    raise SystemExit('latest official river source missing')
print('FloodSafe v0.8.21 actual local river geometry + realtime status colours PASS')