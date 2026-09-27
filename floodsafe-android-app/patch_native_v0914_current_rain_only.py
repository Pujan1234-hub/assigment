from pathlib import Path

ROOT = Path("floodsafe-android-app")
J = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
DHM = J / "DhmRainMirror.java"
OVERLAY = J / "WeatherMapOverlayController.java"
VERIFIER = J / "DhmCurrentRainVerifier.java"
GRADLE = ROOT / "app/build.gradle"

d = DHM.read_text(encoding="utf-8")
w = OVERLAY.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

def repl(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)

# DHM 1-hour accumulation is NOT a current-rain signal. Expose fresh gauge locations
# so a separate current-weather verifier can sample current precipitation at those points.
anchor = '    static List<RainPoint> freshRainPoints() {'
if anchor not in d:
    raise SystemExit('v0.9.13 DHM rain-point anchor missing')
method = r'''    /**
     * V0914_DHM_GAUGE_LOCATIONS_ONLY
     * Fresh DHM rainfall gauge locations. These are sampling locations only;
     * h1/h3/h24 accumulation values must never directly drive current rain animation.
     */
    static List<RainPoint> freshStationPoints() {
        List<RainPoint> out = new ArrayList<>();
        long now = System.currentTimeMillis();
        if (ROWS.isEmpty() || savedAt <= 0L || now - savedAt > DISPLAY_FRESH_MS) return out;
        for (RainRow row : ROWS.values()) {
            if (row == null || !Double.isFinite(row.lat) || !Double.isFinite(row.lon)) continue;
            out.add(new RainPoint(row.name, row.district, row.lat, row.lon, row.h1,
                    row.h3, row.h24, row.status, updated, savedAt));
        }
        return out;
    }

'''
d = d.replace(anchor, method + anchor, 1)

# Weather overlay must use only current-confirmed rain points, never raw DHM 1-hour accumulation.
w = repl(
    w,
    '            List<DhmRainMirror.RainPoint> dhm = DhmRainMirror.freshRainPoints(); // V0913_DHM_NATIVE_RAIN_OVERLAY',
    '            List<DhmRainMirror.RainPoint> dhm = DhmCurrentRainVerifier.currentRainPoints(mapView == null ? null : mapView.getContext()); // V0914_CURRENT_RAIN_ONLY',
    'current rain verifier hook',
)
w = w.replace('V0913_DHM_STATION_LOCAL_RAIN_FIELD — local animation around fresh official DHM rainfall gauges.',
              'V0914_CURRENT_RAIN_LOCAL_FIELD — local animation only around DHM gauge coordinates with current rain confirmation.', 1)
w = w.replace('.put("source", "DHM")', '.put("source", "CURRENT@DHM-GAUGE")', 1)

