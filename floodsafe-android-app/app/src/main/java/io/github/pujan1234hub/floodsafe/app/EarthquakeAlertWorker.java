package io.github.pujan1234hub.floodsafe.app;
import android.Manifest;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.SystemClock;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.Map;

/** Post-event catalogue notifications, not an earthquake early-warning or prediction system. */
public final class EarthquakeAlertWorker extends Worker {
    private static final String FEED="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson";
    private static final long MAX_AGE=2L*60L*60L*1000L;
    private static final double NEAR_KM=100d;
    private static long lastAttempt=-1L;
    private static NepalRiverBoundary boundary;
    public EarthquakeAlertWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
    @NonNull @Override public Result doWork(){try{poll(getApplicationContext());return Result.success();}catch(Exception e){return Result.retry();}}
    static synchronized void poll(Context app)throws Exception{
        SharedPreferences monitoring=app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE);
        if(!monitoring.getBoolean("enabled",false))return;
        if(Build.VERSION.SDK_INT>=33&&app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
        NotificationManager nm=app.getSystemService(NotificationManager.class);
        if(nm==null||!nm.areNotificationsEnabled())return;
        long elapsed=SystemClock.elapsedRealtime();
        if(lastAttempt>=0&&elapsed-lastAttempt<60_000L)return;lastAttempt=elapsed;
        if(boundary==null){try(InputStream in=app.getAssets().open("floodsafe-nepal/v24/nepal-districts.geojson")){boundary=new NepalRiverBoundary(read(in,15_000_000));}}
        JSONObject catalog=fetch();JSONArray events=catalog.optJSONArray("features");if(events==null)throw new IllegalStateException("Earthquake feed unavailable");
        long now=System.currentTimeMillis();
        double la=Double.longBitsToDouble(monitoring.getLong("device_lat",Double.doubleToRawLongBits(Double.NaN))),lo=Double.longBitsToDouble(monitoring.getLong("device_lon",Double.doubleToRawLongBits(Double.NaN)));
        boolean gps=(app.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED||app.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED)&&MonitoringLocationPolicy.freshDeviceLocation(monitoring.getLong("device_location_time",0L),now,la,lo);
        boolean english=app.getSharedPreferences("floodsafe-native-full",Context.MODE_PRIVATE).getBoolean("lang_en",false);
        SharedPreferences seen=app.getSharedPreferences("floodsafe_earthquake_seen_v1",Context.MODE_PRIVATE);
        SharedPreferences.Editor prune=seen.edit();
        for(Map.Entry<String,?> e:seen.getAll().entrySet())if(e.getValue() instanceof Long&&now-(Long)e.getValue()>3L*86400000L)prune.remove(e.getKey());prune.apply();
        for(int i=0;i<events.length();i++){
            JSONObject event=events.optJSONObject(i);if(event==null)continue;
            JSONObject p=event.optJSONObject("properties"),g=event.optJSONObject("geometry");if(p==null||g==null||!"earthquake".equals(p.optString("type")))continue;
            JSONArray xy=g.optJSONArray("coordinates");if(xy==null||xy.length()<2)continue;
            double lon=xy.optDouble(0,Double.NaN),lat=xy.optDouble(1,Double.NaN);
            if(!Double.isFinite(lon)||!Double.isFinite(lat)||Math.abs(lat)>90||Math.abs(lon)>180)continue;
            long at=p.optLong("time",0);if(at<=0||at>now||now-at>MAX_AGE)continue;
            String id=event.optString("id","");if(id.isEmpty()||seen.contains(id))continue;
            boolean nepal=boundary.contains(lon,lat);double km=gps?distance(la,lo,lat,lon):Double.NaN;
            if(!nepal&&(!Double.isFinite(km)||km>NEAR_KM))continue;
            String district=nepal?boundary.districtAt(lon,lat):"";
            String where=!district.isEmpty()?district+", Nepal":nepal?"Nepal":p.optString("place",String.format(Locale.US,"%.2f, %.2f",lat,lon));
            double magnitude=p.optDouble("mag",Double.NaN);
            String mag=Double.isFinite(magnitude)?String.format(Locale.US,"M %.1f",magnitude):(english?"Magnitude unavailable":"परिमाण उपलब्ध छैन");
            String title=english?"Earthquake recorded":"भूकम्प रेकर्ड भएको छ";
            String time=Instant.ofEpochMilli(at).atZone(nepal?ZoneId.of("Asia/Kathmandu"):ZoneId.systemDefault()).format(DateTimeFormatter.ofPattern("dd MMM HH:mm z",Locale.ENGLISH));
            String body=mag+" • "+where+" • "+time+(Double.isFinite(km)?String.format(Locale.US," • %.0f km",km):"")+" • USGS";
            int request=0x42000000|(id.hashCode()&0x00ffffff);
            Intent open=new Intent(app,NativeFullActivity.class).putExtra(NativeFullActivity.EXTRA_OPEN_HOME,true).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pi=PendingIntent.getActivity(app,request,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            Notification notification=new Notification.Builder(app,FloodSafeSounds.channel(app,false,false)).setSmallIcon(R.drawable.ic_floodsafe).setContentTitle(title).setContentText(body).setStyle(new Notification.BigTextStyle().bigText(body)).setContentIntent(pi).setAutoCancel(true).build();
            nm.notify(request,notification);seen.edit().putLong(id,now).apply();
        }
    }
    private static JSONObject fetch()throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(FEED).openConnection();c.setConnectTimeout(10000);c.setReadTimeout(15000);c.setRequestProperty("Accept","application/geo+json, application/json");try{if(c.getResponseCode()!=200)throw new IllegalStateException("Earthquake feed unavailable");try(InputStream in=c.getInputStream()){return new JSONObject(read(in,4_000_000));}}finally{c.disconnect();}}
    private static String read(InputStream in,int max)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>max)throw new IllegalStateException("Feed too large");out.write(b,0,n);}return new String(out.toByteArray(),StandardCharsets.UTF_8);}
    static double distance(double a,double o,double b,double p){double x=Math.toRadians(b-a),y=Math.toRadians(p-o),v=Math.sin(x/2)*Math.sin(x/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(b))*Math.sin(y/2)*Math.sin(y/2);return 6371d*2*Math.asin(Math.sqrt(Math.max(0d,Math.min(1d,v))));}
}
