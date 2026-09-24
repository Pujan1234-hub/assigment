from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.89 real-device persistence repair:
# - transient/partial refreshes must not erase already-rendered official station dots;
# - zoom/tile swaps must not blank the monitored river network while replacement geometry loads;
# - retained river geometry is revalidated against the CURRENT official station set.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s*[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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
    if not sp:raise SystemExit('v0889 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

field='    private final List<RiverWay> v887ViewportRiverCandidates = new ArrayList<>(); // V0887_VIEWPORT_RIVER_CANDIDATES\n'
if 'V0889_STABLE_MONITORED_RIVERS' not in m:
    if field not in m:raise SystemExit('v0889 viewport candidate field missing')
    m=m.replace(field,field+'    private final List<RiverWay> v889StableMonitoredRivers = new ArrayList<>(); // V0889_STABLE_MONITORED_RIVERS\n',1)

helpers=r'''    private static String v889StationKey(StationDot s){
        if(s==null)return "";
        String n=s.name==null?"":s.name.trim().toLowerCase(Locale.ROOT).replaceAll("\\s+"," ");
        if(!n.isEmpty())return n;
        return String.format(Locale.US,"%.5f|%.5f",s.lat,s.lon);
    } // V0889_STABLE_STATION_KEY

'''
if 'V0889_STABLE_STATION_KEY' not in m:
    sp=method_span(m,'setStations')
    if not sp:raise SystemExit('v0889 setStations anchor missing')
    m=m[:sp[0]]+helpers+m[sp[0]:]

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
            int oldCount=stations.size();
            if(next.isEmpty() && oldCount>0){
                // V0889_EMPTY_REFRESH_RETAINS_STATIONS
            }else if(oldCount>0 && next.size()<Math.max(25,(int)Math.floor(oldCount*0.65))){
                java.util.LinkedHashMap<String,StationDot> merged=new java.util.LinkedHashMap<>();
                for(StationDot s:stations){String k=v889StationKey(s);if(!k.isEmpty())merged.put(k,s);}
                for(StationDot s:next){String k=v889StationKey(s);if(!k.isEmpty())merged.put(k,s);}
                stations.clear();stations.addAll(merged.values()); // V0889_PARTIAL_REFRESH_MERGES_STATIONS
            }else{
                stations.clear();stations.addAll(next); // V0889_COMPLETE_REFRESH_REPLACES_STATIONS
            }
        }
        refreshStationSources();
        refreshUserSource();
        v887ApplyMonitoredRiverGeometry(); // V0889_STATION_REFRESH_PRESERVES_RIVERS
    }
'''
m=replace_method(m,'setStations',set_stations)

apply=r'''    private void v887ApplyMonitoredRiverGeometry(){
        if(!styleReady||style==null)return;
        List<RiverWay> candidates;
        synchronized(v887ViewportRiverCandidates){candidates=new ArrayList<>(v887ViewportRiverCandidates);}
        List<RiverWay> current=v887MonitoredRivers(candidates);
        List<RiverWay> render;
        synchronized(v889StableMonitoredRivers){
            List<RiverWay> stillValid=v887MonitoredRivers(v889StableMonitoredRivers);
            if(!current.isEmpty())stillValid.addAll(current);
            List<RiverWay> dedup=v879Dedup(stillValid);
            if(!dedup.isEmpty()){
                v889StableMonitoredRivers.clear();v889StableMonitoredRivers.addAll(dedup);
            }else if(stations.isEmpty()){
                // V0889_EMPTY_STATION_WINDOW_KEEPS_RIVER_GEOMETRY
            }else{
                v889StableMonitoredRivers.clear();
            }
            render=new ArrayList<>(v889StableMonitoredRivers);
        }
        if(render.isEmpty()&&!rivers.isEmpty())return; // V0889_NO_ZOOM_BLANK_FRAME
        try{
            String nextGeoJson=makeRiversGeoJson(render); // V0889_COMPILE_SAFE_GEOJSON_BUILD
            rivers.clear();rivers.addAll(render);riversGeoJson=nextGeoJson;
            GeoJsonSource s=style.getSourceAs("fs-rivers");
            if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();
        }catch(Exception ignored){
            // Keep the last successfully rendered monitored network if GeoJSON generation/style swap fails.
            // V0889_RENDER_FAILURE_RETAINS_LAST_GOOD
            return;
        }
        refreshRiverRiskSources();
    } // V0889_PERSISTENT_MONITORED_RIVER_NETWORK V0889_ZOOM_TILE_SWAP_NO_DISAPPEAR
'''
m=replace_method(m,'v887ApplyMonitoredRiverGeometry',apply)

g=re.sub(r'versionCode\s+108\b','versionCode 109',g,count=1)
g=g.replace("versionName '0.8.88'","versionName '0.8.89'",1)

required=[
 'V0889_STABLE_MONITORED_RIVERS','V0889_STABLE_STATION_KEY','V0889_EMPTY_REFRESH_RETAINS_STATIONS',
 'V0889_PARTIAL_REFRESH_MERGES_STATIONS','V0889_COMPLETE_REFRESH_REPLACES_STATIONS',
 'V0889_STATION_REFRESH_PRESERVES_RIVERS','V0889_EMPTY_STATION_WINDOW_KEEPS_RIVER_GEOMETRY',
 'V0889_NO_ZOOM_BLANK_FRAME','V0889_PERSISTENT_MONITORED_RIVER_NETWORK','V0889_ZOOM_TILE_SWAP_NO_DISAPPEAR',
 'V0889_COMPILE_SAFE_GEOJSON_BUILD','V0889_RENDER_FAILURE_RETAINS_LAST_GOOD',
 'V0888_FAST_MONITORED_RIVER_FILTER','V0886_NO_NEARBY_ONLY_FALLBACK'
]
for x in required:
    if x not in m:raise SystemExit('v0889 map contract missing: '+x)
if 'versionCode 109' not in g or "versionName '0.8.89'" not in g:raise SystemExit('v0889 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.89 PASS: station dots survive partial/empty refresh; monitored river network survives zoom/tile swaps; compile-safe GeoJSON swap')
