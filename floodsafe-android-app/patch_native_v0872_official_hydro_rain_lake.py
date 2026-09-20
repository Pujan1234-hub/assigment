from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
s_path=src/'FloodMonitorService.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
s=s_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.72 is deliberately narrow and builds on the known-good v0.8.70/v0.8.71 native chain:
# - river + rainfall + official hydrology/flood/streamflow station rows are live
# - no WebView UI conversion, no news/SATHI/language/layout rewrite
# - normal/current station dots = green, current user = blue
# - alert/watch = yellow, warning = orange, danger = red
# - foreground river + rain recheck request every second; background foreground-service
#   rechecker is wired through FloodLiveGaugeMonitor
# - public BIPAD does not expose a separate `lake-stations` resource; lake/reservoir-like
#   official rows are accepted from the documented hydrology/flood/streamflow/station feeds


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
# 1) Native activity: keep official rain stations visible and recheck rain each second.
# -----------------------------------------------------------------------------
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0872 refreshRainUi missing')
rain_ui=r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        if(map!=null)map.setRainStations(copy); // V0872_SHOW_OFFICIAL_RAIN_STATIONS
        updateMapHintCounts();
    }
'''
a=a[:sp[0]]+rain_ui+a[sp[1]:]

poll='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'
if 'V0872_ONE_SECOND_RAIN_RECHECK' not in a:
    if poll not in a:raise SystemExit('v0872 v0871 one-second foreground poll anchor missing')
    a=a.replace(poll,'refreshRain(); // V0872_ONE_SECOND_RAIN_RECHECK\n        '+poll,1)

# -----------------------------------------------------------------------------
# 2) Merge any usable official water-level row from BIPAD flood/streamflow/location feeds.
#    This catches official lake/reservoir/dam-type hydrology stations without inventing a
#    non-existent lake API. Metadata-only rows are ignored by the live map.
# -----------------------------------------------------------------------------
anchor='        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();'
if 'V0872_EXTRA_OFFICIAL_HYDROLOGY_FEEDS' not in a:
    if anchor not in a:raise SystemExit('v0872 V0862 output anchor missing')
    extra=r'''        String[] v872HydroPaths={"flood-station/?limit=2000","streamflow/?limit=2000","station-location/?limit=2000"};
        for(String path:v872HydroPaths){
            try{
                JSONArray extraRows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<extraRows.length();i++){
                    JSONObject live=extraRows.optJSONObject(i);if(live==null)continue;JSONObject lf=live.optJSONObject("fields");
                    double level=numDeep(live,lf,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");
                    long at=trustedRowTime(live);if(!Double.isFinite(level)||at<=0L)continue; // realtime observation only
                    String ix=v846StationIndex(live),nm=v846StationName(live),key=v862FinalKey(ix,nm);if(key.isEmpty())continue;
                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
                    JSONObject row=v862FinalMetaOnly(meta,live);
                    try{
                        row.put("_floodsafeOnline",true);row.put("_floodsafeSource","BIPAD "+path);
                        String kind=strDeep(live,lf,"stationType","station_type","type","category","waterbodyType","waterbody_type");
                        String desc=strDeep(live,lf,"description","stationDescription","station_description");
                        String hay=(nm+" "+kind+" "+desc).toLowerCase(Locale.ROOT);
                        if(hay.contains("lake")||hay.contains("reservoir")||hay.contains("dam")||hay.contains("glacial")||hay.contains("tal")||hay.contains("ताल"))row.put("_floodsafeWaterbodyType","lake/reservoir");
                    }catch(Exception ignored){}
                    JSONObject old=current.get(key);long oldAt=old==null?0L:trustedRowTime(old);
                    if(old==null||at>oldAt)current.put(key,row);
                }
            }catch(Exception ignored){}
        } // V0872_EXTRA_OFFICIAL_HYDROLOGY_FEEDS

