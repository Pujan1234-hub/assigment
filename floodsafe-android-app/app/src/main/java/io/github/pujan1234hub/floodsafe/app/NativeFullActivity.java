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

/** V0899_STALE_CURRENT_SEMANTICS — Full native Android FloodSafe UI. No WebView is used. */
public final class NativeFullActivity extends Activity implements LocationListener {
    private static final int REQ_LOCATION=801, REQ_MIC=802, REQ_NOTIFY=803;
    private static final String PREFS="floodsafe-native-full";
    private static final String KEY_LAT="lat",KEY_LON="lon",KEY_AT="at",KEY_LANG="lang_en";
    private static final long RIVER_FRESH_MS=10L*60L*1000L;
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
    private double lat=Double.NaN,lon=Double.NaN;
    private long locAt;
    private FrameLayout root;
    private ScrollView scroll;
    private LinearLayout content,nearList,nationalList,newsList,humanCard,alarmBanner;
    private TextView brandSub,langBtn,place,clock,temp,weatherText,weatherSupport,rainTiming,rain,humidity,wind;
    private TextView alarmTitle,alarmText,riskBadge,riskValue,riskText,stationCount,warningCount,dangerCount,feedFresh;
    private TextView nearTitle,nearSub,nationalTitle,nationalSub,nationalFresh,humanFresh,humanDeaths,humanInjured,humanMissing,humanRescued,humanDetail;
    private TextView newsTitle,newsSub,privacyTitle,privacySub,mapTitle,mapSub,mapHint;
    private FloodSafeNativeMapView map;
    private View homeAnchor,mapAnchor,newsAnchor;
    private String currentWeather="";
    private boolean showAllStations=false;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(223,242,251));
        getWindow().setNavigationBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        SharedPreferences p=getSharedPreferences(PREFS,MODE_PRIVATE);english=p.getBoolean(KEY_LANG,false);
        lat=Double.longBitsToDouble(p.getLong(KEY_LAT,Double.doubleToRawLongBits(Double.NaN)));
        lon=Double.longBitsToDouble(p.getLong(KEY_LON,Double.doubleToRawLongBits(Double.NaN)));
        locAt=p.getLong(KEY_AT,0L);
        lm=getSystemService(LocationManager.class);
        initTts();
        DhmRainMirror.ensureStarted(this);
        setContentView(buildScreen());
        enableMonitoring();
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
        homeAnchor=header(); content.addView(homeAnchor);
        content.addView(hero(),lp(-1,-2,0,0,0,dp(12)));
        Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->requestLocation()); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12)));
        TextView outside=text("",13,true,Color.rgb(40,85,111)); outside.setId(android.R.id.hint); outside.setPadding(dp(15),dp(13),dp(15),dp(13)); outside.setBackground(round(Color.rgb(239,249,255),22,Color.rgb(159,205,232),1)); content.addView(outside,lp(-1,-2,0,0,0,dp(10)));
        alarmBanner=new LinearLayout(this);alarmBanner.setOrientation(LinearLayout.VERTICAL);alarmBanner.setPadding(dp(16),dp(14),dp(16),dp(14));alarmBanner.setBackground(round(Color.rgb(255,235,239),22,Color.rgb(239,138,152),2));
        alarmTitle=text(t("⚠️ नदी चेतावनी","⚠️ River warning"),22,true,Color.rgb(146,34,56));alarmText=text("",14,true,Color.rgb(146,34,56));alarmBanner.addView(alarmTitle);alarmBanner.addView(alarmText);alarmBanner.setVisibility(View.GONE);content.addView(alarmBanner,lp(-1,-2,0,0,0,dp(12)));
        mapAnchor=mapCard();content.addView(mapAnchor);
        content.addView(riskCard());
        content.addView(nearCard());
        content.addView(nationalCard());
        humanCard=humanCard();content.addView(humanCard);
        newsAnchor=newsCard();content.addView(newsAnchor);
        content.addView(privacyCard());
        root.addView(bottomNav(),bottomParams());
        Button sathi=button("🤖 SATHI");sathi.setTextSize(13);sathi.setOnClickListener(v->showSathiDialog(null));FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(dp(104),dp(48),Gravity.END|Gravity.BOTTOM);fp.setMargins(0,0,dp(18),dp(82));root.addView(sathi,fp);
        applyLanguage();return root;
    }

    private View header(){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,0,0,dp(12));
        ImageView icon=new ImageView(this);icon.setImageResource(R.mipmap.ic_launcher);GradientDrawable ib=round(Color.WHITE,16,Color.rgb(209,229,239),1);icon.setBackground(ib);icon.setPadding(dp(3),dp(3),dp(3),dp(3));row.addView(icon,new LinearLayout.LayoutParams(dp(52),dp(52)));
        LinearLayout brand=new LinearLayout(this);brand.setOrientation(LinearLayout.VERTICAL);brand.setPadding(dp(10),0,0,0);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,-2,1f);row.addView(brand,bp);
        TextView title=text("FloodSafe Nepal",25,true,Color.rgb(16,39,70));brand.addView(title);brandSub=text("",12,true,Color.rgb(82,116,139));brand.addView(brandSub);
        langBtn=text("",12,true,Color.rgb(18,48,76));langBtn.setGravity(Gravity.CENTER);langBtn.setPadding(dp(12),dp(10),dp(12),dp(10));langBtn.setBackground(round(Color.WHITE,99,Color.rgb(209,229,239),1));langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();refreshRiverUi();});row.addView(langBtn);
        return row;
    }

    private View hero(){
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);card.setPadding(dp(20),dp(18),dp(20),dp(20));GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{Color.rgb(44,143,199),Color.rgb(30,121,173),Color.rgb(23,108,125)});g.setCornerRadius(dp(31));card.setBackground(g);
        LinearLayout stripe=new LinearLayout(this);stripe.setOrientation(LinearLayout.HORIZONTAL);View b=new View(this),w=new View(this),r=new View(this);b.setBackgroundColor(Color.rgb(0,56,147));w.setBackgroundColor(Color.WHITE);r.setBackgroundColor(Color.rgb(220,20,60));stripe.addView(b,new LinearLayout.LayoutParams(0,dp(6),45));stripe.addView(w,new LinearLayout.LayoutParams(0,dp(6),10));stripe.addView(r,new LinearLayout.LayoutParams(0,dp(6),45));card.addView(stripe,lp(-1,dp(6),0,0,0,dp(18)));
        LinearLayout top=new LinearLayout(this);top.setOrientation(LinearLayout.HORIZONTAL);place=text("",14,true,Color.WHITE);clock=text("",11,true,Color.WHITE);top.addView(place,new LinearLayout.LayoutParams(0,-2,1f));top.addView(clock);card.addView(top);
        temp=text("—°",72,false,Color.WHITE);card.addView(temp,lp(-1,-2,0,dp(20),0,0));weatherText=text("",27,true,Color.WHITE);card.addView(weatherText);weatherSupport=text("",13,false,Color.rgb(232,247,255));card.addView(weatherSupport,lp(-1,-2,0,dp(6),0,0));
        rainTiming=text("",12,true,Color.WHITE);rainTiming.setPadding(dp(10),dp(9),dp(10),dp(9));rainTiming.setBackground(round(Color.argb(55,7,61,95),14,Color.argb(64,255,255,255),1));card.addView(rainTiming,lp(-1,-2,0,dp(11),0,0));
        LinearLayout grid=new LinearLayout(this);grid.setOrientation(LinearLayout.HORIZONTAL);grid.setPadding(0,dp(14),0,0);rain=weatherStat(grid,"—",t("वर्षा","Rain"));humidity=weatherStat(grid,"—",t("आर्द्रता","Humidity"));wind=weatherStat(grid,"—",t("हावा","Wind"));card.addView(grid);return card;
    }
    private TextView weatherStat(LinearLayout parent,String value,String label){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);TextView v=text(value,18,true,Color.WHITE);TextView l=text(label,11,true,Color.rgb(215,238,248));box.addView(v);box.addView(l);parent.addView(box,new LinearLayout.LayoutParams(0,-2,1f));return v;}

    private View mapCard(){
        LinearLayout c=card();LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);LinearLayout labels=new LinearLayout(this);labels.setOrientation(LinearLayout.VERTICAL);head.addView(labels,new LinearLayout.LayoutParams(0,-2,1));mapTitle=text("",20,true,Color.rgb(16,39,70));mapSub=text("",12,true,Color.rgb(100,130,151));labels.addView(mapTitle);labels.addView(mapSub);TextView live=badge(t("आधिकारिक","OFFICIAL"),Color.rgb(233,255,245),Color.rgb(18,128,90));head.addView(live);c.addView(head);
        LinearLayout tools=new LinearLayout(this);tools.setOrientation(LinearLayout.HORIZONTAL);Button zi=smallButton("＋ "+t("ठूलो","Zoom")),zo=smallButton("− "+t("सानो","Out")),d3=smallButton("◈ 3D"),reset=smallButton("🇳🇵 "+t("नेपाल","Nepal"));tools.addView(zi,weight());tools.addView(zo,weight());tools.addView(d3,weight());tools.addView(reset,weight());c.addView(tools,lp(-1,dp(48),0,dp(10),0,dp(8)));
        FrameLayout holder=new FrameLayout(this);map=new FloodSafeNativeMapView(this, stationObject -> { if(stationObject instanceof RiverStation) showStation((RiverStation)stationObject); });holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));mapHint=text("",11,true,Color.rgb(84,115,137));mapHint.setPadding(dp(12),dp(9),dp(12),dp(9));mapHint.setBackground(round(Color.argb(240,255,255,255),18,Color.rgb(207,226,237),1));FrameLayout.LayoutParams hp=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);hp.setMargins(dp(10),0,dp(10),dp(10));holder.addView(mapHint,hp);c.addView(holder);
        zi.setOnClickListener(v->map.zoomBy(1.25f));zo.setOnClickListener(v->map.zoomBy(.8f));reset.setOnClickListener(v->map.resetView());d3.setOnClickListener(v->{map.toggleTerrain();d3.setText(map.terrain?"▱ 2D":"◈ 3D");});return c;
    }

    private View riskCard(){LinearLayout c=card();LinearLayout h=new LinearLayout(this);h.setOrientation(LinearLayout.HORIZONTAL);LinearLayout left=new LinearLayout(this);left.setOrientation(LinearLayout.VERTICAL);h.addView(left,new LinearLayout.LayoutParams(0,-2,1));TextView title=text(t("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम","🛡️ Flood risk near me"),20,true,Color.rgb(16,39,70));left.addView(title);feedFresh=text("",12,true,Color.rgb(100,130,151));left.addView(feedFresh);riskBadge=badge("—",Color.rgb(237,247,252),Color.rgb(23,116,174));h.addView(riskBadge);c.addView(h);riskValue=text("—",34,true,Color.rgb(85,117,139));c.addView(riskValue,lp(-1,-2,0,dp(12),0,0));riskText=text("",13,false,Color.rgb(95,125,146));c.addView(riskText);LinearLayout stats=new LinearLayout(this);stats.setOrientation(LinearLayout.HORIZONTAL);stationCount=stat(stats,"—",t("सबै official स्टेशन","Official stations"));warningCount=stat(stats,"—",t("चेतावनी","Warning"));dangerCount=stat(stats,"—",t("खतरा","Danger"));c.addView(stats,lp(-1,-2,0,dp(12),0,0));return c;}
    private TextView stat(LinearLayout p,String n,String l){LinearLayout b=new LinearLayout(this);b.setOrientation(LinearLayout.VERTICAL);b.setGravity(Gravity.CENTER);b.setPadding(dp(5),dp(9),dp(5),dp(9));b.setBackground(round(Color.rgb(243,249,252),16,Color.rgb(218,234,242),1));TextView v=text(n,21,true,Color.rgb(16,39,70));TextView s=text(l,9,true,Color.rgb(103,132,154));s.setGravity(Gravity.CENTER);b.addView(v);b.addView(s);LinearLayout.LayoutParams q=new LinearLayout.LayoutParams(0,-2,1);q.setMargins(dp(3),0,dp(3),0);p.addView(b,q);return v;}

    private View nearCard(){LinearLayout c=card();nearTitle=text("",20,true,Color.rgb(16,39,70));nearSub=text("",12,true,Color.rgb(100,130,151));c.addView(nearTitle);c.addView(nearSub);nearList=new LinearLayout(this);nearList.setOrientation(LinearLayout.VERTICAL);c.addView(nearList,lp(-1,-2,0,dp(10),0,0));return c;}
    private View nationalCard(){LinearLayout c=card();nationalTitle=text("",20,true,Color.rgb(16,39,70));nationalSub=text("",12,true,Color.rgb(100,130,151));nationalFresh=text("",12,true,Color.rgb(100,130,151));c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);c.addView(nationalList,lp(-1,-2,0,dp(8),0,0));Button more=smallButton(t("सबै स्टेशन देखाउनुहोस्","Show all stations"));more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम देखाउनुहोस्","Show less"):t("सबै स्टेशन देखाउनुहोस्","Show all stations"));refreshRiverUi();});c.addView(more);return c;}
    private LinearLayout humanCard(){LinearLayout c=card();TextView t=text("🧑‍🤝‍🧑 "+t("Human Status — पछिल्लो विपद्","Human Status — latest disaster"),20,true,Color.rgb(16,39,70));humanFresh=text("",12,true,Color.rgb(100,130,151));c.addView(t);c.addView(humanFresh);LinearLayout stats=new LinearLayout(this);stats.setOrientation(LinearLayout.HORIZONTAL);humanDeaths=stat(stats,"—",t("मृतक","Deaths"));humanInjured=stat(stats,"—",t("घाइते","Injured"));humanMissing=stat(stats,"—",t("बेपत्ता","Missing"));humanRescued=stat(stats,"—",t("उद्धार","Rescued"));c.addView(stats,lp(-1,-2,0,dp(10),0,0));humanDetail=text("",12,false,Color.rgb(95,125,146));c.addView(humanDetail);c.setVisibility(View.GONE);return c;}
    private View newsCard(){LinearLayout c=card();newsTitle=text("",20,true,Color.rgb(16,39,70));newsSub=text("RONB Post • Radio Nepal • News24 Nepal",12,true,Color.rgb(100,130,151));c.addView(newsTitle);c.addView(newsSub);newsList=new LinearLayout(this);newsList.setOrientation(LinearLayout.VERTICAL);c.addView(newsList,lp(-1,-2,0,dp(8),0,0));return c;}
    private View privacyCard(){LinearLayout c=card();privacyTitle=text("",20,true,Color.rgb(16,39,70));privacySub=text("",12,true,Color.rgb(100,130,151));c.addView(privacyTitle);c.addView(privacySub);Button b=smallButton(t("गोपनीयता नीति हेर्नुहोस् →","View privacy policy →"));b.setOnClickListener(v->showPrivacy());c.addView(b,lp(-1,dp(48),0,dp(10),0,0));return c;}

    private View bottomNav(){LinearLayout nav=new LinearLayout(this);nav.setOrientation(LinearLayout.HORIZONTAL);nav.setPadding(dp(8),dp(7),dp(8),dp(7));nav.setBackground(round(Color.argb(246,255,255,255),24,Color.rgb(208,227,237),1));Button h=navButton("⌂\n"+t("गृह","Home")),m=navButton("🗺️\n"+t("नदी नक्सा","River map")),n=navButton("🔔\n"+t("समाचार","News"));nav.addView(h,weight());nav.addView(m,weight());nav.addView(n,weight());h.setOnClickListener(v->smoothTo(homeAnchor));m.setOnClickListener(v->smoothTo(mapAnchor));n.setOnClickListener(v->smoothTo(newsAnchor));return nav;}
    private FrameLayout.LayoutParams bottomParams(){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(-1,dp(72),Gravity.BOTTOM);p.setMargins(dp(9),0,dp(9),dp(9));return p;}
    private void smoothTo(View v){if(v==null)return;scroll.post(()->scroll.smoothScrollTo(0,Math.max(0,v.getTop()-dp(8))));}

    private void applyLanguage(){brandSub.setText(t("नेपाल • नदी • बाढी • चौबीसै घण्टा चेतावनी","Nepal • rivers • floods • 24/7 alerts"));langBtn.setText(t("अङ्ग्रेजी","नेपाली"));weatherText.setText(currentWeather.isEmpty()?t("नेपालको निगरानी स्थान छान्नुहोस्","Choose a monitoring location"):currentWeather);weatherSupport.setText(t("नेपालको मौसम + official BIPAD/DHM realtime नदी status","Local weather + official BIPAD/DHM river status"));if(!Double.isFinite(lat)){place.setText(t("📍 नेपालमा निगरानी स्थान छान्नुहोस्","📍 Choose a monitoring location"));rainTiming.setText(t("हालको स्थान लिएपछि आगामी वर्षा timing देखाइन्छ।","Rain timing appears after location is available."));}mapTitle.setText(t("🇳🇵 BIPAD आधिकारिक नदी नक्सा","🇳🇵 BIPAD official river map"));mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, चेतावनी र official time हेर्नुहोस्।","Tap a river station for level, warning and official time."));mapHint.setText(t("🇳🇵 official नदी स्टेशन र नदी geometry","🇳🇵 official stations and river geometry"));nearTitle.setText(t("🌊 नजिकका नदी स्टेशन","🌊 Nearby river stations"));nearSub.setText(t("तपाईंको स्थान नजिकको official नदी अवस्था","Official river status near your location"));nationalTitle.setText(t("🌊 ७७ जिल्ला — सबै official नदी स्टेशन","🌊 77 districts — official river stations"));nationalSub.setText(t("Latest official reading; stale data लाई live खतरा मानिँदैन।","Latest official readings; stale data is not treated as a live threat."));newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));privacyTitle.setText(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety"));privacySub.setText(t("Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used."));updateOutsideNotice();}
    private String t(String ne,String en){return english?en:ne;}

    private void refreshAll(){restoreLocation();refreshRivers();refreshHuman();refreshNews();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}
    private void restoreLocation(){if(Double.isFinite(lat)&&Double.isFinite(lon)){place.setText(isNepal(lat,lon)?t("📍 पछिल्लो GPS • Nepal","📍 Last GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • weather follows this location"));updateOutsideNotice();}}
    private void updateOutsideNotice(){TextView v=root==null?null:root.findViewById(android.R.id.hint);if(v==null)return;boolean out=Double.isFinite(lat)&&Double.isFinite(lon)&&!isNepal(lat,lon);v.setVisibility(out?View.VISIBLE:View.GONE);v.setText(t("🇳🇵 FloodSafe Nepal-only monitoring\nतपाईं नेपाल बाहिर हुँदा नजिकको नदी चेतावनी पठाइँदैन। नेपालभित्र current GPS हुँदा २ km भित्रको verified Warning/Danger मात्र emergency alert आउँछ।","🇳🇵 FloodSafe Nepal-only monitoring\nOutside Nepal, nearby river warnings are not sent. In Nepal, only verified Warning/Danger within 2 km can trigger the emergency river alert."));}

    private void requestLocation(){if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}if(lm==null)return;try{Location a=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),b=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER),best=a==null?b:b==null?a:(a.getTime()>=b.getTime()?a:b);if(best!=null&&System.currentTimeMillis()-best.getTime()<24L*60*60*1000)onLocationChanged(best);if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());else if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());}catch(Exception ignored){}}
    @Override public void onLocationChanged(Location l){if(l==null)return;lat=l.getLatitude();lon=l.getLongitude();locAt=System.currentTimeMillis();getSharedPreferences(PREFS,MODE_PRIVATE).edit().putLong(KEY_LAT,Double.doubleToRawLongBits(lat)).putLong(KEY_LON,Double.doubleToRawLongBits(lon)).putLong(KEY_AT,locAt).apply();getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit().putLong("lat",Double.doubleToRawLongBits(lat)).putLong("lon",Double.doubleToRawLongBits(lon)).putLong("location_time",locAt).putLong("device_lat",Double.doubleToRawLongBits(lat)).putLong("device_lon",Double.doubleToRawLongBits(lon)).putLong("device_location_time",locAt).putBoolean("follow_device",true).putBoolean("location_stale",false).putBoolean("enabled",true).apply();place.setText(isNepal(lat,lon)?t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • local weather only"));updateOutsideNotice();reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();FloodMonitorService.startIfEnabled(this);}
    private void reverseGeocode(){io.execute(()->{try{List<android.location.Address>a=new Geocoder(this,Locale.getDefault()).getFromLocation(lat,lon,1);if(a!=null&&!a.isEmpty()){String s=a.get(0).getLocality();if(s==null)s=a.get(0).getSubAdminArea();if(s==null)s=a.get(0).getCountryName();final String label=s;if(label!=null)runOnUiThread(()->place.setText("📍 "+label));}}catch(Exception ignored){}});}

    private void fetchWeather(double a,double o){io.execute(()->{try{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),pr=c.optDouble("precipitation",0),hu=c.optDouble("relative_humidity_2m",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);String ws=pr>=.5?t("अहिले वर्षा भइरहेको छ","Rain now"):t("अहिले वर्षा छैन","No rain now");String timing=rainTiming(j);currentWeather=ws;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);});}catch(Exception e){runOnUiThread(()->weatherText.setText(t("मौसम refresh हुन सकेन","Weather refresh failed")));}});}
    private String rainTiming(JSONObject j){try{JSONObject h=j.getJSONObject("hourly");JSONArray time=h.getJSONArray("time"),pp=h.getJSONArray("precipitation_probability"),pr=h.getJSONArray("precipitation");for(int i=0;i<Math.min(time.length(),6);i++){double mm=pr.optDouble(i,0);int p=pp.optInt(i,0);if(mm>=.2||p>=55)return t("🌧️ आगामी "+Math.max(1,i+1)+" घण्टाभित्र वर्षाको सम्भावना "+p+"%","🌧️ Rain chance "+p+"% within about "+Math.max(1,i+1)+"h");}return t("☁️ आगामी केही घण्टामा उल्लेख्य वर्षा संकेत छैन","☁️ No significant rain signal in the next few hours");}catch(Exception e){return t("वर्षा timing उपलब्ध छैन","Rain timing unavailable");}}

    private void refreshRivers(){feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));io.execute(()->{try{JSONObject root=getJson(RIVER_ENDPOINT+"?_nativefull="+System.currentTimeMillis());JSONArray rows=root.optJSONArray("results");if(rows==null)rows=root.optJSONArray("data");if(rows==null)rows=new JSONArray();List<RiverStation> out=new ArrayList<>();long now=System.currentTimeMillis();for(int i=0;i<rows.length();i++){RiverStation s=parseStation(rows.optJSONObject(i),now);if(s!=null)out.add(s);}out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));synchronized(stations){stations.clear();stations.addAll(out);}runOnUiThread(this::refreshRiverUi);}catch(Exception e){runOnUiThread(()->feedFresh.setText(t("River data refresh हुन सकेन • stale लाई live भनिएको छैन","River refresh failed • stale data is not live")));}});}
    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;
        double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel"),
                warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),
                danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=parseTime(str(r,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));
        boolean fresh=at>0&&now-at<=RIVER_FRESH_MS&&at-now<=5*60_000L;
        String raw=str(r,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(fresh){
            if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE")){stage="normal";rank=3;}
        }
        String stationId=str(r,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id");
        String riverName=str(r,"river_name","riverName","river");
        String name=str(r,"station_name","stationName","title","name");
        if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";
        String district=str(r,"districtName","district_name","district");
        return new RiverStation(stationId,name,riverName,district,a,o,level,warning,danger,at,fresh,stage,rank);
    } // V0899_STALE_CURRENT_SEMANTICS

    private void refreshRiverUi(){if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}map.setStations(copy,lat,lon);int d=0,w=0,a=0,n=0,stale=0;for(RiverStation s:copy){switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}}stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));feedFresh.setText(t("Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale,"Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale));nationalFresh.setText(feedFresh.getText());updateRisk(copy);nearList.removeAllViews();List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));int nearShown=Math.min(8,near.size());for(int i=0;i<nearShown;i++)nearList.addView(stationRow(near.get(i)));if(nearShown==0)nearList.addView(empty(t("नेपालमा GPS location लिएपछि नजिकका station देखिन्छन्।","Nearby stations appear after a Nepal GPS location is available.")));nationalList.removeAllViews();int max=showAllStations?copy.size():Math.min(24,copy.size());for(int i=0;i<max;i++)nationalList.addView(stationRow(copy.get(i)));}
    private View stationRow(RiverStation s){TextView v=text(stageDot(s.stage)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(stageBg(s.stage),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
    private void updateRisk(List<RiverStation> copy){
        RiverStation nearest=null,emergencyStation=null;double nearestStationKm=Double.POSITIVE_INFINITY,emergencyRiverKm=Double.POSITIVE_INFINITY;
        for(RiverStation s:copy){
            double sd=distanceKm(s.lat,s.lon);if(Double.isFinite(sd)&&sd<nearestStationKm){nearestStationKm=sd;nearest=s;}
            if(s.fresh&&(s.stage.equals("warning")||s.stage.equals("danger"))&&map!=null&&isNepal(lat,lon)){
                double rd=map.distanceToMatchedRiverKm(s,lat,lon);
                if(Double.isFinite(rd)&&rd<=2d&&rd<emergencyRiverKm){emergencyRiverKm=rd;emergencyStation=s;}
            }
        }
        RiverStation best=emergencyStation!=null?emergencyStation:nearest;
        if(best==null){riskValue.setText("—");riskBadge.setText(t("प्रतीक्षा","WAIT"));riskText.setText(t("नेपालमा location लिएपछि नजिकको official river risk देखिन्छ।","Take a Nepal location to see nearby official river risk."));alarmBanner.setVisibility(View.GONE);return;}
        riskValue.setText(stageName(best.stage));riskBadge.setText(stageName(best.stage));
        double shownDistance=best==emergencyStation?emergencyRiverKm:nearestStationKm;
        String basis=best==emergencyStation?t(" • प्रभावित नदी geometry सम्म "," • to affected river geometry "):t(" • station सम्म "," • to station ");
        riskText.setText(best.name+basis+String.format(Locale.US,"%.1f km",shownDistance)+" • "+stationLine(best));
        int col=stageColor(best.stage);riskValue.setTextColor(col);riskBadge.setTextColor(col);
        boolean emergency=emergencyStation!=null;
        alarmBanner.setVisibility(emergency?View.VISIBLE:View.GONE);
        if(emergency){alarmTitle.setText(best.stage.equals("danger")?t("🚨 DANGER — प्रभावित नदी 2 km भित्र","🚨 DANGER — affected river within 2 km"):t("⚠️ WARNING — प्रभावित नदी 2 km भित्र","⚠️ WARNING — affected river within 2 km"));alarmText.setText(best.name+" • river geometry "+String.format(Locale.US,"%.1f km",emergencyRiverKm)+" • "+stationLine(best));}
    } // V0899_FOREGROUND_ALERT_USES_RIVER_GEOMETRY
    private String stationLine(RiverStation s){
        long ageMs=s.at>0?Math.max(0,System.currentTimeMillis()-s.at):-1L;
        String age;
        if(ageMs<0)age=t("official time उपलब्ध छैन","official time unavailable");
        else if(ageMs<60L*60L*1000L)age=(ageMs/60000L)+" min ago";
        else if(ageMs<48L*60L*60L*1000L)age=(ageMs/(60L*60L*1000L))+" hr ago";
        else age=(ageMs/(24L*60L*60L*1000L))+" days ago";
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";
        double d=distanceKm(s.lat,s.lon);
        String freshness=s.fresh?t("हालको आधिकारिक","CURRENT official"):t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात","HISTORICAL / STALE • last known");
        return freshness+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • station %.1f km",d):"");
    }
    private void showStation(RiverStation s){
        StringBuilder b=new StringBuilder();
        b.append(s.fresh?stageDot(s.stage)+" "+stageName(s.stage):"⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading"));
        if(!s.stationId.isEmpty())b.append("\nStation ID: ").append(s.stationId);
        if(!s.riverName.isEmpty())b.append("\nRiver: ").append(s.riverName);
        b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.2f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.2f m",s.danger));
        b.append("\n").append(t("Official observation: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—");
        if(!s.fresh)b.append("\n\n").append(t("यो पुरानो/ऐतिहासिक reading warning colour वा alarm मा प्रयोग हुँदैन।","This historical/stale reading is not used for warning colours or alarms."));
        String rainDetail=DhmRainMirror.detailFor(s.name,s.district,s.lat,s.lon);
        b.append("\n\n").append(rainDetail!=null?rainDetail:t("Rainfall: सुरक्षित रूपमा match भएको fresh DHM rainfall reading उपलब्ध छैन।","Rainfall: no safely matched fresh DHM rainfall reading is available."));
        b.append("\n\nSource: BIPAD / DHM");
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton("OK",null).show();
    } // V0899_STATION_STALE_AND_RAIN_DETAIL


    private void refreshHuman(){io.execute(()->{try{JSONObject inc=getJson(BIPAD+"incident/?limit=500&ordering=-incidentOn"),loss=getJson(BIPAD+"loss-people/?limit=1000&ordering=-createdOn");JSONArray ir=rows(inc),lr=rows(loss);long cutoff=System.currentTimeMillis()-10L*24*60*60*1000;List<String> ids=new ArrayList<>();int incidents=0;for(int i=0;i<ir.length();i++){JSONObject o=ir.optJSONObject(i);if(o==null)continue;long tm=parseTime(str(o,"incidentOn","incident_on","createdOn","created_at","modifiedOn","updated_at","date"));String tx=o.toString().toLowerCase(Locale.ROOT);if(tm>=cutoff&&isDisaster(tx)){incidents++;ids.add(String.valueOf(o.opt("id")));}}int dead=0,inj=0,miss=0,res=0;boolean ds=false,is=false,ms=false,rs=false;for(int i=0;i<lr.length();i++){JSONObject o=lr.optJSONObject(i);if(o==null)continue;String id=str(o,"incident_id","incidentId");if(!id.isEmpty()&&!ids.contains(id))continue;String tx=o.toString().toLowerCase(Locale.ROOT);int q=(int)Math.max(0,numOr(o,"count","people","peopleCount","people_count","number","total","value","noOfPeople","no_of_people"));if(tx.matches(".*(dead|death|deceased|fatal|मृत|मृत्यु).*")){dead+=q;ds=true;}else if(tx.matches(".*(injur|घाइते).*")){inj+=q;is=true;}else if(tx.matches(".*(missing|बेपत्ता).*")){miss+=q;ms=true;}else if(tx.matches(".*(rescued|rescue|उद्धार).*")){res+=q;rs=true;}}final int fi=incidents,fd=dead,fj=inj,fm=miss,fr=res;final boolean fds=ds,fis=is,fms=ms,frs=rs;runOnUiThread(()->{humanCard.setVisibility(fi>0?View.VISIBLE:View.GONE);if(fi>0){humanFresh.setText(t("BIPAD official • पछिल्लो १० दिन • "+fi+" घटना","BIPAD official • last 10 days • "+fi+" incidents"));humanDeaths.setText(fds?String.valueOf(fd):"—");humanInjured.setText(fis?String.valueOf(fj):"—");humanMissing.setText(fms?String.valueOf(fm):"—");humanRescued.setText(frs?String.valueOf(fr):"—");humanDetail.setText(t("अनुमानित संख्या देखाइँदैन। Official loss records मात्र।","No estimated counts. Official loss records only."));}});}catch(Exception ignored){}});}
    private void refreshNews(){newsList.removeAllViews();newsList.addView(empty(t("नयाँ समाचार जाँच हुँदैछ…","Checking latest news…")));io.execute(()->{try{JSONObject j=getJson(NEWS_ENDPOINT+"?_native="+System.currentTimeMillis());JSONArray arr=j.optJSONArray("items");if(arr==null)arr=j.optJSONArray("results");if(arr==null)arr=j.optJSONArray("news");if(arr==null)arr=new JSONArray();final List<NewsItem> out=new ArrayList<>();long now=System.currentTimeMillis();for(int i=0;i<arr.length()&&out.size()<12;i++){JSONObject o=arr.optJSONObject(i);if(o==null)continue;String source=str(o,"source"),title=str(o,"title"),url=str(o,"url","link");long at=parseTime(str(o,"published_at","publishedAt","date"));if(title.isEmpty()||url.isEmpty()||!(source.equals("RONB Post")||source.equals("Radio Nepal")||source.equals("News24 Nepal")))continue;if(at>0&&now-at>30L*60*1000)continue;out.add(new NewsItem(title,source,url,at));}runOnUiThread(()->renderNews(out));}catch(Exception e){runOnUiThread(()->{newsList.removeAllViews();newsList.addView(empty(t("Live news अहिले उपलब्ध छैन।","Live news is currently unavailable.")));});}});}
    private void renderNews(List<NewsItem> out){newsList.removeAllViews();if(out.isEmpty()){newsList.addView(empty(t("नयाँ live समाचार भेटिएन।","No fresh live stories found.")));return;}for(NewsItem n:out){LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(12),dp(11),dp(12),dp(11));c.setBackground(round(Color.rgb(248,252,254),17,Color.rgb(216,234,243),1));TextView title=text(n.title,15,true,Color.rgb(16,39,70));TextView meta=text(n.source+(n.at>0?" • "+Math.max(0,(System.currentTimeMillis()-n.at)/60000)+" min ago":""),11,false,Color.rgb(102,131,153));TextView open=text(t("खोल्नुहोस् ↗","Open ↗"),12,true,Color.rgb(20,119,184));open.setPadding(0,dp(5),0,0);open.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(n.url)));}catch(Exception ignored){}});c.addView(title);c.addView(meta);c.addView(open);LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(8));newsList.addView(c,p);}}

    private void showPrivacy(){new AlertDialog.Builder(this).setTitle(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety")).setMessage(t("FloodSafe ले location स्थानीय मौसम र 2 km verified river warning मिलाउन प्रयोग गर्छ। Background location user-enabled monitoring का लागि मात्र हो। Microphone SATHI voice का लागि मात्र प्रयोग हुन्छ। FCM notification delivery का लागि device token प्रयोग हुन सक्छ। Force stop पछि Android ले background काम रोक्न सक्छ।","FloodSafe uses location for local weather and verified river warnings within 2 km. Background location is used only for user-enabled monitoring. Microphone is used for SATHI voice. FCM may process a device token for notification delivery. Android can stop background work after an explicit Force stop.")).setPositiveButton("OK",null).show();}

    private void showSathiDialog(String initial){LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(8),dp(18),0);TextView answer=text(initial==null?t("मौसम, नदी, warning वा app status सोध्नुहोस्।","Ask about weather, rivers, warnings or app status."):answerSathi(initial),14,false,Color.rgb(30,52,72));box.addView(answer);Button mic=button(t("🎙️ माइकबाट सोध्नुहोस्","🎙️ Ask by voice"));box.addView(mic,lp(-1,dp(52),0,dp(12),0,0));AlertDialog d=new AlertDialog.Builder(this).setTitle("🤖 SATHI").setView(box).setNegativeButton(t("बन्द","Close"),null).create();mic.setOnClickListener(v->startVoice(answer));d.show();}
    private void startVoice(TextView out){if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},REQ_MIC);return;}if(!SpeechRecognizer.isRecognitionAvailable(this)){out.setText(t("यो फोनमा voice recognition उपलब्ध छैन।","Voice recognition is unavailable on this phone."));return;}if(speech!=null)try{speech.destroy();}catch(Exception ignored){}speech=SpeechRecognizer.createSpeechRecognizer(this);speech.setRecognitionListener(new RecognitionListener(){public void onReadyForSpeech(Bundle b){out.setText(t("🎙 सुन्दैछु…","🎙 Listening…"));}public void onBeginningOfSpeech(){}public void onRmsChanged(float x){}public void onBufferReceived(byte[]b){}public void onEndOfSpeech(){}public void onError(int e){out.setText(t("आवाज बुझिएन। फेरि प्रयास गर्नुहोस्।","Could not understand. Try again."));}public void onPartialResults(Bundle b){}public void onEvent(int t,Bundle b){}public void onResults(Bundle b){ArrayList<String> r=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);String q=r==null||r.isEmpty()?"":r.get(0);String a=answerSathi(q);out.setText("तपाईं: "+q+"\n\nSATHI: "+a);speak(a);}});speech.startListening(new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,english?"en-GB":"ne-NP").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,5));}
    private String answerSathi(String q){String x=q==null?"":q.toLowerCase(Locale.ROOT);if(x.contains("weather")||x.contains("मौसम")||x.contains("rain")||x.contains("वर्षा"))return currentWeather.isEmpty()?t("मौसम data refresh हुँदैछ।","Weather data is refreshing."):currentWeather;if(x.contains("river")||x.contains("नदी")||x.contains("खोला")||x.contains("flood")||x.contains("बाढी")){int d=0,w=0,a=0;synchronized(stations){for(RiverStation s:stations){if(s.stage.equals("danger"))d++;else if(s.stage.equals("warning"))w++;else if(s.stage.equals("alert"))a++;}}return t("Fresh official river status: danger "+d+", warning "+w+", alert "+a+"।","Fresh official river status: danger "+d+", warning "+w+", alert "+a+".");}if(x.contains("notification")||x.contains("alert")||x.contains("warning"))return t("२ घण्टाको weather digest र verified Warning/Danger २ km भित्रको emergency river alert सक्रिय छन्।","Two-hour weather digests and verified Warning/Danger river alerts within 2 km are enabled.");return t("मौसम, नदी, flood warning, location वा notification बारे सोध्नुहोस्।","Ask about weather, rivers, flood warnings, location or notifications.");}
    private void consumeSathiIntent(Intent i){if(i==null)return;String q=i.getStringExtra(SathiWakeService.EXTRA_QUERY);if(q!=null&&!q.trim().isEmpty()){showSathiDialog(q.trim());i.removeExtra(SathiWakeService.EXTRA_QUERY);}}

    private void enableMonitoring(){getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit().putBoolean("enabled",true).apply();Constraints c=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();WorkManager wm=WorkManager.getInstance(getApplicationContext());wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RainAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RiverAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},REQ_NOTIFY);}

    private void loadMapBase(){io.execute(()->{try{Bitmap b=renderMapBitmap();runOnUiThread(()->map.setBase(b));}catch(Exception e){runOnUiThread(()->mapHint.setText(t("नक्सा geometry लोड हुन सकेन; station data चलिरहेको छ।","Map geometry failed to load; station data remains active.")));}});}
    private Bitmap renderMapBitmap()throws Exception{int W=1500,H=820;Bitmap b=Bitmap.createBitmap(W,H,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(b);Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);p.setColor(Color.rgb(219,239,246));c.drawColor(Color.rgb(219,239,246));JSONObject districts=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=districts.optJSONArray("features");if(fs==null){districts=assetJson("floodsafe-nepal/v24/nepal-districts.json");fs=districts.optJSONArray("features");}if(fs!=null){for(int i=0;i<fs.length();i++){JSONObject g=fs.optJSONObject(i);if(g==null)continue;JSONObject geo=g.optJSONObject("geometry");if(geo==null)continue;JSONArray co=geo.optJSONArray("coordinates");if(co==null)continue;p.setStyle(Paint.Style.FILL);p.setColor(i%3==0?Color.rgb(220,239,231):i%3==1?Color.rgb(205,232,242):Color.rgb(229,237,207));drawGeo(c,p,geo.optString("type"),co,W,H);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.5f);p.setColor(Color.WHITE);drawGeo(c,p,geo.optString("type"),co,W,H);}}
        JSONObject rivers=assetJson("data/nepal-waterways-tiles/overview.json");JSONArray ways=rivers.optJSONArray("waterways");if(ways!=null){p.setStyle(Paint.Style.STROKE);p.setStrokeCap(Paint.Cap.ROUND);p.setColor(Color.rgb(49,169,221));p.setAlpha(205);p.setStrokeWidth(2.2f);for(int i=0;i<ways.length();i++){JSONObject w=ways.optJSONObject(i);JSONArray pts=w==null?null:w.optJSONArray("pts");if(pts==null||pts.length()<2)continue;Path path=new Path();for(int j=0;j<pts.length();j++){JSONArray pt=pts.optJSONArray(j);if(pt==null||pt.length()<2)continue;float x=mapX(pt.optDouble(0),W),y=mapY(pt.optDouble(1),H);if(j==0)path.moveTo(x,y);else path.lineTo(x,y);}c.drawPath(path,p);}}
        p.setStyle(Paint.Style.FILL);p.setColor(Color.rgb(31,69,60));p.setTextSize(25f);p.setTypeface(Typeface.DEFAULT_BOLD);c.drawText("NEPAL • official river map",34,42,p);return b;}
    private void drawGeo(Canvas c,Paint p,String type,JSONArray co,int W,int H){try{if("Polygon".equals(type)){drawPolygon(c,p,co,W,H);}else if("MultiPolygon".equals(type)){for(int i=0;i<co.length();i++){JSONArray poly=co.optJSONArray(i);if(poly!=null)drawPolygon(c,p,poly,W,H);}}}catch(Exception ignored){}}
    private void drawPolygon(Canvas c,Paint p,JSONArray poly,int W,int H){JSONArray ring=poly.optJSONArray(0);if(ring==null||ring.length()<3)return;Path path=new Path();for(int i=0;i<ring.length();i++){JSONArray pt=ring.optJSONArray(i);if(pt==null)continue;float x=mapX(pt.optDouble(0),W),y=mapY(pt.optDouble(1),H);if(i==0)path.moveTo(x,y);else path.lineTo(x,y);}path.close();c.drawPath(path,p);}
    private static float mapX(double lo,int w){return(float)((lo-80.0)/(88.35-80.0)*w);}private static float mapY(double la,int h){return(float)((30.5-la)/(30.5-26.2)*h);}

    private final class NativeRiverMap extends View{
        private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);private Bitmap base;private List<RiverStation> data=new ArrayList<>();private double uLat=Double.NaN,uLon=Double.NaN;private float scale=1f,tx=0,ty=0;private boolean terrain=false;private final ScaleGestureDetector scaler;private final GestureDetector gestures;
        NativeRiverMap(){super(NativeFullActivity.this);setBackgroundColor(Color.rgb(219,239,246));scaler=new ScaleGestureDetector(NativeFullActivity.this,new ScaleGestureDetector.SimpleOnScaleGestureListener(){@Override public boolean onScale(ScaleGestureDetector d){float old=scale;scale=Math.max(1f,Math.min(6f,scale*d.getScaleFactor()));float f=scale/old;tx=d.getFocusX()-(d.getFocusX()-tx)*f;ty=d.getFocusY()-(d.getFocusY()-ty)*f;invalidate();return true;}});gestures=new GestureDetector(NativeFullActivity.this,new GestureDetector.SimpleOnGestureListener(){@Override public boolean onDown(MotionEvent e){return true;}@Override public boolean onScroll(MotionEvent e1,MotionEvent e2,float dx,float dy){tx-=dx;ty-=dy;invalidate();return true;}@Override public boolean onSingleTapConfirmed(MotionEvent e){RiverStation s=findStationAt(e.getX(),e.getY());if(s!=null)showStation(s);return true;}});}
        void setBase(Bitmap b){base=b;invalidate();}void setStations(List<RiverStation>s,double la,double lo){data=new ArrayList<>(s);uLat=la;uLon=lo;invalidate();}void zoomBy(float f){float cx=getWidth()/2f,cy=getHeight()/2f,old=scale;scale=Math.max(1f,Math.min(6f,scale*f));float q=scale/old;tx=cx-(cx-tx)*q;ty=cy-(cy-ty)*q;invalidate();}void resetView(){scale=1f;tx=ty=0;invalidate();}void toggleTerrain(){terrain=!terrain;invalidate();}
        @Override public boolean onTouchEvent(MotionEvent e){scaler.onTouchEvent(e);gestures.onTouchEvent(e);return true;}
        @Override protected void onDraw(Canvas c){super.onDraw(c);float w=getWidth(),h=getHeight();c.save();c.translate(tx,ty);c.scale(scale,scale);if(base!=null){RectF dst=new RectF(0,0,w,h);if(terrain){p.setColor(Color.argb(70,0,0,0));c.drawBitmap(base,null,new RectF(dp(5),dp(7),w+dp(5),h+dp(7)),p);}p.setAlpha(255);c.drawBitmap(base,null,dst,p);}for(RiverStation s:data){float x=(float)((s.lon-80)/(88.35-80))*w,y=(float)((30.5-s.lat)/(30.5-26.2))*h;p.setStyle(Paint.Style.FILL);p.setColor(stageColor(s.stage));c.drawCircle(x,y,Math.max(3f,dp((s.stage.equals("danger")||s.stage.equals("warning"))?5:3)/scale),p);}if(isNepal(uLat,uLon)){float x=(float)((uLon-80)/(88.35-80))*w,y=(float)((30.5-uLat)/(30.5-26.2))*h;p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(Math.max(2f,dp(2)/scale));p.setColor(Color.rgb(11,127,208));c.drawCircle(x,y,dp(9)/scale,p);p.setStyle(Paint.Style.FILL);}c.restore();}
        RiverStation findStationAt(float sx,float sy){float x=(sx-tx)/scale,y=(sy-ty)/scale,w=getWidth(),h=getHeight();RiverStation best=null;double bd=30/scale;for(RiverStation s:data){float px=(float)((s.lon-80)/(88.35-80))*w,py=(float)((30.5-s.lat)/(30.5-26.2))*h;double d=Math.hypot(px-x,py-y);if(d<bd){bd=d;best=s;}}return best;}
    }

    private final Runnable clockTick=new Runnable(){@Override public void run(){try{java.time.ZonedDateTime z=java.time.ZonedDateTime.now(java.time.ZoneId.of("Asia/Kathmandu"));clock.setText(String.format(Locale.US,"%02d:%02d:%02d NPT",z.getHour(),z.getMinute(),z.getSecond()));}catch(Exception ignored){}main.postDelayed(this,1000);}};
    private void initTts(){tts=new TextToSpeech(getApplicationContext(),s->{if(s==TextToSpeech.SUCCESS&&tts!=null){int r=tts.setLanguage(Locale.forLanguageTag("ne-NP"));if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(new Locale("ne"));tts.setSpeechRate(.92f);}});}private void speak(String s){if(tts!=null&&s!=null&&!s.isEmpty())tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"sathi-native-full");}
    @Override public void onRequestPermissionsResult(int code,String[]p,int[]g){super.onRequestPermissionsResult(code,p,g);if(code==REQ_LOCATION&&hasLocationPermission())requestLocation();else if(code==REQ_MIC&&checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)showSathiDialog(null);}
    private boolean hasLocationPermission(){return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED||checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
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
    private static int stageColor(String s){switch(s){case"danger":return Color.rgb(214,47,67);case"warning":return Color.rgb(239,125,36);case"alert":return Color.rgb(224,165,42);case"normal":return Color.rgb(45,140,255);default:return Color.rgb(113,139,155);}}private static int stageBg(String s){switch(s){case"danger":return Color.rgb(255,240,242);case"warning":return Color.rgb(255,247,235);case"alert":return Color.rgb(255,248,233);case"normal":return Color.rgb(233,255,245);default:return Color.rgb(243,249,252);}}private static String stageDot(String s){switch(s){case"danger":return"🔴";case"warning":return"🟠";case"alert":return"🟡";case"normal":return"🔵";default:return"⚪";}}private String stageName(String s){switch(s){case"danger":return t("खतरा","DANGER");case"warning":return t("चेतावनी","WARNING");case"alert":return t("निगरानी","ALERT");case"normal":return t("सामान्य","NORMAL");default:return t("पुरानो/अज्ञात","STALE/UNKNOWN");}}
    private LinearLayout card(){LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(17),dp(16),dp(17),dp(16));c.setBackground(round(Color.argb(248,255,255,255),25,Color.rgb(207,229,239),1));c.setElevation(dp(3));c.setLayoutParams(lp(-1,-2,0,0,0,dp(14)));return c;}
    private TextView text(String s,float sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);v.setGravity(Gravity.START);v.setLineSpacing(0,1.08f);if(bold)v.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));return v;}
    private TextView badge(String s,int bg,int fg){TextView v=text(s,10,true,fg);v.setPadding(dp(9),dp(6),dp(9),dp(6));v.setGravity(Gravity.CENTER);v.setBackground(round(bg,99,Color.TRANSPARENT,0));return v;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(Color.rgb(18,48,75));b.setTextSize(15);b.setTypeface(Typeface.DEFAULT_BOLD);b.setBackground(round(Color.WHITE,18,Color.rgb(207,228,239),1));return b;}
    private Button smallButton(String s){Button b=button(s);b.setTextSize(12);return b;}private Button navButton(String s){Button b=button(s);b.setTextSize(11);b.setBackground(round(Color.rgb(234,246,252),16,Color.TRANSPARENT,0));return b;}
    private TextView empty(String s){TextView v=text(s,12,false,Color.rgb(102,131,153));v.setPadding(dp(14),dp(13),dp(14),dp(13));v.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));return v;}
    private GradientDrawable round(int color,int radius,int stroke,int sw){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));if(sw>0)g.setStroke(dp(sw),stroke);return g;}
    private LinearLayout.LayoutParams lp(int w,int h,int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w,h);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}private LinearLayout.LayoutParams weight(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-1,1f);p.setMargins(dp(2),0,dp(2),0);return p;}private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private static final class RiverStation{final String stationId,name,riverName,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){this("",n,"",di,a,o,l,w,d,tm,f,s,r);}RiverStation(String id,String n,String rn,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){stationId=id==null?"":id;name=n;riverName=rn==null?"":rn;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;}}
    private static final class NewsItem{final String title,source,url;final long at;NewsItem(String t,String s,String u,long a){title=t;source=s;url=u;at=a;}}
    @Override protected void onDestroy(){main.removeCallbacksAndMessages(null);if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}if(tts!=null){tts.stop();tts.shutdown();}io.shutdownNow();super.onDestroy();}
}
