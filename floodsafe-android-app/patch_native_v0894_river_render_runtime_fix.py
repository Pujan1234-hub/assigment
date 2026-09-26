from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.94: make the dedicated river renderer robust on real devices.
# 1) post-clipped assets may contain LineString OR MultiLineString.
# 2) official observations refresh every second; geometry matching must not restart every second.
# 3) publish a visible cyan river source as soon as one station-river match completes, then only
#    recalculate geometry when station identity/coordinates change.

field='    private boolean v893PulseStarted = false; // V0893_DEDICATED_STATION_RIVER_LAYER'
if field not in m: raise SystemExit('v893 field anchor missing')
m=m.replace(field, field+'\n    private volatile boolean v894RiverMatchRunning = false;\n    private volatile String v894StationGeometryFingerprint = "";\n    private volatile String v894PendingFingerprint = ""; // V0894_RIVER_MATCH_DEBOUNCE',1)

# helper to replace a whole Java method by brace matching
def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[A-Za-z0-9_<>\[\]?., ]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());d=0;quote=None;esc=False
    for i in range(op,len(text)):
        c=text[i]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in ('\"',"'"):quote=c
            elif c=='{':d+=1
            elif c=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def replace_method(text,name,block):
    s=method_span(text,name)
    if not s: raise SystemExit('missing method '+name)
    return text[:s[0]]+block+text[s[1]:]

load=r'''    private void v893LoadDedicatedRiverBase(){
        io.execute(()->{
            try{
                String raw=readAsset("data/nepal-waterways-medium-v0842.geojson");
                JSONObject fc=new JSONObject(raw);JSONArray fs=fc.optJSONArray("features");
                List<RiverWay> parsed=new ArrayList<>();
                if(fs!=null) for(int i=0;i<fs.length();i++){
                    JSONObject f=fs.optJSONObject(i);if(f==null)continue;
                    JSONObject geom=f.optJSONObject("geometry");if(geom==null)continue;
                    JSONObject p=f.optJSONObject("properties");
                    String nm=p==null?"नदी / खोला":firstNonEmpty(p.optString("name"),p.optString("name_en"),p.optString("name_osm"),"नदी / खोला");
                    String typ=p==null?"river":p.optString("type","river");
                    String gt=geom.optString("type","");
                    if("LineString".equals(gt)){
                        RiverWay r=v894RiverFromCoords(geom.optJSONArray("coordinates"),nm,typ);if(r!=null)parsed.add(r);
                    }else if("MultiLineString".equals(gt)){
                        JSONArray lines=geom.optJSONArray("coordinates");
                        if(lines!=null)for(int j=0;j<lines.length();j++){RiverWay r=v894RiverFromCoords(lines.optJSONArray(j),nm,typ);if(r!=null)parsed.add(r);}
                    }
                }
                synchronized(v893AllRivers){v893AllRivers.clear();v893AllRivers.addAll(parsed);}
                main.post(this::v893EnsureDedicatedLayers);
                v893RefreshDedicatedStationRivers();
            }catch(Exception ignored){}
        });
    } // V0894_LINE_AND_MULTILINE_ASSET_PARSER

    private RiverWay v894RiverFromCoords(JSONArray cs,String name,String type){
        if(cs==null||cs.length()<2)return null;RiverWay r=new RiverWay();r.name=name;r.type=type;
        for(int j=0;j<cs.length();j++){JSONArray q=cs.optJSONArray(j);if(q==null||q.length()<2)continue;double lo=q.optDouble(0,Double.NaN),la=q.optDouble(1,Double.NaN);if(Double.isFinite(lo)&&Double.isFinite(la)&&isNepalish(la,lo))r.points.add(new double[]{lo,la});}
        return r.points.size()>=2?r:null;
    }
'''
m=replace_method(m,'v893LoadDedicatedRiverBase',load)

