from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
s_path=src/'FloodMonitorService.java'
l_path=src/'FloodLiveGaugeMonitor.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
s=s_path.read_text(encoding='utf-8')
l=l_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.73 is deliberately narrow. It keeps the complete v0.8.72 native app intact and
# changes only official hydrology/rain station visibility + colour/source parity:
# normal/current station = green, current user = blue, alert/watch = yellow,
# warning = orange, danger = red. River, rain and public BIPAD hydrology/flood/streamflow
# rows recheck without screen reload. BIPAD's public API has no separate lake-stations
# resource, so lake/reservoir/dam-like official rows are accepted from the documented
# water-level/hydrology resources rather than fabricated.


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

# 1) Show official rainfall stations on the native map again. Internal rain parsing was
# already preserved by v0.8.69; only the map publication had been intentionally hidden.
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0873 refreshRainUi missing')
rain_ui=r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        if(map!=null)map.setRainStations(copy); // V0873_SHOW_OFFICIAL_RAIN_STATIONS
        updateMapHintCounts();
    }
'''
a=a[:sp[0]]+rain_ui+a[sp[1]:]

# Recheck rainfall on the same one-second foreground scheduler used by v0.8.71 river data.
poll='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'
if 'V0873_ONE_SECOND_RAIN_RECHECK' not in a:
    if poll not in a:raise SystemExit('v0873 one-second river scheduler missing')
    a=a.replace(poll,'refreshRain(); // V0873_ONE_SECOND_RAIN_RECHECK\n        '+poll,1)

# 2) Merge usable live observations from the other public BIPAD hydrology resources.
# Metadata-only station rows are ignored. Existing river-stations latest/direct DHM rows win
# unless one of these official rows has a newer source timestamp.
anchor='        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();'
if 'V0873_EXTRA_OFFICIAL_HYDROLOGY_FEEDS' not in a:
    if anchor not in a:raise SystemExit('v0873 V0862 loader output anchor missing')
    extra=r'''        String[] v873HydroPaths={"flood-station/?limit=2000","streamflow/?limit=2000","station-location/?limit=2000"};
        for(String path:v873HydroPaths){
            try{
                JSONArray extraRows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<extraRows.length();i++){
                    JSONObject live=extraRows.optJSONObject(i);if(live==null)continue;JSONObject lf=live.optJSONObject("fields");
                    double level=numDeep(live,lf,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");
                    long at=trustedRowTime(live);if(!Double.isFinite(level)||at<=0L)continue;
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
        } // V0873_EXTRA_OFFICIAL_HYDROLOGY_FEEDS

'''
    a=a.replace(anchor,extra+anchor,1)

# Add the source-provided station/waterbody type to the existing v0.8.72 full live detail.
if 'V0873_DETAIL_STATION_TYPE' not in a:
    sp=method_span(a,'v871GaugeDetailText')
    if not sp:raise SystemExit('v0873 v871GaugeDetailText missing')
    b=a[sp[0]:sp[1]]
    src_line='        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");'
    if src_line not in b:raise SystemExit('v0873 detail source anchor missing')
    b=b.replace(src_line,src_line+'\n        String stationType=strDeep(row,f,"_floodsafeWaterbodyType","stationType","station_type","waterbodyType","waterbody_type","type","category"); // V0873_DETAIL_STATION_TYPE',1)
    basin='        if(!basin.isEmpty())b.append("\\n").append(t("Basin: ","Basin: ")).append(basin);'
    if basin not in b:raise SystemExit('v0873 detail basin anchor missing')
    b=b.replace(basin,basin+'\n        if(!stationType.isEmpty())b.append("\\n").append(t("प्रकार: ","Type: ")).append(stationType);',1)
    a=a[:sp[0]]+b+a[sp[1]:]

# Status-coloured list dot: normal green, alert yellow, warning orange, danger red.
sp=method_span(a,'v849AvailabilityDot')
if not sp:raise SystemExit('v0873 v849AvailabilityDot missing')
avail=r'''    private static String v849AvailabilityDot(RiverStation s){
        if(s==null||!s.fresh)return "⚫";
        if("danger".equals(s.stage))return "🔴";
        if("warning".equals(s.stage))return "🟠";
        if("alert".equals(s.stage))return "🟡";
        return "🟢";
    } // V0873_STATUS_COLOURED_STATION_DOT
'''
a=a[:sp[0]]+avail+a[sp[1]:]

# 3) Publish every official rainfall point to MapLibre and keep it tappable.
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0873 map refreshRainSources missing')
rain_sources=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        List<RainDot> snapshot;synchronized(rainStations){snapshot=new ArrayList<>(rainStations);}
        setGeo("fs-rain-stale",rainGeo(snapshot,"stale"));
        setGeo("fs-rain-normal",rainGeo(snapshot,"normal"));
        setGeo("fs-rain-alert",rainGeo(snapshot,"alert"));
        setGeo("fs-rain-warning",rainGeo(snapshot,"warning"));
        setGeo("fs-rain-danger",rainGeo(snapshot,"danger"));
        v849AvailabilityDotColours(); // V0873_APPLY_RAIN_STATUS_COLOURS
    } // V0873_ALL_RAIN_STATIONS_VISIBLE
'''
m=m[:sp[0]]+rain_sources+m[sp[1]:]

sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0873 map onMapClick missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}
        RainDot rain=nearestRain(p.getLatitude(),p.getLongitude());
        double rainThreshold=Math.max(0.20,Math.min(2.2,1.8/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double rd=rain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),rain.lat,rain.lon);
        if(rain!=null&&rd<=rainThreshold){showRain(rain);return true;} // V0873_RAIN_STATION_TAP
        RiverWay r=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(r!=null){showRiver(r,p.getLatitude(),p.getLongitude());return true;}
        return false;
    }
