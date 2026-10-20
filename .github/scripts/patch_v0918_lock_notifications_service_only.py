from pathlib import Path

J = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app')
service = J / 'FloodMonitorService.java'
s = service.read_text(encoding='utf-8')

# Notification-only hook inside the already-existing foreground monitoring service.
if 'LockedRainNotificationMonitor lockedRainNotificationMonitor;' not in s:
    s = s.replace(
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;',
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;\n    private LockedRainNotificationMonitor lockedRainNotificationMonitor; // V0918_LOCK_NOTIFICATION_ONLY',
        1,
    )
    s = s.replace(
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);',
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);\n        lockedRainNotificationMonitor = new LockedRainNotificationMonitor(this);',
        1,
    )
    s = s.replace(
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();',
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();\n        if (lockedRainNotificationMonitor != null) lockedRainNotificationMonitor.start(); // V0918_LOCK_NOTIFICATION_ONLY_START',
        1,
    )
    marker = '    @Override public void onDestroy() {\n'
    if marker not in s:
        raise SystemExit('FloodMonitorService onDestroy marker missing')
    s = s.replace(
        marker,
        marker + '        if (lockedRainNotificationMonitor != null) {\n'
                 '            try { lockedRainNotificationMonitor.stop(); } catch (RuntimeException ignored) { }\n'
                 '            lockedRainNotificationMonitor = null;\n'
                 '        } // V0918_LOCK_NOTIFICATION_ONLY_STOP\n',
        1,
    )
service.write_text(s, encoding='utf-8')

