package io.github.pujan1234hub.floodsafe.app;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.media.AudioAttributes;
import android.net.Uri;
import android.provider.Settings;

final class FloodSafeSounds {
    static final String NORMAL="floodsafe_soft_notice_v1";
    static final String WARNING="floodsafe_river_warning_soft_v1";
    static final String DANGER="floodsafe_nearby_danger_alarm_v1";
    private FloodSafeSounds(){}
    static String channel(Context c, boolean danger, boolean warning){
        String id=danger?DANGER:warning?WARNING:NORMAL;
        NotificationManager nm=c.getSystemService(NotificationManager.class);
        if(nm==null)return id;
        NotificationChannel ch=new NotificationChannel(id,danger?"Nearby river danger alarm":warning?"River warnings":"FloodSafe updates",danger||warning?NotificationManager.IMPORTANCE_HIGH:NotificationManager.IMPORTANCE_DEFAULT);
        Uri uri=danger?Settings.System.DEFAULT_ALARM_ALERT_URI:Uri.parse("android.resource://"+c.getPackageName()+"/"+R.raw.floodsafe_soft_chime);
        AudioAttributes aa=new AudioAttributes.Builder().setUsage(danger?AudioAttributes.USAGE_ALARM:AudioAttributes.USAGE_NOTIFICATION).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
        ch.setSound(uri,aa);ch.enableVibration(danger||warning);nm.createNotificationChannel(ch);return id;
    }
}
