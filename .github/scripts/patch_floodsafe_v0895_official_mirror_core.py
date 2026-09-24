from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app';src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java';m_path=src/'FloodSafeNativeMapView.java';l_path=src/'FloodLiveGaugeMonitor.java';s_path=src/'FloodMonitorService.java';g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8');m=m_path.read_text(encoding='utf-8');l=l_path.read_text(encoding='utf-8');s=s_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

def span(text,name):
    pat=re.compile(r'(?m)^\s*(?:private|public|protected)\s+[^\n;{]*?\b'+re.escape(name)+r'\s*\([^\n;]*\)\s*(?:throws\s+[^\n{]+)?\s*\{')
    q=pat.search(text)
    if not q:return None
    op=text.find('{',q.start());d=0;quote=None;esc=False
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
    z=span(text,name)
    if not z:raise SystemExit('v0895 method missing: '+name)
    return text[:z[0]]+block+text[z[1]:]

# -----------------------------------------------------------------------------
# 1) BIPAD River Watch mirror.
# Do not rewrite the old multi-source loader: add a new direct mirror and route every
# live refresh call to it. This prevents old river archive rows from re-entering UI.
# -----------------------------------------------------------------------------
activity_anchor='    private View buildScreen(){'
if activity_anchor not in a:raise SystemExit('v0895 activity insertion anchor missing')
if 'V0895_BIPAD_RIVER_WATCH_MIRROR_NO_ARCHIVE' not in a:
    mirror=r'''    private String v895NamedRiverFromStation(String title){
        if(title==null)return "";String x=title.trim();String low=x.toLowerCase(Locale.ROOT);int cut=-1;
        for(String sep:new String[]{" at "," @ "," near "}){int p=low.indexOf(sep);if(p>0&&(cut<0||p<cut))cut=p;}
        if(cut>0)x=x.substring(0,cut).trim();return x;
    } // V0895_NAMED_RIVER_FROM_BIPAD_TITLE

    private List<RiverStation> v895LoadBipadRiverWatch(long now)throws Exception{
        final long WATCH_MS=24L*60L*60L*1000L;
        JSONArray rows=trustedPages(BIPAD+"river-stations/?format=json&limit=5000&_fs="+now,now); // V0895_DIRECT_BIPAD_RIVER_WATCH
        List<RiverStation> out=new ArrayList<>();java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextRows=new java.util.concurrent.ConcurrentHashMap<>();
        int fresh=0,current=0;
        for(int i=0;i<rows.length();i++){
            JSONObject source=rows.optJSONObject(i);if(source==null)continue;
            double level=v877ObservationLevel(source);long at=v877ObservationTime(source);if(!Double.isFinite(level)||at<=0L)continue;
            long age=now-at;if(age<-(5L*60L*1000L)||age>WATCH_MS)continue; // V0895_BIPAD_24H_RIVER_WATCH_ONLY
            JSONObject row=new JSONObject(source.toString());
            String rn=v877RiverName(row);if(rn.isEmpty())rn=v895NamedRiverFromStation(v846StationName(row));
            if(rn.isEmpty()||!rn.matches(".*[A-Za-z\\p{L}].*"))continue; // V0895_NAMED_RIVERS_ONLY
            row.put("_floodsafeRiverName",rn);row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","BIPAD River Watch / DHM-connected");
            RiverStation st=parseStation(row,now);if(st==null)continue;out.add(st);current++;if(st.fresh)fresh++;
            String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));
        }
        out.sort(Comparator.comparingInt((RiverStation x)->x.rank).thenComparing(x->x.name,String.CASE_INSENSITIVE_ORDER));
        v849CatalogCount=current;v849LatestCount=current;v877LatestObservationCount=current;v877NoObservationCount=0;v877FreshObservationCount=fresh;
        v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0895_BIPAD_RIVER_WATCH_MIRROR_NO_ARCHIVE

'''
    a=a.replace(activity_anchor,mirror+activity_anchor,1)

# Route active refresh calls away from the historical union loader.
a,n=re.subn(r'\bloadTrustedRiverStationsV862\(now\)', 'v895LoadBipadRiverWatch(now)', a)
if n<1:raise SystemExit('v0895 active river loader call missing')

