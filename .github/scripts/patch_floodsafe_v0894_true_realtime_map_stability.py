from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start()); d=0; quote=None; esc=False
    for i in range(op,len(text)):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':d+=1
            elif ch=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def replace_method(text,name,block):
    s=span(text,name)
    if not s:raise SystemExit('v0894 method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]

# -----------------------------------------------------------------------------
# REALTIME SOURCE FIX
# The station catalogue can contain an embedded old reading. It is metadata, not a
# realtime observation. v0.8.94 only promotes rows coming from realtime observation
# endpoints and only if their measurement timestamp is within the last 24 hours.
# Also parse the field names used by BIPAD realtime rows (eventOn + magnitude).
# -----------------------------------------------------------------------------
level=r'''    private double v877ObservationLevel(JSONObject r){
        if(r==null)return Double.NaN;JSONObject f=r.optJSONObject("fields");
        double v=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","magnitude");
        if(Double.isFinite(v))return v;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){v=numDeep(o,o.optJSONObject("fields"),"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","magnitude");if(Double.isFinite(v))return v;}}
        return Double.NaN;
    } // V0894_BIPAD_MAGNITUDE_IS_RIVER_LEVEL
'''
a=replace_method(a,'v877ObservationLevel',level)

# Add a robust parser before the observation-time method.
s=span(a,'v877ObservationTime')
if not s:raise SystemExit('v0894 observation time anchor missing')
helper=r'''    private long v894ParseOfficialTime(String raw){
        if(raw==null)return 0L;String x=raw.trim();if(x.isEmpty()||"null".equalsIgnoreCase(x))return 0L;
        try{return java.time.Instant.parse(x).toEpochMilli();}catch(Exception ignored){}
        try{return java.time.OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}
        try{return java.time.ZonedDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}
        String y=x.replace(' ','T');
        try{return java.time.LocalDateTime.parse(y).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}
        try{return java.time.LocalDateTime.parse(y,java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}
        return 0L;
    } // V0894_PARSE_BIPAD_EVENT_TIME

    private long v894DirectOfficialTime(JSONObject r){
        if(r==null)return 0L;JSONObject f=r.optJSONObject("fields");
        String[] ks={"waterLevelOn","water_level_on","eventOn","event_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","dateTime","date_time"};
        for(String k:ks){Object v=r.opt(k);long t=v894ParseOfficialTime(v==null?null:String.valueOf(v));if(t>0L)return t;if(f!=null){v=f.opt(k);t=v894ParseOfficialTime(v==null?null:String.valueOf(v));if(t>0L)return t;}}
        return 0L;
    } // V0894_BIPAD_EVENTON_WATERLEVELON

'''
a=a[:s[0]]+helper+a[s[0]:]
time=r'''    private long v877ObservationTime(JSONObject r){
        if(r==null)return 0L;
        long at=v894DirectOfficialTime(r);if(at>0L)return at;
        at=trustedRowTime(r);if(at>0L)return at;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){at=v894DirectOfficialTime(o);if(at<=0L)at=trustedRowTime(o);if(at>0L)return at;}}
        return 0L;
    } // V0894_TRUE_OBSERVATION_TIME
'''
a=replace_method(a,'v877ObservationTime',time)

# Helper for removing stale measurement fields carried by station catalogue metadata.
s=span(a,'v877MergeOfficial')
if not s:raise SystemExit('v0894 merge helper anchor missing')
clear_helper=r'''

    private JSONObject v894CatalogMetadataOnly(JSONObject source){
        try{
            JSONObject out=source==null?new JSONObject():new JSONObject(source.toString());
            String[] ks={"waterLevel","water_level","waterLevelOn","water_level_on","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","magnitude","eventOn","event_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_lastWaterLevel","_measurementTime","_officialStatus"};
            for(String k:ks)out.remove(k);
            JSONObject f=out.optJSONObject("fields");if(f!=null)for(String k:ks)f.remove(k);
            out.put("_floodsafeCatalogOnly",true);out.put("_floodsafeOnline",false);out.put("_floodsafeSource","BIPAD river-stations inventory metadata");
            return out;
        }catch(Exception ignored){return new JSONObject();}
    } // V0894_CATALOG_IS_METADATA_NOT_REALTIME

    private String v894LooseLiveKey(JSONObject r){
        String ix=v846StationIndex(r);if(!ix.isEmpty())return "id:"+v846Key(ix);
        String nm=v846StationName(r);if(!nm.isEmpty())return "name:"+v846Key(nm);
        return "";
    } // V0894_UNMATCHED_LIVE_ROWS_RETAINED
'''
a=a[:s[1]]+clear_helper+a[s[1]:]

loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
        final long DISPLAY_MAX_AGE_MS=24L*60L*60L*1000L; // V0894_REALTIME_24H_DISPLAY_WINDOW
        JSONArray catalog=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=5000&_fs="+now,now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> unmatchedLive=new java.util.LinkedHashMap<>();
        String[] paths={"river/?limit=5000","river-trimed/?limit=5000","river-stations/?latest=true&limit=5000"};
        for(String path:paths){
            try{
                JSONArray rows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<rows.length();i++){
                    JSONObject live=rows.optJSONObject(i);if(live==null)continue;
                    double level=v877ObservationLevel(live);long at=v877ObservationTime(live);
                    if(!Double.isFinite(level)||at<=0L)continue;
                    long age=now-at;if(age<-(5L*60L*1000L)||age>DISPLAY_MAX_AGE_MS)continue; // never show August/old catalogue rows as realtime
                    String ix=v846StationIndex(live),nm=v846StationName(live);
                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;
                    if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
                    JSONObject merged=v877MergeOfficial(meta,live);
                    try{
                        merged.put("_floodsafeObservationMatched",true);merged.put("_floodsafeOnline",true);merged.put("_floodsafeSource","BIPAD realtime "+path);
                        String rn=v877RiverName(live);if(rn.isEmpty()&&meta!=null)rn=v877RiverName(meta);if(!rn.isEmpty())merged.put("_floodsafeRiverName",rn);
                        String wt=v877WaterbodyType(live);if(wt.isEmpty()&&meta!=null)wt=v877WaterbodyType(meta);if(!wt.isEmpty())merged.put("_floodsafeWaterbodyType",wt);
                    }catch(Exception ignored){}
                    String key=meta==null?v894LooseLiveKey(live):v862FinalKey(v846StationIndex(meta),v846StationName(meta));
                    if(key.isEmpty())continue;
                    java.util.LinkedHashMap<String,JSONObject> target=meta==null?unmatchedLive:newest;
                    JSONObject old=target.get(key);long oldAt=old==null?0L:v877ObservationTime(old);
                    if(old==null||at>oldAt)target.put(key,merged);
                }
            }catch(Exception ignored){}
        } // V0894_BIPAD_REALTIME_OBSERVATION_UNION

        // Direct DHM remains a secondary official source. Only recent rows are accepted.
        String[] dhmUrls={"https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,"https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now};
        for(String url:dhmUrls){
            try{
                String html=getTextV846(url);long pageAt=v846DhmUpdatedAt(html,0L);if(pageAt<=0L||now-pageAt>DISPLAY_MAX_AGE_MS)continue;
                for(DhmLiveV846 d:v846ParseDhmRows(html)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    JSONObject meta=null;if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));if(meta==null)meta=metaByName.get(v846Key(d.name));
                    JSONObject row=v877MergeOfficial(meta,null);row.put("stationIndex",meta==null?d.index:v846StationIndex(meta));row.put("stationName",meta==null?d.name:v846StationName(meta));if(!d.district.isEmpty())row.put("districtName",d.district);
                    row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);row.put("_measurementTime",java.time.Instant.ofEpochMilli(pageAt).toString());row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");
                    String key=meta==null?v894LooseLiveKey(row):v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
                    java.util.LinkedHashMap<String,JSONObject> target=meta==null?unmatchedLive:newest;JSONObject old=target.get(key);long oldAt=old==null?0L:v877ObservationTime(old);if(old==null||pageAt>oldAt)target.put(key,row);
                }
            }catch(Exception ignored){}
        } // V0894_DHM_RECENT_ONLY

        List<RiverStation> out=new ArrayList<>();
        java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextRows=new java.util.concurrent.ConcurrentHashMap<>();
        int freshCount=0,latestCount=0;
        for(int i=0;i<catalog.length();i++){
            JSONObject meta=catalog.optJSONObject(i);if(meta==null)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));JSONObject row=newest.get(key);
            if(row==null)row=v894CatalogMetadataOnly(meta); // stale embedded catalogue reading is intentionally erased
            RiverStation s=parseStation(row,now);if(s==null)continue;
            out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;
            try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        }
        for(JSONObject row:unmatchedLive.values()){
            RiverStation s=parseStation(row,now);if(s==null)continue;
            out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;
            try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        } // V0894_KEEP_CURRENT_ROWS_EVEN_WITHOUT_CATALOG_JOIN
        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,catalog.length()-latestCount);
        v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0894_TRUE_REALTIME_SOURCE_NO_STALE_CATALOG_READING
