package io.github.pujan1234hub.floodsafe.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** App-private alarm trigger; no data download or river alert filtering occurs in a receiver. */
public final class WeatherWakeReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (context == null || intent == null) return;
        if (!"io.github.pujan1234hub.floodsafe.WEATHER_WAKE".equals(intent.getAction())) return;
        WeatherWakeScheduler.onWake(context);
    }
}
