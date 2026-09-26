from pathlib import Path
import re

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path = src / 'FloodSafeNativeMapView.java'
build_path = root / 'app/build.gradle'
m = map_path.read_text(encoding='utf-8')
g = build_path.read_text(encoding='utf-8')

if 'V0900_STATION_RIVERS_ONLY' in m:
    print('v0.9.00 station-rivers-only patch already applied')
    raise SystemExit(0)

def method_span(text, name):
    q = re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b' + re.escape(name) + r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{', text)
    if not q:
        return None
    op = text.find('{', q.start())
    depth = 0; quote = None; esc = False
    for i in range(op, len(text)):
        ch = text[i]
        if quote:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == quote: quote = None
        else:
            if ch in ('"', "'"): quote = ch
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0: return q.start(), i + 1
    return None

def replace_method(text, name, block):
    sp = method_span(text, name)
    if not sp: raise SystemExit('Missing method: ' + name)
    return text[:sp[0]] + block + text[sp[1]:]

def insert_before_method(text, name, block, marker):
    if marker in text: return text
    sp = method_span(text, name)
    if not sp: raise SystemExit('Missing insertion anchor: ' + name)
    return text[:sp[0]] + block + text[sp[0]:]

# Candidate river geometry remains loaded once in memory, but ONLY station-linked
# geometry is exposed to MapLibre's visible/animated fs-rivers source.
field_anchor = '    private final List<RiverWay> rivers = new ArrayList<>();\n'
if field_anchor not in m: raise SystemExit('river candidate field anchor missing')
m = m.replace(field_anchor, field_anchor +
'''    private final List<RiverWay> monitoredRivers = new ArrayList<>(); // V0900_STATION_RIVERS_ONLY\n    private final java.util.Map<String,List<RiverWay>> monitoredByStation = new java.util.HashMap<>();\n    private volatile String stationInventoryFingerprint = "";\n    private volatile String mappedInventoryFingerprint = "";\n    private volatile int monitoredSourceFeatureCount = 0;\n''', 1)

set_stations = r'''    void setStations(List<?> source, double lat, double lon) {
        userLat = lat;
        userLon = lon;
        List<StationDot> next = new ArrayList<>();
        if (source != null) {
            for (Object o : source) {
                StationDot s = readStation(o);
                if (s != null) next.add(s);
            }
        }
        synchronized (stations) {
            stations.clear();
            stations.addAll(next);
        }
        String inventory = stationInventoryFingerprint(next);
        boolean inventoryChanged = !inventory.equals(stationInventoryFingerprint);
        stationInventoryFingerprint = inventory;
        if (inventoryChanged || !inventory.equals(mappedInventoryFingerprint)) {
            io.execute(() -> rebuildMonitoredRiverMapping(inventory));
        }
        refreshStationSources();
        refreshRiskRiverSources();
        refreshUserSource();
    } // V0900_MAP_ON_INVENTORY_CHANGE_ONLY
'''
m = replace_method(m, 'setStations', set_stations)

load_geometry = r'''    private void loadBundledGeometry() {
        io.execute(() -> {
            try {
                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");
            } catch (Exception ignored) {
                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}
            }
            try {
                String raw;
                String assetPath = "data/nepal-waterways-tiles/overview.json";
                try { raw = readAsset(assetPath); }
                catch (Exception e) {
                    assetPath = "data/nepal-waterways-snapshot.json";
                    raw = readAsset(assetPath);
                }
                JSONObject root = new JSONObject(raw);
                JSONArray ways = root.optJSONArray("waterways");
                List<RiverWay> all = new ArrayList<>();
                if (ways != null) {
                    for (int i = 0; i < ways.length(); i++) {
                        JSONObject w = ways.optJSONObject(i);
                        if (w == null) continue;
                        JSONArray pts = w.optJSONArray("pts");
                        if (pts == null || pts.length() < 2) continue;
                        RiverWay rw = new RiverWay();
                        rw.name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");
                        rw.type = w.optString("type", "stream");
                        for (int j = 0; j < pts.length(); j++) {
                            JSONArray p = pts.optJSONArray(j);
                            if (p == null || p.length() < 2) continue;
                            double lo = p.optDouble(0, Double.NaN), la = p.optDouble(1, Double.NaN);
                            if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo)) rw.points.add(new double[]{lo, la});
                        }
                        if (rw.points.size() >= 2) all.add(rw);
                    }
                }
                synchronized (rivers) {
                    rivers.clear();
                    rivers.addAll(all);
                }
                // Critical: never render the candidate/full Nepal mesh.
                riversGeoJson = emptyFeatureCollection();
                android.util.Log.i("FloodSafeRiver", "candidate_geometry=" + all.size() + " visible_station_rivers=0 asset=" + assetPath);
                String inv = stationInventoryFingerprint;
                if (!inv.isEmpty()) rebuildMonitoredRiverMapping(inv);
            } catch (Exception e) {
                android.util.Log.e("FloodSafeRiver", "candidate geometry load failed", e);
            }
            main.post(this::installGeoLayers);
        });
    } // V0900_FULL_NETWORK_NEVER_RENDERED
'''
m = replace_method(m, 'loadBundledGeometry', load_geometry)

