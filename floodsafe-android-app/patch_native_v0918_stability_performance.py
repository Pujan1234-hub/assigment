from pathlib import Path
import re

ROOT=Path('floodsafe-android-app')
J=ROOT/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
UI=J/'NativeFullActivity.java'
MON=J/'FloodLiveGaugeMonitor.java'
GRADLE=ROOT/'app/build.gradle'

u=UI.read_text(encoding='utf-8')
m=MON.read_text(encoding='utf-8')
g=GRADLE.read_text(encoding='utf-8')

def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1, got {n}')
    return text.replace(old,new,1)

# 1) Language switch: rebuild the native view from persisted language so every static
# label changes together (bottom nav, weather stat labels, cards) instead of partial mutation.
old_lang='langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();v0909SkipMapUpdateOnce=true;applyLanguage();v0909TranslateStaticTree(root);refreshRiverUi();updateWeatherLayerUi();}); // V0909_FAST_LANGUAGE_NO_RECREATE'
new_lang='langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();recreate();}); /* V0918_ATOMIC_LANGUAGE_SWITCH */'
u=once(u,old_lang,new_lang,'atomic language switch')

# 2) Weather hero: keep rich detail for SATHI, but show only the condition headline in hero.
anchor='    private String t(String ne,String en){return english?en:ne;}'
helper='''    private String weatherHeadline(String detail){if(detail==null||detail.trim().isEmpty())return "";int i=detail.indexOf(',');return (i>0?detail.substring(0,i):detail).trim();} // V0918_WEATHER_HEADLINE_ONLY\n\n'''
if helper.strip() not in u:
    if anchor not in u: raise SystemExit('t() anchor missing')
    u=u.replace(anchor,helper+anchor,1)
old_apply='weatherText.setText(currentWeather.isEmpty()?t("नेपालको निगरानी स्थान छान्नुहोस्","Choose a monitoring location"):currentWeather);'
new_apply='weatherText.setText(currentWeather.isEmpty()?t("नेपालको निगरानी स्थान छान्नुहोस्","Choose a monitoring location"):weatherHeadline(currentWeather));'
u=once(u,old_apply,new_apply,'weather headline applyLanguage')
u=u.replace('weatherText.setText(currentWeather);','weatherText.setText(weatherHeadline(currentWeather));')

# 3) Hero clock follows the phone/local timezone. River/station timestamps remain official Nepal time.
clock_pat=re.compile(r'    private final Runnable clockTick=new Runnable\(\)\{@Override public void run\(\)\{try\{java\.time\.ZonedDateTime z=java\.time\.ZonedDateTime\.now\(java\.time\.ZoneId\.of\("Asia/Kathmandu"\)\);clock\.setText\(String\.format\(Locale\.US,"%02d:%02d:%02d NPT",z\.getHour\(\),z\.getMinute\(\),z\.getSecond\(\)\)\);\}catch\(Exception ignored\)\{\}main\.postDelayed\(this,1000\);\}\};')
new_clock='    private final Runnable clockTick=new Runnable(){@Override public void run(){try{java.time.ZonedDateTime z=java.time.ZonedDateTime.now();clock.setText(String.format(Locale.US,"%02d:%02d:%02d",z.getHour(),z.getMinute(),z.getSecond()));}catch(Exception ignored){}main.postDelayed(this,1000);}}; // V0918_LOCAL_DEVICE_CLOCK'
u,n=clock_pat.subn(new_clock,u,count=1)
if n!=1: raise SystemExit(f'local clock anchor count={n}')

# 4) Remove mixed-language text from the Nepali outside-Nepal notice only.
old_notice='🇳🇵 FloodSafe Nepal-only monitoring\\nतपाईं नेपाल बाहिर हुँदा नजिकको नदी चेतावनी पठाइँदैन। नेपालभित्र current GPS हुँदा २ km भित्रको verified Warning/Danger मात्र emergency alert आउँछ।'
new_notice='🇳🇵 FloodSafe Nepal निगरानी\\nतपाईं नेपाल बाहिर हुँदा नजिकको नदी चेतावनी पठाइँदैन। नेपालभित्र हालको GPS हुँदा २ किमिभित्रको प्रमाणित चेतावनी/खतरा मात्र आपतकालीन सूचना आउँछ।'
if old_notice not in u: raise SystemExit('outside notice anchor missing')
u=u.replace(old_notice,new_notice,1)

