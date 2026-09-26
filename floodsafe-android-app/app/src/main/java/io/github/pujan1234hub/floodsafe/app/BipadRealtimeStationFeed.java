package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * V0904_BIPAD_RIVER_WATCH_PARITY
 *
 * The visible station set follows BIPAD's current River watch measurement feed, not
 * the larger river-stations metadata catalogue. The catalogue/mirror are used only
 * to complete coordinates, thresholds, basin/river names and other metadata.
 * Therefore catalogue-only/mirror-only rows can never inflate the visible count.
 */
final class BipadRealtimeStationFeed {
    private static final String BIPAD = "https://bipadportal.gov.np/api/v1/";
    private static final String CURRENT = BIPAD + "river/?limit=5000&ordering=-waterLevelOn";
    private static final String TRIMMED = BIPAD + "river-trimed/?limit=5000";
    private static final String LATEST = BIPAD + "river-stations/?latest=true&limit=5000";
    private static final String CATALOG = BIPAD + "river-stations/?limit=5000";

    private BipadRealtimeStationFeed() {}

    static JSONArray fetch() throws Exception {
        long now = System.currentTimeMillis();

        // BIPAD Realtime > River watch is measurement-driven. Use this as the visible set.
        JSONArray visible = safeRows(CURRENT + "&_v0904=" + now);
        String source = "river";
        if (visible.length() == 0) {
            visible = safeRows(TRIMMED + "&_v0904=" + now);
            source = "river-trimed";
        }
        if (visible.length() == 0) {
            visible = safeRows(LATEST + "&_v0904=" + now);
            source = "river-stations-latest";
        }
        if (visible.length() == 0) throw new IllegalStateException("No BIPAD River watch observations");

        JSONArray catalog = safeRows(CATALOG + "&_v0904=" + now);
        JSONArray mirror = safeRows(OfficialRiverData.MIRROR_URL + "?_v0904=" + now);

        Map<String, JSONObject> catalogById = new HashMap<>();
        Map<String, JSONObject> catalogByName = new HashMap<>();
        Map<String, JSONObject> mirrorById = new HashMap<>();
        Map<String, JSONObject> mirrorByName = new HashMap<>();
        index(catalog, catalogById, catalogByName);
        index(mirror, mirrorById, mirrorByName);

        // Keep one newest current BIPAD observation per station identity, preserving API order.
        LinkedHashMap<String, JSONObject> currentByStation = new LinkedHashMap<>();
        int anonymous = 0;
        for (int i = 0; i < visible.length(); i++) {
            JSONObject raw = visible.optJSONObject(i);
            if (raw == null) continue;
            JSONObject live = normalized(raw);
            String id = stationId(live), name = stationName(live);
            String identity = !id.isEmpty() ? "id:" + key(id) : (!name.isEmpty() ? "name:" + key(name) : "row:" + (anonymous++));
            JSONObject old = currentByStation.get(identity);
            if (old == null || OfficialRiverData.observationTime(live) > OfficialRiverData.observationTime(old)) {
                currentByStation.put(identity, live);
            }
        }

        JSONArray out = new JSONArray();
        for (JSONObject live : currentByStation.values()) {
            String id = stationId(live), name = stationName(live);
            JSONObject meta = !id.isEmpty() ? catalogById.get(key(id)) : null;
            if (meta == null && !name.isEmpty()) meta = catalogByName.get(key(name));

            // Mirror is metadata fallback only and is never iterated as a visible source.
            JSONObject mirrorMeta = !id.isEmpty() ? mirrorById.get(key(id)) : null;
            if (mirrorMeta == null && !name.isEmpty()) mirrorMeta = mirrorByName.get(key(name));

            JSONObject row = new JSONObject();
            if (mirrorMeta != null) row = merge(row, mirrorMeta);
            if (meta != null) row = merge(row, meta);
            row = merge(row, live); // official current observation always wins
            try {
                row.put("_fsRiverWatchParity", true);
                row.put("_fsVisibleSource", source);
                row.put("_fsCatalogCount", catalog.length());
            } catch (Exception ignored) {}
            out.put(row);
        }
        return out;
    }

