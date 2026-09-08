package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.os.SystemClock;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** Additive, read-only nearby danger alert layer. Existing FloodSafe river/map code is untouched. */
public final class FloodDangerMonitorService extends Service implements LocationListener {
    static final String PREFS = "floodsafe-danger-monitor-v1";
    private static final String ACTIVE_KEY = "active_nearby_danger";
    private static final String MONITOR_CHANNEL = "flood_danger_monitor";
    private static final String DANGER_CHANNEL = "official_flood_danger";
    private static final int FOREGROUND_ID = 73101;
    private static final long POLL_MS = 45_000L;
    private static final long FRESH_MS = 10 * 60_000L;
    private static final long FUTURE_ALLOW_MS = 5 * 60_000L;
    private static final double ALERT_RADIUS_KM = 10.0;
    private static final String FEED =
            "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";

    private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();
    private volatile boolean scheduled;
    private volatile boolean checking;
    private LocationManager locationManager;

    public static void start(Context context) {
        try {
            Intent service = new Intent(context, FloodDangerMonitorService.class);
            if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(service);
            else context.startService(service);
        } catch (RuntimeException ignored) {}
    }

    @Override public void onCreate() {
        super.onCreate();
        createChannels();
        promoteForeground();
        startLocationUpdatesIfAllowed();
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        promoteForeground();
        startLocationUpdatesIfAllowed();
        if (!scheduled) {
            scheduled = true;
            executor.scheduleWithFixedDelay(this::checkSafely, 0, POLL_MS, TimeUnit.MILLISECONDS);
        }
        return START_STICKY;
    }

    @Override public IBinder onBind(Intent intent) { return null; }

    private void createChannels() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (nm == null) return;

        NotificationChannel monitor = new NotificationChannel(
                MONITOR_CHANNEL, "Flood danger monitoring", NotificationManager.IMPORTANCE_LOW);
        monitor.setDescription("Silent official river danger monitoring");
        monitor.setSound(null, null);
        monitor.enableVibration(false);
        monitor.setShowBadge(false);
        nm.createNotificationChannel(monitor);