mapping_helpers = r'''    private static String stationInventoryFingerprint(List<StationDot> list) {
        List<String> parts = new ArrayList<>();
        if (list != null) for (StationDot s : list) {
            if (s == null) continue;
            parts.add(stationKey(s) + "|" + riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name)));
        }
        Collections.sort(parts);
        StringBuilder b = new StringBuilder();
        for (String p : parts) b.append(p).append('\n');
        return parts.size() + ":" + Integer.toHexString(b.toString().hashCode());
    }

    private static String stationKey(StationDot s) {
        if (s == null) return "";
        return riverKey(s.name) + "@" + String.format(Locale.US, "%.4f,%.4f", s.lat, s.lon);
    }

    private void rebuildMonitoredRiverMapping(String requestedInventory) {
        if (requestedInventory == null || requestedInventory.isEmpty()) return;
        List<StationDot> ss;
        List<RiverWay> candidates;
        synchronized (stations) { ss = new ArrayList<>(stations); }
        synchronized (rivers) { candidates = new ArrayList<>(rivers); }
        if (ss.isEmpty() || candidates.isEmpty()) return;
        java.util.LinkedHashSet<RiverWay> visible = new java.util.LinkedHashSet<>();
        java.util.Map<String,List<RiverWay>> byStation = new java.util.HashMap<>();
        int exact = 0, fallback = 0, unmatched = 0;
        String sample = "";
        for (StationDot s : ss) {
            RiverWay seed = seedRiverForStation(s, candidates);
            if (seed == null) { unmatched++; continue; }
            String wanted = riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name));
            boolean named = !wanted.isEmpty() && sameRiverKey(wanted, riverKey(seed.name));
            if (named) exact++; else fallback++;
            List<RiverWay> local = localConnectedRiverSegments(s, seed, candidates, named);
            if (local.isEmpty()) local = Collections.singletonList(seed);
            visible.addAll(local);
            byStation.put(stationKey(s), new ArrayList<>(local));
            String probe = ((s.name == null ? "" : s.name) + " " + (s.riverName == null ? "" : s.riverName)).toLowerCase(Locale.ROOT);
            if (sample.isEmpty() && (probe.contains("bagmati") || probe.contains("gaurighat"))) {
                sample = s.name + " -> " + seed.name + " segments=" + local.size();
            }
        }
        if (!requestedInventory.equals(stationInventoryFingerprint)) return;
        List<RiverWay> next = new ArrayList<>(visible);
        String geo = makeRiversGeoJsonSafe(next);
        synchronized (monitoredRivers) {
            monitoredRivers.clear();
            monitoredRivers.addAll(next);
        }
        synchronized (monitoredByStation) {
            monitoredByStation.clear();
            monitoredByStation.putAll(byStation);
        }
        riversGeoJson = geo;
        monitoredSourceFeatureCount = next.size();
        mappedInventoryFingerprint = requestedInventory;
        android.util.Log.i("FloodSafeRiver", "station_linked_features=" + next.size() + " stations=" + ss.size()
                + " exact=" + exact + " coordinate_fallback=" + fallback + " unmatched=" + unmatched
                + (sample.isEmpty() ? "" : " sample=" + sample));
        main.post(() -> {
            if (styleReady && style != null) {
                if (style.getSource("fs-rivers") == null) installGeoLayers();
                setGeo("fs-rivers", riversGeoJson);
                refreshRiskRiverSources();
            }
        });
    } // V0900_BUILD_MAPPING_ONCE

    private RiverWay seedRiverForStation(StationDot s, List<RiverWay> candidates) {
        if (s == null || candidates == null || candidates.isEmpty()) return null;
        String wanted = riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name));
        RiverWay best = null; double bestD = Double.POSITIVE_INFINITY;
        if (!wanted.isEmpty()) {
            for (RiverWay r : candidates) {
                if (!sameRiverKey(wanted, riverKey(r.name))) continue;
                double d = distanceToRiverKm(s.lat, s.lon, r);
                if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
            }
            if (best != null && bestD <= 10.0) return best;
        }
        // Coordinate fallback is intentionally strict and used only when name matching fails.
        best = null; bestD = Double.POSITIVE_INFINITY;
        for (RiverWay r : candidates) {
            double d = distanceToRiverKm(s.lat, s.lon, r);
            if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
        }
        return bestD <= 0.85 ? best : null;
    } // V0900_NAME_FIRST_STRICT_COORD_FALLBACK

    private List<RiverWay> localConnectedRiverSegments(StationDot s, RiverWay seed, List<RiverWay> candidates, boolean namedMatch) {
        java.util.LinkedHashSet<RiverWay> out = new java.util.LinkedHashSet<>();
        out.add(seed);
        String key = riverKey(seed.name);
        if (key.isEmpty() || !namedMatch) return new ArrayList<>(out);
        for (int round = 0; round < 5; round++) {
            boolean changed = false;
            List<RiverWay> current = new ArrayList<>(out);
            for (RiverWay r : candidates) {
                if (out.contains(r) || !sameRiverKey(key, riverKey(r.name))) continue;
                double stationD = distanceToRiverKm(s.lat, s.lon, r);
                if (!Double.isFinite(stationD) || stationD > 35.0) continue;
                boolean connected = stationD <= 2.0;
                if (!connected) {
                    for (RiverWay have : current) {
                        if (riverGapKm(have, r) <= 1.25) { connected = true; break; }
                    }
                }
                if (connected) { out.add(r); changed = true; }
            }
            if (!changed) break;
        }
        return new ArrayList<>(out);
    } // V0900_LOCAL_SAME_RIVER_ONLY

    private static double riverGapKm(RiverWay a, RiverWay b) {
        if (a == null || b == null || a.points.isEmpty() || b.points.isEmpty()) return Double.POSITIVE_INFINITY;
        double best = Double.POSITIVE_INFINITY;
        double[][] ae = {a.points.get(0), a.points.get(a.points.size()-1)};
        double[][] be = {b.points.get(0), b.points.get(b.points.size()-1)};
        for (double[] x : ae) for (double[] y : be) best = Math.min(best, km(x[1], x[0], y[1], y[0]));
        return best;
    }

    private List<RiverWay> stationSegments(StationDot s) {
        if (s == null) return Collections.emptyList();
        synchronized (monitoredByStation) {
            List<RiverWay> found = monitoredByStation.get(stationKey(s));
            return found == null ? Collections.emptyList() : new ArrayList<>(found);
        }
    }

'''
m = insert_before_method(m, 'installGeoLayers', mapping_helpers, 'V0900_BUILD_MAPPING_ONCE')

