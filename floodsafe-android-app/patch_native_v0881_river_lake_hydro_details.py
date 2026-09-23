from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# FloodSafe Nepal v0.8.81
# Field feedback repair: v0.8.80 still behaved station-first. A river tap delegated to the
# station popup and lake/reservoir/outlet metadata had no first-class map layer. This patch
# makes river, hydrology and lake/outlet information directly visible without inventing
# readings that do not exist in an official source.
#
# Safety invariants deliberately unchanged:
# - LIVE remains fresh-only according to the existing trusted-source policy
# - Warning/Danger emergency radius remains 2 km
# - no different-river / merely-nearby gauge is attached to a named river
# - exact official station coordinates/readings are not changed


def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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


def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0881 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# -----------------------------------------------------------------------------
# A) Preserve extra display-only official metadata on StationDot.
#    Prefix every new field to avoid colliding with historical StationDot fields.
# -----------------------------------------------------------------------------
if 'V0881_WATERBODY_DOT_FIELDS' not in m:
    q=re.search(r'private\s+static\s+final\s+class\s+StationDot\s*\{',m)
    if not q:raise SystemExit('v0881 StationDot class missing')
    fields='''\n        String v881WaterKind="",v881WaterType="",v881StationType="",v881Source="";\n        double v881Warning=Double.NaN,v881Danger=Double.NaN; long v881At=0L; JSONObject v881Raw=null;\n        /* V0881_WATERBODY_DOT_FIELDS */\n'''
    m=m[:q.end()]+fields+m[q.end():]

# Reflection helpers read metadata already carried by RiverStation.raw; they never alter it.
if 'V0881_RAW_OFFICIAL_METADATA_HELPERS' not in m:
    anchor=re.search(r'(?m)^\s*private\s+static\s+double\s+getDouble\s*\(',m)
    if not anchor:raise SystemExit('v0881 getDouble helper anchor missing')
    helpers=r'''    private static double v881FieldDouble(Class<?> c,Object o,String name){
        try{Field f=c.getDeclaredField(name);f.setAccessible(true);Object v=f.get(o);return v instanceof Number?((Number)v).doubleValue():Double.NaN;}catch(Exception ignored){return Double.NaN;}
    }
    private static long v881FieldLong(Class<?> c,Object o,String name){
        try{Field f=c.getDeclaredField(name);f.setAccessible(true);Object v=f.get(o);return v instanceof Number?((Number)v).longValue():0L;}catch(Exception ignored){return 0L;}
    }
    private static JSONObject v881RawRow(Class<?> c,Object o){
        try{Field f=c.getDeclaredField("raw");f.setAccessible(true);Object v=f.get(o);return v instanceof JSONObject?(JSONObject)v:null;}catch(Exception ignored){return null;}
    }
    private static String v881JsonString(JSONObject row,String...keys){
        if(row==null||keys==null)return "";JSONObject f=row.optJSONObject("fields");
        for(String k:keys){
            if(k==null)continue;Object v=row.opt(k);if((v==null||v==JSONObject.NULL)&&f!=null)v=f.opt(k);
            if(v!=null&&v!=JSONObject.NULL){String s=String.valueOf(v).trim();if(!s.isEmpty()&&!"null".equalsIgnoreCase(s))return s;}
        }
        return "";
    }
    private static String v881WaterKind(StationDot s){
        if(s==null)return "";
        String desc=v881JsonString(s.v881Raw,"description","stationDescription","station_description");
        String hay=(s.name+" "+s.riverName+" "+s.v881WaterType+" "+s.v881StationType+" "+desc).toLowerCase(Locale.ROOT);
        if(hay.contains("lake outlet")||hay.contains("outlet")||hay.contains("glof")||hay.contains("glacial"))return "lake/outlet";
        if(hay.contains("lake")||hay.contains("reservoir")||hay.contains("dam")||hay.contains(" tal")||hay.startsWith("tal ")||hay.contains("ताल"))return "lake/reservoir";
        return "";
    }
    private static boolean v881IsWaterbody(StationDot s){return s!=null&&!s.v881WaterKind.isEmpty();}
    private static String v881Time(long at){
        if(at<=0L)return "";
        try{return new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss z",Locale.US).format(new java.util.Date(at));}catch(Exception ignored){return String.valueOf(at);}
    } // V0881_RAW_OFFICIAL_METADATA_HELPERS

'''
    m=m[:anchor.start()]+helpers+m[anchor.start():]

