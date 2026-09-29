from pathlib import Path

ROOT = Path('floodsafe-android-app/app/src/main')
JAVA = ROOT / 'java/io/github/pujan1234hub/floodsafe/app'


def replace_once(path: Path, old: str, new: str, label: str):
    s = path.read_text(encoding='utf-8')
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'{label}: expected source marker missing in {path}')
    path.write_text(s.replace(old, new, 1), encoding='utf-8')

# 1) Notification-only permissions needed for lock-screen reliability.
manifest = ROOT / 'AndroidManifest.xml'
ms = manifest.read_text(encoding='utf-8')
for permission in [
    'android.permission.WAKE_LOCK',
    'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS',
]:
    line = f'    <uses-permission android:name="{permission}" />\n'
    if permission not in ms:
        marker = '    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n'
        if marker not in ms:
            raise SystemExit('manifest permission insertion marker missing')
        ms = ms.replace(marker, marker + line, 1)
manifest.write_text(ms, encoding='utf-8')

# 2) Keep a last known device location long enough for weather checks while locked,
# but keep river/FCM proximity freshness much tighter.
policy = JAVA / 'MonitoringLocationPolicy.java'
ps = policy.read_text(encoding='utf-8')
ps = ps.replace(
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 5L * 60L * 1000L;',
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 2L * 60L * 60L * 1000L; // V0918_LOCK_WEATHER_LOCATION_WINDOW\n'
    '    static final long MAX_RIVER_DEVICE_AGE_MS = 30L * 60L * 1000L; // V0918_LOCK_RIVER_LOCATION_WINDOW'
)
old = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {\n        return freshDeviceLocation(locationTime, now, lat, lon) && insideNepal(lat, lon);\n    }'''
new = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {\n        if (!insideNepal(lat, lon) || locationTime <= 0L) return false;\n        long age = now - locationTime;\n        return age <= MAX_RIVER_DEVICE_AGE_MS && age >= -FUTURE_TOLERANCE_MS;\n    }'''
if old not in ps and 'MAX_RIVER_DEVICE_AGE_MS' not in ps:
    raise SystemExit('MonitoringLocationPolicy river freshness marker missing')
if old in ps:
    ps = ps.replace(old, new, 1)
policy.write_text(ps, encoding='utf-8')

# 3) The live river monitor must never use a too-old location just to gain lock reliability.
live = JAVA / 'FloodLiveGaugeMonitor.java'
ls = live.read_text(encoding='utf-8')
needle = 'double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN))),homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));\n        if(!insideNepal(homeLat,homeLon))return;'
replacement = 'double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN))),homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));\n        long locationTime=monitor.getLong("location_time",0L);\n        if(!MonitoringLocationPolicy.freshNepalDeviceLocation(locationTime,System.currentTimeMillis(),homeLat,homeLon))return; // V0918_LOCK_FRESH_RIVER_GUARD'
if replacement not in ls:
    if needle not in ls:
        raise SystemExit('FloodLiveGaugeMonitor location marker missing')
    ls = ls.replace(needle, replacement, 1)
live.write_text(ls, encoding='utf-8')

