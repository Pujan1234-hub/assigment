from pathlib import Path
import re

P = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/WeatherMapOverlayController.java')
s = P.read_text(encoding='utf-8')

if 'V0918_WEB_STYLE_CLOUDS' in s:
    print('V0918_WEB_STYLE_MOVING_CLOUDS_ALREADY_PATCHED')
    raise SystemExit(0)

def sub_once(pattern, repl, label, flags=0):
    global s
    s2, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, got {n}')
    s = s2

# Constants are inserted before the timing constants so this stays compatible with
# the final v0.9.18 overlay even when earlier patch steps rename weather sources.
sub_once(
    r'(?m)^(\s*private static final long PULSE_MS\s*=.*)$',
    '    // V0918_WEB_STYLE_CLOUDS — visual-only moving cloud sprites driven by current cloud cover.\n'
    '    private static final String SRC_CLOUD_SPRITES = "fs-weather-cloud-sprites";\n'
    '    private static final String IMG_CLOUD = "fs-weather-cloud-image";\n'
    '    private static final String LYR_CLOUD_SPRITES = "fs-weather-cloud-sprites-layer";\n'
    r'\1',
    'timing anchor')

sub_once(
    r'(?m)^(\s*private static final long RAIN_FRAME_MS\s*=\s*[^;]+;)$',
    r'\1\n    private static final long CLOUD_FRAME_MS = 420L;',
    'rain frame anchor')

sub_once(
    r'(?m)^(\s*private long rainStartedAt\s*=\s*System\.currentTimeMillis\(\);)$',
    r'\1\n    private long cloudStartedAt = System.currentTimeMillis();',
    'rain start anchor')

# Wire cloud animation into the existing animation lifecycle.
sub_once(
    r'(\s*main\.removeCallbacks\(rainTick\);)',
    r'\1\n        main.removeCallbacks(cloudTick);',
    'remove callback anchor')
sub_once(
    r'(\s*main\.post\(rainTick\);)',
    r'\1\n        main.post(cloudTick);',
    'post callback anchor')

rain_block = re.compile(
    r'(\n\s*private final Runnable rainTick = new Runnable\(\) \{.*?\n\s*\};)',
    re.S)
m = rain_block.search(s)
if not m:
    raise SystemExit('rain runnable anchor missing')
cloud_runnable = r'''

    // Smooth native cloud drift. This does not alter river/station geometry or risk logic.
    private final Runnable cloudTick = new Runnable() {
        @Override public void run() {
            if (destroyed) return;
            if (enabled) updateCloudFrames();
            main.postDelayed(this, CLOUD_FRAME_MS);
        }
    };'''
s = s[:m.end()] + cloud_runnable + s[m.end():]

# Ensure layer once during the normal refresh setup. Anchor on the last rain-line
# setup if present; otherwise insert immediately before the district enabled check.
needle = 'if (!enabled || districtGeometry == null)'
idx = s.find(needle)
if idx < 0:
    raise SystemExit('refresh enabled anchor missing')
line_start = s.rfind('\n', 0, idx) + 1
indent = s[line_start:idx]
s = s[:line_start] + indent + 'ensureCloudSprites(style);\n' + s[line_start:]

# Clear the moving cloud source when the weather layer is switched off.
clear_marker = 'private void clearAll()'
ci = s.find(clear_marker)
if ci < 0:
    raise SystemExit('clearAll missing')
ci_end = s.find('\n    }', ci)
if ci_end < 0:
    raise SystemExit('clearAll end missing')
s = s[:ci_end] + '\n        setGeo(style, SRC_CLOUD_SPRITES, EMPTY);' + s[ci_end:]

anchor = '    private static void ensureFill(Style style, String sourceId, String layerId, String color, float opacity) {'
if anchor not in s:
    raise SystemExit('ensureFill anchor missing')

cloud_methods = r'''    private void updateCloudFrames() {
        if (!enabled || style == null || !style.isFullyLoaded()) return;
        try {
            if (style.getSource(SRC_CLOUD_SPRITES) == null || style.getLayer(LYR_CLOUD_SPRITES) == null) return;
            double phase = ((System.currentTimeMillis() - cloudStartedAt) % 18000L) / 18000.0d;
            setGeo(style, SRC_CLOUD_SPRITES, cloudSprites(snapshot(), phase));
        } catch (Exception ignored) {}
    }

    private static void ensureCloudSprites(Style style) {
        if (style.getSource(SRC_CLOUD_SPRITES) == null) {
            style.addSource(new GeoJsonSource(SRC_CLOUD_SPRITES, EMPTY));
        }
        if (style.getLayer(LYR_CLOUD_SPRITES) == null) {
            try { style.addImage(IMG_CLOUD, cloudBitmap()); } catch (Exception ignored) {}
            org.maplibre.android.style.layers.SymbolLayer layer =
                    new org.maplibre.android.style.layers.SymbolLayer(LYR_CLOUD_SPRITES, SRC_CLOUD_SPRITES)
                    .withProperties(
                            org.maplibre.android.style.layers.PropertyFactory.iconImage(IMG_CLOUD),
                            org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap(true),
                            org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement(true),
                            org.maplibre.android.style.layers.PropertyFactory.iconOpacity(0.78f),
                            org.maplibre.android.style.layers.PropertyFactory.iconSize(0.68f)
                    );
            // Weather visuals stay under official rivers/stations.
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");
            else style.addLayer(layer);
        }
    }

    private static android.graphics.Bitmap cloudBitmap() {
        final int w = 180, h = 108;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(w, h, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        // Several translucent lobes create a soft cloud instead of an emoji/icon.
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
                // More current cloud cover = more cloud sprites, while remaining lightweight.
                int count = 1 + (int)Math.floor(Math.min(100d, p.cloud) / 24d);
                count = Math.max(1, Math.min(5, count));
                for (int i = 0; i < count; i++) {
                    long h1 = ((long)p.district.hashCode() * 2654435761L) + i * 1103515245L;
                    long h2 = h1 * 1664525L + 1013904223L;
                    double rx = ((h1 & 0x7fffffffL) % 1000L) / 999.0d;
                    double ry = ((h2 & 0x7fffffffL) % 1000L) / 999.0d;
                    double offset = (((h1 >>> 11) & 2047L) / 2047.0d);
                    double drift = (phase + offset) % 1.0d;
                    // Slow west-to-east visual drift. Weather values themselves remain untouched.
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