# New class only. It reads the SAME saved current location but does not touch UI, map, cloud,
# river geometry, language state, SATHI, or shared safety policy.
(J / 'LockedRainNotificationMonitor.java').write_text(r'''package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Notification-only lock-screen heartbeat attached to FloodSafe's existing foreground service.
 * This intentionally has no UI/map/weather-overlay/cloud-marker code.
 */
final class LockedRainNotificationMonitor {
    private static final long CHECK_MS = 2L * 60L * 1000L;
    private static final long MAX_LOCATION_AGE_MS = 2L * 60L * 60L * 1000L;
    private static final double WET_MM = 0.10d;
    private static final int LOOKAHEAD_MINUTES = 35;
    private static final String CHANNEL_ID = "local_rain_alerts_v2";
    private static final int NOTIFICATION_ID = 7421;

    private final Context app;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final AtomicBoolean busy = new AtomicBoolean(false);
    private volatile boolean running;

    LockedRainNotificationMonitor(Context context) {
        app = context.getApplicationContext();
    }

    void start() {
        if (running) return;
        running = true;
        ensureChannel();
        main.postDelayed(tick, 8_000L);
    }

    void stop() {
        running = false;
        main.removeCallbacks(tick);
        io.shutdownNow();
    }

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            if (!running) return;
            if (busy.compareAndSet(false, true)) {
                io.execute(() -> {
                    try { checkWeatherEvent(); } catch (Exception ignored) { }
                    finally { busy.set(false); }
                });
            }
            main.postDelayed(this, CHECK_MS);
        }
    };

    private void checkWeatherEvent() throws Exception {
        SharedPreferences prefs = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("enabled", false)) return;
        if (Build.VERSION.SDK_INT >= 33
                && app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;

        double lat = Double.longBitsToDouble(prefs.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(prefs.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        long locationTime = prefs.getLong("location_time", 0L);
        long nowMs = System.currentTimeMillis();
        if (!validLockedLocation(lat, lon, locationTime, nowMs)) return;

        JSONObject data = fetch(lat, lon);
        JSONObject current = data.optJSONObject("current");
        double currentMm = max(value(current, "precipitation"), value(current, "rain"), value(current, "showers"));
        int weatherCode = current == null ? -1 : current.optInt("weather_code", -1);
        boolean rainingNow = currentMm >= WET_MM || wetCode(weatherCode);

        ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));
        ZonedDateTime now = ZonedDateTime.now(zone);
        RainSlot next = firstWetSlot(data.optJSONObject("minutely_15"), now);

        boolean known = prefs.getBoolean("locked_rain_state_known_v1", false);
        boolean previous = prefs.getBoolean("locked_raining_v1", false);
        if (!known) {
            prefs.edit().putBoolean("locked_rain_state_known_v1", true)
                    .putBoolean("locked_raining_v1", rainingNow).apply();
        } else if (previous != rainingNow) {
            prefs.edit().putBoolean("locked_raining_v1", rainingNow)
                    .putLong("last_alert", nowMs).apply();
            if (rainingNow) notifyHigh("🌧️ वर्षा सुरु भएको छ", "हालको स्थानमा वर्षा सुरु भएको देखिन्छ।");
            else notifyHigh("🌤️ वर्षा रोकिएको छ", "हालको स्थानमा वर्षा रोकिएको देखिन्छ।");
        }

        if (!rainingNow && next != null) {
            long lead = Math.max(0L, java.time.Duration.between(now, next.start).toMinutes());
            if (lead <= LOOKAHEAD_MINUTES) {
                String key = next.start.withSecond(0).withNano(0).toString();
                if (!key.equals(prefs.getString("locked_upcoming_rain_key_v1", ""))) {
                    prefs.edit().putString("locked_upcoming_rain_key_v1", key)
                            .putLong("last_alert", nowMs).apply();
                    notifyHigh("☔ वर्षा सुरु हुन सक्छ", "करिब " + Math.max(1L, lead) + " मिनेटभित्र वर्षाको संकेत छ।");
                }
            }
        }
    }

    private static boolean validLockedLocation(double lat, double lon, long at, long now) {
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return false;
        if (lat < -90d || lat > 90d || lon < -180d || lon > 180d || at <= 0L) return false;
        long age = now - at;
        return age >= -30_000L && age <= MAX_LOCATION_AGE_MS;
    }

    private JSONObject fetch(double lat, double lon) throws Exception {
        String query = "latitude=" + URLEncoder.encode(String.valueOf(lat), "UTF-8")
                + "&longitude=" + URLEncoder.encode(String.valueOf(lon), "UTF-8")
                + "&current=precipitation,rain,showers,weather_code"
                + "&minutely_15=precipitation,rain,showers&forecast_hours=2&timezone=auto";
        HttpURLConnection c = (HttpURLConnection) new URL("https://api.open-meteo.com/v1/forecast?" + query).openConnection();
        c.setConnectTimeout(10_000);
        c.setReadTimeout(10_000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache");
        if (c.getResponseCode() != 200) { c.disconnect(); throw new IllegalStateException("weather http"); }
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line; while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static final class RainSlot {
        final ZonedDateTime start;
        RainSlot(ZonedDateTime start) { this.start = start; }
    }

    private static RainSlot firstWetSlot(JSONObject block, ZonedDateTime now) {
        if (block == null) return null;
        JSONArray times = block.optJSONArray("time");
        JSONArray precipitation = block.optJSONArray("precipitation");
        JSONArray rain = block.optJSONArray("rain");
        JSONArray showers = block.optJSONArray("showers");
        if (times == null) return null;
        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.plusMinutes(15).isBefore(now)) continue;
            double mm = max(at(precipitation, i), at(rain, i), at(showers, i));
            if (mm >= WET_MM) return new RainSlot(slot);
        }
        return null;
    }

    private void ensureChannel() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager n = app.getSystemService(NotificationManager.class);
        if (n == null) return;
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "Rain and local weather alerts", NotificationManager.IMPORTANCE_HIGH);
        channel.enableVibration(true);
        channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        n.createNotificationChannel(channel);
    }

    private void notifyHigh(String title, String text) {
        NotificationManager n = app.getSystemService(NotificationManager.class);
        if (n == null) return;
        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(app, NOTIFICATION_ID, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(app, CHANNEL_ID) : new Notification.Builder(app);
        Notification notification = b.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title).setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setContentIntent(open).setAutoCancel(true)
                .setPriority(Notification.PRIORITY_HIGH)
                .setVisibility(Notification.VISIBILITY_PUBLIC).build();
        n.notify(NOTIFICATION_ID, notification);
    }

    private static ZonedDateTime parseSlot(String raw, ZoneId zone) {
        try { return LocalDateTime.parse(raw, DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(zone); }
        catch (Exception ignored) { return null; }
    }
    private static ZoneId safeZone(String id) { try { return ZoneId.of(id); } catch (Exception e) { return ZoneId.of("Asia/Kathmandu"); } }
    private static double value(JSONObject o, String key) { return o == null ? Double.NaN : number(o.opt(key)); }
    private static double at(JSONArray a, int i) { return a == null ? Double.NaN : number(a.opt(i)); }
    private static double number(Object v) { if (v instanceof Number) return ((Number)v).doubleValue(); try { return v == null ? Double.NaN : Double.parseDouble(String.valueOf(v)); } catch (Exception e) { return Double.NaN; } }
    private static double max(double... values) { double m = 0d; for (double v : values) if (Double.isFinite(v)) m = Math.max(m, v); return m; }
    private static boolean wetCode(int code) { return (code >= 51 && code <= 67) || (code >= 80 && code <= 82) || (code >= 95 && code <= 99); }
}
''', encoding='utf-8')

print('V0918_LOCK_NOTIFICATION_SERVICE_ONLY_OK')
