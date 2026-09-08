package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.app.Application;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;

/** Starts the additive danger-monitoring service once a Nepal monitoring point exists. */
public final class FloodSafeApp extends Application implements Application.ActivityLifecycleCallbacks {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private int resumedActivities;
    private final Runnable retry = new Runnable() {
        @Override public void run() {
            if (resumedActivities > 0) {
                maybeStartDangerMonitor();
                handler.postDelayed(this, 10_000L);
            }
        }
    };

    @Override public void onCreate() {
        super.onCreate();
        registerActivityLifecycleCallbacks(this);
        maybeStartDangerMonitor();
    }

    private void maybeStartDangerMonitor() {
        SharedPreferences p = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
        if (!p.contains("lat") || !p.contains("lon")) return;
        double lat = Double.longBitsToDouble(p.getLong("lat", Double.doubleToRawLongBits(Double.NaN)));
        double lon = Double.longBitsToDouble(p.getLong("lon", Double.doubleToRawLongBits(Double.NaN)));
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return;
        if (lat < 26.0 || lat > 31.0 || lon < 79.5 || lon > 89.0) return;
        FloodDangerMonitorService.start(this);
    }

    @Override public void onActivityResumed(Activity activity) {
        resumedActivities++;
        handler.removeCallbacks(retry);
        maybeStartDangerMonitor();
        handler.postDelayed(retry, 2_500L);
    }

    @Override public void onActivityPaused(Activity activity) {
        resumedActivities = Math.max(0, resumedActivities - 1);
        if (resumedActivities == 0) handler.removeCallbacks(retry);
    }

    @Override public void onActivityCreated(Activity activity, Bundle state) {}
    @Override public void onActivityStarted(Activity activity) {}
    @Override public void onActivityStopped(Activity activity) {}
    @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {}
    @Override public void onActivityDestroyed(Activity activity) {}
}
