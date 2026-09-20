from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
r_path=src/'RainAlertWorker.java'
b_path=src/'BootReceiver.java'
w_path=src/'RiverAlertWorker.java'
f_path=src/'FloodSafeMessagingService.java'
g_path=root/'app/build.gradle'

a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
r=r_path.read_text(encoding='utf-8')
b=b_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.69 is intentionally narrow:
# - display only official river/water-level gauges (no rain-only/velocity dots)
# - preserve source-exact latest river value/time; no local display minute cutoff
# - keep official rainfall feed hidden as dots but expose nearest rainfall detail inside river gauge detail
# - restore a true 2-hour weather digest + rain-event alerts and kick workers after startup/GPS
# - keep verified river Warning/Danger push radius exactly 2 km

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# 1) Final river refresh = water-level gauge inventory only. Rainfall/velocity series never enter map/list.
sp=method_span(a,'refreshRivers')
if not sp:raise SystemExit('v0869 refreshRivers missing')
refresh=r'''    private void refreshRivers(){
        if(v862FinalRefreshInFlight)return;v862FinalRefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> raw=loadTrustedRiverStationsV862(now);
                List<RiverStation> out=new ArrayList<>();
                for(RiverStation s:raw)if(v0857WaterLevelStation(s))out.add(s); // V0869_RIVER_GAUGES_ONLY
                out.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                int sourceCurrent=0;for(RiverStation s:out)if(s.online&&Double.isFinite(s.level)&&s.at>0L)sourceCurrent++;
                v849CatalogCount=out.size();v849LatestCount=sourceCurrent; // counts now mean river gauges only
                String fp=v862FinalFingerprint(out);boolean changed=!fp.equals(v862FinalLastFingerprint);
                if(!out.isEmpty()&&changed){synchronized(stations){stations.clear();stations.addAll(out);}v862FinalLastFingerprint=fp;}
                runOnUiThread(()->{v862FinalRefreshInFlight=false;if(changed&&!out.isEmpty())refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v862FinalRefreshInFlight=false);}
        });
    } // V0869_284_GAUGE_ONLY_REFRESH
'''
a=a[:sp[0]]+refresh+a[sp[1]:]

# 2) UI/map: only river gauge dots. District page shows full gauge inventory for all 77 districts;
# source-current rows carry the exact official source value/time, unavailable rows stay unavailable.
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0869 refreshRiverUi missing')
river_ui=r'''    private void refreshRiverUi(){
        if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        copy.removeIf(s->!v0857WaterLevelStation(s));
        copy.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(copy,lat,lon);
        map.setRainStations(new ArrayList<>()); // V0869_NO_RAIN_ONLY_MAP_DOTS

        int current=0,d=0,w=0,al=0,n=0;
        for(RiverStation s:copy){if(s.online&&Double.isFinite(s.level)&&s.at>0L){current++;if("danger".equals(s.stage))d++;else if("warning".equals(s.stage))w++;else if("alert".equals(s.stage))al++;else n++;}}
        int sourceTotal=copy.size();mapRiverCurrent=current;mapRiverTotal=sourceTotal;
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("आधिकारिक नदी gauge "+sourceTotal+" • स्रोतमा अहिले मापन "+current+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n,
                "Official river gauges "+sourceTotal+" • current source readings "+current+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n)); // V0869_GAUGE_COUNT_UI
        updateMapHintCounts();
        updateRisk(copy);

        nearList.removeAllViews();
        if(!Double.isFinite(lat)||!Double.isFinite(lon)){
            nearSub.setText(t("हालको GPS लिएपछि वास्तविक नजिकका official river gauge देखिन्छन्।","Get current GPS to show the actual nearest official river gauges."));
            nearList.addView(empty(t("◎ मेरो हालको स्थान थिचेर GPS लिनुहोस्।","Tap My current location to get GPS.")));
        }else if(!isNepal(lat,lon)){
            nearSub.setText(t("तपाईं अहिले नेपाल बाहिर हुनुहुन्छ।","You are currently outside Nepal."));
            nearList.addView(empty(t("नेपाल बाहिर हुँदा नजिकका नेपाल river gauge देखाइँदैन।","Nearby Nepal river gauges are not shown outside Nepal.")));
        }else{
            nearSub.setText(t("हालको GPS बाट दूरीअनुसार नजिकका official river gauge","Official river gauges nearest to current GPS"));
            List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));
            for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));
            if(near.isEmpty())nearList.addView(empty(t("नजिकको official river gauge भेटिएन।","No nearby official river gauge was found.")));
        }

        if(nationalList!=null){
            nationalList.removeAllViews();
            if(selectedDistrict.isEmpty()){
                nationalFresh.setText(t("जिल्ला छानेर त्यहाँका official river gauge, exact source time र rainfall detail हेर्नुहोस्।","Choose a district to view official river gauges, exact source time and rainfall detail."));
                nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));
            }else{
                int total=0,live=0;
                for(RiverStation s:copy)if(selectedDistrict.equalsIgnoreCase(s.district)){
                    total++;if(s.online&&Double.isFinite(s.level)&&s.at>0L)live++;nationalList.addView(stationRow(s));
                }
                nationalFresh.setText(t(selectedDistrict+": official river gauge "+total+" • अहिले source reading "+live,
                        selectedDistrict+": official river gauges "+total+" • current source readings "+live));
                if(total==0)nationalList.addView(empty(t("यो जिल्लामा catalog भएको official river gauge भेटिएन।","No catalogued official river gauge was found in this district.")));
            }
        }
    } // V0869_77_DISTRICT_GAUGE_DETAIL
'''
a=a[:sp[0]]+river_ui+a[sp[1]:]

