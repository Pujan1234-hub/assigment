package io.github.pujan1234hub.floodsafe.app;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.MotionEvent;
import android.widget.FrameLayout;

import org.json.JSONArray;
import org.json.JSONObject;
import org.maplibre.android.MapLibre;
import org.maplibre.android.camera.CameraPosition;
import org.maplibre.android.camera.CameraUpdateFactory;
import org.maplibre.android.geometry.LatLng;
import org.maplibre.android.geometry.LatLngBounds;
import org.maplibre.android.maps.MapLibreMap;
import org.maplibre.android.maps.MapView;
import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.CircleLayer;
import org.maplibre.android.style.layers.FillLayer;
import org.maplibre.android.style.layers.LineLayer;
import org.maplibre.android.style.sources.GeoJsonSource;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.maplibre.android.style.layers.PropertyFactory.circleColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeWidth;
import static org.maplibre.android.style.layers.PropertyFactory.fillColor;
import static org.maplibre.android.style.layers.PropertyFactory.fillOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.lineCap;
import static org.maplibre.android.style.layers.PropertyFactory.lineColor;
import static org.maplibre.android.style.layers.PropertyFactory.lineJoin;
import static org.maplibre.android.style.layers.PropertyFactory.lineOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;
import static org.maplibre.android.style.layers.Property.LINE_CAP_ROUND;
import static org.maplibre.android.style.layers.Property.LINE_JOIN_ROUND;

/**
 * V0899_VERIFIED_RIVER_FLOW_SAFETY
 * 100% native Android river map using MapLibre Native. No WebView is used.
 * Mirrors the proven FloodSafe web map: Nepal bounds, Esri satellite imagery,
 * terrain hillshade, cyan river network, verified station status colours,
 * native pan/pinch/zoom, and tap details.
 */
final class FloodSafeNativeMapView extends FrameLayout {
    interface StationTapListener { void onStationTap(Object stationObject); }

    private static final double NEPAL_MIN_LAT = 26.2, NEPAL_MAX_LAT = 30.5;
    private static final double NEPAL_MIN_LON = 80.0, NEPAL_MAX_LON = 88.35;
    private static final LatLng NEPAL_CENTER = new LatLng(28.10, 84.15);
    private static final String STYLE_JSON = "{\"version\":8,\"sources\":{" +
            "\"satellite\":{\"type\":\"raster\",\"tiles\":[\"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}\"],\"tileSize\":256,\"maxzoom\":19,\"attribution\":\"Imagery © Esri\"}," +
            "\"terrain\":{\"type\":\"raster-dem\",\"tiles\":[\"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png\"],\"tileSize\":256,\"encoding\":\"terrarium\",\"minzoom\":0,\"maxzoom\":15,\"attribution\":\"Terrain © AWS Terrain Tiles\"}}," +
            "\"layers\":[{\"id\":\"satellite\",\"type\":\"raster\",\"source\":\"satellite\"},{\"id\":\"hillshade\",\"type\":\"hillshade\",\"source\":\"terrain\",\"paint\":{\"hillshade-exaggeration\":0.30,\"hillshade-shadow-color\":\"#14242c\",\"hillshade-highlight-color\":\"#f2fdff\",\"hillshade-accent-color\":\"#4f7f8e\"}}]}";

    private final MapView mapView;
    private final StationTapListener stationTapListener;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<StationDot> stations = new ArrayList<>();
    private final List<RiverWay> rivers = new ArrayList<>();
    private final List<RiverWay> monitoredRivers = new ArrayList<>(); // V0900_STATION_RIVERS_ONLY
    private final java.util.Map<String,List<RiverWay>> monitoredByStation = new java.util.HashMap<>();
    private volatile String stationInventoryFingerprint = "";
    private volatile String mappedInventoryFingerprint = "";
    private volatile int monitoredSourceFeatureCount = 0;
    private MapLibreMap map;
    private Style style;
    private boolean styleReady = false;
    boolean terrain = true;
    private double userLat = Double.NaN, userLon = Double.NaN;
    private String districtGeoJson = null;
    private String riversGeoJson = null;
    private long particleStart = 0L;
    private boolean animationRunning = false;
    private long animationFrameCount = 0L; // V0899_FLOW_FRAME_COUNTER

