from pathlib import Path

ROOT = Path('floodsafe-android-app/app/src/main')
JAVA = ROOT / 'java/io/github/pujan1234hub/floodsafe/app'

# Notification-only permissions.
manifest = ROOT / 'AndroidManifest.xml'
ms = manifest.read_text(encoding='utf-8')
marker = '    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />\n'
for permission in ('android.permission.WAKE_LOCK', 'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS'):
    line = f'    <uses-permission android:name="{permission}" />\n'
    if permission not in ms:
        if marker not in ms:
            raise SystemExit('manifest permission marker missing')
        ms = ms.replace(marker, marker + line, 1)
manifest.write_text(ms, encoding='utf-8')

# Keep weather location usable while locked, while river alerts keep a tighter freshness window.
policy = JAVA / 'MonitoringLocationPolicy.java'
ps = policy.read_text(encoding='utf-8')
ps = ps.replace(
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 5L * 60L * 1000L;',
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 2L * 60L * 60L * 1000L; // V0918_LOCK_WEATHER_LOCATION_WINDOW\n'
    '    static final long MAX_RIVER_DEVICE_AGE_MS = 30L * 60L * 1000L; // V0918_LOCK_RIVER_LOCATION_WINDOW',
    1)
old = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {
        return freshDeviceLocation(locationTime, now, lat, lon) && insideNepal(lat, lon);
    }'''
new = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {
        if (!insideNepal(lat, lon) || locationTime <= 0L) return false;
        long age = now - locationTime;
        return age <= MAX_RIVER_DEVICE_AGE_MS && age >= -FUTURE_TOLERANCE_MS;
    }'''
if old in ps:
    ps = ps.replace(old, new, 1)
if 'V0918_LOCK_RIVER_LOCATION_WINDOW' not in ps:
    raise SystemExit('location policy patch failed')
policy.write_text(ps, encoding='utf-8')

# Guard direct river notifications with the tighter river-location freshness window.
live = JAVA / 'FloodLiveGaugeMonitor.java'
ls = live.read_text(encoding='utf-8')
needle = 'double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN))),homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));\n        if(!insideNepal(homeLat,homeLon))return;'
replacement = 'double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN))),homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));\n        long locationTime=monitor.getLong("location_time",0L);\n        if(!MonitoringLocationPolicy.freshNepalDeviceLocation(locationTime,System.currentTimeMillis(),homeLat,homeLon))return; // V0918_LOCK_FRESH_RIVER_GUARD\n        '
if 'V0918_LOCK_FRESH_RIVER_GUARD' not in ls:
    if needle not in ls:
        raise SystemExit('live river location marker missing')
    ls = ls.replace(needle, replacement, 1)
live.write_text(ls, encoding='utf-8')

