package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.TextView;

import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.CircleLayer;
import org.maplibre.android.style.layers.Layer;
import org.maplibre.android.style.layers.LineLayer;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.WeakHashMap;

import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.lineOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;

/**
 * Clean v0.9.18 native realtime hook.
 *
 * This deliberately does NOT add station layers, cards, counters, alternate river
 * geometry, extra particle sources, or replacement UI. The existing v0.9.18 native
 * screen and map remain the source of truth.
 *
 * It only:
 *  - asks the existing NativeFullActivity river loader to recheck the official mirror;
 *  - avoids leaving the card flashing "refreshing" between polls;
 *  - gently animates the already-existing river glow/flow-particle layers so movement
 *    is visible without filling the map with duplicate dots.
 */
final class NativeRealtimeCleanV0918 {
    private static final long RIVER_POLL_MS = 15_000L;
    private static final long FLOW_FRAME_MS = 140L;
    private static final WeakHashMap<Activity, Session> SESSIONS = new WeakHashMap<>();
    private static boolean installed;

    private NativeRealtimeCleanV0918() {}

    static synchronized void install(Context context) {
        if (installed || context == null) return;
        Context app = context.getApplicationContext();
        if (!(app instanceof Application)) return;
        installed = true;

        ((Application) app).registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override public void onActivityCreated(Activity activity, Bundle state) {}
            @Override public void onActivityStarted(Activity activity) {}

            @Override public void onActivityResumed(Activity activity) {
                if (!isTarget(activity)) return;
                Session session;
                synchronized (SESSIONS) {
                    session = SESSIONS.get(activity);
                    if (session == null) {
                        session = new Session(activity);
                        SESSIONS.put(activity, session);
                    }
                }
                session.start();
            }

            @Override public void onActivityPaused(Activity activity) {
                if (!isTarget(activity)) return;
                synchronized (SESSIONS) {
                    Session session = SESSIONS.get(activity);
                    if (session != null) session.pause();
                }
            }

            @Override public void onActivityStopped(Activity activity) {}
            @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {}

            @Override public void onActivityDestroyed(Activity activity) {
                synchronized (SESSIONS) {
                    Session session = SESSIONS.remove(activity);
                    if (session != null) session.pause();
                }
            }
        });
    }

    private static boolean isTarget(Activity activity) {
        return activity != null && activity.getClass().getName().endsWith(".NativeFullActivity");
    }

    private static final class Session {
        private final Activity activity;
        private final Handler main = new Handler(Looper.getMainLooper());
        private boolean running;
        private long animationStart;
        private boolean loggedStyle;

        Session(Activity activity) {
            this.activity = activity;
        }

        void start() {
            if (running) return;
            running = true;
            if (animationStart == 0L) animationStart = System.currentTimeMillis();
            main.removeCallbacks(pollTick);
            main.removeCallbacks(flowTick);
            // NativeFullActivity already performs an initial refresh in onCreate().
            main.postDelayed(pollTick, RIVER_POLL_MS);
            main.postDelayed(flowTick, 500L);
        }

        void pause() {
            running = false;
            main.removeCallbacks(pollTick);
            main.removeCallbacks(flowTick);
        }

        private final Runnable pollTick = new Runnable() {
            @Override public void run() {
                if (!alive()) return;
                quietOfficialRefresh();
                main.postDelayed(this, RIVER_POLL_MS);
            }
        };

        private final Runnable flowTick = new Runnable() {
            @Override public void run() {
                if (!alive()) return;
                try {
                    animateExistingMapLayers();
                } catch (Throwable ignored) {
                    // The base map must never be broken by a cosmetic animation tick.
                }
                main.postDelayed(this, FLOW_FRAME_MS);
            }
        };

        private boolean alive() {
            return running && !activity.isFinishing() && !activity.isDestroyed();
        }

        private void quietOfficialRefresh() {
            try {
                TextView feed = textField(activity, "feedFresh");
                final CharSequence before = feed == null ? null : feed.getText();

                Method method = activity.getClass().getDeclaredMethod("refreshRivers");
                method.setAccessible(true);
                method.invoke(activity);

                // refreshRivers() writes a temporary "Refreshing..." message before its
                // asynchronous request. Keep the last verified summary visible until the
                // request completes and refreshRiverUi() publishes the new official result.
                if (feed != null && before != null && before.length() > 0) {
                    main.postDelayed(() -> {
                        if (!alive()) return;
                        CharSequence current = feed.getText();
                        String s = current == null ? "" : current.toString().toLowerCase();
                        if (s.contains("refresh") || s.contains("हुँदैछ")) {
                            feed.setText(before);
                        }
                    }, 80L);
                }
            } catch (Throwable ignored) {
                // Do not interfere with the base v0.9.18 screen if reflection is unavailable.
            }
        }

        private void animateExistingMapLayers() throws Exception {
            Object mapView = objectField(activity, "map");
            if (mapView == null) return;
            Boolean ready = (Boolean) objectField(mapView, "styleReady");
            Style style = (Style) objectField(mapView, "style");
            if (!Boolean.TRUE.equals(ready) || style == null) return;

            long elapsed = Math.max(0L, System.currentTimeMillis() - animationStart);
            float wave = (float) ((Math.sin(elapsed / 420.0) + 1.0) * 0.5);

            // Only style layers that the original v0.9.18 map already created.
            // No duplicate source/layer is ever added here.
            Layer glow = style.getLayer("fs-river-glow");
            if (glow instanceof LineLayer) {
                ((LineLayer) glow).setProperties(
                        lineWidth(5.7f + 0.8f * wave),
                        lineOpacity(0.46f + 0.10f * wave));
            }

            Layer core = style.getLayer("fs-rivers-layer");
            if (core instanceof LineLayer) {
                ((LineLayer) core).setProperties(lineOpacity(0.91f + 0.08f * wave));
            }

            Layer particles = style.getLayer("fs-flow-particles-layer");
            if (particles instanceof CircleLayer) {
                ((CircleLayer) particles).setProperties(
                        circleRadius(2.25f + 0.55f * wave),
                        circleOpacity(0.84f + 0.14f * wave));
            }

            if (!loggedStyle) {
                loggedStyle = true;
                android.util.Log.i("FloodSafeRealtime", "v0.9.18 clean realtime hook active; original map layers preserved");
            }
        }

        private static TextView textField(Object target, String name) {
            try {
                Object value = objectField(target, name);
                return value instanceof TextView ? (TextView) value : null;
            } catch (Throwable ignored) {
                return null;
            }
        }

        private static Object objectField(Object target, String name) throws Exception {
            Field field = target.getClass().getDeclaredField(name);
            field.setAccessible(true);
            return field.get(target);
        }
    }
}
