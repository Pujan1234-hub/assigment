from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; w_path=src/'RiverAlertWorker.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); w=w_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

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
    if not s:raise SystemExit('missing method '+name)
    return text[:s[0]]+block+text[s[1]:]

# UI: latest official source row is valid until BIPAD/DHM replaces it; no local 20m hiding.
a=a.replace('यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।','यो BIPAD/DHM को latest official reading हो। Official source update हुनेबित्तिकै app refresh हुन्छ।')
a=a.replace('This is the latest official reading; it is older than 20 minutes so it is not used for LIVE alerts.','This is the latest official BIPAD/DHM reading. The app refreshes when the official source updates.')
a=re.sub(r'private static final long RIVER_FRESH_MS\s*=\s*[^;]+;','private static final long RIVER_FRESH_MS=Long.MAX_VALUE; // V0884_NO_UI_MINUTE_CUTOFF',a,count=1)

# Map station: any real latest water-level observation remains source-current; no-reading stations stay grey.
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
            s.fresh=getBoolean(c,o,"fresh",false)||Double.isFinite(s.level);
            return s;
        } catch(Exception ignored){ return null; }
    } // V0884_LATEST_OFFICIAL_READING_VISIBLE
'''
m=repl(m,'readStation',read)

apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> base=v879Dedup(input);
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        io.execute(()->{
            List<RiverWay> matched=new ArrayList<>(), normal=new ArrayList<>(), alert=new ArrayList<>(), warning=new ArrayList<>(), danger=new ArrayList<>();
            for(RiverWay r:base){String st=v884Stage(r,ss);if(st==null)continue;matched.add(r);if("danger".equals(st))danger.add(r);else if("warning".equals(st))warning.add(r);else if("alert".equals(st))alert.add(r);else normal.add(r);}
            try{
                final String bg=base.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(base), ng=normal.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(normal), ag=alert.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(alert), wg=warning.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(warning), dg=danger.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(danger);
                main.post(()->{if(generation!=v879RiverLoadGeneration)return;try{rivers.clear();rivers.addAll(base);v883StationRivers.clear();v883StationRivers.addAll(matched);riversGeoJson=bg;v879RiverGeometryKey=key;GeoJsonSource rs=styleReady&&style!=null?style.getSourceAs("fs-rivers"):null;if(rs!=null)rs.setGeoJson(bg);else installGeoLayers();v884Layer("normal",ng,"#2d8cff");v884Layer("alert",ag,"#ffc928");v884Layer("warning",wg,"#ff8a1f");v884Layer("danger",dg,"#f22f4b");}catch(Exception ignored){}});
            }catch(Exception ignored){}
        });
    } // V0884_STATUS_COLOUR_STATION_RIVERS_BACKGROUND
'''
m=repl(m,'v879ApplyRiverGeometry',apply)
anchor='    private static int v879TileX(double lon)'
if anchor not in m:raise SystemExit('tile anchor missing')
helper=r'''    private String v884Stage(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2)return null;String rn=v881Norm(r.name),best=null;int rank=-1;
        for(StationDot s:ss){if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;String sn=v881Norm(s.name);boolean ok=!rn.isEmpty()&&!sn.isEmpty()&&(rn.contains(sn)||sn.contains(rn));if(!ok){double d=v881DistanceToRiverKm(s.lat,s.lon,r);ok=Double.isFinite(d)&&d<=2.5d;}if(!ok)continue;String st=normalizeStage(s.stage);int q="danger".equals(st)?3:"warning".equals(st)?2:"alert".equals(st)?1:0;if(q>rank){rank=q;best=st;}}
        return best;
    } // V0884_MATCH_LATEST_STATION_STATUS_TO_RIVER
    private void v884Layer(String n,String geo,String color){
        if(!styleReady||style==null)return;try{String id="fs-v884-"+n;GeoJsonSource s=style.getSourceAs(id);if(s==null){style.addSource(new GeoJsonSource(id,geo));style.addLayer(new LineLayer(id+"-glow",id).withProperties(lineColor(color),lineWidth(8f),lineOpacity(.30f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));style.addLayer(new LineLayer(id+"-core",id).withProperties(lineColor(color),lineWidth(2.8f),lineOpacity(1f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));}else s.setGeoJson(geo);}catch(Exception ignored){}
    } // V0884_RIVER_STATUS_COLOUR_LAYERS

'''
m=m.replace(anchor,helper+anchor,1)
# ensure base rivers are visible; station-bearing rivers get stronger status overlay and particles from v0.8.83.
m=m.replace('lineWidth(3.0f), lineOpacity(0.30f)','lineWidth(4.2f), lineOpacity(0.40f)',1).replace('lineWidth(1.45f), lineOpacity(0.82f)','lineWidth(1.9f), lineOpacity(0.98f)',1)

# Closed-app 2km warning/danger: trust latest official status; remove arbitrary local observation-age rejection.
w,n=re.subn(r'private static final long MAX_AGE_MS\s*=\s*[^;]+;','private static final long MAX_AGE_MS = Long.MAX_VALUE; // V0884_NO_LOCAL_AGE_CUTOFF',w,count=1)
if n==0:
    mark='private static final double RADIUS_KM = 2d;'
    if mark in w:w=w.replace(mark,mark+'\n    private static final long MAX_AGE_MS = Long.MAX_VALUE; // V0884_NO_LOCAL_AGE_CUTOFF',1)
w=re.sub(r'now\s*-\s*measuredAt\s*>\s*MAX_AGE_MS\s*\|\|\s*','',w)
w=w.replace('Only fresh, verified','Latest verified')

# version
g=re.sub(r'versionCode\s+103\b','versionCode 104',g,count=1);g=g.replace("versionName '0.8.83'","versionName '0.8.84'",1)
for x in ['V0884_LATEST_OFFICIAL_READING_VISIBLE','V0884_STATUS_COLOUR_STATION_RIVERS_BACKGROUND','V0884_MATCH_LATEST_STATION_STATUS_TO_RIVER','V0884_RIVER_STATUS_COLOUR_LAYERS']:
    if x not in m:raise SystemExit('missing '+x)
if 'V0884_NO_LOCAL_AGE_CUTOFF' not in w:raise SystemExit('worker cutoff marker missing')
if "versionName '0.8.84'" not in g or 'versionCode 104' not in g:raise SystemExit('version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');w_path.write_text(w,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.84 FIXED PASS: latest BIPAD/DHM source truth + visible flow/glow + status river colours + 2km alert')
