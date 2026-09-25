package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Native-only helper for measuring a device's distance to the actual river geometry.
 * It uses the bundled Nepal waterways snapshot already shipped with FloodSafe.
 */
final class NativeRiverRiskDistance {
    private static volatile List<RiverShape> cached;

    private NativeRiverRiskDistance() {}

    static double distanceKm(Context context, double userLat, double userLon, String riverOrStationName) {
        if (!Double.isFinite(userLat) || !Double.isFinite(userLon)) return Double.NaN;
        String wanted = normalize(riverOrStationName);
        if (wanted.isEmpty()) return Double.NaN;
        try {
            List<RiverShape> rivers = load(context);
            double best = Double.POSITIVE_INFINITY;
            int matches = 0;
            for (RiverShape river : rivers) {
                if (!nameMatches(wanted, river.normalizedName)) continue;
                matches++;
                double d = distanceToPolylineKm(userLat, userLon, river.points);
                if (d < best) best = d;
            }
            return matches == 0 || !Double.isFinite(best) ? Double.NaN : best;
        } catch (Exception ignored) {
            return Double.NaN;
        }
    }

    private static List<RiverShape> load(Context context) throws Exception {
        List<RiverShape> result = cached;
        if (result != null) return result;
        synchronized (NativeRiverRiskDistance.class) {
            if (cached != null) return cached;
            String raw;
            try {
                raw = readAsset(context, "data/nepal-waterways-snapshot.json");
            } catch (Exception first) {
                raw = readAsset(context, "data/nepal-waterways-tiles/overview.json");
            }
            JSONObject root = new JSONObject(raw);
            JSONArray ways = root.optJSONArray("waterways");
            List<RiverShape> parsed = new ArrayList<>();
            if (ways != null) {
                for (int i = 0; i < ways.length(); i++) {
                    JSONObject w = ways.optJSONObject(i);
                    if (w == null) continue;
                    String name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"));
                    String normalized = normalize(name);
                    if (normalized.isEmpty()) continue;
                    JSONArray pts = w.optJSONArray("pts");
                    if (pts == null || pts.length() < 2) continue;
                    List<double[]> points = new ArrayList<>();
                    for (int j = 0; j < pts.length(); j++) {
                        JSONArray p = pts.optJSONArray(j);
                        if (p == null || p.length() < 2) continue;
                        double lon = p.optDouble(0, Double.NaN);
                        double lat = p.optDouble(1, Double.NaN);
                        if (Double.isFinite(lat) && Double.isFinite(lon)) points.add(new double[]{lat, lon});
                    }
                    if (points.size() >= 2) parsed.add(new RiverShape(normalized, points));
                }
            }
            cached = parsed;
            return parsed;
        }
    }

    private static double distanceToPolylineKm(double lat, double lon, List<double[]> pts) {
        if (pts == null || pts.isEmpty()) return Double.NaN;
        double best = Double.POSITIVE_INFINITY;
        for (int i = 0; i < pts.size() - 1; i++) {
            double[] a = pts.get(i), b = pts.get(i + 1);
            double d = pointSegmentKm(lat, lon, a[0], a[1], b[0], b[1]);
            if (d < best) best = d;
        }
        return best;
    }

    // Local equirectangular projection is accurate enough for the 2 km safety radius.
    private static double pointSegmentKm(double lat, double lon,
                                         double lat1, double lon1, double lat2, double lon2) {
        double meanLat = Math.toRadians((lat + lat1 + lat2) / 3.0);
        double kx = 111.320 * Math.cos(meanLat);
        double ky = 110.574;
        double px = lon * kx, py = lat * ky;
        double ax = lon1 * kx, ay = lat1 * ky;
        double bx = lon2 * kx, by = lat2 * ky;
        double dx = bx - ax, dy = by - ay;
        double len2 = dx * dx + dy * dy;
        double t = len2 <= 1e-12 ? 0.0 : ((px - ax) * dx + (py - ay) * dy) / len2;
        t = Math.max(0.0, Math.min(1.0, t));
        double cx = ax + t * dx, cy = ay + t * dy;
        double ex = px - cx, ey = py - cy;
        return Math.sqrt(ex * ex + ey * ey);
    }

    private static boolean nameMatches(String a, String b) {
        if (a.equals(b) || a.contains(b) || b.contains(a)) return true;
        String[] aa = a.split(" ");
        String[] bb = b.split(" ");
        int useful = 0, common = 0;
        for (String x : aa) {
            if (x.length() < 3 || generic(x)) continue;
            useful++;
            for (String y : bb) {
                if (x.equals(y)) { common++; break; }
            }
        }
        return useful > 0 && common >= Math.min(2, useful);
    }

    private static boolean generic(String s) {
        return "river".equals(s) || "khola".equals(s) || "nadi".equals(s) || "station".equals(s)
                || "gauge".equals(s) || " नदी".equals(s) || "खोला".equals(s);
    }

    private static String normalize(String value) {
        if (value == null) return "";
        return value.toLowerCase(Locale.ROOT)
                .replace('_', ' ')
                .replace('-', ' ')
                .replaceAll("[^\\p{L}\\p{N} ]", " ")
                .replaceAll("\\s+", " ")
                .trim();
    }

    private static String firstNonEmpty(String... values) {
        for (String value : values) if (value != null && !value.trim().isEmpty()) return value.trim();
        return "";
    }

    private static String readAsset(Context context, String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder b = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) b.append(line);
            return b.toString();
        }
    }

    private static final class RiverShape {
        final String normalizedName;
        final List<double[]> points;
        RiverShape(String normalizedName, List<double[]> points) {
            this.normalizedName = normalizedName;
            this.points = points;
        }
    }
}