# 3) Rain stays a data feed for detail/alerts, never a standalone station layer on the map.
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0869 refreshRainUi missing')
rain_ui=r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        int current=0;for(RainStation s:copy)if(s.fresh&&s.at>0L)current++;
        mapRainFresh=current;mapRainTotal=copy.size();
        map.setRainStations(new ArrayList<>()); // V0869_RAIN_DATA_NOT_RAIN_STATION_DOTS
        updateMapHintCounts();
    }
'''
a=a[:sp[0]]+rain_ui+a[sp[1]:]

sp=method_span(a,'updateMapHintCounts')
if not sp:raise SystemExit('v0869 updateMapHintCounts missing')
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 official river gauge "+mapRiverCurrent+" / "+mapRiverTotal+" • 77 जिल्ला • rainfall detail gauge card भित्र",
                          "🌊 official river gauges "+mapRiverCurrent+" / "+mapRiverTotal+" • 77 districts • rainfall detail inside gauge cards"));
    } // V0869_RIVER_ONLY_MAP_HEADER
'''
a=a[:sp[0]]+hint+a[sp[1]:]

# 4) River-gauge detail includes nearest official rainfall observation with its own exact source time.
if 'private RainStation v0869NearestRain(' not in a:
    sp=method_span(a,'showStation')
    if not sp:raise SystemExit('v0869 showStation insert anchor missing')
    helper=r'''    private RainStation v0869NearestRain(RiverStation gauge){
        if(gauge==null)return null;RainStation best=null;double bestD=Double.POSITIVE_INFINITY;
        synchronized(rainStations){for(RainStation r:rainStations){if(r==null||!r.fresh||r.at<=0L)continue;double d=distanceKm(gauge.lat,gauge.lon,r.lat,r.lon);if(Double.isFinite(d)&&d<bestD){bestD=d;best=r;}}}
        return best; // clearly labelled nearest official rain station; never represented as a river gauge
    } // V0869_NEAREST_RAIN_DETAIL

'''
    a=a[:sp[0]]+helper+a[sp[0]:]

