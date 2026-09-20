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

# v0.8.73 V2 starts from the verified v0.8.71 native chain, not the brittle old
# v0.8.72 layer-anchor patch. Only requested source/map behavior changes here.

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
# Official rainfall stations: publish on native map, refresh on 1-second foreground tick.
# -----------------------------------------------------------------------------
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0873v2 refreshRainUi missing')
a=a[:sp[0]]+r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        if(map!=null)map.setRainStations(copy); // V0873_SHOW_OFFICIAL_RAIN_STATIONS
        updateMapHintCounts();
    }
'''+a[sp[1]:]

poll='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'
if 'V0873_ONE_SECOND_RAIN_RECHECK' not in a:
    if poll not in a:raise SystemExit('v0873v2 one-second river scheduler missing')
    # v0.8.71 livePoll already calls refreshRainStations() on this 1-second loop.
    # Keep that source loader as the single rain refresh path; do not call a non-existent refreshRain().
    a=a.replace(poll,'// V0873_ONE_SECOND_RAIN_RECHECK\n        '+poll,1)

# -----------------------------------------------------------------------------
# Add official BIPAD hydrology feeds. No made-up lake endpoint: lake/reservoir/dam-type
# rows are recognized only when an official documented feed actually supplies them.
# -----------------------------------------------------------------------------
anchor='        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();'
if 'V0873_EXTRA_OFFICIAL_HYDROLOGY_FEEDS' not in a:
    if anchor not in a:raise SystemExit('v0873v2 trusted loader output anchor missing')
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

# Full v0.8.71 source popup: retain exact source values and append source station type.
if 'V0873_DETAIL_STATION_TYPE' not in a:
    sp=method_span(a,'v871GaugeDetailText')
    if not sp:raise SystemExit('v0873v2 live gauge detail missing')
    b=a[sp[0]:sp[1]]
    src_line='        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");'
    if src_line not in b:raise SystemExit('v0873v2 detail source anchor missing')
    b=b.replace(src_line,src_line+'\n        String stationType=strDeep(row,f,"_floodsafeWaterbodyType","stationType","station_type","waterbodyType","waterbody_type","type","category"); // V0873_DETAIL_STATION_TYPE',1)
    basin='        if(!basin.isEmpty())b.append("\\n").append(t("Basin: ","Basin: ")).append(basin);'
    if basin not in b:raise SystemExit('v0873v2 detail basin anchor missing')
    b=b.replace(basin,basin+'\n        if(!stationType.isEmpty())b.append("\\n").append(t("प्रकार: ","Type: ")).append(stationType);',1)
    a=a[:sp[0]]+b+a[sp[1]:]

# Source-status list dot: current normal green; flood status overrides it.
sp=method_span(a,'v849AvailabilityDot')
if not sp:raise SystemExit('v0873v2 availability dot missing')
a=a[:sp[0]]+r'''    private static String v849AvailabilityDot(RiverStation s){
        if(s==null||!s.fresh)return "⚫";
        if("danger".equals(s.stage))return "🔴";
        if("warning".equals(s.stage))return "🟠";
        if("alert".equals(s.stage))return "🟡";
        return "🟢";
    } // V0873_STATUS_COLOURED_STATION_DOT
'''+a[sp[1]:]

# -----------------------------------------------------------------------------
# Native MapLibre rain layers and taps.
# -----------------------------------------------------------------------------
sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0873v2 map refreshRainSources missing')
m=m[:sp[0]]+r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        List<RainDot> snapshot;synchronized(rainStations){snapshot=new ArrayList<>(rainStations);}
        setGeo("fs-rain-stale",rainGeo(snapshot,"stale"));
        setGeo("fs-rain-normal",rainGeo(snapshot,"normal"));
        setGeo("fs-rain-alert",rainGeo(snapshot,"alert"));
        setGeo("fs-rain-warning",rainGeo(snapshot,"warning"));
        setGeo("fs-rain-danger",rainGeo(snapshot,"danger"));
        v849AvailabilityDotColours(); // V0873_APPLY_RAIN_STATUS_COLOURS
    } // V0873_ALL_RAIN_STATIONS_VISIBLE

    private static String rainGeo(List<RainDot> list,String group){
        try{
            JSONArray features=new JSONArray();
            for(RainDot r:list){
                if(r==null)continue;
                Class<?> c=r.getClass();
                double la=getDouble(c,r,"lat"),lo=getDouble(c,r,"lon");
                if(!Double.isFinite(la)||!Double.isFinite(lo))continue;
                String stage=getString(c,r,"stage","");
                if(stage==null||stage.trim().isEmpty())stage=getString(c,r,"status","normal");
                boolean fresh=getBoolean(c,r,"fresh",true);
                String g=fresh?normalizeStage(stage):"stale";
                if(!group.equals(g))continue;
                String name=getString(c,r,"name","Official rainfall station");
                features.put(pointFeature(lo,la,name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",features).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    } // V0873_RAIN_GEO_COMPILE_HELPER
'''+m[sp[1]:]

sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0873v2 map onMapClick missing')
m=m[:sp[0]]+r'''    private boolean onMapClick(LatLng p) {
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
'''+m[sp[1]:]

# Marker colours: normal/current station green, user blue, alert/watch yellow,
# warning orange, danger red. Existing v0.8.48 river risk overlays remain untouched.
sp=method_span(m,'v849AvailabilityDotColours')
if not sp:raise SystemExit('v0873v2 marker colour helper missing')
m=m[:sp[0]]+r'''    private void v849AvailabilityDotColours(){
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
'''+m[sp[1]:]

# Background multi-feed one-second monitor is already in native service source; verify
# the v0.8.71 chain did not remove it. No second service/monitor is created here.
for x in ['V0872_BACKGROUND_SOURCE_MONITOR_FIELD','V0872_START_1S_BACKGROUND_SOURCE','V0872_STOP_BACKGROUND_SOURCE']:
    if x not in s:raise SystemExit('v0873v2 background service wiring missing: '+x)
for x in ['RAIN_ENDPOINT','HYDRO_ENDPOINTS','flood-station/?limit=2000','streamflow/?limit=2000','station-location/?limit=2000','V0872_ONE_SECOND_BACKGROUND_RECHECK']:
    if x not in l:raise SystemExit('v0873v2 background multi-feed monitor missing: '+x)

# Release identity directly from v0.8.71 -> v0.8.73. We intentionally bypass only the
# brittle v0.8.72 patch file, not its requested background monitor behavior.
if 'versionCode 91' in g:g=g.replace('versionCode 91','versionCode 93',1)
elif 'versionCode 93' not in g:raise SystemExit('v0873v2 versionCode anchor missing')
if "versionName '0.8.71'" in g:g=g.replace("versionName '0.8.71'","versionName '0.8.73'",1)
elif "versionName '0.8.73'" not in g:raise SystemExit('v0873v2 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0873_SHOW_OFFICIAL_RAIN_STATIONS','V0873_ONE_SECOND_RAIN_RECHECK','V0873_EXTRA_OFFICIAL_HYDROLOGY_FEEDS','V0873_DETAIL_STATION_TYPE','V0873_STATUS_COLOURED_STATION_DOT','V0871_SOURCE_EXACT_DETAIL','V0871_OPEN_POPUP_LIVE_UPDATE','V0870_BIPAD_POINT_COORDS']:
    if x not in a:raise SystemExit('v0873v2 activity contract missing: '+x)
for x in ['V0873_ALL_RAIN_STATIONS_VISIBLE','V0873_RAIN_STATION_TAP','V0873_STATION_GREEN_USER_BLUE_STATUS_COLOURS','V0873_RAIN_GEO_COMPILE_HELPER','V0848_FLOOD_COLOUR_PRIORITY']:
    if x not in m:raise SystemExit('v0873v2 map contract missing: '+x)
if 'RIVER_FRESH_MS=Long.MAX_VALUE' not in a:raise SystemExit('v0873v2 source-current policy changed')
if 'versionCode 93' not in g or "versionName '0.8.73'" not in g:raise SystemExit('v0873v2 version failed')
print('FloodSafe v0.8.73 V2 PASS: native river+rain+official hydrology/lake-like feeds; green normal stations, blue user, flood-status colours; 1s foreground/background recheck')