verifier = r'''package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * V0914_CURRENT_RAIN_ONLY_VERIFIER
 * Uses fresh DHM gauge coordinates as sampling locations, but NEVER uses DHM 1h/3h/24h
 * accumulation as proof that it is raining now. A gauge area is animated only when the
 * current weather response reports precipitation > 0 or a current WMO drizzle/rain/
 * showers/thunderstorm code. Cached confirmations expire quickly so stopped rain stops animating.
 */
final class DhmCurrentRainVerifier {
    private static final long REFRESH_MS = 4L * 60L * 1000L;
    private static final long MAX_CURRENT_AGE_MS = 7L * 60L * 1000L;
    private static final int BATCH = 40;
    private static final ExecutorService EXEC = Executors.newSingleThreadExecutor();
    private static final AtomicBoolean BUSY = new AtomicBoolean(false);
    private static volatile List<DhmRainMirror.RainPoint> CURRENT = Collections.emptyList();
    private static volatile long verifiedAt = 0L;

    private DhmCurrentRainVerifier() {}

    static List<DhmRainMirror.RainPoint> currentRainPoints(Context context) {
        long now = System.currentTimeMillis();
        if (verifiedAt <= 0L || now - verifiedAt >= REFRESH_MS) refreshAsync();
        if (verifiedAt <= 0L || now - verifiedAt > MAX_CURRENT_AGE_MS) return Collections.emptyList();
        return new ArrayList<>(CURRENT);
    }

    private static void refreshAsync() {
        if (!BUSY.compareAndSet(false, true)) return;
        EXEC.execute(() -> {
            try {
                List<DhmRainMirror.RainPoint> gauges = DhmRainMirror.freshStationPoints();
                List<DhmRainMirror.RainPoint> confirmed = new ArrayList<>();
                for (int start = 0; start < gauges.size(); start += BATCH) {
                    int end = Math.min(gauges.size(), start + BATCH);
                    verifyBatch(gauges.subList(start, end), confirmed);
                }
                CURRENT = confirmed;
                verifiedAt = System.currentTimeMillis();
            } catch (Exception ignored) {
                // Do not extend freshness on failure. Existing confirmations naturally expire,
                // preventing stale 'still raining' animation.
            } finally {
                BUSY.set(false);
            }
        });
    }

    private static void verifyBatch(List<DhmRainMirror.RainPoint> gauges,
                                    List<DhmRainMirror.RainPoint> confirmed) throws Exception {
        if (gauges == null || gauges.isEmpty()) return;
        StringBuilder lat = new StringBuilder(), lon = new StringBuilder();
        for (int i = 0; i < gauges.size(); i++) {
            if (i > 0) { lat.append(','); lon.append(','); }
            lat.append(String.format(Locale.US, "%.5f", gauges.get(i).lat));
            lon.append(String.format(Locale.US, "%.5f", gauges.get(i).lon));
        }
        String u = "https://api.open-meteo.com/v1/forecast?latitude=" + lat
                + "&longitude=" + lon
                + "&current=precipitation,weather_code&timezone=Asia%2FKathmandu";
        HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
        c.setConnectTimeout(7000);
        c.setReadTimeout(10000);
        c.setUseCaches(false);
        c.setRequestProperty("User-Agent", "FloodSafe-Nepal/native-current-rain");
        c.setRequestProperty("Cache-Control", "no-cache");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) { c.disconnect(); throw new IllegalStateException("HTTP " + code); }
        StringBuilder text = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line; while ((line = r.readLine()) != null) text.append(line);
        }
        c.disconnect();

        String raw = text.toString().trim();
        JSONArray rows;
        if (raw.startsWith("[")) rows = new JSONArray(raw);
        else { rows = new JSONArray(); rows.put(new JSONObject(raw)); }
        int n = Math.min(rows.length(), gauges.size());
        for (int i = 0; i < n; i++) {
            JSONObject row = rows.optJSONObject(i);
            JSONObject cur = row == null ? null : row.optJSONObject("current");
            if (cur == null) continue;
            double mm = cur.optDouble("precipitation", 0d);
            int wmo = cur.optInt("weather_code", -1);
            if (isCurrentRain(mm, wmo)) confirmed.add(gauges.get(i));
        }
    }

    static boolean isCurrentRain(double precipitation, int weatherCode) {
        if (Double.isFinite(precipitation) && precipitation > 0d) return true;
        return (weatherCode >= 51 && weatherCode <= 57)
                || (weatherCode >= 61 && weatherCode <= 67)
                || (weatherCode >= 80 && weatherCode <= 82)
                || (weatherCode >= 95 && weatherCode <= 99);
    }
}
'''
VERIFIER.write_text(verifier, encoding="utf-8")

# Version bump only after v0.9.13 chain.
g = repl(g, 'versionCode 30', 'versionCode 31', 'versionCode')
g = repl(g, "versionName '0.9.13-dhm-rain-overlay'", "versionName '0.9.14-current-rain-only'", 'versionName')

assert 'V0914_DHM_GAUGE_LOCATIONS_ONLY' in d
assert 'V0914_CURRENT_RAIN_ONLY' in w
assert 'DhmCurrentRainVerifier.currentRainPoints' in w
assert 'DhmRainMirror.freshRainPoints()' not in w
assert 'V0914_CURRENT_RAIN_ONLY_VERIFIER' in verifier
assert 'current=precipitation,weather_code' in verifier
assert 'versionCode 31' in g
assert "versionName '0.9.14-current-rain-only'" in g

DHM.write_text(d, encoding="utf-8")
OVERLAY.write_text(w, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("V0914_CURRENT_RAIN_ONLY_PATCHED")
