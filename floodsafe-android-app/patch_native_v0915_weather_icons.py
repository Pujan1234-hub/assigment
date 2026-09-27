from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
OVERLAY = J / "WeatherMapOverlayController.java"
GRADLE = ROOT / "app/build.gradle"

s = OVERLAY.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

def repl(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)

if 'V0914_CURRENT_RAIN_ONLY' not in s:
    raise SystemExit('v0.9.14 current-rain-only overlay missing')
if 'final int weatherCode;' not in s:
    raise SystemExit('weatherCode support missing')

s = repl(
    s,
    'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.sources.GeoJsonSource;',
    'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.layers.SymbolLayer;\nimport org.maplibre.android.style.sources.GeoJsonSource;',
    'SymbolLayer import',
)

s = repl(
    s,
    '    private static final String SRC_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy";',
    '    private static final String SRC_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy";\n'
    '    private static final String SRC_ICON_CLEAR = "fs-weather-icon-clear";\n'
    '    private static final String SRC_ICON_CLOUD = "fs-weather-icon-cloud";\n'
    '    private static final String SRC_ICON_RAIN = "fs-weather-icon-rain";\n'
    '    private static final String SRC_ICON_THUNDER = "fs-weather-icon-thunder";',
    'weather icon sources',
)
s = repl(
    s,
    '    private static final String LYR_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy-layer";',
    '    private static final String LYR_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy-layer";\n'
    '    private static final String LYR_ICON_CLEAR = "fs-weather-icon-clear-layer";\n'
    '    private static final String LYR_ICON_CLOUD = "fs-weather-icon-cloud-layer";\n'
    '    private static final String LYR_ICON_RAIN = "fs-weather-icon-rain-layer";\n'
    '    private static final String LYR_ICON_THUNDER = "fs-weather-icon-thunder-layer";\n'
    '    private static final String IMG_ICON_CLEAR = "fs-weather-img-clear";\n'
    '    private static final String IMG_ICON_CLOUD = "fs-weather-img-cloud";\n'
    '    private static final String IMG_ICON_RAIN = "fs-weather-img-rain";\n'
    '    private static final String IMG_ICON_THUNDER = "fs-weather-img-thunder";',
    'weather icon layers/images',
)

s = repl(
    s,
    '                ensureRainLine(style, SRC_DHM_RAIN_HEAVY, LYR_DHM_RAIN_HEAVY, "#e8fbff", 2.45f, 0.90f);',
    '                ensureRainLine(style, SRC_DHM_RAIN_HEAVY, LYR_DHM_RAIN_HEAVY, "#e8fbff", 2.45f, 0.90f);\n'
    '                ensureWeatherIcon(style, SRC_ICON_CLEAR, LYR_ICON_CLEAR, IMG_ICON_CLEAR, "☀️");\n'
    '                ensureWeatherIcon(style, SRC_ICON_CLOUD, LYR_ICON_CLOUD, IMG_ICON_CLOUD, "☁️");\n'
    '                ensureWeatherIcon(style, SRC_ICON_RAIN, LYR_ICON_RAIN, IMG_ICON_RAIN, "🌧️");\n'
    '                ensureWeatherIcon(style, SRC_ICON_THUNDER, LYR_ICON_THUNDER, IMG_ICON_THUNDER, "⛈️");',
    'install weather icons',
)

# Insert immediately before refresh's applyPulse/updateRainFrames pair. This is stable
# across the v0.9.13/v0.9.14 generated overlay even when rain-source population changes.
s = repl(
    s,
    '                applyPulse();\n                updateRainFrames();',
    '                setGeo(style, SRC_ICON_CLEAR, weatherIconPoints(snapshot, "clear"));\n'
    '                setGeo(style, SRC_ICON_CLOUD, weatherIconPoints(snapshot, "cloud"));\n'
    '                setGeo(style, SRC_ICON_RAIN, weatherIconPoints(snapshot, "rain"));\n'
    '                setGeo(style, SRC_ICON_THUNDER, weatherIconPoints(snapshot, "thunder"));\n'
    '                applyPulse();\n                updateRainFrames();',
    'populate weather icons',
)

s = repl(
    s,
    '        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);',
    '        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);\n'
    '        setGeo(style, SRC_ICON_CLEAR, EMPTY);\n'
    '        setGeo(style, SRC_ICON_CLOUD, EMPTY);\n'
    '        setGeo(style, SRC_ICON_RAIN, EMPTY);\n'
    '        setGeo(style, SRC_ICON_THUNDER, EMPTY);',
    'clear weather icons',
)

