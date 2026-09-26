from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

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

refresh=r'''    private void v893RefreshDedicatedStationRivers(){
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        final List<RiverWay> all; synchronized(v893AllRivers){all=new ArrayList<>(v893AllRivers);}
        if(ss.isEmpty()||all.isEmpty())return;
        StringBuilder fb=new StringBuilder();
        for(StationDot s:ss)if(s!=null&&Double.isFinite(s.lat)&&Double.isFinite(s.lon))fb.append(v881Norm(s.name)).append('@').append(Math.round(s.lat*10000d)).append(',').append(Math.round(s.lon*10000d)).append(';');
        final String fingerprint=fb.toString();
        if(fingerprint.equals(v894StationGeometryFingerprint)&&!v893StationRivers.isEmpty()){
            v894UpdateDedicatedStatus(ss);return;
        }
        v894PendingFingerprint=fingerprint;
        if(v894RiverMatchRunning)return;
        v894RiverMatchRunning=true;
        io.execute(()->{
            try{
                java.util.LinkedHashSet<RiverWay> chosen=new java.util.LinkedHashSet<>();
                java.util.LinkedHashMap<String,List<StationDot>> stationsByRiver=new java.util.LinkedHashMap<>();
                for(StationDot s:ss){
                    if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                    String sn=v881Norm(s.name);RiverWay bestName=null,bestNear=null;double dn=Double.POSITIVE_INFINITY,da=Double.POSITIVE_INFINITY;
                    for(RiverWay r:all){
                        if(r==null||r.points==null||r.points.size()<2)continue;
                        boolean plausible=false;int stride=Math.max(1,r.points.size()/12);
                        for(int pi=0;pi<r.points.size();pi+=stride){double[] q=r.points.get(pi);if(Math.abs(q[1]-s.lat)<0.22&&Math.abs(q[0]-s.lon)<0.26){plausible=true;break;}}
                        if(!plausible)continue;
                        double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(!Double.isFinite(d)||d>22d)continue;
                        String rn=v881Norm(r.name);boolean nm=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                        if(nm&&d<dn){dn=d;bestName=r;}if(d<da){da=d;bestNear=r;}
                    }
                    RiverWay seed=bestName!=null?bestName:bestNear;
                    if(seed==null)continue;
                    chosen.add(seed);
                    String key=v881Norm(seed.name);
                    if(!key.isEmpty())stationsByRiver.computeIfAbsent(key,k->new ArrayList<>()).add(s);
                }

                // Expand ONLY around stations bound to that same river name. Do not paint all same-name
                // geometry across Nepal. This keeps the map to the river corridors actually monitored by BIPAD.
                if(!stationsByRiver.isEmpty()){
                    for(RiverWay r:all){
                        if(r==null||r.points==null||r.points.size()<2)continue;
                        String rn=v881Norm(r.name);List<StationDot> bound=stationsByRiver.get(rn);if(bound==null||bound.isEmpty())continue;
                        boolean nearMonitoredStation=false;
                        for(StationDot s:bound){double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(Double.isFinite(d)&&d<=18d){nearMonitoredStation=true;break;}}
                        if(nearMonitoredStation)chosen.add(r);
                    }
                }

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
    } // V0895_STATION_RIVERS_ONLY_18KM_CORRIDOR
'''

m=replace_method(m,'v893RefreshDedicatedStationRivers',refresh)

g=re.sub(r'versionCode\s+114\b','versionCode 115',g,count=1)
g=g.replace("versionName '0.8.94'","versionName '0.8.95'",1)

for token in ['V0895_STATION_RIVERS_ONLY_18KM_CORRIDOR','stationsByRiver','d<=18d']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.95'" not in g or 'versionCode 115' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.95 PASS: only monitored station river corridors, no unrelated same-name river network')