    FloodSafeNativeMapView(Context context, StationTapListener listener) {
        super(context);
        stationTapListener = listener;
        setBackgroundColor(Color.rgb(8, 24, 34));
        MapLibre.getInstance(context.getApplicationContext());
        mapView = new MapView(context);
        addView(mapView, new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));
        mapView.onCreate((Bundle) null);
        mapView.getMapAsync(m -> {
            map = m;
            map.setMinZoomPreference(4.8);
            map.setMaxZoomPreference(19.0);
            try {
                LatLngBounds bounds = new LatLngBounds.Builder()
                        .include(new LatLng(NEPAL_MIN_LAT, NEPAL_MIN_LON))
                        .include(new LatLng(NEPAL_MAX_LAT, NEPAL_MAX_LON)).build();
                map.setLatLngBoundsForCameraTarget(bounds);
            } catch (Exception ignored) {}
            map.setStyle(new Style.Builder().fromJson(STYLE_JSON), s -> {
                style = s;
                styleReady = true;
                installGeoLayers();
                resetView();
                refreshStationSources();
                refreshUserSource();
                startParticles();
            });
            map.addOnMapClickListener(this::onMapClick);
        });
        loadBundledGeometry();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        try { mapView.onStart(); } catch (Exception ignored) {}
        try { mapView.onResume(); } catch (Exception ignored) {}
    }

    @Override protected void onDetachedFromWindow() {
        animationRunning = false;
        main.removeCallbacksAndMessages(null);
        try { mapView.onPause(); } catch (Exception ignored) {}
        try { mapView.onStop(); } catch (Exception ignored) {}
        try { mapView.onDestroy(); } catch (Exception ignored) {}
        io.shutdownNow();
        super.onDetachedFromWindow();
    }

    @Override public boolean dispatchTouchEvent(MotionEvent ev) {
        int action = ev.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_MOVE || ev.getPointerCount() > 1) {
            if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(true);
        } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(false);
        }
        return super.dispatchTouchEvent(ev);
    }

    void setBase(Bitmap ignored) { /* Legacy Canvas hook; MapLibre loads native layers itself. */ }
    void setStations(List<?> source, double lat, double lon) {
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
 // V0899_STATUS_REFRESH_RECOLOURS_MATCHED_RIVER


    void zoomBy(float factor) {
        if (map == null) return;
        double current = map.getCameraPosition().zoom;
        double delta = Math.log(Math.max(0.2f, factor)) / Math.log(2.0);
        map.animateCamera(CameraUpdateFactory.zoomTo(Math.max(4.8, Math.min(19.0, current + delta))), 300);
    }

    void resetView() {
        if (map == null) return;
        CameraPosition cp = new CameraPosition.Builder()
                .target(NEPAL_CENTER).zoom(5.4).tilt(terrain ? 28.0 : 0.0).bearing(0.0).build();
        map.animateCamera(CameraUpdateFactory.newCameraPosition(cp), 450);
    }

    void toggleTerrain() {
        terrain = !terrain;
        if (map == null) return;
        CameraPosition old = map.getCameraPosition();
        CameraPosition cp = new CameraPosition.Builder(old)
                .tilt(terrain ? 45.0 : 0.0).bearing(0.0).build();
        map.animateCamera(CameraUpdateFactory.newCameraPosition(cp), 500);
    }
    private void loadBundledGeometry() {
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
                        rw.name = firstNonEmpty(w.optString("name_en"), w.optString("name"), w.optString("name_ne"), "नदी / खोला"); // V0900_BIPAD_NAME_MATCH_PRIORITY
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
 // V0899_REAL_BUNDLED_RIVER_GEOMETRY
    private static String stationInventoryFingerprint(List<StationDot> list) {
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
        if (requestedInventory.equals(mappedInventoryFingerprint) && monitoredSourceFeatureCount > 0) return;
        final long started = android.os.SystemClock.elapsedRealtime();
        List<StationDot> ss;
        List<RiverWay> candidates;
        synchronized (stations) { ss = new ArrayList<>(stations); }
        synchronized (rivers) { candidates = new ArrayList<>(rivers); }
        if (ss.isEmpty() || candidates.isEmpty()) {
            android.util.Log.i("FloodSafeRiver", "mapping_wait stations=" + ss.size() + " candidates=" + candidates.size());
            return;
        }

        java.util.Map<String,List<RiverWay>> byKey = new java.util.HashMap<>();
        java.util.IdentityHashMap<RiverWay,double[]> bounds = new java.util.IdentityHashMap<>();
        for (RiverWay r : candidates) {
            String k = riverKey(r.name);
            if (!k.isEmpty()) byKey.computeIfAbsent(k, ignored -> new ArrayList<>()).add(r);
            bounds.put(r, riverBounds(r));
        }
        android.util.Log.i("FloodSafeRiver", "mapping_start stations=" + ss.size() + " candidates=" + candidates.size() + " river_keys=" + byKey.size());

        java.util.LinkedHashSet<RiverWay> visible = new java.util.LinkedHashSet<>();
        java.util.Map<String,List<RiverWay>> byStation = new java.util.HashMap<>();
        int exact = 0, fallback = 0, unmatched = 0;
        String sample = "";
        for (StationDot st : ss) {
            String wanted = riverKey(!empty(st.riverName) ? st.riverName : riverFromStationTitle(st.name));
            List<RiverWay> family = candidateFamily(wanted, byKey);
            RiverWay seed = seedRiverForStation(st, family, bounds, candidates);
            if (seed == null) { unmatched++; continue; }
            boolean named = !family.isEmpty() && family.contains(seed) && !wanted.isEmpty()
                    && sameRiverKey(wanted, riverKey(seed.name));
            if (named) exact++; else fallback++;
            List<RiverWay> local = localConnectedRiverSegments(st, seed, family, named);
            if (local.isEmpty()) local = Collections.singletonList(seed);
            visible.addAll(local);
            byStation.put(stationKey(st), new ArrayList<>(local));
            String probe = ((st.name == null ? "" : st.name) + " " + (st.riverName == null ? "" : st.riverName)).toLowerCase(Locale.ROOT);
            if (sample.isEmpty() && (probe.contains("bagmati") || probe.contains("gaurighat"))) {
                sample = st.name + " -> " + seed.name + " segments=" + local.size();
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
        long elapsed = android.os.SystemClock.elapsedRealtime() - started;
        android.util.Log.i("FloodSafeRiver", "station_linked_features=" + next.size() + " stations=" + ss.size()
                + " exact=" + exact + " coordinate_fallback=" + fallback + " unmatched=" + unmatched
                + " mapping_ms=" + elapsed + (sample.isEmpty() ? "" : " sample=" + sample));
        main.post(() -> {
            if (styleReady && style != null) {
                if (style.getSource("fs-rivers") == null) installGeoLayers();
                setGeo("fs-rivers", riversGeoJson);
                refreshRiskRiverSources();
            }
        });
    } // V0901_FAST_STATION_MAPPING
 // V0900_BUILD_MAPPING_ONCE
    private static List<RiverWay> candidateFamily(String wanted, java.util.Map<String,List<RiverWay>> byKey) {
        if (wanted == null || wanted.isEmpty() || byKey == null || byKey.isEmpty()) return Collections.emptyList();
        List<RiverWay> exact = byKey.get(wanted);
        if (exact != null && !exact.isEmpty()) return new ArrayList<>(exact);
        java.util.LinkedHashSet<RiverWay> out = new java.util.LinkedHashSet<>();
        for (java.util.Map.Entry<String,List<RiverWay>> e : byKey.entrySet()) {
            if (sameRiverKey(wanted, e.getKey())) out.addAll(e.getValue());
        }
        return new ArrayList<>(out);
    }

    private static double[] riverBounds(RiverWay r) {
        double minLat = Double.POSITIVE_INFINITY, maxLat = Double.NEGATIVE_INFINITY;
        double minLon = Double.POSITIVE_INFINITY, maxLon = Double.NEGATIVE_INFINITY;
        if (r != null) for (double[] p : r.points) {
            if (p == null || p.length < 2) continue;
            minLon = Math.min(minLon, p[0]); maxLon = Math.max(maxLon, p[0]);
            minLat = Math.min(minLat, p[1]); maxLat = Math.max(maxLat, p[1]);
        }
        return new double[]{minLat, maxLat, minLon, maxLon};
    }

    private static boolean boundsNear(double lat, double lon, double[] b, double padKm) {
        if (b == null || b.length < 4 || !Double.isFinite(b[0])) return false;
        double latPad = padKm / 110.574;
        double cos = Math.max(0.25, Math.cos(Math.toRadians(lat)));
        double lonPad = padKm / (111.320 * cos);
        return lat >= b[0] - latPad && lat <= b[1] + latPad
                && lon >= b[2] - lonPad && lon <= b[3] + lonPad;
    }

    private RiverWay seedRiverForStation(StationDot st, List<RiverWay> family,
                                          java.util.IdentityHashMap<RiverWay,double[]> bounds,
                                          List<RiverWay> candidates) {
        if (st == null) return null;
        RiverWay best = null;
        double bestD = Double.POSITIVE_INFINITY;
        if (family != null) {
            for (RiverWay r : family) {
                double d = distanceToRiverKm(st.lat, st.lon, r);
                if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
            }
            if (best != null && bestD <= 10.0) return best;
        }
        // Strict coordinate fallback. Cheap bounds reject avoids millions of segment calculations.
        best = null; bestD = Double.POSITIVE_INFINITY;
        if (candidates != null) for (RiverWay r : candidates) {
            if (!boundsNear(st.lat, st.lon, bounds.get(r), 1.15)) continue;
            double d = distanceToRiverKm(st.lat, st.lon, r);
            if (Double.isFinite(d) && d < bestD) { bestD = d; best = r; }
        }
        return bestD <= 0.85 ? best : null;
    } // V0901_NAME_INDEX_BOUNDS_FALLBACK
 // V0900_NAME_FIRST_STRICT_COORD_FALLBACK
    private List<RiverWay> localConnectedRiverSegments(StationDot st, RiverWay seed, List<RiverWay> family, boolean namedMatch) {
        java.util.LinkedHashSet<RiverWay> out = new java.util.LinkedHashSet<>();
        out.add(seed);
        if (!namedMatch || family == null || family.isEmpty()) return new ArrayList<>(out);
        java.util.IdentityHashMap<RiverWay,Double> stationDistance = new java.util.IdentityHashMap<>();
        for (RiverWay r : family) stationDistance.put(r, distanceToRiverKm(st.lat, st.lon, r));
        for (int round = 0; round < 5; round++) {
            boolean changed = false;
            List<RiverWay> current = new ArrayList<>(out);
            for (RiverWay r : family) {
                if (out.contains(r)) continue;
                Double stationD = stationDistance.get(r);
                if (stationD == null || !Double.isFinite(stationD) || stationD > 35.0) continue;
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
    } // V0901_LOCAL_FAMILY_ONLY
 // V0900_LOCAL_SAME_RIVER_ONLY

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
    private void installGeoLayers() {
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
 // V0899_VISIBLE_GLOW_CORE_STATUS_LAYERS


    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {
        if (style.getSource(sourceId) != null) return;
        style.addSource(new GeoJsonSource(sourceId, emptyFeatureCollection()));
        style.addLayer(new CircleLayer(layerId, sourceId).withProperties(
                circleColor(color), circleRadius(radius), circleOpacity(opacity),
                circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)));
    }
    private void ensureLineSource(String sourceId, String layerId, String color, float width, float opacity) {
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
    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        setGeo("fs-stale", stationGeo(snapshot, "stale"));
        setGeo("fs-normal", stationGeo(snapshot, "normal"));
        setGeo("fs-alert", stationGeo(snapshot, "alert"));
        setGeo("fs-warning", stationGeo(snapshot, "warning"));
        setGeo("fs-danger", stationGeo(snapshot, "danger"));
    }


    private void refreshUserSource() {
        if (!styleReady || style == null) return;
        String geo = emptyFeatureCollection();
        if (Double.isFinite(userLat) && Double.isFinite(userLon) && isNepalish(userLat, userLon)) {
            geo = pointFeatureCollection(userLon, userLat, "me");
        }
        setGeo("fs-user", geo);
    }

    private void setGeo(String id, String json) {
        try {
            GeoJsonSource s = style.getSourceAs(id);
            if (s != null) s.setGeoJson(json);
        } catch (Exception ignored) {}
    }

    private boolean onMapClick(LatLng p) {
        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
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
        return false;
    }

    private StationDot nearestStation(double la, double lo) {
        StationDot best = null; double d = Double.MAX_VALUE;
        synchronized (stations) {
            for (StationDot s : stations) {
                double x = km(la, lo, s.lat, s.lon);
                if (x < d) { d = x; best = s; }
            }
        }
        return best;
    }
    private RiverWay nearestRiver(double la, double lo, double thresholdKm) {
        RiverWay best = null; double d = Double.MAX_VALUE;
        synchronized (monitoredRivers) {
            for (RiverWay r : monitoredRivers) {
                double x = distanceToRiverKm(la, lo, r);
                if (x < d) { d = x; best = r; }
            }
        }
        return d <= thresholdKm ? best : null;
    } // V0900_TAP_ONLY_MONITORED_RIVERS
 // V0899_SEGMENT_BASED_RIVER_TAP
    private void refreshRiskRiverSources() {
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
 // V0899_FRESH_MATCHED_RIVER_STATUS_ONLY

    double distanceToMatchedRiverKm(Object stationObject, double la, double lo) {
        StationDot s = readStation(stationObject);
        if (s == null) return Double.NaN;
        RiverWay r = matchedRiverForStation(s);
        return r == null ? Double.NaN : distanceToRiverKm(la, lo, r);
    } // V0899_FOREGROUND_2KM_GEOMETRY_DISTANCE
    private RiverWay matchedRiverForStation(StationDot s) {
        List<RiverWay> linked = stationSegments(s);
        if (!linked.isEmpty()) return linked.get(0);
        return null;
    } // V0900_REUSE_PREBUILT_STATION_MAPPING


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
    private void showRiver(RiverWay r, double la, double lo) {
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


    private void startParticles() {
        if (animationRunning) return;
        animationRunning = true;
        particleStart = System.currentTimeMillis();
        main.post(particleTick);
    }

    private final Runnable particleTick = new Runnable() {
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

    private StationDot readStation(Object o) {
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


    private static double getDouble(Class<?> c, Object o, String name) throws Exception {
        Field f = c.getDeclaredField(name); f.setAccessible(true); return ((Number) f.get(o)).doubleValue();
    }
    private static boolean getBoolean(Class<?> c, Object o, String name, boolean fallback) {
        try { Field f=c.getDeclaredField(name); f.setAccessible(true); return f.getBoolean(o); } catch (Exception e) { return fallback; }
    }
    private static long getLong(Class<?> c, Object o, String name, long fallback) {
        try { Field f = c.getDeclaredField(name); f.setAccessible(true); return ((Number)f.get(o)).longValue(); }
        catch (Exception e) { return fallback; }
    }
    private static String getString(Class<?> c, Object o, String name, String fallback) {
        try { Field f=c.getDeclaredField(name); f.setAccessible(true); Object v=f.get(o); return v==null?fallback:String.valueOf(v); } catch (Exception e) { return fallback; }
    }

    private String readAsset(String path) throws Exception {
        try (InputStream in = getContext().getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder b = new StringBuilder(); String line;
            while ((line = r.readLine()) != null) b.append(line);
            return b.toString();
        }
    }

    private static String makeRiversGeoJson(List<RiverWay> ways) throws Exception {
        JSONArray features = new JSONArray();
        for (RiverWay r : ways) {
            JSONArray coords = new JSONArray();
            for (double[] p : r.points) coords.put(new JSONArray().put(p[0]).put(p[1]));
            JSONObject geom = new JSONObject().put("type", "LineString").put("coordinates", coords);
            JSONObject props = new JSONObject().put("name", r.name).put("type", r.type);
            features.put(new JSONObject().put("type", "Feature").put("geometry", geom).put("properties", props));
        }
        return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
    }

    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                String g = s.fresh ? normalizeStage(s.stage) : "stale";
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon, s.lat, s.name));
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }

    private static JSONObject pointFeature(double lo, double la, String name) throws Exception {
        JSONObject geom = new JSONObject().put("type", "Point").put("coordinates", new JSONArray().put(lo).put(la));
        return new JSONObject().put("type", "Feature").put("geometry", geom)
                .put("properties", new JSONObject().put("name", name));
    }
    private static String pointFeatureCollection(double lo, double la, String name) {
        try { return new JSONObject().put("type", "FeatureCollection").put("features", new JSONArray().put(pointFeature(lo, la, name))).toString(); }
        catch (Exception e) { return emptyFeatureCollection(); }
    }
    private static String emptyFeatureCollection() { return "{\"type\":\"FeatureCollection\",\"features\":[]}"; }

    private static String normalizeStage(String s) {
        if (s == null) return "normal";
        s = s.toLowerCase(Locale.ROOT);
        if (s.contains("danger")) return "danger";
        if (s.contains("warning")) return "warning";
        if (s.contains("alert") || s.contains("watch")) return "alert";
        return "normal";
    }
    private static String firstNonEmpty(String... a) { for (String s : a) if (s != null && !s.trim().isEmpty()) return s.trim(); return "River"; }
    private static int riverScore(RiverWay r) {
        int n = r.points.size(); return ("river".equalsIgnoreCase(r.type) ? 160 : 0) + Math.min(90, n * 2) + (r.name == null ? 0 : 70);
    }
    private static boolean isNepalish(double la, double lo) { return la >= NEPAL_MIN_LAT && la <= NEPAL_MAX_LAT && lo >= NEPAL_MIN_LON && lo <= NEPAL_MAX_LON; } // V0900_STRICT_NEPAL_BOUNDS
    private static double km(double a, double b, double c, double d) {
        double R = 6371.0, p1=Math.toRadians(a), p2=Math.toRadians(c), dp=Math.toRadians(c-a), dl=Math.toRadians(d-b);
        double q=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
        return 2*R*Math.atan2(Math.sqrt(q),Math.sqrt(1-q));
    }

    private static final class StationDot {
        Object original; String stationId, name, riverName, district, stage; double lat, lon, level; long at; boolean fresh;
    }
    private static final class RiverWay {
        String name, type; final List<double[]> points = new ArrayList<>();
    }
}