# Enrich readStation without replacing historical fields used by risk matching.
if 'V0881_READ_WATERBODY_METADATA' not in m:
    sp=method_span(m,'readStation')
    if not sp:raise SystemExit('v0881 readStation missing')
    block=m[sp[0]:sp[1]]
    marker='s.riverName=getString(c,o,"riverName",""); // V0880_READ_OFFICIAL_RIVER_NAME'
    if marker not in block:raise SystemExit('v0881 requires v0.8.80 riverName read marker')
    extra=r'''
            s.v881Warning=v881FieldDouble(c,o,"warning");s.v881Danger=v881FieldDouble(c,o,"danger");s.v881At=v881FieldLong(c,o,"at");
            s.v881Raw=v881RawRow(c,o);
            s.v881Source=v881JsonString(s.v881Raw,"_floodsafeSource","source","dataSource","data_source");
            s.v881WaterType=v881JsonString(s.v881Raw,"_floodsafeWaterbodyType","waterbodyType","waterbody_type","type","category");
            s.v881StationType=v881JsonString(s.v881Raw,"stationType","station_type","type","category");
            s.v881WaterKind=v881WaterKind(s); // V0881_READ_WATERBODY_METADATA
'''
    block=block.replace(marker,marker+extra,1)
    m=m[:sp[0]]+block+m[sp[1]:]

# -----------------------------------------------------------------------------
# B) Dedicated hydrology + lake/reservoir/outlet map layers.
#    Hydrology gets a subtle cyan halo. Waterbody sites are coloured by the SAME existing
#    stage/freshness truth: grey=not current, green/yellow/orange/red=current status.
# -----------------------------------------------------------------------------
if 'V0881_HYDRO_WATERBODY_GEO' not in m:
    sp=method_span(m,'refreshUserSource')
    if not sp:raise SystemExit('v0881 refreshUserSource anchor missing')
    geo=r'''    private static String v881HydroGeo(List<StationDot> list){
        try{JSONArray f=new JSONArray();for(StationDot s:list){if(s==null)continue;f.put(pointFeature(s.lon,s.lat,s.name));}
            return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    }
    private static String v881WaterGeo(List<StationDot> list,String group){
        try{JSONArray f=new JSONArray();for(StationDot s:list){
            if(!v881IsWaterbody(s))continue;String g=s.fresh?normalizeStage(s.stage):"stale";if(!group.equals(g))continue;
            f.put(pointFeature(s.lon,s.lat,s.name));
        }return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    }
    private void v881EnsureHydroWaterbodyLayers(){
        if(!styleReady||style==null)return;
        ensurePointSource("fs-hydro-sites","fs-hydro-sites-layer","#27D7E8",7.0f,0.22f);
        ensurePointSource("fs-water-stale","fs-water-stale-layer","#64748B",7.3f,0.96f);
        ensurePointSource("fs-water-normal","fs-water-normal-layer","#16A34A",7.3f,0.96f);
        ensurePointSource("fs-water-alert","fs-water-alert-layer","#FFD447",7.6f,0.98f);
        ensurePointSource("fs-water-warning","fs-water-warning-layer","#FF9418",7.9f,1.0f);
        ensurePointSource("fs-water-danger","fs-water-danger-layer","#F04444",8.2f,1.0f);
    } // V0881_HYDRO_WATERBODY_GEO

'''
    m=m[:sp[0]]+geo+m[sp[0]:]

if 'V0881_PUBLISH_HYDRO_WATERBODY_LAYERS' not in m:
    sp=method_span(m,'refreshStationSources')
    if not sp:raise SystemExit('v0881 refreshStationSources missing')
    block=m[sp[0]:sp[1]]
    ins=block.rfind('}')
    if ins<0:raise SystemExit('v0881 refreshStationSources close missing')
    publish=r'''
        v881EnsureHydroWaterbodyLayers();
        setGeo("fs-hydro-sites",v881HydroGeo(snapshot));
        setGeo("fs-water-stale",v881WaterGeo(snapshot,"stale"));
        setGeo("fs-water-normal",v881WaterGeo(snapshot,"normal"));
        setGeo("fs-water-alert",v881WaterGeo(snapshot,"alert"));
        setGeo("fs-water-warning",v881WaterGeo(snapshot,"warning"));
        setGeo("fs-water-danger",v881WaterGeo(snapshot,"danger")); // V0881_PUBLISH_HYDRO_WATERBODY_LAYERS
'''
    block=block[:ins]+publish+block[ins:]
    m=m[:sp[0]]+block+m[sp[1]:]

