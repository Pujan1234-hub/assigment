from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.91 safety/truth repair:
# - old official WARNING/DANGER rows are history, not a current flood.
# - map station and river risk colours are severe ONLY while the reading is fresh.
# - stale observed gauges are placed in the stale/unknown source rather than warning/danger.
# - retain v0.8.90 name/geometry join and anti-flicker behavior.

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
    if not sp:raise SystemExit('v0891 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

map_colour=r'''    private static String v884MapColour(StationDot s){
        if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)return "GREY / NO OFFICIAL READING";
        if(!s.fresh)return "GREY / STALE"; // V0891_STALE_STATION_GREY
        String g=normalizeStage(s.stage);
        if("danger".equals(g))return "RED";
        if("warning".equals(g))return "ORANGE";
        if("alert".equals(g))return "YELLOW";
        return "GREEN / NORMAL";
    } // V0891_FRESH_ONLY_STATION_COLOUR
'''
m=replace_method(m,'v884MapColour',map_colour)

risk=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null)return null;
        StationDot best=null;double bestScore=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!Double.isFinite(x.level)||x.v881At<=0L||!x.fresh||!group.equals(normalizeStage(x.stage)))continue; // V0891_FRESH_ONLY_RISK_LINE
            double d=v872GaugeToRiverKm(x,r);if(!Double.isFinite(d))continue;
            boolean named=v890LikelySameRiver(r,x)&&d<=7.5;
            boolean tight=v890TightGeometryJoin(r,x);
            if(!named&&!tight)continue;
            double score=d+(named?0.0:20.0);
            if(score<bestScore){bestScore=score;best=x;}
        }
        return best;
    } // V0891_CURRENT_FLOOD_RIVER_ONLY
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk)

# Keep the existing two-argument source API used by refreshStationSources, but
# classify a severe status as severe only while its observation is fresh.
station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                boolean observed=s!=null&&Double.isFinite(s.level)&&s.v881At>0L;
                String g;
                if(!observed||!s.fresh)g="stale"; // V0891_STATION_GEO_USES_FRESH_TRUTH
                else g=normalizeStage(s.stage);
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon,s.lat,s.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }
'''
m=replace_method(m,'stationGeo',station_geo)

g=re.sub(r'versionCode\s+110\b','versionCode 111',g,count=1)
g=g.replace("versionName '0.8.90'","versionName '0.8.91'",1)

required=[
 'V0891_STALE_STATION_GREY','V0891_FRESH_ONLY_STATION_COLOUR','V0891_FRESH_ONLY_RISK_LINE',
 'V0891_CURRENT_FLOOD_RIVER_ONLY','V0891_STATION_GEO_USES_FRESH_TRUTH',
 'V0890_NO_UNCHANGED_STATION_FLICKER','V0890_FUZZY_RIVER_NAME_EVIDENCE','V0890_TIGHT_GEOMETRY_JOIN',
 'V0889_PERSISTENT_MONITORED_RIVER_NETWORK','V0886_NO_NEARBY_ONLY_FALLBACK'
]
for x in required:
    if x not in m:raise SystemExit('v0891 map contract missing: '+x)
if 'versionCode 111' not in g or "versionName '0.8.91'" not in g:raise SystemExit('v0891 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.91 PASS: fresh-only river risk colours + stale gauges removed from severe layers + stable non-flickering stations')