        NotificationChannel danger = new NotificationChannel(
                DANGER_CHANNEL, "Official nearby flood danger", NotificationManager.IMPORTANCE_HIGH);
        danger.setDescription("Nearby fresh BIPAD/DHM river danger alerts");
        danger.enableVibration(true);
        danger.setVibrationPattern(new long[]{0, 280, 170, 280});
        AudioAttributes attrs = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build();
        danger.setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION), attrs);
        nm.createNotificationChannel(danger);
    }

    private Notification monitorNotification() {
        Intent launch = new Intent(this, VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, FOREGROUND_ID, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, MONITOR_CHANNEL)
                : new Notification.Builder(this);
        return b.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle("FloodSafe Nepal")
                .setContentText("नजिकको आधिकारिक बाढी खतरा निगरानी सक्रिय छ")
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setContentIntent(open)
                .build();
    }

    private void promoteForeground() {
        Notification n = monitorNotification();
        if (Build.VERSION.SDK_INT >= 29) {
            int type = ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC;
            if (hasLocationPermission()) type |= ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION;
            try {
                startForeground(FOREGROUND_ID, n, type);
                return;
            } catch (RuntimeException ignored) {}
        }
        try { startForeground(FOREGROUND_ID, n); } catch (RuntimeException ignored) {}
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void startLocationUpdatesIfAllowed() {
        SharedPreferences p = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
        if (!p.getBoolean("follow_device", false) || !hasLocationPermission()) return;
        if (locationManager == null) locationManager = getSystemService(LocationManager.class);
        if (locationManager == null) return;
        try {
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER))
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 60_000L, 100f, this);
        } catch (RuntimeException ignored) {}
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER))
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 60_000L, 100f, this);
        } catch (RuntimeException ignored) {}
    }

    @Override public void onLocationChanged(Location location) {
        if (location == null) return;
        double lat = location.getLatitude(), lon = location.getLongitude();
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return;
        getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit()
                .putLong("lat", Double.doubleToRawLongBits(lat))
                .putLong("lon", Double.doubleToRawLongBits(lon))
                .apply();
    }
    @Override public void onProviderEnabled(String provider) {}
    @Override public void onProviderDisabled(String provider) {}
    @Override public void onStatusChanged(String provider, int status, Bundle extras) {}

    private void checkSafely() {
        if (checking) return;
        checking = true;
        try { checkNow(); } catch (Exception ignored) {} finally { checking = false; }
    }

    private void checkNow() throws Exception {
        Point user = monitoringPoint();
        if (user == null || !insideNepal(user.lat, user.lon)) return;
        JSONArray rows = fetchJson(FEED).optJSONArray("results");
        if (rows == null) return;

        long now = System.currentTimeMillis();
        SharedPreferences dangerPrefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        Set<String> previous = new HashSet<>(dangerPrefs.getStringSet(ACTIVE_KEY, new HashSet<>()));
        Set<String> activeNearby = new HashSet<>();
        List<DangerStation> freshEntries = new ArrayList<>();

        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            DangerStation s = row == null ? null : dangerStation(row, now, user);
            if (s == null || s.distanceKm > ALERT_RADIUS_KM) continue;
            activeNearby.add(s.key);
            if (!previous.contains(s.key)) freshEntries.add(s);
        }

        dangerPrefs.edit().putStringSet(ACTIVE_KEY, activeNearby).putLong("last_check_ms", now).apply();
        for (DangerStation s : freshEntries) notifyDanger(s);
    }

    private Point monitoringPoint() {
        SharedPreferences p = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
        if (!p.contains("lat") || !p.contains("lon")) return null;
        double lat = Double.longBitsToDouble(p.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(p.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        return Double.isFinite(lat) && Double.isFinite(lon) ? new Point(lat, lon) : null;
    }

    private DangerStation dangerStation(JSONObject row, long now, Point user) {
        Double level = number(row, "waterLevel", "water_level", "currentWaterLevel", "level", "value");
        Double danger = number(row, "dangerLevel", "danger_level", "dangerThreshold", "danger_threshold");
        String status = text(row, "status", "status_name", "statusText", "alertStatus", "riskLevel");
        long measuredAt = parseTime(text(row, "waterLevelOn", "water_level_on", "measuredOn",
                "measurementTime", "observationTime", "observedAt", "datetime", "timestamp"));
        if (measuredAt <= 0 || measuredAt > now + FUTURE_ALLOW_MS || now - measuredAt > FRESH_MS) return null;

        boolean crossed = level != null && danger != null && level >= danger;
        String upper = status == null ? "" : status.toUpperCase(Locale.ROOT);
        if (!crossed && !upper.contains("DANGER") && !upper.contains("RED")) return null;

        Double lat = number(row, "latitude", "lat", "stationLatitude");
        Double lon = number(row, "longitude", "lon", "lng", "stationLongitude");
        if (lat == null || lon == null || !insideNepal(lat, lon)) return null;

        String name = text(row, "title", "name", "stationName", "station_name", "riverName", "river_name");
        if (name == null || name.isEmpty()) name = "नजिकको नदी स्टेशन";
        String key = text(row, "stationSeriesId", "station_series_id", "stationId", "station_id", "id");
        if (key == null || key.isEmpty()) key = "name:" + name + ":" + lat + ":" + lon;
        return new DangerStation(key, name, level, danger, measuredAt,
                distanceKm(user.lat, user.lon, lat, lon));
    }

    private void notifyDanger(DangerStation s) {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (nm == null) return;

        String dist = s.distanceKm < 1
                ? String.format(Locale.US, "%.0f मिटर", s.distanceKm * 1000)
                : String.format(Locale.US, "%.1f km", s.distanceKm);
        StringBuilder body = new StringBuilder(s.name)
                .append(" तपाईंको निगरानी स्थानबाट करिब ").append(dist).append(" टाढा छ। ");
        if (s.level != null) body.append("हालको जलस्तर ").append(fmt(s.level)).append(" मि. ");
        if (s.danger != null) body.append("खतरा तह ").append(fmt(s.danger)).append(" मि. ");
        body.append("मापन ").append(clock(s.measuredAt))
                .append("। नदी/खोला किनारबाट टाढा रहनुहोस् र सुरक्षित उच्च स्थानतर्फ जान तयार हुनुहोस्। स्रोत: BIPAD/DHM official.");

        Intent launch = new Intent(this, VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, s.key.hashCode(), launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, DANGER_CHANNEL)
                : new Notification.Builder(this);
        Notification n = b.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle("🚨 नजिकै आधिकारिक बाढी खतरा")
                .setContentText(body.toString())
                .setStyle(new Notification.BigTextStyle().bigText(body.toString()))
                .setCategory(Notification.CATEGORY_ALARM)
                .setPriority(Notification.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setContentIntent(open)
                .build();
        nm.notify(0x5f000000 ^ s.key.hashCode(), n);
    }

    private static JSONObject fetchJson(String base) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(base + "?_danger=" + SystemClock.elapsedRealtime()).openConnection();
        c.setRequestMethod("GET");
        c.setConnectTimeout(9000);
        c.setReadTimeout(12000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache");
        int code = c.getResponseCode();
        InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
        if (in == null) { c.disconnect(); throw new IllegalStateException("HTTP " + code); }
        StringBuilder out = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            for (String line; (line = r.readLine()) != null;) {
                if (out.length() > 5_000_000) throw new IllegalStateException("Feed too large");
                out.append(line);
            }
        } finally { c.disconnect(); }
        if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
        return new JSONObject(out.toString());
    }

    private static Double number(JSONObject o, String... keys) {
        for (String key : keys) {
            Object v = o.opt(key);
            if (v == null || v == JSONObject.NULL) continue;
            try {
                double n = v instanceof Number ? ((Number) v).doubleValue()
                        : Double.parseDouble(String.valueOf(v).trim());
                if (Double.isFinite(n)) return n;
            } catch (RuntimeException ignored) {}
        }
        return null;
    }

    private static String text(JSONObject o, String... keys) {
        for (String key : keys) {
            Object v = o.opt(key);
            if (v == null || v == JSONObject.NULL) continue;
            String s = String.valueOf(v).trim();
            if (!s.isEmpty()) return s;
        }
        return null;
    }

    private static long parseTime(String value) {
        if (value == null || value.isEmpty()) return 0;
        try {
            String v = value.trim();
            if (v.matches("^\\d{10}$")) return Long.parseLong(v) * 1000L;
            if (v.matches("^\\d{13}$")) return Long.parseLong(v);
            if (Build.VERSION.SDK_INT >= 26) return java.time.Instant.parse(v).toEpochMilli();
        } catch (RuntimeException ignored) {}
        String[] patterns = {"yyyy-MM-dd'T'HH:mm:ss.SSSXXX", "yyyy-MM-dd'T'HH:mm:ssXXX",
                "yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd'T'HH:mm:ss"};
        for (String pattern : patterns) {
            try {
                SimpleDateFormat f = new SimpleDateFormat(pattern, Locale.US);
                if (!pattern.contains("XXX")) f.setTimeZone(TimeZone.getTimeZone("Asia/Kathmandu"));
                Date d = f.parse(value);
                if (d != null) return d.getTime();
            } catch (Exception ignored) {}
        }
        return 0;
    }

    private static String clock(long ms) {
        SimpleDateFormat f = new SimpleDateFormat("HH:mm", new Locale("ne", "NP"));
        f.setTimeZone(TimeZone.getTimeZone("Asia/Kathmandu"));
        return f.format(new Date(ms)) + " NPT";
    }

    private static String fmt(double n) { return String.format(Locale.US, "%.2f", n); }
    private static boolean insideNepal(double lat, double lon) {
        return lat >= 26.0 && lat <= 31.0 && lon >= 79.5 && lon <= 89.0;
    }
    private static double distanceKm(double a, double b, double c, double d) {
        double r = 6371.0088, p1 = Math.toRadians(a), p2 = Math.toRadians(c);
        double dp = Math.toRadians(c - a), dl = Math.toRadians(d - b);
        double q = Math.sin(dp / 2) * Math.sin(dp / 2)
                + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2);
        return 2 * r * Math.asin(Math.sqrt(q));
    }

    @Override public void onDestroy() {
        executor.shutdownNow();
        if (locationManager != null) {
            try { locationManager.removeUpdates(this); } catch (RuntimeException ignored) {}
        }
        super.onDestroy();
    }

    private static final class Point {
        final double lat, lon;
        Point(double lat, double lon) { this.lat = lat; this.lon = lon; }
    }
    private static final class DangerStation {
        final String key, name;
        final Double level, danger;
        final long measuredAt;
        final double distanceKm;
        DangerStation(String key, String name, Double level, Double danger, long measuredAt, double distanceKm) {
            this.key = key; this.name = name; this.level = level; this.danger = danger;
            this.measuredAt = measuredAt; this.distanceKm = distanceKm;
        }
    }
}
