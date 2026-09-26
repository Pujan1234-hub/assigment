from pathlib import Path
import re

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path = src / 'FloodSafeNativeMapView.java'
activity_path = src / 'NativeFullActivity.java'
build_path = root / 'app/build.gradle'

m = map_path.read_text(encoding='utf-8')
a = activity_path.read_text(encoding='utf-8')
g = build_path.read_text(encoding='utf-8')

if 'V0899_VERIFIED_RIVER_FLOW_SAFETY' in m and 'V0899_STALE_CURRENT_SEMANTICS' in a:
    print('v0.8.99 patch already applied')
    raise SystemExit(0)


def method_span(text, name):
    q = re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b' + re.escape(name) + r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{', text)
    if not q:
        return None
    op = text.find('{', q.start())
    depth = 0
    quote = None
    esc = False
    i = op
    while i < len(text):
        ch = text[i]
        if quote:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('"', "'"):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return q.start(), i + 1
        i += 1
    return None


def replace_method(text, name, block):
    sp = method_span(text, name)
    if not sp:
        raise SystemExit('Missing method: ' + name)
    return text[:sp[0]] + block + text[sp[1]:]


def insert_before_method(text, name, block, marker):
    if marker in text:
        return text
    sp = method_span(text, name)
    if not sp:
        raise SystemExit('Missing insertion anchor: ' + name)
    return text[:sp[0]] + block + text[sp[0]:]

# ---------------- Native MapLibre river map ----------------

m = m.replace('    private boolean animationRunning = false;\n',
              '    private boolean animationRunning = false;\n'
              '    private long animationFrameCount = 0L; // V0899_FLOW_FRAME_COUNTER\n', 1)

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
        refreshStationSources();
        refreshRiskRiverSources();
        refreshUserSource();
    } // V0899_STATUS_REFRESH_RECOLOURS_MATCHED_RIVER
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
                if (ways != null) {
                    List<RiverWay> all = new ArrayList<>();
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
                    all.sort(Comparator.comparingInt(FloodSafeNativeMapView::riverScore).reversed());
                    if (assetPath.contains("snapshot") && all.size() > 3200) {
                        all = new ArrayList<>(all.subList(0, 3200));
                    }
                    synchronized (rivers) {
                        rivers.clear();
                        rivers.addAll(all);
                    }
                    riversGeoJson = makeRiversGeoJson(all);
                    android.util.Log.i("FloodSafeRiver", "river_features=" + all.size() + " asset=" + assetPath);
                }
            } catch (Exception e) {
                android.util.Log.e("FloodSafeRiver", "river geometry load failed", e);
            }
            main.post(this::installGeoLayers);
        });
    } // V0899_REAL_BUNDLED_RIVER_GEOMETRY
