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
import java.util.Locale;
import java.util.WeakHashMap;

import static org.maplibre.android.style.layers.PropertyFactory.circleColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.lineOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;

/**
 * v0.9.18 targeted repair:
 * - keeps the existing NativeFullActivity and FloodSafeNativeMapView map implementation untouched;
 * - mirrors the already configured official river feed every 10 seconds while the screen is active;
 * - makes the existing station-linked river motion unmistakably visible with a lightweight overlay.
 *
 * Safety: this class never promotes stale readings to fresh and never changes warning/danger logic.
 */
final class RiverRealtimeV0918 {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
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
        long lastPollAt;

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
                lastPollAt = System.currentTimeMillis();
                // The official source normally publishes measurements every few minutes.
                // Polling every 10 s mirrors a new BIPAD/DHM observation quickly without
                // pretending old observations are fresh.
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
                main.postDelayed(this::appendSyncLabel, 2200L);
            } catch (Throwable ignored) {}
        }

        void appendSyncLabel() {
            if (!running || activity.isFinishing() || activity.isDestroyed()) return;
            try {
                Field f = activity.getClass().getDeclaredField("feedFresh");
                f.setAccessible(true);
                Object o = f.get(activity);
                if (!(o instanceof TextView)) return;
                TextView tv = (TextView) o;
                String current = String.valueOf(tv.getText());
                if (current.contains("auto 10s")) return;
                boolean en = activity.getSharedPreferences("floodsafe-native-full", Context.MODE_PRIVATE)
                        .getBoolean("lang_en", false);
                String suffix = en ? "  • BIPAD mirror: auto 10s" : "  • BIPAD mirror: १० सेकेन्डमा auto";
                tv.setText(current + suffix);
                try {
                    Field nf = activity.getClass().getDeclaredField("nationalFresh");
                    nf.setAccessible(true);
                    Object n = nf.get(activity);
                    if (n instanceof TextView) ((TextView) n).setText(tv.getText());
                } catch (Throwable ignored) {}
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
            if (style.getSource(sourceId) == null) {
                style.addSource(new GeoJsonSource(sourceId, emptyCollection()));
            }
            if (style.getLayer(glowId) == null) {
                style.addLayer(new CircleLayer(glowId, sourceId).withProperties(
                        circleColor("#52e7ff"), circleRadius(5.3f), circleOpacity(0.34f)));
            }
            if (style.getLayer(coreId) == null) {
                style.addLayer(new CircleLayer(coreId, sourceId).withProperties(
                        circleColor("#e9fdff"), circleRadius(2.7f), circleOpacity(0.98f)));
            }

            Object listObj = objectField(nativeMap, "monitoredRivers");
            if (!(listObj instanceof List)) return;
            List<Object> ways;
            synchronized (listObj) { ways = new ArrayList<>((List<Object>) listObj); }
            if (ways.isEmpty()) return;

            long elapsed = Math.max(0L, System.currentTimeMillis() - animationStart);
            double basePhase = (elapsed % 4600L) / 4600.0;
            JSONArray features = new JSONArray();
            int emitted = 0;
            final int maxFeatures = 900;

            for (int i = 0; i < ways.size() && emitted < maxFeatures; i++) {
                Object way = ways.get(i);
                Object ptsObj = objectField(way, "points");
                if (!(ptsObj instanceof List)) continue;
                List<?> pts = (List<?>) ptsObj;
                if (pts.size() < 2) continue;

                // Two moving comets per station-linked river. Each comet has a short
                // three-dot trail, making direction/motion obvious instead of looking
                // like another static station marker.
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
                        JSONObject g = new JSONObject().put("type", "Point")
                                .put("coordinates", new JSONArray().put(lon).put(lat));
                        JSONObject p = new JSONObject().put("trail", trail);
                        features.put(new JSONObject().put("type", "Feature").put("properties", p).put("geometry", g));
                        emitted++;
                    }
                }
            }
            GeoJsonSource source = style.getSourceAs(sourceId);
            if (source != null) {
                source.setGeoJson(new JSONObject().put("type", "FeatureCollection")
                        .put("features", features).toString());
            }

            // Strong but non-destructive breathing glow on the same existing river
            // geometry. Geometry/source/stations are not replaced.
            float wave = (float) ((Math.sin(elapsed / 330.0) + 1.0) * 0.5);
            Layer riverGlow = style.getLayer("fs-river-glow");
            if (riverGlow instanceof LineLayer) {
                ((LineLayer) riverGlow).setProperties(
                        lineWidth(6.2f + 1.8f * wave),
                        lineOpacity(0.48f + 0.28f * wave));
            }
            Layer core = style.getLayer("fs-rivers-layer");
            if (core instanceof LineLayer) {
                ((LineLayer) core).setProperties(lineOpacity(0.84f + 0.16f * wave));
            }
            Layer flowCore = style.getLayer(coreId);
            if (flowCore instanceof CircleLayer) {
                ((CircleLayer) flowCore).setProperties(circleRadius(2.5f + 0.7f * wave));
            }
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
    }

    private static String emptyCollection() {
        return "{\"type\":\"FeatureCollection\",\"features\":[]}";
    }
}
