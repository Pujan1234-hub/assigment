from pathlib import Path
import re

root = Path(__file__).resolve().parent
pkg = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
splash_p = pkg / 'PJBuiltsSplashActivity.java'
full_p = pkg / 'NativeFullActivity.java'
map_p = pkg / 'FloodSafeNativeMapView.java'
gradle_p = root / 'app/build.gradle'

splash = splash_p.read_text(encoding='utf-8')
full = full_p.read_text(encoding='utf-8')
mp = map_p.read_text(encoding='utf-8')
gradle = gradle_p.read_text(encoding='utf-8')

# 1) Stop launching the legacy WebView shell. The existing native dashboard already
# owns weather, realtime river stations, risk cards, SATHI, alerts and monitoring.
old = 'Intent app = new Intent(this, VoiceMainActivity.class);'
if old not in splash and 'Intent app = new Intent(this, NativeFullActivity.class);' not in splash:
    raise SystemExit('v0885 splash launcher anchor missing')
splash = splash.replace(old, 'Intent app = new Intent(this, NativeFullActivity.class); // V0885_NATIVE_LAUNCHER', 1)

# 2) Swap the older Canvas river widget in NativeFullActivity for the existing
# MapLibre-native map. Its API intentionally mirrors the old widget, so the full
# native dashboard keeps the same realtime station feed and controls.
if 'private FloodSafeNativeMapView map;' not in full:
    full, n = re.subn(r'private NativeRiverMap map;', 'private FloodSafeNativeMapView map; // V0885_MAPLIBRE_NATIVE', full, count=1)
    if n != 1:
        raise SystemExit('v0885 native map field anchor missing')

old_holder = 'FrameLayout holder=new FrameLayout(this);map=new NativeRiverMap();holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));'
new_holder = ('FrameLayout holder=new FrameLayout(this);'
              'map=new FloodSafeNativeMapView(this,stationObject->{if(stationObject instanceof RiverStation)showStation((RiverStation)stationObject);});'
              'holder.addView(map,new FrameLayout.LayoutParams(-1,dp(420))); // V0885_MAPLIBRE_NATIVE')
if old_holder in full:
    full = full.replace(old_holder, new_holder, 1)
elif 'V0885_MAPLIBRE_NATIVE' not in full:
    raise SystemExit('v0885 map holder anchor missing')

# Source parity: do not hide the official latest record merely because an app-defined
# number of minutes elapsed. We still reject timestamps implausibly in the future and
# always show the official observation age to the user.
old_fresh = 'boolean fresh=at>0&&now-at<=RIVER_FRESH_MS&&at-now<=5*60_000L;'
new_fresh = 'boolean fresh=at>0&&at-now<=5*60_000L; // V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF'
if old_fresh in full:
    full = full.replace(old_fresh, new_fresh, 1)
elif 'V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF' not in full:
    raise SystemExit('v0885 station freshness anchor missing')

# 3) Make MapLibre taps river-first except when the user is actually on a station dot.
mp, n = re.subn(
    r'double stationThreshold = Math\.max\(0\.6, 28\.0 / Math\.pow\(2\.0, Math\.max\(0\.0, zoom - 6\.0\)\)\);',
    'double stationThreshold = Math.max(0.12, 2.8 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))); // V0885_STATION_DOT_HITBOX',
    mp, count=1)
if n == 0 and 'V0885_STATION_DOT_HITBOX' not in mp:
    raise SystemExit('v0885 station hitbox anchor missing')
mp, n = re.subn(
    r'RiverWay rw = nearestRiver\(p\.getLatitude\(\), p\.getLongitude\(\), Math\.max\(0\.35, 18\.0 / Math\.pow\(2\.0, Math\.max\(0\.0, zoom - 6\.0\)\)\)\);',
    'RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.22, 7.5 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)))); // V0885_RIVER_FIRST_TAP',
    mp, count=1)
if n == 0 and 'V0885_RIVER_FIRST_TAP' not in mp:
    raise SystemExit('v0885 river hitbox anchor missing')

# Tighten Nepal overview and make rivers visually clearer while keeping native gestures.
mp = mp.replace('map.setMinZoomPreference(4.8);', 'map.setMinZoomPreference(5.15); // V0885_NATIVE_MIN_ZOOM', 1)
mp = mp.replace('Math.max(4.8, Math.min(19.0, current + delta))', 'Math.max(5.15, Math.min(19.0, current + delta))', 1)
mp = mp.replace('.target(NEPAL_CENTER).zoom(5.4).tilt(terrain ? 28.0 : 0.0)', '.target(NEPAL_CENTER).zoom(5.65).tilt(terrain ? 22.0 : 0.0)', 1)
mp = mp.replace('lineWidth(4.0f), lineOpacity(0.55f)', 'lineWidth(5.0f), lineOpacity(0.58f)', 1)
mp = mp.replace('lineWidth(1.65f), lineOpacity(0.96f)', 'lineWidth(2.15f), lineOpacity(0.98f)', 1)

