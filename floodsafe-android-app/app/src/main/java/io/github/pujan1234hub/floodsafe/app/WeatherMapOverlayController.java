package io.github.pujan1234hub.floodsafe.app;

import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;

import org.json.JSONArray;
import org.json.JSONObject;
import org.maplibre.android.maps.MapView;
import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.CircleLayer;
import org.maplibre.android.style.sources.GeoJsonSource;

import java.util.ArrayList;
import java.util.List;

import static org.maplibre.android.style.layers.PropertyFactory.circleColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeWidth;

/**
 * WEATHER_OVERLAY_V2_MAP_ONLY_ANIMATED
 * Weather-model cloud/rain animation layered below FloodSafe river/station layers.
 * FloodSafeNativeMapView, river geometry, river flow/status and station sources are not edited.
 */
final class WeatherMapOverlayController {
    static final class WeatherPoint {
        final String district;
        final double lat, lon, cloud, precipitation, temperature;
        WeatherPoint(String district, double lat, double lon, double cloud, double precipitation, double temperature) {
            this.district = district == null ? "" : district;
            this.lat = lat;
            this.lon = lon;
            this.cloud = cloud;
            this.precipitation = precipitation;
            this.temperature = temperature;
        }
    }

    private static final String EMPTY = "{\"type\":\"FeatureCollection\",\"features\":[]}";
    private static final String SRC_LIGHT = "fs-weather-cloud-light";
    private static final String SRC_MID = "fs-weather-cloud-mid";
    private static final String SRC_HEAVY = "fs-weather-cloud-heavy";
    private static final String SRC_RAIN = "fs-weather-rain";
    private static final String LYR_LIGHT = "fs-weather-cloud-light-layer";
    private static final String LYR_MID = "fs-weather-cloud-mid-layer";
    private static final String LYR_HEAVY = "fs-weather-cloud-heavy-layer";
    private static final String LYR_RAIN = "fs-weather-rain-layer";
    private static final long ANIMATION_MS = 2200L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<WeatherPoint> points = new ArrayList<>();
    private final MapView mapView;
    private Style style;
    private boolean enabled = true;
    private boolean destroyed = false;
    private int retries = 0;
    private long phaseStep = 0L;

    WeatherMapOverlayController(FloodSafeNativeMapView host) {
        mapView = findMapView(host);
        if (mapView != null) {
            mapView.getMapAsync(map -> map.getStyle(s -> {
                style = s;
                retries = 0;
                refreshFrame();
                startAnimation();
            }));
        }
    }

    void setEnabled(boolean enabled) {
        this.enabled = enabled;
        retries = 0;
        refreshFrame();
        if (enabled) startAnimation();
    }

    void update(List<WeatherPoint> next) {
        synchronized (points) {
            points.clear();
            if (next != null) points.addAll(next);
        }
        retries = 0;
        refreshFrame();
        startAnimation();
    }

    void destroy() {
        destroyed = true;
        main.removeCallbacksAndMessages(null);
    }

    private void startAnimation() {
        if (destroyed) return;
        main.removeCallbacks(animationTick);
        main.postDelayed(animationTick, ANIMATION_MS);
    }

    private final Runnable animationTick = new Runnable() {
        @Override public void run() {
            if (destroyed) return;
            if (enabled) {
                phaseStep++;
                refreshFrame();
            }
            main.postDelayed(this, ANIMATION_MS);
        }
    };

    private void refreshFrame() {
        main.post(() -> {
            if (destroyed) return;
            if (style == null || !style.isFullyLoaded()) {
                if (mapView != null && retries++ < 30) {
                    mapView.getMapAsync(map -> map.getStyle(s -> style = s));
                    main.postDelayed(this::refreshFrame, 400L);
                }
                return;
            }
            try {
                // Soft, translucent weather visuals. Every layer is inserted below the river layer.
                ensure(style, SRC_LIGHT, LYR_LIGHT, "#f7fbff", 24f, 0.11f, "#ffffff");
                ensure(style, SRC_MID, LYR_MID, "#edf4f7", 34f, 0.17f, "#ffffff");
                ensure(style, SRC_HEAVY, LYR_HEAVY, "#d5e0e6", 45f, 0.24f, "#ffffff");
                ensure(style, SRC_RAIN, LYR_RAIN, "#2aa7ff", 23f, 0.28f, "#bde7ff");
                if (!enabled) {
                    setGeo(style, SRC_LIGHT, EMPTY);
                    setGeo(style, SRC_MID, EMPTY);
                    setGeo(style, SRC_HEAVY, EMPTY);
                    setGeo(style, SRC_RAIN, EMPTY);
                    return;
                }
                List<WeatherPoint> snapshot;
                synchronized (points) { snapshot = new ArrayList<>(points); }
                double phase = (phaseStep % 18L) / 18.0;
                setGeo(style, SRC_LIGHT, featureCollection(snapshot, 25, 50, false, phase));
                setGeo(style, SRC_MID, featureCollection(snapshot, 50, 75, false, phase));
                setGeo(style, SRC_HEAVY, featureCollection(snapshot, 75, 101, false, phase));
                setGeo(style, SRC_RAIN, featureCollection(snapshot, 0, 101, true, phase));
            } catch (Exception e) {
                android.util.Log.e("FloodSafeWeather", "weather overlay refresh failed", e);
            }
        });
    }

