package io.github.pujan1234hub.floodsafe.app;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;
import java.util.Locale;
import java.util.Map;

/** Displays verified push messages while the app is closed, with local river filtering. */
public final class FloodSafeMessagingService extends FirebaseMessagingService {
    private static final String CHANNEL_ID = "official_nepal_alerts_v2";
    private static final double DEFAULT_RIVER_RADIUS_KM = 15d;
    private static final String PUSH_PREFS = "floodsafe_push_guard";

    @Override public void onMessageReceived(RemoteMessage message) {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) return;

        Map<String, String> data = message.getData();
        if ("river_alert".equals(data.get("kind")) && !acceptNearbyRiver(data)) return;

        String title = "FloodSafe Nepal alert";
        String body = "Open FloodSafe Nepal for current official information.";
        if (message.getNotification() != null) {
            if (message.getNotification().getTitle() != null) title = message.getNotification().getTitle();
            if (message.getNotification().getBody() != null) body = message.getNotification().getBody();
        }
        if (data.containsKey("title")) title = data.get("title");
        if (data.containsKey("body")) body = data.get("body");

        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                    "Nearby river and Nepal alerts", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Nearby official river warning/danger and verified Nepal alerts");
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }

        Intent launch = new Intent(this, VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 0, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(this, CHANNEL_ID)
                : new android.app.Notification.Builder(this);
        android.app.Notification notification = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(body))
                .setAutoCancel(true)
                .setContentIntent(open)
                .build();
        manager.notify((int) (System.currentTimeMillis() & 0x7fffffff), notification);
    }

    private boolean acceptNearbyRiver(Map<String, String> data) {
        double stationLat = number(data.get("lat"));
        double stationLon = number(data.get("lon"));
        if (!Double.isFinite(stationLat) || !Double.isFinite(stationLon)) return false;

        SharedPreferences monitor = getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!monitor.getBoolean("enabled", false)) return false;
        double homeLat = Double.longBitsToDouble(monitor.getLong(
                "lat", Double.doubleToRawLongBits(Double.NaN)));
        double homeLon = Double.longBitsToDouble(monitor.getLong(
                "lon", Double.doubleToRawLongBits(Double.NaN)));
        if (!Double.isFinite(homeLat) || !Double.isFinite(homeLon)) return false;

        double radius = number(data.get("radius_km"));
        if (!Double.isFinite(radius) || radius <= 0d || radius > 30d) radius = DEFAULT_RIVER_RADIUS_KM;
        double distance = haversineKm(homeLat, homeLon, stationLat, stationLon);
        if (distance > radius) return false;

        String stage = safe(data.get("stage"));
        if (!("warning".equals(stage) || "danger".equals(stage))) return false;
        String signature = safe(data.get("station_id")) + "|" + stage + "|"
                + safe(data.get("measured_at")) + "|" + safe(data.get("water_level"));
        if (signature.length() < 6) return false;

        SharedPreferences guard = getSharedPreferences(PUSH_PREFS, Context.MODE_PRIVATE);
        String key = "river_" + Integer.toHexString(safe(data.get("station_id")).hashCode());
        if (signature.equals(guard.getString(key, ""))) return false;
        guard.edit().putString(key, signature).apply();

        // Put an exact local distance into the message shown to the user.
        if (data instanceof java.util.HashMap) {
            @SuppressWarnings("unchecked") java.util.HashMap<String, String> mutable =
                    (java.util.HashMap<String, String>) data;
            String river = safe(data.get("river_name"));
            String level = safe(data.get("water_level"));
            String title = "danger".equals(stage) ? "🚨 नजिकको नदी खतरा चेतावनी" : "⚠️ नजिकको नदी चेतावनी";
            String body = (river.isEmpty() ? "Official river station" : river)
                    + " • " + String.format(Locale.US, "%.1f km", distance)
                    + (level.isEmpty() ? "" : " • " + level + " m")
                    + " • BIPAD/DHM official";
            mutable.put("title", title);
            mutable.put("body", body);
        }
        return true;
    }

    private static String safe(String value) { return value == null ? "" : value.trim(); }
    private static double number(String value) {
        try { return Double.parseDouble(value == null ? "" : value.trim()); }
        catch (Exception ignored) { return Double.NaN; }
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
