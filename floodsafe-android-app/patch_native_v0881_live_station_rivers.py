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
    if not sp:raise SystemExit('v0881 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# Use the resilient official BIPAD+DHM loader rather than a single mirror response.
refresh=r'''    private void refreshRivers(){
        if(feedFresh!=null)feedFresh.setText(t("BIPAD/DHM live station refresh हुँदैछ…","Refreshing BIPAD/DHM live stations…"));
        io.execute(()->{
            long now=System.currentTimeMillis();
            try{
                List<RiverStation> out=loadTrustedRiverStationsV862(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
                synchronized(stations){stations.clear();stations.addAll(out);}
                runOnUiThread(this::refreshRiverUi);
            }catch(Exception e){
                runOnUiThread(()->{
                    if(feedFresh!=null)feedFresh.setText(t("Official station refresh असफल • पुरानो/fake live देखाइएको छैन","Official station refresh failed • no fake live data shown"));
                    refreshRiverUi();
                });
            }
        });
    } // V0881_DIRECT_TRUSTED_BIPAD_DHM_STATIONS
'''
a=replace_method(a,'refreshRivers',refresh)

if 'V0879_FULL_RIVER_TILE_RUNTIME' not in m:
    raise SystemExit('v0881 requires v0.8.79 progressive river runtime')

# Only draw/animate river geometry that corresponds to a currently fresh official station.
apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> base=v879Dedup(input);
        main.post(()->{
            if(generation!=v879RiverLoadGeneration)return;
            try{
                List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
                List<RiverWay> next=v881OnlyLiveStationRivers(base,ss);
                rivers.clear();rivers.addAll(next);
                riversGeoJson=next.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(next);
                v879RiverGeometryKey=key;
                if(styleReady&&style!=null){
                    GeoJsonSource s=style.getSourceAs("fs-rivers");
                    if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();
                }else installGeoLayers();
            }catch(Exception ignored){}
        });
    } // V0881_ONLY_LIVE_STATION_RIVERS
'''
m=replace_method(m,'v879ApplyRiverGeometry',apply)

# A station refresh must immediately re-filter the currently visible river tile.
setstations=r'''    void setStations(List<?> source, double lat, double lon) {
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
            stations.clear();
            stations.addAll(next);
        }
        refreshStationSources();
        refreshUserSource();
        v879RiverGeometryKey="";
        v879RefreshRiverGeometryForCamera();
    } // V0881_STATION_REFRESH_RELOADS_RIVERS
'''
m=replace_method(m,'setStations',setstations)

anchor='    private static int v879TileX(double lon)'
if anchor not in m:raise SystemExit('v0881 tile helper anchor missing')
helpers=r'''    private List<RiverWay> v881OnlyLiveStationRivers(List<RiverWay> input,List<StationDot> ss){
        List<RiverWay> out=new ArrayList<>();
        if(input==null||input.isEmpty()||ss==null||ss.isEmpty())return out;
        for(RiverWay r:input){if(v881RiverHasLiveStation(r,ss))out.add(r);}
        return out;
    } // V0881_FILTER_NO_STATION_RIVERS

    private boolean v881RiverHasLiveStation(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return false;
        String rn=v881Norm(r.name);
        for(StationDot s:ss){
            if(s==null||!s.fresh||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            if(!rn.isEmpty()&&!sn.isEmpty()&&(rn.contains(sn)||sn.contains(rn)))return true;
            double km=v881DistanceToRiverKm(s.lat,s.lon,r);
            if(Double.isFinite(km)&&km<=2.5d)return true;
        }
        return false;
    } // V0881_LIVE_STATION_MATCH

    private static String v881Norm(String s){
        if(s==null)return "";
        return s.toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]","")
                .replace("river","").replace("khola","").replace("nadi","")
                .replace("नदी","").replace("खोला","");
    }

    private static double v881DistanceToRiverKm(double lat,double lon,RiverWay r){
        double best=Double.POSITIVE_INFINITY,cos=Math.cos(Math.toRadians(lat));
        for(int i=1;i<r.points.size();i++){
            double[] a=r.points.get(i-1),b=r.points.get(i);
            double ax=(a[0]-lon)*111.320*cos,ay=(a[1]-lat)*110.574;
            double bx=(b[0]-lon)*111.320*cos,by=(b[1]-lat)*110.574;
            double dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy;
            double t=den>0?-(ax*dx+ay*dy)/den:0d;t=Math.max(0d,Math.min(1d,t));
            double px=ax+t*dx,py=ay+t*dy,d=Math.sqrt(px*px+py*py);if(d<best)best=d;
        }
        return best;
    }

'''
m=m.replace(anchor,helpers+anchor,1)

# Make station dots clearly visible and easier to tap.
m=m.replace('ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);','ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 5.3f, 0.96f);')
m=m.replace('ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f);','ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 6.0f, 1f);')
m=m.replace('ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 5.0f, 1f);','ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 6.7f, 1f);')
m=m.replace('ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 5.8f, 1f);','ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 7.3f, 1f);')
m=m.replace('ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f);','ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 8.0f, 1f);')

g=re.sub(r'versionCode\s+100\b','versionCode 101',g,count=1)
g=g.replace("versionName '0.8.80'","versionName '0.8.81'",1)
if 'versionCode 101' not in g or "versionName '0.8.81'" not in g:
    raise SystemExit('v0881 version bump failed')

need=['V0881_DIRECT_TRUSTED_BIPAD_DHM_STATIONS','V0881_ONLY_LIVE_STATION_RIVERS','V0881_STATION_REFRESH_RELOADS_RIVERS','V0881_FILTER_NO_STATION_RIVERS','V0881_LIVE_STATION_MATCH']
for x in need:
    if x not in a and x not in m:raise SystemExit('missing '+x)

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.81 live-station-only river network + station detail visibility patch applied')
