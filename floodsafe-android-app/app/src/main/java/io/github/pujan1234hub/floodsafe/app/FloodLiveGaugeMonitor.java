package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * One-second foreground-service rechecker for official BIPAD/DHM hydrology sources.
 * River, rainfall and the public hydrology/flood/streamflow station feeds are fetched
 * independently.  The one-second scheduler never overlaps a still-running request.
 */
final class FloodLiveGaugeMonitor {
    private static final String RIVER_ENDPOINT="https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String BIPAD="https://bipadportal.gov.np/api/v1/";
    private static final String RAIN_ENDPOINT=BIPAD+"rain-stations/?limit=2000";
    private static final String[] HYDRO_ENDPOINTS={
            BIPAD+"flood-station/?limit=2000",
            BIPAD+"streamflow/?limit=2000",
            BIPAD+"station-location/?limit=2000"
    };
    private static final String ALERT_CHANNEL="official_nepal_alerts_v3";
    private static final String PUSH_PREFS="floodsafe_push_guard";
    private static final double RADIUS_KM=2d;
    private static final long WARNING_REPEAT_MS=90L*60L*1000L;
    private static final long DANGER_REPEAT_MS=30L*60L*1000L;
    private static final double MATERIAL_RISE_METRES=0.20d;

    private final Context app;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService io=Executors.newFixedThreadPool(3);
    private final AtomicBoolean riverInFlight=new AtomicBoolean(false);
    private final AtomicBoolean rainInFlight=new AtomicBoolean(false);
    private final AtomicBoolean hydroInFlight=new AtomicBoolean(false);
    private volatile boolean running=false;
    private volatile int lastRiverHash=0,lastRainHash=0,lastHydroHash=0;

    FloodLiveGaugeMonitor(Context context){app=context.getApplicationContext();}
    void start(){if(running)return;running=true;handler.post(tick);}
    void stop(){running=false;handler.removeCallbacks(tick);io.shutdownNow();}

    private final Runnable tick=new Runnable(){@Override public void run(){
        if(!running)return;
        if(riverInFlight.compareAndSet(false,true))io.execute(()->{try{pollRiverOnce();}catch(Exception ignored){}finally{riverInFlight.set(false);}});
        if(rainInFlight.compareAndSet(false,true))io.execute(()->{try{pollRainOnce();}catch(Exception ignored){}finally{rainInFlight.set(false);}});
        if(hydroInFlight.compareAndSet(false,true))io.execute(()->{try{pollHydrologyOnce();}catch(Exception ignored){}finally{hydroInFlight.set(false);}});
        handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK
    }};

    private void pollRiverOnce() throws Exception{
        String body=fetch(RIVER_ENDPOINT+"?_bg="+System.currentTimeMillis());if(body.isEmpty())return;
        markPoll("live_gauge_poll_time");int hash=hash(body);if(hash==lastRiverHash)return;lastRiverHash=hash;
        cacheBody("floodsafe_live_gauges",body,"live_gauge_change_time");
        try{checkNearbyHazards(new JSONObject(body));}catch(Exception ignored){}
    }

    private void pollRainOnce() throws Exception{
        String body=fetch(RAIN_ENDPOINT+"&_bg="+System.currentTimeMillis());if(body.isEmpty())return;
        markPoll("live_rain_poll_time");int hash=hash(body);if(hash==lastRainHash)return;lastRainHash=hash;
        cacheBody("floodsafe_live_rain",body,"live_rain_change_time");
    }

    private void pollHydrologyOnce() throws Exception{
        JSONObject merged=new JSONObject();JSONArray feeds=new JSONArray();
        for(String endpoint:HYDRO_ENDPOINTS){
            try{
                String body=fetch(endpoint+"&_bg="+System.currentTimeMillis());if(body.isEmpty())continue;
                JSONObject item=new JSONObject();item.put("endpoint",endpoint);item.put("payload",new JSONObject(body));feeds.put(item);
            }catch(Exception ignored){}
        }
        if(feeds.length()==0)return;merged.put("feeds",feeds);String body=merged.toString();
        markPoll("live_hydrology_poll_time");int hash=hash(body);if(hash==lastHydroHash)return;lastHydroHash=hash;
        cacheBody("floodsafe_live_hydrology",body,"live_hydrology_change_time");
        // A flood/streamflow row with the same standard level/status fields is allowed
        // to trigger the same verified 2 km warning/danger guard; metadata-only rows do nothing.
        for(int i=0;i<feeds.length();i++)try{JSONObject item=feeds.optJSONObject(i);if(item!=null)checkNearbyHazards(item.optJSONObject("payload"));}catch(Exception ignored){}
    }

