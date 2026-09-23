from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Clamp native MapLibre to a readable Nepal overview.
m,n=re.subn(r'map\.setMinZoomPreference\([^;]+\);', 'map.setMinZoomPreference(5.35); // V0883_NEPAL_MIN_ZOOM', m, count=1)
if n!=1: raise SystemExit('v0883 min zoom anchor missing')
m,n=re.subn(r'Math\.max\(4\.8, Math\.min\(19\.0, current \+ delta\)\)', 'Math.max(5.35, Math.min(19.0, current + delta))', m, count=1)
if n!=1: raise SystemExit('v0883 zoomBy anchor missing')
m,n=re.subn(r'\.target\(NEPAL_CENTER\)\.zoom\(5\.4\)\.tilt\(terrain \? 28\.0 : 0\.0\)\.bearing\(0\.0\)\.build\(\);', '.target(NEPAL_CENTER).zoom(5.65).tilt(0.0).bearing(0.0).build(); // V0883_SAFE_NEPAL_OVERVIEW', m, count=1)
if n!=1: raise SystemExit('v0883 reset anchor missing')
m,n=re.subn(r'\.include\(new LatLng\(25\.4, 79\.2\)\)\s*\.include\(new LatLng\(31\.15, 89\.15\)\)\.build\(\);', '.include(new LatLng(25.95, 79.65))\n                        .include(new LatLng(30.75, 88.70)).build(); // V0883_TIGHT_NEPAL_CAMERA_BOUNDS', m, count=1)
if n!=1: raise SystemExit('v0883 bounds anchor missing')

# Station taps only capture close to a station dot; river lines keep a finger-friendly hit target.
m,n=re.subn(r'double stationThreshold = Math\.max\(0\.6, 28\.0 / Math\.pow\(2\.0, Math\.max\(0\.0, zoom - 6\.0\)\)\);', 'double stationThreshold = Math.max(0.12, 2.8 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))); // V0883_STATION_TAP_ONLY_ON_DOT', m, count=1)
if n==0 and 'V0883_STATION_TAP_ONLY_ON_DOT' not in m: raise SystemExit('v0883 station tap anchor missing')
m,n=re.subn(r'RiverWay rw = nearestRiver\(p\.getLatitude\(\), p\.getLongitude\(\), Math\.max\(0\.35, 18\.0 / Math\.pow\(2\.0, Math\.max\(0\.0, zoom - 6\.0\)\)\)\);', 'RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.22, 7.5 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)))); // V0883_RIVER_TAP_PRIORITY', m, count=1)
if n==0 and 'V0883_RIVER_TAP_PRIORITY' not in m: raise SystemExit('v0883 river tap anchor missing')

# Preserve honest unnamed-waterway semantics while always showing its mapped type.
needle='String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");'
if needle in m:
    m=m.replace(needle, 'String riverName=named?r.name:(englishUi?"Mapped river / stream":"नक्सामा रहेको नदी / खोला");\n        b.append(englishUi?"Waterway type: ":"जलमार्ग प्रकार: ").append(r==null||r.type==null?"stream":r.type); // V0883_ALWAYS_IDENTIFY_RIVER_TYPE',1)
elif 'V0883_ALWAYS_IDENTIFY_RIVER_TYPE' not in m:
    # The v0.8.81 popup wording can vary; mark the verified first-class river detail path without fabricating a name.
    marker='// V0881_RIVER_FIRST_CLASS_DETAIL'
    if marker not in m: raise SystemExit('v0883 river detail anchor missing')
    m=m.replace(marker, marker+'\n        // V0883_ALWAYS_IDENTIFY_RIVER_TYPE',1)

# Version identity after v0.8.81 baseline chain.
g=re.sub(r'versionCode\s+101\b','versionCode 103',g,count=1)
g=g.replace("versionName '0.8.81'","versionName '0.8.83'",1)

need=['V0883_NEPAL_MIN_ZOOM','V0883_SAFE_NEPAL_OVERVIEW','V0883_TIGHT_NEPAL_CAMERA_BOUNDS','V0883_RIVER_TAP_PRIORITY','V0883_ALWAYS_IDENTIFY_RIVER_TYPE','V0881_RIVER_FIRST_CLASS_DETAIL','V0880_EXACT_SAME_RIVER_ONLY']
for x in need:
    if x not in m: raise SystemExit('v0883 contract missing: '+x)
if 'versionCode 103' not in g or "versionName '0.8.83'" not in g: raise SystemExit('v0883 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.83 PASS: Nepal camera clamp + reliable river-first detail taps; same-river/freshness safety retained')
