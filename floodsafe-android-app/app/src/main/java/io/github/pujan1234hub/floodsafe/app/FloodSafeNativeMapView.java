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
 * 100% native Android river map using MapLibre Native. No WebView is used.
 * Nepal map + river geometry + official live station status + GPS puck.
 */
final class FloodSafeNativeMapView extends FrameLayout {
    interface StationTapListener { void onStationTap(Object stationObject); }

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
    private MapLibreMap map;
    private Style style;
    private boolean styleReady = false;
    boolean terrain = true;
    private double userLat = Double.NaN, userLon = Double.NaN;
    private String districtGeoJson = null;
    private String riversGeoJson = null;
    private long particleStart = 0L;
    private boolean animationRunning = false;

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
                        .include(new LatLng(25.4, 79.2))
                        .include(new LatLng(31.15, 89.15)).build();
                map.setLatLngBoundsForCameraTarget(bounds);
            } catch (Exception ignored) {}
            map.setStyle(new Style.Builder().fromJson(STYLE_JSON), s -> {
                style = s;
                styleReady = true;
                installGeoLayers();
                resetView();
                refreshStationSources();
                refreshRiverRiskSources();
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

    void setBase(Bitmap ignored) { }

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
        refreshStationSources();
        refreshRiverRiskSources();
        refreshUserSource();
    }

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
                try { raw = readAsset("data/nepal-waterways-snapshot.json"); }
                catch (Exception e) { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }
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
                    if (all.size() > 1400) all = new ArrayList<>(all.subList(0, 1400));
                    rivers.clear();
                    rivers.addAll(all);
                    riversGeoJson = makeRiversGeoJson(all);
                }
            } catch (Exception ignored) {}
            main.post(() -> {
                installGeoLayers();
                refreshRiverRiskSources();
            });
        });
    }

    private void installGeoLayers() {
        if (!styleReady || style == null) return;
        try {
            if (districtGeoJson != null && style.getSource("fs-districts") == null) {
                style.addSource(new GeoJsonSource("fs-districts", districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill", "fs-districts").withProperties(
                        fillColor("#8deeff"), fillOpacity(0.08f)));
                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(
                        lineColor("#e8fbff"), lineWidth(1.15f), lineOpacity(0.82f), lineJoin(LINE_JOIN_ROUND)));
            }
            if (riversGeoJson != null && style.getSource("fs-rivers") == null) {
                style.addSource(new GeoJsonSource("fs-rivers", riversGeoJson));
                style.addLayer(new LineLayer("fs-river-glow", "fs-rivers").withProperties(
                        lineColor("#003d55"), lineWidth(4.0f), lineOpacity(0.55f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(
                        lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
            }
            ensureRiverRiskSource("fs-river-alert", "fs-river-alert-glow", "fs-river-alert-layer", "#ffc928");
            ensureRiverRiskSource("fs-river-warning", "fs-river-warning-glow", "fs-river-warning-layer", "#ff8a1f");
            ensureRiverRiskSource("fs-river-danger", "fs-river-danger-glow", "fs-river-danger-layer", "#f22f4b");
            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#d6fbff", 2.7f, 0.90f);
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
            refreshRiverRiskSources();
            refreshUserSource();
        } catch (Exception ignored) {}
    }

    private void ensureRiverRiskSource(String sourceId, String glowId, String layerId, String color) {
        if (style.getSource(sourceId) != null) return;
        style.addSource(new GeoJsonSource(sourceId, emptyFeatureCollection()));
        style.addLayer(new LineLayer(glowId, sourceId).withProperties(
                lineColor(color), lineWidth(7.0f), lineOpacity(0.30f),
                lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
        style.addLayer(new LineLayer(layerId, sourceId).withProperties(
                lineColor(color), lineWidth(3.6f), lineOpacity(1.0f),
                lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));
    }

    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {
        if (style.getSource(sourceId) != null) return;
        style.addSource(new GeoJsonSource(sourceId, emptyFeatureCollection()));
        style.addLayer(new CircleLayer(layerId, sourceId).withProperties(
                circleColor(color), circleRadius(radius), circleOpacity(opacity),
                circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)));
    }

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

    private void refreshRiverRiskSources() {
        if (!styleReady || style == null || rivers.isEmpty()) return;
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        for (RiverWay river : rivers) river.stage = riverStage(river, snapshot);
        setGeo("fs-river-alert", riverGeoByStage(rivers, "alert"));
        setGeo("fs-river-warning", riverGeoByStage(rivers, "warning"));
        setGeo("fs-river-danger", riverGeoByStage(rivers, "danger"));
    }

    private static String riverStage(RiverWay river, List<StationDot> snapshot) {
        int best = 0;
        for (StationDot s : snapshot) {
            if (!s.fresh) continue;
            String stage = normalizeStage(s.stage);
            int severity = severity(stage);
            if (severity <= best || severity == 0) continue;
            if (nameMatches(river.name, s.name) || stationNearRiver(s, river, 2.5)) best = severity;
        }
        if (best >= 3) return "danger";
        if (best == 2) return "warning";
        if (best == 1) return "alert";
        return "normal";
    }

    private static boolean stationNearRiver(StationDot s, RiverWay r, double maxKm) {
        int stride = Math.max(1, r.points.size() / 100);
        double best = Double.MAX_VALUE;
        for (int i = 0; i < r.points.size(); i += stride) {
            double[] p = r.points.get(i);
            double d = km(s.lat, s.lon, p[1], p[0]);
            if (d < best) best = d;
            if (best <= maxKm) return true;
        }
        return false;
    }

    private static boolean nameMatches(String a, String b) {
        String x = normalizeName(a), y = normalizeName(b);
        if (x.isEmpty() || y.isEmpty()) return false;
        if (x.equals(y) || x.contains(y) || y.contains(x)) return true;
        String[] xx = x.split(" "), yy = y.split(" ");
        int common = 0;
        for (String p : xx) {
            if (p.length() < 3 || genericWord(p)) continue;
            for (String q : yy) if (p.equals(q)) { common++; break; }
        }
        return common >= 1;
    }

    private static String normalizeName(String value) {
        if (value == null) return "";
        return value.toLowerCase(Locale.ROOT).replace('_', ' ').replace('-', ' ')
                .replaceAll("[^\\p{L}\\p{N} ]", " ").replaceAll("\\s+", " ").trim();
    }

    private static boolean genericWord(String s) {
        return "river".equals(s) || "khola".equals(s) || "nadi".equals(s)
                || "station".equals(s) || "gauge".equals(s) || "नदी".equals(s) || "खोला".equals(s);
    }

    private static int severity(String stage) {
        if ("danger".equals(stage)) return 3;
        if ("warning".equals(stage)) return 2;
        if ("alert".equals(stage)) return 1;
        return 0;
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
        for (RiverWay r : rivers) {
            int stride = Math.max(1, r.points.size() / 140);
            for (int i = 0; i < r.points.size(); i += stride) {
                double[] p = r.points.get(i);
                double x = km(la, lo, p[1], p[0]);
                if (x < d) { d = x; best = r; }
            }
        }
        return d <= thresholdKm ? best : null;
    }

    private void showRiver(RiverWay r, double la, double lo) {
        StationDot gauge = nearestStation(la, lo);
        StringBuilder msg = new StringBuilder();
        msg.append("River status: ").append(r.stage.toUpperCase(Locale.ROOT));
        if (gauge != null) {
            double d = km(la, lo, gauge.lat, gauge.lon);
            msg.append("\n\nनजिकको official gauge: ").append(gauge.name)
                    .append(String.format(Locale.US, " • %.1f km", d));
            if (Double.isFinite(gauge.level)) msg.append(String.format(Locale.US, "\nपानीको सतह: %.2f m", gauge.level));
            msg.append("\nStatus: ").append(gauge.fresh ? gauge.stage.toUpperCase(Locale.ROOT) : "STALE / UNKNOWN");
            if (Double.isFinite(gauge.rainfallMm)) {
                msg.append(String.format(Locale.US, "\nवर्षा: %.1f mm", gauge.rainfallMm));
            }
        } else msg.append("\n\nयो नदी segment नजिक direct official gauge reference भेटिएन।");
        msg.append("\n\nRainfall station markers map मा देखाइँदैनन्; उपलब्ध rainfall detail station/river detail भित्र मात्र देखाइन्छ।");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ", null).show();
    }

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
                JSONArray features = new JSONArray();
                int n = Math.min(36, rivers.size());
                double phase = ((System.currentTimeMillis() - particleStart) % 6500L) / 6500.0;
                for (int i = 0; i < n; i++) {
                    RiverWay r = rivers.get(i);
                    if (r.points.size() < 2) continue;
                    double v = ((phase + i * 0.173) % 1.0) * (r.points.size() - 1);
                    int ix = Math.min(r.points.size() - 2, (int) Math.floor(v));
                    double f = v - ix;
                    double[] a = r.points.get(ix), b = r.points.get(ix + 1);
                    double lo = a[0] + (b[0] - a[0]) * f, la = a[1] + (b[1] - a[1]) * f;
                    features.put(pointFeature(lo, la, "flow"));
                }
                JSONObject fc = new JSONObject().put("type", "FeatureCollection").put("features", features);
                setGeo("fs-flow-particles", fc.toString());
            } catch (Exception ignored) {}
            main.postDelayed(this, 160L);
        }
    };

    private StationDot readStation(Object o) {
        if (o == null) return null;
        try {
            Class<?> c = o.getClass();
            double la = getDouble(c, o, "lat"), lo = getDouble(c, o, "lon");
            if (!Double.isFinite(la) || !Double.isFinite(lo)) return null;
            StationDot s = new StationDot();
            s.original = o; s.lat = la; s.lon = lo;
            s.name = getString(c, o, "name", "Official river station");
            s.stage = getString(c, o, "stage", "normal").toLowerCase(Locale.ROOT);
            s.fresh = getBoolean(c, o, "fresh", false);
            s.level = getDouble(c, o, "level");
            s.rainfallMm = getOptionalDouble(c, o,
                    "rainfallMm", "rainfall", "rainfall24h", "rain24h", "rain_mm", "precipitation");
            return s;
        } catch (Exception ignored) { return null; }
    }

    private static double getDouble(Class<?> c, Object o, String name) throws Exception {
        Field f = c.getDeclaredField(name); f.setAccessible(true); return ((Number) f.get(o)).doubleValue();
    }
    private static double getOptionalDouble(Class<?> c, Object o, String... names) {
        for (String name : names) {
            try {
                Field f = c.getDeclaredField(name); f.setAccessible(true);
                Object v = f.get(o);
                if (v instanceof Number) {
                    double n = ((Number) v).doubleValue();
                    if (Double.isFinite(n)) return n;
                }
            } catch (Exception ignored) {}
        }
        return Double.NaN;
    }
    private static boolean getBoolean(Class<?> c, Object o, String name, boolean fallback) {
        try { Field f=c.getDeclaredField(name); f.setAccessible(true); return f.getBoolean(o); } catch (Exception e) { return fallback; }
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
        for (RiverWay r : ways) features.put(riverFeature(r));
        return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
    }

    private static String riverGeoByStage(List<RiverWay> ways, String stage) {
        try {
            JSONArray features = new JSONArray();
            for (RiverWay r : ways) if (stage.equals(r.stage)) features.put(riverFeature(r));
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }

    private static JSONObject riverFeature(RiverWay r) throws Exception {
        JSONArray coords = new JSONArray();
        for (double[] p : r.points) coords.put(new JSONArray().put(p[0]).put(p[1]));
        JSONObject geom = new JSONObject().put("type", "LineString").put("coordinates", coords);
        JSONObject props = new JSONObject().put("name", r.name).put("type", r.type).put("stage", r.stage);
        return new JSONObject().put("type", "Feature").put("geometry", geom).put("properties", props);
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
    private static boolean isNepalish(double la, double lo) { return la >= 25.4 && la <= 31.15 && lo >= 79.2 && lo <= 89.15; }
    private static double km(double a, double b, double c, double d) {
        double R = 6371.0, p1=Math.toRadians(a), p2=Math.toRadians(c), dp=Math.toRadians(c-a), dl=Math.toRadians(d-b);
        double q=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);
        return 2*R*Math.atan2(Math.sqrt(q),Math.sqrt(1-q));
    }

    private static final class StationDot {
        Object original; String name, stage; double lat, lon, level, rainfallMm; boolean fresh;
    }
    private static final class RiverWay {
        String name, type, stage = "normal"; final List<double[]> points = new ArrayList<>();
    }
}