# Near-realtime mirror; BIPAD source updates are normally 5/10-minute observations, so
# 10-second polling mirrors a source change quickly without hitting the public API each second.
a=re.sub(r'main\.postDelayed\(this,\s*1_000L\);\s*/[/*][^\n]*V0871_ONE_SECOND_SOURCE_RECHECK[^\n]*', 'main.postDelayed(this,10_000L); /* V0895_TEN_SECOND_BIPAD_MIRROR V0871_ONE_SECOND_SOURCE_RECHECK */', a, count=1)
if 'V0895_TEN_SECOND_BIPAD_MIRROR' not in a:
    # Some late variants already use another delay: mark and normalize the scheduler containing the marker.
    a,n=re.subn(r'main\.postDelayed\(this,\s*[0-9_]+L\);\s*[^\n]*V0871_ONE_SECOND_SOURCE_RECHECK[^\n]*', 'main.postDelayed(this,10_000L); /* V0895_TEN_SECOND_BIPAD_MIRROR V0871_ONE_SECOND_SOURCE_RECHECK */', a, count=1)
    if n!=1:raise SystemExit('v0895 foreground poll anchor missing')

needle='setContentView(buildScreen());'
if needle not in a:raise SystemExit('v0895 activity startup anchor missing')
if 'V0895_DHM_RAIN_MIRROR_START' not in a:a=a.replace(needle,needle+'\n        main.postDelayed(() -> DhmRainMirror.ensureStarted(this),900L); // V0895_DHM_RAIN_MIRROR_START',1)

# -----------------------------------------------------------------------------
# 2) Rain popup: DHM Rainfall Watch 1/3/6/12/24-hour mirror first.
# -----------------------------------------------------------------------------
z=span(m,'showRain')
if not z:raise SystemExit('v0895 showRain missing')
b=m[z[0]:z[1]]
if 'V0895_DHM_RAIN_DETAIL_PRIMARY' not in b:
    op=b.find('{')+1
    inject=r'''
        try{
            String v895RainName=r==null?"":getString(r.getClass(),r,"name","");
            String v895Dhm=DhmRainMirror.detailFor(v895RainName);
            if(v895Dhm!=null&&!v895Dhm.isEmpty()){
                new AlertDialog.Builder(getContext()).setTitle(v895RainName.isEmpty()?"DHM Rainfall Watch":v895RainName).setMessage(v895Dhm).setPositiveButton("ठीक छ",null).show();
                return; // V0895_DHM_RAIN_DETAIL_PRIMARY
            }
        }catch(Exception ignored){}
'''
    b=b[:op]+inject+b[op:];m=m[:z[0]]+b+m[z[1]:]

# -----------------------------------------------------------------------------
# 3) Map: actual Nepal bounds, readable town/place labels, named monitored rivers only.
# -----------------------------------------------------------------------------
if 'import org.maplibre.android.style.sources.RasterSource;' not in m:
    m=m.replace('import org.maplibre.android.style.sources.GeoJsonSource;','import org.maplibre.android.style.sources.GeoJsonSource;\nimport org.maplibre.android.style.sources.RasterSource;\nimport org.maplibre.android.style.sources.TileSet;\nimport org.maplibre.android.style.layers.RasterLayer;',1)
if 'import static org.maplibre.android.style.layers.PropertyFactory.rasterOpacity;' not in m:
    m=m.replace('import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;','import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\nimport static org.maplibre.android.style.layers.PropertyFactory.rasterOpacity;',1)

m=m.replace('private static final double NEPAL_MIN_LAT = 26.2, NEPAL_MAX_LAT = 30.5;','private static final double NEPAL_MIN_LAT = 26.20, NEPAL_MAX_LAT = 30.50; // V0895_STRICT_NEPAL_MAP',1)
if 'V0895_STRICT_NEPAL_MAP' not in m:m=m.replace('private static final double NEPAL_MIN_LAT = 26.20, NEPAL_MAX_LAT = 30.50;','private static final double NEPAL_MIN_LAT = 26.20, NEPAL_MAX_LAT = 30.50; // V0895_STRICT_NEPAL_MAP',1)
m=m.replace('private static final double NEPAL_MIN_LON = 80.0, NEPAL_MAX_LON = 88.35;','private static final double NEPAL_MIN_LON = 80.00, NEPAL_MAX_LON = 88.35;',1)
# Real camera target; v0.8.83 previously marked but did not tighten the old numbers.
m=m.replace('new LatLng(25.4, 79.2)','new LatLng(26.20, 80.00)')
m=m.replace('new LatLng(31.15, 89.15)','new LatLng(30.50, 88.35)')
if 'V0895_REAL_NEPAL_CAMERA_BOUNDS' not in m:
    target='map.setLatLngBoundsForCameraTarget(bounds);'
    if target not in m:raise SystemExit('v0895 map camera target missing')
    m=m.replace(target,target+' // V0895_REAL_NEPAL_CAMERA_BOUNDS',1)

