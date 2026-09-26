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
 * V0905_BIPAD_LATEST_PARITY
 *
 * BIPAD Realtime > River watch currently maps to river-stations/?latest=true.
 * That endpoint is the visible station set. The larger station catalogue and mirror
 * only enrich coordinates/thresholds/river metadata; they never add visible rows.
 * Historical river feeds may refresh a matching visible station with a newer official
 * observation, but cannot add another station to the visible set.
 */
final class BipadRealtimeStationFeed {
    private static final String BIPAD = "https://bipadportal.gov.np/api/v1/";
    private static final String LATEST = BIPAD + "river-stations/?latest=true&limit=5000";
    private static final String CATALOG = BIPAD + "river-stations/?limit=5000";
    private static final String CURRENT = BIPAD + "river/?limit=5000&ordering=-waterLevelOn";
    private static final String TRIMMED = BIPAD + "river-trimed/?limit=5000";

    private BipadRealtimeStationFeed() {}

    static JSONArray fetch() throws Exception {
        long now = System.currentTimeMillis();

        // This is the exact BIPAD River watch visible set. If it fails, do not replace
        // an already displayed verified set with the larger metadata inventory.
        JSONArray visible = safeRows(LATEST + "&_v0905=" + now);
        if (visible.length() == 0) throw new IllegalStateException("No BIPAD latest River watch rows");

        JSONArray catalog = safeRows(CATALOG + "&_v0905=" + now);
        JSONArray mirror = safeRows(OfficialRiverData.MIRROR_URL + "?_v0905=" + now);

        Map<String, JSONObject> catalogById = new HashMap<>();
        Map<String, JSONObject> catalogByName = new HashMap<>();
        Map<String, JSONObject> mirrorById = new HashMap<>();
        Map<String, JSONObject> mirrorByName = new HashMap<>();
        index(catalog, catalogById, catalogByName);
        index(mirror, mirrorById, mirrorByName);

        // Historical/live feeds are observation refresh sources only. They cannot add
        // a station that BIPAD latest=true did not include in the visible River watch set.
        Map<String, JSONObject> newestById = new HashMap<>();
        Map<String, JSONObject> newestByName = new HashMap<>();
        collectNewest(safeRows(CURRENT + "&_v0905=" + now), newestById, newestByName);
        collectNewest(safeRows(TRIMMED + "&_v0905=" + now), newestById, newestByName);

        LinkedHashMap<String, JSONObject> visibleUnique = new LinkedHashMap<>();
        int anonymous = 0;
        for (int i = 0; i < visible.length(); i++) {
            JSONObject raw = visible.optJSONObject(i);
            if (raw == null) continue;
            JSONObject latest = normalized(raw);
            String id = stationId(latest), name = stationName(latest);
            String identity = !id.isEmpty() ? "id:" + key(id) : (!name.isEmpty() ? "name:" + key(name) : "row:" + (anonymous++));
            JSONObject old = visibleUnique.get(identity);
            if (old == null || OfficialRiverData.observationTime(latest) >= OfficialRiverData.observationTime(old)) {
                visibleUnique.put(identity, latest);
            }
        }

        JSONArray out = new JSONArray();
        for (JSONObject latest : visibleUnique.values()) {
            String id = stationId(latest), name = stationName(latest);

            JSONObject catalogMeta = !id.isEmpty() ? catalogById.get(key(id)) : null;
            if (catalogMeta == null && !name.isEmpty()) catalogMeta = catalogByName.get(key(name));
            JSONObject mirrorMeta = !id.isEmpty() ? mirrorById.get(key(id)) : null;
            if (mirrorMeta == null && !name.isEmpty()) mirrorMeta = mirrorByName.get(key(name));

            JSONObject row = new JSONObject();
            if (mirrorMeta != null) row = merge(row, mirrorMeta);
            if (catalogMeta != null) row = merge(row, catalogMeta);
            row = merge(row, latest);

            JSONObject refreshed = !id.isEmpty() ? newestById.get(key(id)) : null;
            if (refreshed == null && !name.isEmpty()) refreshed = newestByName.get(key(name));
            if (refreshed != null) {
                long refreshAt = OfficialRiverData.observationTime(refreshed);
                long latestAt = OfficialRiverData.observationTime(row);
                if (refreshAt > 0L && (latestAt <= 0L || refreshAt >= latestAt)) row = merge(row, refreshed);
            }

            try {
                row.put("_fsBipadLatestParity", true);
                row.put("_fsVisibleSource", "river-stations-latest");
                row.put("_fsCatalogCount", catalog.length());
            } catch (Exception ignored) {}
            out.put(row);
        }
        if (out.length() == 0) throw new IllegalStateException("BIPAD latest rows parsed to zero");
        return out;
    }

    private static void collectNewest(JSONArray rows, Map<String, JSONObject> byId, Map<String, JSONObject> byName) {
        for (int i = 0; i < rows.length(); i++) {
            JSONObject raw = rows.optJSONObject(i);
            if (raw == null) continue;
            JSONObject row = normalized(raw);
            String id = stationId(row), name = stationName(row);
            if (!id.isEmpty()) putNewest(byId, key(id), row);
            if (!name.isEmpty()) putNewest(byName, key(name), row);
        }
    }

    private static void putNewest(Map<String, JSONObject> map, String k, JSONObject row) {
        JSONObject old = map.get(k);
        long nextAt = OfficialRiverData.observationTime(row);
        long oldAt = old == null ? -1L : OfficialRiverData.observationTime(old);
        if (old == null || nextAt > oldAt) map.put(k, row);
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
        c.setRequestProperty("User-Agent", "FloodSafe-Nepal/native-v0905-bipad-latest");
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
