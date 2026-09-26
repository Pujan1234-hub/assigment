from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
w_path=src/'RiverAlertWorker.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
w=w_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

WINDOW='45L*60L*1000L'

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

# UI freshness: do not hide the station/river, but only a recent official observation is LIVE/current.
a=re.sub(r'private static final long RIVER_FRESH_MS\s*=\s*[^;]+;','private static final long RIVER_FRESH_MS='+WINDOW+'; // V0889_45M_LIVE_WINDOW',a,count=1)
if 'V0889_45M_LIVE_WINDOW' not in a:
    raise SystemExit('RIVER_FRESH_MS anchor missing')

# Map station classification from the actual source timestamp on RiverStation, not merely level presence.
read=r'''    private StationDot readStation(Object o) {
        if (o == null) return null;
        try {
            Class<?> c = o.getClass();
            double la = getDouble(c, o, "lat"), lo = getDouble(c, o, "lon");
            if (!Double.isFinite(la) || !Double.isFinite(lo)) return null;
            StationDot s = new StationDot();
            s.original=o; s.lat=la; s.lon=lo;
            s.name=getString(c,o,"name","Official river station");
            s.stage=getString(c,o,"stage","normal").toLowerCase(Locale.ROOT);
            s.level=getDouble(c,o,"level");
            s.at=v889LongAny(c,o,"at","measuredAt","measurementAt","timestamp","time");
            long now=System.currentTimeMillis();
            long age=s.at>0L?Math.abs(now-s.at):Long.MAX_VALUE;
            s.fresh=Double.isFinite(s.level)&&s.at>0L&&age<=45L*60L*1000L;
            return s;
        } catch(Exception ignored){ return null; }
    } // V0889_TIMESTAMP_DRIVEN_STATION_FRESHNESS
'''
m=repl(m,'readStation',read)

# helper before getDouble
anchor='    private static double getDouble(Class<?> c, Object o, String name) throws Exception {'
if anchor not in m: raise SystemExit('getDouble anchor missing')
helper=r'''    private static long v889LongAny(Class<?> c,Object o,String... names){
        for(String n:names){
            try{Field f=c.getDeclaredField(n);f.setAccessible(true);Object v=f.get(o);if(v instanceof Number)return ((Number)v).longValue();}
            catch(Exception ignored){}
        }
        return 0L;
    } // V0889_READ_SOURCE_TIMESTAMP

'''
m=m.replace(anchor,helper+anchor,1)

# Old historical readings remain visible as stale/grey and never as green/normal.
station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                String g = s.fresh ? normalizeStage(s.stage) : "stale";
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon, s.lat, s.name));
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    } // V0889_STALE_NEVER_GREEN
'''
m=repl(m,'stationGeo',station_geo)

# Status colours are safety-critical: only current/recent official observations may colour a river.
stage=r'''    private String v884Stage(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return null;
        String rn=v881Norm(r.name),best=null;int rank=-1;
        for(StationDot s:ss){
            if(s==null||!s.fresh||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            boolean nameMatch=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
            boolean geometryMatch=false;
            if(!nameMatch){double d=v881DistanceToRiverKm(s.lat,s.lon,r);geometryMatch=Double.isFinite(d)&&d<=4.5d;}
            if(!nameMatch&&!geometryMatch)continue;
            String st=normalizeStage(s.stage);
            int q="danger".equals(st)?3:"warning".equals(st)?2:"alert".equals(st)?1:0;
            if(q>rank){rank=q;best=st;}
        }
        return best;
    } // V0889_RECENT_ONLY_RIVER_STATUS_COLOUR
'''
m=repl(m,'v884Stage',stage)

# Station-bearing river geometry should still be shown even when the latest observation is stale.
has=r'''    private boolean v881RiverHasLiveStation(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return false;
        String rn=v881Norm(r.name);
        for(StationDot s:ss){
            if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            if(!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn)))return true;
            double km=v881DistanceToRiverKm(s.lat,s.lon,r);
            if(Double.isFinite(km)&&km<=6.0d)return true;
        }
        return false;
    } // V0889_STATION_RIVER_VISIBLE_INDEPENDENT_OF_FRESHNESS
'''
m=repl(m,'v881RiverHasLiveStation',has)

# Strengthen station-river overlay so it cannot disappear behind imagery.
m=m.replace('lineWidth(7.0f),lineOpacity(0.34f)','lineWidth(9.0f),lineOpacity(0.44f)')
m=m.replace('lineWidth(2.35f),lineOpacity(1.0f)','lineWidth(3.2f),lineOpacity(1.0f)')

# Extend StationDot with source timestamp.
m=m.replace('Object original; String name, stage; double lat, lon, level; boolean fresh;','Object original; String name, stage; double lat, lon, level; long at; boolean fresh;',1)
if 'long at; boolean fresh;' not in m: raise SystemExit('StationDot timestamp field patch failed')

# Closed-app alert safety: stale/historical readings must never trigger 2 km warnings.
w=re.sub(r'private static final long MAX_AGE_MS\s*=\s*[^;]+;','private static final long MAX_AGE_MS = 45L * 60L * 1000L; // V0889_ALERT_RECENCY_GUARD',w,count=1)
if 'V0889_ALERT_RECENCY_GUARD' not in w:
    raise SystemExit('MAX_AGE_MS anchor missing')
# Restore age rejection if earlier patches removed it.
if 'now - measuredAt > MAX_AGE_MS' not in w:
    needle='if (measuredAt <= 0L) return null;'
    if needle in w:
        w=w.replace(needle,needle+'\n        if (now - measuredAt > MAX_AGE_MS || measuredAt - now > 5L * 60L * 1000L) return null; // V0889_REJECT_STALE_ALERT',1)
    else:
        # compact variants
        pat=re.compile(r'(long\s+measuredAt\s*=\s*[^;]+;)')
        w,n=pat.subn(r'\1\n        if (measuredAt <= 0L || now - measuredAt > MAX_AGE_MS || measuredAt - now > 5L * 60L * 1000L) return null; // V0889_REJECT_STALE_ALERT',w,count=1)
        if n==0: raise SystemExit('measuredAt guard anchor missing')

# Version bump after v0.8.88.
g=re.sub(r'versionCode\s+108\b','versionCode 109',g,count=1)
g=g.replace("versionName '0.8.88'","versionName '0.8.89'",1)

for token in ['V0889_45M_LIVE_WINDOW','V0889_TIMESTAMP_DRIVEN_STATION_FRESHNESS','V0889_STALE_NEVER_GREEN','V0889_RECENT_ONLY_RIVER_STATUS_COLOUR','V0889_STATION_RIVER_VISIBLE_INDEPENDENT_OF_FRESHNESS','V0889_ALERT_RECENCY_GUARD']:
    if token not in a+m+w: raise SystemExit('missing '+token)
if "versionName '0.8.89'" not in g or 'versionCode 109' not in g: raise SystemExit('version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
w_path.write_text(w,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.89 PASS: newest-reading truth + stale-history isolation + station-river visibility + fresh-only safety colours/alerts')
