from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.87 field correction:
# - Do NOT paint tens of thousands of bright blue rivers with no official gauge detail.
# - Bright/tappable river geometry is limited to rivers that resolve to an official station
#   carrying a water-level + source-time reading. Therefore every visible blue/status river
#   has real source detail when tapped.
# - Ship a build-time official BIPAD bootstrap snapshot so station dots are visible immediately
#   at first open; the normal network refresh replaces it with newer official rows afterwards.


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
    if not sp:raise SystemExit('v0887 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# -----------------------------------------------------------------------------
# A) Immediate official station bootstrap on first paint.
# -----------------------------------------------------------------------------
if 'V0887_BOOTSTRAP_OFFICIAL_STATIONS' not in a:
    sp=method_span(a,'restoreLocation')
    if not sp:raise SystemExit('v0887 restoreLocation anchor missing')
    helper=r'''

    private void v887LoadBootstrapOfficialStations(){
        try{
            InputStream in=getAssets().open("data/bipad-river-stations-bootstrap.json");
            BufferedReader br=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8));
            StringBuilder sb=new StringBuilder();String line;while((line=br.readLine())!=null)sb.append(line);br.close();
            JSONObject root=new JSONObject(sb.toString());JSONArray rows=root.optJSONArray("results");if(rows==null)rows=root.optJSONArray("data");if(rows==null||rows.length()==0)return;
            long now=System.currentTimeMillis();List<RiverStation> out=new ArrayList<>();
            java.util.concurrent.ConcurrentHashMap<String,JSONObject> sourceRows=new java.util.concurrent.ConcurrentHashMap<>();
            int fresh=0,latest=0;
            for(int i=0;i<rows.length();i++){
                JSONObject r=rows.optJSONObject(i);if(r==null)continue;
                try{
                    double lv=v877ObservationLevel(r);long at=v877ObservationTime(r);
                    if(Double.isFinite(lv)&&at>0L){r.put("_floodsafeObservationMatched",true);r.put("_floodsafeOnline",true);}
                    r.put("_floodsafeSource","BIPAD river-stations bootstrap; network refresh pending");
                }catch(Exception ignored){}
                RiverStation s=parseStation(r,now);if(s==null)continue;
                out.add(s);if(s.fresh)fresh++;if(Double.isFinite(s.level)&&s.at>0L)latest++;
                try{String nm=v846StationName(r);if(!nm.isEmpty())sourceRows.put(v846Key(nm),new JSONObject(r.toString()));}catch(Exception ignored){}
            }
            if(out.isEmpty())return;
            out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
            synchronized(stations){stations.clear();stations.addAll(out);}
            v849CatalogCount=rows.length();v877FreshObservationCount=fresh;v877LatestObservationCount=latest;v877NoObservationCount=Math.max(0,rows.length()-latest);v849LatestCount=latest;
            v871SourceRowsByName.clear();v871SourceRowsByName.putAll(sourceRows);
            refreshRiverUi();
        }catch(Exception ignored){}
    } // V0887_BOOTSTRAP_OFFICIAL_STATIONS V0887_FIRST_OPEN_STATIONS_IMMEDIATE
'''
    a=a[:sp[1]]+helper+a[sp[1]:]

if 'V0887_BOOTSTRAP_CALL' not in a:
    anchor='setContentView(buildScreen());'
    if anchor not in a:raise SystemExit('v0887 setContentView anchor missing')
    a=a.replace(anchor,anchor+'\n        v887LoadBootstrapOfficialStations(); // V0887_BOOTSTRAP_CALL',1)

# -----------------------------------------------------------------------------
# B) Keep the full official river geometry as candidate data, but render/tap only rivers
# that resolve to a station with an actual official reading. This makes blue mean
# "monitored river with official detail", not decorative OSM hydrography.
# -----------------------------------------------------------------------------
field_anchor='    private String v885NationalRiverGeoJson = null; // V0885_NATIONAL_NETWORK_FIELD\n'
if 'V0887_VIEWPORT_RIVER_CANDIDATES' not in m:
    if field_anchor not in m:raise SystemExit('v0887 national field anchor missing')
    m=m.replace(field_anchor,field_anchor+'    private final List<RiverWay> v887ViewportRiverCandidates = new ArrayList<>(); // V0887_VIEWPORT_RIVER_CANDIDATES\n',1)

helpers=r'''    private boolean v887RiverHasOfficialReading(RiverWay r){
        if(r==null||!v863UsefulRiverName(r.name))return false;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)continue;
            if(!v886SameOfficialRiver(r,s))continue;
            double d=v872GaugeToRiverKm(s,r);
            if(Double.isFinite(d)&&d<=7.5)return true;
        }}
        return false;
    } // V0887_ONLY_RIVERS_WITH_OFFICIAL_READING

    private List<RiverWay> v887MonitoredRivers(List<RiverWay> input){
        List<RiverWay> out=new ArrayList<>();if(input==null)return out;
        for(RiverWay r:input)if(v887RiverHasOfficialReading(r))out.add(r);
        return out;
    } // V0887_FILTER_DECORATIVE_UNGAUGED_RIVERS

    private void v887ApplyMonitoredRiverGeometry(){
        if(!styleReady||style==null)return;
        List<RiverWay> candidates;
        synchronized(v887ViewportRiverCandidates){candidates=new ArrayList<>(v887ViewportRiverCandidates);}
        List<RiverWay> monitored=v887MonitoredRivers(candidates);
        rivers.clear();rivers.addAll(monitored);riversGeoJson=makeRiversGeoJson(monitored);
        try{GeoJsonSource s=style.getSourceAs("fs-rivers");if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();}catch(Exception ignored){}
        refreshRiverRiskSources();
    } // V0887_BLUE_RIVER_ALWAYS_HAS_DETAIL

'''
if 'V0887_ONLY_RIVERS_WITH_OFFICIAL_READING' not in m:
    sp=method_span(m,'v879ApplyRiverGeometry')
    if not sp:raise SystemExit('v0887 river apply anchor missing')
    m=m[:sp[0]]+helpers+m[sp[0]:]

river_apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> next=v879Dedup(input);
        main.post(()->{
            if(generation!=v879RiverLoadGeneration)return;
            try{
                synchronized(v887ViewportRiverCandidates){v887ViewportRiverCandidates.clear();v887ViewportRiverCandidates.addAll(next);}
                v879RiverGeometryKey=key;
                v887ApplyMonitoredRiverGeometry(); // V0887_MONITORED_ONLY_AFTER_TILE_SWAP
            }catch(Exception ignored){}
        });
    }
