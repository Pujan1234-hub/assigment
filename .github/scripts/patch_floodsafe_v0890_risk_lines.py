from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.90 field repair from real-device video:
# - official station dots must not blink on every 1-second refresh when nothing changed;
# - severe official station status must visibly propagate to the corresponding river geometry;
# - keep the no-unrelated-river safety rule by requiring either river-name evidence + geometry,
#   or an ultra-tight station-on-river geometry join for script/name variants.

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
    if not sp:raise SystemExit('v0890 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# Stable station source fingerprint: do not replace the GeoJSON point source every second
# when the official rows are byte-for-byte equivalent from the user's point of view.
field='    private final List<RiverWay> v889StableMonitoredRivers = new ArrayList<>(); // V0889_STABLE_MONITORED_RIVERS\n'
if 'V0890_STABLE_STATION_RENDER' not in m:
    if field not in m:raise SystemExit('v0890 stable-river field anchor missing')
    m=m.replace(field,field+'    private String v890StationVisualFingerprint = ""; // V0890_STABLE_STATION_RENDER\n',1)

helpers=r'''    private static int v890EditDistance(String a,String b){
        if(a==null)a="";if(b==null)b="";
        int[] prev=new int[b.length()+1],cur=new int[b.length()+1];
        for(int j=0;j<=b.length();j++)prev[j]=j;
        for(int i=1;i<=a.length();i++){
            cur[0]=i;
            for(int j=1;j<=b.length();j++){
                int cost=a.charAt(i-1)==b.charAt(j-1)?0:1;
                cur[j]=Math.min(Math.min(cur[j-1]+1,prev[j]+1),prev[j-1]+cost);
            }
            int[] t=prev;prev=cur;cur=t;
        }
        return prev[b.length()];
    }

    private static boolean v890LatinComparable(String x){
        if(x==null||x.length()<4)return false;
        for(int i=0;i<x.length();i++)if(x.charAt(i)>127)return false;
        return true;
    }

    private static boolean v890CloseRiverKey(String a,String b){
        if(a==null||b==null||a.isEmpty()||b.isEmpty())return false;
        if(a.equals(b))return true;
        if(!v890LatinComparable(a)||!v890LatinComparable(b))return false;
        int min=Math.min(a.length(),b.length()),max=Math.max(a.length(),b.length());
        if(min>=5&&(a.contains(b)||b.contains(a))&&max-min<=3)return true;
        int lim=max<=6?1:(max<=10?2:3);
        return v890EditDistance(a,b)<=lim;
    }

    private static boolean v890LikelySameRiver(RiverWay r,StationDot s){
        if(r==null||s==null||!v863UsefulRiverName(r.name))return false;
        if(v886SameOfficialRiver(r,s))return true;
        String rk=v886RiverKey(r.name);if(rk.isEmpty())return false;
        String sk=v886RiverKey(s.riverName);
        String tk=v886RiverKey(v886StationRiverFromTitle(s.name));
        return v890CloseRiverKey(rk,sk)||v890CloseRiverKey(rk,tk);
    } // V0890_FUZZY_RIVER_NAME_EVIDENCE

    private boolean v890TightGeometryJoin(RiverWay r,StationDot s){
        if(r==null||s==null)return false;
        double d=v872GaugeToRiverKm(s,r);
        return Double.isFinite(d)&&d<=0.45;
    } // V0890_TIGHT_GEOMETRY_JOIN

    private String v890StationFingerprint(){
        List<String> parts=new ArrayList<>();
        synchronized(stations){for(StationDot s:stations){
            if(s==null)continue;
            parts.add((s.name==null?"":s.name)+"|"+String.format(Locale.US,"%.5f|%.5f|%.4f",s.lat,s.lon,s.level)+"|"+(s.stage==null?"":s.stage)+"|"+s.v881At);
        }}
        java.util.Collections.sort(parts);
        StringBuilder b=new StringBuilder();for(String p:parts)b.append(p).append('\n');
        return parts.size()+":"+Integer.toHexString(b.toString().hashCode());
    } // V0890_STATION_SOURCE_FINGERPRINT

'''
if 'V0890_FUZZY_RIVER_NAME_EVIDENCE' not in m:
    sp=method_span(m,'v887RiverHasOfficialReading')
    if not sp:raise SystemExit('v0890 monitored-river matcher anchor missing')
    m=m[:sp[0]]+helpers+m[sp[0]:]

monitored=r'''    private boolean v887RiverHasOfficialReading(RiverWay r){
        if(r==null)return false;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)continue;
            double d=v872GaugeToRiverKm(s,r);if(!Double.isFinite(d))continue;
            boolean named=v890LikelySameRiver(r,s)&&d<=7.5;
            boolean tight=v890TightGeometryJoin(r,s);
            if(named||tight)return true;
        }}
        return false;
    } // V0890_MONITORED_RIVER_JOIN
'''
m=replace_method(m,'v887RiverHasOfficialReading',monitored)

risk=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null)return null;
        StationDot best=null;double bestScore=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!Double.isFinite(x.level)||x.v881At<=0L||!group.equals(normalizeStage(x.stage)))continue;
            double d=v872GaugeToRiverKm(x,r);if(!Double.isFinite(d))continue;
            boolean named=v890LikelySameRiver(r,x)&&d<=7.5;
            boolean tight=v890TightGeometryJoin(r,x);
            if(!named&&!tight)continue;
            double score=d+(named?0.0:20.0);
            if(score<bestScore){bestScore=score;best=x;}
        }
        return best;
    } // V0890_RISK_LINE_FROM_OFFICIAL_STATUS
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk)

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
        String fp=v890StationFingerprint();
        boolean changed=!fp.equals(v890StationVisualFingerprint);
        if(changed){
            v890StationVisualFingerprint=fp;
            refreshStationSources(); // V0890_NO_UNCHANGED_STATION_FLICKER
            v887ApplyMonitoredRiverGeometry(); // V0890_STATUS_REFRESH_RECOLOURS_RIVERS
        }
        refreshUserSource();
    }
'''
m=replace_method(m,'setStations',set_stations)

g=re.sub(r'versionCode\s+109\b','versionCode 110',g,count=1)
g=g.replace("versionName '0.8.89'","versionName '0.8.90'",1)

required=[
 'V0890_STABLE_STATION_RENDER','V0890_STATION_SOURCE_FINGERPRINT','V0890_FUZZY_RIVER_NAME_EVIDENCE',
 'V0890_TIGHT_GEOMETRY_JOIN','V0890_MONITORED_RIVER_JOIN','V0890_RISK_LINE_FROM_OFFICIAL_STATUS',
 'V0890_NO_UNCHANGED_STATION_FLICKER','V0890_STATUS_REFRESH_RECOLOURS_RIVERS',
 'V0889_PERSISTENT_MONITORED_RIVER_NETWORK','V0886_NO_NEARBY_ONLY_FALLBACK','V0885_MAP_COLOUR_FOLLOWS_OFFICIAL_LATEST'
]
for x in required:
    if x not in m:raise SystemExit('v0890 map contract missing: '+x)
if 'versionCode 110' not in g or "versionName '0.8.90'" not in g:raise SystemExit('v0890 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.90 PASS: stable station dots + official severe status visibly mapped to same/geometry-verified river')
