from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app';src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java';m_path=src/'FloodSafeNativeMapView.java';l_path=src/'FloodLiveGaugeMonitor.java';s_path=src/'FloodMonitorService.java';g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8');m=m_path.read_text(encoding='utf-8');l=l_path.read_text(encoding='utf-8');s=s_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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
# 1) BIPAD River Watch = direct river-stations mirror. No river historical archive.
# Keep only measurements within 24 h, matching the public River Watch population.
# -----------------------------------------------------------------------------
z=span(a,'loadTrustedRiverStationsV862')
if not z:raise SystemExit('v0895 river loader missing')
helper=r'''    private String v895NamedRiverFromStation(String title){
        if(title==null)return "";String x=title.trim();String low=x.toLowerCase(Locale.ROOT);int cut=-1;
        for(String sep:new String[]{" at "," @ "," near "}){int p=low.indexOf(sep);if(p>0&&(cut<0||p<cut))cut=p;}
        if(cut>0)x=x.substring(0,cut).trim();return x;
    } // V0895_NAMED_RIVER_FROM_BIPAD_TITLE

'''
a=a[:z[0]]+helper+a[z[0]:]
loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
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
        v849CatalogCount=current;v849LatestCount=current;v877LatestObservationCount=current;v877NoObservationCount=0;v877FreshObservationCount=fresh;
        v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0895_BIPAD_RIVER_WATCH_MIRROR_NO_ARCHIVE
'''
a=replace_method(a,'loadTrustedRiverStationsV862',loader)

# Near-realtime, but do not hammer official public servers every second.
a=a.replace('main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */','main.postDelayed(this,10_000L); /* V0895_TEN_SECOND_BIPAD_MIRROR V0871_ONE_SECOND_SOURCE_RECHECK */')
a=a.replace('main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK','main.postDelayed(this,10_000L); // V0895_TEN_SECOND_BIPAD_MIRROR V0871_ONE_SECOND_SOURCE_RECHECK')
if 'V0895_TEN_SECOND_BIPAD_MIRROR' not in a:raise SystemExit('v0895 foreground poll anchor missing')

# Direct DHM rainfall mirror starts after first UI frame; background service also keeps it warm.
needle='setContentView(buildScreen());'
if needle not in a:raise SystemExit('v0895 activity startup anchor missing')
a=a.replace(needle,needle+'\n        main.postDelayed(() -> DhmRainMirror.ensureStarted(this),900L); // V0895_DHM_RAIN_MIRROR_START',1)

# -----------------------------------------------------------------------------
# 2) Rain detail popup = DHM Rainfall Watch 1/3/6/12/24 h values when name matches.
# Existing BIPAD rain detail remains fallback only.
# -----------------------------------------------------------------------------
z=span(m,'showRain')
if not z:raise SystemExit('v0895 showRain missing')
b=m[z[0]:z[1]];op=b.find('{')+1
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
# 3) Map: strict Nepal viewport, named monitored rivers, readable topo + place labels.
# -----------------------------------------------------------------------------
if 'RasterSource' not in m:
    m=m.replace('import org.maplibre.android.style.sources.GeoJsonSource;','import org.maplibre.android.style.sources.GeoJsonSource;\nimport org.maplibre.android.style.sources.RasterSource;\nimport org.maplibre.android.style.sources.TileSet;\nimport org.maplibre.android.style.layers.RasterLayer;',1)
if 'rasterOpacity' not in m:
    m=m.replace('import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;','import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\nimport static org.maplibre.android.style.layers.PropertyFactory.rasterOpacity;',1)

# Reinforce actual bounds after prior camera fix.
m=m.replace('private static final double NEPAL_MIN_LAT = 26.2, NEPAL_MAX_LAT = 30.5;','private static final double NEPAL_MIN_LAT = 26.20, NEPAL_MAX_LAT = 30.50; // V0895_STRICT_NEPAL_MAP',1)
m=m.replace('private static final double NEPAL_MIN_LON = 80.0, NEPAL_MAX_LON = 88.35;','private static final double NEPAL_MIN_LON = 80.00, NEPAL_MAX_LON = 88.35;',1)

z=span(m,'installGeoLayers')
if not z:raise SystemExit('v0895 installGeoLayers missing')
b=m[z[0]:z[1]];op=b.find('{')+1
places=r'''
        try{
            if(style.getSource("fs-place-labels")==null){
                TileSet ts=new TileSet("2.2.0","https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}");
                ts.setMaxZoom(19f);style.addSource(new RasterSource("fs-place-labels",ts,256));
                style.addLayer(new RasterLayer("fs-place-labels-layer","fs-place-labels").withProperties(rasterOpacity(0.92f))); // V0895_PLACE_TOWN_LABEL_LAYER
            }
        }catch(Exception ignored){}
'''
b=b[:op]+places+b[op:];m=m[:z[0]]+b+m[z[1]:]

# Only useful named rivers which have an active official River Watch station are rendered.
z=span(m,'v887MonitoredRivers')
if not z:raise SystemExit('v0895 monitored rivers missing')
mon=r'''    private List<RiverWay> v887MonitoredRivers(List<RiverWay> input){
        List<RiverWay> out=new ArrayList<>();if(input==null||input.isEmpty())return out;
        java.util.HashSet<String> officialKeys=new java.util.HashSet<>();
        synchronized(stations){for(StationDot s:stations){if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)continue;String k=v886RiverKey(s.riverName);if(!k.isEmpty())officialKeys.add(k);String tk=v886RiverKey(v886StationRiverFromTitle(s.name));if(!tk.isEmpty())officialKeys.add(tk);}}
        for(RiverWay r:input){if(r==null||!v863UsefulRiverName(r.name))continue;String rk=v886RiverKey(r.name);if(!rk.isEmpty()&&officialKeys.contains(rk))out.add(r);}
        return out;
    } // V0895_NAMED_ACTIVE_BIPAD_RIVERS_ONLY