# 4) Direct foreground-service notification monitor. This does NOT alter map/UI/data systems.
locked = JAVA / 'LockedNotificationMonitor.java'
locked.write_text(r'''package io.github.pujan1234hub.floodsafe.app;

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
 * Notification-only foreground-service heartbeat.
 * It bypasses Doze-delayed periodic WorkManager for time-sensitive rain/event delivery
 * while preserving the existing workers as fallback. No map, river geometry or UI code lives here.
 */
final class LockedNotificationMonitor {
    private static final long CHECK_MS = 2L * 60L * 1000L;
    private static final long DIGEST_MS = 3L * 60L * 60L * 1000L;
    private static final double WET_MM = 0.10d;
    private static final int LOOKAHEAD_MIN = 35;
    private static final String RAIN_CHANNEL = "floodsafe_lock_rain_v1";
    private static final String WEATHER_CHANNEL = "floodsafe_lock_weather_v1";
    private static final int RAIN_ID = 7411;
    private static final int EVENT_ID = 7412;
    private static final int DIGEST_ID = 7413;

    private final Context app;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final AtomicBoolean inFlight = new AtomicBoolean(false);
    private volatile boolean running;

    LockedNotificationMonitor(Context context) { app = context.getApplicationContext(); }

    void start() {
        if (running) return;
        running = true;
        ensureChannels();
        handler.postDelayed(tick, 5_000L);
    }

    void stop() {
        running = false;
        handler.removeCallbacks(tick);
        io.shutdownNow();
    }

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            if (!running) return;
            if (inFlight.compareAndSet(false, true)) {
                io.execute(() -> {
                    try { checkNow(); } catch (Exception ignored) { }
                    finally { inFlight.set(false); }
                });
            }
            handler.postDelayed(this, CHECK_MS);
        }
    };

    private void checkNow() throws Exception {
        SharedPreferences p = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!p.getBoolean("enabled", false)) return;
        if (Build.VERSION.SDK_INT >= 33 && app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) return;
        double lat = Double.longBitsToDouble(p.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(p.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        long locationTime = p.getLong("location_time", 0L);
        if (!MonitoringLocationPolicy.freshDeviceLocation(locationTime, System.currentTimeMillis(), lat, lon)) return;

        JSONObject data = fetch(lat, lon);
        JSONObject current = data.optJSONObject("current");
        double precipitation = max(value(current, "precipitation"), value(current, "rain"), value(current, "showers"));
        int currentCode = current == null ? -1 : current.optInt("weather_code", -1);
        boolean raining = precipitation >= WET_MM || wetCode(currentCode);

        boolean known = p.getBoolean("lock_rain_state_known", false);
        boolean oldRaining = p.getBoolean("lock_raining", false);
        if (!known) {
            p.edit().putBoolean("lock_rain_state_known", true).putBoolean("lock_raining", raining).apply();
        } else if (raining != oldRaining) {
            p.edit().putBoolean("lock_raining", raining).putLong("last_alert", System.currentTimeMillis()).apply();
            if (raining) notifyHigh(RAIN_ID, "🌧️ वर्षा सुरु भएको छ", "हालको स्थानमा वर्षा सुरु भएको देखिन्छ।", false);
            else notifyHigh(RAIN_ID, "🌤️ वर्षा रोकिएको छ", "हालको स्थानमा वर्षा रोकिएको देखिन्छ।", false);
        }

        ZonedDateTime now = ZonedDateTime.now(safeZone(data.optString("timezone", "Asia/Kathmandu")));
        UpcomingRain upcoming = upcomingRain(data.optJSONObject("minutely_15"), now);
        if (!raining && upcoming != null && upcoming.leadMinutes <= LOOKAHEAD_MIN) {
            String key = upcoming.start.withSecond(0).withNano(0).toString();
            if (!key.equals(p.getString("lock_upcoming_rain_key", ""))) {
                p.edit().putString("lock_upcoming_rain_key", key).putLong("last_alert", System.currentTimeMillis()).apply();
                notifyHigh(RAIN_ID, "☔ वर्षा सुरु हुन सक्छ", "करिब " + Math.max(1, upcoming.leadMinutes) + " मिनेटभित्र वर्षाको संकेत छ।", false);
            }
        }

        if (thunderNowOrSoon(currentCode, data.optJSONObject("hourly"), now)) {
            String thunderKey = now.toLocalDate().toString() + "-" + (now.getHour() / 3);
            if (!thunderKey.equals(p.getString("lock_thunder_key", ""))) {
                p.edit().putString("lock_thunder_key", thunderKey).apply();
                notifyHigh(EVENT_ID, "⚡ मेघगर्जन / चट्याङ सम्भावना", "हालको वा आगामी केही घण्टाको मौसममा thunderstorm संकेत देखिएको छ।", true);
            }
        }

        long nowMs = System.currentTimeMillis();
        long lastDigest = p.getLong("last_weather_digest_at", 0L);
        if (lastDigest <= 0L || nowMs - lastDigest >= DIGEST_MS) {
            double t = value(current, "temperature_2m");
            double humidity = value(current, "relative_humidity_2m");
            double wind = value(current, "wind_speed_10m");
            int probability = maxProbabilityNext3h(data.optJSONObject("hourly"), now);
            StringBuilder body = new StringBuilder();
            if (Double.isFinite(t)) body.append("अहिले ").append(Math.round(t)).append("°C");
            if (probability >= 0) body.append(body.length() == 0 ? "" : " • ").append("वर्षा ").append(probability).append("%");
            if (Double.isFinite(wind)) body.append(body.length() == 0 ? "" : " • ").append("हावा ").append(Math.round(wind)).append(" km/h");
            if (Double.isFinite(humidity)) body.append(body.length() == 0 ? "" : " • ").append("आर्द्रता ").append(Math.round(humidity)).append("%");
            if (body.length() > 0) {
                p.edit().putLong("last_weather_digest_at", nowMs).apply();
                notifyDefault(DIGEST_ID, "🌤️ ३ घण्टाको मौसम अपडेट", body.toString());
            }
        }
    }

    private JSONObject fetch(double lat, double lon) throws Exception {
        String q = "latitude=" + URLEncoder.encode(String.valueOf(lat), "UTF-8")
                + "&longitude=" + URLEncoder.encode(String.valueOf(lon), "UTF-8")
                + "&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m"
                + "&minutely_15=precipitation,rain,showers"
                + "&hourly=precipitation_probability,weather_code&forecast_hours=4&timezone=auto";
        HttpURLConnection c = (HttpURLConnection) new URL("https://api.open-meteo.com/v1/forecast?" + q).openConnection();
        c.setConnectTimeout(10_000); c.setReadTimeout(10_000); c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json"); c.setRequestProperty("Cache-Control", "no-cache");
        int code = c.getResponseCode();
        if (code != 200) { c.disconnect(); throw new IllegalStateException("weather " + code); }
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line; while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static final class UpcomingRain {
        final ZonedDateTime start; final long leadMinutes;
        UpcomingRain(ZonedDateTime start, long leadMinutes) { this.start = start; this.leadMinutes = leadMinutes; }
    }

    private static UpcomingRain upcomingRain(JSONObject block, ZonedDateTime now) {
        if (block == null) return null;
        JSONArray times = block.optJSONArray("time");
        JSONArray precipitation = block.optJSONArray("precipitation");
        JSONArray rain = block.optJSONArray("rain");
        JSONArray showers = block.optJSONArray("showers");
        if (times == null) return null;
        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.plusMinutes(15).isBefore(now)) continue;
            double mm = max(valueAt(precipitation, i), valueAt(rain, i), valueAt(showers, i));
            if (mm < WET_MM) continue;
            long lead = Math.max(0L, java.time.Duration.between(now, slot).toMinutes());
            return new UpcomingRain(slot, lead);
        }
        return null;
    }

    private static boolean thunderNowOrSoon(int currentCode, JSONObject hourly, ZonedDateTime now) {
        if (currentCode == 95 || currentCode == 96 || currentCode == 99) return true;
        if (hourly == null) return false;
        JSONArray times = hourly.optJSONArray("time"); JSONArray codes = hourly.optJSONArray("weather_code");
        if (times == null || codes == null) return false;
        ZonedDateTime end = now.plusHours(3).plusMinutes(30);
        for (int i = 0; i < times.length() && i < codes.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.isBefore(now.minusMinutes(30)) || slot.isAfter(end)) continue;
            int code = codes.optInt(i, -1);
            if (code == 95 || code == 96 || code == 99) return true;
        }
        return false;
    }

    private static int maxProbabilityNext3h(JSONObject hourly, ZonedDateTime now) {
        if (hourly == null) return -1;
        JSONArray times = hourly.optJSONArray("time"); JSONArray probs = hourly.optJSONArray("precipitation_probability");
        if (times == null || probs == null) return -1;
        int max = -1; ZonedDateTime end = now.plusHours(3).plusMinutes(30);
        for (int i = 0; i < times.length() && i < probs.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.isBefore(now.minusMinutes(30)) || slot.isAfter(end)) continue;
            max = Math.max(max, probs.optInt(i, -1));
        }
        return max;
    }

    private void ensureChannels() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager n = app.getSystemService(NotificationManager.class); if (n == null) return;
        NotificationChannel rain = new NotificationChannel(RAIN_CHANNEL, "FloodSafe lock-screen rain/events", NotificationManager.IMPORTANCE_HIGH);
        rain.setDescription("Rain start/stop, upcoming rain and thunderstorm alerts while the phone is locked");
        rain.enableVibration(true); rain.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC); n.createNotificationChannel(rain);
        NotificationChannel weather = new NotificationChannel(WEATHER_CHANNEL, "FloodSafe lock-screen weather", NotificationManager.IMPORTANCE_DEFAULT);
        weather.setDescription("Periodic current-location weather updates while the phone is locked");
        weather.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC); n.createNotificationChannel(weather);
    }

    private void notifyHigh(int id, String title, String text, boolean event) {
        NotificationManager n = app.getSystemService(NotificationManager.class); if (n == null) return;
        PendingIntent pi = openApp(id);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(app, RAIN_CHANNEL) : new Notification.Builder(app);
        Notification out = b.setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true).setContentIntent(pi)
                .setPriority(Notification.PRIORITY_HIGH).setVisibility(Notification.VISIBILITY_PUBLIC).build();
        n.notify(id, out);
    }

    private void notifyDefault(int id, String title, String text) {
        NotificationManager n = app.getSystemService(NotificationManager.class); if (n == null) return;
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(app, WEATHER_CHANNEL) : new Notification.Builder(app);
        Notification out = b.setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true).setContentIntent(openApp(id))
                .setVisibility(Notification.VISIBILITY_PUBLIC).build();
        n.notify(id, out);
    }

    private PendingIntent openApp(int requestCode) {
        Intent i = new Intent(app, NativeFullActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        return PendingIntent.getActivity(app, requestCode, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private static ZonedDateTime parseSlot(String raw, ZoneId zone) {
        if (raw == null || raw.trim().isEmpty()) return null;
        try { return LocalDateTime.parse(raw.trim(), DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(zone); }
        catch (Exception ignored) { return null; }
    }
    private static ZoneId safeZone(String id) { try { return ZoneId.of(id); } catch (Exception ignored) { return ZoneId.of("Asia/Kathmandu"); } }
    private static double value(JSONObject o, String key) { if (o == null) return Double.NaN; Object v = o.opt(key); return number(v); }
    private static double valueAt(JSONArray a, int i) { return a == null ? Double.NaN : number(a.opt(i)); }
    private static double number(Object v) { if (v instanceof Number) return ((Number)v).doubleValue(); try { return v == null ? Double.NaN : Double.parseDouble(String.valueOf(v)); } catch (Exception e) { return Double.NaN; } }
    private static double max(double... values) { double m = 0d; for (double v : values) if (Double.isFinite(v)) m = Math.max(m, v); return m; }
    private static boolean wetCode(int code) { return (code >= 51 && code <= 67) || (code >= 80 && code <= 82) || (code >= 95 && code <= 99); }
}
''', encoding='utf-8')

