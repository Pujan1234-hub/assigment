from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
DHM = J / "DhmRainMirror.java"
OVERLAY = J / "WeatherMapOverlayController.java"
GRADLE = ROOT / "app/build.gradle"

d = DHM.read_text(encoding="utf-8")
w = OVERLAY.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")


def repl(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)

# ---- DHM: expose only fresh official last-hour rainfall points to the weather overlay. ----
d = repl(
    d,
    'import java.util.Locale;\nimport java.util.Map;',
    'import java.util.ArrayList;\nimport java.util.List;\nimport java.util.Locale;\nimport java.util.Map;',
    'DHM list imports',
)

anchor = '    private static String read(HttpURLConnection c) throws Exception {'
if anchor not in d:
    raise SystemExit('DHM read anchor missing')

dhm_api = r'''    /**
     * V0913_DHM_FRESH_RAIN_POINTS
     * Fresh official rainfall observations for native map visualization only.
     * A point is returned only while the DHM mirror cache itself is fresh and
     * the official 1-hour accumulation is positive. River warning logic does
     * not use this method.
     */
    static List<RainPoint> freshRainPoints() {
        List<RainPoint> out = new ArrayList<>();
        long now = System.currentTimeMillis();
        if (ROWS.isEmpty() || savedAt <= 0L || now - savedAt > DISPLAY_FRESH_MS) return out;
        for (RainRow row : ROWS.values()) {
            if (row == null || !Double.isFinite(row.lat) || !Double.isFinite(row.lon)) continue;
            double h1 = Double.isFinite(row.h1) ? Math.max(0d, row.h1) : Double.NaN;
            if (!Double.isFinite(h1) || h1 <= 0d) continue;
            out.add(new RainPoint(row.name, row.district, row.lat, row.lon, h1,
                    row.h3, row.h24, row.status, updated, savedAt));
        }
        return out;
    }

    static final class RainPoint {
        final String name, district, status, officialUpdated;
        final double lat, lon, h1, h3, h24;
        final long mirroredAt;
        RainPoint(String name, String district, double lat, double lon, double h1,
                  double h3, double h24, String status, String officialUpdated, long mirroredAt) {
            this.name = name == null ? "" : name;
            this.district = district == null ? "" : district;
            this.lat = lat;
            this.lon = lon;
            this.h1 = h1;
            this.h3 = h3;
            this.h24 = h24;
            this.status = status == null ? "" : status;
            this.officialUpdated = officialUpdated == null ? "" : officialUpdated;
            this.mirroredAt = mirroredAt;
        }
    }

'''
d = d.replace(anchor, dhm_api + anchor, 1)

# ---- Weather overlay: preserve existing Open-Meteo layers and add local DHM rain streaks. ----
w = repl(
    w,
    '    private static final String SRC_LIGHTNING = "fs-weather-lightning-current";',
    '    private static final String SRC_LIGHTNING = "fs-weather-lightning-current";\n    private static final String SRC_DHM_RAIN_LIGHT = "fs-dhm-rain-streak-light";\n    private static final String SRC_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy";',
    'DHM source constants',
)
w = repl(
    w,
    '    private static final String LYR_LIGHTNING = "fs-weather-lightning-current-layer";',
    '    private static final String LYR_LIGHTNING = "fs-weather-lightning-current-layer";\n    private static final String LYR_DHM_RAIN_LIGHT = "fs-dhm-rain-streak-light-layer";\n    private static final String LYR_DHM_RAIN_HEAVY = "fs-dhm-rain-streak-heavy-layer";',
    'DHM layer constants',
)

w = repl(
    w,
    '                ensureRainLine(style, SRC_LIGHTNING, LYR_LIGHTNING, "#fff3a6", 2.6f, 0.96f);',
    '                ensureRainLine(style, SRC_LIGHTNING, LYR_LIGHTNING, "#fff3a6", 2.6f, 0.96f);\n                ensureRainLine(style, SRC_DHM_RAIN_LIGHT, LYR_DHM_RAIN_LIGHT, "#68d2ff", 1.55f, 0.72f);\n                ensureRainLine(style, SRC_DHM_RAIN_HEAVY, LYR_DHM_RAIN_HEAVY, "#e8fbff", 2.45f, 0.90f);',
    'install DHM rain layers',
)

w = repl(
    w,
    '        setGeo(style, SRC_LIGHTNING, EMPTY);',
    '        setGeo(style, SRC_LIGHTNING, EMPTY);\n        setGeo(style, SRC_DHM_RAIN_LIGHT, EMPTY);\n        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);',
    'clear DHM rain layers',
)

old_frame = '''            List<WeatherPoint> snapshot = snapshot();
            boolean any = false;
            for (WeatherPoint p : snapshot) {
                if (isRainSignal(p)) { any = true; break; }
            }
            if (!any) {
                setGeo(style, SRC_RAIN_STREAK_LIGHT, EMPTY);
                setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);
                return;
            }
            double phase = ((System.currentTimeMillis() - rainStartedAt) % 1600L) / 1600.0;
            setGeo(style, SRC_RAIN_STREAK_LIGHT, rainStreaks(snapshot, false, phase));
            setGeo(style, SRC_RAIN_STREAK_HEAVY, rainStreaks(snapshot, true, phase));
            setGeo(style, SRC_LIGHTNING, lightningBolts(snapshot));'''
