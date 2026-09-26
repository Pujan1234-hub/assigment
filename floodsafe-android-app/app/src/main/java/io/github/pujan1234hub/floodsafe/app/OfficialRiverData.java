package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * FloodSafe river truth layer.
 *
 * BIPAD is primary for latest observations/status. The Supabase mirror is used as the
 * complete station inventory and as a network fallback only. A cached/mirrored row is
 * never allowed to replace a newer BIPAD observation.
 */
final class OfficialRiverData {
    static final String BIPAD_RIVER_URL =
            "https://bipadportal.gov.np/api/v1/river/?limit=1000&ordering=-waterLevelOn";
    static final String MIRROR_URL =
            "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";

    // BIPAD/DHM river stations do not all report in the same minute. Two hours is a
    // conservative current window while still preventing historical values from being live.
    static final long CURRENT_MAX_AGE_MS = 2L * 60L * 60L * 1000L;
    static final long FUTURE_TOLERANCE_MS = 5L * 60L * 1000L;

    private OfficialRiverData() {}

    static final class Snapshot {
        final JSONArray rows;
        final int catalogCount;
        final int directBipadCount;
        final boolean directBipadOk;
        final long newestObservationAt;
        final String source;

        Snapshot(JSONArray rows, int catalogCount, int directBipadCount,
                 boolean directBipadOk, long newestObservationAt, String source) {
            this.rows = rows;
            this.catalogCount = catalogCount;
            this.directBipadCount = directBipadCount;
            this.directBipadOk = directBipadOk;
            this.newestObservationAt = newestObservationAt;
            this.source = source;
        }
    }

    static Snapshot fetch() throws Exception {
        JSONObject mirrorRoot = null;
        JSONObject bipadRoot = null;
        Exception mirrorError = null;
        Exception bipadError = null;
        try { mirrorRoot = getJson(MIRROR_URL + "?_fs=" + System.currentTimeMillis()); }
        catch (Exception e) { mirrorError = e; }
        try { bipadRoot = getJson(BIPAD_RIVER_URL + "&_fs=" + System.currentTimeMillis()); }
        catch (Exception e) { bipadError = e; }

        JSONArray catalog = mirrorRoot == null ? new JSONArray() : rows(mirrorRoot);
        JSONArray direct = bipadRoot == null ? new JSONArray() : rows(bipadRoot);
        boolean directOk = direct.length() > 0;
        if (catalog.length() == 0 && direct.length() == 0) {
            if (bipadError != null) throw bipadError;
            if (mirrorError != null) throw mirrorError;
            throw new IllegalStateException("No official river rows returned");
        }

        JSONArray merged = mergeNewerDirectOverCatalog(catalog, direct);
        long newest = -1L;
        for (int i = 0; i < merged.length(); i++) {
            JSONObject row = merged.optJSONObject(i);
            newest = Math.max(newest, observationTime(row));
        }
        String source = directOk ? "BIPAD direct + inventory mirror" : "inventory mirror fallback";
        return new Snapshot(merged,
                catalog.length() > 0 ? catalog.length() : merged.length(),
                direct.length(), directOk, newest, source);
    }

