package io.github.pujan1234hub.floodsafe.app;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.SystemClock;

import androidx.work.Constraints;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.OutOfQuotaPolicy;
import androidx.work.WorkManager;

/**
 * Additional while-idle trigger for routine weather notifications.
 * The existing 15-minute WorkManager and server-sent emergency alerts are unchanged.
 * This is best effort: Android can still defer an inexact alarm or network job.
 */
final class WeatherWakeScheduler {
    private static final long INTERVAL_MS = 3L * 60L * 60L * 1000L;
    private static final String NEXT_WAKE_KEY = "weather_next_wake_elapsed";
    private static final int REQUEST_CODE = 7315;

    private WeatherWakeScheduler() {}

    static void ensureScheduled(Context context, boolean afterBoot) {
        Context app = context.getApplicationContext();
        SharedPreferences prefs = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        if (!prefs.getBoolean("enabled", false)) return;
        AlarmManager alarms = (AlarmManager) app.getSystemService(Context.ALARM_SERVICE);
        if (alarms == null) return;

        long now = SystemClock.elapsedRealtime();
        long next = prefs.getLong(NEXT_WAKE_KEY, 0L);
        // Keep an existing alarm when reopening the app. Boot always requires a new alarm.
        if (!afterBoot && next > now + 60_000L && next <= now + INTERVAL_MS) return;

        Intent intent = new Intent(app, WeatherWakeReceiver.class)
                .setAction("io.github.pujan1234hub.floodsafe.WEATHER_WAKE");
        PendingIntent operation = PendingIntent.getBroadcast(
                app, REQUEST_CODE, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        long fireAt = now + INTERVAL_MS;
        try {
            if (Build.VERSION.SDK_INT >= 23) {
                alarms.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, fireAt, operation);
            } else {
                alarms.set(AlarmManager.ELAPSED_REALTIME_WAKEUP, fireAt, operation);
            }
            prefs.edit().putLong(NEXT_WAKE_KEY, fireAt).apply();
        } catch (RuntimeException ignored) {
            // Never interfere with existing WorkManager monitoring if the OS denies alarms.
        }
    }

    static void onWake(Context context) {
        Context app = context.getApplicationContext();
        SharedPreferences prefs = app.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE);
        prefs.edit().remove(NEXT_WAKE_KEY).apply();
        if (!prefs.getBoolean("enabled", false)) return;

        // Rearm before enqueuing so temporary lack of network cannot stop later wakes.
        ensureScheduled(app, true);
        Constraints network = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED).build();
        OneTimeWorkRequest weather = new OneTimeWorkRequest.Builder(RainAlertWorker.class)
                .setConstraints(network)
                .setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED_WORK_REQUEST)
                .build();
        WorkManager.getInstance(app).enqueueUniqueWork(
                "floodsafe-weather-while-idle", ExistingWorkPolicy.REPLACE, weather);
    }
}