refresh=r'''    private void v893RefreshDedicatedStationRivers(){
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        final List<RiverWay> all; synchronized(v893AllRivers){all=new ArrayList<>(v893AllRivers);}
        if(ss.isEmpty()||all.isEmpty())return;
        StringBuilder fb=new StringBuilder();
        for(StationDot s:ss)if(s!=null&&Double.isFinite(s.lat)&&Double.isFinite(s.lon))fb.append(v881Norm(s.name)).append('@').append(Math.round(s.lat*10000d)).append(',').append(Math.round(s.lon*10000d)).append(';');
        final String fingerprint=fb.toString();

        // Same stations, new 1-second readings: do NOT rematch 4k river geometries.
        if(fingerprint.equals(v894StationGeometryFingerprint)&&!v893StationRivers.isEmpty()){
            v894UpdateDedicatedStatus(ss);return;
        }
        v894PendingFingerprint=fingerprint;
        if(v894RiverMatchRunning)return;
        v894RiverMatchRunning=true;
        io.execute(()->{
            try{
                java.util.LinkedHashSet<RiverWay> chosen=new java.util.LinkedHashSet<>();
                java.util.LinkedHashSet<String> names=new java.util.LinkedHashSet<>();
                for(StationDot s:ss){
                    if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                    String sn=v881Norm(s.name);RiverWay bestName=null,bestNear=null;double dn=Double.POSITIVE_INFINITY,da=Double.POSITIVE_INFINITY;
                    for(RiverWay r:all){
                        if(r==null||r.points==null||r.points.size()<2)continue;
                        // Cheap bbox/point proximity prefilter before segment distance.
                        boolean plausible=false;int stride=Math.max(1,r.points.size()/12);
                        for(int pi=0;pi<r.points.size();pi+=stride){double[] q=r.points.get(pi);if(Math.abs(q[1]-s.lat)<0.35&&Math.abs(q[0]-s.lon)<0.40){plausible=true;break;}}
                        if(!plausible)continue;
                        double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(!Double.isFinite(d)||d>35d)continue;
                        String rn=v881Norm(r.name);boolean nm=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                        if(nm&&d<dn){dn=d;bestName=r;}if(d<da){da=d;bestNear=r;}
                    }
                    RiverWay seed=bestName!=null?bestName:bestNear;
                    if(seed!=null){chosen.add(seed);String k=v881Norm(seed.name);if(!k.isEmpty())names.add(k);}
                }
                if(!names.isEmpty())for(RiverWay r:all){String rn=v881Norm(r.name);if(rn.isEmpty())continue;for(String k:names){if(rn.equals(k)||rn.contains(k)||k.contains(rn)){chosen.add(r);break;}}}
                final List<RiverWay> selected=new ArrayList<>(chosen);
                final String geo=selected.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(selected);
                main.post(()->{
                    v893StationRivers.clear();v893StationRivers.addAll(selected);v893StationRiverGeoJson=geo;v894StationGeometryFingerprint=fingerprint;
                    v893EnsureDedicatedLayers();v893SetGeo("fs-v893-station-rivers",geo);v894UpdateDedicatedStatus(ss);
                });
            }catch(Exception ignored){}finally{
                v894RiverMatchRunning=false;
                if(!v894PendingFingerprint.equals(v894StationGeometryFingerprint))main.post(this::v893RefreshDedicatedStationRivers);
            }
        });
    } // V0894_NO_1SEC_GEOMETRY_REMATCH

    private void v894UpdateDedicatedStatus(List<StationDot> ss){
        if(v893StationRivers.isEmpty())return;io.execute(()->{try{
            List<RiverWay> al=new ArrayList<>(),wa=new ArrayList<>(),da=new ArrayList<>();
            for(RiverWay r:new ArrayList<>(v893StationRivers)){String st=v884Stage(r,ss);if("danger".equals(st))da.add(r);else if("warning".equals(st))wa.add(r);else if("alert".equals(st))al.add(r);}
            final String ag=al.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(al),wg=wa.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(wa),dg=da.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(da);
            main.post(()->{v893EnsureDedicatedLayers();v893SetGeo("fs-v893-alert",ag);v893SetGeo("fs-v893-warning",wg);v893SetGeo("fs-v893-danger",dg);});
        }catch(Exception ignored){}});
    } // V0894_STATUS_ONLY_REFRESH
'''
m=replace_method(m,'v893RefreshDedicatedStationRivers',refresh)

# version bump based on patched build state from v0.8.93
g=re.sub(r'versionCode\s+113\b','versionCode 114',g,count=1)
g=g.replace("versionName '0.8.93'","versionName '0.8.94'",1)

for token in ['V0894_RIVER_MATCH_DEBOUNCE','V0894_LINE_AND_MULTILINE_ASSET_PARSER','V0894_NO_1SEC_GEOMETRY_REMATCH','V0894_STATUS_ONLY_REFRESH']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.94'" not in g or 'versionCode 114' not in g: raise SystemExit('version bump failed')
m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.94 PASS: LineString+MultiLineString parser + debounced station-river match + status-only 1s refresh')