'''
    a=a.replace(anchor,extra+anchor,1)

# Add source type to the already-live v0.8.71 detail without changing the rest of the dialog.
if 'V0872_DETAIL_STATION_TYPE' not in a:
    sp=method_span(a,'v871GaugeDetailText')
    if not sp:raise SystemExit('v0872 v871GaugeDetailText missing')
    b=a[sp[0]:sp[1]]
    src_line='        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");'
    if src_line not in b:raise SystemExit('v0872 detail source anchor missing')
    b=b.replace(src_line,src_line+'\n        String stationType=strDeep(row,f,"_floodsafeWaterbodyType","stationType","station_type","waterbodyType","waterbody_type","type","category"); // V0872_DETAIL_STATION_TYPE',1)
    basin='        if(!basin.isEmpty())b.append("\\n").append(t("Basin: ","Basin: ")).append(basin);'
    if basin not in b:raise SystemExit('v0872 detail basin anchor missing')
    b=b.replace(basin,basin+'\n        if(!stationType.isEmpty())b.append("\\n").append(t("प्रकार: ","Type: ")).append(stationType);',1)
    a=a[:sp[0]]+b+a[sp[1]:]

# -----------------------------------------------------------------------------
# 3) Native MapLibre map: all official rain dots visible, tap-enabled, source-status colours.
# -----------------------------------------------------------------------------
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0872 map refreshRainSources missing')
rain_sources=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        List<RainDot> snapshot;synchronized(rainStations){snapshot=new ArrayList<>(rainStations);}
        setGeo("fs-rain-stale",rainGeo(snapshot,"stale"));
        setGeo("fs-rain-normal",rainGeo(snapshot,"normal"));
        setGeo("fs-rain-alert",rainGeo(snapshot,"alert"));
        setGeo("fs-rain-warning",rainGeo(snapshot,"warning"));
        setGeo("fs-rain-danger",rainGeo(snapshot,"danger"));
        v849AvailabilityDotColours(); // V0872_APPLY_RAIN_STATUS_COLOURS
    } // V0872_ALL_RAIN_STATIONS_VISIBLE
'''
m=m[:sp[0]]+rain_sources+m[sp[1]:]

sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0872 map onMapClick missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}
        RainDot rain=nearestRain(p.getLatitude(),p.getLongitude());
        double rainThreshold=Math.max(0.20,Math.min(2.2,1.8/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double rd=rain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),rain.lat,rain.lon);
        if(rain!=null&&rd<=rainThreshold){showRain(rain);return true;} // V0872_RAIN_STATION_TAP
        RiverWay r=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(r!=null){showRiver(r,p.getLatitude(),p.getLongitude());return true;}
        return false;
    }
