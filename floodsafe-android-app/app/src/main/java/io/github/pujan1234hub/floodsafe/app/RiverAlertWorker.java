package io.github.pujan1234hub.floodsafe.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;

import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
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
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Closed-app fallback for nearby official river warnings.
 *
 * Safety contract:
 *  - only fresh BIPAD/DHM Warning/Danger observations can trigger;
 *  - the official gauge must be matched to a bundled real river geometry by river-name evidence;
 *  - the user's distance is measured to that affected river geometry, not to the station dot;
 *  - if a safe same-river geometry match cannot be established, no emergency notification is sent.
 */
public final class RiverAlertWorker extends Worker {
    private static final String ENDPOINT =
            "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String CHANNEL_ID = "official_nepal_alerts_v4";
    private static final String PUSH_PREFS = "floodsafe_push_guard";
    private static final double RADIUS_KM = 2d;
    private static final long MAX_AGE_MS = 10L * 60L * 1000L;
    private static final long FUTURE_TOLERANCE_MS = 5L * 60L * 1000L;
    private static final long WARNING_REPEAT_MS = 90L * 60L * 1000L;
    private static final long DANGER_REPEAT_MS = 30L * 60L * 1000L;
    private static final double MATERIAL_RISE_METRES = 0.20d;
    private static final int MAX_NOTIFICATIONS_PER_RUN = 3;