sp=method_span(a,'showStation')
if not sp:raise SystemExit('v0869 showStation missing')
station_detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;boolean hasReading=s.online&&Double.isFinite(s.level)&&s.at>0L;
        StringBuilder b=new StringBuilder();
        b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("पछिल्लो official source मा उपलब्ध","Available in latest official source"):t("पछिल्लो official source मा उपलब्ध छैन","Not available in latest official source"));
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);
        if(hasReading){
            b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
            b.append("\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
            b.append("\n").append(t("Official source time: ","Official source time: ")).append(v848Time(s.at));
            b.append("\n").append(t("Source age: ","Source age: ")).append(v850Age(s.at));
        }else b.append("\n\n").append(t("हाल official source मा पानीको सतह/समय उपलब्ध छैन।","Water level/time is not currently available in the official source."));

        RainStation rr=v0869NearestRain(s);
        b.append("\n\n🌧️ ").append(t("वर्षा detail","Rainfall detail"));
        if(rr!=null){
            double rd=distanceKm(s.lat,s.lon,rr.lat,rr.lon);
            b.append("\n").append(t("नजिकको official rainfall station: ","Nearest official rainfall station: ")).append(rr.name);
            b.append("\n").append(t("Rainfall: ","Rainfall: ")).append(Double.isFinite(rr.rainfall)?String.format(Locale.US,"%.1f mm",rr.rainfall):"—");
            b.append("\n").append(t("Rain source time: ","Rain source time: ")).append(v848Time(rr.at));
            if(Double.isFinite(rd))b.append("\n").append(t("River gauge बाट दूरी: ","Distance from river gauge: ")).append(String.format(Locale.US,"%.1f km",rd));
        }else b.append("\n").append(t("हाल official rainfall reading उपलब्ध छैन।","No official rainfall reading is currently available."));
        b.append("\n\n").append(t("स्रोत: BIPAD/DHM official • app ले आफ्नै minute cutoff वा बनावटी time/value राख्दैन।","Source: official BIPAD/DHM • the app does not invent a minute cutoff, time or value."));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0869_GAUGE_PLUS_RAIN_DETAIL
'''
a=a[:sp[0]]+station_detail+a[sp[1]:]

# 5) Native map rain layers stay empty and rain-only tap target is removed.
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0869 map refreshRainSources missing')
rain_sources=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        setGeo("fs-rain-stale",emptyFeatureCollection());
        setGeo("fs-rain-normal",emptyFeatureCollection());
        setGeo("fs-rain-alert",emptyFeatureCollection());
        setGeo("fs-rain-warning",emptyFeatureCollection());
        setGeo("fs-rain-danger",emptyFeatureCollection());
    } // V0869_HIDE_RAIN_ONLY_STATIONS
'''
m=m[:sp[0]]+rain_sources+m[sp[1]:]

sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0869 onMapClick missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;} // V0869_RIVER_GAUGE_TAP_FIRST
        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}
        return false;
    } // V0869_NO_RAIN_STATION_TAP
'''
m=m[:sp[0]]+click+m[sp[1]:]

# 6) Lock the final built worker to a 2-hour weather digest. Rain-start alerts remain event-driven.
r=r.replace('roughly every 3 hours','roughly every 2 hours').replace('roughly every 4 hours','roughly every 2 hours')
r=re.sub(r'WEATHER_DIGEST_INTERVAL_MS\s*=\s*\d+L\s*\*\s*60L\s*\*\s*60L\s*\*\s*1000L',
         'WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L',r,count=1)
r=re.sub(r'smart_weather_updates_v\d+','smart_weather_updates_v4',r)
r=re.sub(r'last_weather_digest(?:_v\d+)?_at','last_weather_digest_v4_at',r)
r=r.replace('आगामी ३ घण्टामा वर्षाको सम्भावना','आगामी २ घण्टामा वर्षाको सम्भावना').replace('आगामी ४ घण्टामा वर्षाको सम्भावना','आगामी २ घण्टामा वर्षाको सम्भावना')
r=r.replace('३ घण्टाको मौसम अपडेट','२ घण्टाको मौसम अपडेट').replace('४ घण्टाको मौसम अपडेट','२ घण्टाको मौसम अपडेट')
r=r.replace('३ घण्टापछि करिब ','२ घण्टापछि करिब ').replace('४ घण्टापछि करिब ','२ घण्टापछि करिब ')
r=r.replace('now.plusHours(3).plusMinutes(30)','now.plusHours(2).plusMinutes(30)').replace('now.plusHours(4).plusMinutes(30)','now.plusHours(2).plusMinutes(30)')
if 'V0869_TWO_HOUR_NOTIFICATIONS' not in r:r=r.replace('private static final long EVENING_MIN_GAP_MS', '// V0869_TWO_HOUR_NOTIFICATIONS\n    private static final long EVENING_MIN_GAP_MS',1)

# 7) Kick rain/river checks immediately at startup and whenever GPS is refreshed; periodic 15-min WorkManager remains.
sp=method_span(a,'enableMonitoring')
if not sp:raise SystemExit('v0869 enableMonitoring missing')
enable=r'''    private void enableMonitoring(){
        getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit().putBoolean("enabled",true).apply();
        Constraints c=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();WorkManager wm=WorkManager.getInstance(getApplicationContext());
        wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RainAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());
        wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RiverAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());
        wm.enqueueUniqueWork("floodsafe-rain-check-now",androidx.work.ExistingWorkPolicy.REPLACE,new androidx.work.OneTimeWorkRequest.Builder(RainAlertWorker.class).setConstraints(c).build());
        wm.enqueueUniqueWork("floodsafe-river-check-now",androidx.work.ExistingWorkPolicy.REPLACE,new androidx.work.OneTimeWorkRequest.Builder(RiverAlertWorker.class).setConstraints(c).build()); // V0869_IMMEDIATE_ALERT_CHECK
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},REQ_NOTIFY);
    }

    private void v0869KickAlertChecks(){
        Constraints c=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();WorkManager wm=WorkManager.getInstance(getApplicationContext());
        wm.enqueueUniqueWork("floodsafe-rain-check-gps",androidx.work.ExistingWorkPolicy.REPLACE,new androidx.work.OneTimeWorkRequest.Builder(RainAlertWorker.class).setConstraints(c).build());
        wm.enqueueUniqueWork("floodsafe-river-check-gps",androidx.work.ExistingWorkPolicy.REPLACE,new androidx.work.OneTimeWorkRequest.Builder(RiverAlertWorker.class).setConstraints(c).build());
    } // V0869_GPS_ALERT_KICK
