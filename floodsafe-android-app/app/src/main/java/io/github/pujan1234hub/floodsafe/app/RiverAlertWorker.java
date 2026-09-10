package io.github.pujan1234hub.floodsafe.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
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
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/**
 * Closed-app fallback for nearby official river warnings. The preferred path is
 * Firebase push; this worker independently checks the FloodSafe BIPAD/DHM mirror
 * so a missing server push credential cannot leave Android users without alerts.
 * Android WorkManager enforces a 15-minute minimum periodic interval.
 */
public final class RiverAlertWorker extends Worker {
    private static final String ENDPOINT =
            "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String CHANNEL_ID = "official_nepal_alerts_v2";
    private static final String PUSH_PREFS = "floodsafe_push_guard";
    private static final double RADIUS_KM = 2d;
    private static final long MAX_AGE_MS = 20L * 60L * 1000L;
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

        try {
            JSONObject root = fetch();
            JSONArray rows = root.optJSONArray("results");
            if (rows == null) return Result.retry();

            long now = System.currentTimeMillis();
            List<Hazard> hazards = new ArrayList<>();
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.optJSONObject(i);
                if (row == null) continue;
                Hazard hazard = hazard(row, homeLat, homeLon, now);
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
        HttpURLConnection connection = (HttpURLConnection) new URL(ENDPOINT).openConnection();
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(20000);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-cache");
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
        final String name;
        final double distanceKm;
        final double level;
        final double warning;
        final double danger;
        final long measuredAt;

        Hazard(String stage, String stationId, String name, double distanceKm,
               double level, double warning, double danger, long measuredAt) {
            this.stage = stage;
            this.stationId = stationId;
            this.name = name;
            this.distanceKm = distanceKm;
            this.level = level;
            this.warning = warning;
            this.danger = danger;
            this.measuredAt = measuredAt;
        }
    }

    private static Hazard hazard(JSONObject row, double homeLat, double homeLon, long now) {
        double lat = firstNumber(row, "latitude", "lat", "stationLatitude", "station_latitude");
        double lon = firstNumber(row, "longitude", "lon", "lng", "stationLongitude", "station_longitude");
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return null;
        if (!insideNepal(lat, lon)) return null;

        double distance = haversineKm(homeLat, homeLon, lat, lon);
        if (!Double.isFinite(distance) || distance > RADIUS_KM) return null;

        double level = firstNumber(row, "waterLevel", "water_level", "currentWaterLevel",
                "current_water_level", "currentLevel", "current_level", "level", "value", "_lastWaterLevel");
        double warning = firstNumber(row, "warningLevel", "warning_level", "warningThreshold",
                "warning_threshold", "_lastWarningLevel");
        double danger = firstNumber(row, "dangerLevel", "danger_level", "dangerThreshold",
                "danger_threshold", "_lastDangerLevel");
        String official = firstString(row, "status", "status_name", "alertStatus", "alert_status",
                "riskLevel", "risk_level").toUpperCase(Locale.ROOT);

        String stage = "";
        if (Double.isFinite(level) && Double.isFinite(danger) && danger > 0d && level >= danger) {
            stage = "danger";
        } else if (official.contains("DANGER") || official.contains("RED")) {
            stage = "danger";
        } else if (Double.isFinite(level) && Double.isFinite(warning) && warning > 0d && level >= warning) {
            stage = "warning";
        } else if (official.contains("WARNING") || official.contains("ORANGE")) {
            stage = "warning";
        }
        if (stage.isEmpty()) return null;

        String measured = firstString(row, "waterLevelOn", "water_level_on", "measuredOn",
                "measured_on", "measurementTime", "measurement_time", "observationTime",
                "observation_time", "observedAt", "observed_at", "datetime", "timestamp");
        long measuredAt = parseTime(measured);
        if (measuredAt <= 0L || now - measuredAt > MAX_AGE_MS || measuredAt - now > FUTURE_TOLERANCE_MS) {
            return null;
        }

        String stationId = firstString(row, "stationSeriesId", "station_series_id",
                "stationId", "station_id", "stationIndex", "station_index", "id");
        String name = firstString(row, "river_name", "riverName", "station_name", "stationName",
                "title", "name");
        if (name.isEmpty()) name = "Official river station";
        if (stationId.isEmpty()) stationId = name + "@" + String.format(Locale.US, "%.5f,%.5f", lat, lon);

        return new Hazard(stage, stationId, name, distance, level, warning, danger, measuredAt);
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
            channel.setDescription("Nearby official river warning/danger and verified Nepal alerts");
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }

        String title = "danger".equals(hazard.stage)
                ? "🚨 नजिकको नदी खतरा चेतावनी"
                : "⚠️ नजिकको नदी चेतावनी";
        StringBuilder body = new StringBuilder(hazard.name)
                .append(" • ").append(String.format(Locale.US, "%.1f km", hazard.distanceKm));
        if (Double.isFinite(hazard.level)) {
            body.append(" • ").append(String.format(Locale.US, "%.2f m", hazard.level));
        }
        body.append(" • BIPAD/DHM official");

        Intent launch = new Intent(app, VoiceMainActivity.class)
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
            } catch (Exception ignored) { }
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
        } catch (Exception ignored) { }
        try { return Instant.parse(s).toEpochMilli(); }
        catch (Exception ignored) { }
        try { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); }
        catch (Exception ignored) { }
        try { return ZonedDateTime.parse(s).toInstant().toEpochMilli(); }
        catch (Exception ignored) { }
        try {
            return LocalDateTime.parse(s.replace(' ', 'T'), DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                    .atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();
        } catch (Exception ignored) { return -1L; }
    }

    private static boolean insideNepal(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon)
                && lat >= 26.2d && lat <= 30.5d && lon >= 80d && lon <= 88.35d;
    }

    private static double haversineKm(double lat1, double lon1, double lat2, double lon2) {
        double r = 6371d;
        double dLat = Math.toRadians(lat2 - lat1), dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2d) * Math.sin(dLat / 2d)
                + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                * Math.sin(dLon / 2d) * Math.sin(dLon / 2d);
        return 2d * r * Math.asin(Math.sqrt(a));
    }
}