    private static void index(JSONArray rows, Map<String, JSONObject> byId, Map<String, JSONObject> byName) {
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            if (row == null) continue;
            JSONObject n = normalized(row);
            String id = stationId(n), name = stationName(n);
            if (!id.isEmpty()) byId.put(key(id), n);
            if (!name.isEmpty()) byName.put(key(name), n);
        }
    }

    private static JSONArray safeRows(String url) {
        try { return rows(get(url)); }
        catch (Exception ignored) { return new JSONArray(); }
    }

    private static JSONObject get(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(18000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("User-Agent", "FloodSafe-Nepal/native-v0904-river-watch");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        c.setRequestProperty("Pragma", "no-cache");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) {
            c.disconnect();
            throw new IllegalStateException("HTTP " + code);
        }
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static JSONArray rows(JSONObject root) {
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

    private static JSONObject normalized(JSONObject src) {
        JSONObject out;
        try { out = new JSONObject(src.toString()); }
        catch (Exception e) { out = new JSONObject(); }
        try {
            JSONObject fields = out.optJSONObject("fields");
            if (fields != null) overlayMissing(out, fields);
            normalizeCoordinates(out);
        } catch (Exception ignored) {}
        return out;
    }

    private static void normalizeCoordinates(JSONObject row) {
        double lat = firstNumber(row, "latitude", "lat", "stationLatitude", "station_latitude", "stationLat");
        double lon = firstNumber(row, "longitude", "lon", "lng", "stationLongitude", "station_longitude", "stationLon");
        if (Double.isFinite(lat) && Double.isFinite(lon)) return;
        Object point = row.opt("point");
        if (point == null || point == JSONObject.NULL) point = row.opt("geometry");
        JSONArray c = null;
        if (point instanceof JSONObject) c = ((JSONObject) point).optJSONArray("coordinates");
        else if (point instanceof JSONArray) c = (JSONArray) point;
        if (c != null && c.length() >= 2) {
            double lo = c.optDouble(0, Double.NaN), la = c.optDouble(1, Double.NaN);
            if (Double.isFinite(la) && Double.isFinite(lo)) {
                try { row.put("latitude", la); row.put("longitude", lo); } catch (Exception ignored) {}
            }
        }
    }

    private static JSONObject merge(JSONObject base, JSONObject newer) {
        JSONObject out;
        try { out = new JSONObject(base == null ? "{}" : base.toString()); }
        catch (Exception e) { out = new JSONObject(); }
        if (newer != null) {
            Iterator<String> it = newer.keys();
            while (it.hasNext()) {
                String k = it.next();
                Object v = newer.opt(k);
                if (v == null || v == JSONObject.NULL) continue;
                if (v instanceof String && ((String) v).trim().isEmpty()) continue;
                try { out.put(k, v); } catch (Exception ignored) {}
            }
        }
        normalizeCoordinates(out);
        return out;
    }

    private static void overlayMissing(JSONObject target, JSONObject source) {
        Iterator<String> it = source.keys();
        while (it.hasNext()) {
            String k = it.next();
            Object existing = target.opt(k);
            if (existing != null && existing != JSONObject.NULL && !String.valueOf(existing).trim().isEmpty()) continue;
            Object v = source.opt(k);
            if (v == null || v == JSONObject.NULL) continue;
            try { target.put(k, v); } catch (Exception ignored) {}
        }
    }

    private static String stationId(JSONObject row) {
        return firstString(row, "stationSeriesId", "station_series_id", "stationId", "station_id",
                "stationIndex", "station_index", "seriesId", "series_id");
    }

    private static String stationName(JSONObject row) {
        return firstString(row, "station_name", "stationName", "title", "name");
    }

    private static String firstString(JSONObject row, String... keys) {
        for (String k : keys) {
            Object v = row.opt(k);
            if (v == null || v == JSONObject.NULL || v instanceof JSONObject) continue;
            String s = String.valueOf(v).trim();
            if (!s.isEmpty() && !"null".equalsIgnoreCase(s)) return s;
        }
        return "";
    }

    private static double firstNumber(JSONObject row, String... keys) {
        for (String k : keys) {
            Object v = row.opt(k);
            if (v instanceof Number) {
                double d = ((Number) v).doubleValue();
                if (Double.isFinite(d)) return d;
            }
            if (v != null && v != JSONObject.NULL) {
                try {
                    double d = Double.parseDouble(String.valueOf(v).replace(",", "").trim());
                    if (Double.isFinite(d)) return d;
                } catch (Exception ignored) {}
            }
        }
        return Double.NaN;
    }

    private static String key(String value) {
        if (value == null) return "";
        return value.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]", "");
    }
}
