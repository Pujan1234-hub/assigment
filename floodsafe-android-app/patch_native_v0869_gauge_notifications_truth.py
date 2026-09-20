from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
rain_worker_path=src/'RainAlertWorker.java'
river_worker_path=src/'RiverAlertWorker.java'
g_path=root/'app/build.gradle'

a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
rw=rain_worker_path.read_text(encoding='utf-8')
riverw=river_worker_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.69 is intentionally narrow:
# - map = official river gauges only (no rainfall-only dots)
# - retain the complete official river-gauge inventory, including unavailable gauges
# - all 77 districts stay selectable
# - river/current time mirrors the latest official BIPAD/DHM source with no local display minute gate
# - rainfall remains loaded internally and is shown only inside a safely matched river-gauge detail
# - weather digest checks are due every 2h; rainfall event checks stay frequent
# - 2 km verified river Warning/Danger alert radius remains unchanged


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

# -----------------------------------------------------------------------------
# 1) Rain is source-current data internally, but never a standalone map station.
# -----------------------------------------------------------------------------
sp=method_span(a,'parseRainStation')
if not sp:raise SystemExit('v0869 parseRainStation missing')
block=a[sp[0]:sp[1]]
if 'V0869_RAIN_SOURCE_CURRENT_INTERNAL' not in block:
    # Compatible with the interval-aware v0.8.17 parser.
    if 'mm1=rainAverage(r,1)' in block:
        repl='boolean hasRain=Double.isFinite(mm)||Double.isFinite(mm3)||Double.isFinite(mm6)||Double.isFinite(mm12)||Double.isFinite(mm24); boolean fresh=hasRain&&at>0L; // V0869_RAIN_SOURCE_CURRENT_INTERNAL'
    else:
        repl='boolean hasRain=Double.isFinite(mm); boolean fresh=hasRain&&at>0L; // V0869_RAIN_SOURCE_CURRENT_INTERNAL'
    block,n=re.subn(r'boolean\s+fresh\s*=\s*[^;]+;',repl,block,count=1)
    if n!=1:raise SystemExit('v0869 rain freshness anchor missing')
    a=a[:sp[0]]+block+a[sp[1]:]

a,n=re.subn(r'private\s+static\s+final\s+long\s+RAIN_FRESH_MS\s*=\s*[^;]+;',
            'private static final long RAIN_FRESH_MS=Long.MAX_VALUE; // V0869_NO_RAIN_DISPLAY_AGE_GATE',a,count=1)
if n!=1 and 'V0869_NO_RAIN_DISPLAY_AGE_GATE' not in a:raise SystemExit('v0869 RAIN_FRESH_MS missing')

# Keep rain objects for river-gauge details, but publish ZERO rain-only map markers.
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0869 refreshRainUi missing')
rain_ui=r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        if(map!=null)map.setRainStations(java.util.Collections.emptyList()); // V0869_NO_RAIN_ONLY_MAP_STATIONS
        updateMapHintCounts();
    }
'''
a=a[:sp[0]]+rain_ui+a[sp[1]:]

sp=method_span(a,'updateMapHintCounts')
if not sp:raise SystemExit('v0869 updateMapHintCounts missing')
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 आधिकारिक नदी gauge "+mapRiverCurrent+" / "+mapRiverTotal,
                          "🌊 official river gauges "+mapRiverCurrent+" / "+mapRiverTotal));
    } // V0869_RIVER_GAUGE_HEADER_ONLY
'''
a=a[:sp[0]]+hint+a[sp[1]:]

# Clear all legacy rain marker layers if they exist. Internal rain data is untouched.
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0869 map refreshRainSources missing')
rain_sources=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        String empty=emptyFeatureCollection();
        setGeo("fs-rain-stale",empty);setGeo("fs-rain-normal",empty);setGeo("fs-rain-alert",empty);
        setGeo("fs-rain-warning",empty);setGeo("fs-rain-danger",empty);
    } // V0869_HIDE_RAIN_ONLY_MARKERS
'''
m=m[:sp[0]]+rain_sources+m[sp[1]:]

# Tap priority is river gauge -> actual river. Rainfall-only markers/taps are removed.
sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0869 onMapClick missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){
            if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);
            return true;
        } // V0869_RIVER_GAUGE_TAP_ONLY
        RiverWay r=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(r!=null){showRiver(r,p.getLatitude(),p.getLongitude());return true;}
        return false;
    }
'''
m=m[:sp[0]]+click+m[sp[1]:]

