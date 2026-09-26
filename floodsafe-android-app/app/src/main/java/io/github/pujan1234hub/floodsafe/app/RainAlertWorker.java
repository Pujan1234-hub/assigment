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
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/**
 * Background weather + rain alert worker.
 *
 * Behaviour:
 *  - rain-start warning around 15-30 minutes before forecast rain (existing safety feature)
 *  - smart current-location weather digest roughly every 3 hours, anywhere in the world
 *  - one richer tomorrow forecast in the local evening
 *
 * Flood/river proximity remains Nepal-only in RiverAlertWorker/FCM.
 */
public final class RainAlertWorker extends Worker {
    static final String PREFS = "floodsafe_rain_alerts";
    static final String CHANNEL_ID = "local_rain_alerts_v2";
    private static final String WEATHER_CHANNEL_ID = "smart_weather_updates_v1";
    private static final double WET_MM = 0.10d;
    private static final int LOOKAHEAD_MINUTES = 35;
    private static final long WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L;
    private static final long EVENING_MIN_GAP_MS = 45L * 60L * 1000L;

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
        if (prefs.getBoolean("follow_device", false)) {
            long locationTime = prefs.getLong("location_time", 0L);
            if (!MonitoringLocationPolicy.freshDeviceLocation(
                    locationTime, System.currentTimeMillis(), lat, lon)) return Result.success();
        }

