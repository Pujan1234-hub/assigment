from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
OVERLAY = J / "WeatherMapOverlayController.java"
UI = J / "NativeFullActivity.java"
GRADLE = ROOT / "app/build.gradle"

s = OVERLAY.read_text(encoding="utf-8")
u = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

# WEATHER ONLY. Do not touch river/station/map geometry or official feeds.
# The old native overlay hid light rain below 0.10 mm. Use any positive current
# precipitation instead, matching the web behaviour much more closely.
old_ge = "p.precipitation >= 0.10d"
count_ge = s.count(old_ge)
if count_ge < 1:
    raise SystemExit(f"rain >=0.10 rule not found (count={count_ge})")
s = s.replace(old_ge, "p.precipitation > 0.0d")

old_lt = "p.precipitation < 0.10d"
count_lt = s.count(old_lt)
if count_lt < 1:
    raise SystemExit(f"rain <0.10 rule not found (count={count_lt})")
s = s.replace(old_lt, "p.precipitation <= 0.0d")

anchor = "    private void updateRainFrames() {"
if anchor not in s:
    raise SystemExit("updateRainFrames anchor missing")
s = s.replace(anchor, "    // V0912_WEB_NATIVE_RAIN_PARITY_ANY_POSITIVE_PRECIP\n" + anchor, 1)

# If Open-Meteo reports a rain-family WMO weather code while the rounded current
# precipitation value is 0.0, pass a tiny non-zero map-only signal. The displayed
# weather value remains the real Open-Meteo precipitation; only the animation
# eligibility uses this fallback signal.
ui_anchor = "    private String weatherCodeText(int code,double precipitation){"
if ui_anchor not in u:
    raise SystemExit("weatherCodeText anchor missing")
helper = '''    // V0912_RAIN_WMO_CODE_FALLBACK_FOR_NATIVE_MAP\n    private static double nativeRainSignalMm(DistrictWeather d){\n        if(d==null)return 0.0d;\n        if(Double.isFinite(d.precip)&&d.precip>0.0d)return d.precip;\n        int c=d.code;\n        boolean rain=(c>=51&&c<=57)||(c>=61&&c<=67)||(c>=80&&c<=82)||(c>=95&&c<=99);\n        return rain?0.01d:0.0d;\n    }\n'''
u = u.replace(ui_anchor, helper + ui_anchor, 1)

old_ctor = "new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp)"
ctor_count = u.count(old_ctor)
if ctor_count < 1:
    raise SystemExit(f"WeatherPoint constructor call not found (count={ctor_count})")
u = u.replace(old_ctor, "new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,nativeRainSignalMm(d),d.temp)")

# Version only after the verified v0.9.11 patch chain has completed.
if g.count("versionCode 28") != 1:
    raise SystemExit("versionCode 28 missing")
g = g.replace("versionCode 28", "versionCode 29", 1)
if g.count("versionName '0.9.11-river2km-events-language-ninda'") != 1:
    raise SystemExit("v0.9.11 versionName missing")
g = g.replace("versionName '0.9.11-river2km-events-language-ninda'", "versionName '0.9.12-native-rain-parity'", 1)

OVERLAY.write_text(s, encoding="utf-8")
UI.write_text(u, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")

print(f"V0912_NATIVE_RAIN_PARITY_PATCHED thresholds={count_ge}/{count_lt} constructors={ctor_count}")