install = r'''    private void installGeoLayers() {
        if (!styleReady || style == null) return;
        try {
            if (districtGeoJson != null && style.getSource("fs-districts") == null) {
                style.addSource(new GeoJsonSource("fs-districts", districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill", "fs-districts").withProperties(
                        fillColor("#8deeff"), fillOpacity(0.06f)));
                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(
                        lineColor("#e8fbff"), lineWidth(1.05f), lineOpacity(0.74f), lineJoin(LINE_JOIN_ROUND)));
            }
            if (style.getSource("fs-rivers") == null) {
                style.addSource(new GeoJsonSource("fs-rivers", riversGeoJson == null ? emptyFeatureCollection() : riversGeoJson));
                style.addLayer(new LineLayer("fs-river-glow", "fs-rivers").withProperties(
                        lineColor("#007ea6"), lineWidth(5.8f), lineOpacity(0.50f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(
                        lineColor("#42ddff"), lineWidth(2.35f), lineOpacity(0.99f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
                android.util.Log.i("FloodSafeRiver", "station-only river layers active glow=5.8/0.50 core=2.35/0.99");
            }
            ensureLineSource("fs-river-alert-risk", "fs-river-alert-risk-layer", "#ffd43b", 3.4f, 0.98f);
            ensureLineSource("fs-river-warning-risk", "fs-river-warning-risk-layer", "#ff8a1f", 4.0f, 1f);
            ensureLineSource("fs-river-danger-risk", "fs-river-danger-risk-layer", "#f22f4b", 4.6f, 1f);
            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#e3fdff", 2.35f, 0.92f);
            ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);
            ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f);
            ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 5.0f, 1f);
            ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 5.8f, 1f);
            ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f);
            if (style.getSource("fs-user") == null) {
                style.addSource(new GeoJsonSource("fs-user", emptyFeatureCollection()));
                style.addLayer(new CircleLayer("fs-user-halo", "fs-user").withProperties(
                        circleColor("#ffffff"), circleRadius(9.0f), circleOpacity(0.72f)));
                style.addLayer(new CircleLayer("fs-user-layer", "fs-user").withProperties(
                        circleColor("#0b7fd0"), circleRadius(5.7f), circleStrokeColor("#ffffff"), circleStrokeWidth(1.5f)));
            }
            if (riversGeoJson != null) setGeo("fs-rivers", riversGeoJson);
            refreshStationSources();
            refreshRiskRiverSources();
            refreshUserSource();
        } catch (Exception e) {
            android.util.Log.e("FloodSafeRiver", "station-only layer install failed", e);
        }
    } // V0900_VISIBLE_SOURCE_IS_MONITORED_ONLY
'''
m = replace_method(m, 'installGeoLayers', install)