# Direct foreground-service weather/rain notifier so Doze-delayed WorkManager is not the only path.
(JAVA / 'LockedNotificationMonitor.java').write_text(r'''package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
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
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

final class LockedNotificationMonitor {
    private static final long CHECK_MS=2L*60L*1000L, DIGEST_MS=3L*60L*60L*1000L;
    private static final double WET_MM=.10d;
    private static final String RAIN_CH="floodsafe_lock_rain_v1", WEATHER_CH="floodsafe_lock_weather_v1";
    private final Context app;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final AtomicBoolean busy=new AtomicBoolean(false);
    private volatile boolean running;

    LockedNotificationMonitor(Context c){app=c.getApplicationContext();}
    void start(){if(running)return;running=true;channels();main.postDelayed(tick,5000L);}
    void stop(){running=false;main.removeCallbacks(tick);io.shutdownNow();}
    private final Runnable tick=new Runnable(){@Override public void run(){
        if(!running)return;
        if(busy.compareAndSet(false,true))io.execute(()->{try{check();}catch(Exception ignored){}finally{busy.set(false);}});
        main.postDelayed(this,CHECK_MS);
    }};

    private void check() throws Exception{
        SharedPreferences p=app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE);
        if(!p.getBoolean("enabled",false))return;
        if(Build.VERSION.SDK_INT>=33&&app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
        double lat=Double.longBitsToDouble(p.getLong("lat",Double.doubleToRawLongBits(Double.NaN)));
        double lon=Double.longBitsToDouble(p.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));
        long locationAt=p.getLong("location_time",0L),nowMs=System.currentTimeMillis();
        if(!MonitoringLocationPolicy.freshDeviceLocation(locationAt,nowMs,lat,lon))return;
        JSONObject data=fetch(lat,lon),cur=data.optJSONObject("current");
        double mm=max(num(cur,"precipitation"),num(cur,"rain"),num(cur,"showers"));
        int code=cur==null?-1:cur.optInt("weather_code",-1);
        boolean raining=mm>=WET_MM||wetCode(code),known=p.getBoolean("lock_rain_known",false),old=p.getBoolean("lock_raining",false);
        if(!known)p.edit().putBoolean("lock_rain_known",true).putBoolean("lock_raining",raining).apply();
        else if(old!=raining){
            p.edit().putBoolean("lock_raining",raining).putLong("last_alert",nowMs).apply();
            high(7411,raining?"🌧️ वर्षा सुरु भएको छ":"🌤️ वर्षा रोकिएको छ",raining?"हालको स्थानमा वर्षा सुरु भएको देखिन्छ।":"हालको स्थानमा वर्षा रोकिएको देखिन्छ।");
        }
        ZonedDateTime now=ZonedDateTime.now(zone(data.optString("timezone","Asia/Kathmandu")));
        ZonedDateTime rainAt=nextRain(data.optJSONObject("minutely_15"),now);
        if(!raining&&rainAt!=null){long lead=Math.max(0,java.time.Duration.between(now,rainAt).toMinutes());if(lead<=35){String k=rainAt.withSecond(0).withNano(0).toString();if(!k.equals(p.getString("lock_next_rain", ""))){p.edit().putString("lock_next_rain",k).putLong("last_alert",nowMs).apply();high(7411,"☔ वर्षा सुरु हुन सक्छ","करिब "+Math.max(1,lead)+" मिनेटभित्र वर्षाको संकेत छ।");}}}
        if(thunder(code,data.optJSONObject("hourly"),now)){String k=now.toLocalDate()+"-"+(now.getHour()/3);if(!k.equals(p.getString("lock_thunder", ""))){p.edit().putString("lock_thunder",k).apply();high(7412,"⚡ मेघगर्जन / चट्याङ सम्भावना","हालको वा आगामी केही घण्टामा thunderstorm संकेत देखिएको छ।");}}
        long last=p.getLong("last_weather_digest_at",0L);
        if(last<=0||nowMs-last>=DIGEST_MS){double t=num(cur,"temperature_2m"),h=num(cur,"relative_humidity_2m"),w=num(cur,"wind_speed_10m");int prob=maxProb(data.optJSONObject("hourly"),now);StringBuilder b=new StringBuilder();if(Double.isFinite(t))b.append("अहिले ").append(Math.round(t)).append("°C");if(prob>=0)add(b,"वर्षा "+prob+"%");if(Double.isFinite(w))add(b,"हावा "+Math.round(w)+" km/h");if(Double.isFinite(h))add(b,"आर्द्रता "+Math.round(h)+"%");if(b.length()>0){p.edit().putLong("last_weather_digest_at",nowMs).apply();normal(7413,"🌤️ ३ घण्टाको मौसम अपडेट",b.toString());}}
    }

    private JSONObject fetch(double lat,double lon)throws Exception{
        String q="latitude="+URLEncoder.encode(String.valueOf(lat),"UTF-8")+"&longitude="+URLEncoder.encode(String.valueOf(lon),"UTF-8")+"&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m&minutely_15=precipitation,rain,showers&hourly=precipitation_probability,weather_code&forecast_hours=4&timezone=auto";
        HttpURLConnection c=(HttpURLConnection)new URL("https://api.open-meteo.com/v1/forecast?"+q).openConnection();c.setConnectTimeout(10000);c.setReadTimeout(10000);c.setUseCaches(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache");int status=c.getResponseCode();if(status!=200){c.disconnect();throw new IllegalStateException("weather "+status);}StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null)b.append(line);}finally{c.disconnect();}return new JSONObject(b.toString());
    }
    private static ZonedDateTime nextRain(JSONObject x,ZonedDateTime now){if(x==null)return null;JSONArray t=x.optJSONArray("time"),p=x.optJSONArray("precipitation"),r=x.optJSONArray("rain"),s=x.optJSONArray("showers");if(t==null)return null;for(int i=0;i<t.length();i++){ZonedDateTime z=slot(t.optString(i),now.getZone());if(z==null||z.plusMinutes(15).isBefore(now))continue;if(max(at(p,i),at(r,i),at(s,i))>=WET_MM)return z;}return null;}
    private static boolean thunder(int current,JSONObject h,ZonedDateTime now){if(current==95||current==96||current==99)return true;if(h==null)return false;JSONArray t=h.optJSONArray("time"),c=h.optJSONArray("weather_code");if(t==null||c==null)return false;ZonedDateTime end=now.plusHours(3).plusMinutes(30);for(int i=0;i<t.length()&&i<c.length();i++){ZonedDateTime z=slot(t.optString(i),now.getZone());if(z==null||z.isBefore(now.minusMinutes(30))||z.isAfter(end))continue;int v=c.optInt(i,-1);if(v==95||v==96||v==99)return true;}return false;}
    private static int maxProb(JSONObject h,ZonedDateTime now){if(h==null)return -1;JSONArray t=h.optJSONArray("time"),p=h.optJSONArray("precipitation_probability");if(t==null||p==null)return -1;int m=-1;ZonedDateTime end=now.plusHours(3).plusMinutes(30);for(int i=0;i<t.length()&&i<p.length();i++){ZonedDateTime z=slot(t.optString(i),now.getZone());if(z!=null&&!z.isBefore(now.minusMinutes(30))&&!z.isAfter(end))m=Math.max(m,p.optInt(i,-1));}return m;}
    private void channels(){if(Build.VERSION.SDK_INT<26)return;NotificationManager n=app.getSystemService(NotificationManager.class);if(n==null)return;NotificationChannel a=new NotificationChannel(RAIN_CH,"FloodSafe lock-screen rain/events",NotificationManager.IMPORTANCE_HIGH);a.enableVibration(true);a.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);n.createNotificationChannel(a);NotificationChannel b=new NotificationChannel(WEATHER_CH,"FloodSafe lock-screen weather",NotificationManager.IMPORTANCE_DEFAULT);b.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);n.createNotificationChannel(b);}
    private void high(int id,String title,String text){notify(id,title,text,RAIN_CH,true);}
    private void normal(int id,String title,String text){notify(id,title,text,WEATHER_CH,false);}
    private void notify(int id,String title,String text,String ch,boolean high){NotificationManager n=app.getSystemService(NotificationManager.class);if(n==null)return;Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(app,ch):new Notification.Builder(app);Notification out=b.setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(text).setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true).setContentIntent(open(id)).setVisibility(Notification.VISIBILITY_PUBLIC).setPriority(high?Notification.PRIORITY_HIGH:Notification.PRIORITY_DEFAULT).build();n.notify(id,out);}
    private PendingIntent open(int rc){Intent i=new Intent(app,NativeFullActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);return PendingIntent.getActivity(app,rc,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    private static ZonedDateTime slot(String s,ZoneId z){try{return LocalDateTime.parse(s,DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(z);}catch(Exception e){return null;}}
    private static ZoneId zone(String s){try{return ZoneId.of(s);}catch(Exception e){return ZoneId.of("Asia/Kathmandu");}}
    private static double num(JSONObject o,String k){return o==null?Double.NaN:number(o.opt(k));}private static double at(JSONArray a,int i){return a==null?Double.NaN:number(a.opt(i));}private static double number(Object v){if(v instanceof Number)return((Number)v).doubleValue();try{return v==null?Double.NaN:Double.parseDouble(String.valueOf(v));}catch(Exception e){return Double.NaN;}}private static double max(double...v){double m=0;for(double x:v)if(Double.isFinite(x))m=Math.max(m,x);return m;}private static boolean wetCode(int c){return(c>=51&&c<=67)||(c>=80&&c<=82)||(c>=95&&c<=99);}private static void add(StringBuilder b,String s){if(b.length()>0)b.append(" • ");b.append(s);}
}
''',encoding='utf-8')