'''
m=m[:sp[0]]+click+m[sp[1]:]

sp=method_span(m,'v849AvailabilityDotColours')
if not sp:raise SystemExit('v0872 map v849AvailabilityDotColours missing')
colours=r'''    private void v849AvailabilityDotColours(){
        if(!styleReady||style==null)return;
        try{CircleLayer x=style.getLayerAs("fs-stale-layer");if(x!=null)x.setProperties(circleColor("#64748B"),circleOpacity(1.0f),circleRadius(4.8f));}catch(Exception ignored){}
        String[] stationIds={"fs-normal-layer","fs-alert-layer","fs-warning-layer","fs-danger-layer"};
        String[] stationColours={"#16A34A","#FFD447","#FF9418","#F04444"};
        for(int i=0;i<stationIds.length;i++)try{CircleLayer x=style.getLayerAs(stationIds[i]);if(x!=null)x.setProperties(circleColor(stationColours[i]),circleOpacity(1.0f),circleRadius(5.1f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-rain-stale-layer");if(x!=null)x.setProperties(circleColor("#64748B"),circleOpacity(0.95f),circleRadius(4.4f));}catch(Exception ignored){}
        String[] rainIds={"fs-rain-normal-layer","fs-rain-alert-layer","fs-rain-warning-layer","fs-rain-danger-layer"};
        String[] rainColours={"#16A34A","#FFD447","#FF9418","#F04444"};
        for(int i=0;i<rainIds.length;i++)try{CircleLayer x=style.getLayerAs(rainIds[i]);if(x!=null)x.setProperties(circleColor(rainColours[i]),circleOpacity(0.98f),circleRadius(4.7f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-user-layer");if(x!=null)x.setProperties(circleColor("#0B7FD0"),circleOpacity(1.0f));}catch(Exception ignored){}
    } // V0872_STATION_GREEN_USER_BLUE_STATUS_COLOURS
'''
m=m[:sp[0]]+colours+m[sp[1]:]

# -----------------------------------------------------------------------------
# 4) Ensure the existing native foreground service owns the background 1-second monitor.
# -----------------------------------------------------------------------------
if 'V0872_BACKGROUND_HYDRO_MONITOR' not in s:
    fld='    private boolean updatesStarted;'
    if fld not in s:raise SystemExit('v0872 service field anchor missing')
    s=s.replace(fld,fld+'\n    private FloodLiveGaugeMonitor liveHydrologyMonitor; // V0872_BACKGROUND_HYDRO_MONITOR',1)
if 'liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);' not in s:
    q='        locationManager = getSystemService(LocationManager.class);'
    if q not in s:raise SystemExit('v0872 service onCreate anchor missing')
    s=s.replace(q,q+'\n        liveHydrologyMonitor = new FloodLiveGaugeMonitor(this);',1)
if 'V0872_START_ONE_SECOND_HYDRO' not in s:
    q='        startLocationUpdates();'
    if q not in s:raise SystemExit('v0872 service start anchor missing')
    s=s.replace(q,q+'\n        if(liveHydrologyMonitor!=null)liveHydrologyMonitor.start(); // V0872_START_ONE_SECOND_HYDRO',1)
if 'liveHydrologyMonitor.stop()' not in s:
    q='    @Override public void onDestroy() {'
    if q not in s:raise SystemExit('v0872 service destroy anchor missing')
    s=s.replace(q,q+'\n        if(liveHydrologyMonitor!=null){try{liveHydrologyMonitor.stop();}catch(RuntimeException ignored){}liveHydrologyMonitor=null;}',1)

# Release identity only; no other feature/version chain changes.
if 'versionCode 91' in g:g=g.replace('versionCode 91','versionCode 92',1)
elif 'versionCode 92' not in g:raise SystemExit('v0872 versionCode anchor missing')
if "versionName '0.8.71'" in g:g=g.replace("versionName '0.8.71'","versionName '0.8.72'",1)
elif "versionName '0.8.72'" not in g:raise SystemExit('v0872 versionName anchor missing')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
s_path.write_text(s,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

for x in ['V0872_SHOW_OFFICIAL_RAIN_STATIONS','V0872_ONE_SECOND_RAIN_RECHECK','V0872_EXTRA_OFFICIAL_HYDROLOGY_FEEDS','V0872_DETAIL_STATION_TYPE','V0871_SOURCE_EXACT_DETAIL','V0871_ONE_SECOND_SOURCE_RECHECK','V0870_BIPAD_POINT_COORDS']:
    if x not in a:raise SystemExit('v0872 activity guard failed: '+x)
for x in ['V0872_ALL_RAIN_STATIONS_VISIBLE','V0872_RAIN_STATION_TAP','V0872_STATION_GREEN_USER_BLUE_STATUS_COLOURS','V0848_FLOOD_COLOUR_PRIORITY']:
    if x not in m:raise SystemExit('v0872 map guard failed: '+x)
for x in ['V0872_BACKGROUND_HYDRO_MONITOR','V0872_START_ONE_SECOND_HYDRO']:
    if x not in s:raise SystemExit('v0872 service guard failed: '+x)
for x in ['versionCode 92',"versionName '0.8.72'"]:
    if x not in g:raise SystemExit('v0872 version guard failed: '+x)
print('FloodSafe v0.8.72 PASS: native river+rain+official hydrology/lake-like station parity, green normal stations, blue user, source-status colours, 1s foreground/background recheck')