'''
m=replace_method(m,'v887MonitoredRivers',mon)

# -----------------------------------------------------------------------------
# 4) Background mirror: direct BIPAD river-stations, 10 s polling, strict fresh 2 km alerts.
# -----------------------------------------------------------------------------
l=re.sub(r'private static final String RIVER_ENDPOINT="[^"]+";', 'private static final String RIVER_ENDPOINT=BIPAD+"river-stations/?format=json&limit=5000"; // V0895_BACKGROUND_DIRECT_BIPAD',l,count=1)
l=l.replace('handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK','handler.postDelayed(this,10_000L); // V0895_BACKGROUND_TEN_SECOND_MIRROR V0872_ONE_SECOND_BACKGROUND_RECHECK')
# Avoid malformed double '?' when RIVER_ENDPOINT already contains query.
l=l.replace('fetch(RIVER_ENDPOINT+"?_bg="+System.currentTimeMillis())','fetch(RIVER_ENDPOINT+"&_bg="+System.currentTimeMillis())')

# Add exact BIPAD measurement-time freshness guard to emergency warning path.
needle='long now=System.currentTimeMillis();int shown=0;'
if needle not in l:raise SystemExit('v0895 background hazard loop anchor missing')
l=l.replace(needle,needle+'\n        final long ALERT_FRESH_MS=30L*60L*1000L; // V0895_ALERT_FRESHNESS_SEPARATE_FROM_24H_DISPLAY',1)
needle2='JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");'
if needle2 not in l:raise SystemExit('v0895 background row anchor missing')
l=l.replace(needle2,needle2+'long obsAt=v895ObservationTime(row,f);if(obsAt<=0L||now-obsAt>ALERT_FRESH_MS||obsAt-now>5L*60L*1000L)continue;',1)
# helper before array()
anchor='    private static JSONArray array(JSONObject root,String... keys)'
if anchor not in l:raise SystemExit('v0895 monitor helper anchor missing')
helper=r'''    private static long v895ObservationTime(JSONObject r,JSONObject f){
        String x=str(r,f,"waterLevelOn","water_level_on","eventOn","event_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp");if(x.isEmpty())return 0L;
        try{return java.time.Instant.parse(x).toEpochMilli();}catch(Exception ignored){}
        try{return java.time.OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}
        try{return java.time.LocalDateTime.parse(x.replace(' ','T')).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}
        return 0L;
    } // V0895_BACKGROUND_BIPAD_TIME_TRUTH

'''
l=l.replace(anchor,helper+anchor,1)
if 'V0895_BACKGROUND_TEN_SECOND_MIRROR' not in l:raise SystemExit('v0895 background interval anchor missing')

# Keep DHM rain cache alive while foreground service survives app UI closure.
service_anchor='super.onCreate();'
if service_anchor not in s:raise SystemExit('v0895 service onCreate anchor missing')
s=s.replace(service_anchor,service_anchor+'\n        DhmRainMirror.ensureStarted(this); // V0895_DHM_RAIN_BACKGROUND_MIRROR',1)

# Release identity.
g=re.sub(r'versionCode\s+114\b','versionCode 115',g,count=1);g=g.replace("versionName '0.8.94'","versionName '0.8.95'",1)

for x in ['V0895_DIRECT_BIPAD_RIVER_WATCH','V0895_BIPAD_24H_RIVER_WATCH_ONLY','V0895_NAMED_RIVERS_ONLY','V0895_BIPAD_RIVER_WATCH_MIRROR_NO_ARCHIVE','V0895_TEN_SECOND_BIPAD_MIRROR','V0895_DHM_RAIN_MIRROR_START']:
    if x not in a:raise SystemExit('v0895 activity contract missing '+x)
for x in ['V0895_DHM_RAIN_DETAIL_PRIMARY','V0895_PLACE_TOWN_LABEL_LAYER','V0895_NAMED_ACTIVE_BIPAD_RIVERS_ONLY','V0895_STRICT_NEPAL_MAP','V0893_BIPAD_RIVER_COLOUR_PARITY']:
    if x not in m:raise SystemExit('v0895 map contract missing '+x)
for x in ['V0895_BACKGROUND_DIRECT_BIPAD','V0895_BACKGROUND_TEN_SECOND_MIRROR','V0895_ALERT_FRESHNESS_SEPARATE_FROM_24H_DISPLAY','V0895_BACKGROUND_BIPAD_TIME_TRUTH']:
    if x not in l:raise SystemExit('v0895 monitor contract missing '+x)
if 'V0895_DHM_RAIN_BACKGROUND_MIRROR' not in s:raise SystemExit('v0895 service rain mirror missing')
if 'versionCode 115' not in g or "versionName '0.8.95'" not in g:raise SystemExit('v0895 version bump failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');l_path.write_text(l,encoding='utf-8');s_path.write_text(s,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.95 PASS: BIPAD River Watch mirror + DHM rainfall mirror + background/GPS safety + named status rivers + place labels')
