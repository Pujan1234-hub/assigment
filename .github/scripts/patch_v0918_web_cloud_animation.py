from pathlib import Path

P = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/WeatherMapOverlayController.java')
s = P.read_text(encoding='utf-8')

def once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, got {n}')
    s = s.replace(old, new, 1)

once(
'''    private static final String SRC_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy";\n    private static final String LYR_LIGHT = "fs-weather-cloud-light-layer";''',
'''    private static final String SRC_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy";\n    // V0918_WEB_STYLE_CLOUDS — visual-only moving cloud sprites driven by current cloud cover.\n    private static final String SRC_CLOUD_SPRITES = "fs-weather-cloud-sprites";\n    private static final String IMG_CLOUD = "fs-weather-cloud-image";\n    private static final String LYR_CLOUD_SPRITES = "fs-weather-cloud-sprites-layer";\n    private static final String LYR_LIGHT = "fs-weather-cloud-light-layer";''',
'cloud ids')

once(
'''    private static final long PULSE_MS = 1900L;\n    private static final long RAIN_FRAME_MS = 240L;''',
'''    private static final long PULSE_MS = 1900L;\n    private static final long RAIN_FRAME_MS = 240L;\n    private static final long CLOUD_FRAME_MS = 420L;''',
'cloud frame constant')

once(
'''    private long rainStartedAt = System.currentTimeMillis();\n    private JSONObject districtGeometry;''',
'''    private long rainStartedAt = System.currentTimeMillis();\n    private long cloudStartedAt = System.currentTimeMillis();\n    private JSONObject districtGeometry;''',
'cloud start field')

once(
'''        main.removeCallbacks(pulseTick);\n        main.removeCallbacks(rainTick);\n        main.postDelayed(pulseTick, PULSE_MS);\n        main.post(rainTick);''',
'''        main.removeCallbacks(pulseTick);\n        main.removeCallbacks(rainTick);\n        main.removeCallbacks(cloudTick);\n        main.postDelayed(pulseTick, PULSE_MS);\n        main.post(rainTick);\n        main.post(cloudTick);''',
'start cloud animation')

once(
'''    private final Runnable rainTick = new Runnable() {\n        @Override public void run() {\n            if (destroyed) return;\n            if (enabled) updateRainFrames();\n            main.postDelayed(this, RAIN_FRAME_MS);\n        }\n    };''',
'''    private final Runnable rainTick = new Runnable() {\n        @Override public void run() {\n            if (destroyed) return;\n            if (enabled) updateRainFrames();\n            main.postDelayed(this, RAIN_FRAME_MS);\n        }\n    };\n\n    // Smooth native cloud drift. This does not alter river/station geometry or risk logic.\n    private final Runnable cloudTick = new Runnable() {\n        @Override public void run() {\n            if (destroyed) return;\n            if (enabled) updateCloudFrames();\n            main.postDelayed(this, CLOUD_FRAME_MS);\n        }\n    };''',
'cloud runnable')

once(
'''                ensureRainLine(style, SRC_RAIN_STREAK_LIGHT, LYR_RAIN_STREAK_LIGHT, "#8fd3ff", 1.25f, 0.48f);\n                ensureRainLine(style, SRC_RAIN_STREAK_HEAVY, LYR_RAIN_STREAK_HEAVY, "#d8f3ff", 2.05f, 0.72f);''',
'''                ensureRainLine(style, SRC_RAIN_STREAK_LIGHT, LYR_RAIN_STREAK_LIGHT, "#8fd3ff", 1.25f, 0.48f);\n                ensureRainLine(style, SRC_RAIN_STREAK_HEAVY, LYR_RAIN_STREAK_HEAVY, "#d8f3ff", 2.05f, 0.72f);\n                ensureCloudSprites(style);''',
'ensure cloud layer')

once(
'''                applyPulse();\n                updateRainFrames();''',
'''                applyPulse();\n                updateRainFrames();\n                updateCloudFrames();''',
'refresh cloud frame')

once(
'''        setGeo(style, SRC_RAIN_STREAK_LIGHT, EMPTY);\n        setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);''',
'''        setGeo(style, SRC_RAIN_STREAK_LIGHT, EMPTY);\n        setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);\n        setGeo(style, SRC_CLOUD_SPRITES, EMPTY);''',
'clear clouds')

anchor = '''    private static void ensureFill(Style style, String sourceId, String layerId, String color, float opacity) {'''
if anchor not in s:
    raise SystemExit('ensureFill anchor missing')