'''
m = replace_method(m, 'loadBundledGeometry', load_geometry)

install_layers = r'''    private void installGeoLayers() {
        if (!styleReady || style == null) return;
        try {
            if (districtGeoJson != null && style.getSource("fs-districts") == null) {
                style.addSource(new GeoJsonSource("fs-districts", districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill", "fs-districts").withProperties(
                        fillColor("#8deeff"), fillOpacity(0.06f)));
                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(
                        lineColor("#e8fbff"), lineWidth(1.05f), lineOpacity(0.74f), lineJoin(LINE_JOIN_ROUND)));
            }
            if (riversGeoJson != null && style.getSource("fs-rivers") == null) {
                style.addSource(new GeoJsonSource("fs-rivers", riversGeoJson));
                style.addLayer(new LineLayer("fs-river-glow", "fs-rivers").withProperties(
                        lineColor("#007ea6"), lineWidth(5.4f), lineOpacity(0.48f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(
                        lineColor("#42ddff"), lineWidth(2.15f), lineOpacity(0.98f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
                android.util.Log.i("FloodSafeRiver", "river layers active: glow+core");
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
            refreshStationSources();
            refreshRiskRiverSources();
            refreshUserSource();
        } catch (Exception e) {
            android.util.Log.e("FloodSafeRiver", "layer install failed", e);
        }
    } // V0899_VISIBLE_GLOW_CORE_STATUS_LAYERS
'''
m = replace_method(m, 'installGeoLayers', install_layers)

line_helper = r'''    private void ensureLineSource(String sourceId, String layerId, String color, float width, float opacity) {
        if (style.getSource(sourceId) == null) {
            style.addSource(new GeoJsonSource(sourceId, emptyFeatureCollection()));
        }
        if (style.getLayer(layerId + "-glow") == null) {
            style.addLayer(new LineLayer(layerId + "-glow", sourceId).withProperties(
                    lineColor(color), lineWidth(width + 3.1f), lineOpacity(0.30f),
                    lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
        }
        if (style.getLayer(layerId) == null) {
            style.addLayer(new LineLayer(layerId, sourceId).withProperties(
                    lineColor(color), lineWidth(width), lineOpacity(opacity),
                    lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
        }
    } // V0899_STATUS_LINE_HELPER

'''
m = insert_before_method(m, 'refreshStationSources', line_helper, 'V0899_STATUS_LINE_HELPER')

refresh_stations = r'''    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        setGeo("fs-stale", stationGeo(snapshot, "stale"));
        setGeo("fs-normal", stationGeo(snapshot, "normal"));
        setGeo("fs-alert", stationGeo(snapshot, "alert"));
        setGeo("fs-warning", stationGeo(snapshot, "warning"));
        setGeo("fs-danger", stationGeo(snapshot, "danger"));
    }
'''
m = replace_method(m, 'refreshStationSources', refresh_stations)

nearest_river = r'''    private RiverWay nearestRiver(double la, double lo, double thresholdKm) {
        RiverWay best = null;
        double d = Double.MAX_VALUE;
        synchronized (rivers) {
            for (RiverWay r : rivers) {
                double x = distanceToRiverKm(la, lo, r);
                if (x < d) { d = x; best = r; }
            }
        }
        return d <= thresholdKm ? best : null;
    } // V0899_SEGMENT_BASED_RIVER_TAP
'''
m = replace_method(m, 'nearestRiver', nearest_river)

map_helpers = r'''    private void refreshRiskRiverSources() {
        if (!styleReady || style == null || rivers.isEmpty()) return;
        List<RiverWay> alert = new ArrayList<>(), warning = new ArrayList<>(), danger = new ArrayList<>();
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        for (StationDot s : snapshot) {
            if (s == null || !s.fresh) continue;
            String group = normalizeStage(s.stage);
            if (!("alert".equals(group) || "warning".equals(group) || "danger".equals(group))) continue;
            RiverWay r = matchedRiverForStation(s);
            if (r == null) continue;
            List<RiverWay> target = "danger".equals(group) ? danger : ("warning".equals(group) ? warning : alert);
            if (!target.contains(r)) target.add(r);
        }
        setGeo("fs-river-alert-risk", makeRiversGeoJsonSafe(alert));
        setGeo("fs-river-warning-risk", makeRiversGeoJsonSafe(warning));
        setGeo("fs-river-danger-risk", makeRiversGeoJsonSafe(danger));
        android.util.Log.i("FloodSafeRiver", "status_coloured_rivers=" + (alert.size() + warning.size() + danger.size())
                + " alert=" + alert.size() + " warning=" + warning.size() + " danger=" + danger.size());
    } // V0899_FRESH_MATCHED_RIVER_STATUS_ONLY

    double distanceToMatchedRiverKm(Object stationObject, double la, double lo) {
        StationDot s = readStation(stationObject);
        if (s == null) return Double.NaN;
        RiverWay r = matchedRiverForStation(s);
        return r == null ? Double.NaN : distanceToRiverKm(la, lo, r);
    } // V0899_FOREGROUND_2KM_GEOMETRY_DISTANCE

    private RiverWay matchedRiverForStation(StationDot s) {
        if (s == null) return null;
        String wanted = riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name));
        if (wanted.isEmpty()) return null;
        RiverWay best = null;
        double bestDistance = Double.POSITIVE_INFINITY;
        synchronized (rivers) {
            for (RiverWay r : rivers) {
                String rk = riverKey(r.name);
                if (!sameRiverKey(wanted, rk)) continue;
                double d = distanceToRiverKm(s.lat, s.lon, r);
                if (Double.isFinite(d) && d <= 8.0 && d < bestDistance) {
                    best = r;
                    bestDistance = d;
                }
            }
        }
        return best;
    }

    private StationDot bestGaugeForRiver(RiverWay r, double tapLat, double tapLon) {
        if (r == null) return null;
        String rk = riverKey(r.name);
        if (rk.isEmpty()) return null;
        StationDot best = null;
        double bestScore = Double.POSITIVE_INFINITY;
        synchronized (stations) {
            for (StationDot s : stations) {
                String sk = riverKey(!empty(s.riverName) ? s.riverName : riverFromStationTitle(s.name));
                if (!sameRiverKey(rk, sk)) continue;
                double toRiver = distanceToRiverKm(s.lat, s.lon, r);
                if (!Double.isFinite(toRiver) || toRiver > 8.0) continue;
                double toTap = km(tapLat, tapLon, s.lat, s.lon);
                double score = toTap + toRiver * 2.0;
                if (score < bestScore) { bestScore = score; best = s; }
            }
        }
        return best;
    } // V0899_NO_UNRELATED_NEAREST_GAUGE

    private static boolean empty(String s) { return s == null || s.trim().isEmpty(); }

    private static String riverFromStationTitle(String value) {
        if (value == null) return "";
        String s = value.trim();
        String lower = s.toLowerCase(Locale.ROOT);
        int at = lower.indexOf(" at ");
        if (at > 0) s = s.substring(0, at);
        return s;
    }

    private static String riverKey(String value) {
        String s = riverFromStationTitle(value).toLowerCase(Locale.ROOT);
        s = s.replace("river", "").replace("khola", "").replace("nadi", "")
                .replace("nadhi", "").replace("stream", "")
                .replace("नदी", "").replace("खोला", "");
        return s.replaceAll("[^a-z0-9\\p{L}]", "");
    }

    private static boolean sameRiverKey(String a, String b) {
        if (a == null || b == null || a.isEmpty() || b.isEmpty()) return false;
        if (a.equals(b)) return true;
        int min = Math.min(a.length(), b.length());
        return min >= 5 && (a.contains(b) || b.contains(a));
    }

    private static double distanceToRiverKm(double la, double lo, RiverWay r) {
        if (r == null || r.points.size() < 2) return Double.NaN;
        double best = Double.POSITIVE_INFINITY;
        for (int i = 0; i < r.points.size() - 1; i++) {
            double[] a = r.points.get(i), b = r.points.get(i + 1);
            double d = pointSegmentKm(la, lo, a[1], a[0], b[1], b[0]);
            if (d < best) best = d;
        }
        return best;
    }

    private static double pointSegmentKm(double lat, double lon,
                                         double lat1, double lon1, double lat2, double lon2) {
        double cos = Math.cos(Math.toRadians(lat));
        double x1 = (lon1 - lon) * 111.320 * cos, y1 = (lat1 - lat) * 110.574;
        double x2 = (lon2 - lon) * 111.320 * cos, y2 = (lat2 - lat) * 110.574;
        double dx = x2 - x1, dy = y2 - y1, len2 = dx * dx + dy * dy;
        double t = len2 <= 1e-12 ? 0.0 : -(x1 * dx + y1 * dy) / len2;
        t = Math.max(0.0, Math.min(1.0, t));
        double x = x1 + t * dx, y = y1 + t * dy;
        return Math.sqrt(x * x + y * y);
    }

    private static String makeRiversGeoJsonSafe(List<RiverWay> ways) {
        try { return makeRiversGeoJson(ways); } catch (Exception e) { return emptyFeatureCollection(); }
    }

'''
m = insert_before_method(m, 'showRiver', map_helpers, 'V0899_FRESH_MATCHED_RIVER_STATUS_ONLY')

show_river = r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot gauge = bestGaugeForRiver(r, la, lo);
        StringBuilder msg = new StringBuilder();
        if (gauge != null) {
            double d = km(la, lo, gauge.lat, gauge.lon);
            msg.append("Same-river official gauge: ").append(gauge.name)
                    .append(String.format(Locale.US, " • %.1f km", d));
            if (Double.isFinite(gauge.level)) msg.append(String.format(Locale.US, "\nWater level: %.2f m", gauge.level));
            if (gauge.at > 0L) {
                msg.append("\nOfficial observation: ")
                        .append(java.time.Instant.ofEpochMilli(gauge.at)
                                .atZone(java.time.ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
            }
            if (gauge.fresh) {
                msg.append("\nStatus: ").append(normalizeStage(gauge.stage).toUpperCase(Locale.ROOT)).append(" • CURRENT official");
            } else {
                msg.append("\nStatus: HISTORICAL / STALE • last known reading")
                        .append("\nThis old reading is not used for warning colours or alerts.");
            }
            String rain = DhmRainMirror.detailFor(gauge.name, gauge.district, gauge.lat, gauge.lon);
            msg.append("\n\n").append(rain != null ? rain : "Rainfall: no safely matched fresh DHM rainfall reading available.");
        } else {
            msg.append("No safely matched same-river official gauge was found for this river geometry.")
                    .append("\nRainfall: unavailable because there is no safe river/gauge match.");
        }
        msg.append("\n\nRiver geometry: bundled Nepal waterways");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ", null).show();
    } // V0899_RIVER_TAP_SAME_RIVER_ONLY
'''
m = replace_method(m, 'showRiver', show_river)

# Replace the animation runnable as a unit.
start = m.find('    private final Runnable particleTick = new Runnable() {')
end = m.find('    private StationDot readStation', start)
if start < 0 or end < 0:
    raise SystemExit('particle runnable anchor missing')
particle = r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if (!animationRunning || !styleReady || style == null) return;
            try {
                JSONArray features = new JSONArray();
                List<RiverWay> snapshot;
                synchronized (rivers) { snapshot = new ArrayList<>(rivers); }
                int n = Math.min(90, snapshot.size());
                double phase = ((System.currentTimeMillis() - particleStart) % 7000L) / 7000.0;
                for (int i = 0; i < n; i++) {
                    int ri = n <= 1 ? 0 : (int)Math.floor(i * (snapshot.size() - 1.0) / (n - 1.0));
                    RiverWay r = snapshot.get(Math.max(0, Math.min(snapshot.size() - 1, ri)));
                    if (r.points.size() < 2) continue;
                    for (int p = 0; p < 3; p++) {
                        double localPhase = (phase + p / 3.0 + i * 0.071) % 1.0;
                        double v = localPhase * (r.points.size() - 1);
                        int ix = Math.min(r.points.size() - 2, (int)Math.floor(v));
                        double f = v - ix;
                        double[] aa = r.points.get(ix), bb = r.points.get(ix + 1);
                        double x = aa[0] + (bb[0] - aa[0]) * f;
                        double y = aa[1] + (bb[1] - aa[1]) * f;
                        features.put(pointFeature(x, y, "flow"));
                    }
                }
                setGeo("fs-flow-particles", new JSONObject().put("type", "FeatureCollection").put("features", features).toString());
                double wave = 0.5 + 0.5 * Math.sin(System.currentTimeMillis() / 520.0);
                LineLayer glow = style.getLayerAs("fs-river-glow");
                if (glow != null) glow.setProperties(lineOpacity((float)(0.40 + 0.15 * wave)), lineWidth((float)(5.0 + 0.9 * wave)));
                LineLayer core = style.getLayerAs("fs-rivers-layer");
                if (core != null) core.setProperties(lineOpacity((float)(0.92 + 0.07 * wave)), lineWidth((float)(2.0 + 0.28 * wave)));
                animationFrameCount++;
                if (animationFrameCount % 60L == 0L) {
                    android.util.Log.i("FloodSafeRiver", "flow_animation_frames=" + animationFrameCount
                            + " moving_particles=" + features.length() + " active_flow_layer=fs-flow-particles-layer");
                }
            } catch (Exception e) {
                android.util.Log.w("FloodSafeRiver", "flow animation frame failed", e);
            }
            main.postDelayed(this, 220L);
        }
    }; // V0899_VISIBLE_MOVING_FLOW_ON_REAL_RIVERS

'''
m = m[:start] + particle + m[end:]

read_station = r'''    private StationDot readStation(Object o) {
        if (o == null) return null;
        try {
            Class<?> c = o.getClass();
            double la = getDouble(c, o, "lat"), lo = getDouble(c, o, "lon");
            if (!Double.isFinite(la) || !Double.isFinite(lo)) return null;
            StationDot s = new StationDot();
            s.original = o;
            s.lat = la; s.lon = lo;
            s.name = getString(c, o, "name", "Official river station");
            s.riverName = getString(c, o, "riverName", "");
            s.district = getString(c, o, "district", "");
            s.stationId = getString(c, o, "stationId", "");
            s.stage = getString(c, o, "stage", "normal").toLowerCase(Locale.ROOT);
            s.fresh = getBoolean(c, o, "fresh", false);
            s.level = getDouble(c, o, "level");
            s.at = getLong(c, o, "at", -1L);
            return s;
        } catch (Exception ignored) { return null; }
    } // V0899_STATION_RIVER_ID_TIME_BRIDGE
'''
m = replace_method(m, 'readStation', read_station)

# Add long reflection helper.
get_long = r'''    private static long getLong(Class<?> c, Object o, String name, long fallback) {
        try { Field f = c.getDeclaredField(name); f.setAccessible(true); return ((Number)f.get(o)).longValue(); }
        catch (Exception e) { return fallback; }
    }
'''
m = insert_before_method(m, 'getString', get_long, 'private static long getLong')

old_station_dot = '    private static final class StationDot {\n        Object original; String name, stage; double lat, lon, level; boolean fresh;\n    }'
new_station_dot = '    private static final class StationDot {\n        Object original; String stationId, name, riverName, district, stage; double lat, lon, level; long at; boolean fresh;\n    }'
if old_station_dot not in m:
    raise SystemExit('StationDot anchor missing')
m = m.replace(old_station_dot, new_station_dot, 1)

# Marker used by CI and human review.
m = m.replace('/**\n * 100% native Android river map using MapLibre Native. No WebView is used.',
              '/**\n * V0899_VERIFIED_RIVER_FLOW_SAFETY\n * 100% native Android river map using MapLibre Native. No WebView is used.', 1)

# ---------------- Native activity semantics ----------------

# Start the DHM mirror without adding map clutter.
oncreate = method_span(a, 'onCreate')
if not oncreate:
    raise SystemExit('onCreate missing')
block = a[oncreate[0]:oncreate[1]]
if 'DhmRainMirror.ensureStarted' not in block:
    block = block.replace('        initTts();', '        initTts();\n        DhmRainMirror.ensureStarted(this);')
    a = a[:oncreate[0]] + block + a[oncreate[1]:]

# Generic map badge must not claim every old observation is LIVE.
a = a.replace('TextView live=badge(t("प्रत्यक्ष","LIVE")', 'TextView live=badge(t("आधिकारिक","OFFICIAL")', 1)
a = a.replace('t("🇳🇵 BIPAD नदी प्रत्यक्ष नक्सा","🇳🇵 BIPAD live river map")',
              't("🇳🇵 BIPAD आधिकारिक नदी नक्सा","🇳🇵 BIPAD official river map")', 1)

parse_station = r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;
        double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel"),
                warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),
                danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=parseTime(str(r,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));
        boolean fresh=at>0&&now-at<=RIVER_FRESH_MS&&at-now<=5*60_000L;
        String raw=str(r,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(fresh){
            if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE")){stage="normal";rank=3;}
        }
        String stationId=str(r,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id");
        String riverName=str(r,"river_name","riverName","river");
        String name=str(r,"station_name","stationName","title","name");
        if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";
        String district=str(r,"districtName","district_name","district");
        return new RiverStation(stationId,name,riverName,district,a,o,level,warning,danger,at,fresh,stage,rank);
    } // V0899_STALE_CURRENT_SEMANTICS
'''
a = replace_method(a, 'parseStation', parse_station)

update_risk = r'''    private void updateRisk(List<RiverStation> copy){
        RiverStation nearest=null,emergencyStation=null;double nearestStationKm=Double.POSITIVE_INFINITY,emergencyRiverKm=Double.POSITIVE_INFINITY;
        for(RiverStation s:copy){
            double sd=distanceKm(s.lat,s.lon);if(Double.isFinite(sd)&&sd<nearestStationKm){nearestStationKm=sd;nearest=s;}
            if(s.fresh&&(s.stage.equals("warning")||s.stage.equals("danger"))&&map!=null&&isNepal(lat,lon)){
                double rd=map.distanceToMatchedRiverKm(s,lat,lon);
                if(Double.isFinite(rd)&&rd<=2d&&rd<emergencyRiverKm){emergencyRiverKm=rd;emergencyStation=s;}
            }
        }
        RiverStation best=emergencyStation!=null?emergencyStation:nearest;
        if(best==null){riskValue.setText("—");riskBadge.setText(t("प्रतीक्षा","WAIT"));riskText.setText(t("नेपालमा location लिएपछि नजिकको official river risk देखिन्छ।","Take a Nepal location to see nearby official river risk."));alarmBanner.setVisibility(View.GONE);return;}
        riskValue.setText(stageName(best.stage));riskBadge.setText(stageName(best.stage));
        double shownDistance=best==emergencyStation?emergencyRiverKm:nearestStationKm;
        String basis=best==emergencyStation?t(" • प्रभावित नदी geometry सम्म "," • to affected river geometry "):t(" • station सम्म "," • to station ");
        riskText.setText(best.name+basis+String.format(Locale.US,"%.1f km",shownDistance)+" • "+stationLine(best));
        int col=stageColor(best.stage);riskValue.setTextColor(col);riskBadge.setTextColor(col);
        boolean emergency=emergencyStation!=null;
        alarmBanner.setVisibility(emergency?View.VISIBLE:View.GONE);
        if(emergency){alarmTitle.setText(best.stage.equals("danger")?t("🚨 DANGER — प्रभावित नदी 2 km भित्र","🚨 DANGER — affected river within 2 km"):t("⚠️ WARNING — प्रभावित नदी 2 km भित्र","⚠️ WARNING — affected river within 2 km"));alarmText.setText(best.name+" • river geometry "+String.format(Locale.US,"%.1f km",emergencyRiverKm)+" • "+stationLine(best));}
    } // V0899_FOREGROUND_ALERT_USES_RIVER_GEOMETRY
'''
a = replace_method(a, 'updateRisk', update_risk)

station_line = r'''    private String stationLine(RiverStation s){
        long ageMs=s.at>0?Math.max(0,System.currentTimeMillis()-s.at):-1L;
        String age;
        if(ageMs<0)age=t("official time उपलब्ध छैन","official time unavailable");
        else if(ageMs<60L*60L*1000L)age=(ageMs/60000L)+" min ago";
        else if(ageMs<48L*60L*60L*1000L)age=(ageMs/(60L*60L*1000L))+" hr ago";
        else age=(ageMs/(24L*60L*60L*1000L))+" days ago";
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";
        double d=distanceKm(s.lat,s.lon);
        String freshness=s.fresh?t("हालको आधिकारिक","CURRENT official"):t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात","HISTORICAL / STALE • last known");
        return freshness+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • station %.1f km",d):"");
    }
'''
a = replace_method(a, 'stationLine', station_line)

show_station = r'''    private void showStation(RiverStation s){
        StringBuilder b=new StringBuilder();
        b.append(s.fresh?stageDot(s.stage)+" "+stageName(s.stage):"⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading"));
        if(!s.stationId.isEmpty())b.append("\nStation ID: ").append(s.stationId);
        if(!s.riverName.isEmpty())b.append("\nRiver: ").append(s.riverName);
        b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.2f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.2f m",s.danger));
        b.append("\n").append(t("Official observation: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—");
        if(!s.fresh)b.append("\n\n").append(t("यो पुरानो/ऐतिहासिक reading warning colour वा alarm मा प्रयोग हुँदैन।","This historical/stale reading is not used for warning colours or alarms."));
        String rainDetail=DhmRainMirror.detailFor(s.name,s.district,s.lat,s.lon);
        b.append("\n\n").append(rainDetail!=null?rainDetail:t("Rainfall: सुरक्षित रूपमा match भएको fresh DHM rainfall reading उपलब्ध छैन।","Rainfall: no safely matched fresh DHM rainfall reading is available."));
        b.append("\n\nSource: BIPAD / DHM");
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton("OK",null).show();
    } // V0899_STATION_STALE_AND_RAIN_DETAIL
'''
a = replace_method(a, 'showStation', show_station)

# Replace RiverStation with fields required by same-river matching while preserving an old constructor.
river_station_pattern = r'    private static final class RiverStation\{[^\n]*\}\n'
river_station_new = '''    private static final class RiverStation{final String stationId,name,riverName,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){this("",n,"",di,a,o,l,w,d,tm,f,s,r);}RiverStation(String id,String n,String rn,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){stationId=id==null?"":id;name=n;riverName=rn==null?"":rn;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;}}\n'''
a, count = re.subn(river_station_pattern, river_station_new, a, count=1)
if count != 1:
    raise SystemExit('RiverStation class anchor missing')

# Activity marker.
a = a.replace('/** Full native Android implementation of the FloodSafe Nepal web dashboard. No WebView is used. */',
              '/** V0899_STALE_CURRENT_SEMANTICS — Full native Android FloodSafe UI. No WebView is used. */', 1)

# Version bump only once.
g = re.sub(r'versionCode\s+15\b', 'versionCode 16', g, count=1)
g = g.replace("versionName '0.8.98-native'", "versionName '0.8.99-native'", 1)

required_map = [
    'V0899_VERIFIED_RIVER_FLOW_SAFETY','V0899_VISIBLE_GLOW_CORE_STATUS_LAYERS',
    'V0899_VISIBLE_MOVING_FLOW_ON_REAL_RIVERS','V0899_FRESH_MATCHED_RIVER_STATUS_ONLY',
    'V0899_RIVER_TAP_SAME_RIVER_ONLY','V0899_FOREGROUND_2KM_GEOMETRY_DISTANCE'
]
for marker in required_map:
    if marker not in m:
        raise SystemExit('Missing map contract marker: ' + marker)
required_activity = [
    'V0899_STALE_CURRENT_SEMANTICS','V0899_FOREGROUND_ALERT_USES_RIVER_GEOMETRY',
    'V0899_STATION_STALE_AND_RAIN_DETAIL','DhmRainMirror.ensureStarted'
]
for marker in required_activity:
    if marker not in a:
        raise SystemExit('Missing activity contract marker: ' + marker)

map_path.write_text(m, encoding='utf-8')
activity_path.write_text(a, encoding='utf-8')
build_path.write_text(g, encoding='utf-8')
print('FloodSafe v0.8.99 patch applied: visible native flow/glow + matched river status + stale safety + rainfall detail + river geometry alerts')
