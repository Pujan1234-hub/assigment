package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Direct read-only mirror of the official DHM Rainfall Watch Map. */
final class DhmRainMirror {
    static final String PAGE="https://dhm.gov.np/hydrology/rainfall-watch-map";
    static final String API="https://dhm.gov.np/hydrology/getRainfallFilter";
    static final String PREFS="floodsafe_dhm_rain_mirror_v1";
    static final String CACHE="rows_json";
    static final long POLL_MS=5L*60L*1000L; // DHM's own page refresh cadence.
    private static final ScheduledExecutorService EXEC=Executors.newSingleThreadScheduledExecutor();
    private static final AtomicBoolean STARTED=new AtomicBoolean(false),BUSY=new AtomicBoolean(false);
    private static final Map<String,RainRow> ROWS=new ConcurrentHashMap<>();
    private static volatile String updated="", error="";

    private DhmRainMirror(){}

    static void ensureStarted(Context c){
        Context app=c.getApplicationContext();
        loadCache(app);
        if(STARTED.compareAndSet(false,true)){
            EXEC.scheduleWithFixedDelay(()->refresh(app),0,POLL_MS,TimeUnit.MILLISECONDS);
        }else refreshAsync(app);
    }

    static void refreshAsync(Context c){Context app=c.getApplicationContext();EXEC.execute(()->refresh(app));}