    private static JSONArray mergeNewerDirectOverCatalog(JSONArray catalog, JSONArray direct) {
        LinkedHashMap<String, JSONObject> merged = new LinkedHashMap<>();
        int anonymous = 0;
        for (int i = 0; i < catalog.length(); i++) {
            JSONObject row = catalog.optJSONObject(i);
            if (row == null) continue;
            JSONObject copy = cloneJson(row);
            String key = identity(copy);
            if (key.isEmpty()) key = "catalog#" + (anonymous++);
            merged.put(key, copy);
        }

        for (int i = 0; i < direct.length(); i++) {
            JSONObject live = direct.optJSONObject(i);
            if (live == null) continue;
            String key = identity(live);
            JSONObject base = key.isEmpty() ? null : merged.get(key);
            if (base == null) {
                // Try a name-only identity if one side used a numeric station id.
                String nameKey = "name:" + key(firstString(live,
                        "station_name", "stationName", "title", "name"));
                for (Map.Entry<String, JSONObject> e : merged.entrySet()) {
                    String existingNameKey = "name:" + key(firstString(e.getValue(),
                            "station_name", "stationName", "title", "name"));
                    if (nameKey.length() > 5 && nameKey.equals(existingNameKey)) {
                        key = e.getKey();
                        base = e.getValue();
                        break;
                    }
                }
            }
            if (base == null) {
                base = cloneJson(live);
                key = key.isEmpty() ? "bipad#" + (anonymous++) : key;
                merged.put(key, base);
            }

            long liveAt = observationTime(live);
            long cachedAt = observationTime(base);
            // Direct BIPAD is authoritative when it is newer or when the mirror has no
            // observation timestamp. Older direct data must not erase a newer mirror row.
            if (liveAt <= 0L || cachedAt <= 0L || liveAt >= cachedAt) {
                overlay(base, live);
                base.put("_fsDirectBipad", true);
                base.put("_fsDirectObservationAt", liveAt);
            }
        }

        JSONArray out = new JSONArray();
        for (JSONObject row : merged.values()) out.put(row);
        return out;
    }

    static long observationTime(JSONObject row) {
        if (row == null) return -1L;
        return parseTime(firstString(row,
                "waterLevelOn", "water_level_on",
                "measuredOn", "measured_on",
                "measurementTime", "measurement_time",
                "observationTime", "observation_time",
                "observedAt", "observed_at",
                "datetime", "timestamp", "_measurementTime"));
    }

    static boolean isCurrent(JSONObject row, long now) {
        long at = observationTime(row);
        return isCurrent(at, now);
    }

    static boolean isCurrent(long at, long now) {
        return at > 0L && at - now <= FUTURE_TOLERANCE_MS && now - at <= CURRENT_MAX_AGE_MS;
    }

    /** Official BIPAD status wins. Thresholds are fallback only when no usable status exists. */
    static String stage(JSONObject row, boolean current) {
        if (!current || row == null) return "unknown";
        String raw = firstString(row, "status", "status_name", "alertStatus", "alert_status",
                "riskLevel", "risk_level", "_officialStatus").trim().toUpperCase(Locale.ROOT);
        String official = officialStage(raw);
        if (!official.isEmpty()) return official;

        double level = firstNumber(row, "waterLevel", "water_level", "currentWaterLevel",
                "current_water_level", "currentLevel", "current_level", "level", "value", "_lastWaterLevel");
        double danger = firstNumber(row, "dangerLevel", "danger_level", "dangerThreshold",
                "danger_threshold", "_lastDangerLevel");
        double warning = firstNumber(row, "warningLevel", "warning_level", "warningThreshold",
                "warning_threshold", "_lastWarningLevel");
        double alert = firstNumber(row, "alertLevel", "alert_level", "alertThreshold", "alert_threshold");
        if (Double.isFinite(level) && Double.isFinite(danger) && danger > 0d && level >= danger) return "danger";
        if (Double.isFinite(level) && Double.isFinite(warning) && warning > 0d && level >= warning) return "warning";
        if (Double.isFinite(level) && Double.isFinite(alert) && alert > 0d && level >= alert) return "alert";
        if (Double.isFinite(level)) return "normal";
        return "unknown";
    }

    static String officialStage(String raw) {
        if (raw == null) return "";
        String s = raw.trim().toUpperCase(Locale.ROOT);
        if (s.isEmpty() || "NULL".equals(s) || "UNKNOWN".equals(s) || "N/A".equals(s)) return "";
        if (s.contains("ABOVE DANGER") || s.contains("DANGER LEVEL") && !s.contains("BELOW DANGER")
                || s.equals("DANGER") || s.contains(" RED" ) || s.startsWith("RED")) return "danger";
        if (s.contains("ABOVE WARNING") || s.contains("WARNING LEVEL") && !s.contains("BELOW WARNING")
                || s.equals("WARNING") || s.contains("ORANGE")) return "warning";
        if (s.contains("ALERT") || s.contains("WATCH") || s.contains("YELLOW")) return "alert";
        if (s.contains("BELOW WARNING") || s.contains("BELOW ALERT") || s.contains("NORMAL")
                || s.contains("SAFE") || s.contains("GREEN") || s.contains("BLUE")) return "normal";
        return "";
    }