reset=r'''    void resetView() {
        if (map == null) return;
        CameraPosition cp = new CameraPosition.Builder().target(new LatLng(28.25,84.15)).zoom(5.95).tilt(0.0).bearing(0.0).build();
        map.animateCamera(CameraUpdateFactory.newCameraPosition(cp),380); // V0895_NEPAL_CENTERED_RESET
    }
'''
m=replace_method(m,'resetView',reset)

z=span(m,'installGeoLayers')
if not z:raise SystemExit('v0895 installGeoLayers missing')
b=m[z[0]:z[1]]
if 'V0895_PLACE_TOWN_LABEL_LAYER' not in b:
    op=b.find('{')+1
    places=r'''
        try{
            if(style.getSource("fs-place-labels")==null){
                TileSet ts=new TileSet("2.2.0","https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}");
                ts.setMaxZoom(19f);style.addSource(new RasterSource("fs-place-labels",ts,256));
                style.addLayer(new RasterLayer("fs-place-labels-layer","fs-place-labels").withProperties(rasterOpacity(0.90f))); // V0895_PLACE_TOWN_LABEL_LAYER
            }
        }catch(Exception ignored){}
'''
    b=b[:op]+places+b[op:];m=m[:z[0]]+b+m[z[1]:]

mon=r'''    private List<RiverWay> v887MonitoredRivers(List<RiverWay> input){
        List<RiverWay> out=new ArrayList<>();if(input==null||input.isEmpty())return out;
        java.util.HashSet<String> officialKeys=new java.util.HashSet<>();
        synchronized(stations){for(StationDot s:stations){if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)continue;String k=v886RiverKey(s.riverName);if(!k.isEmpty())officialKeys.add(k);String tk=v886RiverKey(v886StationRiverFromTitle(s.name));if(!tk.isEmpty())officialKeys.add(tk);}}
        for(RiverWay r:input){if(r==null||!v863UsefulRiverName(r.name))continue;String rk=v886RiverKey(r.name);if(!rk.isEmpty()&&officialKeys.contains(rk))out.add(r);}
        return out;
    } // V0895_NAMED_ACTIVE_BIPAD_RIVERS_ONLY
'''
m=replace_method(m,'v887MonitoredRivers',mon)

# Avoid startup UI stalls: risk geometry is already delayed by v0.8.89; increase the final
# recolour debounce so source refresh does not fight the first map frame.
m=m.replace('main.postDelayed(v894RiskGeometryRefresh, 700L);','main.postDelayed(v894RiskGeometryRefresh, 1200L);') if 'v894RiskGeometryRefresh' in m else m

# -----------------------------------------------------------------------------
# 4) App-closed service: direct BIPAD mirror every 10s; emergency alerts stay fresh-only.
# -----------------------------------------------------------------------------
l=re.sub(r'private static final String RIVER_ENDPOINT="[^"]+";', 'private static final String RIVER_ENDPOINT=BIPAD+"river-stations/?format=json&limit=5000"; // V0895_BACKGROUND_DIRECT_BIPAD',l,count=1)
l=l.replace('handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK','handler.postDelayed(this,10_000L); // V0895_BACKGROUND_TEN_SECOND_MIRROR V0872_ONE_SECOND_BACKGROUND_RECHECK')
l=l.replace('fetch(RIVER_ENDPOINT+"?_bg="+System.currentTimeMillis())','fetch(RIVER_ENDPOINT+"&_bg="+System.currentTimeMillis())')
if 'V0895_BACKGROUND_TEN_SECOND_MIRROR' not in l:
    l,n=re.subn(r'handler\.postDelayed\(this,\s*[0-9_]+L\);\s*// V0872_ONE_SECOND_BACKGROUND_RECHECK','handler.postDelayed(this,10_000L); // V0895_BACKGROUND_TEN_SECOND_MIRROR V0872_ONE_SECOND_BACKGROUND_RECHECK',l,count=1)
    if n!=1:raise SystemExit('v0895 background interval anchor missing')