# Attach notification heartbeat to existing foreground monitor.
service=JAVA/'FloodMonitorService.java'
ss=service.read_text(encoding='utf-8')
if 'LockedNotificationMonitor lockedNotificationMonitor;' not in ss:
    ss=ss.replace('private FloodLiveGaugeMonitor liveHydrologyMonitor;','private FloodLiveGaugeMonitor liveHydrologyMonitor;\n    private LockedNotificationMonitor lockedNotificationMonitor; // V0918_LOCK_NOTIFICATION_MONITOR_FIELD',1)
    ss=ss.replace('liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);','liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);\n        lockedNotificationMonitor = new LockedNotificationMonitor(this);',1)
    ss=ss.replace('if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();','if (liveHydrologyMonitor != null) liveHydrologyMonitor.start();\n        if (lockedNotificationMonitor != null) lockedNotificationMonitor.start(); // V0918_LOCK_NOTIFICATION_MONITOR_START',1)
    dm='    @Override public void onDestroy() {\n'
    if dm not in ss: raise SystemExit('service onDestroy marker missing')
    ss=ss.replace(dm,dm+'        if (lockedNotificationMonitor != null) { try { lockedNotificationMonitor.stop(); } catch (RuntimeException ignored) { } lockedNotificationMonitor = null; } // V0918_LOCK_NOTIFICATION_MONITOR_STOP\n',1)