    static int rank(String stage) {
        if ("danger".equals(stage)) return 0;
        if ("warning".equals(stage)) return 1;
        if ("alert".equals(stage)) return 2;
        if ("normal".equals(stage)) return 3;
        return 4;
    }

    static JSONArray rows(JSONObject root) {
        if (root == null) return new JSONArray();
        JSONArray a = root.optJSONArray("results");
        if (a == null) a = root.optJSONArray("data");
        if (a != null) return a;
        JSONObject data = root.optJSONObject("data");
        if (data != null) {
            a = data.optJSONArray("results");
            if (a != null) return a;
        }
        return new JSONArray();
    }

    static String firstString(JSONObject o, String... keys) {
        if (o == null) return "";
        for (String key : keys) {
            if (!o.has(key) || o.isNull(key)) continue;
            Object value = o.opt(key);
            if (value instanceof JSONObject) continue;
            String s = String.valueOf(value).trim();
            if (!s.isEmpty() && !"null".equalsIgnoreCase(s)) return s;
        }
        return "";
    }

    static double firstNumber(JSONObject o, String... keys) {
        if (o == null) return Double.NaN;
        for (String key : keys) {
            if (!o.has(key) || o.isNull(key)) continue;
            Object value = o.opt(key);
            if (value instanceof Number) {
                double d = ((Number) value).doubleValue();
                if (Double.isFinite(d)) return d;
            }
            try {
                double d = Double.parseDouble(String.valueOf(value).replace(",", "").trim());
                if (Double.isFinite(d)) return d;
            } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    static long parseTime(String value) {
        if (value == null || value.trim().isEmpty()) return -1L;
        String v = value.trim();
        try {
            long n = Long.parseLong(v);
            return n < 10_000_000_000L ? n * 1000L : n;
        } catch (Exception ignored) {}
        try { return Instant.parse(v).toEpochMilli(); } catch (Exception ignored) {}
        try { return OffsetDateTime.parse(v).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return ZonedDateTime.parse(v).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try {
            return LocalDateTime.parse(v.replace(' ', 'T'), DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                    .atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();
        } catch (Exception ignored) { return -1L; }
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(22000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("User-Agent", "Mozilla/5.0 FloodSafe-Nepal/native");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        c.setRequestProperty("Pragma", "no-cache");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) {
            c.disconnect();
            throw new IllegalStateException("HTTP " + code + " for " + url);
        }
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static String identity(JSONObject row) {
        String id = firstString(row, "stationSeriesId", "station_series_id", "stationId", "station_id",
                "stationIndex", "station_index", "seriesId", "series_id", "id");
        if (!id.isEmpty()) return "id:" + id;
        String name = firstString(row, "station_name", "stationName", "title", "name");
        return name.isEmpty() ? "" : "name:" + key(name);
    }

    private static String key(String s) {
        return s == null ? "" : s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]", "");
    }

    private static JSONObject cloneJson(JSONObject row) {
        try { return new JSONObject(row.toString()); }
        catch (Exception ignored) { return new JSONObject(); }
    }

    private static void overlay(JSONObject base, JSONObject newer) {
        if (base == null || newer == null) return;
        Iterator<String> it = newer.keys();
        while (it.hasNext()) {
            String key = it.next();
            Object value = newer.opt(key);
            if (value == null || value == JSONObject.NULL) continue;
            if (value instanceof String && ((String) value).trim().isEmpty()) continue;
            try { base.put(key, value); } catch (Exception ignored) {}
        }
    }
}
