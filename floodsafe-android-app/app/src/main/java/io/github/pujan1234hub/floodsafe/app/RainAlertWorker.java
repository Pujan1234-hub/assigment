package io.github.pujan1234hub.floodsafe.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
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
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/**
 * Background rain alert. Uses the same FloodSafe monitoring point and Open-Meteo
 * 15-minute forecast. It warns once for each rain event, normally around
 * 15-30 minutes before the forecast start, and also catches rain that has just begun.
 */
public final class RainAlertWorker extends Worker {
    static final String PREFS = "floodsafe_rain_alerts";
    static final String CHANNEL_ID = "local_rain_alerts_v2";
    private static final double WET_MM = 0.10d;
    private static final int LOOKAHEAD_MINUTES = 35;

    public RainAlertWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull @Override public Result doWork() {
        Context app = getApplicationContext();
        SharedPreferences prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("enabled", false)) return Result.success();
        if (Build.VERSION.SDK_INT >= 33 && app.checkSelfPermission(
                android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return Result.success();
        }

        double lat = Double.longBitsToDouble(prefs.getLong(
                "lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(prefs.getLong(
                "lon", Double.doubleToRawLongBits(Double.NaN)));
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return Result.success();

        try {
            JSONObject data = fetch(lat, lon);
            JSONObject currentData = data.optJSONObject("current");
            double current = max(
                    value(currentData, "precipitation"),
                    value(currentData, "rain"),
                    value(currentData, "showers"));
            double temperature = valueOrNaN(currentData, "temperature_2m");
            double humidity = valueOrNaN(currentData, "relative_humidity_2m");
            double wind = valueOrNaN(currentData, "wind_speed_10m");

            ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));
            ZonedDateTime now = ZonedDateTime.now(zone);
            RainEvent event = findEvent(data.optJSONObject("minutely_15"), now);
            boolean rainingNow = current >= WET_MM || (event != null && event.activeNow);

            if (!rainingNow && event == null) {
                if ("wet-current".equals(prefs.getString("last_event_key", ""))) {
                    prefs.edit().remove("last_event_key").apply();
                }
                return Result.success();
            }
            long lead = event == null ? 0L
                    : Math.max(0L, java.time.Duration.between(now, event.start).toMinutes());
            if (!rainingNow && lead > LOOKAHEAD_MINUTES) return Result.success();

            String eventKey;
            if (event != null) eventKey = event.start.withSecond(0).withNano(0).toString();
            else eventKey = "wet-current";

            if (eventKey.equals(prefs.getString("last_event_key", ""))) return Result.success();
            prefs.edit()
                    .putString("last_event_key", eventKey)
                    .putLong("last_alert", System.currentTimeMillis())
                    .apply();