# 5) Start/stop the direct notification heartbeat from the existing foreground monitor.
service = JAVA / 'FloodMonitorService.java'
ss = service.read_text(encoding='utf-8')
if 'LockedNotificationMonitor lockedNotificationMonitor;' not in ss:
    ss = ss.replace(
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;',
        'private FloodLiveGaugeMonitor liveHydrologyMonitor;\n    private LockedNotificationMonitor lockedNotificationMonitor; // V0918_LOCK_NOTIFICATION_MONITOR_FIELD',
        1
    )
    ss = ss.replace(
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);',
        'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);\n        lockedNotificationMonitor = new LockedNotificationMonitor(this);',
        1
    )
    ss = ss.replace(
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();',
        'if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();\n        if (lockedNotificationMonitor != null) lockedNotificationMonitor.start(); // V0918_LOCK_NOTIFICATION_MONITOR_START',
        1
    )
    destroy_marker = '    @Override public void onDestroy() {\n'
    if destroy_marker not in ss:
        raise SystemExit('FloodMonitorService onDestroy marker missing')
    ss = ss.replace(destroy_marker,
        destroy_marker + '        if (lockedNotificationMonitor != null) {\n            try { lockedNotificationMonitor.stop(); } catch (RuntimeException ignored) { }\n            lockedNotificationMonitor = null; // V0918_LOCK_NOTIFICATION_MONITOR_STOP\n        }\n', 1)
