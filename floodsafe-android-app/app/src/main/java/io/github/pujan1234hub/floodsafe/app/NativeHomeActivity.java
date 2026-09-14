package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import com.google.firebase.messaging.FirebaseMessaging;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/** Fully native FloodSafe Nepal dashboard. No WebView/HTML/JS is used. */
public class NativeHomeActivity extends Activity implements LocationListener {
    private static final int LOCATION_REQUEST = 740;
    private static final int MIC_REQUEST = 741;
    private static final int NOTIFY_REQUEST = 742;
    private static final String PREFS = "floodsafe-native-home";
    private static final String KEY_LAT = "last_lat";
    private static final String KEY_LON = "last_lon";
    private static final String KEY_AT = "last_at";
    private static final long LAST_LOCATION_MAX_AGE_MS = 7L * 24L * 60L * 60L * 1000L;
    private static final long RIVER_FRESH_MS = 10L * 60L * 1000L;
    private static final String RIVER_ENDPOINT = "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String BIPAD = "https://bipadportal.gov.np/api/v1/";

    private final ExecutorService io = Executors.newFixedThreadPool(3);
    private final List<RiverStation> stations = new ArrayList<>();
    private LocationManager locationManager;
    private SpeechRecognizer speech;
    private TextToSpeech tts;
    private TextView locationText, temperatureText, weatherText, detailText, statusText;
    private TextView riverSummary, humanSummary, sathiAnswer;
    private LinearLayout riverList;
    private NativeRiverMap riverMap;
    private double cachedLat = Double.NaN, cachedLon = Double.NaN;
    private long cachedAt;
    private String currentWeatherSummary = "मौसम data अझ आएको छैन";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(234, 246, 255));
        getWindow().setNavigationBarColor(Color.rgb(234, 246, 255));
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        locationManager = getSystemService(LocationManager.class);
        initTts();
        setContentView(buildUi());
        enableSafetyMonitoring();
        restoreLastLocationAndWeather();
        requestCurrentLocation();
        refreshRivers();
        refreshHumanStatus();
        consumeSathiIntent(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        consumeSathiIntent(intent);
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(16), dp(18), dp(36));
        root.setBackgroundColor(Color.rgb(234, 246, 255));
        scroll.addView(root);

        TextView title = text("FloodSafe Nepal", 30, true, Color.rgb(13, 42, 87));
        root.addView(title);
        root.addView(text("Official safety data • Native Android", 13, false, Color.rgb(72,95,120)), lp(-1, dp(34)));

        LinearLayout weatherCard = card(Color.rgb(37, 146, 196));
        locationText = text("📍 Location जाँच हुँदैछ…", 16, true, Color.WHITE);
        temperatureText = text("—°", 48, false, Color.WHITE);
        weatherText = text("मौसम लोड हुँदैछ…", 25, true, Color.WHITE);
        detailText = text("", 14, false, Color.rgb(232,248,255));
        detailText.setPadding(0, dp(12), 0, 0);
        weatherCard.addView(locationText); weatherCard.addView(temperatureText);
        weatherCard.addView(weatherText); weatherCard.addView(detailText);
        root.addView(weatherCard, lp(-1, -2));

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        Button locate = button("◎ Location");
        locate.setOnClickListener(v -> requestCurrentLocation());
        Button refresh = button("↻ Refresh");
        refresh.setOnClickListener(v -> { refreshRivers(); refreshHumanStatus(); if (hasUsableCache()) fetchWeather(cachedLat, cachedLon, true); });
        Button sathi = button("🎙 SATHI");
        sathi.setOnClickListener(v -> startSathiVoice());
        actions.addView(locate, weight()); actions.addView(refresh, weight()); actions.addView(sathi, weight());
        root.addView(actions, lp(-1, dp(58)));

        statusText = text("🛡️ Flood/rain alerts तयार हुँदैछन्…", 14, false, Color.rgb(28,58,85));
        statusText.setPadding(dp(4), dp(6), dp(4), dp(14));
        root.addView(statusText);

        TextView rTitle = text("🌊 Live River Map", 22, true, Color.rgb(13,42,87));
        root.addView(rTitle);
        riverSummary = text("Official BIPAD/DHM stations refresh हुँदैछन्…", 13, false, Color.rgb(72,95,120));
        root.addView(riverSummary, lp(-1, dp(42)));
        riverMap = new NativeRiverMap();
        root.addView(riverMap, lp(-1, dp(230)));
        riverList = new LinearLayout(this);
        riverList.setOrientation(LinearLayout.VERTICAL);
        root.addView(riverList, lp(-1, -2));

        TextView legend = text("🔴 Danger   🟠 Warning   🟡 Alert   🔵 Normal   ⚪ Stale/Unknown", 12, true, Color.rgb(52,75,95));
        root.addView(legend, lp(-1, dp(42)));

        LinearLayout humanCard = card(Color.WHITE);
        humanCard.addView(text("👥 Human / Disaster Status", 20, true, Color.rgb(13,42,87)));
        humanSummary = text("BIPAD official 10-day status refresh हुँदैछ…", 14, false, Color.rgb(60,78,98));
        humanSummary.setPadding(0, dp(10), 0, 0);
        humanCard.addView(humanSummary);
        root.addView(humanCard, lp(-1, -2));

        LinearLayout sathiCard = card(Color.rgb(245, 249, 255));
        sathiCard.addView(text("🤖 SATHI", 20, true, Color.rgb(13,42,87)));
        sathiAnswer = text("माइक थिचेर मौसम, नदी, warning वा app status सोध्न सक्नुहुन्छ।", 14, false, Color.rgb(60,78,98));
        sathiAnswer.setPadding(0, dp(8), 0, dp(8));
        sathiCard.addView(sathiAnswer);
        Button always = button("“Ye Sathi” background voice");
        always.setOnClickListener(v -> toggleWakeService());
        sathiCard.addView(always);
        root.addView(sathiCard, lp(-1, -2));

        root.addView(text("⚠️ 2 km notification rule: fresh verified Warning/Danger मात्र। Stale data लाई live खतरा मानिँदैन।", 13, false, Color.rgb(80,74,45)));
        return scroll;
    }

    private LinearLayout card(int color) {
        LinearLayout c = new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(18), dp(18), dp(18), dp(18));
        c.setBackgroundColor(color);
        return c;
    }
    private TextView text(String value, int sp, boolean bold, int color) {
        TextView t = new TextView(this); t.setText(value); t.setTextSize(sp); t.setTextColor(color); t.setGravity(Gravity.START);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD); return t;
    }
    private Button button(String value) { Button b = new Button(this); b.setText(value); b.setAllCaps(false); return b; }
    private LinearLayout.LayoutParams lp(int w, int h) { LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w,h); p.setMargins(0,0,0,dp(14)); return p; }
    private LinearLayout.LayoutParams weight() { LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0,-1,1f); p.setMargins(dp(2),0,dp(2),0); return p; }
    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    private void enableSafetyMonitoring() {
        getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit().putBoolean("enabled", true).apply();
        Constraints c = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest rain = new PeriodicWorkRequest.Builder(RainAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build();
        PeriodicWorkRequest river = new PeriodicWorkRequest.Builder(RiverAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build();
        WorkManager wm = WorkManager.getInstance(getApplicationContext());
        wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts", ExistingPeriodicWorkPolicy.UPDATE, rain);
        wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts", ExistingPeriodicWorkPolicy.UPDATE, river);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, NOTIFY_REQUEST);
        }
        statusText.setText("🛡️ Auto flood/rain monitoring ON • 2 km verified Warning/Danger मात्र");
    }

    private void restoreLastLocationAndWeather() {
        SharedPreferences p = getSharedPreferences(PREFS, MODE_PRIVATE);
        cachedAt = p.getLong(KEY_AT, 0L);
        cachedLat = Double.longBitsToDouble(p.getLong(KEY_LAT, Double.doubleToRawLongBits(Double.NaN)));
        cachedLon = Double.longBitsToDouble(p.getLong(KEY_LON, Double.doubleToRawLongBits(Double.NaN)));
        if (hasUsableCache()) { showCachedLocationLabel(); fetchWeather(cachedLat, cachedLon, true); }
        else { locationText.setText("📍 Location उपलब्ध छैन"); weatherText.setText("Location अनुमति दिनुहोस्"); temperatureText.setText("—°"); }
    }
    private boolean hasUsableCache() { return Double.isFinite(cachedLat)&&Double.isFinite(cachedLon)&&cachedAt>0&&System.currentTimeMillis()-cachedAt<=LAST_LOCATION_MAX_AGE_MS; }
    private void showCachedLocationLabel() { if (!hasUsableCache()) return; locationText.setText(isNepal(cachedLat,cachedLon)?"📍 पछिल्लो verified GPS • Nepal":"🌍 पछिल्लो verified GPS Nepal बाहिर • weather यही स्थानको हो"); }

    private void requestCurrentLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_REQUEST); return;
        }
        if (locationManager==null) return;
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) locationManager.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());
            else if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) locationManager.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());
            else { showCachedLocationLabel(); statusText.setText("📍 GPS बन्द छ • पछिल्लो verified location मात्र प्रयोग भइरहेको छ"); }
        } catch (SecurityException ignored) { showCachedLocationLabel(); }
    }

    @Override public void onLocationChanged(Location location) {
        if (location==null) return; cachedLat=location.getLatitude(); cachedLon=location.getLongitude(); cachedAt=System.currentTimeMillis();
        getSharedPreferences(PREFS,MODE_PRIVATE).edit().putLong(KEY_LAT,Double.doubleToRawLongBits(cachedLat)).putLong(KEY_LON,Double.doubleToRawLongBits(cachedLon)).putLong(KEY_AT,cachedAt).apply();
        getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit()
                .putLong("lat",Double.doubleToRawLongBits(cachedLat)).putLong("lon",Double.doubleToRawLongBits(cachedLon)).putLong("location_time",cachedAt)
                .putLong("device_lat",Double.doubleToRawLongBits(cachedLat)).putLong("device_lon",Double.doubleToRawLongBits(cachedLon)).putLong("device_location_time",cachedAt)
                .putBoolean("follow_device",true).putBoolean("location_stale",false).putBoolean("enabled",true).apply();
        locationText.setText(isNepal(cachedLat,cachedLon)?"📍 हालको GPS • Nepal":"🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो");
        FloodMonitorService.startIfEnabled(this); fetchWeather(cachedLat,cachedLon,false); refreshRiverUi();
    }

    private void fetchWeather(double lat,double lon,boolean cached) {
        io.execute(() -> { try {
            JSONObject j = getJson(String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto",lat,lon));
            JSONObject cur=j.getJSONObject("current"); double temp=cur.optDouble("temperature_2m",Double.NaN), rain=cur.optDouble("precipitation",0), hum=cur.optDouble("relative_humidity_2m",Double.NaN), wind=cur.optDouble("wind_speed_10m",Double.NaN); String zone=j.optString("timezone","local");
            currentWeatherSummary=String.format(Locale.US,"अहिले %.0f°C, वर्षा %.1f mm, आर्द्रता %.0f%%, हावा %.0f km/h",temp,rain,hum,wind);
            runOnUiThread(() -> { temperatureText.setText(Double.isFinite(temp)?Math.round(temp)+"°":"—°"); weatherText.setText(rain>=.5?"अहिले/छिट्टै वर्षा":"अहिले वर्षा छैन"); detailText.setText(String.format(Locale.US,"%.1f mm वर्षा • %.0f%% आर्द्रता • %.0f km/h हावा\n%s%s",rain,hum,wind,zone,cached?" • last verified GPS":"")); });
        } catch(Exception e){ runOnUiThread(() -> weatherText.setText("मौसम refresh हुन सकेन")); } });
    }

    private void refreshRivers() {
        riverSummary.setText("Official river data refresh हुँदैछ…");
        io.execute(() -> { try {
            JSONObject root=getJson(RIVER_ENDPOINT+"?_native="+System.currentTimeMillis()); JSONArray rows=root.optJSONArray("results"); if(rows==null) rows=new JSONArray();
            List<RiverStation> out=new ArrayList<>(); long now=System.currentTimeMillis();
            for(int i=0;i<rows.length();i++){ JSONObject r=rows.optJSONObject(i); if(r==null)continue; RiverStation s=parseStation(r,now); if(s!=null)out.add(s); }
            out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
            synchronized(stations){ stations.clear(); stations.addAll(out); }
            runOnUiThread(this::refreshRiverUi);
        } catch(Exception e){ runOnUiThread(() -> riverSummary.setText("River data refresh हुन सकेन • पुरानो data लाई live भनिएको छैन")); } });
    }

    private RiverStation parseStation(JSONObject r,long now) {
        double lat=num(r,"latitude","lat","stationLatitude","station_latitude"), lon=num(r,"longitude","lon","lng","stationLongitude","station_longitude"); if(!Double.isFinite(lat)||!Double.isFinite(lon)||!isNepal(lat,lon))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel");
        double warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"); double danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long measured=parseTime(str(r,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));
        boolean fresh=measured>0 && now-measured<=RIVER_FRESH_MS && measured-now<=5*60_000L;
        String official=str(r,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus").toUpperCase(Locale.ROOT);
        String stage="unknown"; int rank=4;
        if(fresh){ if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(official.contains("DANGER")&&!official.contains("BELOW DANGER"))||official.contains("RED")){stage="danger";rank=0;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(official.contains("WARNING")&&!official.contains("BELOW WARNING"))||official.contains("ORANGE")){stage="warning";rank=1;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||official.contains("ALERT")||official.contains("YELLOW")){stage="alert";rank=2;}
            else if(Double.isFinite(level)||official.contains("NORMAL")||official.contains("BLUE")){stage="normal";rank=3;} }
        String name=str(r,"river_name","riverName","station_name","stationName","title","name"); if(name.isEmpty())name="Official river station";
        return new RiverStation(name,lat,lon,level,warning,danger,measured,fresh,stage,rank);
    }

    private void refreshRiverUi() {
        if(riverList==null||riverMap==null)return; List<RiverStation> copy; synchronized(stations){copy=new ArrayList<>(stations);} riverMap.setStations(copy,cachedLat,cachedLon);
        int danger=0,warning=0,alert=0,normal=0,stale=0; for(RiverStation s:copy){switch(s.stage){case"danger":danger++;break;case"warning":warning++;break;case"alert":alert++;break;case"normal":normal++;break;default:stale++;}}
        riverSummary.setText("Fresh: 🔴 "+danger+"  🟠 "+warning+"  🟡 "+alert+"  🔵 "+normal+" • stale/unknown "+stale+" • "+copy.size()+" stations");
        riverList.removeAllViews(); int shown=Math.min(copy.size(),12); for(int i=0;i<shown;i++){ RiverStation s=copy.get(i); TextView row=text(stageDot(s.stage)+" "+s.name+"\n"+stationLine(s),15,true,Color.rgb(30,52,72)); row.setPadding(dp(12),dp(10),dp(12),dp(10)); row.setBackgroundColor(stageBg(s.stage)); riverList.addView(row,lp(-1,-2)); }
        if(copy.isEmpty()) riverList.addView(text("Official river stations अहिले उपलब्ध छैनन्।",14,false,Color.DKGRAY));
    }
    private String stationLine(RiverStation s){ String age=s.measuredAt>0?Math.max(0,(System.currentTimeMillis()-s.measuredAt)/60000)+" min ago":"time unknown"; String l=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —"; double d=distanceKm(s.lat,s.lon); return stageName(s.stage)+" • "+l+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • %.1f km",d):""); }

    private void refreshHumanStatus() {
        humanSummary.setText("BIPAD official 10-day status refresh हुँदैछ…");
        io.execute(() -> { try {
            JSONObject inc=getJson(BIPAD+"incident/?limit=500&ordering=-incidentOn"); JSONObject loss=getJson(BIPAD+"loss-people/?limit=1000&ordering=-createdOn"); JSONArray ir=rows(inc), lr=rows(loss); long now=System.currentTimeMillis(), cutoff=now-10L*24*60*60*1000; List<String> ids=new ArrayList<>(); int incidents=0; String latest=""; long latestAt=0;
            for(int i=0;i<ir.length();i++){JSONObject o=ir.optJSONObject(i);if(o==null)continue;long t=parseTime(str(o,"incidentOn","incident_on","createdOn","created_at","modifiedOn","updated_at","date"));String tx=o.toString().toLowerCase(Locale.ROOT);if(t>=cutoff&&isDisasterText(tx)){incidents++;String id=String.valueOf(o.opt("id"));ids.add(id);if(t>latestAt){latestAt=t;latest=str(o,"titleNe","title","nameNe","name");}}}
            int dead=0,inj=0,missing=0,rescued=0; boolean dSeen=false,iSeen=false,mSeen=false,rSeen=false;
            for(int i=0;i<lr.length();i++){JSONObject o=lr.optJSONObject(i);if(o==null)continue;String rid=str(o,"incident_id","incidentId"); if(!rid.isEmpty()&&!ids.contains(rid))continue; String tx=o.toString().toLowerCase(Locale.ROOT); int n=(int)Math.max(0,numOr(o,"count","people","peopleCount","people_count","number","total","value","noOfPeople","no_of_people")); if(tx.matches(".*(dead|death|deceased|fatal|मृत|मृत्यु).*")){dead+=n;dSeen=true;} else if(tx.matches(".*(injur|घाइते).*")){inj+=n;iSeen=true;} else if(tx.matches(".*(missing|बेपत्ता).*")){missing+=n;mSeen=true;} else if(tx.matches(".*(rescued|rescue|उद्धार).*")){rescued+=n;rSeen=true;}}
            String msg=incidents==0?"पछिल्लो १० दिनमा matching official disaster incident भेटिएन।":"BIPAD official • "+incidents+" घटना"+(latest.isEmpty()?"":" • latest: "+latest)+"\nमृत "+(dSeen?dead:"—")+" • घाइते "+(iSeen?inj:"—")+" • बेपत्ता "+(mSeen?missing:"—")+" • उद्धार "+(rSeen?rescued:"—")+"\nअनुमानित संख्या देखाइँदैन।";
            runOnUiThread(() -> humanSummary.setText(msg));
        } catch(Exception e){ runOnUiThread(() -> humanSummary.setText("Human Status अहिले refresh हुन सकेन; stale result लाई live भनिएको छैन।")); } });
    }

    private void startSathiVoice() {
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},MIC_REQUEST);return;}
        if(!SpeechRecognizer.isRecognitionAvailable(this)){sathiAnswer.setText("यो फोनमा Android voice recognition उपलब्ध छैन।");return;}
        if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}
        speech=SpeechRecognizer.createSpeechRecognizer(this); speech.setRecognitionListener(new RecognitionListener(){public void onReadyForSpeech(Bundle p){sathiAnswer.setText("🎙 सुन्दैछु…");} public void onBeginningOfSpeech(){} public void onRmsChanged(float r){} public void onBufferReceived(byte[]b){} public void onEndOfSpeech(){} public void onError(int e){sathiAnswer.setText("आवाज बुझिएन, फेरि प्रयास गर्नुहोस्।");} public void onPartialResults(Bundle b){} public void onEvent(int t,Bundle b){} public void onResults(Bundle b){ArrayList<String>r=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);String q=r==null||r.isEmpty()?"":r.get(0);answerSathi(q);} });
        speech.startListening(new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,"ne-NP").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,5));
    }
    private void answerSathi(String q){String x=q==null?"":q.toLowerCase(Locale.ROOT);String a;if(x.contains("मौसम")||x.contains("weather")||x.contains("rain"))a=currentWeatherSummary;else if(x.contains("नदी")||x.contains("river")||x.contains("flood")||x.contains("बाढी")){int d=0,w=0; synchronized(stations){for(RiverStation s:stations){if("danger".equals(s.stage))d++;if("warning".equals(s.stage))w++;}}a="Fresh official river data मा danger "+d+" र warning "+w+" station छन्।";}else if(x.contains("alert")||x.contains("warning")||x.contains("notification"))a="Flood/rain monitoring चालु छ। नदीका fresh verified Warning वा Danger 2 km भित्र भए मात्र proximity alert जान्छ।";else a="मौसम, नदीको status, flood warning वा notification बारे सोध्नुहोस्।";sathiAnswer.setText("तपाईं: "+q+"\nSATHI: "+a);speak(a);}
    private void toggleWakeService(){boolean on=getSharedPreferences(SathiWakeService.PREFS,MODE_PRIVATE).getBoolean(SathiWakeService.KEY_ENABLED,false); if(on){getSharedPreferences(SathiWakeService.PREFS,MODE_PRIVATE).edit().putBoolean(SathiWakeService.KEY_ENABLED,false).apply();startServiceSafe(SathiWakeService.ACTION_STOP);sathiAnswer.setText("“Ye Sathi” background voice बन्द भयो।");}else{if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},MIC_REQUEST);return;}getSharedPreferences(SathiWakeService.PREFS,MODE_PRIVATE).edit().putBoolean(SathiWakeService.KEY_ENABLED,true).apply();startServiceSafe(SathiWakeService.ACTION_START);sathiAnswer.setText("“Ye Sathi” background voice ON भयो।");}}
    private void startServiceSafe(String action){try{Intent i=new Intent(this,SathiWakeService.class).setAction(action);if(Build.VERSION.SDK_INT>=26)startForegroundService(i);else startService(i);}catch(Exception ignored){}}
    private void consumeSathiIntent(Intent i){if(i==null)return;String q=i.getStringExtra(SathiWakeService.EXTRA_QUERY);if(q!=null&&!q.trim().isEmpty()){answerSathi(q.trim());i.removeExtra(SathiWakeService.EXTRA_QUERY);}}
    private void initTts(){tts=new TextToSpeech(getApplicationContext(),s->{if(s==TextToSpeech.SUCCESS&&tts!=null){int r=tts.setLanguage(Locale.forLanguageTag("ne-NP"));if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(new Locale("ne"));tts.setSpeechRate(.92f);}});} private void speak(String s){if(tts!=null&&s!=null&&!s.isEmpty())tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"sathi-native");}

    @Override public void onRequestPermissionsResult(int code,String[]p,int[]g){super.onRequestPermissionsResult(code,p,g);if(code==LOCATION_REQUEST&&hasLocationPermission())requestCurrentLocation();else if(code==MIC_REQUEST&&checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)startSathiVoice();}
    private boolean hasLocationPermission(){return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED||checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
    private static boolean isNepal(double lat,double lon){return Double.isFinite(lat)&&Double.isFinite(lon)&&lat>=26.2&&lat<=30.5&&lon>=80&&lon<=88.35;}
    private double distanceKm(double lat,double lon){if(!hasUsableCache()||!isNepal(cachedLat,cachedLon))return Double.NaN;double r=6371,dLat=Math.toRadians(lat-cachedLat),dLon=Math.toRadians(lon-cachedLon);double a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(Math.toRadians(cachedLat))*Math.cos(Math.toRadians(lat))*Math.sin(dLon/2)*Math.sin(dLon/2);return 2*r*Math.asin(Math.sqrt(a));}

    private static JSONObject getJson(String u)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(15000);c.setReadTimeout(20000);c.setUseCaches(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store");if(c.getResponseCode()!=200)throw new IllegalStateException("HTTP "+c.getResponseCode());StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}finally{c.disconnect();}return new JSONObject(b.toString());}
    private static JSONArray rows(JSONObject j){JSONArray a=j.optJSONArray("results");if(a==null)a=j.optJSONArray("data");return a==null?new JSONArray():a;}
    private static String str(JSONObject o,String...k){for(String x:k){if(o.has(x)&&!o.isNull(x)){String s=String.valueOf(o.opt(x)).trim();if(!s.isEmpty()&&!"null".equalsIgnoreCase(s))return s;}}return"";}
    private static double num(JSONObject o,String...k){for(String x:k){if(!o.has(x)||o.isNull(x))continue;Object v=o.opt(x);if(v instanceof Number){double n=((Number)v).doubleValue();if(Double.isFinite(n))return n;}try{double n=Double.parseDouble(String.valueOf(v).trim());if(Double.isFinite(n))return n;}catch(Exception ignored){}}return Double.NaN;}
    private static double numOr(JSONObject o,String...k){double n=num(o,k);return Double.isFinite(n)?n:0;}
    private static long parseTime(String s){if(s==null||s.trim().isEmpty())return-1;String v=s.trim();try{long n=Long.parseLong(v);return n<10_000_000_000L?n*1000:n;}catch(Exception ignored){}try{return Instant.parse(v).toEpochMilli();}catch(Exception ignored){}try{return OffsetDateTime.parse(v).toInstant().toEpochMilli();}catch(Exception ignored){}try{return ZonedDateTime.parse(v).toInstant().toEpochMilli();}catch(Exception ignored){}try{return LocalDateTime.parse(v.replace(' ','T'),DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){return-1;}}
    private static boolean isDisasterText(String t){return t.matches(".*(flood|flash flood|landslide|earthquake|avalanche|glacial|glof|fire|wildfire|lightning|storm|windstorm|heavy rain|inundation|बाढी|पहिरो|भूकम्प|हिमपहिरो|डढेलो|आगलागी|चट्याङ|डुबान|अविरल वर्षा).*" )&&!t.matches(".*(road accident|vehicle accident|traffic accident|दुर्घटना|राजनीति|खेलकुद|निर्वाचन).*" );}
    private static String stageDot(String s){switch(s){case"danger":return"🔴";case"warning":return"🟠";case"alert":return"🟡";case"normal":return"🔵";default:return"⚪";}} private static String stageName(String s){switch(s){case"danger":return"DANGER";case"warning":return"WARNING";case"alert":return"ALERT";case"normal":return"NORMAL";default:return"STALE/UNKNOWN";}} private static int stageBg(String s){switch(s){case"danger":return Color.rgb(255,232,232);case"warning":return Color.rgb(255,241,220);case"alert":return Color.rgb(255,250,218);case"normal":return Color.rgb(226,243,255);default:return Color.rgb(238,240,243);}}

    private static final class RiverStation {final String name,stage;final double lat,lon,level,warning,danger;final long measuredAt;final boolean fresh;final int rank;RiverStation(String n,double a,double o,double l,double w,double d,long m,boolean f,String s,int r){name=n;lat=a;lon=o;level=l;warning=w;danger=d;measuredAt=m;fresh=f;stage=s;rank=r;}}
    private final class NativeRiverMap extends View {private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);private List<RiverStation> data=new ArrayList<>();private double uLat=Double.NaN,uLon=Double.NaN;NativeRiverMap(){super(NativeHomeActivity.this);p.setTypeface(Typeface.DEFAULT_BOLD);setBackgroundColor(Color.rgb(218,239,249));}void setStations(List<RiverStation>s,double lat,double lon){data=new ArrayList<>(s);uLat=lat;uLon=lon;invalidate();}@Override protected void onDraw(Canvas c){super.onDraw(c);float w=getWidth(),h=getHeight();p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(204,228,210));RectF land=new RectF(dp(12),dp(18),w-dp(12),h-dp(18));c.drawRoundRect(land,dp(22),dp(22),p);p.setTextSize(dp(11));p.setColor(Color.rgb(55,82,65));c.drawText("NEPAL • official station overview",dp(22),dp(35),p);for(RiverStation s:data){float x=(float)((s.lon-80.0)/(88.35-80.0))*(w-dp(36))+dp(18);float y=(float)((30.5-s.lat)/(30.5-26.2))*(h-dp(48))+dp(28);p.setColor(dotColor(s.stage));c.drawCircle(x,y,dp("danger".equals(s.stage)?6:4),p);}if(isNepal(uLat,uLon)){float x=(float)((uLon-80)/(88.35-80))*(w-dp(36))+dp(18);float y=(float)((30.5-uLat)/(30.5-26.2))*(h-dp(48))+dp(28);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(dp(2));p.setColor(Color.BLACK);c.drawCircle(x,y,dp(8),p);p.setStyle(Paint.Style.FILL);}}private int dotColor(String s){switch(s){case"danger":return Color.rgb(214,39,40);case"warning":return Color.rgb(240,126,25);case"alert":return Color.rgb(236,190,35);case"normal":return Color.rgb(39,128,214);default:return Color.rgb(130,136,145);}}}

    @Override protected void onDestroy(){if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}if(tts!=null){tts.stop();tts.shutdown();}io.shutdownNow();super.onDestroy();}
}
