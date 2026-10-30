package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.time.Instant;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONArray;
import org.json.JSONObject;

/** Dedicated full-screen river map. Do not nest a continuously-rendering MapLibre view in the Home ScrollView. */
public final class FloodSafeMapActivity extends Activity {
    private final ExecutorService io=Executors.newFixedThreadPool(2);
    private FloodSafeNativeMapView nativeMap;
    private DistrictWeatherOverlay weatherOverlay;
    private TextView status;
    private boolean english;
    private double deviceLat=Double.NaN,deviceLon=Double.NaN;
    private static final long MAP_STATION_REFRESH_MS=30_000L;
    private static final long MAP_READING_FRESH_MS=30L*60L*1000L;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final List<MapStation> lastMapStations=new ArrayList<>();
    private boolean mapFetchInFlight=false;
    private String currentObservationSource="none";
    private final Runnable mapRefreshTick=new Runnable(){
        @Override public void run(){
            if(isFinishing()||isDestroyed())return;
            expireMapMarkers();
            refreshStationData();
            handler.postDelayed(this,MAP_STATION_REFRESH_MS);
        }
    };

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        english=getSharedPreferences("floodsafe-native-full",MODE_PRIVATE).getBoolean("lang_en",false);
        deviceLat=getIntent().getDoubleExtra("lat",Double.NaN);
        deviceLon=getIntent().getDoubleExtra("lon",Double.NaN);
        getWindow().setStatusBarColor(Color.rgb(225,242,252));
        getWindow().setNavigationBarColor(Color.rgb(235,248,253));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        FrameLayout root=new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(228,243,252));
        SafeInsets.apply(root);
        setContentView(root);

        // Full-screen MapLibre never participates in Home dashboard scrolling.
        nativeMap=new FloodSafeNativeMapView(this,station->{
            if(station instanceof MapStation)showStation((MapStation)station);
        });
        root.addView(nativeMap,new FrameLayout.LayoutParams(-1,-1));

        weatherOverlay=new DistrictWeatherOverlay(this,new DistrictWeatherOverlay.Projection(){
            public android.graphics.PointF project(double lat,double lon){return nativeMap==null?null:nativeMap.weatherPoint(lat,lon);}
            public double zoom(){return nativeMap==null?5.4:nativeMap.weatherZoom();}
        });
        root.addView(weatherOverlay,new FrameLayout.LayoutParams(-1,-1));
        nativeMap.setWeatherOverlayInvalidator(()->{if(weatherOverlay!=null)weatherOverlay.invalidate();});

        LinearLayout toolbar=new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.VERTICAL);
        toolbar.setPadding(dp(10),dp(8),dp(10),dp(7));
        toolbar.setBackground(bg(Color.argb(245,255,255,255),Color.rgb(202,224,237),16));
        FrameLayout.LayoutParams tp=new FrameLayout.LayoutParams(-1,-2,Gravity.TOP);
        tp.setMargins(dp(10),dp(12),dp(10),0);
        root.addView(toolbar,tp);
        TextView title=new TextView(this);
        title.setText(english?"🇳🇵 Nepal river map · DHM / BIPAD":"🇳🇵 नेपालको नदी नक्सा · DHM / BIPAD");
        title.setTextColor(Color.rgb(19,45,71));title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setTextSize(19);
        toolbar.addView(title);
        status=new TextView(this);
        status.setText(english?"Loading official rivers and 77-district weather…":"आधिकारिक नदी र ७७ जिल्लाको मौसम ल्याउँदैछ…");
        status.setTextColor(Color.rgb(88,119,137));status.setTextSize(12);status.setMaxLines(3);
        toolbar.addView(status);
        LinearLayout buttons=new LinearLayout(this);
        buttons.setOrientation(LinearLayout.HORIZONTAL);toolbar.addView(buttons);
        Button back=button(english?"← Home":"← गृह");
        Button zoomIn=button("+");
        Button zoomOut=button("−");
        Button terrain=button("◈ 3D");
        Button reset=button("🇳🇵");
        for(Button button:new Button[]{back,zoomIn,zoomOut,terrain,reset}){
            LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,dp(48),1f);p.setMargins(dp(2),dp(7),dp(2),0);buttons.addView(button,p);
        }
        back.setOnClickListener(v->finish());
        zoomIn.setOnClickListener(v->nativeMap.zoomBy(1.25f));
        zoomOut.setOnClickListener(v->nativeMap.zoomBy(.8f));
        terrain.setOnClickListener(v->{nativeMap.toggleTerrain();terrain.setText(nativeMap.terrain?"▱ 2D":"◈ 3D");});
        reset.setOnClickListener(v->nativeMap.resetView());
        if(Double.isFinite(deviceLat)&&Double.isFinite(deviceLon))
           nativeMap.updateUserLocation(deviceLat,deviceLon);

        fetchMapData();
    }

    private void fetchMapData(){
        refreshStationData();
        // Weather icons are a separate model overlay, never official river alerts.
        io.execute(()->{
            try{
                JSONArray data=DistrictWeatherStore.fetch(getApplicationContext());
                runOnUiThread(()->{
                    if(!isFinishing()&&!isDestroyed()&&weatherOverlay!=null)weatherOverlay.setDistricts(data);
                });
            }catch(Exception ignored){}
        });
    }

    private void refreshStationData(){
        if(mapFetchInFlight||isFinishing()||isDestroyed())return;
        mapFetchInFlight=true;
        io.execute(()->{
            try{
                JSONObject feeds=OfficialStationFeeds.rivers();
                String source=feeds.optString("activeObservationSource","none");
                JSONArray arr=feeds.optJSONArray("results");
                if(arr==null)arr=feeds.optJSONArray("data");
                List<MapStation> points=new ArrayList<>();
                long now=System.currentTimeMillis();
                if(arr!=null)for(int i=0;i<arr.length();i++){
                    JSONObject o=arr.optJSONObject(i);if(o==null)continue;
                    double lat=number(o,"latitude","lat","stationLatitude","station_latitude");
                    double lon=number(o,"longitude","lon","lng","stationLongitude","station_longitude");
                    if(!Double.isFinite(lat)||!Double.isFinite(lon)||lat<26.2||lat>30.5||lon<80||lon>88.35)continue;
                    double level=number(o,"waterLevel","water_level","currentWaterLevel","current_level","_lastWaterLevel");
                    double warn=number(o,"warningLevel","warning_level","warningThreshold","_lastWarningLevel");
                    double danger=number(o,"dangerLevel","danger_level","dangerThreshold","_lastDangerLevel");
                    long at=timestamp(text(o,"waterLevelOn","water_level_on","measuredOn","observedAt","observationTime","_measurementTime"));
                    boolean fresh=at>0&&at<=now+300000L&&now-at<=MAP_READING_FRESH_MS;
                    String raw=text(o,"_officialStatus","status","riskLevel").toUpperCase(Locale.ROOT);
                    String stage="unknown";
                    // Match the Home dashboard's official classification exactly.
                    // Do not invent WATCH solely because level >= 80% of warning.
                    if(fresh){
                        if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)
                                ||raw.contains("DANGER")&&!raw.contains("BELOW DANGER")||raw.contains("RED"))
                            stage="danger";
                        else if((Double.isFinite(level)&&Double.isFinite(warn)&&warn>0&&level>=warn)
                                ||raw.contains("WARNING")&&!raw.contains("BELOW WARNING")||raw.contains("ORANGE"))
                            stage="warning";
                        else if(!raw.contains("BELOW")&&(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")))
                            stage="alert";
                        else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE"))
                            stage="normal";
                    }
                    String name=text(o,"river_name","riverName","station_name","stationName","title","name");
                    if(name.isEmpty())name="Official station";
                    points.add(new MapStation(name,lat,lon,level,positiveThreshold(warn),positiveThreshold(danger),fresh,stage,at));
                }
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed()||nativeMap==null)return;
                    lastMapStations.clear();
                    lastMapStations.addAll(points);
                    currentObservationSource="dhm".equals(source)?"dhm":("bipad".equals(source)?"bipad":"none");
                    nativeMap.setStations(points,deviceLat,deviceLon);
                    int dangerCount=0,warningCount=0,watchCount=0;
                    for(MapStation p:points){
                        if("danger".equals(p.stage))dangerCount++;
                        else if("warning".equals(p.stage))warningCount++;
                        else if("alert".equals(p.stage))watchCount++;
                    }
                    String feed="dhm".equals(currentObservationSource)?"DHM":
                        "bipad".equals(currentObservationSource)?(english?"BIPAD fallback":"BIPAD वैकल्पिक स्रोत"):
                        (english?"No current official reading":"सरकारी ताजा मापन छैन");
                    status.setText(feed+" · "+points.size()+(english?" stations":" स्टेशन")+" · 🔴 "+dangerCount+
                        " 🟠 "+warningCount+" 🟡 "+watchCount);
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed())return;
                    currentObservationSource="none";
                    // No network is not evidence that a cached yellow/red station is still current.
                    if(nativeMap!=null&&!lastMapStations.isEmpty()){
                        List<MapStation> unknown=new ArrayList<>();
                        for(MapStation p:lastMapStations)
                            unknown.add(new MapStation(p.name,p.lat,p.lon,p.level,p.warning,p.danger,false,"unknown",p.at));
                        lastMapStations.clear();lastMapStations.addAll(unknown);
                        nativeMap.setStations(unknown,deviceLat,deviceLon);
                    }
                    if(status!=null)status.setText(english?
                        "Official station feed unavailable · old markers are not live":
                        "आधिकारिक स्टेशन स्रोत उपलब्ध छैन · पुराना बिन्दु live होइनन्");
                });
            }finally{
                runOnUiThread(()->mapFetchInFlight=false);
            }
        });
    }

    private void expireMapMarkers(){
        if(lastMapStations.isEmpty()||nativeMap==null)return;
        long now=System.currentTimeMillis();
        boolean changed=false;
        List<MapStation> updated=new ArrayList<>();
        for(MapStation p:lastMapStations){
            boolean fresh=p.fresh&&p.at>0&&p.at<=now+300000L&&now-p.at<=MAP_READING_FRESH_MS;
            if(p.fresh&&!fresh)changed=true;
            updated.add(fresh?p:new MapStation(p.name,p.lat,p.lon,p.level,p.warning,p.danger,false,"unknown",p.at));
        }
        if(changed){
            lastMapStations.clear();lastMapStations.addAll(updated);
            nativeMap.setStations(updated,deviceLat,deviceLon);
        }
    }
    private void showStation(MapStation s){
        // Already loaded station measurement: open instantly, no extra network round-trip.
        StationDetailSheet.show(this,s.name,s.stage,s.level,s.fresh,s.at,
            english?"Verified DHM/BIPAD station. Tap a new marker to inspect that gauge.":
                    "DHM/BIPAD स्टेशनको उपलब्ध मापन। अर्को स्टेशन हेर्न नक्साको बिन्दु थिच्नुहोस्।",
            english,false,s.warning,s.danger);
    }
    private Button button(String s){
        Button b=new Button(this);b.setAllCaps(false);b.setText(s);b.setTextSize(13);
        b.setTextColor(Color.rgb(23,58,83));b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        b.setBackground(bg(Color.rgb(243,251,255),Color.rgb(195,219,234),12));return b;
    }
    private android.graphics.drawable.GradientDrawable bg(int c,int stroke,int r){
        android.graphics.drawable.GradientDrawable d=new android.graphics.drawable.GradientDrawable();
        d.setColor(c);d.setCornerRadius(dp(r));d.setStroke(dp(1),stroke);return d;
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private static String text(JSONObject o,String...names){for(String n:names){String s=o.optString(n,"").trim();if(!s.isEmpty()&&!"null".equalsIgnoreCase(s))return s;}return "";}
    private static double number(JSONObject o,String...names){for(String n:names){double x=o.optDouble(n,Double.NaN);if(Double.isFinite(x))return x;}return Double.NaN;}
    private static long timestamp(String s){try{return Instant.parse(s).toEpochMilli();}catch(Exception ignored){return -1L;}}
    private static double positiveThreshold(double threshold){
        // Missing and zero thresholds must never appear as real official gauge limits.
        return Double.isFinite(threshold)&&threshold>0d?threshold:Double.NaN;
    }
    private static final class MapStation {
        final String name,stage;
        final double lat,lon,level,rainfallMm,warning,danger;
        final boolean fresh;final long at;
        MapStation(String n,double a,double o,double l,double w,double d,boolean f,String st,long t){
            name=n;lat=a;lon=o;level=l;rainfallMm=Double.NaN;
            warning=w;danger=d;fresh=f;stage=st;at=t;
        }
    }
    @Override protected void onPause(){
        handler.removeCallbacks(mapRefreshTick);
        if(nativeMap!=null)nativeMap.onHostPause();
        super.onPause();
    }
    @Override protected void onResume(){
        super.onResume();
        if(nativeMap!=null)nativeMap.onHostResume();
        expireMapMarkers();
        handler.removeCallbacks(mapRefreshTick);
        handler.postDelayed(mapRefreshTick,MAP_STATION_REFRESH_MS);
    }
    @Override protected void onDestroy(){
        handler.removeCallbacks(mapRefreshTick);
        io.shutdownNow();
        super.onDestroy();
    }
}
