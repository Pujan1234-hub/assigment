from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
OVERLAY = J / "WeatherMapOverlayController.java"
UI = J / "NativeFullActivity.java"
GRADLE = ROOT / "app/build.gradle"

s = OVERLAY.read_text(encoding="utf-8")
u = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")


def repl(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)

# WEATHER ONLY. Do not touch river/station/map geometry or official feeds.
s = repl(
    s,
    '        final double lat, lon, cloud, precipitation, temperature;\n        WeatherPoint(String district, double lat, double lon, double cloud, double precipitation, double temperature) {',
    '        final double lat, lon, cloud, precipitation, temperature;\n        final int weatherCode; // V0912_WEB_NATIVE_RAIN_PARITY\n        WeatherPoint(String district, double lat, double lon, double cloud, double precipitation, double temperature, int weatherCode) {',
    "WeatherPoint signature",
)
s = repl(
    s,
    '            this.temperature = temperature;\n        }',
    '            this.temperature = temperature;\n            this.weatherCode = weatherCode;\n        }',
    "WeatherPoint weather code assignment",
)

# Open-Meteo rain-family WMO codes: drizzle 51-57, rain 61-67,
# showers 80-82, thunderstorm 95-99. A positive current precipitation value
# also counts, so light rain below the old 0.10 mm cutoff is no longer hidden.
marker = '    private void updateRainFrames() {'
helper = '''    // V0912_RAIN_SIGNAL_USES_PRECIP_AND_WMO_CODE\n    private static boolean isRainSignal(WeatherPoint p) {\n        if (p == null) return false;\n        if (Double.isFinite(p.precipitation) && p.precipitation > 0.0d) return true;\n        int c = p.weatherCode;\n        return (c >= 51 && c <= 57) || (c >= 61 && c <= 67) ||\n               (c >= 80 && c <= 82) || (c >= 95 && c <= 99);\n    }\n\n'''
if helper.strip() not in s:
    if marker not in s:
        raise SystemExit("updateRainFrames anchor missing")
    s = s.replace(marker, helper + marker, 1)

s = repl(
    s,
    '                if (p != null && Double.isFinite(p.precipitation) && p.precipitation >= 0.10d) { any = true; break; }',
    '                if (isRainSignal(p)) { any = true; break; }',
    "rain any-signal rule",
)

s = repl(
    s,
    '                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !Double.isFinite(p.precipitation)) continue;\n                boolean isHeavy = p.precipitation >= 2.0d;\n                if (p.precipitation < 0.10d || isHeavy != heavy) continue;',
    '                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !isRainSignal(p)) continue;\n                double mm = Double.isFinite(p.precipitation) ? Math.max(0.0d, p.precipitation) : 0.0d;\n                boolean isHeavy = mm >= 2.0d || (p.weatherCode >= 95 && p.weatherCode <= 99);\n                if (isHeavy != heavy) continue;',
    "rain streak eligibility",
)
s = repl(
    s,
    '                int count = heavy ? Math.min(18, 8 + (int)Math.round(Math.min(10d, p.precipitation) * 1.2d))\n                                  : Math.min(10, 4 + (int)Math.round(Math.min(2d, p.precipitation) * 2.0d));',
    '                int count = heavy ? Math.min(18, 8 + (int)Math.round(Math.min(10d, mm) * 1.2d))\n                                  : Math.min(10, 4 + (int)Math.round(Math.min(2d, mm) * 2.0d));',
    "rain streak count",
)
s = repl(
    s,
    '                    JSONObject props = new JSONObject().put("district", p.district).put("precipitation", p.precipitation);',
    '                    JSONObject props = new JSONObject().put("district", p.district).put("precipitation", p.precipitation).put("weather_code", p.weatherCode);',
    "rain props",
)
s = repl(
    s,
    '                    if (rainOnly) use = Double.isFinite(p.precipitation) && p.precipitation >= 0.10d;',
    '                    if (rainOnly) use = isRainSignal(p);',
    "rain polygon eligibility",
)
s = repl(
    s,
    '                    cp.put("temperature", p.temperature);',
    '                    cp.put("temperature", p.temperature);\n                    cp.put("weather_code", p.weatherCode);',
    "polygon weather code",
)

# District weather already receives Open-Meteo weather_code; pass it into the native map overlay.
u = repl(
    u,
    'new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp)',
    'new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp,d.code)',
    "NativeFullActivity overlay weather code",
)

# Version only after the verified v0.9.11 patch chain has completed.
g = repl(g, 'versionCode 28', 'versionCode 29', "versionCode")
g = repl(
    g,
    "versionName '0.9.11-river2km-events-language-ninda'",
    "versionName '0.9.12-native-rain-parity'",
    "versionName",
)

OVERLAY.write_text(s, encoding="utf-8")
UI.write_text(u, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")

print("V0912_NATIVE_RAIN_PARITY_PATCHED")
