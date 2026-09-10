package io.github.pujan1234hub.floodsafe.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import com.google.firebase.messaging.FirebaseMessaging;
import java.util.concurrent.TimeUnit;

/** Restores background flood/rain checks after reboot or app replacement. */
public final class BootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (context == null || intent == null) return;
        String action = intent.getAction();
        if (!Intent.ACTION_BOOT_COMPLETED.equals(action)
                && !Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) return;

        boolean enabled = context.getSharedPreferences(RainAlertWorker.PREFS, Context.MODE_PRIVATE)
                .getBoolean("enabled", false);
        if (!enabled) return;

        Constraints constraints = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build();
        PeriodicWorkRequest rainWork = new PeriodicWorkRequest.Builder(
                RainAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(
                RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        WorkManager manager = WorkManager.getInstance(context.getApplicationContext());
        manager.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, rainWork);
        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
    }
}