# -----------------------------------------------------------------------------
# C) Waterbody tap detail: direct official status/source/time, never fabricated.
# -----------------------------------------------------------------------------
if 'V0881_WATERBODY_DETAIL_POPUP' not in m:
    sp=method_span(m,'nearestStation')
    if not sp:raise SystemExit('v0881 nearestStation anchor missing')
    detail=r'''    private StationDot v881NearestWaterSite(double la,double lo){
        StationDot best=null;double d=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){if(!v881IsWaterbody(s))continue;double x=km(la,lo,s.lat,s.lon);if(x<d){d=x;best=s;}}}
        return best;
    }
    private void v881ShowWaterSite(StationDot s,double tapLat,double tapLon){
        if(s==null)return;StringBuilder b=new StringBuilder();
        String type=s.v881WaterKind.isEmpty()?s.v881WaterType:s.v881WaterKind;
        b.append(englishUi?"Type: ":"प्रकार: ").append(type.isEmpty()?"official hydrology site":type);
        if(s.riverName!=null&&!s.riverName.trim().isEmpty())b.append("\n").append(englishUi?"River / waterbody: ":"नदी / जलस्रोत: ").append(s.riverName);
        b.append("\n").append(englishUi?"Status: ":"स्थिति: ");
        if(s.fresh)b.append(normalizeStage(s.stage).toUpperCase(Locale.ROOT)).append(" • LIVE");
        else b.append(englishUi?"NO CURRENT OFFICIAL READING":"हालको आधिकारिक reading छैन");
        if(Double.isFinite(s.level))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Water level: ":"पानीको सतह: ",s.level));
        if(Double.isFinite(s.v881Warning))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Warning level: ":"Warning level: ",s.v881Warning));
        if(Double.isFinite(s.v881Danger))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Danger level: ":"Danger level: ",s.v881Danger));
        if(s.v881At>0L)b.append("\n").append(englishUi?"Observation time: ":"मापन समय: ").append(v881Time(s.v881At));
        if(s.v881Source!=null&&!s.v881Source.isEmpty())b.append("\n").append(englishUi?"Official source: ":"आधिकारिक स्रोत: ").append(s.v881Source);
        b.append(String.format(Locale.US,"\n%s%.2f km",englishUi?"Tap distance: ":"Tap दूरी: ",km(tapLat,tapLon,s.lat,s.lon)));
        if(!s.fresh)b.append("\n\n").append(englishUi?
                "The official site is shown, but FloodSafe will not invent a live status or level when the source has no current observation.":
                "आधिकारिक site देखाइएको छ, तर source मा हालको observation नभए FloodSafe ले live status वा level बनाउँदैन।");
        new AlertDialog.Builder(getContext()).setTitle(s.name).setMessage(b.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0881_WATERBODY_DETAIL_POPUP

'''
    m=m[:sp[0]]+detail+m[sp[0]:]

# Insert waterbody hit-testing before the ordinary station hit test while preserving rain,
# station and river behavior already present in v0.8.80.
if 'V0881_WATERBODY_TAP_PRIORITY' not in m:
    sp=method_span(m,'onMapClick')
    if not sp:raise SystemExit('v0881 onMapClick missing')
    block=m[sp[0]:sp[1]]
    z=re.search(r'double\s+zoom\s*=\s*[^;]+;',block)
    if not z:raise SystemExit('v0881 onMapClick zoom anchor missing')
    hit=r'''
        StationDot v881Water=v881NearestWaterSite(p.getLatitude(),p.getLongitude());
        double v881WaterThreshold=Math.max(0.20,Math.min(2.4,1.9/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        if(v881Water!=null&&km(p.getLatitude(),p.getLongitude(),v881Water.lat,v881Water.lon)<=v881WaterThreshold){
            v881ShowWaterSite(v881Water,p.getLatitude(),p.getLongitude());return true;
        } // V0881_WATERBODY_TAP_PRIORITY
'''
    block=block[:z.end()]+hit+block[z.end():]
    m=m[:sp[0]]+block+m[sp[1]:]

