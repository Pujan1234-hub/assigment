from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
OVERLAY = J / "WeatherMapOverlayController.java"
UI = J / "NativeFullActivity.java"
GRADLE = ROOT / "app/build.gradle"

s = OVERLAY.read_text(encoding="utf-8")
u = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

# WEATHER OVERLAY ONLY. River geometry, BIPAD/DHM feeds, station markers,
# alert matching and native map implementation are intentionally untouched.
# v0.9.11 already passes current Open-Meteo WMO weatherCode into WeatherPoint.
if "final int weatherCode;" not in s:
    raise SystemExit("v0.9.11 storm weatherCode support missing")
if "new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp,d.code)" not in u:
    raise SystemExit("v0.9.11 UI weatherCode pass-through missing")

# Add one shared rain signal rule: any positive current precipitation OR an
# Open-Meteo rain-family WMO code (drizzle/rain/showers/thunderstorm).
anchor = "    private void updateRainFrames() {"
if anchor not in s:
    raise SystemExit("updateRainFrames anchor missing")
helper = '''    // V0912_WEB_NATIVE_RAIN_PARITY\n    private static boolean isRainSignal(WeatherPoint p) {\n        if (p == null) return false;\n        if (Double.isFinite(p.precipitation) && p.precipitation > 0.0d) return true;\n        int c = p.weatherCode;\n        return (c >= 51 && c <= 57) || (c >= 61 && c <= 67) ||\n               (c >= 80 && c <= 82) || (c >= 95 && c <= 99);\n    }\n\n'''
s = s.replace(anchor, helper + anchor, 1)

old_any = "                if (p != null && Double.isFinite(p.precipitation) && p.precipitation >= 0.10d) { any = true; break; }"
if s.count(old_any) != 1:
    raise SystemExit(f"old rain any rule expected 1, got {s.count(old_any)}")
s = s.replace(old_any, "                if (isRainSignal(p)) { any = true; break; }", 1)

old_streak = '''                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !Double.isFinite(p.precipitation)) continue;\n                boolean isHeavy = p.precipitation >= 2.0d;\n                if (p.precipitation < 0.10d || isHeavy != heavy) continue;'''
new_streak = '''                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !isRainSignal(p)) continue;\n                double mm = Double.isFinite(p.precipitation) ? Math.max(0.0d, p.precipitation) : 0.0d;\n                boolean isHeavy = mm >= 2.0d;\n                if (isHeavy != heavy) continue;'''
if s.count(old_streak) != 1:
    raise SystemExit(f"old rain streak rule expected 1, got {s.count(old_streak)}")
s = s.replace(old_streak, new_streak, 1)

old_count = '''                int count = heavy ? Math.min(18, 8 + (int)Math.round(Math.min(10d, p.precipitation) * 1.2d))\n                                  : Math.min(10, 4 + (int)Math.round(Math.min(2d, p.precipitation) * 2.0d));'''
new_count = '''                int count = heavy ? Math.min(18, 8 + (int)Math.round(Math.min(10d, mm) * 1.2d))\n                                  : Math.min(10, 4 + (int)Math.round(Math.min(2d, mm) * 2.0d));'''
if s.count(old_count) != 1:
    raise SystemExit(f"old rain streak count expected 1, got {s.count(old_count)}")
s = s.replace(old_count, new_count, 1)

old_polygon = "                    if (rainOnly) use = Double.isFinite(p.precipitation) && p.precipitation >= 0.10d;"
if s.count(old_polygon) != 1:
    raise SystemExit(f"old rain polygon rule expected 1, got {s.count(old_polygon)}")
s = s.replace(old_polygon, "                    if (rainOnly) use = isRainSignal(p);", 1)

# Version only after the verified v0.9.11 patch chain has completed.
if g.count("versionCode 28") != 1:
    raise SystemExit("versionCode 28 missing")
g = g.replace("versionCode 28", "versionCode 29", 1)
if g.count("versionName '0.9.11-river2km-events-language-ninda'") != 1:
    raise SystemExit("v0.9.11 versionName missing")
g = g.replace("versionName '0.9.11-river2km-events-language-ninda'", "versionName '0.9.12-native-rain-parity'", 1)

OVERLAY.write_text(s, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("V0912_NATIVE_RAIN_PARITY_PATCHED")
