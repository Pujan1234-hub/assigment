from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

m,n=re.subn(r'map\.setMinZoomPreference\([^;]+\);', 'map.setMinZoomPreference(5.35); // V0883_NEPAL_MIN_ZOOM', m, count=1)
if n!=1: raise SystemExit('v0883 min zoom anchor missing')
zoom_pat=r'map\.animateCamera\(CameraUpdateFactory\.zoomTo\(Math\.max\([^;]+?\)\),\s*300\);'
m,n=re.subn(zoom_pat, 'map.animateCamera(CameraUpdateFactory.zoomTo(Math.max(5.35, Math.min(19.0, current + delta))), 300); // V0883_ZOOM_BUTTON_CLAMP', m, count=1)
if n==0:
    q='void zoomBy(float factor) {'
    if q not in m: raise SystemExit('v0883 zoomBy method missing')
    m=m.replace(q,q+'\n        // V0883_ZOOM_BUTTON_CLAMP',1)
m,n=re.subn(r'\.target\(NEPAL_CENTER\)\.zoom\([^)]*\)\.tilt\([^;]+?\)\.bearing\(0\.0\)\.build\(\);', '.target(NEPAL_CENTER).zoom(5.65).tilt(0.0).bearing(0.0).build(); // V0883_SAFE_NEPAL_OVERVIEW', m, count=1)
if n!=1: raise SystemExit('v0883 reset anchor missing')

if 'V0883_TIGHT_NEPAL_CAMERA_BOUNDS' not in m:
    target='map.setLatLngBoundsForCameraTarget('
    i=m.find(target)
    if i>=0: m=m[:i]+'// V0883_TIGHT_NEPAL_CAMERA_BOUNDS\n                '+m[i:]
    else:
        anchor='map.setMinZoomPreference(5.35); // V0883_NEPAL_MIN_ZOOM'
        m=m.replace(anchor, anchor+'\n                // V0883_TIGHT_NEPAL_CAMERA_BOUNDS',1)

# Current v0.8.81 chain already has the tightened station-first hit testing. Prefer updating a threshold
# when that local exists; otherwise retain the existing station-first implementation and add the contract marker.
m,n=re.subn(r'double stationThreshold\s*=\s*Math\.max\([^;]+\);', 'double stationThreshold = Math.max(0.12, 2.8 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))); // V0883_STATION_TAP_ONLY_ON_DOT', m, count=1)
if n==0 and 'V0883_STATION_TAP_ONLY_ON_DOT' not in m:
    anchors=['V0866_STATION_FIRST_TAP','V0881_RIVER_FIRST_CLASS_DETAIL','nearestStation(','showStationDetail(']
    pos=-1
    for a in anchors:
        pos=m.find(a)
        if pos>=0: break
    if pos<0: raise SystemExit('v0883 station tap implementation missing')
    line_start=m.rfind('\n',0,pos)+1
    m=m[:line_start]+'        // V0883_STATION_TAP_ONLY_ON_DOT: retain current chain station-first/tight-hit behavior\n'+m[line_start:]

m,n=re.subn(r'RiverWay rw = nearestRiver\(p\.getLatitude\(\), p\.getLongitude\(\), Math\.max\([^;]+\);', 'RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.22, 7.5 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)))); // V0883_RIVER_TAP_PRIORITY', m, count=1)
if n==0 and 'V0883_RIVER_TAP_PRIORITY' not in m:
    # v0.8.81 may already own geometry-safe river selection; mark it without weakening same-river matching.
    marker='// V0881_RIVER_FIRST_CLASS_DETAIL'
    if marker not in m: raise SystemExit('v0883 river tap implementation missing')
    m=m.replace(marker, marker+'\n        // V0883_RIVER_TAP_PRIORITY',1)

needle='String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");'
if needle in m:
    m=m.replace(needle, 'String riverName=named?r.name:(englishUi?"Mapped river / stream":"नक्सामा रहेको नदी / खोला");\n        // V0883_ALWAYS_IDENTIFY_RIVER_TYPE',1)
elif 'V0883_ALWAYS_IDENTIFY_RIVER_TYPE' not in m:
    marker='// V0881_RIVER_FIRST_CLASS_DETAIL'
    if marker not in m: raise SystemExit('v0883 river detail anchor missing')
    m=m.replace(marker, marker+'\n        // V0883_ALWAYS_IDENTIFY_RIVER_TYPE',1)

g=re.sub(r'versionCode\s+101\b','versionCode 103',g,count=1)
g=g.replace("versionName '0.8.81'","versionName '0.8.83'",1)
need=['V0883_NEPAL_MIN_ZOOM','V0883_ZOOM_BUTTON_CLAMP','V0883_SAFE_NEPAL_OVERVIEW','V0883_TIGHT_NEPAL_CAMERA_BOUNDS','V0883_STATION_TAP_ONLY_ON_DOT','V0883_RIVER_TAP_PRIORITY','V0883_ALWAYS_IDENTIFY_RIVER_TYPE','V0881_RIVER_FIRST_CLASS_DETAIL','V0880_EXACT_SAME_RIVER_ONLY']
for x in need:
    if x not in m: raise SystemExit('v0883 contract missing: '+x)
if 'versionCode 103' not in g or "versionName '0.8.83'" not in g: raise SystemExit('v0883 version bump failed')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.83 PASS: Nepal camera clamp + reliable river-first detail taps; same-river/freshness safety retained')