# -----------------------------------------------------------------------------
# 2) Full gauge inventory + 77 districts + current-source truth.
# -----------------------------------------------------------------------------
# District picker is built from the bundled official 77-district geometry, then augmented
# by any source district names. This keeps all districts selectable even when a district
# has no current water-level observation.
sp=method_span(a,'showDistrictPicker')
if not sp:raise SystemExit('v0869 showDistrictPicker missing')
picker=r'''    private void showDistrictPicker(){
        java.util.TreeSet<String> names=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        try{
            JSONObject root=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=root.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){
                JSONObject f=fs.optJSONObject(i),p=f==null?null:f.optJSONObject("properties");if(p==null)continue;
                String n=str(p,"nameEn","NAME_3","DISTRICT","district","name");if(n!=null&&!n.trim().isEmpty())names.add(n.trim());
            }
        }catch(Exception ignored){}
        synchronized(stations){for(RiverStation s:stations){if(s!=null&&s.district!=null&&!s.district.trim().isEmpty()&&!s.district.trim().matches("\\d+"))names.add(s.district.trim());}}
        if(names.isEmpty()){new AlertDialog.Builder(this).setMessage(t("जिल्ला data refresh हुँदैछ।","District data is refreshing.")).setPositiveButton("OK",null).show();return;}
        String[] x=names.toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle(t("जिल्ला छान्नुहोस्","Choose district")).setItems(x,(d,w)->{selectedDistrict=x[w];districtPicker.setText(selectedDistrict+" ▾");refreshRiverUi();}).setNegativeButton(t("बन्द","Close"),null).show();
    } // V0869_ALL_77_DISTRICTS
'''
a=a[:sp[0]]+picker+a[sp[1]:]

# Every official WATER-LEVEL gauge stays on map/list. Latest source membership controls
# green/current status; unavailable catalog gauges remain visible rather than disappearing.
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0869 refreshRiverUi missing')
refresh=r'''    private void refreshRiverUi(){
        if(nearList==null)return;
        List<RiverStation> all;synchronized(stations){all=new ArrayList<>(stations);}
        List<RiverStation> gauges=new ArrayList<>();for(RiverStation s:all)if(v0857WaterLevelStation(s))gauges.add(s);
        gauges.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(gauges,lat,lon);if(map!=null)map.setRainStations(java.util.Collections.emptyList());

        int online=0,current=0,d=0,w=0,al=0,n=0;
        for(RiverStation s:gauges){if(s.online)online++;if(s.fresh){current++;if("danger".equals(s.stage))d++;else if("warning".equals(s.stage))w++;else if("alert".equals(s.stage))al++;else if("normal".equals(s.stage))n++;}}
        int sourceTotal=Math.max(v849CatalogCount,gauges.size());
        mapRiverCurrent=current;mapRiverTotal=sourceTotal;updateMapHintCounts();
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("आधिकारिक नदी gauge: "+sourceTotal+" • अहिले source मा मापन "+current+" • 🟢 "+online+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n,
                "Official river gauges: "+sourceTotal+" • readings in source now "+current+" • 🟢 "+online+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n)); // V0869_FULL_GAUGE_INVENTORY
        updateRisk(gauges);

        nearList.removeAllViews();
        if(!Double.isFinite(lat)||!Double.isFinite(lon)){
            nearSub.setText(t("हालको जीपीएस लिएपछि वास्तविक नजिकका नदी gauge देखिन्छन्।","Get current GPS to show the actual nearest river gauges."));
            nearList.addView(empty(t("◎ मेरो हालको स्थान थिचेर जीपीएस स्थान लिनुहोस्।","Tap My current location to get your GPS position.")));
        }else if(!isNepal(lat,lon)){
            nearSub.setText(t("तपाईं अहिले नेपाल बाहिर हुनुहुन्छ।","You are currently outside Nepal."));
            nearList.addView(empty(t("नेपाल बाहिर हुँदा नजिकका नेपाल नदी gauge देखाइँदैन।","Nearby Nepal river gauges are not shown while you are outside Nepal.")));
        }else{
            nearSub.setText(t("तपाईंको हालको जीपीएसबाट दूरीअनुसार नजिकका आधिकारिक नदी gauge","Official river gauges nearest to your current GPS, sorted by distance"));
            List<RiverStation> near=new ArrayList<>(gauges);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));
            for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));
            if(near.isEmpty())nearList.addView(empty(t("नजिकको आधिकारिक नदी gauge भेटिएन।","No nearby official river gauge was found.")));
        }

        if(nationalList!=null){
            nationalList.removeAllViews();
            if(selectedDistrict.isEmpty()){
                nationalFresh.setText(t("७७ जिल्लामध्ये जिल्ला छानेर सबै आधिकारिक नदी gauge हेर्नुहोस्।","Choose any of 77 districts to view all official river gauges."));
                nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));
            }else{
                int total=0,live=0;
                for(RiverStation s:gauges)if(selectedDistrict.equalsIgnoreCase(s.district)){total++;if(s.fresh)live++;nationalList.addView(stationRow(s));}
                nationalFresh.setText(t(selectedDistrict+": आधिकारिक नदी gauge "+total+" • अहिले source मा मापन "+live,
                        selectedDistrict+": official river gauges "+total+" • readings in source now "+live));
                if(total==0)nationalList.addView(empty(t("यो जिल्लामा catalog मा आधिकारिक नदी gauge भेटिएन।","No official river gauge is listed for this district in the catalog.")));
            }
        }
    } // V0869_ALL_GAUGES_NOT_ONLY_CURRENT
'''
a=a[:sp[0]]+refresh+a[sp[1]:]

