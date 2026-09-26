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
        refreshStationSources();
        refreshRiskRiverSources();
        refreshUserSource();
    } // V0899_STATUS_REFRESH_RECOLOURS_MATCHED_RIVER


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
    private void refreshRiskRiverSources() {
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
    private static boolean isNepalish(double la, double lo) { return la >= 25.4 && la <= 31.15 && lo >= 79.2 && lo <= 89.15; }
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
