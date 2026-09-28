package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;
import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.CircleLayer;
import org.maplibre.android.style.layers.Layer;
import org.maplibre.android.style.layers.LineLayer;
import org.maplibre.android.style.sources.GeoJsonSource;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.WeakHashMap;

import static org.maplibre.android.style.layers.PropertyFactory.circleColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.lineOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;

/**
 * v0.9.18 targeted repair.
 *
 * The original NativeFullActivity and FloodSafeNativeMapView are deliberately not
 * edited. This layer only:
 *  1) rechecks the app's official BIPAD mirror every 10 seconds while foregrounded;
 *  2) separates the map's latest-official display from the strict <=10 minute safety
 *     freshness used by alerts (old observations are NEVER promoted to alert-fresh);
 *  3) makes station-linked river movement unmistakably visible with moving comets
 *     and a breathing river glow.
 */
final class RiverRealtimeV0918 {
    private static final WeakHashMap<Activity, Session> SESSIONS = new WeakHashMap<>();
    private static boolean installed;

    private RiverRealtimeV0918() {}

    static synchronized void install(Context context) {
        if (installed || context == null) return;
        Context app = context.getApplicationContext();
        if (!(app instanceof Application)) return;
        installed = true;
        ((Application) app).registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override public void onActivityCreated(Activity activity, Bundle bundle) {}
            @Override public void onActivityStarted(Activity activity) {}
            @Override public void onActivityResumed(Activity activity) {
                if (!target(activity)) return;
                Session s;
                synchronized (SESSIONS) {
                    s = SESSIONS.get(activity);
                    if (s == null) {
                        s = new Session(activity);
                        SESSIONS.put(activity, s);
                    }
                }
                s.start();
            }
            @Override public void onActivityPaused(Activity activity) {
                if (!target(activity)) return;
                synchronized (SESSIONS) {
                    Session s = SESSIONS.get(activity);
                    if (s != null) s.pause();
                }
            }
            @Override public void onActivityStopped(Activity activity) {}
            @Override public void onActivitySaveInstanceState(Activity activity, Bundle bundle) {}
            @Override public void onActivityDestroyed(Activity activity) {
                synchronized (SESSIONS) {
                    Session s = SESSIONS.remove(activity);
                    if (s != null) s.close();
                }
            }
        });
    }

    private static boolean target(Activity activity) {
        return activity != null && activity.getClass().getName().endsWith(".NativeFullActivity");
    }

    private static final class Session {
        final Activity activity;
        final Handler main = new Handler(Looper.getMainLooper());
        boolean running;
        long animationStart;

        Session(Activity activity) { this.activity = activity; }

        void start() {
            if (running) return;
            running = true;
            if (animationStart == 0L) animationStart = System.currentTimeMillis();
            main.removeCallbacks(pollTick);
            main.removeCallbacks(flowTick);
            main.post(pollTick);
            main.postDelayed(flowTick, 450L);
        }

        void pause() {
            running = false;
            main.removeCallbacks(pollTick);
            main.removeCallbacks(flowTick);
        }

        void close() { pause(); }

        final Runnable pollTick = new Runnable() {
            @Override public void run() {
                if (!running || activity.isFinishing() || activity.isDestroyed()) return;
                invokeRiverRefresh();
                // BIPAD/DHM gauges usually publish at minute-scale intervals. A 10 s
                // mirror poll sees a source change quickly without falsifying source time.
                main.postDelayed(this, 10_000L);
            }
        };

        final Runnable flowTick = new Runnable() {
            @Override public void run() {
                if (!running || activity.isFinishing() || activity.isDestroyed()) return;
                try { renderVisibleFlow(); } catch (Throwable ignored) {}
                main.postDelayed(this, 80L);
            }
        };

        void invokeRiverRefresh() {
            try {
                Method m = activity.getClass().getDeclaredMethod("refreshRivers");
                m.setAccessible(true);
                m.invoke(activity);
                // refreshRivers does network I/O asynchronously. Update the visual
                // mirror summary shortly after the returned station list is applied.
                main.postDelayed(this::renderLatestOfficialStationDisplay, 2400L);
                main.postDelayed(this::renderLatestOfficialStationDisplay, 5200L);
            } catch (Throwable ignored) {}
        }

        @SuppressWarnings("unchecked")
        void renderLatestOfficialStationDisplay() {
            if (!running || activity.isFinishing() || activity.isDestroyed()) return;
            try {
                Object listObj = activityField("stations");
                if (!(listObj instanceof List)) return;
                List<Object> stationRows;
                synchronized (listObj) { stationRows = new ArrayList<>((List<Object>) listObj); }

                int strictDanger = 0, strictWarning = 0, strictAlert = 0, strictNormal = 0;
                int latest24h = 0, older = 0;
                JSONArray normal = new JSONArray(), alert = new JSONArray(), warning = new JSONArray(), danger = new JSONArray();
                long now = System.currentTimeMillis();
                final long DAY = 24L * 60L * 60L * 1000L;

                for (Object s : stationRows) {
                    if (s == null) continue;
                    boolean fresh = boolField(s, "fresh", false);
                    String strict = stringField(s, "stage", "unknown");
                    if (fresh) {
                        if ("danger".equals(strict)) strictDanger++;
                        else if ("warning".equals(strict)) strictWarning++;
                        else if ("alert".equals(strict)) strictAlert++;
                        else if ("normal".equals(strict)) strictNormal++;
                    }

                    long at = longField(s, "at", -1L);
                    double lat = doubleField(s, "lat"), lon = doubleField(s, "lon");
                    double level = doubleField(s, "level"), warn = doubleField(s, "warning"), dang = doubleField(s, "danger");
                    boolean recent = at > 0L && at <= now + 5L * 60L * 1000L && now - at <= DAY;
                    if (!recent || !Double.isFinite(lat) || !Double.isFinite(lon)) { older++; continue; }
                    latest24h++;
                    String display = latestDisplayStage(level, warn, dang);
                    JSONObject point = pointFeature(lon, lat);
                    if ("danger".equals(display)) danger.put(point);
                    else if ("warning".equals(display)) warning.put(point);
                    else if ("alert".equals(display)) alert.put(point);
                    else if ("normal".equals(display)) normal.put(point);
                }

                Object nativeMap = activityField("map");
                Style style = nativeMap == null ? null : (Style) objectField(nativeMap, "style");
                Boolean ready = nativeMap == null ? null : (Boolean) objectField(nativeMap, "styleReady");
                if (style != null && Boolean.TRUE.equals(ready)) {
                    setDisplayStationSource(style, "normal", "#2d8cff", 4.7f, normal);
                    setDisplayStationSource(style, "alert", "#ffc928", 5.3f, alert);
                    setDisplayStationSource(style, "warning", "#ff8a1f", 5.9f, warning);
                    setDisplayStationSource(style, "danger", "#f22f4b", 6.5f, danger);
                }

                boolean en = activity.getSharedPreferences("floodsafe-native-full", Context.MODE_PRIVATE)
                        .getBoolean("lang_en", false);
                String label;
                if (en) {
                    label = "BIPAD mirror auto 10s • safety fresh≤10m: 🔴 " + strictDanger + "  🟠 " + strictWarning
                            + "  🟡 " + strictAlert + "  🔵 " + strictNormal
                            + " • latest official≤24h: " + latest24h + " • older: " + older;
                } else {
                    label = "BIPAD mirror auto १०s • सुरक्षा fresh≤१०m: 🔴 " + strictDanger + "  🟠 " + strictWarning
                            + "  🟡 " + strictAlert + "  🔵 " + strictNormal
                            + " • पछिल्लो official≤२४h: " + latest24h + " • पुरानो: " + older;
                }
                setTextField("feedFresh", label);
                setTextField("nationalFresh", label);
            } catch (Throwable ignored) {}
        }

        void setDisplayStationSource(Style style, String stage, String color, float radius, JSONArray features) {
            try {
                String sourceId = "fs-v0918-display-" + stage;
                String layerId = sourceId + "-layer";
                if (style.getSource(sourceId) == null) style.addSource(new GeoJsonSource(sourceId, emptyCollection()));
                if (style.getLayer(layerId) == null) {
                    style.addLayer(new CircleLayer(layerId, sourceId).withProperties(
                            circleColor(color), circleRadius(radius), circleOpacity(0.94f)));
                }
                GeoJsonSource src = style.getSourceAs(sourceId);
                if (src != null) src.setGeoJson(featureCollection(features));
            } catch (Throwable ignored) {}
        }

        @SuppressWarnings("unchecked")
        void renderVisibleFlow() throws Exception {
            Object nativeMap = activityField("map");
            if (nativeMap == null) return;
            Style style = (Style) objectField(nativeMap, "style");
            Boolean ready = (Boolean) objectField(nativeMap, "styleReady");
            if (style == null || !Boolean.TRUE.equals(ready)) return;

            final String sourceId = "fs-v0918-visible-flow";
            final String glowId = "fs-v0918-visible-flow-glow";
            final String coreId = "fs-v0918-visible-flow-core";
            if (style.getSource(sourceId) == null) style.addSource(new GeoJsonSource(sourceId, emptyCollection()));
            if (style.getLayer(glowId) == null) {
                style.addLayer(new CircleLayer(glowId, sourceId).withProperties(
                        circleColor("#52e7ff"), circleRadius(5.6f), circleOpacity(0.38f)));
            }
            if (style.getLayer(coreId) == null) {
                style.addLayer(new CircleLayer(coreId, sourceId).withProperties(
                        circleColor("#e9fdff"), circleRadius(2.9f), circleOpacity(1.0f)));
            }

            Object listObj = objectField(nativeMap, "monitoredRivers");
            if (!(listObj instanceof List)) return;
            List<Object> ways;
            synchronized (listObj) { ways = new ArrayList<>((List<Object>) listObj); }
            if (ways.isEmpty()) return;

            long elapsed = Math.max(0L, System.currentTimeMillis() - animationStart);
            double basePhase = (elapsed % 4200L) / 4200.0;
            JSONArray features = new JSONArray();
            int emitted = 0;
            final int maxFeatures = 900;

            for (int i = 0; i < ways.size() && emitted < maxFeatures; i++) {
                Object way = ways.get(i);
                Object ptsObj = objectField(way, "points");
                if (!(ptsObj instanceof List)) continue;
                List<?> pts = (List<?>) ptsObj;
                if (pts.size() < 2) continue;

                // Two moving comets per station-linked river; each has a 3-dot trail.
                // Unlike the old single tiny dot, motion is visibly directional.
                for (int comet = 0; comet < 2 && emitted < maxFeatures; comet++) {
                    double cometPhase = (basePhase + i * 0.071 + comet * 0.50) % 1.0;
                    for (int trail = 0; trail < 3 && emitted < maxFeatures; trail++) {
                        double phase = cometPhase - trail * 0.018;
                        while (phase < 0.0) phase += 1.0;
                        double v = phase * (pts.size() - 1);
                        int ix = Math.min(pts.size() - 2, Math.max(0, (int) Math.floor(v)));
                        double frac = v - ix;
                        Object pa = pts.get(ix), pb = pts.get(ix + 1);
                        if (!(pa instanceof double[]) || !(pb instanceof double[])) continue;
                        double[] a = (double[]) pa, b = (double[]) pb;
                        if (a.length < 2 || b.length < 2) continue;
                        double lon = a[0] + (b[0] - a[0]) * frac;
                        double lat = a[1] + (b[1] - a[1]) * frac;
                        features.put(pointFeature(lon, lat));
                        emitted++;
                    }
                }
            }
            GeoJsonSource source = style.getSourceAs(sourceId);
            if (source != null) source.setGeoJson(featureCollection(features));

            // Breathing cyan glow uses the exact existing station-linked river geometry.
            float wave = (float) ((Math.sin(elapsed / 330.0) + 1.0) * 0.5);
            Layer riverGlow = style.getLayer("fs-river-glow");
            if (riverGlow instanceof LineLayer) {
                ((LineLayer) riverGlow).setProperties(
                        lineWidth(6.3f + 1.9f * wave), lineOpacity(0.48f + 0.30f * wave));
            }
            Layer core = style.getLayer("fs-rivers-layer");
            if (core instanceof LineLayer) {
                ((LineLayer) core).setProperties(lineOpacity(0.84f + 0.16f * wave));
            }
            Layer flowCore = style.getLayer(coreId);
            if (flowCore instanceof CircleLayer) {
                ((CircleLayer) flowCore).setProperties(circleRadius(2.6f + 0.9f * wave));
            }
            pulseStationLayer(style, "alert", 5.3f, wave);
            pulseStationLayer(style, "warning", 5.9f, wave);
            pulseStationLayer(style, "danger", 6.5f, wave);
        }

        void pulseStationLayer(Style style, String stage, float base, float wave) {
            try {
                Layer layer = style.getLayer("fs-v0918-display-" + stage + "-layer");
                if (layer instanceof CircleLayer) {
                    ((CircleLayer) layer).setProperties(circleRadius(base + 1.0f * wave));
                }
            } catch (Throwable ignored) {}
        }

        String latestDisplayStage(double level, double warning, double danger) {
            if (!Double.isFinite(level)) return "unknown";
            if (Double.isFinite(danger) && danger > 0.0 && level >= danger) return "danger";
            if (Double.isFinite(warning) && warning > 0.0 && level >= warning) return "warning";
            if (Double.isFinite(warning) && warning > 0.0 && level >= warning * 0.80) return "alert";
            return "normal";
        }

        JSONObject pointFeature(double lon, double lat) throws Exception {
            JSONObject geometry = new JSONObject().put("type", "Point")
                    .put("coordinates", new JSONArray().put(lon).put(lat));
            return new JSONObject().put("type", "Feature")
                    .put("properties", new JSONObject())
                    .put("geometry", geometry);
        }

        String featureCollection(JSONArray features) throws Exception {
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        }

        void setTextField(String name, String text) {
            try {
                Object o = activityField(name);
                if (o instanceof TextView) ((TextView) o).setText(text);
            } catch (Throwable ignored) {}
        }

        Object activityField(String name) {
            try {
                Field f = activity.getClass().getDeclaredField(name);
                f.setAccessible(true);
                return f.get(activity);
            } catch (Throwable e) { return null; }
        }

        Object objectField(Object target, String name) {
            if (target == null) return null;
            try {
                Field f = target.getClass().getDeclaredField(name);
                f.setAccessible(true);
                return f.get(target);
            } catch (Throwable e) { return null; }
        }

        double doubleField(Object target, String name) {
            try { Object v = objectField(target, name); return v instanceof Number ? ((Number) v).doubleValue() : Double.NaN; }
            catch (Throwable e) { return Double.NaN; }
        }

        long longField(Object target, String name, long fallback) {
            try { Object v = objectField(target, name); return v instanceof Number ? ((Number) v).longValue() : fallback; }
            catch (Throwable e) { return fallback; }
        }

        boolean boolField(Object target, String name, boolean fallback) {
            try { Object v = objectField(target, name); return v instanceof Boolean ? (Boolean) v : fallback; }
            catch (Throwable e) { return fallback; }
        }

        String stringField(Object target, String name, String fallback) {
            try { Object v = objectField(target, name); return v == null ? fallback : String.valueOf(v); }
            catch (Throwable e) { return fallback; }
        }
    }

    private static String emptyCollection() {
        return "{\"type\":\"FeatureCollection\",\"features\":[]}";
    }
}
