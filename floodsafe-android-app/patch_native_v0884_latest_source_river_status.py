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
    if not sp: raise SystemExit('v0884 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# 1) Latest official source observation stays visible regardless of an arbitrary local minute cutoff.
a=a.replace('यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।',
            'यो BIPAD/DHM को latest official reading हो। Source update हुनेबित्तिकै app refresh हुन्छ।')
a=a.replace('This is the latest official reading; it is older than 20 minutes so it is not used for LIVE alerts.',
            'This is the latest official BIPAD/DHM reading. The app refreshes when the official source updates.')
a=a.replace('RIVER_FRESH_MS=10L*60L*1000L','RIVER_FRESH_MS=3650L*24L*60L*60L*1000L')

# 2) A station with a real latest water-level observation is treated as current source truth on the map.
read_station=r'''    private StationDot readStation(Object o) {
        if (o == null) return null;
        try {
            Class<?> c = o.getClass();
            double la = getDouble(c, o, "lat"), lo = getDouble(c, o, "lon");
            if (!Double.isFinite(la) || !Double.isFinite(lo)) return null;
            StationDot s = new StationDot();
            s.original = o; s.lat = la; s.lon = lo;
            s.name = getString(c, o, "name", "Official river station");
            s.stage = getString(c, o, "stage", "normal").toLowerCase(Locale.ROOT);
            s.level = getDouble(c, o, "level");
            s.fresh = getBoolean(c, o, "fresh", false) || Double.isFinite(s.level);
            return s;
        } catch (Exception ignored) { return null; }
    } // V0884_LATEST_OFFICIAL_READING_VISIBLE
'''
m=replace_method(m,'readStation',read_station)

# 3) Classify station-bearing river geometry by the matching station's latest official status.
apply=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> base=v879Dedup(input);
        final List<StationDot> ss;
        synchronized(stations){ss=new ArrayList<>(stations);}
        io.execute(()->{
            final List<RiverWay> matched=new ArrayList<>();
            final List<RiverWay> normal=new ArrayList<>(), alert=new ArrayList<>(), warning=new ArrayList<>(), danger=new ArrayList<>();
            for(RiverWay r:base){
                String stage=v884RiverStage(r,ss);
                if(stage==null)continue;
                matched.add(r);
                if("danger".equals(stage))danger.add(r);
                else if("warning".equals(stage))warning.add(r);
                else if("alert".equals(stage))alert.add(r);
                else normal.add(r);
            }
            try{
                final String baseGeo=base.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(base);
                final String nGeo=normal.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(normal);
                final String aGeo=alert.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(alert);
                final String wGeo=warning.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(warning);
                final String dGeo=danger.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(danger);
                main.post(()->{
                    if(generation!=v879RiverLoadGeneration)return;
                    try{
                        rivers.clear();rivers.addAll(base);
                        v883StationRivers.clear();v883StationRivers.addAll(matched);
                        riversGeoJson=baseGeo;v879RiverGeometryKey=key;
                        if(styleReady&&style!=null){
                            GeoJsonSource s=style.getSourceAs("fs-rivers");
                            if(s!=null)s.setGeoJson(baseGeo);else installGeoLayers();
                            v884ApplyStageRiver("normal",nGeo,"#2d8cff");
                            v884ApplyStageRiver("alert",aGeo,"#ffc928");
                            v884ApplyStageRiver("warning",wGeo,"#ff8a1f");
                            v884ApplyStageRiver("danger",dGeo,"#f22f4b");
                        }else installGeoLayers();
                    }catch(Exception ignored){}
                });
            }catch(Exception ignored){}
        });
    } // V0884_STATUS_COLOUR_STATION_RIVERS_BACKGROUND
'''
m=replace_method(m,'v879ApplyRiverGeometry',apply)

anchor='    private static int v879TileX(double lon)'
if anchor not in m: raise SystemExit('v0884 tile anchor missing')
helpers=r'''    private String v884RiverStage(RiverWay r,List<StationDot> ss){
        if(r==null||r.points==null||r.points.size()<2||ss==null)return null;
        String rn=v881Norm(r.name); String best=null; int rank=-1;
        for(StationDot s:ss){
            if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
            String sn=v881Norm(s.name);
            boolean match=!rn.isEmpty()&&!sn.isEmpty()&&(rn.contains(sn)||sn.contains(rn));
            if(!match){double d=v881DistanceToRiverKm(s.lat,s.lon,r);match=Double.isFinite(d)&&d<=2.5d;}
            if(!match)continue;
            String st=normalizeStage(s.stage); int q="danger".equals(st)?3:"warning".equals(st)?2:"alert".equals(st)?1:0;
            if(q>rank){rank=q;best=st;}
        }
        return best;
    } // V0884_MATCH_LATEST_STATION_STATUS_TO_RIVER

    private void v884ApplyStageRiver(String stageName,String geo,String color){
        if(!styleReady||style==null)return;
        try{
            String sid="fs-river-status-"+stageName, glow=sid+"-glow", core=sid+"-core";
            GeoJsonSource src=style.getSourceAs(sid);
            if(src==null){
                style.addSource(new GeoJsonSource(sid,geo));
                style.addLayer(new LineLayer(glow,sid).withProperties(lineColor(color),lineWidth(8.0f),lineOpacity(0.28f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer(core,sid).withProperties(lineColor(color),lineWidth(2.8f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            }else src.setGeoJson(geo);
        }catch(Exception ignored){}
    } // V0884_RIVER_STATUS_COLOUR_LAYERS

'''
m=m.replace(anchor,helpers+anchor,1)

# Make the actual river base unmistakably visible even before station matching finishes.
m=m.replace('lineWidth(3.0f), lineOpacity(0.30f)','lineWidth(4.2f), lineOpacity(0.38f)',1)
m=m.replace('lineWidth(1.45f), lineOpacity(0.82f)','lineWidth(1.9f), lineOpacity(0.96f)',1)

# 4) Closed-app 2 km alert follows latest official warning/danger instead of rejecting it by local age.
w=w.replace('private static final long MAX_AGE_MS = 10L * 60L * 1000L;','private static final long MAX_AGE_MS = Long.MAX_VALUE; // V0884_NO_LOCAL_AGE_CUTOFF')
w=w.replace('if (measuredAt <= 0L || now - measuredAt > MAX_AGE_MS || measuredAt - now > FUTURE_TOLERANCE_MS) {','if (measuredAt <= 0L || measuredAt - now > FUTURE_TOLERANCE_MS) {')
w=w.replace('Only fresh, verified\n * BIPAD/DHM warning/danger observations inside 2 km','Latest verified\n * BIPAD/DHM warning/danger observations inside 2 km')

# Version bump.
g=re.sub(r'versionCode\s+103\b','versionCode 104',g,count=1)
g=g.replace("versionName '0.8.83'","versionName '0.8.84'",1)

for token in ['V0884_LATEST_OFFICIAL_READING_VISIBLE','V0884_STATUS_COLOUR_STATION_RIVERS_BACKGROUND','V0884_MATCH_LATEST_STATION_STATUS_TO_RIVER','V0884_RIVER_STATUS_COLOUR_LAYERS']:
    if token not in m: raise SystemExit('missing '+token)
if 'V0884_NO_LOCAL_AGE_CUTOFF' not in w: raise SystemExit('alert cutoff patch missing')
if 'versionCode 104' not in g or "versionName '0.8.84'" not in g: raise SystemExit('v0884 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
w_path.write_text(w,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.84 PASS: no arbitrary reading-age cutoff + latest-source river flow/glow + status colours + 2km alert source truth')
