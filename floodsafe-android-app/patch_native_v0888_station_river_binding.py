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

# Station names from BIPAD are commonly "River Name at Gauge Place". Strip location suffix
# before comparing against bundled OSM river names so same-river matching is deterministic.
norm=r'''    private static String v881Norm(String s){
        if(s==null)return "";
        String x=s.toLowerCase(Locale.ROOT).trim();
        x=x.replaceAll("\\s+(at|near|@)\\s+.*$","");
        x=x.replaceAll("\\s+(station|gauge|hydrological station)\\b.*$","");
        x=x.replace(" river"," ").replace("river "," ")
             .replace(" khola"," ").replace("khola "," ")
             .replace(" nadi"," ").replace("nadi "," ")
             .replace("नदी","").replace("खोला","");
        return x.replaceAll("[^\\p{L}\\p{N}]","");
    } // V0888_CANONICAL_BIPAD_RIVER_NAME
'''
m=repl(m,'v881Norm',norm)

# Bind river geometry to station by canonical name first; use a wider geometry tolerance only
# as a fallback because bundled OSM geometry can be offset/generalised from the gauge coordinate.
stage=r'''    private String v884Stage(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return null;
        String rn=v881Norm(r.name),best=null;int rank=-1;
        for(StationDot s:ss){
            if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            boolean nameMatch=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
            boolean geometryMatch=false;
            if(!nameMatch){
                double d=v881DistanceToRiverKm(s.lat,s.lon,r);
                geometryMatch=Double.isFinite(d)&&d<=4.5d;
            }
            if(!nameMatch&&!geometryMatch)continue;
            String st=normalizeStage(s.stage);
            int q="danger".equals(st)?3:"warning".equals(st)?2:"alert".equals(st)?1:0;
            if(q>rank){rank=q;best=st;}
        }
        return best;
    } // V0888_STATION_TO_RIVER_STATUS_BINDING
'''
m=repl(m,'v884Stage',stage)

# Same matching rule for the strong station-river glow/flow overlay. Do not require freshness just
# to bind/display the river; safety alert freshness remains enforced separately by worker logic.
has=r'''    private boolean v881RiverHasLiveStation(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return false;
        String rn=v881Norm(r.name);
        for(StationDot s:ss){
            if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            if(!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn)))return true;
            double km=v881DistanceToRiverKm(s.lat,s.lon,r);
            if(Double.isFinite(km)&&km<=4.5d)return true;
        }
        return false;
    } // V0888_STATION_RIVER_VISIBLE_EVEN_WHEN_READING_OLD
'''
m=repl(m,'v881RiverHasLiveStation',has)

# Make station interaction forgiving on phones: station tap wins before river tap and uses >=1.2km
# geographic hit radius (visual dots are still small; this is an invisible touch target).
click=r'''    private boolean onMapClick(LatLng p) {
        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        double stationThreshold = Math.max(1.2, 42.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        if (nearest != null && km(p.getLatitude(), p.getLongitude(), nearest.lat, nearest.lon) <= stationThreshold) {
            if (stationTapListener != null) stationTapListener.onStationTap(nearest.original);
            return true;
        }
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.65, 24.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) {
            showRiver(rw, p.getLatitude(), p.getLongitude());
            return true;
        }
        return false;
    } // V0888_LARGE_STATION_TAP_TARGET
'''
m=repl(m,'onMapClick',click)

# Make severe river overlays visually unmistakable.
m=m.replace('lineWidth(8f),lineOpacity(.30f)', 'lineWidth(10f),lineOpacity(.42f)')
m=m.replace('lineWidth(2.8f),lineOpacity(1f)', 'lineWidth(3.8f),lineOpacity(1f)')

# bump after v0.8.87
g=re.sub(r'versionCode\s+107\b','versionCode 108',g,count=1)
g=g.replace("versionName '0.8.87'","versionName '0.8.88'",1)

for token in ['V0888_CANONICAL_BIPAD_RIVER_NAME','V0888_STATION_TO_RIVER_STATUS_BINDING','V0888_STATION_RIVER_VISIBLE_EVEN_WHEN_READING_OLD','V0888_LARGE_STATION_TAP_TARGET']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.88'" not in g or 'versionCode 108' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.88 PASS: canonical station-river binding + stronger flood colours + larger station tap target')
