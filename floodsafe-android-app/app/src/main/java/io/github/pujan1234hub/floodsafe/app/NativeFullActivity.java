package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.view.GestureDetector;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.AutoCompleteTextView;
import android.text.Editable;
import android.text.TextWatcher;
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.widget.FrameLayout;
import android.widget.ImageView;
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
import java.io.InputStream;
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

/** Full native Android implementation of the FloodSafe Nepal web dashboard. No WebView is used. */
public final class NativeFullActivity extends Activity implements LocationListener {
    private static final int REQ_LOCATION=801, REQ_MIC=802, REQ_NOTIFY=803;
    private static final String PREFS="floodsafe-native-full";
    private static final String KEY_LAT="lat",KEY_LON="lon",KEY_AT="at",KEY_LANG="lang_en";
    private static final long RIVER_FRESH_MS=2L*60L*60L*1000L;
    private static final long EMERGENCY_FRESH_MS=10L*60L*1000L;
    private static final String RIVER_ENDPOINT="https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String NEWS_ENDPOINT="https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three";
    private static final String BIPAD="https://bipadportal.gov.np/api/v1/";
    private final ExecutorService io=Executors.newFixedThreadPool(4);
    private final Handler main=new Handler(Looper.getMainLooper());
    private final List<RiverStation> stations=new ArrayList<>();
    private LocationManager lm;
    private SpeechRecognizer speech;
    private TextToSpeech tts;
    private boolean english;
    // Live UI translations; do not rebuild screens or touch data on language change.
    private final java.util.Map<String,String> neToEn=new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.Map<String,String> enToNe=new java.util.concurrent.ConcurrentHashMap<>();
    private boolean newsKnowledgeDisconnected=false;
    private double lat=Double.NaN,lon=Double.NaN;
    private long locAt;
    // Only the manually tapped GPS button needs extra duplicate-callback protection.
    private long lastLocationRenderAt=0L, lastLocateTapElapsed=0L;
    private long weatherRequestVersion=0L, forecastRequestVersion=0L;
    private FrameLayout root;
    private ScrollView scroll;
    private LinearLayout content,nearList,nationalList,newsList,humanCard,alarmBanner,governmentList;
    private TextView brandSub,langBtn,place,clock,temp,weatherText,weatherSupport,rainTiming,rain,humidity,wind;
    private TextView alarmTitle,alarmText,riskBadge,riskValue,riskText,stationCount,warningCount,dangerCount,feedFresh;
    private TextView nearTitle,nearSub,nationalTitle,nationalSub,nationalFresh,humanFresh,humanDeaths,humanInjured,humanMissing,humanRescued,humanDetail;
    private TextView newsTitle,newsSub,privacyTitle,privacySub,mapTitle,mapSub,mapHint,gyanTitle,gyanSub,gyanMessage;
    private TextView rainGaugeTitle,rainGaugeInfo,rainGaugeHint;
    private long lastRainGaugeRequestAt=0;
    private double lastRainGaugeLat=Double.NaN,lastRainGaugeLon=Double.NaN;
    private LinearLayout gyanRotator;
    private int gyanIndex=0;
    private final Runnable gyanTick=new Runnable(){
       @Override public void run(){
          if(gyanRotator==null||gyanSub==null||gyanMessage==null||isFinishing()||isDestroyed())return;
          if(GyanKnowledge.ITEMS.isEmpty())return;
          // Vary topics rather than showing all six Gita passages consecutively.
          GyanKnowledge.Entry item=GyanKnowledge.ITEMS.get(gyanIndex%GyanKnowledge.ITEMS.size());
          gyanIndex=(gyanIndex+11)%GyanKnowledge.ITEMS.size();
          gyanRotator.animate().cancel();
          gyanRotator.animate().alpha(0f).setDuration(230L).withEndAction(()->{
             if(isFinishing()||isDestroyed())return;
             gyanSub.setText("✦ "+GyanKnowledge.categoryName(item.category,english)+"  ·  "+item.title(english));
             gyanMessage.setText(item.body(english));
             gyanRotator.animate().alpha(1f).setDuration(350L).start();
          }).start();
          main.postDelayed(this,10000L);
       }
    };
    private FloodSafeNativeMapView map;
    private volatile NepalRiverBoundary nepalDistrictBorder;
    private long lastGovernmentExpiryCheckAt;
    private static final long GOVERNMENT_FOREGROUND_REFRESH_MS=10L*60L*1000L;
    private final Runnable governmentAutoRefresh=new Runnable(){
        @Override public void run(){
            if(isFinishing()||isDestroyed())return;
            refreshGovernment();
            main.postDelayed(this,GOVERNMENT_FOREGROUND_REFRESH_MS);
        }
    };
    private NativeSevenDayChart miniForecast;
    private AnimatedNepalWeatherOverlay mapWeather;
    private DistrictWeatherOverlay districtSky;
    private JSONArray districtWeather=new JSONArray();
    private AutoCompleteTextView districtPicker;
    private TextView districtWeatherInfo;
    private String selectedDistrict="";
    private View nearSection;
    private View homeAnchor,mapAnchor,newsAnchor;
    private String currentWeather="";
    private JSONArray currentGovernmentNotices=new JSONArray();
    private JSONArray currentNewsForSathi=new JSONArray();
    private long newsLastFetchedAt=0L;
    private boolean newsRefreshing=false;
    // Default 60 seconds; safe remote config may adjust within 60..900 seconds.
    private static final long NEWS_POLL_INTERVAL_MS=60_000L;
    private PlayStoreUpdateBridge playUpdates;
    private final Runnable onOtaContentChanged=()->{
        if(isFinishing()||isDestroyed())return;
        showNextNewsKnowledge();
        // Only content and safe presentation intervals update here; no alert thresholds.
    };
    private final List<NewsItem> freshNewsOnScreen=new ArrayList<>();
    private TextView newsKnowledgeCategory,newsKnowledgeText;
    private int newsKnowledgeIndex=4;
    private boolean newsShowingKnowledge=false;
    private final Runnable newsKnowledgeTick=new Runnable(){
        @Override public void run(){
            if(isFinishing()||isDestroyed()||!newsShowingKnowledge)return;
            showNextNewsKnowledge();
            main.postDelayed(this,FloodSafeRemoteConfig.knowledgeRotateMillis());
        }
    };
    private final Runnable newsAutoRefreshTick=new Runnable(){
        @Override public void run(){
            if(isFinishing()||isDestroyed())return;
            // Hide any news immediately when its 30-minute publication window closes.
            if(!newsShowingKnowledge && !freshNewsOnScreen.isEmpty()){
                long now=System.currentTimeMillis();
                List<NewsItem> active=new ArrayList<>();
                for(NewsItem n:freshNewsOnScreen){
                    if(n.at>0 && n.at<=now+300000L && now-n.at<=NewsFeedParser.RECENT_MS)active.add(n);
                }
                if(active.size()!=freshNewsOnScreen.size())renderNews(active);
            }
            if(System.currentTimeMillis()-newsLastFetchedAt>=FloodSafeRemoteConfig.newsPollMillis())refreshNews();
            FloodSafeRemoteConfig.refreshAsync(getApplicationContext(),onOtaContentChanged);
            main.postDelayed(this,20000L);
        }
    };
    private TextView governmentStatus;
    private boolean expandedGovernment=false;
    private long governmentCheckedAt=0L;
    private int nationalPageSize=12;
    private boolean showAllStations=false;
    private boolean mapAnimationVisible=true;
    private final Runnable mapVisibilityTick=()->{
        if(scroll==null||mapAnchor==null||map==null||districtSky==null)return;
        int top=mapAnchor.getTop(),bottom=top+mapAnchor.getHeight();
        int visibleTop=scroll.getScrollY(),visibleBottom=visibleTop+scroll.getHeight();
        boolean visible=bottom>visibleTop&&top<visibleBottom;
        if(visible!=mapAnimationVisible){mapAnimationVisible=visible;
            map.setParticleAnimationEnabled(visible);
            districtSky.setAnimationActive(visible);
        }
    };
    private long lastStationMapHash=Long.MIN_VALUE;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(223,242,251));
        getWindow().setNavigationBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        FloodSafeRemoteConfig.init(getApplicationContext());
        playUpdates=new PlayStoreUpdateBridge(this);
        SharedPreferences p=getSharedPreferences(PREFS,MODE_PRIVATE);english=p.getBoolean(KEY_LANG,false);
        lat=Double.longBitsToDouble(p.getLong(KEY_LAT,Double.doubleToRawLongBits(Double.NaN)));
        lon=Double.longBitsToDouble(p.getLong(KEY_LON,Double.doubleToRawLongBits(Double.NaN)));
        locAt=p.getLong(KEY_AT,0L);
        lm=getSystemService(LocationManager.class);
        initTts();
        setContentView(buildScreen());
        enableMonitoring();
        // Live MapLibre map owns the Nepal border-clipped geometry; no static overview map.
        refreshAll();
        requestLocation();
        consumeSathiIntent(getIntent());
        main.post(clockTick);
    }

    @Override protected void onNewIntent(Intent i){super.onNewIntent(i);setIntent(i);consumeSathiIntent(i);}

    private View buildScreen(){
        root=new FrameLayout(this); root.setBackgroundColor(Color.rgb(223,242,251));
        scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setClipToPadding(false); scroll.setPadding(0,0,0,dp(92));
        content=new LinearLayout(this); content.setOrientation(LinearLayout.VERTICAL); content.setPadding(dp(14),dp(16),dp(14),dp(24));
        scroll.addView(content,new ScrollView.LayoutParams(-1,-2)); root.addView(scroll,new FrameLayout.LayoutParams(-1,-1));
        scroll.setOnScrollChangeListener((v,x,y,oldX,oldY)->{main.removeCallbacks(mapVisibilityTick);main.postDelayed(mapVisibilityTick,160L);});
        homeAnchor=header(); content.addView(homeAnchor);
        content.addView(hero(),lp(-1,-2,0,0,0,dp(12)));
        Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->requestLocation(true)); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12)));
        TextView outside=text("",13,true,Color.rgb(40,85,111)); outside.setId(android.R.id.hint); outside.setPadding(dp(15),dp(13),dp(15),dp(13)); outside.setBackground(round(Color.rgb(239,249,255),22,Color.rgb(159,205,232),1)); content.addView(outside,lp(-1,-2,0,0,0,dp(10)));
        alarmBanner=new LinearLayout(this);alarmBanner.setOrientation(LinearLayout.VERTICAL);alarmBanner.setPadding(dp(16),dp(14),dp(16),dp(14));alarmBanner.setBackground(round(Color.rgb(255,235,239),22,Color.rgb(239,138,152),2));
        alarmTitle=text(t("⚠️ नदी चेतावनी","⚠️ River warning"),22,true,Color.rgb(146,34,56));alarmText=text("",14,true,Color.rgb(146,34,56));alarmBanner.addView(alarmTitle);alarmBanner.addView(alarmText);alarmBanner.setVisibility(View.GONE);content.addView(alarmBanner,lp(-1,-2,0,0,0,dp(12)));
        content.addView(governmentCard(),lp(-1,-2,0,0,0,dp(12)));
        mapAnchor=mapCard();content.addView(mapAnchor);
         Button advanced=button(t("✨ उन्नत जानकारी · नदी, वर्षा, बाढी, NASA र चेतावनी","✨ Advanced · Rivers, Rain, Flood, NASA & Alerts"));
         advanced.setOnClickListener(v->{Intent i=new Intent(this,FloodSafeAdvancedActivity.class);i.putExtra("lat",lat);i.putExtra("lon",lon);startActivity(i);});
         content.addView(advanced,lp(-1,dp(62),0,dp(10),0,dp(12)));
        content.addView(riskCard());
        content.addView(rainGaugeCard());
        nearSection=nearCard();content.addView(nearSection);
        content.addView(nationalCard());
        humanCard=humanCard();content.addView(humanCard);
        // Only one editorial slot: fresh news OR knowledge, never both.
        newsAnchor=newsCard();content.addView(newsAnchor);
        content.addView(privacyCard());
        root.addView(bottomNav(),bottomParams());
        Button sathi=button("🤖 SATHI");sathi.setTextSize(13);sathi.setOnClickListener(v->showSathiDialog(null));FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(dp(104),dp(48),Gravity.END|Gravity.BOTTOM);fp.setMargins(0,0,dp(18),dp(82));root.addView(sathi,fp);
        applyLanguage();SafeInsets.apply(root);root.post(mapVisibilityTick);return root;
    }

    private View header(){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,0,0,dp(12));
        ImageView icon=new ImageView(this);icon.setImageResource(R.mipmap.ic_launcher);GradientDrawable ib=round(Color.WHITE,16,Color.rgb(209,229,239),1);icon.setBackground(ib);icon.setPadding(dp(3),dp(3),dp(3),dp(3));row.addView(icon,new LinearLayout.LayoutParams(dp(52),dp(52)));
        LinearLayout brand=new LinearLayout(this);brand.setOrientation(LinearLayout.VERTICAL);brand.setPadding(dp(10),0,0,0);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,-2,1f);row.addView(brand,bp);
        TextView title=text("FloodSafe Nepal",25,true,Color.rgb(16,39,70));brand.addView(title);brandSub=text("",12,true,Color.rgb(82,116,139));brand.addView(brandSub);
        langBtn=text("",12,true,Color.rgb(18,48,76));langBtn.setGravity(Gravity.CENTER);langBtn.setPadding(dp(12),dp(10),dp(12),dp(10));langBtn.setBackground(round(Color.WHITE,99,Color.rgb(209,229,239),1));langBtn.setOnClickListener(v->{
            english=!english;
            getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();
            // Switch visible text in place; no GPS/weather/network refresh on a language tap.
            applyLanguage();
            refreshRiverUi();
            updateSelectedDistrictWeather();
            renderGovernment();
            if(newsShowingKnowledge){
                newsTitle.setText(t("📚 ज्ञानका कुरा","📚 Knowledge for Life"));
                newsSub.setText(newsKnowledgeDisconnected?
                    t("समाचार स्रोत जोडिएन • नयाँ खबर आएपछि आफैँ देखिन्छ","News feed unavailable • Fresh stories return automatically"):
                    t("३० मिनेटभित्र नयाँ समाचार छैन • जीवनोपयोगी ज्ञान","No news published in the last 30 minutes • Life lessons"));
                renderCurrentNewsKnowledgeLanguage();
            }else if(!freshNewsOnScreen.isEmpty()){
                renderNews(new ArrayList<>(freshNewsOnScreen));
            }
            translateExistingViews(root);
        });row.addView(langBtn);
        return row;
    }

    private View hero(){
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(20),dp(18),dp(20),dp(20));GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{Color.rgb(44,143,199),Color.rgb(30,121,173),Color.rgb(23,108,125)});g.setCornerRadius(dp(31));card.setBackground(g);
        LinearLayout stripe=new LinearLayout(this);stripe.setOrientation(LinearLayout.HORIZONTAL);View b=new View(this),w=new View(this),r=new View(this);b.setBackgroundColor(Color.rgb(0,56,147));w.setBackgroundColor(Color.WHITE);r.setBackgroundColor(Color.rgb(220,20,60));stripe.addView(b,new LinearLayout.LayoutParams(0,dp(6),45));stripe.addView(w,new LinearLayout.LayoutParams(0,dp(6),10));stripe.addView(r,new LinearLayout.LayoutParams(0,dp(6),45));card.addView(stripe,lp(-1,dp(6),0,0,0,dp(18)));
        LinearLayout top=new LinearLayout(this);top.setOrientation(LinearLayout.HORIZONTAL);place=text("",14,true,Color.WHITE);clock=text("",11,true,Color.WHITE);top.addView(place,new LinearLayout.LayoutParams(0,-2,1f));top.addView(clock);card.addView(top);
        temp=text("—°",66,false,Color.WHITE);
         LinearLayout heroMiddle=new LinearLayout(this);heroMiddle.setOrientation(LinearLayout.HORIZONTAL);heroMiddle.setGravity(Gravity.CENTER_VERTICAL);
         heroMiddle.addView(temp,new LinearLayout.LayoutParams(0,-2,1.1f));
         miniForecast=new NativeSevenDayChart(this);miniForecast.useLanguage(english);
         heroMiddle.addView(miniForecast,new LinearLayout.LayoutParams(0,dp(124),1.5f));
         card.addView(heroMiddle,lp(-1,-2,0,dp(12),0,0));weatherText=text("",27,true,Color.WHITE);card.addView(weatherText);weatherSupport=text("",13,false,Color.rgb(232,247,255));card.addView(weatherSupport,lp(-1,-2,0,dp(6),0,0));
        rainTiming=text("",12,true,Color.WHITE);rainTiming.setPadding(dp(10),dp(9),dp(10),dp(9));rainTiming.setBackground(round(Color.argb(55,7,61,95),14,Color.argb(64,255,255,255),1));card.addView(rainTiming,lp(-1,-2,0,dp(11),0,0));
        LinearLayout grid=new LinearLayout(this);grid.setOrientation(LinearLayout.HORIZONTAL);grid.setPadding(0,dp(14),0,0);rain=weatherStat(grid,"—",t("वर्षा","Rain"));humidity=weatherStat(grid,"—",t("आर्द्रता","Humidity"));wind=weatherStat(grid,"—",t("हावा","Wind"));card.addView(grid);return card;
    }
    private TextView weatherStat(LinearLayout parent,String value,String label){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);TextView v=text(value,18,true,Color.WHITE);TextView l=text(label,11,true,Color.rgb(215,238,248));box.addView(v);box.addView(l);parent.addView(box,new LinearLayout.LayoutParams(0,-2,1f));return v;}

    // MapLibre satellite / DEM + river GeoJSON are deliberately NOT inflated inside
    // the Home ScrollView. Rendering a MapView while scrolling caused repeated ANRs
    // on real devices. Full live map remains available on a dedicated screen.
    private View mapCard(){
        LinearLayout c=card();
        mapTitle=text(t("🇳🇵 आधिकारिक नदी नक्सा","🇳🇵 Official river map"),20,true,Color.rgb(16,39,70));
        mapSub=text(t("DHM/BIPAD नदी स्टेशन, नदीको चमक र ७७ जिल्लाको मौसम चिन्ह।",
                       "DHM/BIPAD river stations, river glow and 77-district weather icons."),13,false,Color.rgb(99,126,144));
        c.addView(mapTitle);c.addView(mapSub,lp(-1,-2,0,dp(8),0,dp(12)));
        TextView preview=text(t("🗺️ नदीको नक्सा, 3D, zoom र बादल हेर्न तल थिच्नुहोस्।",
                         "🗺️ Open the live map for river geometry, 3D, zoom and weather clouds."),15,true,Color.rgb(31,80,113));
        preview.setPadding(dp(14),dp(25),dp(14),dp(25));
        preview.setBackground(round(Color.rgb(234,248,255),20,Color.rgb(168,210,230),1));
        c.addView(preview);
        Button open=button(t("🗺️ लाइभ नदी नक्सा खोल्नुहोस् →","🗺️ Open live river map →"));
        open.setOnClickListener(v->openMapScreen());
        c.addView(open,lp(-1,dp(57),0,dp(12),0,0));
        mapHint=text(t("नक्साको rendering छुट्टै स्क्रिनमा हुन्छ, Home scrolling अड्किँदैन।",
                       "The map runs separately so Home stays responsive."),11,false,Color.rgb(103,132,154));
        c.addView(mapHint,lp(-1,-2,0,dp(8),0,0));
        return c;
    }
    private void openMapScreen(){
        Intent i=new Intent(this,FloodSafeMapActivity.class);
        i.putExtra("lat",lat);i.putExtra("lon",lon);
        startActivity(i);
    }
    private View rainGaugeCard(){
        LinearLayout c=card();
        rainGaugeTitle=text(t("🌧️ GPS नजिकको DHM वर्षामापक","🌧️ Nearest DHM rain gauge"),19,true,Color.rgb(17,50,77));
        rainGaugeInfo=text(t("नेपालको location लिएपछि नजिकको आधिकारिक स्टेशन जाँचिन्छ।",
                            "The closest official rain gauge is checked when Nepal GPS is available."),13,true,Color.rgb(47,80,104));
        rainGaugeHint=text(t("यो Open-Meteo अनुमान होइन; उपलब्ध भए DHM को मापन र मिति देखिन्छ।",
                            "Actual DHM observation, when available; separate from Open-Meteo model."),11,false,Color.rgb(102,132,151));
        c.addView(rainGaugeTitle);
        c.addView(rainGaugeInfo,lp(-1,-2,0,dp(12),0,0));
        c.addView(rainGaugeHint,lp(-1,-2,0,dp(8),0,0));
        return c;
    }
    private void refreshNearbyRainGauge(){
        if(rainGaugeInfo==null)return;
        if(!isNepal(lat,lon)){
            rainGaugeInfo.setText(t("नेपालभित्र GPS हुँदा मात्र DHM वर्षामापकसँग दूरी तुलना गर्न सकिन्छ।",
                                    "Nearest DHM rain gauge applies only to a GPS location within Nepal."));
            rainGaugeHint.setText(t("यहाँको मौसम भने Open-Meteo बाट हेर्न सकिन्छ।",
                                   "Your local weather forecast is available separately from Open-Meteo."));
            return;
        }
        final double targetLat=lat,targetLon=lon;
        long now=System.currentTimeMillis();
        if(now-lastRainGaugeRequestAt<10L*60L*1000L&&
           Double.isFinite(lastRainGaugeLat)&&distanceBetweenKm(targetLat,targetLon,lastRainGaugeLat,lastRainGaugeLon)<3d)return;
        lastRainGaugeRequestAt=now;lastRainGaugeLat=targetLat;lastRainGaugeLon=targetLon;
        rainGaugeInfo.setText(t("DHM को नजिकको वास्तविक वर्षामापक जाँच हुँदैछ…",
                                "Checking the nearest real DHM rain gauge…"));
        io.execute(()->{
            try{
                JSONObject root=OfficialStationFeeds.rainfall();
                JSONArray data=root.optJSONArray("results");
                JSONObject nearest=null;double best=Double.POSITIVE_INFINITY;
                if(data!=null)for(int i=0;i<data.length();i++){
                    JSONObject o=data.optJSONObject(i);if(o==null)continue;
                    double a=o.optDouble("latitude",Double.NaN),b=o.optDouble("longitude",Double.NaN);
                    if(!Double.isFinite(a)||!Double.isFinite(b))continue;
                    double km=distanceBetweenKm(targetLat,targetLon,a,b);
                    if(km<best){best=km;nearest=o;}
                }
                final JSONObject station=nearest;final double km=best;
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed()||rainGaugeInfo==null)return;
                    // Ignore a reply for an older GPS location.
                    if(distanceBetweenKm(lat,lon,targetLat,targetLon)>3d)return;
                    if(station==null){
                        rainGaugeInfo.setText(t("अहिले पुष्टि भएको DHM वर्षा मापन उपलब्ध छैन।",
                                            "No currently verified DHM rainfall observation available."));
                        rainGaugeHint.setText(t("API उपलब्ध नभए अनुमानलाई मापन भनेर देखाइँदैन।",
                                             "A forecast is not substituted for a missing gauge reading."));
                        return;
                    }
                    String name=station.optString("stationName","DHM");
                    double amount=station.optDouble("rainfall",Double.NaN);
                    String amt=Double.isFinite(amount)?String.format(Locale.US,"%.1f mm",amount):"—";
                    rainGaugeInfo.setText("📍 "+name+" · "+String.format(Locale.US,"%.1f km",km)+"\n🌧 "+amt);
                    rainGaugeHint.setText((english?"DHM actual rain station · Observed: ":"DHM वास्तविक वर्षामापक · मापन: ")+station.optString("observedAt","—")+
                       (km>50d?t("\n⚠️ यो स्टेशन ५० किमिभन्दा टाढा छ; यहाँको सटीक वर्षा होइन।",
                                  "\n⚠️ This gauge is over 50 km away; not your exact local rainfall."):
                                  t("\nOpen-Meteo को GPS वर्षा अनुमानबाट छुट्टै वास्तविक मापन।",
                                    "\nObserved rain, distinct from GPS modelled rainfall.")));
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed()||rainGaugeInfo==null)return;
                    rainGaugeInfo.setText(t("DHM वर्षा स्टेशनको ताजा मापन अहिले उपलब्ध छैन।",
                                            "Current official DHM rainfall feed unavailable."));
                    rainGaugeHint.setText(t("मौसमको अनुमानलाई सरकारी मापन मानिएको छैन।",
                                           "Model weather is not presented as an official observation."));
                });
            }
        });
    }
    private static double distanceBetweenKm(double a,double o,double b,double p){
        if(!Double.isFinite(a)||!Double.isFinite(o)||!Double.isFinite(b)||!Double.isFinite(p))return Double.POSITIVE_INFINITY;
        double x=Math.toRadians(b-a),y=Math.toRadians(p-o);
        double q=Math.sin(x/2)*Math.sin(x/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(b))*Math.sin(y/2)*Math.sin(y/2);
        return 12742d*Math.asin(Math.min(1d,Math.sqrt(q)));
    }

    private View governmentCard(){
        LinearLayout c=card();
        c.addView(text(t("⚠️ नेपाल सरकारका मौसम तथा बाढी सूचना","⚠️ Government weather and flood advisories"),19,true,Color.rgb(16,39,70)));
        governmentStatus=text(t("DHM / NDRRMA सूचना जाँच हुँदैछ…","Checking DHM / NDRRMA notices…"),12,false,Color.rgb(103,132,154));
        c.addView(governmentStatus);
        governmentList=new LinearLayout(this);governmentList.setOrientation(LinearLayout.VERTICAL);
        c.addView(governmentList,lp(-1,-2,0,dp(8),0,0));
        Button more=smallButton(t("सबै सरकारी सूचना","All government advisories"));
        more.setOnClickListener(v->{expandedGovernment=!expandedGovernment;renderGovernment();});
        c.addView(more,lp(-1,dp(45),0,dp(8),0,0));
        return c;
    }
    private void refreshGovernment(){
        io.execute(()->{
            try {
                JSONObject result=GovernmentNotices.fetch();
                JSONArray notices=GovernmentNotices.active(result,System.currentTimeMillis());
                runOnUiThread(()->{
                    if(isFinishing()||governmentList==null)return;
                    currentGovernmentNotices=notices;
                    governmentCheckedAt=System.currentTimeMillis();
                    renderGovernment();
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    if(governmentStatus!=null)governmentStatus.setText(t("हाल पुष्टि गरिएका सरकारी सूचना ल्याउन सकिएन। DHM मा जाँच्नुहोस्।","Verified government advisories unavailable. Check DHM directly."));
                });
            }
        });
    }
    private void renderGovernment(){
        if(governmentList==null)return;
        // Revalidate expiry even when offline; the last fetched warning must not remain forever.
        JSONArray stillValid=new JSONArray();
        long now=System.currentTimeMillis();
        for(int i=0;i<currentGovernmentNotices.length();i++){
            JSONObject item=currentGovernmentNotices.optJSONObject(i);
            if(GovernmentNotices.valid(item,now))stillValid.put(item);
        }
        currentGovernmentNotices=stillValid;
        governmentList.removeAllViews();
        int count=currentGovernmentNotices.length();
        governmentStatus.setText(count==0?t("हाल लागू भएको प्रमाणित सरकारी सूचना भेटिएन।","No currently active verified government notices.")
          :t("DHM / NDRRMA का "+count+" लागू सूचना · मूल सरकारी प्रकाशनबाट स्रोत हेर्नुहोस्",""+count+" active DHM / NDRRMA advisories · read original publication"));
        for(int i=0;i<Math.min(count,expandedGovernment?count:1);i++){
            JSONObject n=currentGovernmentNotices.optJSONObject(i);
            if(n==null)continue;
            String source=n.optString("sourceUrl"),title=GovernmentNotices.title(n,english);
            String period=GovernmentNotices.period(n,english);
            TextView v=text(n.optString("agency")+" • "+title+"\n"+period,13,true,Color.rgb(30,65,84));
            v.setPadding(dp(12),dp(11),dp(12),dp(11));
            v.setBackground(round(Color.rgb(255,249,236),15,Color.rgb(227,205,166),1));
            LinearLayout.LayoutParams p=lp(-1,-2,0,dp(5),0,dp(5));
            governmentList.addView(v,p);
            v.setOnClickListener(view->new AlertDialog.Builder(this)
                .setTitle(n.optString("agency")+" · "+title)
                .setMessage(GovernmentNotices.summary(n,english)+"\n\n"+period+"\n\n"+t("सरकारी सूचनाको स्वतन्त्र relay; स्रोतबाट पुष्टि गर्नुहोस्।","Independently relayed government announcement; verify the original source."))
                .setPositiveButton(t("मूल सूचना","Open original"),(d,w)->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(source)));}catch(Exception ignored){}})
                .setNegativeButton(t("बन्द","Close"),null).show());
        }
        if(count==0){
            TextView link=text(t("मूल DHM वेबसाइट खोल्नुहोस् ↗","Open official DHM website ↗"),12,true,Color.rgb(18,114,167));
            governmentList.addView(link);
            link.setOnClickListener(v->startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(GovernmentNotices.DIRECT_DHM))));
        }
    }

    private View riskCard(){LinearLayout c=card();LinearLayout h=new LinearLayout(this);h.setOrientation(LinearLayout.HORIZONTAL);LinearLayout left=new LinearLayout(this);left.setOrientation(LinearLayout.VERTICAL);h.addView(left,new LinearLayout.LayoutParams(0,-2,1));TextView title=text(t("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम","🛡️ Flood risk near me"),20,true,Color.rgb(16,39,70));left.addView(title);feedFresh=text("",12,true,Color.rgb(100,130,151));left.addView(feedFresh);riskBadge=badge("—",Color.rgb(237,247,252),Color.rgb(23,116,174));h.addView(riskBadge);c.addView(h);riskValue=text("—",34,true,Color.rgb(85,117,139));c.addView(riskValue,lp(-1,-2,0,dp(12),0,0));riskText=text("",13,false,Color.rgb(95,125,146));c.addView(riskText);LinearLayout stats=new LinearLayout(this);stats.setOrientation(LinearLayout.HORIZONTAL);stationCount=stat(stats,"—",t("सबै official स्टेशन","Official stations"));warningCount=stat(stats,"—",t("चेतावनी","Warning"));dangerCount=stat(stats,"—",t("खतरा","Danger"));c.addView(stats,lp(-1,-2,0,dp(12),0,0));return c;}
    private TextView stat(LinearLayout p,String n,String l){LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);b.setGravity(Gravity.CENTER);b.setPadding(dp(5),dp(9),dp(5),dp(9));b.setBackground(round(Color.rgb(243,249,252),16,Color.rgb(218,234,242),1));TextView v=text(n,21,true,Color.rgb(16,39,70));TextView s=text(l,9,true,Color.rgb(103,132,154));s.setGravity(Gravity.CENTER);b.addView(v);b.addView(s);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(0,-2,1);q.setMargins(dp(3),0,dp(3),0);p.addView(b,q);return v;}

    private View nearCard(){LinearLayout c=card();nearTitle=text("",20,true,Color.rgb(16,39,70));nearSub=text("",12,true,Color.rgb(100,130,151));c.addView(nearTitle);c.addView(nearSub);nearList=new LinearLayout(this);nearList.setOrientation(LinearLayout.VERTICAL);c.addView(nearList,lp(-1,-2,0,dp(10),0,0));return c;}
    private View nationalCard(){
        LinearLayout c=card();nationalTitle=text("",20,true,Color.rgb(16,39,70));
        nationalSub=text("",12,true,Color.rgb(100,130,151));
        nationalFresh=text("",12,true,Color.rgb(100,130,151));
        c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);
        districtPicker=new AutoCompleteTextView(this);
        districtPicker.setSingleLine(true);districtPicker.setTextSize(15);
        districtPicker.setPadding(dp(12),0,dp(12),0);districtPicker.setThreshold(1);
        districtPicker.setBackground(round(Color.rgb(252,254,255),16,Color.rgb(193,218,229),1));
        java.util.ArrayList<String> districts=new java.util.ArrayList<>();
        try{JSONArray list=DistrictWeatherStore.districts(this);
          for(int i=0;i<list.length();i++){String name=list.getJSONObject(i).optString("name").trim();if(!name.isEmpty()&&!districts.contains(name))districts.add(name);}}
        catch(Exception ignored){}
        java.util.Collections.sort(districts,String.CASE_INSENSITIVE_ORDER);
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_dropdown_item_1line,districts);
        districtPicker.setAdapter(adapter);
        districtPicker.setOnFocusChangeListener((v,has)->{if(has)districtPicker.showDropDown();});
        districtPicker.setOnClickListener(v->districtPicker.showDropDown());
        c.addView(districtPicker,lp(-1,dp(54),0,dp(12),0,0));
        nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);
        c.addView(nationalList,lp(-1,-2,0,dp(10),0,0));
        districtWeatherInfo=text(t("जिल्ला छान्दा त्यसै ठाउँको मौसम अनुमान देखिन्छ।","Choose a district for its local weather model."),12,false,Color.rgb(95,125,146));
        c.addView(districtWeatherInfo,lp(-1,-2,0,dp(8),0,0));
        districtPicker.addTextChangedListener(new TextWatcher(){
          public void beforeTextChanged(CharSequence x,int a,int b,int d){}
          public void onTextChanged(CharSequence x,int a,int b,int d){
            String typed=x.toString().trim();
            String match="";
            for(String name:districts)if(name.equalsIgnoreCase(typed)){match=name;break;}
            if(!selectedDistrict.equals(match)){selectedDistrict=match;nationalPageSize=12;refreshNationalList();updateSelectedDistrictWeather();}
          }
          public void afterTextChanged(Editable x){}
        });
        districtPicker.setOnItemClickListener((parent,view,pos,id)->{
           String chosen=String.valueOf(parent.getItemAtPosition(pos));
           selectedDistrict=chosen;nationalPageSize=12;
           refreshNationalList();updateSelectedDistrictWeather();
           districtPicker.clearFocus();
        });
        refreshNationalList();
        return c;
    }
    private void refreshNationalList(){
        if(nationalList==null)return;
        nationalList.removeAllViews();
        if(selectedDistrict.isEmpty()){
            nationalList.addView(empty(t("🔎 माथि ७७ जिल्लामध्ये आफूले हेर्न चाहेको जिल्ला खोजेर छान्नुहोस्। सबै स्टेशन एकैचोटि देखाइँदैनन्।",
                  "🔎 Search and select one of 77 districts above. Stations stay hidden until you choose.")));
            return;
        }
        List<RiverStation> matches=new ArrayList<>();
        synchronized(stations){for(RiverStation q:stations){
            if(selectedDistrict.equalsIgnoreCase(q.district==null?"":q.district.trim()))matches.add(q);
        }}
        if(matches.isEmpty()){nationalList.addView(empty(t(selectedDistrict+" मा हाल आधिकारिक नदी स्टेशन/मापन भेटिएन।",
              "No official station/reading available for "+selectedDistrict+".")));return;}
        TextView summary=text(t("📍 "+selectedDistrict+" • "+matches.size()+" नदी स्टेशन","📍 "+selectedDistrict+" • "+matches.size()+" river stations"),13,true,Color.rgb(49,89,109));
        nationalList.addView(summary,lp(-1,-2,0,0,0,dp(7)));
        for(int i=0;i<Math.min(nationalPageSize,matches.size());i++)nationalList.addView(stationRow(matches.get(i)));
        if(matches.size()>nationalPageSize){
            Button more=smallButton(t("थप "+(matches.size()-nationalPageSize)+" स्टेशन हेर्नुहोस् ↓","Show "+(matches.size()-nationalPageSize)+" more stations ↓"));
            more.setOnClickListener(v->{nationalPageSize+=12;refreshNationalList();});
            nationalList.addView(more,lp(-1,dp(46),0,dp(4),0,dp(5)));
        }
    }
    private View gyanCard(){
        // Automatically rotates short knowledge highlights. No reading screen or tap required.
        LinearLayout c=card();
        gyanTitle=text(t("📚 ज्ञानका कुरा","📚 Knowledge for Life"),20,true,Color.rgb(65,52,39));c.addView(gyanTitle);
        gyanRotator=new LinearLayout(this);gyanRotator.setOrientation(LinearLayout.VERTICAL);
        gyanSub=text("",14,true,Color.rgb(150,104,52));
        gyanRotator.addView(gyanSub,lp(-1,-2,0,dp(10),0,dp(5)));
        gyanMessage=text("",14,false,Color.rgb(75,72,64));
        gyanMessage.setMaxLines(4);
        gyanMessage.setEllipsize(android.text.TextUtils.TruncateAt.END);
        gyanRotator.addView(gyanMessage);
        c.addView(gyanRotator);
        TextView footer=text(t("✨ नयाँ ज्ञान आफैँ आउँछ • गीताको भावार्थ, बाढी, विज्ञान, सामान्य ज्ञान र जीवन","✨ Automatically changing insights • Gita, flood, science and life"),10,false,Color.rgb(132,119,106));
        c.addView(footer,lp(-1,-2,0,dp(10),0,0));
        return c;
    }
    private LinearLayout humanCard(){LinearLayout c=card();TextView t=text("🧑‍🤝‍🧑 "+t("Human Status — पछिल्लो विपद्","Human Status — latest disaster"),20,true,Color.rgb(16,39,70));humanFresh=text("",12,true,Color.rgb(100,130,151));c.addView(t);c.addView(humanFresh);LinearLayout stats=new LinearLayout(this);stats.setOrientation(LinearLayout.HORIZONTAL);humanDeaths=stat(stats,"—",t("मृतक","Deaths"));humanInjured=stat(stats,"—",t("घाइते","Injured"));humanMissing=stat(stats,"—",t("बेपत्ता","Missing"));humanRescued=stat(stats,"—",t("उद्धार","Rescued"));c.addView(stats,lp(-1,-2,0,dp(10),0,0));humanDetail=text("",12,false,Color.rgb(95,125,146));c.addView(humanDetail);c.setVisibility(View.GONE);return c;}
    private View newsCard(){LinearLayout c=card();newsTitle=text("",20,true,Color.rgb(16,39,70));
        newsSub=text("RONB Post • Radio Nepal • News24 Nepal",12,true,Color.rgb(100,130,151));
        c.addView(newsTitle);c.addView(newsSub);
        // Foreground feed polling and lifecycle refresh are automatic; no manual button.
        newsList=new LinearLayout(this);newsList.setOrientation(LinearLayout.VERTICAL);
        c.addView(newsList,lp(-1,-2,0,dp(8),0,0));return c;}
    private View privacyCard(){LinearLayout c=card();privacyTitle=text("",20,true,Color.rgb(16,39,70));privacySub=text("",12,true,Color.rgb(100,130,151));c.addView(privacyTitle);c.addView(privacySub);Button b=smallButton(t("गोपनीयता नीति हेर्नुहोस् →","View privacy policy →"));b.setOnClickListener(v->showPrivacy());c.addView(b,lp(-1,dp(48),0,dp(10),0,0));return c;}

    private View bottomNav(){LinearLayout nav=new LinearLayout(this);nav.setOrientation(LinearLayout.HORIZONTAL);nav.setPadding(dp(8),dp(7),dp(8),dp(7));nav.setBackground(round(Color.argb(246,255,255,255),24,Color.rgb(208,227,237),1));Button h=navButton("⌂\n"+t("गृह","Home")),m=navButton("🗺️\n"+t("नदी नक्सा","River map")),a=navButton("✨\n"+t("उन्नत","Advanced")),n=navButton("🔔\n"+t("समाचार","News"));nav.addView(h,weight());nav.addView(m,weight());nav.addView(a,weight());nav.addView(n,weight());h.setOnClickListener(v->smoothTo(homeAnchor));m.setOnClickListener(v->openMapScreen());a.setOnClickListener(v->{Intent i=new Intent(this,FloodSafeAdvancedActivity.class);i.putExtra("lat",lat);i.putExtra("lon",lon);startActivity(i);});n.setOnClickListener(v->{smoothTo(newsAnchor);if(System.currentTimeMillis()-newsLastFetchedAt>=FloodSafeRemoteConfig.newsPollMillis())refreshNews();});return nav;}
    private FrameLayout.LayoutParams bottomParams(){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(-1,dp(72),Gravity.BOTTOM);p.setMargins(dp(9),0,dp(9),dp(9));return p;}
    private void smoothTo(View v){if(v==null)return;scroll.post(()->scroll.smoothScrollTo(0,Math.max(0,v.getTop()-dp(8))));}

    private void applyLanguage(){brandSub.setText(t("नेपाल • नदी • बाढी • चौबीसै घण्टा चेतावनी","Nepal • rivers • floods • 24/7 alerts"));langBtn.setText(t("अङ्ग्रेजी","नेपाली"));weatherText.setText(currentWeather.isEmpty()?t("निगरानी स्थान छान्नुहोस्","Choose a monitoring location"):currentWeather);weatherSupport.setText(t("स्थानीय मौसम र DHM/BIPAD को वास्तविक नदी अवस्था","Local weather + official BIPAD/DHM river status"));if(!Double.isFinite(lat)){place.setText(t("📍 नेपालमा निगरानी स्थान छान्नुहोस्","📍 Choose a monitoring location"));rainTiming.setText(t("हालको स्थान लिएपछि आगामी वर्षा timing देखाइन्छ।","Rain timing appears after location is available."));}mapTitle.setText(t("🇳🇵 आधिकारिक नदी स्टेशन नक्सा","🇳🇵 Official river station map"));mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, चेतावनी र official time हेर्नुहोस्।","Tap a river station for level, warning and official time."));mapHint.setText(t("🇳🇵 आधिकारिक नदी स्टेशन र नदी संरचना","🇳🇵 official stations and river geometry"));nearTitle.setText(t("🌊 नजिकका नदी स्टेशन","🌊 Nearby river stations"));nearSub.setText(t("तपाईंको स्थान नजिकको official नदी अवस्था","Official river status near your location"));nationalTitle.setText(t("🌊 ७७ जिल्लाका नदी स्टेशन खोज्नुहोस्","🌊 Find river stations by district"));nationalSub.setText(t("जिल्ला छानेपछि त्यही जिल्लाका आधिकारिक स्टेशन र मापन देखिन्छन्।","Choose a district to view only its official stations and readings."));if(districtPicker!=null)districtPicker.setHint(t("🔎 जिल्लाको नाम टाइप गर्नुहोस् / छान्नुहोस्","🔎 Search or select a district"));if(gyanTitle!=null)gyanTitle.setText(t("📚 ज्ञानका कुरा","📚 Knowledge for Life"));if(gyanSub!=null&&gyanMessage!=null){int prev=(gyanIndex+GyanKnowledge.ITEMS.size()-11)%GyanKnowledge.ITEMS.size();GyanKnowledge.Entry e=GyanKnowledge.ITEMS.get(prev);gyanSub.setText("✦ "+GyanKnowledge.categoryName(e.category,english)+" · "+e.title(english));gyanMessage.setText(e.body(english));}newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));privacyTitle.setText(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety"));privacySub.setText(t("स्थान, माइक्रोफोन र चेतावनीका विवरण कसरी प्रयोग हुन्छन् हेर्नुहोस्।","See how location, microphone and alert data are used."));if(miniForecast!=null)miniForecast.useLanguage(english);updateOutsideNotice();}
    private String t(String ne,String en){
        if(ne!=null&&en!=null&&!ne.isEmpty()&&!en.isEmpty()&&!ne.equals(en)){
            neToEn.put(ne,en);
            enToNe.put(en,ne);
        }
        return english?en:ne;
    }
    private String localizedExistingText(String value){
        if(value==null||value.isEmpty())return value;
        java.util.Map<String,String> source=english?neToEn:enToNe;
        String exact=source.get(value);
        if(exact!=null)return exact;
        // Some original labels include an emoji/nav icon before the bilingual text.
        for(java.util.Map.Entry<String,String> pair:source.entrySet()){
            String before=pair.getKey();
            if(before.length()<4||!value.endsWith(before))continue;
            int prefixLen=value.length()-before.length();
            if(prefixLen>0&&prefixLen<=14){
                String prefix=value.substring(0,prefixLen);
                if(prefix.endsWith(" ")||prefix.endsWith("\n"))
                    return prefix+pair.getValue();
            }
        }
        return value;
    }
    private void translateExistingViews(View view){
        if(view==null)return;
        if(view instanceof TextView && !(view instanceof EditText)){
            TextView v=(TextView)view;
            String old=v.getText().toString(),translated=localizedExistingText(old);
            if(!old.equals(translated))v.setText(translated);
        }
        if(view instanceof ViewGroup){
            ViewGroup group=(ViewGroup)view;
            for(int i=0;i<group.getChildCount();i++)translateExistingViews(group.getChildAt(i));
        }
    }
    private void renderCurrentNewsKnowledgeLanguage(){
        if(newsKnowledgeCategory==null||newsKnowledgeText==null||GyanKnowledge.ITEMS.isEmpty())return;
        // Keep the current lesson; the language button does not advance the rotation.
        GyanKnowledge.Entry e=FloodSafeRemoteConfig.newsLessonAt(newsKnowledgeIndex-7);
        newsKnowledgeCategory.setText("✦ "+GyanKnowledge.categoryName(e.category,english)+" · "+e.title(english));
        newsKnowledgeText.setText(e.body(english));
    }

    private void refreshAll(){restoreLocation();refreshRivers();refreshGovernment();refreshDistrictWeather();refreshHuman();refreshNews();refreshNearbyRainGauge();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}
    private void restoreLocation(){if(Double.isFinite(lat)&&Double.isFinite(lon)){place.setText(isNepal(lat,lon)?t("📍 पछिल्लो GPS • Nepal","📍 Last GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • weather follows this location"));updateOutsideNotice();}}
    private void updateOutsideNotice(){TextView v=root==null?null:root.findViewById(android.R.id.hint);if(v==null)return;boolean out=Double.isFinite(lat)&&Double.isFinite(lon)&&!isNepal(lat,lon);v.setVisibility(out?View.VISIBLE:View.GONE);v.setText(t("🇳🇵 FloodSafe नेपालभित्रको निगरानी\nतपाईं नेपाल बाहिर हुँदा नजिकको नदी चेतावनी पठाइँदैन। नेपालभित्र हालको GPS हुँदा २ किमिभित्रको प्रमाणित चेतावनी/खतरा अवस्थामा मात्र आपत्कालीन नदी सूचना आउँछ।","🇳🇵 FloodSafe Nepal-only monitoring\nOutside Nepal, nearby river warnings are not sent. In Nepal, only verified Warning/Danger within 2 km can trigger the emergency river alert."));}

    private void requestLocation(){requestLocation(false);}
    private void requestLocation(boolean fromTap){
        if(!hasLocationPermission()){
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);
            return;
        }
        if(lm==null)return;
        if(fromTap){
            long elapsed=android.os.SystemClock.elapsedRealtime();
            // Prevent a double tap from queuing multiple GPS and weather refreshes.
            if(lastLocateTapElapsed>0&&elapsed-lastLocateTapElapsed<1800L)return;
            lastLocateTapElapsed=elapsed;
        }
        try{
            Location a=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            Location b=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            Location best=a==null?b:b==null?a:(a.getTime()>=b.getTime()?a:b);
            // Previously a tap processed a cached fix immediately, and then another GPS
            // callback seconds later: two location labels, two requests and visible flicker.
            // The button now waits for the fresh fix if we already have coordinates.
            if((!fromTap||!Double.isFinite(lat)||!Double.isFinite(lon))&&best!=null
                    &&System.currentTimeMillis()-best.getTime()<24L*60*60*1000)
                onLocationChanged(best);
            if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))
                lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());
            else if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))
                lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());
        }catch(Exception ignored){}
    }
    @Override public void onLocationChanged(Location l){
        if(l==null||!Double.isFinite(l.getLatitude())||!Double.isFinite(l.getLongitude()))return;
        long now=System.currentTimeMillis();
        float[] meters={Float.POSITIVE_INFINITY};
        if(Double.isFinite(lat)&&Double.isFinite(lon)){
            try{Location.distanceBetween(lat,lon,l.getLatitude(),l.getLongitude(),meters);}
            catch(Exception ignored){}
        }
        // The cached fix and the live GPS fix can represent exactly the same place.
        // Keep monitoring timestamps updated, but do not redraw/re-request the whole
        // weather screen twice within the same 90-second window.
        boolean sameRecentFix=meters[0]<65f&&lastLocationRenderAt>0
                &&now-lastLocationRenderAt<90_000L;
        lat=l.getLatitude();lon=l.getLongitude();locAt=now;
        getSharedPreferences(PREFS,MODE_PRIVATE).edit()
            .putLong(KEY_LAT,Double.doubleToRawLongBits(lat))
            .putLong(KEY_LON,Double.doubleToRawLongBits(lon))
            .putLong(KEY_AT,locAt).apply();
        getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit()
            .putLong("weather_last_lat",Double.doubleToRawLongBits(lat))
            .putLong("weather_last_lon",Double.doubleToRawLongBits(lon))
            .putLong("weather_last_fix_at",locAt)
            .putLong("lat",Double.doubleToRawLongBits(lat))
            .putLong("lon",Double.doubleToRawLongBits(lon))
            .putLong("location_time",locAt)
            .putLong("device_lat",Double.doubleToRawLongBits(lat))
            .putLong("device_lon",Double.doubleToRawLongBits(lon))
            .putLong("device_location_time",locAt)
            .putBoolean("follow_device",true)
            .putBoolean("location_stale",false)
            .putBoolean("enabled",true).apply();
        if(!sameRecentFix){
            lastLocationRenderAt=now;
            String label=isNepal(lat,lon)?
                t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):
                t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो",
                  "🌍 GPS outside Nepal • local weather only");
            if(!android.text.TextUtils.equals(place.getText(),label))place.setText(label);
            updateOutsideNotice();
            reverseGeocode();
            fetchWeather(lat,lon);
            refreshNearbyRainGauge();
            refreshRiverUi();
        }
        FloodMonitorService.startIfEnabled(this);
    }
    private void reverseGeocode(){
        final double requestedLat=lat,requestedLon=lon;
        io.execute(()->{
            try{
                List<android.location.Address> addresses=new Geocoder(this,Locale.getDefault())
                    .getFromLocation(requestedLat,requestedLon,1);
                if(addresses==null||addresses.isEmpty())return;
                String label=addresses.get(0).getLocality();
                if(label==null)label=addresses.get(0).getSubAdminArea();
                if(label==null)label=addresses.get(0).getCountryName();
                if(label==null||label.isEmpty())return;
                final String visible="📍 "+label;
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed())return;
                    // A slower response for an older location cannot replace a newer fix.
                    if(Math.abs(lat-requestedLat)>0.00065||Math.abs(lon-requestedLon)>0.00065)return;
                    if(!android.text.TextUtils.equals(place.getText(),visible))place.setText(visible);
                });
            }catch(Exception ignored){}
        });
    }

    private void fetchWeather(double a,double o){
        final long version=++weatherRequestVersion;
        fetchSevenDay(a,o);
        io.execute(()->{
            try{
                String u=String.format(Locale.US,
                    "https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,weather_code,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);
                JSONObject j=getJson(u),c=j.getJSONObject("current");
                final double te=c.optDouble("temperature_2m",Double.NaN),
                    pr=c.optDouble("precipitation",0),hu=c.optDouble("relative_humidity_2m",Double.NaN),
                    wi=c.optDouble("wind_speed_10m",Double.NaN),cloud=c.optDouble("cloud_cover",0);
                final int code=c.optInt("weather_code",0);
                runOnUiThread(()->{
                    if(isFinishing()||isDestroyed()||version!=weatherRequestVersion)return;
                    // Translate only when displaying the completed result. Previous
                    // background requests must not alternate Nepali and English text.
                    String ws=code>=95?t("⛈️ चट्याङ/हुरीको सम्भावना","⛈️ Thunderstorm"):
                        pr>=.5?t("🌧️ वर्षा भइरहेको छ","🌧️ Rain now"):
                        cloud>65?t("☁️ बादल","☁️ Cloudy"):
                        cloud>25?t("⛅ आंशिक बादल","⛅ Partly cloudy"):
                        t("☀️ सफा मौसम","☀️ Sunny");
                    currentWeather=ws;
                    temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");
                    if(!android.text.TextUtils.equals(weatherText.getText(),ws))weatherText.setText(ws);
                    rain.setText(String.format(Locale.US,"%.1f mm",pr));
                    humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");
                    wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");
                    String timing=rainTiming(j);
                    if(!android.text.TextUtils.equals(rainTiming.getText(),timing))rainTiming.setText(timing);
                    if(mapWeather!=null)mapWeather.setConditions(cloud,pr,code);
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    if(version==weatherRequestVersion&&currentWeather.isEmpty())
                        weatherText.setText(t("मौसम refresh हुन सकेन","Weather refresh failed"));
                    // Keep the previous weather card visible on temporary request failures.
                });
            }
        });
    }
    private void fetchSevenDay(double a,double o){
        final long version=++forecastRequestVersion;
        io.execute(()->{
            try{
                String u=String.format(Locale.US,
                    "https://pjbuilts.com/api/floodsafe-station-details?kind=hero&lat=%.6f&lon=%.6f",a,o);
                JSONObject j=getJson(u);
                runOnUiThread(()->{
                    if(version!=forecastRequestVersion||isFinishing()||isDestroyed())return;
                    if(miniForecast!=null)miniForecast.setForecast(j);
                });
            }catch(Exception ignored){
                // Preserve the last good chart rather than blanking it during a GPS tap.
            }
        });
    }
    private String rainTiming(JSONObject j){try{JSONObject h=j.getJSONObject("hourly");JSONArray time=h.getJSONArray("time"),pp=h.getJSONArray("precipitation_probability"),pr=h.getJSONArray("precipitation");for(int i=0;i<Math.min(time.length(),6);i++){double mm=pr.optDouble(i,0);int p=pp.optInt(i,0);if(mm>=.2||p>=55)return t("🌧️ आगामी "+Math.max(1,i+1)+" घण्टाभित्र वर्षाको सम्भावना "+p+"%","🌧️ Rain chance "+p+"% within about "+Math.max(1,i+1)+"h");}return t("☁️ आगामी केही घण्टामा उल्लेख्य वर्षा संकेत छैन","☁️ No significant rain signal in the next few hours");}catch(Exception e){return t("वर्षा timing उपलब्ध छैन","Rain timing unavailable");}}

    private void refreshDistrictWeather(){
        io.execute(()->{
          try{
            JSONArray data=DistrictWeatherStore.fetch(getApplicationContext());
            runOnUiThread(()->{
              if(isFinishing())return;
              districtWeather=data;
              if(districtSky!=null)districtSky.setDistricts(data);
              updateSelectedDistrictWeather();
            });
          }catch(Exception e){
            runOnUiThread(()->{if(districtWeatherInfo!=null)districtWeatherInfo.setText(t(
              "जिल्लाको मौसम अपडेट भएन; अनुमान उपलब्ध छैन।","District weather estimate unavailable."));});
          }
        });
    }
    private void updateSelectedDistrictWeather(){
      if(districtWeatherInfo==null)return;
      if(selectedDistrict.isEmpty()){districtWeatherInfo.setText(t(
        "७७ जिल्लाको मौसम अनुमान नक्सामा; विस्तृत जानकारीका लागि जिल्ला छान्नुहोस्।",
        "Weather models for 77 districts on the map; select one for details."));return;}
      for(int i=0;i<districtWeather.length();i++){
       JSONObject j=districtWeather.optJSONObject(i);if(j==null)continue;
       if(!selectedDistrict.equalsIgnoreCase(j.optString("name")))continue;
       String text=DistrictWeatherStore.icon(j.optInt("code",-1))+" "+selectedDistrict+
         " · "+DistrictWeatherStore.condition(j.optInt("code",-1),english)+
         " · "+String.format(Locale.US,"%.1f mm",j.optDouble("rain",Double.NaN))+
         " · "+String.format(Locale.US,"%.0f%%",j.optDouble("cloud",Double.NaN))+
         "\n"+t("Open-Meteo अनुमान, नदी स्टेशनको मापन होइन।","Open-Meteo model, not a river-gauge measurement.");
       districtWeatherInfo.setText(text);return;
      }
      districtWeatherInfo.setText(t("यस जिल्लाको ताजा मौसम अनुमान उपलब्ध छैन।","No verified current model for this district."));
    }

    private void refreshRivers(){feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));io.execute(()->{try{JSONObject root=OfficialStationFeeds.rivers();JSONArray rows=root.optJSONArray("results");if(rows==null)rows=root.optJSONArray("data");if(rows==null)rows=new JSONArray();List<RiverStation> out=new ArrayList<>();long now=System.currentTimeMillis();for(int i=0;i<rows.length();i++){RiverStation s=parseStation(rows.optJSONObject(i),now);if(s!=null)out.add(s);}out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));synchronized(stations){stations.clear();stations.addAll(out);}runOnUiThread(this::refreshRiverUi);}catch(Exception e){runOnUiThread(()->feedFresh.setText(t("River data refresh हुन सकेन • stale लाई live भनिएको छैन","River refresh failed • stale data is not live")));}});}
    private RiverStation parseStation(JSONObject r,long now){if(r==null)return null;double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;NepalRiverBoundary polygon=nepalDistrictBorder();if(polygon==null||!polygon.contains(o,a))return null;double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel"),warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");long at=parseTime(str(r,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));boolean fresh=at>0&&now-at<=RIVER_FRESH_MS&&at-now<=5*60_000L;String raw=str(r,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);String stage="unknown";int rank=4;if(fresh){if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")){stage="alert";rank=2;}else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE")){stage="normal";rank=3;}}String name=str(r,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official river station";String district=str(r,"districtName","district_name","district");return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank);}
    private void refreshRiverUi(){if(nearList==null||isFinishing()||isDestroyed())return;
      List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
      long fingerprint=37;
      for(RiverStation q:copy){fingerprint=31*fingerprint+q.name.hashCode();
       fingerprint=31*fingerprint+Long.hashCode(q.at);
       fingerprint=31*fingerprint+Double.hashCode(q.level);
       fingerprint=31*fingerprint+q.stage.hashCode();}
      if(fingerprint!=lastStationMapHash){lastStationMapHash=fingerprint;if(map!=null)map.setStations(copy,lat,lon);}
      else if(map!=null)map.updateUserLocation(lat,lon);int d=0,w=0,a=0,n=0,stale=0;for(RiverStation s:copy){switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}}stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));feedFresh.setText(t("DHM/BIPAD · 🔴 "+d+" 🟠 "+w+" 🟡 "+a+" 🔵 "+n+" · मापन नभएका "+stale,"DHM/BIPAD · 🔴 "+d+" 🟠 "+w+" 🟡 "+a+" 🔵 "+n+" · unavailable "+stale));nationalFresh.setText(feedFresh.getText());updateRisk(copy);nearList.removeAllViews();
        boolean inNepal=isNepal(lat,lon)&&locAt>0&&System.currentTimeMillis()-locAt<24L*60*60*1000;
        if(nearSection!=null)nearSection.setVisibility(inNepal?View.VISIBLE:View.GONE);
        if(inNepal){
          List<RiverStation> near=new ArrayList<>(copy);
          near.sort(Comparator.comparingDouble(q->distanceKm(q.lat,q.lon)));
          int shown=0;
          for(RiverStation q:near){if(shown>=5)break;if(distanceKm(q.lat,q.lon)>30d)break;nearList.addView(stationRow(q));shown++;}
          if(shown==0)nearList.addView(empty(t("३० किमिभित्र official स्टेशन भेटिएन।","No official station within 30 km.")));
        }
        refreshNationalList();}
    private View stationRow(RiverStation s){TextView v=text(stageDot(s.stage)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(stageBg(s.stage),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
    private void updateRisk(List<RiverStation> copy){RiverStation best=null;double bestD=Double.POSITIVE_INFINITY;for(RiverStation s:copy){double km=distanceKm(s.lat,s.lon);if(!Double.isFinite(km))continue;if(km<bestD){bestD=km;best=s;}}if(best==null){riskValue.setText("—");riskBadge.setText(t("प्रतीक्षा","WAIT"));riskText.setText(t("नेपालमा location लिएपछि नजिकको official gauge risk देखिन्छ।","Take a Nepal location to see nearby official gauge risk."));alarmBanner.setVisibility(View.GONE);return;}riskValue.setText(stageName(best.stage));riskBadge.setText(stageName(best.stage));riskText.setText(best.name+" • "+String.format(Locale.US,"%.1f km",bestD)+" • "+stationLine(best));int col=stageColor(best.stage);riskValue.setTextColor(col);riskBadge.setTextColor(col);boolean emergency=bestD<=2d&&best.fresh&&best.at>0&&System.currentTimeMillis()-best.at<=EMERGENCY_FRESH_MS&&(best.stage.equals("warning")||best.stage.equals("danger"));alarmBanner.setVisibility(emergency?View.VISIBLE:View.GONE);if(emergency){alarmTitle.setText(best.stage.equals("danger")?t("🚨 DANGER — 2 km भित्र","🚨 DANGER — within 2 km"):t("⚠️ WARNING — 2 km भित्र","⚠️ WARNING — within 2 km"));alarmText.setText(best.name+" • "+stationLine(best));}}
    private String stationLine(RiverStation s){String age=s.at>0?Math.max(0,(System.currentTimeMillis()-s.at)/60000)+" "+t("मिनेटअघि","min ago"):t("मापन समय उपलब्ध छैन","No time");String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("मापन छैन","No level");double d=distanceKm(s.lat,s.lon);return stageName(s.stage)+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • %.1f km",d):"");}
    private void showStation(RiverStation s){StringBuilder b=new StringBuilder();b.append(stageDot(s.stage)).append(" ").append(stageName(s.stage)).append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.2f m",s.warning));if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.2f m",s.danger));b.append("\n").append(t("Official observation: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—").append("\nSource: BIPAD / DHM");new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton("OK",null).show();}

    private void refreshHuman(){io.execute(()->{try{JSONObject inc=getJson(BIPAD+"incident/?limit=500&ordering=-incidentOn"),loss=getJson(BIPAD+"loss-people/?limit=1000&ordering=-createdOn");JSONArray ir=rows(inc),lr=rows(loss);long cutoff=System.currentTimeMillis()-10L*24*60*60*1000;List<String> ids=new ArrayList<>();int incidents=0;for(int i=0;i<ir.length();i++){JSONObject o=ir.optJSONObject(i);if(o==null)continue;long tm=parseTime(str(o,"incidentOn","incident_on","createdOn","created_at","modifiedOn","updated_at","date"));String tx=o.toString().toLowerCase(Locale.ROOT);if(tm>=cutoff&&isDisaster(tx)){incidents++;ids.add(String.valueOf(o.opt("id")));}}int dead=0,inj=0,miss=0,res=0;boolean ds=false,is=false,ms=false,rs=false;for(int i=0;i<lr.length();i++){JSONObject o=lr.optJSONObject(i);if(o==null)continue;String id=str(o,"incident_id","incidentId");if(!id.isEmpty()&&!ids.contains(id))continue;String tx=o.toString().toLowerCase(Locale.ROOT);int q=(int)Math.max(0,numOr(o,"count","people","peopleCount","people_count","number","total","value","noOfPeople","no_of_people"));if(tx.matches(".*(dead|death|deceased|fatal|मृत|मृत्यु).*")){dead+=q;ds=true;}else if(tx.matches(".*(injur|घाइते).*")){inj+=q;is=true;}else if(tx.matches(".*(missing|बेपत्ता).*")){miss+=q;ms=true;}else if(tx.matches(".*(rescued|rescue|उद्धार).*")){res+=q;rs=true;}}final int fi=incidents,fd=dead,fj=inj,fm=miss,fr=res;final boolean fds=ds,fis=is,fms=ms,frs=rs;runOnUiThread(()->{humanCard.setVisibility(fi>0?View.VISIBLE:View.GONE);if(fi>0){humanFresh.setText(t("BIPAD official • पछिल्लो १० दिन • "+fi+" घटना","BIPAD official • last 10 days • "+fi+" incidents"));humanDeaths.setText(fds?String.valueOf(fd):"—");humanInjured.setText(fis?String.valueOf(fj):"—");humanMissing.setText(fms?String.valueOf(fm):"—");humanRescued.setText(frs?String.valueOf(fr):"—");humanDetail.setText(t("अनुमानित संख्या देखाइँदैन। Official loss records मात्र।","No estimated counts. Official loss records only."));}});}catch(Exception ignored){}});}
    private void refreshNews(){
        if(newsList==null||newsRefreshing||isFinishing()||isDestroyed())return;
        newsRefreshing=true;
        // Preserve the visible headline/knowledge during background refresh to prevent UI flicker.
        if(newsList.getChildCount()==0)showNewsKnowledgeFallback(false);
        io.execute(()->{
            final long now=System.currentTimeMillis();
            List<NewsFeedParser.Item> articles=new ArrayList<>();
            boolean anyResponse=false;
            for(String endpoint:new String[]{
                "https://pjbuilts.com/api/news-live-three",
                NEWS_ENDPOINT
            }){
                try{
                    JSONObject root=getJson(endpoint+(endpoint.contains("?")?"&":"?")+"_at="+now);
                    anyResponse=true;
                    List<NewsFeedParser.Item> parsed=NewsFeedParser.parse(root,now);
                    if(!parsed.isEmpty()){articles=parsed;break;}
                }catch(Exception ignored){}
            }
            final boolean reached=anyResponse;
            final List<NewsItem> out=new ArrayList<>();
            for(NewsFeedParser.Item item:articles)
                out.add(new NewsItem(item.title,item.source,item.url,item.at));
            runOnUiThread(()->{
                newsRefreshing=false;
                if(isFinishing()||isDestroyed()||newsList==null)return;
                newsLastFetchedAt=System.currentTimeMillis();
                if(!reached){
                    if(!newsShowingKnowledge)showNewsKnowledgeFallback(true);
                    return;
                }
                // Render only when content changed or the 30-minute window expired.
                if(!sameCurrentNews(out) || newsShowingKnowledge)renderNews(out);
            });
        });
    }
    private boolean sameCurrentNews(List<NewsItem> incoming){
        long now=System.currentTimeMillis();
        List<NewsItem> filtered=new ArrayList<>();
        for(NewsItem n:incoming)if(n.at>0&&n.at<=now+300000L&&now-n.at<=NewsFeedParser.RECENT_MS)filtered.add(n);
        if(filtered.size()!=freshNewsOnScreen.size())return false;
        for(int i=0;i<filtered.size();i++){
            NewsItem a=filtered.get(i),b=freshNewsOnScreen.get(i);
            if(a.at!=b.at||!a.url.equals(b.url))return false;
        }
        return true;
    }
    private void renderNews(List<NewsItem> out){
        currentNewsForSathi=new JSONArray();
        long now=System.currentTimeMillis();
        List<NewsItem> valid=new ArrayList<>();
        for(NewsItem n:out)if(n.at>0 && n.at<=now+300000L && now-n.at<=NewsFeedParser.RECENT_MS)valid.add(n);
        out=valid;
        freshNewsOnScreen.clear();freshNewsOnScreen.addAll(out);
        for(NewsItem item:out){
            try{currentNewsForSathi.put(new JSONObject().put("title",item.title).put("source",item.source));}
            catch(Exception ignored){}
        }
        if(out.isEmpty()){
            if(!newsShowingKnowledge)showNewsKnowledgeFallback(false);
            return;
        }
        newsShowingKnowledge=false;
        newsKnowledgeDisconnected=false;
        main.removeCallbacks(newsKnowledgeTick);
        newsKnowledgeCategory=null;newsKnowledgeText=null;
        newsList.removeAllViews();
        newsTitle.setText(t("📰 नेपालका ताजा समाचार","📰 Fresh Nepal news"));
        newsSub.setText(t("RONB • Radio Nepal • News24 · ३० मिनेटभित्रका समाचार मात्र",
                          "RONB • Radio Nepal • News24 · published within 30 minutes"));
        for(NewsItem n:out){
            LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);
            c.setPadding(dp(12),dp(11),dp(12),dp(11));
            c.setBackground(round(Color.rgb(248,252,254),17,Color.rgb(216,234,243),1));
            TextView title=text(n.title,15,true,Color.rgb(16,39,70));
            String age=n.at>0?(english?(Math.max(0,(System.currentTimeMillis()-n.at)/60000)+" min ago"):
                 (Math.max(0,(System.currentTimeMillis()-n.at)/60000)+" मिनेटअघि"))
                 :t("प्रकाशन समय पुष्टि भएको छैन","Publication time not verified");
            TextView meta=text(n.source+" • "+age,11,false,Color.rgb(102,131,153));
            TextView open=text(t("मूल समाचार खोल्नुहोस् ↗","Read original article ↗"),12,true,Color.rgb(20,119,184));
            open.setPadding(0,dp(5),0,0);
            open.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(n.url)));}catch(Exception ignored){}});
            c.addView(title);c.addView(meta);c.addView(open);
            newsList.addView(c,lp(-1,-2,0,0,0,dp(8)));
        }
    }

    private void showNewsKnowledgeFallback(boolean disconnected){
        if(newsList==null)return;
        freshNewsOnScreen.clear();
        currentNewsForSathi=new JSONArray();
        newsShowingKnowledge=true;
        newsKnowledgeDisconnected=disconnected;
        newsTitle.setText(t("📚 ज्ञानका कुरा","📚 Knowledge for Life"));
        newsSub.setText(disconnected?
            t("समाचार स्रोत जोडिएन • नयाँ खबर आएपछि आफैँ देखिन्छ","News feed unavailable • Fresh stories return automatically"):
            t("३० मिनेटभित्र नयाँ समाचार छैन • जीवनोपयोगी ज्ञान",
              "No news published in the last 30 minutes • Life lessons"));
        newsList.removeAllViews();
        LinearLayout panel=new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(15),dp(14),dp(15),dp(16));
        panel.setBackground(round(Color.rgb(255,251,241),18,Color.rgb(230,207,169),1));
        newsKnowledgeCategory=text("",12,true,Color.rgb(170,123,62));
        newsKnowledgeText=text("",15,false,Color.rgb(52,59,73));
        newsKnowledgeText.setMaxLines(5);
        newsKnowledgeText.setEllipsize(android.text.TextUtils.TruncateAt.END);
        panel.addView(newsKnowledgeCategory);
        panel.addView(newsKnowledgeText,lp(-1,-2,0,dp(8),0,0));
        newsList.addView(panel);
        showNextNewsKnowledge();
        main.removeCallbacks(newsKnowledgeTick);
        main.postDelayed(newsKnowledgeTick,FloodSafeRemoteConfig.knowledgeRotateMillis());
    }
    private void showNextNewsKnowledge(){
        if(newsKnowledgeCategory==null||newsKnowledgeText==null||GyanKnowledge.ITEMS.isEmpty())return;
        GyanKnowledge.Entry entry=FloodSafeRemoteConfig.newsLessonAt(newsKnowledgeIndex);
        newsKnowledgeIndex+=7;
        newsKnowledgeCategory.setText("✦ "+GyanKnowledge.categoryName(entry.category,english)+" · "+entry.title(english));
        newsKnowledgeText.setText(entry.body(english));
    }

    private void showPrivacy(){new AlertDialog.Builder(this).setTitle(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety")).setMessage(t("FloodSafe ले location स्थानीय मौसम र 2 km verified river warning मिलाउन प्रयोग गर्छ। Background location user-enabled monitoring का लागि मात्र हो। Microphone SATHI voice का लागि मात्र प्रयोग हुन्छ। FCM notification delivery का लागि device token प्रयोग हुन सक्छ। Force stop पछि Android ले background काम रोक्न सक्छ।","FloodSafe uses location for local weather and verified river warnings within 2 km. Background location is used only for user-enabled monitoring. Microphone is used for SATHI voice. FCM may process a device token for notification delivery. Android can stop background work after an explicit Force stop.")).setPositiveButton("OK",null).show();}

    private void showSathiDialog(String initial){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(14),dp(8),dp(14),0);
        ScrollView messages=new ScrollView(this);messages.setFillViewport(false);
        TextView history=text(t("SATHI · नदी/मौसम/चेतावनीसँगै गीता, जीवन, विज्ञान र बाढी सुरक्षाको ज्ञान पनि सोध्नुहोस्।","SATHI · Ask about river gauges, warnings, Gita, life skills, science or flood safety."),14,false,Color.rgb(30,52,72));
        // Text selection previously grabbed focus and kept the old response in view.
        history.setFocusable(false);
        messages.setSmoothScrollingEnabled(true);
        messages.addView(history);
        history.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{
            if(b-t!=ob-ot)scrollSathiToLatest(messages,history);
        });
        messages.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{
            // Keep the newest reply visible after the software keyboard resizes the dialog.
            if(b-t!=ob-ot)scrollSathiToLatest(messages,history);
        });
        box.addView(messages,lp(-1,Math.min(dp(300),getResources().getDisplayMetrics().heightPixels/3),0,0,0,dp(8)));
        EditText question=new EditText(this);question.setSingleLine(true);
        question.setTextSize(15);question.setHint(t("यहाँ प्रश्न लेख्नुहोस्…","Type your question…"));
        box.addView(question,lp(-1,dp(54),0,0,0,dp(5)));
        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
        Button send=smallButton(t("पठाउनुहोस् ↗","Send ↗"));
        Button mic=smallButton(t("🎙️ बोल्नुहोस्","🎙️ Voice"));
        actions.addView(send,new LinearLayout.LayoutParams(0,dp(48),1));
        actions.addView(mic,new LinearLayout.LayoutParams(0,dp(48),1));
        box.addView(actions);
        final String[] lastSubject={""};
        final int[] lessonStep={0};
        Runnable sendQuestion=()->{
            String q=question.getText().toString().trim();if(q.isEmpty())return;
            String normalized=q.toLowerCase(Locale.ROOT);
            boolean followUp=q.length()<50&&(normalized.contains("त्यस")||normalized.contains("अझ")||normalized.contains("अरू")
                ||normalized.contains("more")||normalized.contains("next")||normalized.contains("another")
                ||normalized.contains("explain")||normalized.contains("further")||normalized.contains("aru")
                ||normalized.contains("अर्को")||normalized.contains("फेरि"));
            String effective=followUp&&!lastSubject[0].isEmpty()?lastSubject[0]:q;
            if(!followUp){
                if(q.equalsIgnoreCase(lastSubject[0]))lessonStep[0]++;
                else if(GyanKnowledge.isKnowledgeQuestion(q))lessonStep[0]=0;
                else lessonStep[0]=0;
                lastSubject[0]=q;
            } else if(!lastSubject[0].isEmpty())lessonStep[0]++;
            String a=answerSathi(effective,lessonStep[0]);
            String old=history.getText().toString(),next=old+"\n\n👤 "+q+"\n🤖 SATHI: "+a;
            history.setText(next.length()>13000?next.substring(next.length()-12000):next);
            question.setText("");
            scrollSathiToLatest(messages,history);
        };
        send.setOnClickListener(v->sendQuestion.run());
        mic.setOnClickListener(v->startVoice(history,messages));
        LinearLayout topics=new LinearLayout(this);topics.setOrientation(LinearLayout.HORIZONTAL);
        String[] prompts={t("गीता जीवन ज्ञान","Gita life lesson"),t("बाढीमा के गर्ने","Flood safety"),t("नदीको अवस्था","River status")};
        for(String prompt:prompts){Button quick=smallButton(prompt);quick.setTextSize(10);
           LinearLayout.LayoutParams qp=new LinearLayout.LayoutParams(0,dp(47),1f);qp.setMargins(dp(2),dp(7),dp(2),0);
           topics.addView(quick,qp);quick.setOnClickListener(v->{question.setText(prompt);sendQuestion.run();});}
        box.addView(topics);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("🤖 SATHI · Chat + Voice")
            .setView(box).setPositiveButton(t("बन्द","Close"),null).create();
        dialog.getWindow();
        dialog.show();
        dialog.getWindow().setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        // A lower fixed maximum chat height leaves space for editor and reply on short phones.
        scrollSathiToLatest(messages,history);
        if(initial!=null&&!initial.trim().isEmpty()){
            String a=answerSathi(initial);
            history.append("\n\n👤 "+initial+"\n🤖 SATHI: "+a);
            scrollSathiToLatest(messages,history);
        }
    }
    private void scrollSathiToLatest(ScrollView messages,TextView history){
        if(messages==null||history==null)return;
        messages.post(()->{
            int bottom=Math.max(0,history.getBottom()+messages.getPaddingBottom()-messages.getHeight());
            messages.scrollTo(0,bottom);
            // Re-apply when Android finishes measuring after keyboard/IME animation.
            messages.postDelayed(()->{
                if(messages.isAttachedToWindow()){
                    int currentBottom=Math.max(0,history.getBottom()+messages.getPaddingBottom()-messages.getHeight());
                    messages.scrollTo(0,currentBottom);
                }
            },90L);
        });
    }
    private void startVoice(TextView out){startVoice(out,null);}
    private void startVoice(TextView out,ScrollView chatScroll){if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},REQ_MIC);return;}if(!SpeechRecognizer.isRecognitionAvailable(this)){out.setText(t("यो फोनमा voice recognition उपलब्ध छैन।","Voice recognition is unavailable on this phone."));return;}if(speech!=null)try{speech.destroy();}catch(Exception ignored){}speech=SpeechRecognizer.createSpeechRecognizer(this);speech.setRecognitionListener(new RecognitionListener(){public void onReadyForSpeech(Bundle b){out.append("\n"+t("🎙 सुन्दैछु…","🎙 Listening…"));}public void onBeginningOfSpeech(){}public void onRmsChanged(float x){}public void onBufferReceived(byte[]b){}public void onEndOfSpeech(){}public void onError(int e){out.append("\n"+t("आवाज बुझिएन। फेरि प्रयास गर्नुहोस्।","Could not understand. Try again."));}public void onPartialResults(Bundle b){}public void onEvent(int t,Bundle b){}public void onResults(Bundle b){ArrayList<String> r=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);String q=r==null||r.isEmpty()?"":r.get(0);String a=answerSathi(q);out.append("\n\n👤 "+q+"\n🤖 SATHI: "+a);if(chatScroll!=null)scrollSathiToLatest(chatScroll,out);speak(a);}});speech.startListening(new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,english?"en-GB":"ne-NP").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,5));}
    private String answerSathi(String q){return answerSathi(q,0);}
    private String answerSathi(String q,int lessonOffset){
        JSONArray rs=new JSONArray();
        synchronized(stations){
            for(RiverStation s:stations){
                JSONObject j=new JSONObject();
                try{j.put("name",s.name);j.put("district",s.district);j.put("stage",s.stage);
                    if(Double.isFinite(s.level))j.put("level",s.level);
                    j.put("fresh",s.fresh);j.put("observedAt",s.at);
                    rs.put(j);}catch(Exception ignored){}
            }
        }
        return SathiKnowledge.answer(q,english,rs,currentGovernmentNotices,districtWeather,
            currentNewsForSathi,currentWeather,isNepal(lat,lon),lessonOffset);
    }
    private void consumeSathiIntent(Intent i){if(i==null)return;String q=i.getStringExtra(SathiWakeService.EXTRA_QUERY);if(q!=null&&!q.trim().isEmpty()){showSathiDialog(q.trim());i.removeExtra(SathiWakeService.EXTRA_QUERY);}}

    private void enableMonitoring(){getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit().putBoolean("enabled",true).apply();Constraints c=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();WorkManager wm=WorkManager.getInstance(getApplicationContext());wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RainAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());wm.enqueueUniqueWork("floodsafe-weather-on-open",androidx.work.ExistingWorkPolicy.REPLACE,new androidx.work.OneTimeWorkRequest.Builder(RainAlertWorker.class).setConstraints(c).build());wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RiverAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());wm.enqueueUniquePeriodicWork("floodsafe-government-bulletins",ExistingPeriodicWorkPolicy.KEEP,new PeriodicWorkRequest.Builder(GovernmentWarningWorker.class,30,TimeUnit.MINUTES).setConstraints(c).build());FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},REQ_NOTIFY);}

    private final Runnable clockTick=new Runnable(){@Override public void run(){try{java.time.ZonedDateTime z=java.time.ZonedDateTime.now(java.time.ZoneId.of("Asia/Kathmandu"));clock.setText(String.format(Locale.US,"%02d:%02d:%02d NPT",z.getHour(),z.getMinute(),z.getSecond()));}catch(Exception ignored){}long now=System.currentTimeMillis();
        if(governmentList!=null&&now-lastGovernmentExpiryCheckAt>=60_000L){
            lastGovernmentExpiryCheckAt=now;
            renderGovernment();
        }
        main.postDelayed(this,1000);}};
    private void initTts(){tts=new TextToSpeech(getApplicationContext(),s->{if(s==TextToSpeech.SUCCESS&&tts!=null){int r=tts.setLanguage(Locale.forLanguageTag("ne-NP"));if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(new Locale("ne"));tts.setSpeechRate(.92f);}});}private void speak(String s){if(tts!=null&&s!=null&&!s.isEmpty())tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"sathi-native-full");}
    @Override public void onRequestPermissionsResult(int code,String[]p,int[]g){super.onRequestPermissionsResult(code,p,g);if(code==REQ_LOCATION&&hasLocationPermission())requestLocation();else if(code==REQ_MIC&&checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)showSathiDialog(null);}
    private boolean hasLocationPermission(){return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED||checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
    private synchronized NepalRiverBoundary nepalDistrictBorder(){
        if(nepalDistrictBorder!=null)return nepalDistrictBorder;
        try{nepalDistrictBorder=new NepalRiverBoundary(assetJson("floodsafe-nepal/v24/nepal-districts.geojson").toString());}
        catch(Exception unavailable){try{nepalDistrictBorder=new NepalRiverBoundary(assetJson("floodsafe-nepal/v24/nepal-districts.json").toString());}catch(Exception ignored){}}
        return nepalDistrictBorder;
    }
    private static boolean isNepal(double a,double o){return Double.isFinite(a)&&Double.isFinite(o)&&a>=26.2&&a<=30.5&&o>=80&&o<=88.35;}
    private double distanceKm(double a,double o){if(!isNepal(lat,lon))return Double.NaN;double R=6371,dLat=Math.toRadians(a-lat),dLon=Math.toRadians(o-lon),q=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(Math.toRadians(lat))*Math.cos(Math.toRadians(a))*Math.sin(dLon/2)*Math.sin(dLon/2);return 2*R*Math.asin(Math.sqrt(q));}
    private JSONObject assetJson(String path)throws Exception{try(InputStream in=getAssets().open(path);BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){StringBuilder b=new StringBuilder();String line;while((line=r.readLine())!=null)b.append(line);return new JSONObject(b.toString());}}
    private static JSONObject getJson(String u)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(15000);c.setReadTimeout(22000);c.setUseCaches(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store");int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}finally{c.disconnect();}return new JSONObject(b.toString());}
    private static JSONArray rows(JSONObject j){JSONArray a=j.optJSONArray("results");if(a==null)a=j.optJSONArray("data");return a==null?new JSONArray():a;}
    private static String str(JSONObject o,String...k){for(String x:k){if(o.has(x)&&!o.isNull(x)){String s=String.valueOf(o.opt(x)).trim();if(!s.isEmpty()&&!"null".equalsIgnoreCase(s))return s;}}return"";}
    private static double num(JSONObject o,String...k){for(String x:k){if(!o.has(x)||o.isNull(x))continue;Object v=o.opt(x);if(v instanceof Number){double n=((Number)v).doubleValue();if(Double.isFinite(n))return n;}try{double n=Double.parseDouble(String.valueOf(v).trim());if(Double.isFinite(n))return n;}catch(Exception ignored){}}return Double.NaN;}
    private static double numOr(JSONObject o,String...k){double n=num(o,k);return Double.isFinite(n)?n:0;}
    private static long parseTime(String s){if(s==null||s.trim().isEmpty())return-1;String v=s.trim();try{long n=Long.parseLong(v);return n<10_000_000_000L?n*1000:n;}catch(Exception ignored){}try{return Instant.parse(v).toEpochMilli();}catch(Exception ignored){}try{return OffsetDateTime.parse(v).toInstant().toEpochMilli();}catch(Exception ignored){}try{return ZonedDateTime.parse(v).toInstant().toEpochMilli();}catch(Exception ignored){}try{return LocalDateTime.parse(v.replace(' ','T'),DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){return-1;}}
    private static boolean isDisaster(String s){return s.matches(".*(flood|flash flood|landslide|earthquake|avalanche|glacial|glof|fire|wildfire|lightning|storm|windstorm|heavy rain|inundation|बाढी|पहिरो|भूकम्प|हिमपहिरो|डढेलो|आगलागी|चट्याङ|डुबान|अविरल वर्षा).*" )&&!s.matches(".*(road accident|vehicle accident|traffic accident|दुर्घटना|राजनीति|खेलकुद|निर्वाचन).*" );}
    private static int stageColor(String s){switch(s){case"danger":return Color.rgb(214,47,67);case"warning":return Color.rgb(239,125,36);case"alert":return Color.rgb(224,165,42);case"normal":return Color.rgb(31,164,116);default:return Color.rgb(113,139,155);}}private static int stageBg(String s){switch(s){case"danger":return Color.rgb(255,240,242);case"warning":return Color.rgb(255,247,235);case"alert":return Color.rgb(255,248,233);case"normal":return Color.rgb(233,255,245);default:return Color.rgb(243,249,252);}}private static String stageDot(String s){switch(s){case"danger":return"🔴";case"warning":return"🟠";case"alert":return"🟡";case"normal":return"🟢";default:return"⚪";}}private String stageName(String s){switch(s){case"danger":return t("खतरा","DANGER");case"warning":return t("चेतावनी","WARNING");case"alert":return t("निगरानी","ALERT");case"normal":return t("सामान्य","NORMAL");default:return t("पुरानो/अज्ञात","STALE/UNKNOWN");}}
    private LinearLayout card(){LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(17),dp(16),dp(17),dp(16));c.setBackground(round(Color.argb(248,255,255,255),25,Color.rgb(207,229,239),1));c.setElevation(dp(3));c.setLayoutParams(lp(-1,-2,0,0,0,dp(14)));return c;}
    private TextView text(String s,float sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);v.setGravity(Gravity.START);v.setLineSpacing(0,1.08f);if(bold)v.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));return v;}
    private TextView badge(String s,int bg,int fg){TextView v=text(s,10,true,fg);v.setPadding(dp(9),dp(6),dp(9),dp(6));v.setGravity(Gravity.CENTER);v.setBackground(round(bg,99,Color.TRANSPARENT,0));return v;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(Color.rgb(18,48,75));b.setTextSize(15);b.setTypeface(Typeface.DEFAULT_BOLD);b.setBackground(round(Color.WHITE,18,Color.rgb(207,228,239),1));return b;}
    private Button smallButton(String s){Button b=button(s);b.setTextSize(12);return b;}private Button navButton(String s){Button b=button(s);b.setTextSize(11);b.setBackground(round(Color.rgb(234,246,252),16,Color.TRANSPARENT,0));return b;}
    private TextView empty(String s){TextView v=text(s,12,false,Color.rgb(102,131,153));v.setPadding(dp(14),dp(13),dp(14),dp(13));v.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));return v;}
    private GradientDrawable round(int color,int radius,int stroke,int sw){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));if(sw>0)g.setStroke(dp(sw),stroke);return g;}
    private LinearLayout.LayoutParams lp(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}private LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-1,1f);p.setMargins(dp(2),0,dp(2),0);return p;}private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private static final class RiverStation{final String name,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;}}
    private static final class NewsItem{final String title,source,url;final long at;NewsItem(String t,String s,String u,long a){title=t;source=s;url=u;at=a;}}
    @Override protected void onPause(){main.removeCallbacks(governmentAutoRefresh);main.removeCallbacks(newsAutoRefreshTick);main.removeCallbacks(newsKnowledgeTick);if(gyanRotator!=null)gyanRotator.animate().cancel();if(map!=null)map.onHostPause();super.onPause();}
    @Override protected void onResume(){super.onResume();if(map!=null)map.onHostResume();
        main.post(mapVisibilityTick);
        main.removeCallbacks(governmentAutoRefresh);main.postDelayed(governmentAutoRefresh,GOVERNMENT_FOREGROUND_REFRESH_MS);
        if(newsList!=null&&System.currentTimeMillis()-newsLastFetchedAt>=FloodSafeRemoteConfig.newsPollMillis())refreshNews();
        FloodSafeRemoteConfig.refreshAsync(getApplicationContext(),onOtaContentChanged);
        if(playUpdates!=null)playUpdates.check();
        main.removeCallbacks(newsAutoRefreshTick);main.postDelayed(newsAutoRefreshTick,20000L);
        if(newsShowingKnowledge){main.removeCallbacks(newsKnowledgeTick);main.postDelayed(newsKnowledgeTick,FloodSafeRemoteConfig.knowledgeRotateMillis());}
    }
    @Override protected void onDestroy(){if(playUpdates!=null)playUpdates.close();main.removeCallbacksAndMessages(null);if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}if(tts!=null){tts.stop();tts.shutdown();}io.shutdownNow();super.onDestroy();}
}
