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

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[A-Za-z0-9_<>\[\]?., ]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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
    if not sp:raise SystemExit('v0883 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

old='final java.util.LinkedHashSet<String> v882ActiveKeys=!v882RiverWatchKeys.isEmpty()?v882RiverWatchKeys:v882TrimedKeys;'
new=('java.util.LinkedHashSet<String> v883UnionKeys=new java.util.LinkedHashSet<>(v882RiverWatchKeys);\n'
     '        v883UnionKeys.addAll(v882TrimedKeys);\n'
     '        final java.util.LinkedHashSet<String> v882ActiveKeys=v883UnionKeys; // V0883_BIPAD_RIVER_TRIMED_UNION')
if old not in a: raise SystemExit('v0883 active-set anchor missing')
a=a.replace(old,new,1)

field='    private final List<RiverWay> rivers = new ArrayList<>();'
if field not in m: raise SystemExit('v0883 rivers field anchor missing')
m=m.replace(field,field+'\n    private final List<RiverWay> v883StationRivers = new ArrayList<>(); // V0883_STATION_RIVER_CACHE',1)

apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> base=v879Dedup(input);
        final List<StationDot> ss;
        synchronized(stations){ss=new ArrayList<>(stations);}
        io.execute(()->{
            final List<RiverWay> active=v881OnlyLiveStationRivers(base,ss);
            final String baseGeo;
            final String activeGeo;
            try{
                baseGeo=base.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(base);
                activeGeo=active.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(active);
            }catch(Exception e){return;}
            main.post(()->{
                if(generation!=v879RiverLoadGeneration)return;
                try{
                    rivers.clear();rivers.addAll(base);
                    v883StationRivers.clear();v883StationRivers.addAll(active);
                    riversGeoJson=baseGeo;
                    v879RiverGeometryKey=key;
                    if(styleReady&&style!=null){
                        GeoJsonSource s=style.getSourceAs("fs-rivers");
                        if(s!=null)s.setGeoJson(baseGeo);else installGeoLayers();
                        v883ApplyStationRiverOverlay(activeGeo);
                    }else installGeoLayers();
                }catch(Exception ignored){}
            });
        });
    } // V0883_BACKGROUND_RIVER_MATCH_NO_ANR
'''
m=replace_method(m,'v879ApplyRiverGeometry',apply)

anchor='    private static int v879TileX(double lon)'
if anchor not in m: raise SystemExit('v0883 helper anchor missing')
helper=r'''    private void v883ApplyStationRiverOverlay(String geo){
        if(!styleReady||style==null)return;
        try{
            GeoJsonSource src=style.getSourceAs("fs-station-rivers");
            if(src==null){
                style.addSource(new GeoJsonSource("fs-station-rivers",geo));
                style.addLayer(new LineLayer("fs-station-river-glow","fs-station-rivers").withProperties(
                        lineColor("#00d9ff"),lineWidth(7.0f),lineOpacity(0.34f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-station-river-core","fs-station-rivers").withProperties(
                        lineColor("#55e7ff"),lineWidth(2.35f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            }else src.setGeoJson(geo);
        }catch(Exception ignored){}
    } // V0883_STATION_ONLY_FLOW_GLOW

'''
m=m.replace(anchor,helper+anchor,1)

# Existing animation implementations changed across earlier patches. Redirect common forms when present,
# but do not fail the build if the active animation uses a different helper; the station overlay itself
# remains the authoritative strong glow and the base river geometry remains visible.
m=m.replace('Math.min(36, rivers.size())','Math.min(36, v883StationRivers.size())',1)
m=m.replace('RiverWay r = rivers.get(i);','RiverWay r = v883StationRivers.get(i);',1)
m=m.replace('RiverWay r=rivers.get(i);','RiverWay r=v883StationRivers.get(i);',1)

# Best-effort reduce base network intensity so the station-bearing overlay is visually dominant.
m=m.replace('lineWidth(4.0f), lineOpacity(0.55f)','lineWidth(3.0f), lineOpacity(0.30f)',1)
m=m.replace('lineWidth(1.65f), lineOpacity(0.96f)','lineWidth(1.45f), lineOpacity(0.82f)',1)

g=re.sub(r'versionCode\s+102\b','versionCode 103',g,count=1)
g=g.replace("versionName '0.8.82'","versionName '0.8.83'",1)

for x in ['V0883_BIPAD_RIVER_TRIMED_UNION','V0883_STATION_RIVER_CACHE','V0883_BACKGROUND_RIVER_MATCH_NO_ANR','V0883_STATION_ONLY_FLOW_GLOW']:
    if x not in a and x not in m:raise SystemExit('missing '+x)
if 'versionCode 103' not in g or "versionName '0.8.83'" not in g:raise SystemExit('v0883 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.83 PASS: BIPAD river+trimed union + no-ANR background station matching + visible base rivers + station-only strong glow')