# Same-river gauge only. Never attach an unrelated nearby station to a tapped river.
old_gauge = 'StationDot gauge = nearestStation(la, lo);'
if old_gauge in mp:
    mp = mp.replace(old_gauge, 'StationDot gauge = nearestSameRiverStation(r, la, lo); // V0885_SAME_RIVER_GAUGE_ONLY', 1)
elif 'V0885_SAME_RIVER_GAUGE_ONLY' not in mp:
    raise SystemExit('v0885 river gauge anchor missing')

if 'private StationDot nearestSameRiverStation(' not in mp:
    marker = '    private void showRiver(RiverWay r, double la, double lo) {'
    helper = r'''    private StationDot nearestSameRiverStation(RiverWay r, double la, double lo) {
        if (r == null) return null;
        String rk = riverKey(r.name);
        if (rk.length() < 3) return null;
        StationDot best = null;
        double bestKm = Double.MAX_VALUE;
        synchronized (stations) {
            for (StationDot s : stations) {
                String sk = riverKey(s.name);
                if (!sameRiverKey(rk, sk)) continue;
                double d = km(la, lo, s.lat, s.lon);
                if (d < bestKm) { bestKm = d; best = s; }
            }
        }
        return best;
    }

    private static String riverKey(String s) {
        if (s == null) return "";
        String k = s.toLowerCase(Locale.ROOT)
                .replace("river", " ").replace("khola", " ").replace("khola", " ")
                .replace("nadi", " ").replace("station", " ").replace("gauge", " ")
                .replace("bridge", " ").replaceAll("[^\\p{L}\\p{N}]+", " ").trim();
        return k.replaceAll("\\s+", " ");
    }

    private static boolean sameRiverKey(String a, String b) {
        if (a == null || b == null || a.length() < 3 || b.length() < 3) return false;
        if (a.contains(b) || b.contains(a)) return true;
        String[] aa = a.split(" "), bb = b.split(" ");
        for (String x : aa) if (x.length() >= 4) for (String y : bb) if (x.equals(y)) return true;
        return false;
    }

'''
    if marker not in mp:
        raise SystemExit('v0885 showRiver insertion anchor missing')
    mp = mp.replace(marker, helper + marker, 1)

mp = mp.replace('msg.append("नजिकको official gauge: ")', 'msg.append("यही नदीसँग मिलेको official gauge: ")', 1)
mp = mp.replace('} else msg.append("यो नदी segment नजिक direct official gauge reference भेटिएन।");',
                '} else msg.append("यो नदी/खोलासँग नाम मिलेको direct official gauge reference भेटिएन।");', 1)
if 'River type:' not in mp:
    mp = mp.replace('msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");',
                    'msg.append("\\nRiver type: ").append(r.type == null ? "stream" : r.type);\n        msg.append("\\n\\nRiver geometry: OpenStreetMap / FloodSafe bundled network");', 1)

# Reduce decorative particle work so pan/pinch/zoom remain smooth on mid/low-end phones.
mp = mp.replace('int n = Math.min(36, rivers.size());', 'int n = Math.min(20, rivers.size()); // V0885_SMOOTH_PARTICLES', 1)
mp = mp.replace('main.postDelayed(this, 160L);', 'main.postDelayed(this, 360L);', 1)

# 4) Actual installable app version bump so Android treats this as the newer build.
gradle = re.sub(r'versionCode\s+14\b', 'versionCode 15', gradle, count=1)
gradle = gradle.replace("versionName '0.7.0'", "versionName '0.8.85'", 1)
if 'versionCode 15' not in gradle or "versionName '0.8.85'" not in gradle:
    raise SystemExit('v0885 version bump failed')

contracts = [
    'V0885_NATIVE_LAUNCHER','V0885_MAPLIBRE_NATIVE','V0885_SOURCE_LATEST_NO_APP_MINUTE_CUTOFF',
    'V0885_STATION_DOT_HITBOX','V0885_RIVER_FIRST_TAP','V0885_SAME_RIVER_GAUGE_ONLY',
    'V0885_NATIVE_MIN_ZOOM','V0885_SMOOTH_PARTICLES'
]
joined = splash + full + mp
for c in contracts:
    if c not in joined:
        raise SystemExit('v0885 contract missing: ' + c)

splash_p.write_text(splash, encoding='utf-8')
full_p.write_text(full, encoding='utf-8')
map_p.write_text(mp, encoding='utf-8')
gradle_p.write_text(gradle, encoding='utf-8')
print('FloodSafe v0.8.85 PASS: native launcher + MapLibre river map + river-first/same-river detail + source-latest parity + smoother rendering')
