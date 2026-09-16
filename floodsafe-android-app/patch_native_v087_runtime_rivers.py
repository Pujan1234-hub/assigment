from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
helper_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
helper = helper_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# v0.8.7 runtime fix:
# v0.8.6 clipped every point of thousands of waterways against all 77 district
# polygons before the GeoJSON source was published. On phones this can leave the
# station layer visible while the river layer is still doing expensive geometry
# work. Keep continuous river geometry, but decide whether a whole way touches
# Nepal using a small set of sampled points. This is orders of magnitude cheaper.
slow_overview = 'if (nepalDistricts != null && rw.points.size() >= 2) trimRiverToNepal(rw, nepalDistricts);'
fast_overview = 'if (nepalDistricts != null && rw.points.size() >= 2 && !riverTouchesNepalFast(rw, nepalDistricts)) rw.points.clear();'
if slow_overview in helper:
    helper = helper.replace(slow_overview, fast_overview, 1)
elif fast_overview not in helper:
    raise SystemExit('overview river clipping anchor missing')

slow_tile = 'if(districts!=null&&rw.points.size()>=2)trimRiverToNepal(rw,districts);'
fast_tile = 'if(districts!=null&&rw.points.size()>=2&&!riverTouchesNepalFast(rw,districts))rw.points.clear();'
if slow_tile in helper:
    helper = helper.replace(slow_tile, fast_tile, 1)
elif fast_tile not in helper:
    raise SystemExit('tile river clipping anchor missing')

anchor = '    private static boolean insideNepalSoft(double lo,double la,JSONObject districtRoot) {'
method = r'''    private static boolean riverTouchesNepalFast(RiverWay r, JSONObject districtRoot) {
        if (r == null || r.points.size() < 2 || districtRoot == null) return r != null && r.points.size() >= 2;
        int n = r.points.size();
        int checks = Math.min(5, n);
        for (int i = 0; i < checks; i++) {
            int ix = checks == 1 ? 0 : Math.min(n - 1, (int)Math.round((n - 1) * (i / (double)(checks - 1))));
            double[] p = r.points.get(ix);
            if (insideDistricts(p[0], p[1], districtRoot)) return true;
        }
        // One tolerant midpoint check keeps legitimate border rivers without
        // paying the old per-point polygon cost.
        double[] mid = r.points.get(n / 2);
        return insideNepalSoft(mid[0], mid[1], districtRoot);
    }

'''
if 'private static boolean riverTouchesNepalFast' not in helper:
    if anchor not in helper:
        raise SystemExit('insideNepalSoft anchor missing')
    helper = helper.replace(anchor, method + anchor, 1)

# Make stale/unknown stations informational instead of letting hundreds of grey
# circles visually cover the river network at the Nepal overview.
helper = helper.replace(
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);',
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 2.1f, 0.40f);', 1)

# Only label fresh high-risk stations. Fresh NORMAL remains a blue clickable dot;
# stale stations remain faint grey. This keeps safety semantics honest while
# preventing the national map from becoming a wall of grey text.
helper = helper.replace(
    'setGeo("fs-station-labels", stationGeoAll(snapshot));',
    'setGeo("fs-station-labels", stationGeoImportant(snapshot));', 1)

station_anchor = '    private static String stationGeoAll(List<StationDot> list) {'
station_method = r'''    private static String stationGeoImportant(List<StationDot> list) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                if (!s.fresh) continue;
                String g = normalizeStage(s.stage);
                if (!("danger".equals(g) || "warning".equals(g) || "alert".equals(g))) continue;
                f.put(pointFeature(s.lon, s.lat, s.name));
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }

'''
if 'private static String stationGeoImportant' not in helper:
    if station_anchor not in helper:
        raise SystemExit('stationGeoAll anchor missing')
    helper = helper.replace(station_anchor, station_method + station_anchor, 1)

# Stronger national visibility over satellite imagery. These are visual map lines;
# official station freshness/status remains the realtime risk source.
helper = helper.replace('lineColor("#00bde9"), lineWidth(7.4f), lineOpacity(0.58f)',
                        'lineColor("#00c9f4"), lineWidth(8.6f), lineOpacity(0.66f)', 1)
helper = helper.replace('lineColor("#7ceeff"), lineWidth(2.65f), lineOpacity(1.0f)',
                        'lineColor("#a5f6ff"), lineWidth(3.15f), lineOpacity(1.0f)', 1)

helper_path.write_text(helper, encoding='utf-8')

if "versionName '0.8.7'" not in gradle:
    gradle = gradle.replace('versionCode 26', 'versionCode 27', 1)
    gradle = gradle.replace("versionName '0.8.6'", "versionName '0.8.7'", 1)
if 'versionCode 27' not in gradle or "versionName '0.8.7'" not in gradle:
    raise SystemExit('v0.8.7 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index = index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.6</span>', '<span class="badge green">v0.8.7</span>')
    index_path.write_text(index, encoding='utf-8')

h = helper_path.read_text(encoding='utf-8')
for marker in [
    'riverTouchesNepalFast',
    '!riverTouchesNepalFast(rw, nepalDistricts)',
    '!riverTouchesNepalFast(rw,districts)',
    'stationGeoImportant(snapshot)',
    '"#8e99a5", 2.1f, 0.40f',
    'lineWidth(8.6f)',
    'lineWidth(3.15f)',
    'refreshVisibleRiverTiles',
]:
    if marker not in h:
        raise SystemExit('v0.8.7 runtime marker missing: ' + marker)
print('FloodSafe v0.8.7 fast river runtime + uncluttered fresh-status map patch PASS')