nearest = r'''    private RiverWay nearestRiver(double la, double lo, double thresholdKm) {
        RiverWay best = null; double d = Double.MAX_VALUE;
        synchronized (monitoredRivers) {
            for (RiverWay r : monitoredRivers) {
                double x = distanceToRiverKm(la, lo, r);
                if (x < d) { d = x; best = r; }
            }
        }
        return d <= thresholdKm ? best : null;
    } // V0900_TAP_ONLY_MONITORED_RIVERS
'''
m = replace_method(m, 'nearestRiver', nearest)

risk = r'''    private void refreshRiskRiverSources() {
        if (!styleReady || style == null) return;
        java.util.LinkedHashSet<RiverWay> alert = new java.util.LinkedHashSet<>();
        java.util.LinkedHashSet<RiverWay> warning = new java.util.LinkedHashSet<>();
        java.util.LinkedHashSet<RiverWay> danger = new java.util.LinkedHashSet<>();
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        for (StationDot s : snapshot) {
            if (s == null || !s.fresh) continue;
            String group = normalizeStage(s.stage);
            if (!("alert".equals(group) || "warning".equals(group) || "danger".equals(group))) continue;
            List<RiverWay> linked = stationSegments(s);
            if (linked.isEmpty()) continue;
            if ("danger".equals(group)) danger.addAll(linked);
            else if ("warning".equals(group)) warning.addAll(linked);
            else alert.addAll(linked);
        }
        setGeo("fs-river-alert-risk", makeRiversGeoJsonSafe(new ArrayList<>(alert)));
        setGeo("fs-river-warning-risk", makeRiversGeoJsonSafe(new ArrayList<>(warning)));
        setGeo("fs-river-danger-risk", makeRiversGeoJsonSafe(new ArrayList<>(danger)));
    } // V0900_STATUS_COLOURS_LINKED_SEGMENTS_ONLY
'''
m = replace_method(m, 'refreshRiskRiverSources', risk)

matched = r'''    private RiverWay matchedRiverForStation(StationDot s) {
        List<RiverWay> linked = stationSegments(s);
        if (!linked.isEmpty()) return linked.get(0);
        return null;
    } // V0900_REUSE_PREBUILT_STATION_MAPPING
'''
m = replace_method(m, 'matchedRiverForStation', matched)