'''
m=m[:sp[0]]+click+m[sp[1]:]

# Source-status marker palette. The user/current-location layer remains explicitly blue.
sp=method_span(m,'v849AvailabilityDotColours')
if not sp:raise SystemExit('v0873 map v849AvailabilityDotColours missing')
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
    } // V0873_STATION_GREEN_USER_BLUE_STATUS_COLOURS
'''
m=m[:sp[0]]+colours+m[sp[1]:]

# 4) Guard the already-wired background monitor: it must now fetch river + rain +
# public hydrology resources on the one-second scheduler. Do not create a second service.
for x in ['V0872_BACKGROUND_SOURCE_MONITOR_FIELD','V0872_START_1S_BACKGROUND_SOURCE','V0872_STOP_BACKGROUND_SOURCE']:
    if x not in s:raise SystemExit('v0873 background service wiring missing: '+x)
for x in ['RAIN_ENDPOINT','HYDRO_ENDPOINTS','flood-station/?limit=2000','streamflow/?limit=2000','station-location/?limit=2000','V0872_ONE_SECOND_BACKGROUND_RECHECK']:
    if x not in l:raise SystemExit('v0873 multi-feed background monitor missing: '+x)

# Release identity only.
if 'versionCode 92' in g:g=g.replace('versionCode 92','versionCode 93',1)
elif 'versionCode 93' not in g:raise SystemExit('v0873 versionCode anchor missing')
if "versionName '0.8.72'" in g:g=g.replace("versionName '0.8.72'","versionName '0.8.73'",1)
elif "versionName '0.8.73'" not in g:raise SystemExit('v0873 versionName anchor missing')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

for x in ['V0873_SHOW_OFFICIAL_RAIN_STATIONS','V0873_ONE_SECOND_RAIN_RECHECK','V0873_EXTRA_OFFICIAL_HYDROLOGY_FEEDS','V0873_DETAIL_STATION_TYPE','V0873_STATUS_COLOURED_STATION_DOT','V0872_EXACT_LEVEL_DETAIL','V0871_SOURCE_EXACT_DETAIL']:
    if x not in a:raise SystemExit('v0873 activity guard failed: '+x)
for x in ['V0873_ALL_RAIN_STATIONS_VISIBLE','V0873_RAIN_STATION_TAP','V0873_STATION_GREEN_USER_BLUE_STATUS_COLOURS','V0872_RIVER_STATUS_COLOUR_LAYERS']:
    if x not in m:raise SystemExit('v0873 map guard failed: '+x)
for x in ['versionCode 93',"versionName '0.8.73'"]:
    if x not in g:raise SystemExit('v0873 version guard failed: '+x)
print('FloodSafe v0.8.73 PASS: native official river+rain+hydrology/lake-like stations, green normal station, blue user, source-status colours, one-second foreground/background recheck')