service.write_text(ss,encoding='utf-8')

# One-time Android battery-optimization exemption request for notification reliability.
(JAVA/'NotificationReliability.java').write_text(r'''package io.github.pujan1234hub.floodsafe.app;
import android.app.Activity;import android.content.Context;import android.content.Intent;import android.net.Uri;import android.os.Build;import android.os.Handler;import android.os.Looper;import android.os.PowerManager;import android.provider.Settings;
final class NotificationReliability{
 private static final String P="floodsafe_notification_reliability",K="battery_prompted_v1";private NotificationReliability(){}
 static void requestBatteryExemptionOnce(Activity a){if(a==null||Build.VERSION.SDK_INT<23||a.getSharedPreferences(P,Context.MODE_PRIVATE).getBoolean(K,false))return;PowerManager p=a.getSystemService(PowerManager.class);if(p==null||p.isIgnoringBatteryOptimizations(a.getPackageName())){a.getSharedPreferences(P,Context.MODE_PRIVATE).edit().putBoolean(K,true).apply();return;}a.getSharedPreferences(P,Context.MODE_PRIVATE).edit().putBoolean(K,true).apply();new Handler(Looper.getMainLooper()).postDelayed(()->{if(a.isFinishing()||a.isDestroyed())return;try{a.startActivity(new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,Uri.parse("package:"+a.getPackageName())));}catch(RuntimeException ignored){}},1800L);}
}
''',encoding='utf-8')

activity=JAVA/'NativeFullActivity.java'
asrc=activity.read_text(encoding='utf-8')
if 'NotificationReliability.requestBatteryExemptionOnce(this);' not in asrc:
    am='        enableMonitoring();\n'
    if am not in asrc: raise SystemExit('activity monitoring marker missing')
    asrc=asrc.replace(am,am+'        NotificationReliability.requestBatteryExemptionOnce(this); // V0918_LOCK_BATTERY_RELIABILITY\n',1)
activity.write_text(asrc,encoding='utf-8')

print('v0.9.18 notification-only lock-screen reliability patch applied')