            double nextHour = event == null ? Math.max(0d, current) : event.nextHourMm;
            notifyRain(rainingNow, lead, event, nextHour, temperature, humidity, wind, zone);
            return Result.success();
        } catch (Exception ignored) {
            return Result.retry();
        }
    }

    private static JSONObject fetch(double lat, double lon) throws Exception {
        String query = "latitude=" + URLEncoder.encode(String.valueOf(lat), "UTF-8")
                + "&longitude=" + URLEncoder.encode(String.valueOf(lon), "UTF-8")
                + "&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,wind_speed_10m"
                + "&minutely_15=precipitation,rain,showers"
                + "&forecast_days=1&timezone=auto";
        HttpURLConnection connection = (HttpURLConnection) new URL(
                "https://api.open-meteo.com/v1/forecast?" + query).openConnection();
        connection.setConnectTimeout(12000);
        connection.setReadTimeout(12000);
        connection.setRequestProperty("Accept", "application/json");
        int code = connection.getResponseCode();
        if (code != 200) {
            connection.disconnect();
            throw new IllegalStateException("Weather HTTP " + code);
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

    private static final class RainEvent {
        final ZonedDateTime start;
        final boolean activeNow;
        final double firstSlotMm;
        final double nextHourMm;

        RainEvent(ZonedDateTime start, boolean activeNow, double firstSlotMm, double nextHourMm) {
            this.start = start;
            this.activeNow = activeNow;
            this.firstSlotMm = firstSlotMm;
            this.nextHourMm = nextHourMm;
        }
    }

    private static RainEvent findEvent(JSONObject block, ZonedDateTime now) {
        if (block == null) return null;
        JSONArray times = block.optJSONArray("time");
        JSONArray precipitation = block.optJSONArray("precipitation");
        JSONArray rain = block.optJSONArray("rain");
        JSONArray showers = block.optJSONArray("showers");
        if (times == null || times.length() == 0) return null;

        int firstWet = -1;
        ZonedDateTime start = null;
        boolean activeNow = false;
        double firstMm = 0d;

        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null) continue;
            double mm = max(valueAt(precipitation, i), valueAt(rain, i), valueAt(showers, i));
            ZonedDateTime slotEnd = slot.plusMinutes(15);
            boolean relevant = !slotEnd.isBefore(now);
            if (!relevant || mm < WET_MM) continue;

            firstWet = i;
            firstMm = mm;
            activeNow = !slot.isAfter(now) && slotEnd.isAfter(now);
            start = slot;
            break;
        }
        if (firstWet < 0 || start == null) return null;

        double hour = 0d;
        for (int i = firstWet; i < times.length() && i < firstWet + 4; i++) {
            hour += max(valueAt(precipitation, i), valueAt(rain, i), valueAt(showers, i));
        }
        return new RainEvent(start, activeNow, firstMm, hour);
    }

    private static ZonedDateTime parseSlot(String text, ZoneId zone) {
        if (text == null || text.trim().isEmpty()) return null;
        try {
            return LocalDateTime.parse(text).atZone(zone);
        } catch (Exception ignored) {
            try { return ZonedDateTime.parse(text).withZoneSameInstant(zone); }
            catch (Exception ignoredAgain) { return null; }
        }
    }

    private static ZoneId safeZone(String name) {
        try { return ZoneId.of(name); }
        catch (Exception ignored) { return ZoneId.of("Asia/Kathmandu"); }
    }

    private static double value(JSONObject o, String key) {
        if (o == null || !o.has(key) || o.isNull(key)) return 0d;
        return Math.max(0d, o.optDouble(key, 0d));
    }

    private static double valueOrNaN(JSONObject o, String key) {
        if (o == null || !o.has(key) || o.isNull(key)) return Double.NaN;
        return o.optDouble(key, Double.NaN);
    }

    private static double valueAt(JSONArray a, int i) {
        return a == null ? 0d : Math.max(0d, a.optDouble(i, 0d));
    }

    private static double max(double... values) {
        double out = 0d;
        for (double v : values) if (Double.isFinite(v)) out = Math.max(out, v);
        return out;
    }

    private void notifyRain(boolean rainingNow, long leadMinutes, RainEvent event,
                            double nextHourMm, double temperature, double humidity,
                            double wind, ZoneId zone) {
        NotificationManager manager = getApplicationContext().getSystemService(NotificationManager.class);
        if (manager == null) return;

        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "FloodSafe स्थानीय वर्षा सूचना", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("हालको/छानिएको स्थानमा वर्षा सुरु हुनु अघि 15-minute forecast सूचना");
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }

        String title;
        String timing;
        if (rainingNow) {
            title = "🌧️ तपाईंको क्षेत्रमा वर्षा सुरु भएको देखिन्छ";
            timing = "Open-Meteo पूर्वानुमानमा अहिले वर्षा देखिएको छ।";
        } else {
            long shownLead = Math.max(1L, leadMinutes);
            title = "🌧️ करिब " + shownLead + " मिनेटपछि वर्षा हुनसक्छ";
            String clock = event == null ? "" : event.start.format(DateTimeFormatter.ofPattern("HH:mm"));
            timing = "अनुमानित सुरु " + clock + " • करिब " + shownLead + " मिनेटपछि।";
        }

        String amount = nextHourMm > 0.01d
                ? " आगामी १ घण्टामा करिब " + oneDecimal(nextHourMm) + " mm वर्षा पूर्वानुमान।"
                : "";
        String weather = (Double.isFinite(temperature) ? " तापक्रम " + Math.round(temperature) + "°C" : "")
                + (Double.isFinite(humidity) ? " • आर्द्रता " + Math.round(humidity) + "%" : "")
                + (Double.isFinite(wind) ? " • हावा " + Math.round(wind) + " km/h" : "");
        String text = timing + amount + weather + " यो पूर्वानुमान हो; स्थानीय वर्षा ठ्याक्कै समयभन्दा अगाडि/पछि हुन सक्छ।";

        Intent launch = new Intent(getApplicationContext(), VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(getApplicationContext(), 7101, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(getApplicationContext(), CHANNEL_ID)
                : new android.app.Notification.Builder(getApplicationContext());
        android.app.Notification notification = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setContentIntent(open)
                .build();
        manager.notify(7101, notification);
    }

    private static String oneDecimal(double value) {
        return String.format(Locale.US, "%.1f", Math.max(0d, value));
    }
}
