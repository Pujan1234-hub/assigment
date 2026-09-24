from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.86: river taps must resolve the official station for THAT river, not just draw geometry.
# Real-device regression: OSM "kankai mai" sat ~0.9 km from official "Kankai River at Mainachuli"
# but the strict raw-name equality rejected it. This patch keeps the no-nearby-river safety rule:
# matching requires official river-name/title evidence AND geometry proximity. There is still no
# nearest-station-only fallback.

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
    if not sp:raise SystemExit('v0886 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# Shared resolver used by both river popup detail and river risk colouring.
if 'V0886_OFFICIAL_TITLE_RIVER_JOIN' not in m:
    sp=method_span(m,'v884SameRiverGaugeForDetail')
    if not sp:raise SystemExit('v0886 detail matcher missing')
    helper=r'''    private static String v886StationRiverFromTitle(String title){
        if(title==null)return "";
        String x=title.trim();String low=x.toLowerCase(Locale.ROOT);
        String[] cuts={" at "," @ "," near "," gauge at "," station at "};
        int best=-1;
        for(String cut:cuts){int p=low.indexOf(cut);if(p>0&&(best<0||p<best))best=p;}
        if(best>0)x=x.substring(0,best).trim();
        x=x.replaceAll("(?iu)\\s+(gauge|station)$","").trim();
        return x;
    }

    private static String v886RiverKey(String value){
        String x=v884CanonicalRiverName(value);if(x.isEmpty())return "";
        // DHM/BIPAD and OSM use these names for the same eastern Nepal river.
        if("kankaimai".equals(x)||"kankai".equals(x)||"maikhola".equals(x)||"mai".equals(x))return "kankai";
        return x;
    }

    private static boolean v886SameOfficialRiver(RiverWay r,StationDot s){
        if(r==null||s==null||!v863UsefulRiverName(r.name))return false;
        String rk=v886RiverKey(r.name);if(rk.isEmpty())return false;
        String sk=v886RiverKey(s.riverName);
        if(!sk.isEmpty()&&rk.equals(sk))return true;
        // Some BIPAD rows expose the river most reliably in the station title
        // (for example "Kankai River at Mainachuli"). This is name evidence, not a nearby fallback.
        String tk=v886RiverKey(v886StationRiverFromTitle(s.name));
        return !tk.isEmpty()&&rk.equals(tk);
    } // V0886_OFFICIAL_TITLE_RIVER_JOIN V0886_NO_NEARBY_ONLY_FALLBACK

'''
    m=m[:sp[0]]+helper+m[sp[0]:]

detail=r'''    private StationDot v884SameRiverGaugeForDetail(RiverWay r,double la,double lo){
        if(r==null||!v863UsefulRiverName(r.name))return null;
        StationDot bestObserved=null,bestAny=null;double obsScore=Double.POSITIVE_INFINITY,anyScore=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!v886SameOfficialRiver(r,s))continue; // V0886_DETAIL_USES_OFFICIAL_RIVER_JOIN
            double routeD=v872GaugeToRiverKm(s,r);if(!Double.isFinite(routeD)||routeD>7.5)continue;
            double tapD=km(la,lo,s.lat,s.lon);if(!Double.isFinite(tapD)||tapD>70.0)continue;
            double score=routeD*10.0+tapD;
            if(score<anyScore){anyScore=score;bestAny=s;}
            if((Double.isFinite(s.level)||s.v881At>0L)&&score<obsScore){obsScore=score;bestObserved=s;}
        }}
        return bestObserved!=null?bestObserved:bestAny;
    } // V0886_RIVER_TAP_RETURNS_SAME_RIVER_OFFICIAL_STATION
'''
m=replace_method(m,'v884SameRiverGaugeForDetail',detail)

risk=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null||!v863UsefulRiverName(r.name))return null;
        StationDot best=null;double bestD=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!Double.isFinite(x.level)||x.v881At<=0L||!group.equals(normalizeStage(x.stage)))continue;
            if(!v886SameOfficialRiver(r,x))continue; // V0886_RISK_USES_SAME_OFFICIAL_JOIN
            double d=v872GaugeToRiverKm(x,r);if(Double.isFinite(d)&&d<bestD){bestD=d;best=x;}
        }
        return bestD<=7.5?best:null;
    } // V0872_MATCHED_RIVER_GEOMETRY_ONLY V0886_OFFICIAL_LATEST_RIVER_COLOUR_JOIN
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk)

# Add an explicit source-join line in river detail so field testing can prove which official gauge
# supplied the clicked river values. Existing showRiver already prints level, thresholds, status,
# observation time and source from the resolved StationDot.
sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0886 showRiver missing')
show=m[sp[0]:sp[1]]
if 'V0886_CLICKED_RIVER_OFFICIAL_GAUGE' not in show:
    anchor='b.append("\\n").append(englishUi?"Station: ":"Station: ").append(gauge.name);'
    if anchor not in show:raise SystemExit('v0886 showRiver station anchor missing')
    show=show.replace(anchor,anchor+' // V0886_CLICKED_RIVER_OFFICIAL_GAUGE',1)
    m=m[:sp[0]]+show+m[sp[1]:]

# Release identity.
g=re.sub(r'versionCode\s+105\b','versionCode 106',g,count=1)
g=g.replace("versionName '0.8.85'","versionName '0.8.86'",1)

required=[
    'V0886_OFFICIAL_TITLE_RIVER_JOIN','V0886_NO_NEARBY_ONLY_FALLBACK',
    'V0886_DETAIL_USES_OFFICIAL_RIVER_JOIN','V0886_RIVER_TAP_RETURNS_SAME_RIVER_OFFICIAL_STATION',
    'V0886_RISK_USES_SAME_OFFICIAL_JOIN','V0886_OFFICIAL_LATEST_RIVER_COLOUR_JOIN',
    'V0886_CLICKED_RIVER_OFFICIAL_GAUGE','V0885_ALWAYS_VISIBLE_NATIONAL_RIVER_NETWORK',
    'V0885_MAP_COLOUR_FOLLOWS_OFFICIAL_LATEST','V0884_REAL_RIVER_DETAIL_TIME_SOURCE_THRESHOLDS'
]
for x in required:
    if x not in m:raise SystemExit('v0886 map contract missing: '+x)
if 'versionCode 106' not in g or "versionName '0.8.86'" not in g:
    raise SystemExit('v0886 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.86 PASS: clicked river joins its official BIPAD/DHM station by river/title evidence + geometry; no nearby-only borrowing')