# Replace the moving-flow runnable so it can never animate an unmonitored candidate river.
start = m.find('    private final Runnable particleTick = new Runnable() {')
end = m.find('    private StationDot readStation(', start)
if start < 0 or end < 0: raise SystemExit('particle runnable span missing')
particle = r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if (!animationRunning || !styleReady || style == null) return;
            try {
                List<RiverWay> visible;
                synchronized (monitoredRivers) { visible = new ArrayList<>(monitoredRivers); }
                JSONArray features = new JSONArray();
                int n = visible.size();
                double phase = ((System.currentTimeMillis() - particleStart) % 5600L) / 5600.0;
                for (int i = 0; i < n; i++) {
                    RiverWay r = visible.get(i);
                    if (r.points.size() < 2) continue;
                    double v = ((phase + i * 0.137) % 1.0) * (r.points.size() - 1);
                    int ix = Math.min(r.points.size() - 2, (int)Math.floor(v));
                    double f = v - ix;
                    double[] a = r.points.get(ix), b = r.points.get(ix + 1);
                    double lo = a[0] + (b[0] - a[0]) * f, la = a[1] + (b[1] - a[1]) * f;
                    features.put(pointFeature(lo, la, "flow"));
                }
                JSONObject fc = new JSONObject().put("type", "FeatureCollection").put("features", features);
                setGeo("fs-flow-particles", fc.toString());
                animationFrameCount++;
                if (animationFrameCount == 1 || animationFrameCount % 30L == 0L) {
                    android.util.Log.i("FloodSafeRiver", "flow_frame=" + animationFrameCount + " animated_station_features=" + n
                            + " source_features=" + monitoredSourceFeatureCount);
                }
            } catch (Exception ignored) {}
            main.postDelayed(this, 180L);
        }
    }; // V0900_ANIMATION_MONITORED_SOURCE_ONLY

'''
m = m[:start] + particle + m[end:]

# Camera/river coordinate clipping uses the actual Nepal app bounds, not the wider padding box.
m = m.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();',
              '.include(new LatLng(NEPAL_MIN_LAT, NEPAL_MIN_LON))\n                        .include(new LatLng(NEPAL_MAX_LAT, NEPAL_MAX_LON)).build();', 1)
old_nepal = '    private static boolean isNepalish(double la, double lo) { return la >= 25.4 && la <= 31.15 && lo >= 79.2 && lo <= 89.15; }'
new_nepal = '    private static boolean isNepalish(double la, double lo) { return la >= NEPAL_MIN_LAT && la <= NEPAL_MAX_LAT && lo >= NEPAL_MIN_LON && lo <= NEPAL_MAX_LON; } // V0900_STRICT_NEPAL_BOUNDS'
if old_nepal not in m: raise SystemExit('isNepalish anchor missing')
m = m.replace(old_nepal, new_nepal, 1)

# Bump build only; no other feature source is touched.
g = re.sub(r'versionCode\s+16\b', 'versionCode 17', g, count=1)
g = g.replace("versionName '0.8.99-native'", "versionName '0.9.00-native'", 1)

required = [
    'V0900_STATION_RIVERS_ONLY','V0900_MAP_ON_INVENTORY_CHANGE_ONLY','V0900_FULL_NETWORK_NEVER_RENDERED',
    'V0900_BUILD_MAPPING_ONCE','V0900_NAME_FIRST_STRICT_COORD_FALLBACK','V0900_LOCAL_SAME_RIVER_ONLY',
    'V0900_VISIBLE_SOURCE_IS_MONITORED_ONLY','V0900_TAP_ONLY_MONITORED_RIVERS',
    'V0900_STATUS_COLOURS_LINKED_SEGMENTS_ONLY','V0900_REUSE_PREBUILT_STATION_MAPPING',
    'V0900_ANIMATION_MONITORED_SOURCE_ONLY','V0900_STRICT_NEPAL_BOUNDS'
]
for marker in required:
    if marker not in m: raise SystemExit('v0.9.00 contract missing: ' + marker)
if 'riversGeoJson = makeRiversGeoJson(all)' in m: raise SystemExit('full Nepal river network still assigned to visible source')
if 'int n = Math.min(36, rivers.size())' in m: raise SystemExit('legacy full-network particle animation remains')
if "versionName '0.9.00-native'" not in g or 'versionCode 17' not in g: raise SystemExit('version bump failed')

map_path.write_text(m, encoding='utf-8')
build_path.write_text(g, encoding='utf-8')
print('FloodSafe v0.9.00 PASS: visible/animated river source is station-linked only; full Nepal mesh remains candidate-only in memory')
