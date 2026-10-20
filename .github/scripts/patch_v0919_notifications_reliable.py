from pathlib import Path

J = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app')
service = J / 'FloodMonitorService.java'
s = service.read_text(encoding='utf-8')

# Notification-only reliability hook. Do not touch UI/map/cloud/SATHI/assets.
if 'ReliableNotificationMonitor reliableNotificationMonitor;' not in s:
    s = s.replace(
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;',
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;\n    private ReliableNotificationMonitor reliableNotificationMonitor; // V0919_NOTIFICATION_ONLY',
        1,
    )
    s = s.replace(
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);',
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);\n        reliableNotificationMonitor = new ReliableNotificationMonitor(this);',
        1,
    )
    s = s.replace(
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();',
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();\n        if (reliableNotificationMonitor != null) reliableNotificationMonitor.start(); // V0919_NOTIFICATION_ONLY_START',
        1,
    )
    marker = '    @Override public void onDestroy() {\n'
    if marker not in s:
        raise SystemExit('FloodMonitorService onDestroy marker missing')
    s = s.replace(
        marker,
        marker + '        if (reliableNotificationMonitor != null) {\n'
                 '            try { reliableNotificationMonitor.stop(); } catch (RuntimeException ignored) { }\n'
                 '            reliableNotificationMonitor = null;\n'
                 '        } // V0919_NOTIFICATION_ONLY_STOP\n',
        1,
    )
service.write_text(s, encoding='utf-8')

