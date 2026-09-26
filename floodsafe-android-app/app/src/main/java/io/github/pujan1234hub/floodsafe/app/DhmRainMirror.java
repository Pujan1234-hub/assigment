package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Read-only native mirror of the official DHM Rainfall Watch Map. */
final class DhmRainMirror {
    static final String PAGE = "https://dhm.gov.np/hydrology/rainfall-watch-map";
    static final String API = "https://dhm.gov.np/hydrology/getRainfallFilter";
    private static final String PREFS = "floodsafe_dhm_rain_mirror_native_v1";
    private static final String CACHE = "rows_json";
    private static final long POLL_MS = 5L * 60L * 1000L;
    private static final long DISPLAY_FRESH_MS = 30L * 60L * 1000L;
    private static final ScheduledExecutorService EXEC = Executors.newSingleThreadScheduledExecutor();
    private static final AtomicBoolean STARTED = new AtomicBoolean(false);
    private static final AtomicBoolean BUSY = new AtomicBoolean(false);
    private static final Map<String, RainRow> ROWS = new ConcurrentHashMap<>();
    private static volatile String updated = "";
    private static volatile long savedAt = 0L;

    private DhmRainMirror() {}

    static void ensureStarted(Context context) {
        Context app = context.getApplicationContext();
        loadCache(app);
        if (STARTED.compareAndSet(false, true)) {
            EXEC.scheduleWithFixedDelay(() -> refresh(app), 0L, POLL_MS, TimeUnit.MILLISECONDS);
        } else {
            EXEC.execute(() -> refresh(app));
        }
    }

    private static void refresh(Context app) {
        if (!BUSY.compareAndSet(false, true)) return;
        try {
            Session session = openPage();
            Map<String, RainRow> next = new ConcurrentHashMap<>();
            String newest = "";
            for (int hour : new int[]{1, 3, 6, 12, 24}) {
                JSONObject root = postHour(session, hour);
                if (!"success".equalsIgnoreCase(root.optString("status"))) continue;
                JSONObject data = root.optJSONObject("data");
                if (data == null) continue;
                JSONArray arr = data.optJSONArray("0");
                if (arr == null) continue;
                String stamp = data.optString("rainfall_date_time", "");
                if (!stamp.isEmpty()) newest = stamp;
                for (int i = 0; i < arr.length(); i++) {
                    JSONObject o = arr.optJSONObject(i);
                    if (o == null) continue;
                    String name = o.optString("name", "").trim();
                    if (name.isEmpty()) continue;
                    String key = key(name);
                    RainRow row = next.get(key);
                    if (row == null) {
                        row = new RainRow();
                        row.name = name;
                        row.id = o.optString("id", "");
                        row.seriesId = o.optString("series_id", "");
                        row.basin = o.optString("basin", "");
                        row.district = o.optString("district", "");
                        row.lat = num(o.opt("latitude"));
                        row.lon = num(o.opt("longitude"));
                        row.status = o.optString("status", "");
                        next.put(key, row);
                    }
                    double value = num(o.opt("value"));
                    if (hour == 1) row.h1 = value;
                    else if (hour == 3) row.h3 = value;
                    else if (hour == 6) row.h6 = value;
                    else if (hour == 12) row.h12 = value;
                    else row.h24 = value;
                    String status = o.optString("status", "");
                    if (!status.isEmpty()) row.status = status;
                }
            }
            if (!next.isEmpty()) {
                ROWS.clear();
                ROWS.putAll(next);
                updated = newest;
                savedAt = System.currentTimeMillis();
                saveCache(app);
            }
        } catch (Exception ignored) {
            // Keep the last short-lived verified cache. Old cache is never shown as fresh.
        } finally {
            BUSY.set(false);
        }
    }