# -----------------------------------------------------------------------------
# 3) River-gauge detail = water level + safely matched official rainfall detail.
# -----------------------------------------------------------------------------
helpers=r'''    private static String v869GaugeKey(String s){
        if(s==null)return "";String x=s.toLowerCase(Locale.ROOT);
        x=x.replace("rainfall","").replace("rain gauge","").replace("raingauge","").replace("precipitation","").replace("river","").replace("station","").replace("gauge","").replace("rls","").replace("rain","");
        return x.replaceAll("[^a-z0-9]+","");
    }
    private static double v869Km(double a,double o,double b,double p){double R=6371d,p1=Math.toRadians(a),p2=Math.toRadians(b),dp=Math.toRadians(b-a),dl=Math.toRadians(p-o);double q=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);return 2d*R*Math.atan2(Math.sqrt(q),Math.sqrt(Math.max(0d,1d-q)));}
    private RainStation v869RainForGauge(RiverStation s){
        if(s==null)return null;RainStation best=null;double bd=Double.MAX_VALUE;String sk=v869GaugeKey(s.name);
        synchronized(rainStations){for(RainStation r:rainStations){if(r==null||!r.fresh)continue;double d=v869Km(s.lat,s.lon,r.lat,r.lon);String rk=v869GaugeKey(r.name);boolean strong=!sk.isEmpty()&&!rk.isEmpty()&&(sk.equals(rk)||sk.contains(rk)||rk.contains(sk));boolean safe=d<=0.75d||(strong&&d<=5d);if(safe&&d<bd){bd=d;best=r;}}}
        return best;
    } // V0869_SAFE_RAIN_MATCH
    private void v869AppendRain(StringBuilder b,RiverStation s){
        RainStation r=v869RainForGauge(s);b.append("\n\n").append(t("🌧️ वर्षा विवरण","🌧️ Rainfall detail"));
        if(r==null){b.append("\n").append(t("यस नदी gauge सँग सुरक्षित रूपमा मिल्ने आधिकारिक rainfall reading अहिले उपलब्ध छैन।","No official rainfall reading can currently be safely matched to this river gauge."));return;}
        if(Double.isFinite(r.rainfall))b.append("\n").append(t("१ घण्टा: ","1 hour: ")).append(String.format(Locale.US,"%.1f mm",r.rainfall));
        if(Double.isFinite(r.rain3))b.append("\n").append(t("३ घण्टा: ","3 hours: ")).append(String.format(Locale.US,"%.1f mm",r.rain3));
        if(Double.isFinite(r.rain6))b.append("\n").append(t("६ घण्टा: ","6 hours: ")).append(String.format(Locale.US,"%.1f mm",r.rain6));
        if(Double.isFinite(r.rain12))b.append("\n").append(t("१२ घण्टा: ","12 hours: ")).append(String.format(Locale.US,"%.1f mm",r.rain12));
        if(Double.isFinite(r.rain24))b.append("\n").append(t("२४ घण्टा: ","24 hours: ")).append(String.format(Locale.US,"%.1f mm",r.rain24));
        b.append("\n").append(t("Rain source time: ","Rain source time: ")).append(v848Time(r.at));
        b.append("\n").append(t("Rain source: BIPAD/DHM official","Rain source: official BIPAD/DHM"));
    }

'''
if 'V0869_SAFE_RAIN_MATCH' not in a:
    anchor='    private void showStation(RiverStation s)'
    if anchor not in a:raise SystemExit('v0869 showStation helper anchor missing')
    a=a.replace(anchor,helpers+anchor,1)