    private static void ensure(Style style, String sourceId, String layerId, String color,
                               float radius, float opacity, String stroke) {
        if (style.getSource(sourceId) == null) style.addSource(new GeoJsonSource(sourceId, EMPTY));
        if (style.getLayer(layerId) == null) {
            CircleLayer layer = new CircleLayer(layerId, sourceId).withProperties(
                    circleColor(color), circleRadius(radius), circleOpacity(opacity),
                    circleStrokeColor(stroke), circleStrokeWidth(0.35f));
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static void setGeo(Style style, String sourceId, String json) {
        GeoJsonSource src = style.getSourceAs(sourceId);
        if (src != null) src.setGeoJson(json);
    }

    private static String featureCollection(List<WeatherPoint> all, double minCloud, double maxCloud,
                                            boolean rainOnly, double phase) {
        try {
            JSONObject root = new JSONObject();
            root.put("type", "FeatureCollection");
            JSONArray features = new JSONArray();
            for (WeatherPoint p : all) {
                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon)) continue;
                if (rainOnly) {
                    if (!Double.isFinite(p.precipitation) || p.precipitation < 0.10) continue;
                    // Rain shifts only slightly so the displayed affected district remains truthful.
                    double drift = 0.018 * Math.sin((phase + hashPhase(p.district)) * Math.PI * 2.0);
                    features.put(pointFeature(p, p.lon + drift, p.lat, "rain"));
                } else {
                    if (!Double.isFinite(p.cloud) || p.cloud < minCloud || p.cloud >= maxCloud) continue;
                    // Three translucent particles per district make a slow cloud-bank drift while the
                    // underlying Open-Meteo cloud amount remains the data source for whether it exists.
                    double seed = hashPhase(p.district);
                    double angle = (phase + seed) * Math.PI * 2.0;
                    double strength = 0.035 + Math.min(0.055, Math.max(0.0, p.cloud) / 1800.0);
                    for (int i = 0; i < 3; i++) {
                        double a = angle + i * 2.09439510239;
                        double lo = p.lon + Math.cos(a) * strength;
                        double la = p.lat + Math.sin(a) * strength * 0.62;
                        features.put(pointFeature(p, lo, la, "cloud"));
                    }
                }
            }
            root.put("features", features);
            return root.toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

    private static JSONObject pointFeature(WeatherPoint p, double lon, double lat, String kind) throws Exception {
        JSONObject feature = new JSONObject();
        feature.put("type", "Feature");
        JSONObject geometry = new JSONObject();
        geometry.put("type", "Point");
        geometry.put("coordinates", new JSONArray().put(lon).put(lat));
        feature.put("geometry", geometry);
        JSONObject props = new JSONObject();
        props.put("district", p.district);
        props.put("cloud", p.cloud);
        props.put("precipitation", p.precipitation);
        props.put("temperature", p.temperature);
        props.put("kind", kind);
        feature.put("properties", props);
        return feature;
    }

    private static double hashPhase(String value) {
        int h = value == null ? 0 : value.hashCode();
        return (Math.abs((long)h) % 1000L) / 1000.0;
    }

    private static MapView findMapView(View root) {
        if (root instanceof MapView) return (MapView) root;
        if (root instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) root;
            for (int i = 0; i < g.getChildCount(); i++) {
                MapView found = findMapView(g.getChildAt(i));
                if (found != null) return found;
            }
        }
        return null;
    }
}
