from pathlib import Path
import re

ROOT=Path('floodsafe-android-app')
J=ROOT/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
UI=J/'NativeFullActivity.java'
OVERLAY=J/'WeatherMapOverlayController.java'
VERIFIER=J/'DhmCurrentRainVerifier.java'
GRADLE=ROOT/'app/build.gradle'

u=UI.read_text(encoding='utf-8')
w=OVERLAY.read_text(encoding='utf-8')
v=VERIFIER.read_text(encoding='utf-8')
g=GRADLE.read_text(encoding='utf-8')

def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    return text.replace(old,new,1)

# ---- Native current-location weather: route through the same PJBUILTS weather proxy used by web. ----
old_local='String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);'
new_local='String u=String.format(Locale.US,"https://pjbuilts.com/api/floodsafe-weather?latitude=%.6f&longitude=%.6f",a,o); // V0917_NATIVE_WEATHER_PROXY'
u=once(u,old_local,new_local,'local weather proxy')

# Proxy intentionally returns current weather only, so do not make current card fail/feel stale because hourly forecast is absent.
u=u.replace('String timing=rainTiming(j);', 'String timing=pr>0d?t("🌧️ अहिले वर्षा भइरहेको छ","🌧️ Rain is being measured now"):t("☁️ अहिलेको measurement मा वर्षा छैन","☁️ No current rain in this measurement");', 1)

# ---- 77 district current weather: same reliable proxy, comma-separated coordinates supported. ----
old_district='String u="https://api.open-meteo.com/v1/forecast?latitude="+la+"&longitude="+lo+"&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&timezone=Asia%2FKathmandu&forecast_days=1";'
new_district='String u="https://pjbuilts.com/api/floodsafe-weather?latitude="+la+"&longitude="+lo; // V0917_DISTRICT_WEATHER_PROXY'
u=once(u,old_district,new_district,'district weather proxy')

# ---- SATHI district weather: use proxy too, otherwise chat can fail while the web succeeds. ----
old_sathi='String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.5f&longitude=%.5f&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,weather_code,wind_speed_10m&timezone=Asia%%2FKathmandu",a,o);'
new_sathi='String u=String.format(Locale.US,"https://pjbuilts.com/api/floodsafe-weather?latitude=%.5f&longitude=%.5f",a,o); // V0917_SATHI_WEATHER_PROXY'
u=once(u,old_sathi,new_sathi,'SATHI weather proxy')

# ---- Current rain verifier at DHM gauge coordinates: proxy, never 1h accumulation. ----
old_verifier='String u = "https://api.open-meteo.com/v1/forecast?latitude=" + lat\n                + "&longitude=" + lon\n                + "&current=precipitation,weather_code&timezone=Asia%2FKathmandu";'
new_verifier='String u = "https://pjbuilts.com/api/floodsafe-weather?latitude=" + lat\n                + "&longitude=" + lon; // V0917_CURRENT_RAIN_PROXY'
v=once(v,old_verifier,new_verifier,'current rain proxy')

# ---- Native weather icons: never depend on Android emoji-font rendering. ----
# Force visibility while keeping official stations above the icon layer where present.
w=once(w,
'''                    org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap(false),
                    org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement(false)
            );
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerBelow(layer, "fs-rivers-layer");''',
'''                    org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap(true),
                    org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement(true)
            );
            if (style.getLayer("fs-rivers-layer") != null) style.addLayerAbove(layer, "fs-rivers-layer");''',
'icon visibility/layer order')