sp=method_span(a,'showStation')
if not sp:raise SystemExit('v0869 showStation missing')
station_detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;boolean hasReading=Double.isFinite(s.level)&&s.at>0L;
        StringBuilder b=new StringBuilder();
        b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("पछिल्लो आधिकारिक स्रोतमा उपलब्ध","Available in latest official source"):t("पछिल्लो आधिकारिक स्रोतमा उपलब्ध छैन","Not in latest official source"));
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);
        if(hasReading){
            b.append("\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage));
            b.append("\n\n").append(t("आधिकारिक पानीको सतह: ","Official water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
            b.append("\n").append(t("स्रोतको मापन समय: ","Official measurement time: ")).append(v848Time(s.at));
            b.append("\n").append(t("स्रोत समयदेखि: ","Source age: ")).append(v850Age(s.at));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
        }else b.append("\n\n").append(t("आधिकारिक पानी-सतह/मापन समय अहिले उपलब्ध छैन।","Official water level/measurement time is not currently available."));
        v869AppendRain(b,s);
        b.append("\n\n").append(t("🌊 नदी source: BIPAD/DHM आधिकारिक — source मा जस्तो value/time छ त्यही देखाइन्छ।","🌊 River source: official BIPAD/DHM — the app shows the value/time supplied by the source."));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0869_GAUGE_WATER_AND_RAIN_DETAIL
'''
a=a[:sp[0]]+station_detail+a[sp[1]:]

# -----------------------------------------------------------------------------
# 4) Notification reliability: 2h digest due-time, frequent rain event checks, and
#    foreground monitoring starts from the native launcher when location is available.
# -----------------------------------------------------------------------------
rw,n=re.subn(r'private static final long WEATHER_DIGEST_INTERVAL_MS\s*=\s*3L\s*\*\s*60L\s*\*\s*60L\s*\*\s*1000L;',
             'private static final long WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L; // V0869_TWO_HOUR_DIGEST',rw,count=1)
if n!=1 and 'V0869_TWO_HOUR_DIGEST' not in rw:raise SystemExit('v0869 weather digest interval anchor missing')

# Weather/rain events may use the last device fix for up to 6h so Android doze or a killed
# foreground service does not silently suppress the 2h digest. River 2km safety keeps its
# own strict fresh-device-location rule in RiverAlertWorker.
old='''        if (prefs.getBoolean("follow_device", false)) {
            long locationTime = prefs.getLong("location_time", 0L);
            if (!MonitoringLocationPolicy.freshDeviceLocation(
                    locationTime, System.currentTimeMillis(), lat, lon)) return Result.success();
        }'''
new='''        if (prefs.getBoolean("follow_device", false)) {
            long locationTime=prefs.getLong("location_time",0L), nowMs=System.currentTimeMillis();
            long age=nowMs-locationTime;
            if(locationTime<=0L||age<-(5L*60L*1000L)||age>6L*60L*60L*1000L)return Result.success();
        } // V0869_WEATHER_LOCATION_RESILIENCE'''
if old in rw:rw=rw.replace(old,new,1)
elif 'V0869_WEATHER_LOCATION_RESILIENCE' not in rw:raise SystemExit('v0869 RainAlertWorker location anchor missing')

# Native activity previously scheduled periodic work but did not kick off an immediate check
# or the existing foreground monitor service. Add only those missing pieces.
sp=method_span(a,'enableMonitoring')
if not sp:raise SystemExit('v0869 enableMonitoring missing')
enable=r'''    private void enableMonitoring(){
        getSharedPreferences(RainAlertWorker.PREFS,MODE_PRIVATE).edit().putBoolean("enabled",true).apply();
        Constraints c=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();WorkManager wm=WorkManager.getInstance(getApplicationContext());
        wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RainAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());
        wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",ExistingPeriodicWorkPolicy.UPDATE,new PeriodicWorkRequest.Builder(RiverAlertWorker.class,15,TimeUnit.MINUTES).setConstraints(c).build());
        androidx.work.OneTimeWorkRequest rainNow=new androidx.work.OneTimeWorkRequest.Builder(RainAlertWorker.class).setConstraints(c).build();
        androidx.work.OneTimeWorkRequest riverNow=new androidx.work.OneTimeWorkRequest.Builder(RiverAlertWorker.class).setConstraints(c).build();
        wm.enqueueUniqueWork("floodsafe-native-rain-now",androidx.work.ExistingWorkPolicy.REPLACE,rainNow);
        wm.enqueueUniqueWork("floodsafe-native-river-now",androidx.work.ExistingWorkPolicy.REPLACE,riverNow); // V0869_IMMEDIATE_ALERT_CHECKS
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        if(hasLocationPermission())try{FloodMonitorService.start(this);}catch(Exception ignored){} // V0869_START_MONITOR_SERVICE
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},REQ_NOTIFY);
    }
'''
a=a[:sp[0]]+enable+a[sp[1]:]

# Start/refresh the monitor service as soon as a real location arrives.
if 'V0869_LOCATION_STARTS_MONITOR' not in a:
    needle='.putBoolean("location_stale",false).putBoolean("enabled",true).apply();'
    if needle not in a:raise SystemExit('v0869 onLocationChanged prefs anchor missing')
    a=a.replace(needle,needle+'try{FloodMonitorService.start(this);}catch(Exception ignored){} // V0869_LOCATION_STARTS_MONITOR',1)

# Keep river alert radius and safety thresholds exactly as requested.
if 'RADIUS_KM = 2d' not in riverw:raise SystemExit('v0869 2 km RiverAlertWorker radius missing')

# Release identity. We build directly from the known-good v0.8.67 chain and intentionally
# skip the unwanted v0.8.68 rain-marker UI.
if 'versionCode 87' in g:g=g.replace('versionCode 87','versionCode 89',1)
elif 'versionCode 89' not in g:raise SystemExit('v0869 versionCode anchor missing')
if "versionName '0.8.67'" in g:g=g.replace("versionName '0.8.67'","versionName '0.8.69'",1)
elif "versionName '0.8.69'" not in g:raise SystemExit('v0869 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');rain_worker_path.write_text(rw,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0869_NO_RAIN_ONLY_MAP_STATIONS','V0869_RIVER_GAUGE_HEADER_ONLY','V0869_ALL_77_DISTRICTS','V0869_FULL_GAUGE_INVENTORY','V0869_ALL_GAUGES_NOT_ONLY_CURRENT','V0869_SAFE_RAIN_MATCH','V0869_GAUGE_WATER_AND_RAIN_DETAIL','V0869_IMMEDIATE_ALERT_CHECKS','V0869_START_MONITOR_SERVICE','V0869_LOCATION_STARTS_MONITOR','V0867_SOURCE_CURRENT_NOT_AGE_GATED']:
    if x not in a:raise SystemExit('v0869 activity verification failed: '+x)
for x in ['V0869_HIDE_RAIN_ONLY_MARKERS','V0869_RIVER_GAUGE_TAP_ONLY']:
    if x not in m:raise SystemExit('v0869 map verification failed: '+x)
for x in ['V0869_TWO_HOUR_DIGEST','V0869_WEATHER_LOCATION_RESILIENCE']:
    if x not in rw:raise SystemExit('v0869 rain worker verification failed: '+x)
if 'RADIUS_KM = 2d' not in riverw:raise SystemExit('v0869 river 2km alert changed')
for x in ['versionCode 89',"versionName '0.8.69'"]:
    if x not in g:raise SystemExit('v0869 version verification failed: '+x)
print('FloodSafe v0.8.69 PASS: 284-style full official river gauge inventory + no rain-only map dots + 77 districts + source-time gauge/rain detail + 2h digest + 2km alerts preserved')
