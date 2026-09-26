package io.github.pujan1234hub.floodsafe.app;

import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;

import org.json.JSONArray;
import org.json.JSONObject;
import org.maplibre.android.maps.MapView;
import org.maplibre.android.maps.Style;
import org.maplibre.android.style.layers.FillLayer;
import org.maplibre.android.style.sources.GeoJsonSource;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import static org.maplibre.android.style.layers.PropertyFactory.fillColor;
import static org.maplibre.android.style.layers.PropertyFactory.fillOpacity;

/**
 * WEATHER_OVERLAY_V3_AREA_SHADE
 * Map-only weather shading. No circles are rendered.
 * Clear districts stay clear, cloudier districts get progressively darker translucent
 * shading, and current precipitation adds a blue tint. Layers stay below rivers/stations.
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
    private static final long PULSE_MS = 1800L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<WeatherPoint> points = new ArrayList<>();
    private final MapView mapView;
    private Style style;
    private boolean enabled = true;
    private boolean destroyed = false;
    private boolean pulseHigh = false;
    private int retries = 0;
    private JSONObject districtGeometry;

    WeatherMapOverlayController(FloodSafeNativeMapView host) {
        mapView = findMapView(host);
        districtGeometry = loadDistrictGeometry();
        if (mapView != null) {
            mapView.getMapAsync(map -> map.getStyle(s -> {
                style = s;
                retries = 0;
                refresh();
                startPulse();
            }));
        }
    }

    void setEnabled(boolean enabled) {
        this.enabled = enabled;
        retries = 0;
        refresh();
        if (enabled) startPulse();
    }

    void update(List<WeatherPoint> next) {
        synchronized (points) {
            points.clear();
            if (next != null) points.addAll(next);
        }
        retries = 0;
        refresh();
        startPulse();
    }

    void destroy() {
        destroyed = true;
        main.removeCallbacksAndMessages(null);
    }

    private void startPulse() {
        if (destroyed) return;
        main.removeCallbacks(pulseTick);
        main.postDelayed(pulseTick, PULSE_MS);
    }

    private final Runnable pulseTick = new Runnable() {
        @Override public void run() {
            if (destroyed) return;
            if (enabled) {
                pulseHigh = !pulseHigh;
                applyPulse();
            }
            main.postDelayed(this, PULSE_MS);
        }
    };

    private void refresh() {
        main.post(() -> {
            if (destroyed) return;
            if (style == null || !style.isFullyLoaded()) {
                if (mapView != null && retries++ < 30) {
                    mapView.getMapAsync(map -> map.getStyle(s -> style = s));
                    main.postDelayed(this::refresh, 400L);
                }
                return;
            }
            try {
                ensure(style, SRC_LIGHT, LYR_LIGHT, "#f4f7f8", 0.055f);
                ensure(style, SRC_MID, LYR_MID, "#aeb8bf", 0.14f);
                ensure(style, SRC_HEAVY, LYR_HEAVY, "#37424b", 0.27f);
                ensure(style, SRC_RAIN, LYR_RAIN, "#168de2", 0.16f);
                if (!enabled || districtGeometry == null) {
                    clearAll();
                    return;
                }
                List<WeatherPoint> snapshot;
                synchronized (points) { snapshot = new ArrayList<>(points); }
                setGeo(style, SRC_LIGHT, polygonBucket(snapshot, 25d, 50d, false));
                setGeo(style, SRC_MID, polygonBucket(snapshot, 50d, 75d, false));
                setGeo(style, SRC_HEAVY, polygonBucket(snapshot, 75d, 101d, false));
                setGeo(style, SRC_RAIN, polygonBucket(snapshot, 0d, 101d, true));
                applyPulse();
            } catch (Exception e) {
                android.util.Log.e("FloodSafeWeather", "weather area overlay refresh failed", e);
            }
        });
    }

    private void clearAll() {
        if (style == null) return;
        setGeo(style, SRC_LIGHT, EMPTY);
        setGeo(style, SRC_MID, EMPTY);
        setGeo(style, SRC_HEAVY, EMPTY);
        setGeo(style, SRC_RAIN, EMPTY);
    }

    private void applyPulse() {
        if (style == null || !style.isFullyLoaded()) return;
        try {
            float d = pulseHigh ? 0.018f : 0f;
            if (style.getLayer(LYR_LIGHT) != null) style.getLayer(LYR_LIGHT).setProperties(fillOpacity(enabled ? 0.055f + d * 0.35f : 0f));
            if (style.getLayer(LYR_MID) != null) style.getLayer(LYR_MID).setProperties(fillOpacity(enabled ? 0.14f + d : 0f));
            if (style.getLayer(LYR_HEAVY) != null) style.getLayer(LYR_HEAVY).setProperties(fillOpacity(enabled ? 0.27f + d : 0f));
            if (style.getLayer(LYR_RAIN) != null) style.getLayer(LYR_RAIN).setProperties(fillOpacity(enabled ? 0.16f + d : 0f));
        } catch (Exception ignored) {}
    }

    private static void ensure(Style style, String sourceId, String layerId, String color, float opacity) {
        if (style.getSource(sourceId) == null) style.addSource(new GeoJsonSource(sourceId, EMPTY));
        if (style.getLayer(layerId) == null) {
            FillLayer layer = new FillLayer(layerId, sourceId).withProperties(fillColor(color), fillOpacity(opacity));
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static void setGeo(Style style, String sourceId, String json) {
        GeoJsonSource src = style.getSourceAs(sourceId);
        if (src != null) src.setGeoJson(json);
    }

    private String polygonBucket(List<WeatherPoint> weather, double minCloud, double maxCloud, boolean rainOnly) {
        try {
            Map<String, WeatherPoint> byDistrict = new HashMap<>();
            for (WeatherPoint p : weather) {
                if (p == null) continue;
                byDistrict.put(key(p.district), p);
            }
            JSONArray sourceFeatures = districtGeometry.optJSONArray("features");
            JSONArray selected = new JSONArray();
            if (sourceFeatures != null) {
                for (int i = 0; i < sourceFeatures.length(); i++) {
                    JSONObject f = sourceFeatures.optJSONObject(i);
                    if (f == null) continue;
                    JSONObject props = f.optJSONObject("properties");
                    String name = props == null ? "" : props.optString("nameEn", "");
                    WeatherPoint p = byDistrict.get(key(name));
                    if (p == null) continue;
                    boolean use;
                    if (rainOnly) use = Double.isFinite(p.precipitation) && p.precipitation >= 0.10d;
                    else use = Double.isFinite(p.cloud) && p.cloud >= minCloud && p.cloud < maxCloud;
                    if (!use) continue;
                    JSONObject copy = new JSONObject(f.toString());
                    JSONObject cp = copy.optJSONObject("properties");
                    if (cp == null) { cp = new JSONObject(); copy.put("properties", cp); }
                    cp.put("cloud", p.cloud);
                    cp.put("precipitation", p.precipitation);
                    cp.put("temperature", p.temperature);
                    selected.put(copy);
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", selected).toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

    private JSONObject loadDistrictGeometry() {
        if (mapView == null) return null;
        String[] paths = new String[]{
                "floodsafe-nepal/v24/nepal-districts.geojson",
                "floodsafe-nepal/v24/nepal-districts.json"
        };
        for (String path : paths) {
            try (InputStream in = mapView.getContext().getAssets().open(path);
                 BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                StringBuilder b = new StringBuilder();
                String line;
                while ((line = r.readLine()) != null) b.append(line);
                JSONObject j = new JSONObject(b.toString());
                if (j.optJSONArray("features") != null) return j;
            } catch (Exception ignored) {}
        }
        return null;
    }

    private static String key(String value) {
        if (value == null) return "";
        return value.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]", "");
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