    private static void refresh(Context app){
        if(!BUSY.compareAndSet(false,true))return;
        try{
            Session s=openPage();
            Map<String,RainRow> next=new ConcurrentHashMap<>();String newest="";
            for(int hour:new int[]{1,3,6,12,24}){
                JSONObject root=postHour(s,hour);if(!"success".equalsIgnoreCase(root.optString("status")))continue;
                JSONObject data=root.optJSONObject("data");if(data==null)continue;
                JSONArray arr=data.optJSONArray("0");if(arr==null)continue;
                String stamp=data.optString("rainfall_date_time","");if(!stamp.isEmpty())newest=stamp;
                for(int i=0;i<arr.length();i++){
                    JSONObject o=arr.optJSONObject(i);if(o==null)continue;
                    String name=o.optString("name","").trim();if(name.isEmpty())continue;
                    String key=key(name);RainRow r=next.get(key);if(r==null){r=new RainRow();r.name=name;r.id=o.optString("id","");r.seriesId=o.optString("series_id","");r.basin=o.optString("basin","");r.district=o.optString("district","");r.lat=num(o.opt("latitude"));r.lon=num(o.opt("longitude"));r.status=o.optString("status","");next.put(key,r);}
                    double v=num(o.opt("value"));if(hour==1)r.h1=v;else if(hour==3)r.h3=v;else if(hour==6)r.h6=v;else if(hour==12)r.h12=v;else r.h24=v;
                    String st=o.optString("status","");if(!st.isEmpty())r.status=st;
                }
            }
            if(!next.isEmpty()){
                ROWS.clear();ROWS.putAll(next);updated=newest;error="";saveCache(app);
                app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE).edit().putLong("dhm_rain_mirror_at",System.currentTimeMillis()).apply();
            }else error="DHM rainfall source returned no rows";
        }catch(Exception e){error=e.getClass().getSimpleName()+": "+String.valueOf(e.getMessage());}
        finally{BUSY.set(false);}
    }

    private static Session openPage()throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(PAGE+"?_fs="+System.currentTimeMillis()).openConnection();
        c.setConnectTimeout(7000);c.setReadTimeout(9000);c.setUseCaches(false);c.setRequestProperty("User-Agent","Mozilla/5.0 FloodSafe-Nepal/0.8.95");c.setRequestProperty("Cache-Control","no-cache, no-store");
        String html=read(c);String cookie=c.getHeaderField("Set-Cookie");c.disconnect();
        Matcher m=Pattern.compile("name=\\\"csrf_test_name\\\"\\s+value=\\\"([^\\\"]+)\\\"").matcher(html);if(!m.find())throw new IllegalStateException("DHM CSRF token missing");
        Session s=new Session();s.csrf=m.group(1);s.cookie=cookie==null?"":cookie.split(";",2)[0];return s;
    }

    private static JSONObject postHour(Session s,int hour)throws Exception{
        String body="csrf_test_name="+enc(s.csrf)+"&type=0&mapValue=all&hour="+hour;
        HttpURLConnection c=(HttpURLConnection)new URL(API).openConnection();c.setConnectTimeout(7000);c.setReadTimeout(10000);c.setUseCaches(false);c.setDoOutput(true);c.setRequestMethod("POST");
        c.setRequestProperty("User-Agent","Mozilla/5.0 FloodSafe-Nepal/0.8.95");c.setRequestProperty("Accept","application/json");c.setRequestProperty("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");c.setRequestProperty("X-Requested-With","XMLHttpRequest");c.setRequestProperty("Referer",PAGE);c.setRequestProperty("Cache-Control","no-cache, no-store");if(!s.cookie.isEmpty())c.setRequestProperty("Cookie",s.cookie);
        try(OutputStream out=c.getOutputStream()){out.write(body.getBytes(StandardCharsets.UTF_8));}
        String text=read(c);c.disconnect();return new JSONObject(text);
    }

    private static String read(HttpURLConnection c)throws Exception{int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null)b.append(line);}return b.toString();}
    private static String enc(String s)throws Exception{return URLEncoder.encode(s,"UTF-8");}
    private static double num(Object v){if(v instanceof Number)return((Number)v).doubleValue();if(v!=null&&v!=JSONObject.NULL)try{return Double.parseDouble(String.valueOf(v).replace(",","").trim());}catch(Exception ignored){}return Double.NaN;}
    private static String key(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]","");}

    static String detailFor(String stationName){
        if(ROWS.isEmpty()||stationName==null)return null;String q=key(stationName);RainRow best=ROWS.get(q);
        if(best==null){int score=-1;for(RainRow r:ROWS.values()){String k=key(r.name);int x=(k.contains(q)||q.contains(k))?Math.min(k.length(),q.length()):0;if(x>score){score=x;best=x>=5?r:null;}}}
        if(best==null)return null;StringBuilder b=new StringBuilder();b.append("🌧️ DHM Rainfall Watch — official\n").append(best.name);if(!best.basin.isEmpty())b.append("\nBasin: ").append(best.basin);if(!best.district.isEmpty())b.append("\nDistrict: ").append(best.district);
        b.append("\n\n1 hr: ").append(mm(best.h1)).append("\n3 hr: ").append(mm(best.h3)).append("\n6 hr: ").append(mm(best.h6)).append("\n12 hr: ").append(mm(best.h12)).append("\n24 hr: ").append(mm(best.h24));
        if(!best.status.isEmpty())b.append("\nStatus: ").append(best.status);if(!updated.isEmpty())b.append("\nOfficial update: ").append(updated);b.append("\nSource: DHM Rainfall Watch Map");return b.toString();
    }

    static String nearestSummary(double lat,double lon){
        RainRow best=null;double bd=Double.POSITIVE_INFINITY;for(RainRow r:ROWS.values()){if(!Double.isFinite(r.lat)||!Double.isFinite(r.lon))continue;double d=km(lat,lon,r.lat,r.lon);if(d<bd){bd=d;best=r;}}
        if(best==null)return null;return best.name+String.format(Locale.US," • %.1f km • 1h %s • 24h %s",bd,mm(best.h1),mm(best.h24));
    }

    private static String mm(double v){return Double.isFinite(v)?String.format(Locale.US,"%.1f mm",v):"—";}
    private static double km(double a,double b,double c,double d){double R=6371,dp=Math.toRadians(c-a),dl=Math.toRadians(d-b);double q=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(dl/2)*Math.sin(dl/2);return 2*R*Math.asin(Math.sqrt(q));}

    private static void saveCache(Context app){try{JSONArray a=new JSONArray();for(RainRow r:ROWS.values())a.put(r.json());app.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString(CACHE,a.toString()).putString("updated",updated).putLong("saved",System.currentTimeMillis()).apply();}catch(Exception ignored){}}
    private static void loadCache(Context app){if(!ROWS.isEmpty())return;try{SharedPreferences p=app.getSharedPreferences(PREFS,Context.MODE_PRIVATE);String raw=p.getString(CACHE,"");if(raw.isEmpty())return;JSONArray a=new JSONArray(raw);for(int i=0;i<a.length();i++){RainRow r=RainRow.from(a.optJSONObject(i));if(r!=null&&!r.name.isEmpty())ROWS.put(key(r.name),r);}updated=p.getString("updated","");}catch(Exception ignored){}}

    static final class Session{String csrf,cookie;}
    static final class RainRow{
        String id="",seriesId="",name="",basin="",district="",status="";double lat=Double.NaN,lon=Double.NaN,h1=Double.NaN,h3=Double.NaN,h6=Double.NaN,h12=Double.NaN,h24=Double.NaN;
        JSONObject json()throws Exception{return new JSONObject().put("id",id).put("seriesId",seriesId).put("name",name).put("basin",basin).put("district",district).put("status",status).put("lat",lat).put("lon",lon).put("h1",h1).put("h3",h3).put("h6",h6).put("h12",h12).put("h24",h24);}
        static RainRow from(JSONObject o){if(o==null)return null;RainRow r=new RainRow();r.id=o.optString("id","");r.seriesId=o.optString("seriesId","");r.name=o.optString("name","");r.basin=o.optString("basin","");r.district=o.optString("district","");r.status=o.optString("status","");r.lat=o.optDouble("lat",Double.NaN);r.lon=o.optDouble("lon",Double.NaN);r.h1=o.optDouble("h1",Double.NaN);r.h3=o.optDouble("h3",Double.NaN);r.h6=o.optDouble("h6",Double.NaN);r.h12=o.optDouble("h12",Double.NaN);r.h24=o.optDouble("h24",Double.NaN);return r;}
    }
}