'''
a=replace_method(a,'loadTrustedRiverStationsV862',loader)

# Give Android the first frame before source/bootstrap work begins.
a=a.replace('main.postDelayed(() -> v887LoadBootstrapOfficialStations(), 180L); // V0887_BOOTSTRAP_CALL V0888_FIRST_FRAME_BEFORE_BOOTSTRAP','main.postDelayed(() -> v887LoadBootstrapOfficialStations(), 650L); // V0887_BOOTSTRAP_CALL V0888_FIRST_FRAME_BEFORE_BOOTSTRAP V0894_STARTUP_FIRST_FRAME',1)
if 'V0894_STARTUP_FIRST_FRAME' not in a:
    a=a.replace('V0888_FIRST_FRAME_BEFORE_BOOTSTRAP','V0888_FIRST_FRAME_BEFORE_BOOTSTRAP V0894_STARTUP_FIRST_FRAME',1)

# -----------------------------------------------------------------------------
# MAP FIX: actual Nepal camera bounds (the old v0.8.83 patch only marked the loose
# 25.4..31.15 / 79.2..89.15 bounds). Keep stale/catalog-only dots off the map.
# -----------------------------------------------------------------------------
m=m.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();','.include(new LatLng(26.20, 80.00))\n                        .include(new LatLng(30.50, 88.35)).build(); // V0894_REAL_NEPAL_CAMERA_BOUNDS',1)
if 'V0894_REAL_NEPAL_CAMERA_BOUNDS' not in m:
    # late generated variants may have same numbers formatted differently
    m,n=re.subn(r'\.include\(new LatLng\(25\.4\s*,\s*79\.2\)\)\s*\.include\(new LatLng\(31\.15\s*,\s*89\.15\)\)\.build\(\);','.include(new LatLng(26.20, 80.00)).include(new LatLng(30.50, 88.35)).build(); // V0894_REAL_NEPAL_CAMERA_BOUNDS',m,count=1)
    if n!=1:raise SystemExit('v0894 Nepal camera bounds anchor missing')

reset=r'''    void resetView() {
        if (map == null) return;
        try{
            LatLngBounds b=new LatLngBounds.Builder().include(new LatLng(26.20,80.00)).include(new LatLng(30.50,88.35)).build();
            map.animateCamera(CameraUpdateFactory.newLatLngBounds(b, 28), 380); // V0894_NEPAL_FIT_CAMERA
        }catch(Exception e){
            CameraPosition cp=new CameraPosition.Builder().target(new LatLng(28.35,84.18)).zoom(5.95).tilt(0.0).bearing(0.0).build();
            map.animateCamera(CameraUpdateFactory.newCameraPosition(cp),380);
        }
    }
