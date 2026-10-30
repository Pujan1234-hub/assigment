package io.github.pujan1234hub.floodsafe.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import androidx.annotation.Nullable;

/**
 * Process-start safety gate for current-device monitoring.
 *
 * The user's alert opt-in remains enabled, but a current-device coordinate older
 * than five minutes is removed before workers can use it. Fresh coordinates outside
 * Nepal may still be used for rain timing; river proximity separately requires Nepal.
 */
public final class MonitoringSafetyProvider extends ContentProvider {
    private final Handler main = new Handler(Looper.getMainLooper());
    private Context app;

    private final Runnable guard = new Runnable() {
        @Override public void run() {
            sanitize();
            main.postDelayed(this, 60_000L);
        }
    };

    @Override public boolean onCreate() {
        Context context = getContext();
        if (context == null) return false;
        app = context.getApplicationContext();
        sanitize();
        main.postDelayed(guard, 60_000L);
        return true;
    }

    private void sanitize() {
        Context context = app;
        if (context == null) return;
        SharedPreferences prefs = context.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        boolean followDevice = prefs.getBoolean("follow_device", false);
        long locationTime = prefs.getLong("location_time", 0L);
        double lat = Double.longBitsToDouble(prefs.getLong(
                "lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(prefs.getLong(
                "lon", Double.doubleToRawLongBits(Double.NaN)));
        long now = System.currentTimeMillis();
        // Capture the last genuine GPS fix for ordinary weather updates only.
        // Emergency river alerts still require the separately checked 5-minute GPS fix.
        if (followDevice && MonitoringLocationPolicy.freshDeviceLocation(locationTime, now, lat, lon)
                && locationTime > prefs.getLong("weather_last_fix_at", 0L)) {
            prefs.edit()
                    .putLong("weather_last_lat", Double.doubleToRawLongBits(lat))
                    .putLong("weather_last_lon", Double.doubleToRawLongBits(lon))
                    .putLong("weather_last_fix_at", locationTime)
                    .apply();
        }
        if (!MonitoringLocationPolicy.shouldClearFollowDevice(
                followDevice, locationTime, now, lat, lon)) return;

        // Do not change "enabled": stale GPS pauses location-based matching until
        // a fresh service fix arrives; it must never silently turn the user's alerts off.
        prefs.edit()
                .remove("lat")
                .remove("lon")
                .remove("location_time")
                .remove("device_lat")
                .remove("device_lon")
                .remove("device_location_time")
                .putBoolean("location_stale", true)
                .apply();
    }

    @Nullable @Override public Cursor query(Uri uri, String[] projection, String selection,
                                            String[] selectionArgs, String sortOrder) { return null; }
    @Nullable @Override public String getType(Uri uri) { return null; }
    @Nullable @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) { return 0; }
}
