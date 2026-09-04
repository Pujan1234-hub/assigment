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

/** Checks the user's last chosen point every 15 minutes while the app is closed. */
public final class RainAlertWorker extends Worker {
    static final String PREFS = "floodsafe_rain_alerts";
    static final String CHANNEL_ID = "local_rain_alerts";
    private static final long COOLDOWN_MS = 3L * 60L * 60L * 1000L;

    public RainAlertWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull @Override public Result doWork() {
        SharedPreferences prefs = getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("enabled", false)) return Result.success();
        if (Build.VERSION.SDK_INT >= 33 && getApplicationContext().checkSelfPermission(
                android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            return Result.success();
        }
        double lat = Double.longBitsToDouble(prefs.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(prefs.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return Result.success();

        try {
            String query = "latitude=" + URLEncoder.encode(String.valueOf(lat), "UTF-8")
                    + "&longitude=" + URLEncoder.encode(String.valueOf(lon), "UTF-8")
                    + "&current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m"
                    + "&hourly=rain,showers,precipitation"
                    + "&forecast_days=1&timezone=auto";
            HttpURLConnection connection = (HttpURLConnection) new URL(
                    "https://api.open-meteo.com/v1/forecast?" + query).openConnection();
            connection.setConnectTimeout(12000);
            connection.setReadTimeout(12000);
            connection.setRequestProperty("Accept", "application/json");
            if (connection.getResponseCode() != 200) return Result.retry();
            StringBuilder body = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                    connection.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line = reader.readLine()) != null) body.append(line);
            } finally { connection.disconnect(); }

            JSONObject data = new JSONObject(body.toString());
            JSONObject currentData = data.optJSONObject("current");
            double current = currentData == null ? 0 : currentData.optDouble("precipitation",
                    currentData.optDouble("rain", 0));
            double temperature = currentData == null ? Double.NaN : currentData.optDouble("temperature_2m", Double.NaN);
            double humidity = currentData == null ? Double.NaN : currentData.optDouble("relative_humidity_2m", Double.NaN);
            double wind = currentData == null ? Double.NaN : currentData.optDouble("wind_speed_10m", Double.NaN);
            JSONObject hourly = data.optJSONObject("hourly");
            double next = 0;
            if (hourly != null) {
                JSONArray time = hourly.optJSONArray("time"), rain = hourly.optJSONArray("rain"),
                        showers = hourly.optJSONArray("showers"), precipitation = hourly.optJSONArray("precipitation");
                ZoneId zone = ZoneId.of(data.optString("timezone", "UTC"));
                ZonedDateTime now = ZonedDateTime.now(zone);
                for (int i = 0; time != null && i < time.length(); i++) {
                    ZonedDateTime slot = LocalDateTime.parse(time.optString(i)).atZone(zone);
                    if (!slot.isBefore(now)) {
                        next = Math.max(valueAt(rain, i), Math.max(valueAt(showers, i), valueAt(precipitation, i)));
                        break;
                    }
                }
            }
            if (Math.max(current, next) < 0.1d) return Result.success();

            long now = System.currentTimeMillis();
            if (now - prefs.getLong("last_alert", 0) < COOLDOWN_MS) return Result.success();
            prefs.edit().putLong("last_alert", now).apply();
            notifyRain(current >= 0.1d, next, temperature, humidity, wind);
            return Result.success();
        } catch (Exception ignored) {
            return Result.retry();
        }
    }

    private static double valueAt(JSONArray values, int index) {
        return values == null ? 0 : Math.max(0, values.optDouble(index, 0));
    }

    private void notifyRain(boolean rainingNow, double next, double temperature, double humidity, double wind) {
        NotificationManager manager = getApplicationContext().getSystemService(NotificationManager.class);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "FloodSafe local rain alerts",
                NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("Rain forecast for the last FloodSafe monitoring area");
        manager.createNotificationChannel(channel);
        String title = rainingNow ? "🌧️ तपाईंको निगरानी क्षेत्रमा वर्षा" : "🌧️ वर्षा हुनसक्छ";
        String weather = (Double.isFinite(temperature) ? " " + Math.round(temperature) + "°C" : "")
                + (Double.isFinite(humidity) ? " • आर्द्रता " + Math.round(humidity) + "%" : "")
                + (Double.isFinite(wind) ? " • हावा " + Math.round(wind) + " km/h" : "");
        String text = rainingNow ? "अहिले वर्षा देखिएको छ।" + weather
                : "अर्को घण्टामा वर्षा हुनसक्छ।" + weather;
        Intent launch = new Intent(getApplicationContext(), MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(getApplicationContext(), 1, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        android.app.Notification notification = new android.app.Notification.Builder(getApplicationContext(), CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(text)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true).setContentIntent(open).build();
        manager.notify(7101, notification);
    }
}
