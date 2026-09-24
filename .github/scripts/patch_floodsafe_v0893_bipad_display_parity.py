from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start()); d=0; quote=None; esc=False
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
    s=span(text,name)
    if not s:raise SystemExit('v0893 method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]

# IMPORTANT: display parity and emergency alert freshness are different concerns.
# BIPAD River Watch displays the latest official row/status even when the row is older
# than the notification freshness gate. Therefore map dots and river colours mirror the
# latest official source status. Native alert/push safety remains unchanged elsewhere.
map_colour=r'''    private static String v884MapColour(StationDot s){
        if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)return "GREY / NO OFFICIAL READING";
        String g=normalizeStage(s.stage);
        if("danger".equals(g))return "RED";
        if("warning".equals(g))return "ORANGE";
        if("alert".equals(g))return "YELLOW";
        return "GREEN / NORMAL";
    } // V0893_BIPAD_LATEST_STATUS_DISPLAY_PARITY
'''
m=replace_method(m,'v884MapColour',map_colour)

risk=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null)return null;
        StationDot best=null;double bestScore=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!Double.isFinite(x.level)||x.v881At<=0L||!group.equals(normalizeStage(x.stage)))continue; // V0893_LATEST_OFFICIAL_STATUS_RISK_LINE
            double d=v872GaugeToRiverKm(x,r);if(!Double.isFinite(d))continue;
            boolean named=v890LikelySameRiver(r,x)&&d<=7.5;
            boolean tight=v890TightGeometryJoin(r,x);
            if(!named&&!tight)continue;
            double score=d+(named?0.0:20.0);
            if(score<bestScore){bestScore=score;best=x;}
        }
        return best;
    } // V0893_BIPAD_RIVER_COLOUR_PARITY
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk)

station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                boolean observed=s!=null&&Double.isFinite(s.level)&&s.v881At>0L;
                String g=observed?normalizeStage(s.stage):"stale"; // V0893_BIPAD_STATION_STATUS_PARITY
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon,s.lat,s.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }
'''
m=replace_method(m,'stationGeo',station_geo)

# Leave all existing freshness checks in the activity/background monitor intact.
if 'V0877_CLEAN_FRESH_ONLY_LIVE' not in m and 'V0891_FRESH_ONLY_STATION_COLOUR' not in m:
    # Map file does not own notification freshness; this is only a sanity note.
    pass

# Release identity.
g=re.sub(r'versionCode\s+112\b','versionCode 113',g,count=1)
g=g.replace("versionName '0.8.92'","versionName '0.8.93'",1)

for x in ['V0893_BIPAD_LATEST_STATUS_DISPLAY_PARITY','V0893_LATEST_OFFICIAL_STATUS_RISK_LINE','V0893_BIPAD_RIVER_COLOUR_PARITY','V0893_BIPAD_STATION_STATUS_PARITY','V0892_THIN_BLUE_RIVERS','V0892_CLEAR_TOPO_BASE','V0890_NO_UNCHANGED_STATION_FLICKER']:
    if x not in m:raise SystemExit('v0893 contract missing: '+x)
if 'versionCode 113' not in g or "versionName '0.8.93'" not in g:raise SystemExit('v0893 version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.93 PASS: map/station/river colours mirror latest BIPAD official status; emergency freshness gate remains separate')