pat=re.compile(r'''    private static android\.graphics\.Bitmap weatherEmojiBitmap\(String emoji\) \{.*?\n    \}\n''',re.S)
m=pat.search(w)
if not m: raise SystemExit('weatherEmojiBitmap method missing')
replacement=r'''    // V0917_NATIVE_DRAWN_WEATHER_ICONS — avoids device emoji-font dependency.
    private static android.graphics.Bitmap weatherEmojiBitmap(String emoji) {
        final int size = 92;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(size, size, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        android.graphics.Paint bg = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        bg.setColor(android.graphics.Color.argb(220,255,255,255));
        c.drawCircle(46f,46f,40f,bg);

        android.graphics.Paint p = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        boolean sun = emoji != null && emoji.contains("☀");
        boolean rain = emoji != null && emoji.contains("🌧");
        boolean thunder = emoji != null && (emoji.contains("⛈") || emoji.contains("⚡"));
        boolean cloud = !sun;

        if (sun) {
            p.setColor(android.graphics.Color.rgb(255,183,0)); p.setStrokeWidth(4.5f); p.setStyle(android.graphics.Paint.Style.STROKE);
            for(int i=0;i<8;i++){double a=Math.PI*2d*i/8d;float x1=(float)(46+24*Math.cos(a)),y1=(float)(46+24*Math.sin(a)),x2=(float)(46+33*Math.cos(a)),y2=(float)(46+33*Math.sin(a));c.drawLine(x1,y1,x2,y2,p);}
            p.setStyle(android.graphics.Paint.Style.FILL); c.drawCircle(46f,46f,16f,p);
        }
        if (cloud) {
            p.setStyle(android.graphics.Paint.Style.FILL); p.setColor(android.graphics.Color.rgb(222,230,236));
            c.drawCircle(34f,45f,13f,p); c.drawCircle(48f,38f,17f,p); c.drawCircle(62f,46f,13f,p);
            c.drawRoundRect(new android.graphics.RectF(25f,44f,69f,59f),9f,9f,p);
            p.setStyle(android.graphics.Paint.Style.STROKE); p.setStrokeWidth(2.2f); p.setColor(android.graphics.Color.rgb(135,151,165));
            c.drawRoundRect(new android.graphics.RectF(25f,44f,69f,59f),9f,9f,p);
        }
        if (rain) {
            p.setStyle(android.graphics.Paint.Style.STROKE); p.setStrokeWidth(4.2f); p.setStrokeCap(android.graphics.Paint.Cap.ROUND); p.setColor(android.graphics.Color.rgb(28,154,230));
            c.drawLine(34f,65f,30f,74f,p); c.drawLine(48f,65f,44f,76f,p); c.drawLine(62f,65f,58f,74f,p);
        }
        if (thunder) {
            android.graphics.Path path = new android.graphics.Path();
            path.moveTo(50f,58f); path.lineTo(41f,72f); path.lineTo(49f,71f); path.lineTo(44f,82f); path.lineTo(61f,65f); path.lineTo(52f,66f); path.close();
            p.setStyle(android.graphics.Paint.Style.FILL); p.setColor(android.graphics.Color.rgb(255,183,0)); c.drawPath(path,p);
        }
        return b;
    }
'''
w=w[:m.start()]+replacement+w[m.end():]

# Version bump from verified v0.9.16 chain.
g=once(g,'versionCode 33','versionCode 34','versionCode')
g=once(g,"versionName '0.9.16-sathi-knowledge'","versionName '0.9.17-native-weather-runtime'",'versionName')

for token in ['V0917_NATIVE_WEATHER_PROXY','V0917_DISTRICT_WEATHER_PROXY','V0917_SATHI_WEATHER_PROXY']:
    assert token in u,token
assert 'V0917_CURRENT_RAIN_PROXY' in v
assert 'V0917_NATIVE_DRAWN_WEATHER_ICONS' in w
assert 'iconAllowOverlap(true)' in w
assert 'addLayerAbove(layer, "fs-rivers-layer")' in w
assert 'api.open-meteo.com/v1/forecast' not in u
assert 'api.open-meteo.com/v1/forecast' not in v
assert 'versionCode 34' in g
assert "versionName '0.9.17-native-weather-runtime'" in g

UI.write_text(u,encoding='utf-8')
OVERLAY.write_text(w,encoding='utf-8')
VERIFIER.write_text(v,encoding='utf-8')
GRADLE.write_text(g,encoding='utf-8')
print('V0917_NATIVE_WEATHER_RUNTIME_PATCHED')