    private String fetch(String url)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();
        c.setConnectTimeout(4500);c.setReadTimeout(6000);c.setUseCaches(false);
        c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store");c.setRequestProperty("Pragma","no-cache");
        int code=c.getResponseCode();if(code!=200){c.disconnect();return"";}
        StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null)b.append(line);}finally{c.disconnect();}
        return b.toString();
    }

    private static int hash(String body){return 31*body.length()+body.hashCode();}
    private void markPoll(String key){app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE).edit().putLong(key,System.currentTimeMillis()).apply();}

    private void cacheBody(String base,String body,String changedKey){
        try{
            File tmp=new File(app.getFilesDir(),base+".tmp"),out=new File(app.getFilesDir(),base+".json");
            try(FileOutputStream f=new FileOutputStream(tmp,false)){f.write(body.getBytes(StandardCharsets.UTF_8));f.flush();}
            if(!tmp.renameTo(out)){try(FileOutputStream f=new FileOutputStream(out,false)){f.write(body.getBytes(StandardCharsets.UTF_8));}tmp.delete();}
            app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE).edit().putLong(changedKey,System.currentTimeMillis()).apply();
        }catch(Exception ignored){}
    }

    private void checkNearbyHazards(JSONObject root){
        if(root==null)return;SharedPreferences monitor=app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE);
        if(!monitor.getBoolean("enabled",false)||!monitor.getBoolean("follow_device",false))return;
        if(Build.VERSION.SDK_INT>=33&&app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
        double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN))),homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));
        if(!insideNepal(homeLat,homeLon))return;JSONArray rows=array(root,"results","current","stations","data");if(rows==null)return;
        long now=System.currentTimeMillis();int shown=0;
        for(int i=0;i<rows.length()&&shown<3;i++){
            JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");double[] p=coord(row,f);double la=p[0],lo=p[1];double distance=haversineKm(homeLat,homeLon,la,lo);if(!insideNepal(la,lo)||distance>RADIUS_KM)continue;
            double level=num(row,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");
            double warning=num(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),danger=num(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold");
            String raw=str(row,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT),stage=stage(level,warning,danger,raw);if(!"warning".equals(stage)&&!"danger".equals(stage))continue;
            String id=str(row,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),name=str(row,f,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official hydrology station";if(id.isEmpty())id=name+"@"+String.format(Locale.US,"%.5f,%.5f",la,lo);
            if(!claim(id,stage,level,now))continue;notifyHazard(id,name,stage,distance,level);shown++;
        }
    } // V0872_BACKGROUND_2KM_SOURCE_ALERTS

    private boolean claim(String id,String stage,double level,long now){SharedPreferences g=app.getSharedPreferences(PUSH_PREFS,Context.MODE_PRIVATE);String key="river_"+Integer.toHexString(id.hashCode());String oldStage=g.getString(key+"_stage","");double oldLevel=Double.longBitsToDouble(g.getLong(key+"_level",Double.doubleToRawLongBits(Double.NaN)));long oldAt=g.getLong(key+"_at",0L);boolean changed=!stage.equals(oldStage),risen=Double.isFinite(level)&&Double.isFinite(oldLevel)&&level>=oldLevel+MATERIAL_RISE_METRES;long gap="danger".equals(stage)?DANGER_REPEAT_MS:WARNING_REPEAT_MS;if(!changed&&!risen&&oldAt>0L&&now-oldAt<gap)return false;SharedPreferences.Editor e=g.edit().putString(key+"_stage",stage).putLong(key+"_at",now);if(Double.isFinite(level))e.putLong(key+"_level",Double.doubleToRawLongBits(level));e.apply();return true;}

    private void notifyHazard(String id,String name,String stage,double distance,double level){NotificationManager nm=app.getSystemService(NotificationManager.class);if(nm==null)return;if(Build.VERSION.SDK_INT>=26){NotificationChannel ch=new NotificationChannel(ALERT_CHANNEL,"Nearby river and Nepal alerts",NotificationManager.IMPORTANCE_HIGH);ch.enableVibration(true);Uri sound=android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI;AudioAttributes aa=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();ch.setSound(sound,aa);nm.createNotificationChannel(ch);}String title="danger".equals(stage)?"🚨 नजिकको जलस्रोत खतरा चेतावनी":"⚠️ नजिकको जलस्रोत चेतावनी";String text=name+String.format(Locale.US," • %.1f km",distance)+(Double.isFinite(level)?String.format(Locale.US," • %.3f m",level):"")+" • BIPAD/DHM official";Intent launch=new Intent(app,NativeFullActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);int rc=7600+Math.abs(id.hashCode()%300);PendingIntent pi=PendingIntent.getActivity(app,rc,launch,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);Notification.Builder nb=Build.VERSION.SDK_INT>=26?new Notification.Builder(app,ALERT_CHANNEL):new Notification.Builder(app);Notification n=nb.setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(text).setStyle(new Notification.BigTextStyle().bigText(text)).setAutoCancel(true).setContentIntent(pi).build();nm.notify(rc,n);}

    private static JSONArray array(JSONObject root,String... keys){for(String k:keys){Object v=root.opt(k);if(v instanceof JSONArray)return(JSONArray)v;if(v instanceof JSONObject){JSONArray a=((JSONObject)v).optJSONArray("results");if(a!=null)return a;}}return null;}
    private static double[] coord(JSONObject r,JSONObject f){double la=num(r,f,"latitude","lat","stationLatitude","station_latitude","stationLat"),lo=num(r,f,"longitude","lon","lng","stationLongitude","station_longitude","stationLon");if(Double.isFinite(la)&&Double.isFinite(lo))return new double[]{la,lo};Object p=r.opt("point");if((p==null||p==JSONObject.NULL)&&f!=null)p=f.opt("point");try{JSONObject po=p instanceof JSONObject?(JSONObject)p:null;JSONArray a=p instanceof JSONArray?(JSONArray)p:null;if(po!=null)a=po.optJSONArray("coordinates");if(a!=null&&a.length()>=2){lo=a.optDouble(0,Double.NaN);la=a.optDouble(1,Double.NaN);}}catch(Exception ignored){}return new double[]{la,lo};}
    private static double num(JSONObject r,JSONObject f,String... keys){for(String k:keys){double n=toNum(r==null?null:r.opt(k));if(Double.isFinite(n))return n;n=toNum(f==null?null:f.opt(k));if(Double.isFinite(n))return n;}return Double.NaN;}
    private static double toNum(Object v){if(v instanceof Number)return((Number)v).doubleValue();if(v!=null&&v!=JSONObject.NULL)try{return Double.parseDouble(String.valueOf(v).trim());}catch(Exception ignored){}return Double.NaN;}
    private static String str(JSONObject r,JSONObject f,String... keys){for(String k:keys){Object v=r==null?null:r.opt(k);if(v!=null&&v!=JSONObject.NULL&&!String.valueOf(v).trim().isEmpty())return String.valueOf(v).trim();v=f==null?null:f.opt(k);if(v!=null&&v!=JSONObject.NULL&&!String.valueOf(v).trim().isEmpty())return String.valueOf(v).trim();}return"";}
    private static String stage(double level,double warning,double danger,String raw){if(Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)return"danger";if((raw.contains("DANGER")||raw.contains("RED"))&&!raw.contains("BELOW DANGER"))return"danger";if(Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)return"warning";if((raw.contains("WARNING")||raw.contains("ORANGE"))&&!raw.contains("BELOW WARNING"))return"warning";if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")||raw.contains("RISING")||raw.contains("INCREASING"))return"alert";return"normal";}
    private static boolean insideNepal(double la,double lo){return Double.isFinite(la)&&Double.isFinite(lo)&&la>=26.2&&la<=30.5&&lo>=80&&lo<=88.35;}
    private static double haversineKm(double a,double b,double c,double d){double R=6371,dp=Math.toRadians(c-a),dl=Math.toRadians(d-b);double q=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(dl/2)*Math.sin(dl/2);return 2*R*Math.asin(Math.sqrt(q));}
}