    public RiverAlertWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull @Override public Result doWork() {
        Context app = getApplicationContext();
        SharedPreferences monitor = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!monitor.getBoolean("enabled", false)) return Result.success();
        if (!monitor.getBoolean("follow_device", false)) return Result.success();
        if (Build.VERSION.SDK_INT >= 33 && app.checkSelfPermission(
                android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return Result.success();
        }

        double homeLat = Double.longBitsToDouble(monitor.getLong(
                "lat", Double.doubleToRawLongBits(Double.NaN)));
        double homeLon = Double.longBitsToDouble(monitor.getLong(
                "lon", Double.doubleToRawLongBits(Double.NaN)));
        if (!Double.isFinite(homeLat) || !Double.isFinite(homeLon) || !insideNepal(homeLat, homeLon)) {
            return Result.success();
        }
        long locationTime = monitor.getLong("location_time", 0L);
        if (!MonitoringLocationPolicy.freshNepalDeviceLocation(
                locationTime, System.currentTimeMillis(), homeLat, homeLon)) {
            return Result.success();
        }

        try {
            JSONObject root = fetch();
            JSONArray rows = root.optJSONArray("results");
            if (rows == null) rows = root.optJSONArray("data");
            if (rows == null) return Result.retry();

            List<RiverShape> riverShapes = loadRiverShapes(app);
            if (riverShapes.isEmpty()) return Result.retry();

            long now = System.currentTimeMillis();
            List<Hazard> hazards = new ArrayList<>();
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.optJSONObject(i);
                if (row == null) continue;
                Hazard hazard = hazard(row, riverShapes, homeLat, homeLon, now);
                if (hazard != null) hazards.add(hazard);
            }
            hazards.sort(Comparator
                    .comparingInt((Hazard h) -> "danger".equals(h.stage) ? 0 : 1)
                    .thenComparingDouble(h -> h.distanceKm));

            int shown = 0;
            for (Hazard hazard : hazards) {
                if (shown >= MAX_NOTIFICATIONS_PER_RUN) break;
                if (!claim(hazard, now)) continue;
                notifyHazard(hazard);
                shown++;
            }
            return Result.success();
        } catch (Exception ignored) {
            return Result.retry();
        }
    }

    private static JSONObject fetch() throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(
                ENDPOINT + "?_fs=" + System.currentTimeMillis()).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(20000);
        connection.setUseCaches(false);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-cache, no-store");
        connection.setRequestProperty("Pragma", "no-cache");
        int code = connection.getResponseCode();
        if (code != 200) {
            connection.disconnect();
            throw new IllegalStateException("River HTTP " + code);
        }
        StringBuilder body = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                connection.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) body.append(line);
        } finally {
            connection.disconnect();
        }
        return new JSONObject(body.toString());
    }

    private static final class Hazard {
        final String stage;
        final String stationId;
        final String stationName;
        final String riverName;
        final double distanceKm;
        final double level;
        final double warning;
        final double danger;
        final long measuredAt;

        Hazard(String stage, String stationId, String stationName, String riverName,
               double distanceKm, double level, double warning, double danger, long measuredAt) {
            this.stage = stage;
            this.stationId = stationId;
            this.stationName = stationName;
            this.riverName = riverName;
            this.distanceKm = distanceKm;
            this.level = level;
            this.warning = warning;
            this.danger = danger;
            this.measuredAt = measuredAt;
        }
    }

    private static final class RiverShape {
        String name;
        String key;
        final List<double[]> points = new ArrayList<>();
    }

    private static Hazard hazard(JSONObject row, List<RiverShape> riverShapes,
                                 double homeLat, double homeLon, long now) {
        double lat = firstNumber(row, "latitude", "lat", "stationLatitude", "station_latitude");
        double lon = firstNumber(row, "longitude", "lon", "lng", "stationLongitude", "station_longitude");
        if (!Double.isFinite(lat) || !Double.isFinite(lon) || !insideNepal(lat, lon)) return null;

        double level = firstNumber(row, "waterLevel", "water_level", "currentWaterLevel",
                "current_water_level", "currentLevel", "current_level", "level", "value", "_lastWaterLevel");
        double warning = firstNumber(row, "warningLevel", "warning_level", "warningThreshold",
                "warning_threshold", "_lastWarningLevel");
        double danger = firstNumber(row, "dangerLevel", "danger_level", "dangerThreshold",
                "danger_threshold", "_lastDangerLevel");
        String official = firstString(row, "status", "status_name", "alertStatus", "alert_status",
                "riskLevel", "risk_level", "_officialStatus").toUpperCase(Locale.ROOT);

        String stage = "";
        if (Double.isFinite(level) && Double.isFinite(danger) && danger > 0d && level >= danger) {
            stage = "danger";
        } else if ((official.contains("DANGER") || official.contains("RED"))
                && !official.contains("BELOW DANGER")) {
            stage = "danger";
        } else if (Double.isFinite(level) && Double.isFinite(warning) && warning > 0d && level >= warning) {
            stage = "warning";
        } else if ((official.contains("WARNING") || official.contains("ORANGE"))
                && !official.contains("BELOW WARNING")) {
            stage = "warning";
        }
        if (stage.isEmpty()) return null;

        String measured = firstString(row, "waterLevelOn", "water_level_on", "measuredOn",
                "measured_on", "measurementTime", "measurement_time", "observationTime",
                "observation_time", "observedAt", "observed_at", "datetime", "timestamp", "_measurementTime");
        long measuredAt = parseTime(measured);
        if (measuredAt <= 0L || now - measuredAt > MAX_AGE_MS || measuredAt - now > FUTURE_TOLERANCE_MS) {
            return null;
        }

        String stationId = firstString(row, "stationSeriesId", "station_series_id",
                "stationId", "station_id", "stationIndex", "station_index", "id");
        String stationName = firstString(row, "station_name", "stationName", "title", "name");
        String riverName = firstString(row, "river_name", "riverName", "river");
        if (stationName.isEmpty()) stationName = riverName.isEmpty() ? "Official river station" : riverName;
        if (riverName.isEmpty()) riverName = riverFromStationTitle(stationName);
        if (stationId.isEmpty()) {
            stationId = stationName + "@" + String.format(Locale.US, "%.5f,%.5f", lat, lon);
        }

        RiverShape affected = bestMatchedRiver(riverShapes, riverName, stationName, lat, lon);
        if (affected == null) return null;
        double distance = distanceToRiverKm(homeLat, homeLon, affected);
        if (!Double.isFinite(distance) || distance > RADIUS_KM) return null;

        return new Hazard(stage, stationId, stationName,
                affected.name == null || affected.name.isEmpty() ? riverName : affected.name,
                distance, level, warning, danger, measuredAt);
    }

    private static List<RiverShape> loadRiverShapes(Context app) throws Exception {
        String raw;
        try { raw = readAsset(app, "data/nepal-waterways-tiles/overview.json"); }
        catch (Exception e) { raw = readAsset(app, "data/nepal-waterways-snapshot.json"); }
        JSONObject root = new JSONObject(raw);
        JSONArray ways = root.optJSONArray("waterways");
        List<RiverShape> out = new ArrayList<>();
        if (ways == null) return out;
        for (int i = 0; i < ways.length(); i++) {
            JSONObject w = ways.optJSONObject(i);
            if (w == null) continue;
            JSONArray pts = w.optJSONArray("pts");
            if (pts == null || pts.length() < 2) continue;
            String name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"));
            String key = canonicalRiverName(name);
            if (key.isEmpty()) continue;
            RiverShape shape = new RiverShape();
            shape.name = name;
            shape.key = key;
            for (int j = 0; j < pts.length(); j++) {
                JSONArray p = pts.optJSONArray(j);
                if (p == null || p.length() < 2) continue;
                double lo = p.optDouble(0, Double.NaN), la = p.optDouble(1, Double.NaN);
                if (Double.isFinite(la) && Double.isFinite(lo) && insideNepalLoose(la, lo)) {
                    shape.points.add(new double[]{lo, la});
                }
            }
            if (shape.points.size() >= 2) out.add(shape);
        }
        return out;
    }

    private static String readAsset(Context app, String path) throws Exception {
        try (InputStream in = app.getAssets().open(path);
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder b = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) b.append(line);
            return b.toString();
        }
    }

    private static RiverShape bestMatchedRiver(List<RiverShape> shapes, String riverName,
                                                String stationName, double stationLat, double stationLon) {
        String wanted = canonicalRiverName(riverName);
        if (wanted.isEmpty()) wanted = canonicalRiverName(riverFromStationTitle(stationName));
        if (wanted.isEmpty()) return null;
        RiverShape best = null;
        double bestDistance = Double.POSITIVE_INFINITY;
        for (RiverShape shape : shapes) {
            if (!sameRiverKey(wanted, shape.key)) continue;
            double d = distanceToRiverKm(stationLat, stationLon, shape);
            if (Double.isFinite(d) && d <= 8d && d < bestDistance) {
                best = shape;
                bestDistance = d;
            }
        }
        return best;
    }

    private static boolean sameRiverKey(String a, String b) {
        if (a == null || b == null || a.isEmpty() || b.isEmpty()) return false;
        if (a.equals(b)) return true;
        int min = Math.min(a.length(), b.length());
        return min >= 5 && (a.contains(b) || b.contains(a));
    }

    private static String riverFromStationTitle(String value) {
        if (value == null) return "";
        String s = value.trim();
        String lower = s.toLowerCase(Locale.ROOT);
        int at = lower.indexOf(" at ");
        if (at > 0) s = s.substring(0, at);
        return s;
    }

    private static String canonicalRiverName(String value) {
        String s = riverFromStationTitle(value).toLowerCase(Locale.ROOT);
        s = s.replace("river", "").replace("khola", "").replace("nadi", "")
                .replace("nadhi", "").replace("stream", "")
                .replace("नदी", "").replace("खोला", "");
        return s.replaceAll("[^a-z0-9\\p{L}]", "");
    }

    private static String firstNonEmpty(String... values) {
        for (String value : values) if (value != null && !value.trim().isEmpty()) return value.trim();
        return "";
    }

    private static double distanceToRiverKm(double lat, double lon, RiverShape shape) {
        if (shape == null || shape.points.size() < 2) return Double.NaN;
        double best = Double.POSITIVE_INFINITY;
        for (int i = 0; i < shape.points.size() - 1; i++) {
            double[] a = shape.points.get(i), b = shape.points.get(i + 1);
            double d = pointSegmentKm(lat, lon, a[1], a[0], b[1], b[0]);
            if (d < best) best = d;
        }
        return best;
    }

    private static double pointSegmentKm(double lat, double lon,
                                         double lat1, double lon1, double lat2, double lon2) {
        double cos = Math.cos(Math.toRadians(lat));
        double x1 = (lon1 - lon) * 111.320d * cos, y1 = (lat1 - lat) * 110.574d;
        double x2 = (lon2 - lon) * 111.320d * cos, y2 = (lat2 - lat) * 110.574d;
        double dx = x2 - x1, dy = y2 - y1;
        double len2 = dx * dx + dy * dy;
        double t = len2 <= 1e-12d ? 0d : -(x1 * dx + y1 * dy) / len2;
        t = Math.max(0d, Math.min(1d, t));
        double x = x1 + t * dx, y = y1 + t * dy;
        return Math.sqrt(x * x + y * y);
    }

    private boolean claim(Hazard hazard, long now) {
        SharedPreferences guard = getApplicationContext().getSharedPreferences(PUSH_PREFS, Context.MODE_PRIVATE);
        String key = "river_" + Integer.toHexString(hazard.stationId.hashCode());
        String previousStage = guard.getString(key + "_stage", "");
        double previousLevel = Double.longBitsToDouble(guard.getLong(
                key + "_level", Double.doubleToRawLongBits(Double.NaN)));
        long previousAt = guard.getLong(key + "_at", 0L);

        boolean stageChanged = !hazard.stage.equals(previousStage);
        boolean escalated = "danger".equals(hazard.stage) && !"danger".equals(previousStage);
        boolean materiallyRisen = Double.isFinite(hazard.level) && Double.isFinite(previousLevel)
                && hazard.level >= previousLevel + MATERIAL_RISE_METRES;
        long repeatAfter = "danger".equals(hazard.stage) ? DANGER_REPEAT_MS : WARNING_REPEAT_MS;
        boolean cooldownExpired = previousAt <= 0L || now - previousAt >= repeatAfter;

        if (!stageChanged && !materiallyRisen && !cooldownExpired) return false;
        if (!escalated && "warning".equals(hazard.stage) && "danger".equals(previousStage)
                && !materiallyRisen && !cooldownExpired) return false;

        SharedPreferences.Editor edit = guard.edit()
                .putString(key + "_stage", hazard.stage)
                .putLong(key + "_at", now);
        if (Double.isFinite(hazard.level)) {
            edit.putLong(key + "_level", Double.doubleToRawLongBits(hazard.level));
        }
        edit.apply();
        return true;
    }

    private void notifyHazard(Hazard hazard) {
        Context app = getApplicationContext();
        NotificationManager manager = app.getSystemService(NotificationManager.class);
        if (manager == null) return;

        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                    "Nearby river and Nepal alerts", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Fresh official Warning/Danger within 2 km of the affected river geometry");
            channel.enableVibration(true);
            Uri sound = android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI;
            AudioAttributes audio = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
            channel.setSound(sound, audio);
            manager.createNotificationChannel(channel);
        }

        String title = "danger".equals(hazard.stage)
                ? "🚨 नजिकको नदी खतरा चेतावनी"
                : "⚠️ नजिकको नदी चेतावनी";
        StringBuilder body = new StringBuilder(hazard.riverName)
                .append(" • affected river ")
                .append(String.format(Locale.US, "%.1f km", hazard.distanceKm));
        if (Double.isFinite(hazard.level)) {
            body.append(" • ").append(String.format(Locale.US, "%.2f m", hazard.level));
        }
        body.append(" • BIPAD/DHM official");

        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        int requestCode = 7200 + Math.abs(hazard.stationId.hashCode() % 500);
        PendingIntent open = PendingIntent.getActivity(app, requestCode, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(app, CHANNEL_ID)
                : new android.app.Notification.Builder(app);
        android.app.Notification notification = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(body.toString())
                .setStyle(new android.app.Notification.BigTextStyle().bigText(body.toString()))
                .setAutoCancel(true)
                .setContentIntent(open)
                .setSound(Build.VERSION.SDK_INT < 26 ? android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI : null)
                .build();
        manager.notify(requestCode, notification);
    }

    private static double firstNumber(JSONObject o, String... keys) {
        for (String key : keys) {
            if (!o.has(key) || o.isNull(key)) continue;
            Object raw = o.opt(key);
            if (raw instanceof Number) {
                double n = ((Number) raw).doubleValue();
                if (Double.isFinite(n)) return n;
            }
            try {
                double n = Double.parseDouble(String.valueOf(raw).trim());
                if (Double.isFinite(n)) return n;
            } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    private static String firstString(JSONObject o, String... keys) {
        for (String key : keys) {
            if (!o.has(key) || o.isNull(key)) continue;
            String value = String.valueOf(o.opt(key)).trim();
            if (!value.isEmpty() && !"null".equalsIgnoreCase(value)) return value;
        }
        return "";
    }

    private static long parseTime(String value) {
        if (value == null || value.trim().isEmpty()) return -1L;
        String s = value.trim();
        try {
            long n = Long.parseLong(s);
            return n < 10_000_000_000L ? n * 1000L : n;
        } catch (Exception ignored) {}
        try { return Instant.parse(s).toEpochMilli(); } catch (Exception ignored) {}
        try { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return ZonedDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try {
            return LocalDateTime.parse(s.replace(' ', 'T'), DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                    .atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();
        } catch (Exception ignored) { return -1L; }
    }

    private static boolean insideNepal(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon)
                && lat >= 26.2d && lat <= 30.5d && lon >= 80d && lon <= 88.35d;
    }

    private static boolean insideNepalLoose(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon)
                && lat >= 25.4d && lat <= 31.15d && lon >= 79.2d && lon <= 89.15d;
    }
}