'''
m=replace_method(m,'resetView',reset)

station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();long now=System.currentTimeMillis();
            for (StationDot s : list) {
                boolean observed=s!=null&&Double.isFinite(s.level)&&s.v881At>0L&&now-s.v881At>=-(5L*60L*1000L)&&now-s.v881At<=24L*60L*60L*1000L;
                if(!observed)continue; // V0894_HIDE_CATALOG_AND_OLD_STATION_DOTS
                String g=normalizeStage(s.stage);
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon,s.lat,s.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }
'''
m=replace_method(m,'stationGeo',station_geo)

# Debounce expensive river recolour geometry so app open/scroll does not freeze.
anchor='    private String v890StationVisualFingerprint = ""; // V0890_STABLE_STATION_RENDER\n'
if anchor in m and 'V0894_DEBOUNCED_RISK_GEOMETRY' not in m:
    m=m.replace(anchor,anchor+'    private final Runnable v894RiskGeometryRefresh=() -> v887ApplyMonitoredRiverGeometry(); // V0894_DEBOUNCED_RISK_GEOMETRY\n',1)
m=m.replace('v887ApplyMonitoredRiverGeometry(); // V0890_STATUS_REFRESH_RECOLOURS_RIVERS','main.removeCallbacks(v894RiskGeometryRefresh); main.postDelayed(v894RiskGeometryRefresh, 700L); // V0890_STATUS_REFRESH_RECOLOURS_RIVERS V0894_NO_STARTUP_GEOMETRY_FREEZE',1)
if 'V0894_NO_STARTUP_GEOMETRY_FREEZE' not in m:raise SystemExit('v0894 river recolour debounce anchor missing')

# Release identity.
g=re.sub(r'versionCode\s+113\b','versionCode 114',g,count=1)
g=g.replace("versionName '0.8.93'","versionName '0.8.94'",1)

for x in ['V0894_BIPAD_MAGNITUDE_IS_RIVER_LEVEL','V0894_PARSE_BIPAD_EVENT_TIME','V0894_BIPAD_EVENTON_WATERLEVELON','V0894_CATALOG_IS_METADATA_NOT_REALTIME','V0894_REALTIME_24H_DISPLAY_WINDOW','V0894_BIPAD_REALTIME_OBSERVATION_UNION','V0894_KEEP_CURRENT_ROWS_EVEN_WITHOUT_CATALOG_JOIN','V0894_TRUE_REALTIME_SOURCE_NO_STALE_CATALOG_READING','V0894_REAL_NEPAL_CAMERA_BOUNDS','V0894_NEPAL_FIT_CAMERA','V0894_HIDE_CATALOG_AND_OLD_STATION_DOTS','V0894_DEBOUNCED_RISK_GEOMETRY','V0894_NO_STARTUP_GEOMETRY_FREEZE']:
    if x not in a and x not in m:raise SystemExit('v0894 contract missing: '+x)
if 'versionCode 114' not in g or "versionName '0.8.94'" not in g:raise SystemExit('v0894 version bump failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.94 PASS: true BIPAD realtime observations, stale catalogue readings removed, Nepal camera fixed, startup map work debounced')