# -----------------------------------------------------------------------------
# D) River tap now ALWAYS opens a river detail card. Exact same-river official gauge data
#    is embedded when available; otherwise river identity/type/source still remains visible.
# -----------------------------------------------------------------------------
show=r'''    private void showRiver(RiverWay r,double la,double lo){
        StationDot gauge=v880SameRiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        StringBuilder b=new StringBuilder();
        b.append(englishUi?"River / stream: ":"नदी / खोला: ").append(riverName);
        if(r!=null&&r.type!=null&&!r.type.trim().isEmpty())b.append("\n").append(englishUi?"Map type: ":"नक्सा प्रकार: ").append(r.type);
        b.append(String.format(Locale.US,"\n%s%.5f, %.5f",englishUi?"Tapped at: ":"थिचेको स्थान: ",la,lo));
        if(gauge!=null){
            b.append("\n\n").append(englishUi?"Official same-river hydrology gauge":"आधिकारिक same-river hydrology gauge");
            b.append("\n").append(englishUi?"Station: ":"Station: ").append(gauge.name);
            b.append(String.format(Locale.US," • %.2f km",km(la,lo,gauge.lat,gauge.lon)));
            b.append("\n").append(englishUi?"Status: ":"स्थिति: ");
            if(gauge.fresh)b.append(normalizeStage(gauge.stage).toUpperCase(Locale.ROOT)).append(" • LIVE");
            else b.append(englishUi?"NOT LIVE / LATEST OFFICIAL":"LIVE होइन / पछिल्लो आधिकारिक");
            if(Double.isFinite(gauge.level))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Water level: ":"पानीको सतह: ",gauge.level));
            if(Double.isFinite(gauge.v881Warning))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Warning level: ":"Warning level: ",gauge.v881Warning));
            if(Double.isFinite(gauge.v881Danger))b.append(String.format(Locale.US,"\n%s%.3f m",englishUi?"Danger level: ":"Danger level: ",gauge.v881Danger));
            if(gauge.v881At>0L)b.append("\n").append(englishUi?"Observation time: ":"मापन समय: ").append(v881Time(gauge.v881At));
            if(gauge.v881Source!=null&&!gauge.v881Source.isEmpty())b.append("\n").append(englishUi?"Official source: ":"आधिकारिक स्रोत: ").append(gauge.v881Source);
            if(v881IsWaterbody(gauge))b.append("\n").append(englishUi?"Waterbody type: ":"जलस्रोत प्रकार: ").append(gauge.v881WaterKind);
        }else{
            b.append("\n\n").append(englishUi?
                    "No official gauge in the current catalog can be safely mapped to this exact named river segment.":
                    "यो नदीको यही खण्डसँग सुरक्षित रूपमा मिल्ने आधिकारिक gauge हालको catalog मा भेटिएन।");
            b.append("\n").append(englishUi?
                    "FloodSafe does not borrow a nearby different-river station.":
                    "FloodSafe ले नजिक भएको मात्र आधारमा अर्को नदीको station जोड्दैन।");
        }
        b.append("\n\n").append(englishUi?"River geometry source: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा स्रोत: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(b.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0881_RIVER_FIRST_CLASS_DETAIL V0881_NO_STATION_REDIRECT
'''
m=replace_method(m,'showRiver',show)

# Release identity.
g=re.sub(r'versionCode\s+100\b','versionCode 101',g,count=1)
g=g.replace("versionName '0.8.80'","versionName '0.8.81'",1)
if 'versionCode 101' not in g or "versionName '0.8.81'" not in g:raise SystemExit('v0881 version bump failed')

need=[
    'V0881_WATERBODY_DOT_FIELDS','V0881_RAW_OFFICIAL_METADATA_HELPERS','V0881_READ_WATERBODY_METADATA',
    'V0881_HYDRO_WATERBODY_GEO','V0881_PUBLISH_HYDRO_WATERBODY_LAYERS','V0881_WATERBODY_DETAIL_POPUP',
    'V0881_WATERBODY_TAP_PRIORITY','V0881_RIVER_FIRST_CLASS_DETAIL','V0881_NO_STATION_REDIRECT',
    'V0880_VISIBLE_REGION_ALL_TILES','V0880_EXACT_SAME_RIVER_ONLY','V0877_CLEAN_FRESH_ONLY_LIVE'
]
for x in need:
    if x not in m:raise SystemExit('v0881 map contract missing: '+x)
if 'stationTapListener.onStationTap(gauge.original)' in m[m.find('private void showRiver'):m.find('private void showRiver')+5000]:
    raise SystemExit('v0881 river popup still redirects to station detail')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.81 PASS: first-class river detail + hydrology layer + lake/reservoir/outlet status/source popup; safety truth unchanged')