service.write_text(ss, encoding='utf-8')

# 6) Ask once for Android battery-optimization exemption. This is notification reliability only.
reliability = JAVA / 'NotificationReliability.java'
reliability.write_text(r'''package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;

/** One-time system reliability request for lock-screen/background safety notifications. */
final class NotificationReliability {
    private static final String PREFS = "floodsafe_notification_reliability";
    private static final String KEY_PROMPTED = "battery_prompted_v1";
    private NotificationReliability() { }

    static void requestBatteryExemptionOnce(Activity activity) {
        if (activity == null || Build.VERSION.SDK_INT < 23) return;
        if (activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(KEY_PROMPTED, false)) return;
        PowerManager pm = activity.getSystemService(PowerManager.class);
        if (pm == null || pm.isIgnoringBatteryOptimizations(activity.getPackageName())) {
            activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(KEY_PROMPTED, true).apply();
            return;
        }
        activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(KEY_PROMPTED, true).apply();
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            if (activity.isFinishing() || activity.isDestroyed()) return;
            try {
                Intent i = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + activity.getPackageName()));
                activity.startActivity(i);
            } catch (RuntimeException ignored) { }
        }, 1800L);
    }
}
''', encoding='utf-8')

activity = JAVA / 'NativeFullActivity.java'
asrc = activity.read_text(encoding='utf-8')
if 'NotificationReliability.requestBatteryExemptionOnce(this);' not in asrc:
    marker = '        enableMonitoring();\n'
    if marker not in asrc:
        raise SystemExit('NativeFullActivity enableMonitoring marker missing')
    asrc = asrc.replace(marker, marker + '        NotificationReliability.requestBatteryExemptionOnce(this); // V0918_LOCK_BATTERY_RELIABILITY\n', 1)
activity.write_text(asrc, encoding='utf-8')

print('v0.9.18 notification-only lock-screen reliability patch applied')