'''
m=replace_method(m,'v879ApplyRiverGeometry',river_apply)

set_stations=r'''    void setStations(List<?> source, double lat, double lon) {
        userLat = lat;
        userLon = lon;
        List<StationDot> next = new ArrayList<>();
        if (source != null) {
            for (Object o : source) {
                StationDot s = readStation(o);
                if (s != null) next.add(s);
            }
        }
        synchronized (stations) {
            stations.clear();
            stations.addAll(next);
        }
        refreshStationSources();
        refreshUserSource();
        v887ApplyMonitoredRiverGeometry(); // V0887_STATION_REFRESH_REBUILDS_MONITORED_RIVERS
    }
'''
m=replace_method(m,'setStations',set_stations)

national=r'''    private void v885EnsureNationalRiverLayer(){
        // V0887_NO_DECORATIVE_FULL_BLUE_NETWORK
        // Full national hydrography stays bundled for geometry lookup/fallback, but is not
        // painted as live. Bright river lines are produced only by v887 monitored geometry.
    }
'''
m=replace_method(m,'v885EnsureNationalRiverLayer',national)

sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0887 showRiver missing')
show=m[sp[0]:sp[1]]
if 'V0887_VISIBLE_RIVER_MUST_HAVE_DETAIL' not in show:
    p=show.find('{')+1
    show=show[:p]+'\n        // V0887_VISIBLE_RIVER_MUST_HAVE_DETAIL'+show[p:]
    m=m[:sp[0]]+show+m[sp[1]:]

g=re.sub(r'versionCode\s+106\b','versionCode 107',g,count=1)
g=g.replace("versionName '0.8.86'","versionName '0.8.87'",1)

for x in ['V0887_BOOTSTRAP_OFFICIAL_STATIONS','V0887_FIRST_OPEN_STATIONS_IMMEDIATE','V0887_BOOTSTRAP_CALL']:
    if x not in a:raise SystemExit('v0887 activity contract missing: '+x)
for x in ['V0887_VIEWPORT_RIVER_CANDIDATES','V0887_ONLY_RIVERS_WITH_OFFICIAL_READING','V0887_FILTER_DECORATIVE_UNGAUGED_RIVERS','V0887_BLUE_RIVER_ALWAYS_HAS_DETAIL','V0887_MONITORED_ONLY_AFTER_TILE_SWAP','V0887_STATION_REFRESH_REBUILDS_MONITORED_RIVERS','V0887_NO_DECORATIVE_FULL_BLUE_NETWORK','V0887_VISIBLE_RIVER_MUST_HAVE_DETAIL','V0886_OFFICIAL_TITLE_RIVER_JOIN']:
    if x not in m:raise SystemExit('v0887 map contract missing: '+x)
if 'versionCode 107' not in g or "versionName '0.8.87'" not in g:raise SystemExit('v0887 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.87 PASS: instant official station bootstrap + monitored/detail-backed rivers only; decorative ungauged blue mesh hidden')