cloud_methods = r'''    private void updateCloudFrames() {
        if (!enabled || style == null || !style.isFullyLoaded()) return;
        try {
            ensureCloudSprites(style);
            double phase = ((System.currentTimeMillis() - cloudStartedAt) % 18000L) / 18000.0d;
            setGeo(style, SRC_CLOUD_SPRITES, cloudSprites(snapshot(), phase));
        } catch (Exception ignored) {}
    }

    private static void ensureCloudSprites(Style style) {
        if (style.getSource(SRC_CLOUD_SPRITES) == null) {
            style.addSource(new GeoJsonSource(SRC_CLOUD_SPRITES, EMPTY));
        }
        if (style.getImage(IMG_CLOUD) == null) {
            style.addImage(IMG_CLOUD, cloudBitmap());
        }
        if (style.getLayer(LYR_CLOUD_SPRITES) == null) {
            org.maplibre.android.style.layers.SymbolLayer layer =
                    new org.maplibre.android.style.layers.SymbolLayer(LYR_CLOUD_SPRITES, SRC_CLOUD_SPRITES)
                    .withProperties(
                            org.maplibre.android.style.layers.PropertyFactory.iconImage(IMG_CLOUD),
                            org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap(true),
                            org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement(true),
                            org.maplibre.android.style.layers.PropertyFactory.iconOpacity(0.78f),
                            org.maplibre.android.style.layers.PropertyFactory.iconSize(
                                    org.maplibre.android.style.expressions.Expression.interpolate(
                                            org.maplibre.android.style.expressions.Expression.linear(),
                                            org.maplibre.android.style.expressions.Expression.get("cloud"),
                                            org.maplibre.android.style.expressions.Expression.stop(25, 0.48f),
                                            org.maplibre.android.style.expressions.Expression.stop(60, 0.68f),
                                            org.maplibre.android.style.expressions.Expression.stop(100, 0.88f)
                                    ))
                    );
            // Keep official river/station layers readable above weather visuals.
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static android.graphics.Bitmap cloudBitmap() {
        final int w = 180, h = 108;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(w, h, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        // Layered translucent lobes make this look like a soft cloud instead of an emoji/icon.
        for (int halo = 7; halo >= 1; halo--) {
            int a = 9 + (8 - halo) * 5;
            p.setColor(android.graphics.Color.argb(a, 255, 255, 255));
            float grow = halo * 2.8f;
            c.drawOval(new android.graphics.RectF(22-grow, 43-grow*.35f, 158+grow, 88+grow*.35f), p);
            c.drawCircle(65, 52, 27+grow*.25f, p);
            c.drawCircle(92, 37, 34+grow*.22f, p);
            c.drawCircle(124, 53, 25+grow*.24f, p);
        }
        p.setColor(android.graphics.Color.argb(184, 250, 253, 255));
        c.drawOval(new android.graphics.RectF(25, 46, 155, 87), p);
        c.drawCircle(65, 53, 27, p);
        c.drawCircle(92, 39, 34, p);
        c.drawCircle(124, 54, 25, p);
        p.setColor(android.graphics.Color.argb(50, 145, 165, 178));
        c.drawOval(new android.graphics.RectF(39, 76, 145, 90), p);
        return b;
    }

    private String cloudSprites(List<WeatherPoint> weather, double phase) {
        try {
            JSONArray features = new JSONArray();
            for (WeatherPoint p : weather) {
                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !Double.isFinite(p.cloud)) continue;
                if (p.cloud < 25d) continue;
                int count = 1 + (int)Math.floor(Math.min(100d, p.cloud) / 24d);
                count = Math.max(1, Math.min(5, count));
                for (int i = 0; i < count; i++) {
                    long h1 = ((long)p.district.hashCode() * 2654435761L) + i * 1103515245L;
                    long h2 = h1 * 1664525L + 1013904223L;
                    double rx = ((h1 & 0x7fffffffL) % 1000L) / 999.0d;
                    double ry = ((h2 & 0x7fffffffL) % 1000L) / 999.0d;
                    double offset = (((h1 >>> 11) & 2047L) / 2047.0d);
                    double drift = (phase + offset) % 1.0d;
                    // Slow west-to-east drift with a tiny northward component for a web-like living layer.
                    double lo = p.lon + (rx - 0.5d) * 0.72d + (drift - 0.5d) * 0.42d;
                    double la = p.lat + (ry - 0.5d) * 0.46d + (drift - 0.5d) * 0.055d;
                    JSONObject geom = new JSONObject()
                            .put("type", "Point")
                            .put("coordinates", new JSONArray().put(lo).put(la));
                    JSONObject props = new JSONObject()
                            .put("district", p.district)
                            .put("cloud", p.cloud)
                            .put("precipitation", p.precipitation);
                    features.put(new JSONObject().put("type", "Feature").put("geometry", geom).put("properties", props));
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

'''
s = s.replace(anchor, cloud_methods + anchor, 1)

for token in [
    'V0918_WEB_STYLE_CLOUDS',
    'SRC_CLOUD_SPRITES',
    'updateCloudFrames()',
    'cloudSprites(snapshot(), phase)',
    'cloudBitmap()',
    'iconImage(IMG_CLOUD)'
]:
    if token not in s:
        raise SystemExit(f'missing token after patch: {token}')

P.write_text(s, encoding='utf-8')
print('V0918_WEB_STYLE_MOVING_CLOUDS_PATCHED')