# 5) Background monitor performance: the old code performed river + rain + 3 hydrology
# network fetches on a one-second scheduler. Keep alert semantics and endpoints untouched,
# but stagger source network polling. River remains fast at 15s; rain/hydrology at 60s.
field_anchor='    private volatile boolean running=false;\n    private volatile int lastRiverHash=0,lastRainHash=0,lastHydroHash=0;'
field_new='''    private volatile boolean running=false;
    private volatile int lastRiverHash=0,lastRainHash=0,lastHydroHash=0;
    private static final long SCHEDULER_TICK_MS=5_000L;
    private static final long RIVER_POLL_MS=15_000L;
    private static final long RAIN_POLL_MS=60_000L;
    private static final long HYDRO_POLL_MS=60_000L;
    private volatile long nextRiverAt=0L,nextRainAt=0L,nextHydroAt=0L; // V0918_LOW_POWER_SOURCE_SCHEDULE
'''
m=once(m,field_anchor,field_new,'monitor schedule fields')
old_tick='''    private final Runnable tick=new Runnable(){@Override public void run(){
        if(!running)return;
        if(riverInFlight.compareAndSet(false,true))io.execute(()->{try{pollRiverOnce();}catch(Exception ignored){}finally{riverInFlight.set(false);}});
        if(rainInFlight.compareAndSet(false,true))io.execute(()->{try{pollRainOnce();}catch(Exception ignored){}finally{rainInFlight.set(false);}});
        if(hydroInFlight.compareAndSet(false,true))io.execute(()->{try{pollHydrologyOnce();}catch(Exception ignored){}finally{hydroInFlight.set(false);}});
        handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK
    }};'''
new_tick='''    private final Runnable tick=new Runnable(){@Override public void run(){
        if(!running)return;
        long now=System.currentTimeMillis();
        if(now>=nextRiverAt&&riverInFlight.compareAndSet(false,true)){nextRiverAt=now+RIVER_POLL_MS;io.execute(()->{try{pollRiverOnce();}catch(Exception ignored){}finally{riverInFlight.set(false);}});}
        if(now>=nextRainAt&&rainInFlight.compareAndSet(false,true)){nextRainAt=now+RAIN_POLL_MS;io.execute(()->{try{pollRainOnce();}catch(Exception ignored){}finally{rainInFlight.set(false);}});}
        if(now>=nextHydroAt&&hydroInFlight.compareAndSet(false,true)){nextHydroAt=now+HYDRO_POLL_MS;io.execute(()->{try{pollHydrologyOnce();}catch(Exception ignored){}finally{hydroInFlight.set(false);}});}
        handler.postDelayed(this,SCHEDULER_TICK_MS); // V0918_LOW_POWER_BACKGROUND_RECHECK
    }};'''
m=once(m,old_tick,new_tick,'monitor one-second network loop')

# Version bump from v0.9.17.
g=once(g,'versionCode 34','versionCode 35','versionCode')
g=once(g,"versionName '0.9.17-native-weather-runtime'","versionName '0.9.18-stability-performance'",'versionName')

# Invariants: alert semantics/endpoints remain intact.
for token in ['RADIUS_KM=2d','WARNING_REPEAT_MS=90L*60L*1000L','DANGER_REPEAT_MS=30L*60L*1000L','checkNearbyHazards','RIVER_ENDPOINT','RAIN_ENDPOINT','HYDRO_ENDPOINTS']:
    if token not in m: raise SystemExit('monitor invariant missing: '+token)
for token in ['V0918_ATOMIC_LANGUAGE_SWITCH','V0918_WEATHER_HEADLINE_ONLY','V0918_LOCAL_DEVICE_CLOCK']:
    if token not in u: raise SystemExit('UI invariant missing: '+token)
if 'handler.postDelayed(this,1_000L)' in m: raise SystemExit('one-second network scheduler still present')
if 'versionCode 35' not in g: raise SystemExit('version bump missing')

UI.write_text(u,encoding='utf-8')
MON.write_text(m,encoding='utf-8')
GRADLE.write_text(g,encoding='utf-8')
print('V0918_STABILITY_PERFORMANCE_PATCHED')
