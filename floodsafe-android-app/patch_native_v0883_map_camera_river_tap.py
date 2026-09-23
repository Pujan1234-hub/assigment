from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Real-device repair after v0.8.82:
# - prevent the unusable over-zoomed-out/tilted world imagery state
# - make river hit testing win unless the tap is genuinely on a station marker
# - keep v0.8.81 exact same-river detail and fresh-only truth unchanged

m=m.replace('map.setMinZoomPreference(4.8);','map.setMinZoomPreference(5.35); // V0883_NEPAL_MIN_ZOOM',1)
m=m.replace('Math.max(4.8, Math.min(19.0, current + delta))','Math.max(5.35, Math.min(19.0, current + delta))',1)
m=m.replace('.target(NEPAL_CENTER).zoom(5.4).tilt(terrain ? 28.0 : 0.0).bearing(0.0).build();',
            '.target(NEPAL_CENTER).zoom(5.65).tilt(0.0).bearing(0.0).build(); // V0883_SAFE_NEPAL_OVERVIEW',1)

# Tighten bounds so a full zoom-out remains a readable Nepal map rather than showing
# giant neighbouring-map labels / rotated world imagery.
m=m.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();',
            '.include(new LatLng(25.95, 79.65))\n                        .include(new LatLng(30.75, 88.70)).build(); // V0883_TIGHT_NEPAL_CAMERA_BOUNDS',1)

# v0.8.81 inserts waterbody priority. Replace the remaining broad station-first block.
old='''        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        double stationThreshold = Math.max(0.6, 28.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        if (nearest != null && km(p.getLatitude(), p.getLongitude(), nearest.lat, nearest.lon) <= stationThreshold) {
            if (stationTapListener != null) stationTapListener.onStationTap(nearest.original);
            return true;
        }
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.35, 18.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) {
            showRiver(rw, p.getLatitude(), p.getLongitude());
            return true;
        }
'''
new='''        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        // A station only captures a tap very close to its visible dot. This prevents a nearby
        // station from swallowing taps intended for a river/khola line.
        double stationThreshold = Math.max(0.12, 2.8 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        if (nearest != null && km(p.getLatitude(), p.getLongitude(), nearest.lat, nearest.lon) <= stationThreshold) {
            if (stationTapListener != null) stationTapListener.onStationTap(nearest.original);
            return true;
        }
        // River hit target is intentionally wider than the rendered stroke for finger use.
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.22, 7.5 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) {
            showRiver(rw, p.getLatitude(), p.getLongitude());
            return true;
        } // V0883_RIVER_TAP_PRIORITY
'''
if old not in m:
    # v0.8.81 may have inserted waterbody code between zoom and station block; replace pieces.
    m=m.replace('double stationThreshold = Math.max(0.6, 28.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));',
                'double stationThreshold = Math.max(0.12, 2.8 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))); // V0883_STATION_TAP_ONLY_ON_DOT',1)
    m=m.replace('RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.35, 18.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));',
                'RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.22, 7.5 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)))); // V0883_RIVER_TAP_PRIORITY',1)
else:
    m=m.replace(old,new,1)

# Improve unnamed river wording: identity/type still appears, official gauge is never guessed.
m=m.replace('String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");',
'''String riverName=named?r.name:(englishUi?"Mapped river / stream":"नक्सामा रहेको नदी / खोला");
        b.append(englishUi?"Waterway type: ":"जलमार्ग प्रकार: ").append(r==null||r.type==null?"stream":r.type); // V0883_ALWAYS_IDENTIFY_RIVER_TYPE''',1)

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