        try {
            JSONObject data = fetch(lat, lon);
            JSONObject currentData = data.optJSONObject("current");
            double current = max(
                    value(currentData, "precipitation"),
                    value(currentData, "rain"),
                    value(currentData, "showers"));
            double temperature = valueOrNaN(currentData, "temperature_2m");
            double apparent = valueOrNaN(currentData, "apparent_temperature");
            double humidity = valueOrNaN(currentData, "relative_humidity_2m");
            double wind = valueOrNaN(currentData, "wind_speed_10m");
            int weatherCode = currentData == null ? -1 : currentData.optInt("weather_code", -1);

            ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));
            ZonedDateTime now = ZonedDateTime.now(zone);

            // This is deliberately independent from Nepal. If the user is in the UK,
            // current-location weather notifications still work. Only river alerts are Nepal-only.
            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode);

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
                + "&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m"
                + "&minutely_15=precipitation,rain,showers"
                + "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code"
                + "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max"
                + "&forecast_days=2&timezone=auto";
        HttpURLConnection connection = (HttpURLConnection) new URL(
                "https://api.open-meteo.com/v1/forecast?" + query).openConnection();
        connection.setConnectTimeout(12000);
        connection.setReadTimeout(12000);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Cache-Control", "no-cache");
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

    private static final class ShortForecast {
        double temperature3h = Double.NaN;
        double precipitationMm = 0d;
        int precipitationProbability = -1;
    }

    private static final class DailyForecast {
        final String date;
        final double min;
        final double max;
        final double rainMm;
        final int rainProbability;
        final int weatherCode;

        DailyForecast(String date, double min, double max, double rainMm,
                      int rainProbability, int weatherCode) {
            this.date = date;
            this.min = min;
            this.max = max;
            this.rainMm = rainMm;
            this.rainProbability = rainProbability;
            this.weatherCode = weatherCode;
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

    private void maybeNotifyWeatherDigest(JSONObject data, SharedPreferences prefs,
                                          ZonedDateTime now, double temperature,
                                          double apparent, double humidity, double wind,
                                          int weatherCode) {
        long nowMs = System.currentTimeMillis();
        long last = prefs.getLong("last_weather_digest_at", 0L);
        String todayKey = now.toLocalDate().toString();
        String lastEvening = prefs.getString("last_evening_forecast_date", "");
        boolean intervalDue = last <= 0L || nowMs - last >= WEATHER_DIGEST_INTERVAL_MS;
        boolean eveningWindow = now.getHour() >= 19 && now.getHour() <= 23;
        boolean eveningDue = eveningWindow && !todayKey.equals(lastEvening)
                && (last <= 0L || nowMs - last >= EVENING_MIN_GAP_MS);
        if (!intervalDue && !eveningDue) return;

        ShortForecast shortForecast = shortForecast(data.optJSONObject("hourly"), now);
        DailyForecast today = dailyForecast(data.optJSONObject("daily"), now.toLocalDate());
        DailyForecast tomorrow = dailyForecast(data.optJSONObject("daily"), now.toLocalDate().plusDays(1));
        if (!Double.isFinite(temperature) && today == null && tomorrow == null) return;

        String title;
        String text;
        if (eveningDue && tomorrow != null) {
            title = "🌙 भोलिको मौसम • " + conditionNepali(tomorrow.weatherCode);
            String compare = compareTomorrow(today, tomorrow);
            StringBuilder body = new StringBuilder("भोलि ")
                    .append(tempRange(tomorrow.min, tomorrow.max));
            if (!compare.isEmpty()) body.append(" • ").append(compare);
            if (tomorrow.rainProbability >= 0) {
                body.append(" • वर्षा सम्भावना ").append(tomorrow.rainProbability).append("%");
            }
            if (tomorrow.rainMm > 0.05d) {
                body.append(" • करिब ").append(oneDecimal(tomorrow.rainMm)).append(" mm");
            }
            if (Double.isFinite(temperature)) {
                body.append(" • अहिले ").append(Math.round(temperature)).append("°C");
            }
            text = body.toString();
        } else {
            double delta = Double.isFinite(shortForecast.temperature3h) && Double.isFinite(temperature)
                    ? shortForecast.temperature3h - temperature : Double.NaN;
            if (shortForecast.precipitationProbability >= 60 || shortForecast.precipitationMm >= 0.5d) {
                title = "🌧️ आगामी ३ घण्टामा वर्षाको सम्भावना";
            } else if (Double.isFinite(delta) && Math.abs(delta) >= 2d) {
                title = delta > 0 ? "🌡️ तापक्रम बढ्दैछ" : "🌡️ तापक्रम घट्दैछ";
            } else {
                title = "🌤️ ३ घण्टाको मौसम अपडेट";
            }

            StringBuilder body = new StringBuilder();
            if (Double.isFinite(temperature)) {
                body.append("अहिले ").append(Math.round(temperature)).append("°C");
            }
            if (Double.isFinite(apparent)) {
                if (body.length() > 0) body.append(" • ");
                body.append("महसुस ").append(Math.round(apparent)).append("°C");
            }
            if (Double.isFinite(shortForecast.temperature3h)) {
                if (body.length() > 0) body.append(" • ");
                body.append("३ घण्टापछि करिब ").append(Math.round(shortForecast.temperature3h)).append("°C");
            }
            if (shortForecast.precipitationProbability >= 0) {
                body.append(" • वर्षा ").append(shortForecast.precipitationProbability).append("%");
            }
            if (shortForecast.precipitationMm > 0.05d) {
                body.append(" • ").append(oneDecimal(shortForecast.precipitationMm)).append(" mm");
            }
            if (Double.isFinite(wind)) body.append(" • हावा ").append(Math.round(wind)).append(" km/h");
            if (Double.isFinite(humidity)) body.append(" • आर्द्रता ").append(Math.round(humidity)).append("%");
            if (tomorrow != null && today != null) {
                String compare = compareTomorrow(today, tomorrow);
                if (!compare.isEmpty()) body.append(" • भोलि ").append(compare);
            }
            if (body.length() == 0) body.append(conditionNepali(weatherCode));
            text = body.toString();
        }

        notifyWeather(title, text);
        SharedPreferences.Editor edit = prefs.edit().putLong("last_weather_digest_at", nowMs);
        if (eveningDue) edit.putString("last_evening_forecast_date", todayKey);
        edit.apply();
    }

    private static ShortForecast shortForecast(JSONObject hourly, ZonedDateTime now) {
        ShortForecast out = new ShortForecast();
        if (hourly == null) return out;
        JSONArray times = hourly.optJSONArray("time");
        JSONArray temperatures = hourly.optJSONArray("temperature_2m");
        JSONArray probabilities = hourly.optJSONArray("precipitation_probability");
        JSONArray precipitation = hourly.optJSONArray("precipitation");
        if (times == null) return out;

        ZonedDateTime end = now.plusHours(3).plusMinutes(30);
        ZonedDateTime lastSlot = null;
        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.isBefore(now.minusMinutes(30)) || slot.isAfter(end)) continue;
            int probability = intAt(probabilities, i);
            if (probability >= 0) out.precipitationProbability = Math.max(out.precipitationProbability, probability);
            out.precipitationMm += valueAt(precipitation, i);
            if (lastSlot == null || slot.isAfter(lastSlot)) {
                double t = numberAt(temperatures, i);
                if (Double.isFinite(t)) out.temperature3h = t;
                lastSlot = slot;
            }
        }
        return out;
    }

    private static DailyForecast dailyForecast(JSONObject daily, LocalDate target) {
        if (daily == null || target == null) return null;
        JSONArray times = daily.optJSONArray("time");
        if (times == null) return null;
        for (int i = 0; i < times.length(); i++) {
            if (!target.toString().equals(times.optString(i))) continue;
            return new DailyForecast(
                    times.optString(i),
                    numberAt(daily.optJSONArray("temperature_2m_min"), i),
                    numberAt(daily.optJSONArray("temperature_2m_max"), i),
                    valueAt(daily.optJSONArray("precipitation_sum"), i),
                    intAt(daily.optJSONArray("precipitation_probability_max"), i),
                    intAt(daily.optJSONArray("weather_code"), i));
        }
        return null;
    }

    private static String compareTomorrow(DailyForecast today, DailyForecast tomorrow) {
        if (today == null || tomorrow == null || !Double.isFinite(today.max) || !Double.isFinite(tomorrow.max)) {
            return "";
        }
        double diff = tomorrow.max - today.max;
        long shown = Math.round(Math.abs(diff));
        if (diff >= 1.5d) return "आजभन्दा करिब " + Math.max(1L, shown) + "°C न्यानो";
        if (diff <= -1.5d) return "आजभन्दा करिब " + Math.max(1L, shown) + "°C चिसो";
        return "आजकै हाराहारी तापक्रम";
    }

    private static String tempRange(double min, double max) {
        if (Double.isFinite(min) && Double.isFinite(max)) {
            return Math.round(min) + "–" + Math.round(max) + "°C";
        }
        if (Double.isFinite(max)) return "अधिकतम " + Math.round(max) + "°C";
        if (Double.isFinite(min)) return "न्यूनतम " + Math.round(min) + "°C";
        return "तापक्रम विवरण उपलब्ध छैन";
    }

    private static String conditionNepali(int code) {
        if (code == 0) return "खुला आकाश";
        if (code == 1 || code == 2) return "आंशिक बादल";
        if (code == 3) return "बादल";
        if (code == 45 || code == 48) return "कुहिरो";
        if (code >= 51 && code <= 57) return "सिमसिमे वर्षा";
        if (code >= 61 && code <= 67) return "वर्षा";
        if (code >= 71 && code <= 77) return "हिउँ";
        if (code >= 80 && code <= 82) return "वर्षाको झरी";
        if (code >= 85 && code <= 86) return "हिउँको झरी";
        if (code >= 95) return "मेघगर्जन/चट्याङ सम्भावना";
        return "मौसम अपडेट";
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

    private static double numberAt(JSONArray a, int i) {
        if (a == null || i < 0 || i >= a.length() || a.isNull(i)) return Double.NaN;
        return a.optDouble(i, Double.NaN);
    }

    private static int intAt(JSONArray a, int i) {
        if (a == null || i < 0 || i >= a.length() || a.isNull(i)) return -1;
        return a.optInt(i, -1);
    }

    private static double max(double... values) {
        double out = 0d;
        for (double v : values) if (Double.isFinite(v)) out = Math.max(out, v);
        return out;
    }

    private void notifyWeather(String title, String text) {
        Context app = getApplicationContext();
        NotificationManager manager = app.getSystemService(NotificationManager.class);
        if (manager == null) return;

        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    WEATHER_CHANNEL_ID, "FloodSafe smart weather updates", NotificationManager.IMPORTANCE_DEFAULT);
            channel.setDescription("Current-location weather change and tomorrow forecast updates about every 3 hours");
            channel.enableVibration(false);
            manager.createNotificationChannel(channel);
        }

        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(app, 7102, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(app, WEATHER_CHANNEL_ID)
                : new android.app.Notification.Builder(app);
        android.app.Notification notification = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setOnlyAlertOnce(false)
                .setContentIntent(open)
                .build();
        manager.notify(7102, notification);
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

        Intent launch = new Intent(getApplicationContext(), NativeFullActivity.class)
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