needle='long now=System.currentTimeMillis();int shown=0;'
if needle not in l:raise SystemExit('v0895 background hazard loop anchor missing')
if 'V0895_ALERT_FRESHNESS_SEPARATE_FROM_24H_DISPLAY' not in l:l=l.replace(needle,needle+'\n        final long ALERT_FRESH_MS=30L*60L*1000L; // V0895_ALERT_FRESHNESS_SEPARATE_FROM_24H_DISPLAY',1)
needle2='JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");'
if needle2 not in l:raise SystemExit('v0895 background row anchor missing')
if 'v895ObservationTime(row,f)' not in l:l=l.replace(needle2,needle2+'long obsAt=v895ObservationTime(row,f);if(obsAt<=0L||now-obsAt>ALERT_FRESH_MS||obsAt-now>5L*60L*1000L)continue;',1)
anchor='    private static JSONArray array(JSONObject root,String... keys)'
if anchor not in l:raise SystemExit('v0895 monitor helper anchor missing')
if 'V0895_BACKGROUND_BIPAD_TIME_TRUTH' not in l:
    h=r'''    private static long v895ObservationTime(JSONObject r,JSONObject f){
        String x=str(r,f,"waterLevelOn","water_level_on","eventOn","event_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp");if(x.isEmpty())return 0L;
        try{return java.time.Instant.parse(x).toEpochMilli();}catch(Exception ignored){}
        try{return java.time.OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}
        try{return java.time.LocalDateTime.parse(x.replace(' ','T')).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}
        return 0L;
    } // V0895_BACKGROUND_BIPAD_TIME_TRUTH

'''
    l=l.replace(anchor,h+anchor,1)

service_anchor='super.onCreate();'
if service_anchor not in s:raise SystemExit('v0895 service onCreate anchor missing')
if 'V0895_DHM_RAIN_BACKGROUND_MIRROR' not in s:s=s.replace(service_anchor,service_anchor+'\n        DhmRainMirror.ensureStarted(this); // V0895_DHM_RAIN_BACKGROUND_MIRROR',1)

# Release directly from v0.8.93 or from an optional v0.8.94 intermediate.
g=re.sub(r'versionCode\s+(?:113|114)\b','versionCode 115',g,count=1)
g=g.replace("versionName '0.8.93'","versionName '0.8.95'",1).replace("versionName '0.8.94'","versionName '0.8.95'",1)

for x in ['V0895_DIRECT_BIPAD_RIVER_WATCH','V0895_BIPAD_24H_RIVER_WATCH_ONLY','V0895_NAMED_RIVERS_ONLY','V0895_BIPAD_RIVER_WATCH_MIRROR_NO_ARCHIVE','V0895_TEN_SECOND_BIPAD_MIRROR','V0895_DHM_RAIN_MIRROR_START']:
    if x not in a:raise SystemExit('v0895 activity contract missing '+x)
for x in ['V0895_DHM_RAIN_DETAIL_PRIMARY','V0895_PLACE_TOWN_LABEL_LAYER','V0895_NAMED_ACTIVE_BIPAD_RIVERS_ONLY','V0895_STRICT_NEPAL_MAP','V0895_REAL_NEPAL_CAMERA_BOUNDS','V0895_NEPAL_CENTERED_RESET','V0893_BIPAD_RIVER_COLOUR_PARITY']:
    if x not in m:raise SystemExit('v0895 map contract missing '+x)
for x in ['V0895_BACKGROUND_DIRECT_BIPAD','V0895_BACKGROUND_TEN_SECOND_MIRROR','V0895_ALERT_FRESHNESS_SEPARATE_FROM_24H_DISPLAY','V0895_BACKGROUND_BIPAD_TIME_TRUTH']:
    if x not in l:raise SystemExit('v0895 monitor contract missing '+x)
if 'V0895_DHM_RAIN_BACKGROUND_MIRROR' not in s:raise SystemExit('v0895 service rain mirror missing')
if 'versionCode 115' not in g or "versionName '0.8.95'" not in g:raise SystemExit('v0895 version bump failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');l_path.write_text(l,encoding='utf-8');s_path.write_text(s,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.95 PASS: BIPAD River Watch mirror + DHM rainfall mirror + app-closed monitor + GPS preserved + named status rivers + place labels')
