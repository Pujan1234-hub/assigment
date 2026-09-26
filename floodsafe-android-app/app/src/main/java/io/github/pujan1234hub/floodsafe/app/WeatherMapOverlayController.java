package io.github.pujan1234hub.floodsafe.app;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;
import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.CircleLayer;
import org.maplibre.android.style.sources.GeoJsonSource;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

import static org.maplibre.android.style.layers.PropertyFactory.circleColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleOpacity;
import static org.maplibre.android.style.layers.PropertyFactory.circleRadius;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeColor;
import static org.maplibre.android.style.layers.PropertyFactory.circleStrokeWidth;

/**
 * WEATHER_OVERLAY_V1
 * Adds weather-model cloud/precipitation layers to the already-created native MapLibre style
 * without modifying FloodSafeNativeMapView or any river geometry/status logic.
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

    private final FloodSafeNativeMapView host;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<WeatherPoint> points = new ArrayList<>();
    private boolean enabled = true;
    private int retries = 0;

    WeatherMapOverlayController(FloodSafeNativeMapView host) {
        this.host = host;
    }

    void setEnabled(boolean enabled) {
        this.enabled = enabled;
        retries = 0;
        refresh();
    }

    void update(List<WeatherPoint> next) {
        synchronized (points) {
            points.clear();
            if (next != null) points.addAll(next);
        }
        retries = 0;
        refresh();
    }

    void destroy() {
        main.removeCallbacksAndMessages(null);
    }

    private void refresh() {
        main.post(() -> {
            Style style = readStyle();
            if (style == null || !style.isFullyLoaded()) {
                if (retries++ < 30) main.postDelayed(this::refresh, 400L);
                return;
            }
            try {
                ensure(style, SRC_LIGHT, LYR_LIGHT, "#f7fbff", 23f, 0.13f, "#ffffff");
                ensure(style, SRC_MID, LYR_MID, "#eef5f8", 31f, 0.20f, "#ffffff");
                ensure(style, SRC_HEAVY, LYR_HEAVY, "#d7e1e6", 40f, 0.29f, "#ffffff");
                ensure(style, SRC_RAIN, LYR_RAIN, "#2aa7ff", 21f, 0.31f, "#bde7ff");
                if (!enabled) {
                    setGeo(style, SRC_LIGHT, EMPTY);
                    setGeo(style, SRC_MID, EMPTY);
                    setGeo(style, SRC_HEAVY, EMPTY);
                    setGeo(style, SRC_RAIN, EMPTY);
                    return;
                }
                List<WeatherPoint> snapshot;
                synchronized (points) { snapshot = new ArrayList<>(points); }
                setGeo(style, SRC_LIGHT, featureCollection(snapshot, 25, 50, false));
                setGeo(style, SRC_MID, featureCollection(snapshot, 50, 75, false));
                setGeo(style, SRC_HEAVY, featureCollection(snapshot, 75, 101, false));
                setGeo(style, SRC_RAIN, featureCollection(snapshot, 0, 101, true));
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
                    circleStrokeColor(stroke), circleStrokeWidth(0.45f));
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static void setGeo(Style style, String sourceId, String json) {
        GeoJsonSource src = style.getSourceAs(sourceId);
        if (src != null) src.setGeoJson(json);
    }

    private static String featureCollection(List<WeatherPoint> all, double minCloud, double maxCloud, boolean rainOnly) {
        try {
            JSONObject root = new JSONObject();
            root.put("type", "FeatureCollection");
            JSONArray features = new JSONArray();
            for (WeatherPoint p : all) {
                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon)) continue;
                if (rainOnly) {
                    if (!Double.isFinite(p.precipitation) || p.precipitation < 0.10) continue;
                } else {
                    if (!Double.isFinite(p.cloud) || p.cloud < minCloud || p.cloud >= maxCloud) continue;
                }
                JSONObject feature = new JSONObject();
                feature.put("type", "Feature");
                JSONObject geometry = new JSONObject();
                geometry.put("type", "Point");
                JSONArray coordinates = new JSONArray();
                coordinates.put(p.lon);
                coordinates.put(p.lat);
                geometry.put("coordinates", coordinates);
                feature.put("geometry", geometry);
                JSONObject props = new JSONObject();
                props.put("district", p.district);
                props.put("cloud", p.cloud);
                props.put("precipitation", p.precipitation);
                props.put("temperature", p.temperature);
                feature.put("properties", props);
                features.put(feature);
            }
            root.put("features", features);
            return root.toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

    private Style readStyle() {
        try {
            Field f = FloodSafeNativeMapView.class.getDeclaredField("style");
            f.setAccessible(true);
            Object v = f.get(host);
            return v instanceof Style ? (Style) v : null;
        } catch (Exception e) {
            android.util.Log.e("FloodSafeWeather", "native map style unavailable", e);
            return null;
        }
    }
}