anchor = '    private static void setGeo(Style style, String sourceId, String json) {'
if anchor not in s:
    raise SystemExit('setGeo anchor missing')
helpers = r'''    // V0915_WEB_STYLE_WEATHER_ICONS
    private static void ensureWeatherIcon(Style style, String sourceId, String layerId,
                                          String imageId, String emoji) {
        if (style.getSource(sourceId) == null) style.addSource(new GeoJsonSource(sourceId, EMPTY));
        try {
            if (style.getImage(imageId) == null) style.addImage(imageId, weatherEmojiBitmap(emoji));
        } catch (Exception ignored) {}
        if (style.getLayer(layerId) == null) {
            SymbolLayer layer = new SymbolLayer(layerId, sourceId).withProperties(
                    org.maplibre.android.style.layers.PropertyFactory.iconImage(imageId),
                    org.maplibre.android.style.layers.PropertyFactory.iconSize(0.62f),
                    org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap(false),
                    org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement(false)
            );
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static android.graphics.Bitmap weatherEmojiBitmap(String emoji) {
        int size = 88;
        android.graphics.Bitmap bitmap = android.graphics.Bitmap.createBitmap(
                size, size, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas canvas = new android.graphics.Canvas(bitmap);
        android.graphics.Paint bg = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bg.setColor(android.graphics.Color.argb(210, 255, 255, 255));
        canvas.drawCircle(size / 2f, size / 2f, size * 0.43f, bg);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG | android.graphics.Paint.SUBPIXEL_TEXT_FLAG);
        p.setTextAlign(android.graphics.Paint.Align.CENTER);
        p.setTextSize(49f);
        android.graphics.Paint.FontMetrics fm = p.getFontMetrics();
        float y = size / 2f - (fm.ascent + fm.descent) / 2f;
        canvas.drawText(emoji, size / 2f, y, p);
        return bitmap;
    }

'''
s = s.replace(anchor, helpers + anchor, 1)

anchor2 = '    private String polygonBucket(List<WeatherPoint> weather, double minCloud, double maxCloud, boolean rainOnly) {'
if anchor2 not in s:
    raise SystemExit('polygonBucket anchor missing')
icon_methods = r'''    private static String currentWeatherKind(WeatherPoint p) {
        if (p == null) return "cloud";
        int c = p.weatherCode;
        if (c >= 95 && c <= 99) return "thunder";
        if (isRainSignal(p)) return "rain";
        if ((c >= 1 && c <= 3) || (c >= 45 && c <= 48)) return "cloud";
        if (Double.isFinite(p.cloud) && p.cloud >= 35d) return "cloud";
        return "clear";
    }

    private String weatherIconPoints(List<WeatherPoint> weather, String kind) {
        try {
            JSONArray features = new JSONArray();
            if (weather != null) {
                for (WeatherPoint p : weather) {
                    if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon)) continue;
                    if (!kind.equals(currentWeatherKind(p))) continue;
                    JSONObject geom = new JSONObject().put("type", "Point")
                            .put("coordinates", new JSONArray().put(p.lon).put(p.lat));
                    JSONObject props = new JSONObject()
                            .put("district", p.district)
                            .put("weather_code", p.weatherCode)
                            .put("cloud", p.cloud)
                            .put("precipitation", p.precipitation)
                            .put("kind", kind);
                    features.put(new JSONObject().put("type", "Feature")
                            .put("geometry", geom).put("properties", props));
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

'''
s = s.replace(anchor2, icon_methods + anchor2, 1)

g = repl(g, 'versionCode 31', 'versionCode 32', 'versionCode')
g = repl(g, "versionName '0.9.14-current-rain-only'", "versionName '0.9.15-current-weather-icons'", 'versionName')

for token in [
    'V0915_WEB_STYLE_WEATHER_ICONS', 'SRC_ICON_CLEAR', 'SRC_ICON_CLOUD',
    'SRC_ICON_RAIN', 'SRC_ICON_THUNDER', 'weatherIconPoints(snapshot, "clear")',
    'weatherIconPoints(snapshot, "cloud")', 'weatherIconPoints(snapshot, "rain")',
    'weatherIconPoints(snapshot, "thunder")', 'currentWeatherKind(WeatherPoint p)'
]:
    assert token in s, token
assert 'versionCode 32' in g
assert "versionName '0.9.15-current-weather-icons'" in g

OVERLAY.write_text(s, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("V0915_CURRENT_WEATHER_ICONS_PATCHED")
