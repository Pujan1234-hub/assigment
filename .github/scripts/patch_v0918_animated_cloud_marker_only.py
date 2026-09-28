from pathlib import Path
import re

P = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/WeatherMapOverlayController.java')
s = P.read_text(encoding='utf-8')

if 'V0918_ANIMATED_CLOUD_MARKER_ONLY' in s:
    print('V0918_ANIMATED_CLOUD_MARKER_ONLY_ALREADY_PATCHED')
    raise SystemExit(0)

def sub_once(pattern, repl, label, flags=0):
    global s
    s2, n = re.subn(pattern, repl, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, got {n}')
    s = s2

# IMPORTANT: animate the existing in-map weather marker only.
# Do not add roaming/random cloud overlays or touch river/station/risk logic.
sub_once(
    r'(?m)^(\s*private static final long RAIN_FRAME_MS\s*=\s*[^;]+;)$',
    r'\1\n    private static final long CLOUD_MARKER_FRAME_MS = 650L; // V0918_ANIMATED_CLOUD_MARKER_ONLY',
    'marker timing anchor')

sub_once(
    r'(?m)^(\s*private boolean pulseHigh\s*=\s*false;)$',
    r'\1\n    private boolean cloudMarkerHigh = false;',
    'marker state anchor')

# Hook the marker animation into the existing weather animation lifecycle.
sub_once(
    r'(\s*main\.removeCallbacks\(rainTick\);)',
    r'\1\n        main.removeCallbacks(cloudMarkerTick);',
    'remove marker callback')
sub_once(
    r'(\s*main\.post\(rainTick\);)',
    r'\1\n        main.post(cloudMarkerTick);',
    'post marker callback')

rain_block = re.compile(r'(\n\s*private final Runnable rainTick = new Runnable\(\) \{.*?\n\s*\};)', re.S)
m = rain_block.search(s)
if not m:
    raise SystemExit('rain runnable anchor missing')
marker_run = r'''

    // Gentle breathing motion on the CURRENT cloud weather marker only.
    private final Runnable cloudMarkerTick = new Runnable() {
        @Override public void run() {
            if (destroyed) return;
            if (enabled) {
                cloudMarkerHigh = !cloudMarkerHigh;
                applyCloudMarkerAnimation();
            }
            main.postDelayed(this, CLOUD_MARKER_FRAME_MS);
        }
    };'''
s = s[:m.end()] + marker_run + s[m.end():]

# Replace only the weather icon bitmap renderer. The cloud/rain/thunder markers become
# unmistakable cloud shapes instead of looking like a gray dash/minus inside a circle.
pat = re.compile(r'    private static android\.graphics\.Bitmap weatherEmojiBitmap\(String emoji\) \{.*?\n    \}\n', re.S)
m = pat.search(s)
if not m:
    raise SystemExit('weatherEmojiBitmap method missing')
new_bitmap = r'''    private static android.graphics.Bitmap weatherEmojiBitmap(String emoji) {
        final int w = 144, h = 104;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(w, h, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);

        boolean sun = emoji != null && emoji.contains("☀");
        boolean rain = emoji != null && emoji.contains("🌧");
        boolean thunder = emoji != null && (emoji.contains("⛈") || emoji.contains("⚡"));
        boolean cloud = !sun;

        if (sun) {
            // Clear marker remains a clean sun marker.
            p.setStyle(android.graphics.Paint.Style.FILL);
            p.setColor(android.graphics.Color.argb(222, 255, 255, 255));
            c.drawCircle(72f, 52f, 43f, p);
            p.setColor(android.graphics.Color.rgb(255, 183, 0));
            c.drawCircle(72f, 52f, 20f, p);
            p.setStyle(android.graphics.Paint.Style.STROKE);
            p.setStrokeWidth(5f);
            for (int i=0;i<8;i++) {
                double a=Math.PI*2d*i/8d;
                c.drawLine((float)(72+29*Math.cos(a)),(float)(52+29*Math.sin(a)),
                           (float)(72+39*Math.cos(a)),(float)(52+39*Math.sin(a)),p);
            }
        }

        if (cloud) {
            // Shadow gives the marker depth on satellite terrain.
            p.setStyle(android.graphics.Paint.Style.FILL);
            p.setColor(android.graphics.Color.argb(72, 25, 53, 70));
            c.drawOval(new android.graphics.RectF(29f, 70f, 119f, 91f), p);

            // Main cloud: large lobes + body, no circular badge/background.
            p.setColor(android.graphics.Color.rgb(239, 246, 250));
            c.drawCircle(52f, 59f, 25f, p);
            c.drawCircle(75f, 43f, 32f, p);
            c.drawCircle(103f, 61f, 23f, p);
            c.drawRoundRect(new android.graphics.RectF(31f, 57f, 123f, 82f), 14f, 14f, p);

            // Highlight + soft blue-gray underside so it reads as a real cloud.
            p.setColor(android.graphics.Color.argb(205, 255, 255, 255));
            c.drawOval(new android.graphics.RectF(48f, 34f, 94f, 56f), p);
            p.setColor(android.graphics.Color.rgb(178, 198, 211));
            c.drawRoundRect(new android.graphics.RectF(42f, 72f, 114f, 84f), 8f, 8f, p);

            if (rain) {
                p.setStyle(android.graphics.Paint.Style.STROKE);
                p.setStrokeCap(android.graphics.Paint.Cap.ROUND);
                p.setStrokeWidth(5f);
                p.setColor(android.graphics.Color.rgb(43, 158, 226));
                c.drawLine(52f, 88f, 47f, 99f, p);
                c.drawLine(75f, 88f, 70f, 101f, p);
                c.drawLine(99f, 88f, 94f, 99f, p);
            }
            if (thunder) {
                p.setStyle(android.graphics.Paint.Style.FILL);
                p.setColor(android.graphics.Color.rgb(255, 188, 0));
                android.graphics.Path z = new android.graphics.Path();
                z.moveTo(80f, 78f); z.lineTo(66f, 96f); z.lineTo(76f, 95f);
                z.lineTo(69f, 104f); z.lineTo(94f, 83f); z.lineTo(83f, 85f); z.close();
                c.drawPath(z, p);
            }
        }
        return b;
    }
'''
s = s[:m.start()] + new_bitmap + s[m.end():]

# Make the cloud marker a little larger than the other weather markers so it visibly
# reads as a cloud on a busy satellite map. No new source/layer is created.
old_size = 'org.maplibre.android.style.layers.PropertyFactory.iconSize(0.62f),'
if old_size not in s:
    raise SystemExit('weather icon size anchor missing')
s = s.replace(old_size, 'org.maplibre.android.style.layers.PropertyFactory.iconSize("☁️".equals(emoji) ? 0.82f : 0.62f),', 1)

anchor = '    private static void ensureFill(Style style, String sourceId, String layerId, String color, float opacity) {'
if anchor not in s:
    raise SystemExit('ensureFill anchor missing')
anim_method = r'''    private void applyCloudMarkerAnimation() {
        if (style == null || !style.isFullyLoaded()) return;
        try {
            if (style.getLayer(LYR_ICON_CLOUD) != null) {
                style.getLayer(LYR_ICON_CLOUD).setProperties(
                        org.maplibre.android.style.layers.PropertyFactory.iconSize(cloudMarkerHigh ? 0.88f : 0.80f),
                        org.maplibre.android.style.layers.PropertyFactory.iconOpacity(cloudMarkerHigh ? 1.0f : 0.86f)
                );
            }
        } catch (Exception ignored) {}
    }

'''
s = s.replace(anchor, anim_method + anchor, 1)

# Apply one frame immediately during normal refresh so the marker never starts static.
needle = '                updateRainFrames();'
if needle not in s:
    raise SystemExit('refresh animation anchor missing')
s = s.replace(needle, needle + '\n                applyCloudMarkerAnimation();', 1)

# Guards: this patch must NOT contain the previous roaming/random cloud overlay.
for forbidden in ['SRC_CLOUD_SPRITES', 'LYR_CLOUD_SPRITES', 'cloudSprites(snapshot()', 'updateCloudFrames()']:
    if forbidden in s:
        raise SystemExit('forbidden roaming cloud overlay present: ' + forbidden)
for required in ['V0918_ANIMATED_CLOUD_MARKER_ONLY','cloudMarkerTick','applyCloudMarkerAnimation()','LYR_ICON_CLOUD','weatherEmojiBitmap(String emoji)']:
    if required not in s:
        raise SystemExit('required marker patch missing: ' + required)

P.write_text(s, encoding='utf-8')
print('V0918_ANIMATED_CLOUD_MARKER_ONLY_OK')