    private static Session openPage() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(PAGE + "?_fs=" + System.currentTimeMillis()).openConnection();
        c.setConnectTimeout(7000);
        c.setReadTimeout(9000);
        c.setUseCaches(false);
        c.setRequestProperty("User-Agent", "Mozilla/5.0 FloodSafe-Nepal/native");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        String html = read(c);
        String cookie = c.getHeaderField("Set-Cookie");
        c.disconnect();
        Matcher matcher = Pattern.compile("name=\\\"csrf_test_name\\\"\\s+value=\\\"([^\\\"]+)\\\"").matcher(html);
        if (!matcher.find()) throw new IllegalStateException("DHM CSRF token missing");
        Session s = new Session();
        s.csrf = matcher.group(1);
        s.cookie = cookie == null ? "" : cookie.split(";", 2)[0];
        return s;
    }

    private static JSONObject postHour(Session s, int hour) throws Exception {
        String body = "csrf_test_name=" + enc(s.csrf) + "&type=0&mapValue=all&hour=" + hour;
        HttpURLConnection c = (HttpURLConnection) new URL(API).openConnection();
        c.setConnectTimeout(7000);
        c.setReadTimeout(10000);
        c.setUseCaches(false);
        c.setDoOutput(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("User-Agent", "Mozilla/5.0 FloodSafe-Nepal/native");
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
        c.setRequestProperty("X-Requested-With", "XMLHttpRequest");
        c.setRequestProperty("Referer", PAGE);
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        if (!s.cookie.isEmpty()) c.setRequestProperty("Cookie", s.cookie);
        try (OutputStream out = c.getOutputStream()) {
            out.write(body.getBytes(StandardCharsets.UTF_8));
        }
        String text = read(c);
        c.disconnect();
        return new JSONObject(text);
    }

    /**
     * Returns rainfall only when the mirror itself is fresh and a conservative match exists:
     * strong name evidence, or same district plus a nearby DHM rainfall station.
     */
    static String detailFor(String stationName, String district, double lat, double lon) {
        if (ROWS.isEmpty() || savedAt <= 0L || System.currentTimeMillis() - savedAt > DISPLAY_FRESH_MS) return null;
        String q = key(stationName);
        String qDistrict = key(district);
        RainRow best = null;
        double bestScore = Double.POSITIVE_INFINITY;
        double bestDistance = Double.POSITIVE_INFINITY;
        String matchReason = "";
        for (RainRow row : ROWS.values()) {
            double distance = Double.isFinite(row.lat) && Double.isFinite(row.lon)
                    ? km(lat, lon, row.lat, row.lon) : Double.POSITIVE_INFINITY;
            String rk = key(row.name);
            boolean strongName = !q.isEmpty() && !rk.isEmpty()
                    && Math.min(q.length(), rk.length()) >= 5 && (q.contains(rk) || rk.contains(q));
            boolean sameDistrict = !qDistrict.isEmpty() && qDistrict.equals(key(row.district));
            if (!strongName && !(sameDistrict && distance <= 20d)) continue;
            double score = strongName ? Math.min(distance, 30d) : 100d + distance;
            if (score < bestScore) {
                best = row;
                bestScore = score;
                bestDistance = distance;
                matchReason = strongName ? "name/area match" : "same district + nearby";
            }
        }
        if (best == null) return null;
        StringBuilder b = new StringBuilder();
        b.append("🌧️ DHM rainfall — official\n").append(best.name);
        if (Double.isFinite(bestDistance)) b.append(String.format(Locale.US, " • %.1f km", bestDistance));
        b.append(" • ").append(matchReason);
        if (!best.district.isEmpty()) b.append("\nDistrict: ").append(best.district);
        if (!best.basin.isEmpty()) b.append("\nBasin: ").append(best.basin);
        b.append("\n1 hr: ").append(mm(best.h1))
                .append("\n3 hr: ").append(mm(best.h3))
                .append("\n6 hr: ").append(mm(best.h6))
                .append("\n12 hr: ").append(mm(best.h12))
                .append("\n24 hr: ").append(mm(best.h24));
        if (!best.status.isEmpty()) b.append("\nStatus: ").append(best.status);
        if (!updated.isEmpty()) b.append("\nOfficial update: ").append(updated);
        b.append("\nSource: DHM Rainfall Watch Map");
        return b.toString();
    }

    private static String read(HttpURLConnection c) throws Exception {
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        }
        return b.toString();
    }

    private static String enc(String s) throws Exception { return URLEncoder.encode(s, "UTF-8"); }
    private static double num(Object value) {
        if (value instanceof Number) return ((Number) value).doubleValue();
        if (value != null && value != JSONObject.NULL) {
            try { return Double.parseDouble(String.valueOf(value).replace(",", "").trim()); }
            catch (Exception ignored) {}
        }
        return Double.NaN;
    }
    private static String key(String s) {
        return s == null ? "" : s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]", "");
    }
    private static String mm(double v) { return Double.isFinite(v) ? String.format(Locale.US, "%.1f mm", v) : "—"; }
    private static double km(double a, double b, double c, double d) {
        double r = 6371d, dp = Math.toRadians(c - a), dl = Math.toRadians(d - b);
        double q = Math.sin(dp / 2d) * Math.sin(dp / 2d)
                + Math.cos(Math.toRadians(a)) * Math.cos(Math.toRadians(c)) * Math.sin(dl / 2d) * Math.sin(dl / 2d);
        return 2d * r * Math.asin(Math.sqrt(q));
    }

    private static void saveCache(Context app) {
        try {
            JSONArray a = new JSONArray();
            for (RainRow r : ROWS.values()) a.put(r.json());
            app.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                    .putString(CACHE, a.toString()).putString("updated", updated).putLong("saved", savedAt).apply();
        } catch (Exception ignored) {}
    }

    private static void loadCache(Context app) {
        if (!ROWS.isEmpty()) return;
        try {
            SharedPreferences p = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            String raw = p.getString(CACHE, "");
            long cachedAt = p.getLong("saved", 0L);
            if (raw.isEmpty() || cachedAt <= 0L || System.currentTimeMillis() - cachedAt > DISPLAY_FRESH_MS) return;
            JSONArray a = new JSONArray(raw);
            for (int i = 0; i < a.length(); i++) {
                RainRow r = RainRow.from(a.optJSONObject(i));
                if (r != null && !r.name.isEmpty()) ROWS.put(key(r.name), r);
            }
            updated = p.getString("updated", "");
            savedAt = cachedAt;
        } catch (Exception ignored) {}
    }

    private static final class Session { String csrf, cookie; }
    private static final class RainRow {
        String id = "", seriesId = "", name = "", basin = "", district = "", status = "";
        double lat = Double.NaN, lon = Double.NaN, h1 = Double.NaN, h3 = Double.NaN,
                h6 = Double.NaN, h12 = Double.NaN, h24 = Double.NaN;
        JSONObject json() throws Exception {
            return new JSONObject().put("id", id).put("seriesId", seriesId).put("name", name)
                    .put("basin", basin).put("district", district).put("status", status)
                    .put("lat", lat).put("lon", lon).put("h1", h1).put("h3", h3)
                    .put("h6", h6).put("h12", h12).put("h24", h24);
        }
        static RainRow from(JSONObject o) {
            if (o == null) return null;
            RainRow r = new RainRow();
            r.id = o.optString("id", ""); r.seriesId = o.optString("seriesId", "");
            r.name = o.optString("name", ""); r.basin = o.optString("basin", "");
            r.district = o.optString("district", ""); r.status = o.optString("status", "");
            r.lat = o.optDouble("lat", Double.NaN); r.lon = o.optDouble("lon", Double.NaN);
            r.h1 = o.optDouble("h1", Double.NaN); r.h3 = o.optDouble("h3", Double.NaN);
            r.h6 = o.optDouble("h6", Double.NaN); r.h12 = o.optDouble("h12", Double.NaN);
            r.h24 = o.optDouble("h24", Double.NaN);
            return r;
        }
    }
}
