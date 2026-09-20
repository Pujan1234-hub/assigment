package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.annotation.SuppressLint;
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
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;

/**
 * User-enabled foreground location + official hydrology monitor for FloodSafe alerts.
 * The service keeps device location fresh and runs the native one-second BIPAD/DHM
 * river/rain/hydrology rechecker while monitoring is enabled.
 */
public final class FloodMonitorService extends Service implements LocationListener {
    private static final String CHANNEL_ID = "floodsafe_background_monitor_v1";
    private static final int NOTIFICATION_ID = 7301;
    private static final long MIN_TIME_MS = 30_000L;
    private static final float MIN_DISTANCE_M = 25f;
    private static final long MAX_LAST_KNOWN_AGE_MS = 2L * 60L * 1000L;

    private LocationManager locationManager;
    private SharedPreferences prefs;
    private boolean updatesStarted;
    private FloodLiveGaugeMonitor liveHydrologyMonitor; // V0872_BACKGROUND_HYDRO_MONITOR

    static boolean hasForegroundLocation(Context context) {
        return context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
                || context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    static boolean hasBackgroundLocation(Context context) {
        return Build.VERSION.SDK_INT < 29
                || context.checkSelfPermission(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    static void startIfEnabled(Context context) {
        Context app = context.getApplicationContext();
        if (!app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE)
                .getBoolean("enabled", false)) return;
        if (!hasForegroundLocation(app)) return;
        Intent intent = new Intent(app, FloodMonitorService.class);
        try {
            if (Build.VERSION.SDK_INT >= 26) app.startForegroundService(intent);
            else app.startService(intent);
        } catch (RuntimeException ignored) {
            // FCM/WorkManager remain available if the OS temporarily blocks an FGS start.
        }
    }

    static void start(Context context) { startIfEnabled(context); }

    static void stop(Context context) {
        try { context.getApplicationContext().stopService(
                new Intent(context.getApplicationContext(), FloodMonitorService.class)); }
        catch (RuntimeException ignored) { }
    }

    @Override public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
        locationManager = getSystemService(LocationManager.class);
        liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);
        ensureChannel();
        if (!promoteToForeground()) stopSelf();
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (prefs == null || !prefs.getBoolean("enabled", false)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (!promoteToForeground()) {
            stopSelf();
            return START_NOT_STICKY;
        }
        startLocationUpdates();
        if (liveHydrologyMonitor != null) liveHydrologyMonitor.start(); // V0872_START_ONE_SECOND_HYDRO
        return START_STICKY;
    }

    private void ensureChannel() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager == null) return;
        try {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "FloodSafe background safety monitoring",
                    NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Keeps location and official BIPAD/DHM hydrology monitoring active for FloodSafe alerts");
            channel.setSound(null, null);
            channel.enableVibration(false);
            manager.createNotificationChannel(channel);
        } catch (RuntimeException ignored) { }
    }

    private Notification monitorNotification() {
        Intent launch = new Intent(this, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 7301, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle("FloodSafe Nepal सुरक्षा निगरानी चालु छ")
                .setContentText("App बन्द हुँदा पनि official river/rain/hydrology source recheck र नजिकको alert निगरानी हुन्छ।")
                .setContentIntent(open)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .build();
    }

    private boolean promoteToForeground() {
        try {
            Notification notification = monitorNotification();
            if (Build.VERSION.SDK_INT >= 29) {
                startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION);
            } else {
                startForeground(NOTIFICATION_ID, notification);
            }
            return true;
        } catch (RuntimeException denied) {
            return false;
        }
    }

    @SuppressLint("MissingPermission")
    private void startLocationUpdates() {
        if (updatesStarted || locationManager == null) return;
        if (!hasForegroundLocation(this)) {
            stopSelf();
            return;
        }
        boolean requested = false;
        requested |= requestProvider(LocationManager.NETWORK_PROVIDER);
        requested |= requestProvider(LocationManager.GPS_PROVIDER);
        updatesStarted = requested;
        seedFreshLastKnown();
    }

    @SuppressLint("MissingPermission")
    private boolean requestProvider(String provider) {
        if (locationManager == null) return false;
        try {
            if (!locationManager.isProviderEnabled(provider)) return false;
            locationManager.requestLocationUpdates(provider, MIN_TIME_MS, MIN_DISTANCE_M, this);
            return true;
        } catch (SecurityException | IllegalArgumentException ignored) {
            return false;
        }
    }

    @SuppressLint("MissingPermission")
    private void seedFreshLastKnown() {
        if (locationManager == null || !hasForegroundLocation(this)) return;
        Location best = null;
        for (String provider : new String[]{LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER}) {
            try {
                Location candidate = locationManager.getLastKnownLocation(provider);
                if (candidate == null) continue;
                if (best == null || candidate.getTime() > best.getTime()) best = candidate;
            } catch (SecurityException | IllegalArgumentException ignored) { }
        }
        if (best == null) return;
        long now = System.currentTimeMillis();
        long age = now - best.getTime();
        if (best.getTime() > 0L && age >= -30_000L && age <= MAX_LAST_KNOWN_AGE_MS) {
            saveLocation(best, now);
        }
    }

    @Override public void onLocationChanged(Location location) {
        if (location == null || prefs == null) return;
        if (!prefs.getBoolean("enabled", false)) {
            stopSelf();
            return;
        }
        saveLocation(location, System.currentTimeMillis());
    }

    private void saveLocation(Location location, long now) {
        double lat = location.getLatitude();
        double lon = location.getLongitude();
        if (!Double.isFinite(lat) || !Double.isFinite(lon)
                || lat < -90d || lat > 90d || lon < -180d || lon > 180d) return;
        prefs.edit()
                .putLong("device_lat", Double.doubleToRawLongBits(lat))
                .putLong("device_lon", Double.doubleToRawLongBits(lon))
                .putLong("device_location_time", now)
                .putLong("lat", Double.doubleToRawLongBits(lat))
                .putLong("lon", Double.doubleToRawLongBits(lon))
                .putLong("location_time", now)
                .putBoolean("follow_device", true)
                .putBoolean("location_stale", false)
                .apply();
    }

    @Override public void onProviderEnabled(String provider) {
        updatesStarted = false;
        startLocationUpdates();
    }

    @Override public void onProviderDisabled(String provider) { }
    @Override public void onStatusChanged(String provider, int status, Bundle extras) { }

    @Override public void onDestroy() {
        if (liveHydrologyMonitor != null) {
            try { liveHydrologyMonitor.stop(); } catch (RuntimeException ignored) { }
            liveHydrologyMonitor = null;
        }
        if (locationManager != null) {
            try { locationManager.removeUpdates(this); }
            catch (SecurityException | IllegalArgumentException ignored) { }
        }
        updatesStarted = false;
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