(J / 'ReliableNotificationMonitor.java').write_text(r'''package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
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
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Notification-only reliability monitor attached to the already-existing foreground service.
 * It never changes map, river geometry, cloud rendering, SATHI, language UI or navigation.
 */
final class ReliableNotificationMonitor {
    private static final long CHECK_MS = 2L * 60L * 1000L;
    private static final long DIGEST_MS = 2L * 60L * 60L * 1000L;
    private static final long DEVICE_LOCATION_GRACE_MS = 24L * 60L * 60L * 1000L;
    private static final double WET_MM = 0.10d;
    private static final int LOOKAHEAD_MINUTES = 35;
    private static final String ALERT_CHANNEL = "floodsafe_weather_alerts_v4";
    private static final String DIGEST_CHANNEL = "floodsafe_weather_updates_v4";
    private static final int RAIN_NOTIFICATION_ID = 7421;
    private static final int DIGEST_NOTIFICATION_ID = 7422;
    private static final int STORM_NOTIFICATION_ID = 7423;

    private final Context app;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final AtomicBoolean busy = new AtomicBoolean(false);
    private volatile boolean running;

    ReliableNotificationMonitor(Context context) {
        app = context.getApplicationContext();
    }

    void start() {
        if (running) return;
        running = true;
        ensureChannels();
        main.postDelayed(tick, 5_000L);
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
                    try { checkNow(); } catch (Exception ignored) { }
                    finally { busy.set(false); }
                });
            }
            main.postDelayed(this, CHECK_MS);
        }
    };

    private void checkNow() throws Exception {
        SharedPreferences prefs = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("enabled", false)) return;
        if (!notificationPermissionGranted()) return;

        long nowMs = System.currentTimeMillis();
        LocationPoint point = resolveLocation(prefs, nowMs);
        if (point == null) return;

        JSONObject data = fetch(point.lat, point.lon);
        JSONObject current = data.optJSONObject("current");
        double currentMm = max(value(current, "precipitation"), value(current, "rain"), value(current, "showers"));
        double temperature = value(current, "temperature_2m");
        double apparent = value(current, "apparent_temperature");
        double humidity = value(current, "relative_humidity_2m");
        double wind = value(current, "wind_speed_10m");
        int weatherCode = current == null ? -1 : current.optInt("weather_code", -1);
        boolean rainingNow = currentMm >= WET_MM || wetCode(weatherCode);

        ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));
        ZonedDateTime now = ZonedDateTime.now(zone);
        RainSlot nextRain = firstWetSlot(data.optJSONObject("minutely_15"), now);
        HourWindow hours = nextHours(data.optJSONObject("hourly"), now);

        prefs.edit().putLong("reliable_notification_check_v2", nowMs).apply();
        handleRainState(prefs, rainingNow, nextRain, now, nowMs);
        handleStorm(prefs, weatherCode, hours, now, nowMs);
        handleDigest(prefs, temperature, apparent, humidity, wind, weatherCode, hours, rainingNow, nowMs);
    }

    private void handleRainState(SharedPreferences prefs, boolean rainingNow, RainSlot nextRain,
                                 ZonedDateTime now, long nowMs) {
        boolean known = prefs.getBoolean("reliable_rain_known_v2", false);
        boolean previous = prefs.getBoolean("reliable_raining_v2", false);
        if (!known) {
            prefs.edit().putBoolean("reliable_rain_known_v2", true)
                    .putBoolean("reliable_raining_v2", rainingNow).apply();
        } else if (previous != rainingNow) {
            prefs.edit().putBoolean("reliable_raining_v2", rainingNow)
                    .putLong("last_alert", nowMs).apply();
            if (rainingNow) {
                notifyHigh(RAIN_NOTIFICATION_ID, "🌧️ वर्षा सुरु भएको छ",
                        "हालको स्थानमा वर्षा सुरु भएको देखिन्छ।");
            } else {
                notifyHigh(RAIN_NOTIFICATION_ID, "🌤️ वर्षा रोकिएको छ",
                        "हालको स्थानमा वर्षा रोकिएको देखिन्छ।");
            }
        }

        if (!rainingNow && nextRain != null) {
            long lead = Math.max(0L, java.time.Duration.between(now, nextRain.start).toMinutes());
            if (lead <= LOOKAHEAD_MINUTES) {
                String key = nextRain.start.withSecond(0).withNano(0).toString();
                if (!key.equals(prefs.getString("reliable_upcoming_rain_key_v2", ""))) {
                    prefs.edit().putString("reliable_upcoming_rain_key_v2", key)
                            .putLong("last_alert", nowMs).apply();
                    notifyHigh(RAIN_NOTIFICATION_ID, "☔ वर्षा सुरु हुन सक्छ",
                            "करिब " + Math.max(1L, lead) + " मिनेटभित्र वर्षाको संकेत छ।");
                }
            }
        }
    }

    private void handleStorm(SharedPreferences prefs, int currentCode, HourWindow hours,
                             ZonedDateTime now, long nowMs) {
        boolean thunderNow = thunderCode(currentCode);
        boolean thunderSoon = hours != null && hours.thunderSoon;
        if (!thunderNow && !thunderSoon) return;
        String key = now.toLocalDate() + "T" + now.getHour() + ":" + (thunderNow ? "now" : "soon");
        if (key.equals(prefs.getString("reliable_thunder_key_v2", ""))) return;
        prefs.edit().putString("reliable_thunder_key_v2", key)
                .putLong("last_alert", nowMs).apply();
        if (thunderNow) {
            notifyHigh(STORM_NOTIFICATION_ID, "⛈️ चट्याङ / आँधीको संकेत",
                    "हालको स्थानमा चट्याङ वा आँधीको मौसम संकेत देखिएको छ। सुरक्षित ठाउँमा बस्नुहोस्।");
        } else {
            notifyHigh(STORM_NOTIFICATION_ID, "⛈️ चट्याङको सम्भावना",
                    "आगामी केही घण्टामा चट्याङ वा आँधीको संकेत देखिएको छ। मौसममा ध्यान दिनुहोस्।");
        }
    }

    private void handleDigest(SharedPreferences prefs, double temperature, double apparent,
                              double humidity, double wind, int weatherCode, HourWindow hours,
                              boolean rainingNow, long nowMs) {
        long last = prefs.getLong("reliable_weather_digest_v2_at", 0L);
        if (last > 0L && nowMs - last < DIGEST_MS) return;

        String title = rainingNow ? "🌧️ FloodSafe मौसम अपडेट" : "🌤️ FloodSafe मौसम अपडेट";
        StringBuilder text = new StringBuilder();
        if (Double.isFinite(temperature)) text.append("अहिले ").append(Math.round(temperature)).append("°C");
        String condition = conditionNepali(weatherCode);
        if (!condition.isEmpty()) appendPart(text, condition);
        if (Double.isFinite(apparent)) appendPart(text, "महसुस " + Math.round(apparent) + "°C");
        if (hours != null && hours.maxRainProbability >= 0) {
            appendPart(text, "आगामी ३ घण्टा वर्षा " + hours.maxRainProbability + "%");
        }
        if (hours != null && hours.rainMm > 0.05d) {
            appendPart(text, String.format(Locale.US, "करिब %.1f mm", hours.rainMm));
        }
        if (Double.isFinite(wind)) appendPart(text, "हावा " + Math.round(wind) + " km/h");
        if (Double.isFinite(humidity)) appendPart(text, "आर्द्रता " + Math.round(humidity) + "%");
        if (text.length() == 0) text.append("हालको स्थानको मौसम डेटा अपडेट भयो।");

        notifyDigest(title, text.toString());
        prefs.edit()
                .putLong("reliable_weather_digest_v2_at", nowMs)
                .putLong("last_weather_digest_at", nowMs)
                .apply();
    }

    private boolean notificationPermissionGranted() {
        return Build.VERSION.SDK_INT < 33
                || app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private static final class LocationPoint {
        final double lat;
        final double lon;
        final long time;
        LocationPoint(double lat, double lon, long time) {
            this.lat = lat; this.lon = lon; this.time = time;
        }
    }

    @SuppressLint("MissingPermission")
    private LocationPoint resolveLocation(SharedPreferences prefs, long now) {
        double lat = Double.longBitsToDouble(prefs.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(prefs.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        long at = prefs.getLong("location_time", 0L);
        boolean followDevice = prefs.getBoolean("follow_device", false);

        LocationPoint saved = validCoordinate(lat, lon)
                ? new LocationPoint(lat, lon, at > 0L ? at : now) : null;
        if (!followDevice) return saved;

        boolean locationGranted = app.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || app.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
        if (locationGranted) {
            LocationManager lm = app.getSystemService(LocationManager.class);
            Location best = null;
            if (lm != null) {
                for (String provider : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
                    try {
                        Location candidate = lm.getLastKnownLocation(provider);
                        if (candidate == null || !validCoordinate(candidate.getLatitude(), candidate.getLongitude())) continue;
                        if (best == null || candidate.getTime() > best.getTime()) best = candidate;
                    } catch (SecurityException | IllegalArgumentException ignored) { }
                }
            }
            if (best != null) {
                long bestTime = best.getTime() > 0L ? best.getTime() : now;
                long age = now - bestTime;
                if (age >= -5L * 60L * 1000L && age <= DEVICE_LOCATION_GRACE_MS) {
                    lat = best.getLatitude(); lon = best.getLongitude(); at = bestTime;
                    prefs.edit()
                            .putLong("lat", Double.doubleToRawLongBits(lat))
                            .putLong("lon", Double.doubleToRawLongBits(lon))
                            .putLong("location_time", at)
                            .putLong("device_lat", Double.doubleToRawLongBits(lat))
                            .putLong("device_lon", Double.doubleToRawLongBits(lon))
                            .putLong("device_location_time", at)
                            .apply();
                    saved = new LocationPoint(lat, lon, at);
                }
            }
        }

        if (saved == null) return null;
        long age = now - saved.time;
        if (age < -5L * 60L * 1000L || age > DEVICE_LOCATION_GRACE_MS) return null;
        return saved;
    }

    private static boolean validCoordinate(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon)
                && lat >= -90d && lat <= 90d && lon >= -180d && lon <= 180d;
    }

    private JSONObject fetch(double lat, double lon) throws Exception {
        String query = "latitude=" + URLEncoder.encode(String.valueOf(lat), "UTF-8")
                + "&longitude=" + URLEncoder.encode(String.valueOf(lon), "UTF-8")
                + "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m"
                + "&minutely_15=precipitation,rain,showers"
                + "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code"
                + "&forecast_hours=6&timezone=auto";
        HttpURLConnection c = (HttpURLConnection) new URL("https://api.open-meteo.com/v1/forecast?" + query).openConnection();
        c.setConnectTimeout(10_000);
        c.setReadTimeout(10_000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        c.setRequestProperty("Pragma", "no-cache");
        int code = c.getResponseCode();
        if (code != 200) { c.disconnect(); throw new IllegalStateException("weather http " + code); }
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

    private static final class HourWindow {
        int maxRainProbability = -1;
        double rainMm = 0d;
        boolean thunderSoon = false;
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

    private static HourWindow nextHours(JSONObject hourly, ZonedDateTime now) {
        HourWindow out = new HourWindow();
        if (hourly == null) return out;
        JSONArray times = hourly.optJSONArray("time");
        JSONArray probabilities = hourly.optJSONArray("precipitation_probability");
        JSONArray precipitation = hourly.optJSONArray("precipitation");
        JSONArray codes = hourly.optJSONArray("weather_code");
        if (times == null) return out;
        ZonedDateTime end = now.plusHours(3).plusMinutes(30);
        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.isBefore(now.minusMinutes(30)) || slot.isAfter(end)) continue;
            int probability = intAt(probabilities, i);
            if (probability >= 0) out.maxRainProbability = Math.max(out.maxRainProbability, probability);
            double mm = at(precipitation, i);
            if (Double.isFinite(mm)) out.rainMm += Math.max(0d, mm);
            int code = intAt(codes, i);
            if (thunderCode(code)) out.thunderSoon = true;
        }
        return out;
    }

    private void ensureChannels() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager n = app.getSystemService(NotificationManager.class);
        if (n == null) return;
        NotificationChannel alerts = new NotificationChannel(
                ALERT_CHANNEL, "Rain, thunder and safety alerts", NotificationManager.IMPORTANCE_HIGH);
        alerts.enableVibration(true);
        alerts.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        n.createNotificationChannel(alerts);
        NotificationChannel digest = new NotificationChannel(
                DIGEST_CHANNEL, "Two-hour weather updates", NotificationManager.IMPORTANCE_DEFAULT);
        digest.enableVibration(false);
        digest.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        n.createNotificationChannel(digest);
    }

    private void notifyHigh(int id, String title, String text) {
        notifyOnChannel(id, ALERT_CHANNEL, Notification.PRIORITY_HIGH, title, text);
    }

    private void notifyDigest(String title, String text) {
        notifyOnChannel(DIGEST_NOTIFICATION_ID, DIGEST_CHANNEL, Notification.PRIORITY_DEFAULT, title, text);
    }

    private void notifyOnChannel(int id, String channel, int priority, String title, String text) {
        NotificationManager n = app.getSystemService(NotificationManager.class);
        if (n == null) return;
        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(app, id, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(app, channel) : new Notification.Builder(app);
        Notification notification = b.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setContentIntent(open)
                .setAutoCancel(true)
                .setPriority(priority)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .build();
        n.notify(id, notification);
    }

    private static void appendPart(StringBuilder b, String value) {
        if (value == null || value.isEmpty()) return;
        if (b.length() > 0) b.append(" • ");
        b.append(value);
    }

    private static String conditionNepali(int code) {
        if (code == 0) return "सफा";
        if (code >= 1 && code <= 3) return "बादल";
        if (code == 45 || code == 48) return "कुहिरो";
        if (code >= 51 && code <= 57) return "सिमसिमे वर्षा";
        if (code >= 61 && code <= 67) return "वर्षा";
        if (code >= 71 && code <= 77) return "हिमपात";
        if (code >= 80 && code <= 82) return "वर्षा / shower";
        if (code >= 85 && code <= 86) return "हिमपात";
        if (code >= 95 && code <= 99) return "चट्याङ / आँधी";
        return "मौसम अपडेट";
    }

    private static ZonedDateTime parseSlot(String raw, ZoneId zone) {
        try { return LocalDateTime.parse(raw, DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(zone); }
        catch (Exception ignored) { return null; }
    }

    private static ZoneId safeZone(String id) {
        try { return ZoneId.of(id); }
        catch (Exception ignored) { return ZoneId.of("Asia/Kathmandu"); }
    }

    private static double value(JSONObject o, String key) {
        return o == null ? Double.NaN : number(o.opt(key));
    }

    private static double at(JSONArray a, int i) {
        return a == null ? Double.NaN : number(a.opt(i));
    }

    private static int intAt(JSONArray a, int i) {
        if (a == null || i < 0 || i >= a.length()) return -1;
        Object v = a.opt(i);
        if (v instanceof Number) return ((Number) v).intValue();
        try { return Integer.parseInt(String.valueOf(v)); }
        catch (Exception ignored) { return -1; }
    }

    private static double number(Object v) {
        if (v instanceof Number) return ((Number) v).doubleValue();
        try { return v == null ? Double.NaN : Double.parseDouble(String.valueOf(v)); }
        catch (Exception ignored) { return Double.NaN; }
    }

    private static double max(double... values) {
        double m = 0d;
        for (double v : values) if (Double.isFinite(v)) m = Math.max(m, v);
        return m;
    }

    private static boolean wetCode(int code) {
        return (code >= 51 && code <= 67) || (code >= 80 && code <= 82) || thunderCode(code);
    }

    private static boolean thunderCode(int code) {
        return code >= 95 && code <= 99;
    }
}
''', encoding='utf-8')

print('V0919_NOTIFICATION_RELIABILITY_ONLY_OK')