new_frame = '''            List<WeatherPoint> snapshot = snapshot();
            List<DhmRainMirror.RainPoint> dhm = DhmRainMirror.freshRainPoints(); // V0913_DHM_NATIVE_RAIN_OVERLAY
            boolean anyModel = false;
            for (WeatherPoint p : snapshot) {
                if (isRainSignal(p)) { anyModel = true; break; }
            }
            boolean anyDhm = dhm != null && !dhm.isEmpty();
            if (!anyModel && !anyDhm) {
                setGeo(style, SRC_RAIN_STREAK_LIGHT, EMPTY);
                setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);
                setGeo(style, SRC_DHM_RAIN_LIGHT, EMPTY);
                setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);
                setGeo(style, SRC_LIGHTNING, EMPTY);
                return;
            }
            double phase = ((System.currentTimeMillis() - rainStartedAt) % 1600L) / 1600.0;
            if (anyModel) {
                setGeo(style, SRC_RAIN_STREAK_LIGHT, rainStreaks(snapshot, false, phase));
                setGeo(style, SRC_RAIN_STREAK_HEAVY, rainStreaks(snapshot, true, phase));
                setGeo(style, SRC_LIGHTNING, lightningBolts(snapshot));
            } else {
                setGeo(style, SRC_RAIN_STREAK_LIGHT, EMPTY);
                setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);
                setGeo(style, SRC_LIGHTNING, EMPTY);
            }
            setGeo(style, SRC_DHM_RAIN_LIGHT, dhmRainStreaks(dhm, false, phase));
            setGeo(style, SRC_DHM_RAIN_HEAVY, dhmRainStreaks(dhm, true, phase));'''
w = repl(w, old_frame, new_frame, 'combined Open-Meteo + DHM rain frame')

anchor2 = '    private String stormPolygons(List<WeatherPoint> weather) {'
if anchor2 not in w:
    raise SystemExit('stormPolygons anchor missing')

dhm_streak_method = r'''    /** V0913_DHM_STATION_LOCAL_RAIN_FIELD — local animation around fresh official DHM rainfall gauges. */
    private String dhmRainStreaks(List<DhmRainMirror.RainPoint> rain, boolean heavy, double phase) {
        try {
            JSONArray features = new JSONArray();
            if (rain == null) return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
            for (DhmRainMirror.RainPoint p : rain) {
                if (p == null || !Double.isFinite(p.lat) || !Double.isFinite(p.lon) || !Double.isFinite(p.h1) || p.h1 <= 0d) continue;
                boolean isHeavy = p.h1 >= 5.0d;
                if (isHeavy != heavy) continue;
                int count = heavy ? Math.min(24, 12 + (int)Math.round(Math.min(20d, p.h1) * 0.6d))
                                  : Math.min(14, 6 + (int)Math.round(Math.min(5d, p.h1) * 1.6d));
                double spanLat = heavy ? 0.16d : 0.12d;
                double spanLon = heavy ? 0.22d : 0.17d;
                String seed = (p.name == null ? "" : p.name) + "|" + (p.district == null ? "" : p.district);
                for (int i = 0; i < count; i++) {
                    long h1 = (long)seed.hashCode() * 1103515245L + i * 2654435761L;
                    long h2 = h1 * 1664525L + 1013904223L;
                    double rx = ((h1 & 0x7fffffffL) % 1000L) / 999.0d;
                    double ry = ((h2 & 0x7fffffffL) % 1000L) / 999.0d;
                    double offset = (((h1 >>> 10) & 1023L) / 1023.0d);
                    double fall = (phase + offset) % 1.0d;
                    double lo = p.lon + (rx - 0.5d) * spanLon + fall * (heavy ? 0.028d : 0.018d);
                    double la = p.lat + (ry - 0.5d) * spanLat + spanLat * 0.45d - fall * spanLat * 0.92d;
                    double len = heavy ? 0.040d : 0.026d;
                    JSONArray coords = new JSONArray()
                            .put(new JSONArray().put(lo).put(la))
                            .put(new JSONArray().put(lo + (heavy ? 0.010d : 0.006d)).put(la - len));
                    JSONObject geom = new JSONObject().put("type", "LineString").put("coordinates", coords);
                    JSONObject props = new JSONObject()
                            .put("source", "DHM")
                            .put("station", p.name)
                            .put("district", p.district)
                            .put("rain_1h_mm", p.h1);
                    features.put(new JSONObject().put("type", "Feature").put("geometry", geom).put("properties", props));
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        } catch (Exception e) {
            return EMPTY;
        }
    }

'''
w = w.replace(anchor2, dhm_streak_method + anchor2, 1)

# Version bump after v0.9.12 patch chain.
g = repl(g, 'versionCode 29', 'versionCode 30', 'versionCode')
g = repl(g, "versionName '0.9.12-native-rain-parity'", "versionName '0.9.13-dhm-rain-overlay'", 'versionName')

assert 'V0913_DHM_FRESH_RAIN_POINTS' in d
assert 'V0913_DHM_NATIVE_RAIN_OVERLAY' in w
assert 'V0913_DHM_STATION_LOCAL_RAIN_FIELD' in w
assert 'versionCode 30' in g
assert "versionName '0.9.13-dhm-rain-overlay'" in g

DHM.write_text(d, encoding="utf-8")
OVERLAY.write_text(w, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("V0913_DHM_RAIN_OVERLAY_PATCHED")