'''
a=a[:sp[0]]+enable+a[sp[1]:]
if 'v0869KickAlertChecks();FloodMonitorService.startIfEnabled(this);' not in a:
    a=a.replace('FloodMonitorService.startIfEnabled(this);}', 'v0869KickAlertChecks();FloodMonitorService.startIfEnabled(this);}',1)

# Boot/package replacement also restores periodic work and immediately checks once.
needle='manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",\n                ExistingPeriodicWorkPolicy.UPDATE, riverWork);'
if needle in b and 'V0869_BOOT_IMMEDIATE_CHECK' not in b:
    add=needle+'\n        manager.enqueue(new androidx.work.OneTimeWorkRequest.Builder(RainAlertWorker.class).setConstraints(constraints).build());\n        manager.enqueue(new androidx.work.OneTimeWorkRequest.Builder(RiverAlertWorker.class).setConstraints(constraints).build()); // V0869_BOOT_IMMEDIATE_CHECK'
    b=b.replace(needle,add,1)
elif 'V0869_BOOT_IMMEDIATE_CHECK' not in b:raise SystemExit('v0869 boot work anchor missing')

# Version bump only.
if 'versionCode 88' in g:g=g.replace('versionCode 88','versionCode 89',1)
elif 'versionCode 89' not in g:raise SystemExit('v0869 versionCode anchor missing')
if "versionName '0.8.68'" in g:g=g.replace("versionName '0.8.68'","versionName '0.8.69'",1)
elif "versionName '0.8.69'" not in g:raise SystemExit('v0869 versionName anchor missing')

# Hard safety guards: user asked not to touch these.
for marker in ['RADIUS_KM = 2d','MAX_AGE_MS = 10L * 60L * 1000L']:
    if marker not in w_path.read_text(encoding='utf-8'):raise SystemExit('v0869 river worker safety changed: '+marker)
if 'DEFAULT_RIVER_RADIUS_KM = 2d' not in f_path.read_text(encoding='utf-8'):raise SystemExit('v0869 FCM 2km radius changed')
if 'V0867_SOURCE_CURRENT_NOT_AGE_GATED' not in a:raise SystemExit('v0869 source-current river display regressed')
if 'rain-stations/?latest=true' not in a:raise SystemExit('v0869 official rainfall source loader missing')
if 'WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L' not in r:raise SystemExit('v0869 2-hour digest lock failed')

for x in ['V0869_RIVER_GAUGES_ONLY','V0869_284_GAUGE_ONLY_REFRESH','V0869_NO_RAIN_ONLY_MAP_DOTS','V0869_77_DISTRICT_GAUGE_DETAIL','V0869_GAUGE_PLUS_RAIN_DETAIL','V0869_IMMEDIATE_ALERT_CHECK','V0869_GPS_ALERT_KICK']:
    if x not in a:raise SystemExit('v0869 activity guard failed: '+x)
for x in ['V0869_HIDE_RAIN_ONLY_STATIONS','V0869_NO_RAIN_STATION_TAP','V0869_RIVER_GAUGE_TAP_FIRST']:
    if x not in m:raise SystemExit('v0869 map guard failed: '+x)
if 'V0869_TWO_HOUR_NOTIFICATIONS' not in r:raise SystemExit('v0869 rain notification guard failed')
if 'V0869_BOOT_IMMEDIATE_CHECK' not in b:raise SystemExit('v0869 boot notification guard failed')

# Persist only the intended narrow files.
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');r_path.write_text(r,encoding='utf-8');b_path.write_text(b,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.69 PASS: river gauges only + rainfall detail + 2h/rain alerts + 2km flood alert preserved')
