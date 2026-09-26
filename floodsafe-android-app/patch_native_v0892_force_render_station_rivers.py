from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def span(text,name):
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

def repl(text,name,block):
    s=span(text,name)
    if not s: raise SystemExit('missing method '+name)
    return text[:s[0]]+block+text[s[1]:]

apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> base=v879Dedup(input);
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        io.execute(()->{
            java.util.LinkedHashSet<RiverWay> chosen=new java.util.LinkedHashSet<>();
            java.util.LinkedHashSet<String> chosenNames=new java.util.LinkedHashSet<>();

            // First pass: actual rivers that pass close to an official station, or same-name reaches.
            for(RiverWay r:base){
                if(r==null||r.points==null||r.points.size()<2)continue;
                String rn=v881Norm(r.name); boolean keep=false;
                for(StationDot s:ss){
                    if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                    double km=v881DistanceToRiverKm(s.lat,s.lon,r);
                    if(!Double.isFinite(km)||km>30d)continue;
                    String sn=v881Norm(s.name);
                    boolean nm=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                    if(km<=6d||nm){keep=true;break;}
                }
                if(keep){chosen.add(r);if(!rn.isEmpty())chosenNames.add(rn);}
            }

            // Second pass: guarantee a nearest real river seed for every station represented by this tile.
            for(StationDot s:ss){
                if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                RiverWay best=null;double bestKm=Double.POSITIVE_INFINITY;
                for(RiverWay r:base){
                    if(r==null||r.points==null||r.points.size()<2)continue;
                    double km=v881DistanceToRiverKm(s.lat,s.lon,r);
                    if(Double.isFinite(km)&&km<bestKm){bestKm=km;best=r;}
                }
                if(best!=null&&bestKm<=30d){chosen.add(best);String k=v881Norm(best.name);if(!k.isEmpty())chosenNames.add(k);}
            }

            // Expand selected named rivers to their same-name reaches in this progressive tile.
            if(!chosenNames.isEmpty()) for(RiverWay r:base){
                if(r==null||r.points==null||r.points.size()<2)continue;
                String rn=v881Norm(r.name);if(rn.isEmpty())continue;
                for(String k:chosenNames) if(rn.equals(k)||rn.contains(k)||k.contains(rn)){chosen.add(r);break;}
            }

            final List<RiverWay> stationRivers=new ArrayList<>(chosen);
            List<RiverWay> normal=new ArrayList<>(),alert=new ArrayList<>(),warning=new ArrayList<>(),danger=new ArrayList<>();
            for(RiverWay r:stationRivers){String st=v884Stage(r,ss);if("danger".equals(st))danger.add(r);else if("warning".equals(st))warning.add(r);else if("alert".equals(st))alert.add(r);else normal.add(r);}
            try{
                final String sg=stationRivers.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(stationRivers);
                final String ng=normal.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(normal),ag=alert.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(alert),wg=warning.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(warning),dg=danger.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(danger);
                main.post(()->{
                    if(generation!=v879RiverLoadGeneration)return;
                    try{
                        rivers.clear();rivers.addAll(stationRivers);v883StationRivers.clear();v883StationRivers.addAll(stationRivers);riversGeoJson=sg;v879RiverGeometryKey=key;
                        GeoJsonSource rs=styleReady&&style!=null?style.getSourceAs("fs-rivers"):null;
                        if(rs!=null)rs.setGeoJson(sg);else installGeoLayers();
                        v886EnsureRiverVisibility();
                        v884Layer("normal",ng,"#2d8cff");v884Layer("alert",ag,"#ffc928");v884Layer("warning",wg,"#ff8a1f");v884Layer("danger",dg,"#f22f4b");
                    }catch(Exception ignored){}
                });
            }catch(Exception ignored){}
        });
    } // V0892_DIRECT_STATION_RIVER_RENDER_SOURCE
'''
m=repl(m,'v879ApplyRiverGeometry',apply)

# Make the cyan station-river source unmistakable on satellite imagery.
m=re.sub(r'lineColor\("#00c8ff"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)', 'lineColor("#00c8ff"),lineWidth(11.0f),lineOpacity(0.52f)',m,count=1)
m=re.sub(r'lineColor\("#68efff"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)', 'lineColor("#68efff"),lineWidth(4.2f),lineOpacity(1.0f)',m,count=1)

# version only
g=re.sub(r'versionCode\s+111\b','versionCode 112',g,count=1)
g=g.replace("versionName '0.8.91'","versionName '0.8.92'",1)

if 'V0892_DIRECT_STATION_RIVER_RENDER_SOURCE' not in m: raise SystemExit('v0892 render marker missing')
if 'rs.setGeoJson(sg)' not in m: raise SystemExit('v0892 fs-rivers source assignment missing')
if 'v886EnsureRiverVisibility();' not in m: raise SystemExit('v0892 force layer call missing')
if "versionName '0.8.92'" not in g or 'versionCode 112' not in g: raise SystemExit('v0892 version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.92 PASS: direct official-station river render source + guaranteed visible cyan flow/glow')
