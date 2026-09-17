from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.37 root fix from the 17:17 real-phone screenshot:
# The river layer was still blank because every startup parsed 6k+ overview waterways and
# ran expensive 77-district clipping on-device before publishing fs-rivers. Station dots
# appeared first, making it look like rivers were missing forever. CI now pre-clips ALL
# overview/tile assets against Nepal once. Android therefore publishes the already-safe
# river network immediately, like the GitHub web video.
# MAP ONLY. Alerts/notifications/home/SATHI/navigation remain untouched.

old='''                // Exact 77-district union stays authoritative before anything becomes visible.\n                List<RiverWay> safeAll=all;\n                try{\n                    if(districtGeoJson!=null){\n                        JSONObject nepalRoot=new JSONObject(districtGeoJson);\n                        List<RiverWay> clipped=clipWaysToNepalDense(all,nepalRoot);\n                        if(clipped!=null&&!clipped.isEmpty())safeAll=clipped;\n                    }\n                }catch(Exception ignoredClip){}\n                safeAll.sort(Comparator.comparingInt(FloodSafeNativeMapView::riverScore).reversed());'''
new='''                // PRECLIPPED_BUILD_ASSET: CI already intersected this file with the exact Nepal\n                // 77-district union, so publish immediately instead of doing a huge phone-side clip.\n                List<RiverWay> safeAll=all;\n                safeAll.sort(Comparator.comparingInt(FloodSafeNativeMapView::riverScore).reversed());'''
if old in m:
    m=m.replace(old,new,1)
elif 'PRECLIPPED_BUILD_ASSET' not in m:
    raise SystemExit('v0.8.37 startup clip anchor missing')

# Local tiles are also build-time Nepal-clipped. Never re-run the expensive polygon clip on
# camera idle; direct publish keeps rivers visible during/after zoom just like the web map.
old2='List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);'
new2='List<RiverWay> chosen=candidates; // PRECLIPPED_TILE_ASSET'
if old2 in m:
    m=m.replace(old2,new2,1)
elif 'PRECLIPPED_TILE_ASSET' not in m:
    raise SystemExit('v0.8.37 local clip anchor missing')

# The renderer helper may create an otherwise-unused Nepal object after pre-clipping; harmless,
# but removing it avoids any needless parse on every camera idle.
m=m.replace('                JSONObject nepal=new JSONObject(districtGeoJson);\n                List<RiverWay> candidates=',
            '                List<RiverWay> candidates=',1)

# Make the web-video river style unmistakable over satellite imagery: thin cyan core + blue glow.
# This base style is geographic context. Official warning/danger overlays remain source-driven.
for old_s,new_s in [
    ('lineColor("#1EC8FF"), lineWidth(2.35f), lineOpacity(1.0f)',
     'lineColor("#22D7FF"), lineWidth(2.45f), lineOpacity(1.0f)'),
    ('lineColor("#078BFF"), lineWidth(5.6f), lineOpacity(0.34f)',
     'lineColor("#087CFF"), lineWidth(6.4f), lineOpacity(0.42f)'),
    ('lineWidth((float)(4.8+1.6*wave))','lineWidth((float)(5.3+1.9*wave))'),
    ('lineWidth((float)(2.05+0.45*wave))','lineWidth((float)(2.15+0.50*wave))')]:
    if old_s in m:m=m.replace(old_s,new_s,1)

# Compatibility with any retained v0.8.34 variants.
m=m.replace('lineColor("#22C8FF"), lineWidth(2.20f), lineOpacity(1.0f)',
            'lineColor("#22D7FF"), lineWidth(2.45f), lineOpacity(1.0f)',1)
m=m.replace('lineColor("#0D8DFF"), lineWidth(5.6f), lineOpacity(0.34f)',
            'lineColor("#087CFF"), lineWidth(6.4f), lineOpacity(0.42f)',1)
m=m.replace('lineColor("#1EC8FF")','lineColor("#22D7FF")')
m=m.replace('lineColor("#078BFF")','lineColor("#087CFF")')

# Hide normal/stale river gauge dots at national/mid view so the river network is what the
# user sees. Severe gauges remain visible; local zoom still shows current gauge dots.
# Data remains loaded and river taps still use sameRiverGaugeFor().
rs=m.find('    private void refreshStationSources() {')
re_=m.find('    private void refreshRainSources()',rs)
if rs>=0 and re_>rs:
    station_refresh=r'''    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot; synchronized (stations) { snapshot = new ArrayList<>(stations); }
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        boolean local=zoom>=8.2;
        setGeo("fs-stale", local?stationGeo(snapshot,"stale"):emptyFeatureCollection());
        setGeo("fs-normal", local?stationGeo(snapshot,"normal"):emptyFeatureCollection());
        setGeo("fs-alert", stationGeo(snapshot,"alert"));
        setGeo("fs-warning", stationGeo(snapshot,"warning"));
        setGeo("fs-danger", stationGeo(snapshot,"danger"));
        refreshRiverStatusSources();
    }

'''
    m=m[:rs]+station_refresh+m[re_:]
else:
    raise SystemExit('v0.8.37 station refresh anchors missing')

# Camera zoom changes station-dot visibility as well as the preclipped river tiles.
cam='map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);'
if cam in m and 'map.addOnCameraIdleListener(this::refreshStationSources);' not in m:
    m=m.replace(cam,cam+'\n            map.addOnCameraIdleListener(this::refreshStationSources);',1)

# Version bump.
g=g.replace('versionCode 56','versionCode 57',1).replace("versionName '0.8.36'","versionName '0.8.37'",1)
if 'versionCode 57' not in g or "versionName '0.8.37'" not in g:
    raise SystemExit('v0.8.37 version bump failed')

# Gates requested by user: actual river network visible, no rain dots, river+rain one card,
# official same-river truth, safety untouched.
for marker in [
    'PRECLIPPED_BUILD_ASSET',
    'PRECLIPPED_TILE_ASSET',
    'setGeo("fs-rivers",riversGeoJson)',
    'setGeo("fs-rivers",geo)',
    'lineColor("#22D7FF")',
    'lineColor("#087CFF")',
    'RAIN_DATA_DETAIL_ONLY',
    'RainDot rain=nearestRain(la,lo)',
    'new RiverTapInfo("🌊 "+title',
    'sameRiverGaugeFor(r,la,lo,true)',
    'routeD<=0.75']:
    if marker not in m:raise SystemExit('v0.8.37 marker missing: '+marker)
if 'RainDot rain=nearestRain(p.getLatitude(),p.getLongitude())' in m:
    raise SystemExit('v0.8.37 rain map click returned')
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a:raise SystemExit('v0.8.37 alert safety changed: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.37 PRECLIPPED visible Nepal rivers + combined river/rain detail PASS')
