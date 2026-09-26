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
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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
    if not sp:raise SystemExit('v0896 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# Official BIPAD status wins over contradictory numeric thresholds.
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        double la=numDeep(r,r.optJSONObject("fields"),"latitude","lat","stationLatitude","station_latitude");
        double lo=numDeep(r,r.optJSONObject("fields"),"longitude","lon","lng","stationLongitude","station_longitude");
        if(!nepal(la,lo))return null;
        double level=v877ObservationLevel(r);
        double warning=numDeep(r,r.optJSONObject("fields"),"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel");
        double danger=numDeep(r,r.optJSONObject("fields"),"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=v877ObservationTime(r);
        boolean has=Double.isFinite(level)&&at>0L;
        boolean matched=r.optBoolean("_floodsafeObservationMatched",false);
        boolean online=matched&&has;
        boolean fresh=online&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L;
        String raw=strDeep(r,r.optJSONObject("fields"),"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(has){
            boolean belowWarning=raw.contains("BELOW WARNING")||raw.contains("BELOWWARNING");
            boolean officialNormal=belowWarning||raw.contains("NORMAL")||raw.contains("GREEN")||raw.contains("SAFE");
            boolean officialDanger=(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED");
            boolean officialWarning=(raw.contains("WARNING")&&!belowWarning)||raw.contains("ORANGE")||raw.contains("BELOW DANGER");
            boolean officialAlert=raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW");
            if(officialNormal){stage="normal";rank=3;}
            else if(officialDanger){stage="danger";rank=0;}
            else if(officialWarning){stage="warning";rank=1;}
            else if(officialAlert){stage="alert";rank=2;}
            else{
                boolean sane=Double.isFinite(warning)&&Double.isFinite(danger)&&warning>0d&&danger>warning;
                if(sane&&level>=danger){stage="danger";rank=0;}
                else if(sane&&level>=warning){stage="warning";rank=1;}
                else {stage="normal";rank=3;}
            }
        }
        String name=v846StationName(r);if(name.isEmpty())name=v877RiverName(r);if(name.isEmpty())name="Official river station";
        String district=strDeep(r,r.optJSONObject("fields"),"districtName","district_name","district");
        String basin=strDeep(r,r.optJSONObject("fields"),"basinName","basin_name","basin");
        String id=v846StationIndex(r);
        String source=strDeep(r,r.optJSONObject("fields"),"_floodsafeSource","source");
        String description=strDeep(r,r.optJSONObject("fields"),"description","stationDescription","station_description");
        String river=v877RiverName(r);if(river.isEmpty())river=name;
        double elev=numDeep(r,r.optJSONObject("fields"),"elevation","elevationM","elevation_m");
        double rain=numDeep(r,r.optJSONObject("fields"),"rainfall","rainfallMm","rainfall_mm","rain24h","rainfall24h");
        return new RiverStation(name,district,basin,id,source,description,river,la,lo,elev,level,warning,danger,rain,at,fresh,stage,rank,raw);
    } // V0896_OFFICIAL_STATUS_FIRST
'''
a=replace_method(a,'parseStation',parse)

# Keep only actual rivers bound to official station coordinates. Camera refresh may not overwrite them.
field_anchor='    private volatile String v879RiverGeometryKey=""; // V0879_FULL_RIVER_TILE_RUNTIME\n'
if field_anchor not in m:raise SystemExit('v0896 requires v0879 map patch')
m=m.replace(field_anchor,field_anchor+'    private volatile String v896StationRiverSignature="";\n    private volatile int v896StationRiverGeneration=0; // V0896_STATION_RIVERS_ONLY\n',1)

set_stations=r'''    void setStations(List<?> source, double lat, double lon) {
        userLat=lat;userLon=lon;
        List<StationDot> next=new ArrayList<>();
        if(source!=null)for(Object o:source){StationDot s=readStation(o);if(s!=null)next.add(s);}
        synchronized(stations){stations.clear();stations.addAll(next);}
        refreshStationSources();refreshUserSource();
        v896ScheduleStationRivers(next);
        v896RefreshRiverStages(next);
    } // V0896_BIND_RIVERS_FROM_STATIONS
'''
m=replace_method(m,'setStations',set_stations)

# Disable broad overview/regional camera river swaps: monitored station-river set is authoritative.
m=replace_method(m,'v879RefreshRiverGeometryForCamera',r'''    private void v879RefreshRiverGeometryForCamera(){
        // V0896_NO_CAMERA_RIVER_OVERWRITE: station-bound river geometry is persistent.
    }
''')
m=replace_method(m,'v879ApplyRiverGeometry',r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        main.post(this::installGeoLayers); // V0896_NO_BROAD_RIVER_SWAP
    }
''')

# Always create an empty river source/layers first; station geometry later fills the source.
install=r'''    private void installGeoLayers() {
        if(!styleReady||style==null)return;
        try{
            if(districtGeoJson!=null&&style.getSource("fs-districts")==null){
                style.addSource(new GeoJsonSource("fs-districts",districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill","fs-districts").withProperties(fillColor("#8deeff"),fillOpacity(0.08f)));
                style.addLayer(new LineLayer("fs-district-lines","fs-districts").withProperties(lineColor("#e8fbff"),lineWidth(1.15f),lineOpacity(0.82f),lineJoin(LINE_JOIN_ROUND)));
            }
            if(style.getSource("fs-rivers")==null){
                style.addSource(new GeoJsonSource("fs-rivers",emptyFeatureCollection()));
                style.addLayer(new LineLayer("fs-river-glow","fs-rivers").withProperties(lineColor("#008db8"),lineWidth(10.0f),lineOpacity(0.38f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-rivers-layer","fs-rivers").withProperties(lineColor("#39ddff"),lineWidth(4.2f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            }
            v896EnsureRisk("fs-river-alert","fs-river-alert-glow","fs-river-alert-layer","#ffd12a");
            v896EnsureRisk("fs-river-warning","fs-river-warning-glow","fs-river-warning-layer","#ff8a1f");
            v896EnsureRisk("fs-river-danger","fs-river-danger-glow","fs-river-danger-layer","#f22f4b");
            ensurePointSource("fs-flow-particles","fs-flow-particles-layer","#e8fdff",3.1f,0.96f);
            ensurePointSource("fs-stale","fs-stale-layer","#7f8995",6.6f,0.96f);
            ensurePointSource("fs-normal","fs-normal-layer","#22b37a",7.0f,1f);
            ensurePointSource("fs-alert","fs-alert-layer","#ffd12a",7.4f,1f);
            ensurePointSource("fs-warning","fs-warning-layer","#ff8a1f",8.0f,1f);
            ensurePointSource("fs-danger","fs-danger-layer","#f22f4b",8.6f,1f);
            if(style.getSource("fs-user")==null){
                style.addSource(new GeoJsonSource("fs-user",emptyFeatureCollection()));
                style.addLayer(new CircleLayer("fs-user-halo","fs-user").withProperties(circleColor("#ffffff"),circleRadius(9.0f),circleOpacity(0.72f)));
                style.addLayer(new CircleLayer("fs-user-layer","fs-user").withProperties(circleColor("#0b7fd0"),circleRadius(5.7f),circleStrokeColor("#ffffff"),circleStrokeWidth(1.5f)));
            }
            refreshStationSources();refreshUserSource();v896PushRiverSources();
        }catch(Exception ignored){}
    } // V0896_VISIBLE_RIVER_LAYERS
'''
m=replace_method(m,'installGeoLayers',install)

insert_at=method_span(m,'setStations')[1]
helpers=r'''

    private void v896EnsureRisk(String sourceId,String glowId,String layerId,String color){
        if(style.getSource(sourceId)!=null)return;
        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        style.addLayer(new LineLayer(glowId,sourceId).withProperties(lineColor(color),lineWidth(12.0f),lineOpacity(0.34f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(5.0f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }

    private static String v896Name(String s){
        if(s==null)return "";String x=s.toLowerCase(Locale.ROOT);
        x=x.replaceAll("\\(.*?\\)"," ").replaceAll("\\bat\\b.*$"," ");
        x=x.replace("river", " ").replace("khola"," ").replace("nadi"," ").replace("nadi"," ").replace("नदी"," ").replace("खोला"," ");
        return x.replaceAll("[^a-z0-9\\p{L}]"," ").replaceAll("\\s+"," ").trim();
    }

    private static double v896Km(double a,double b,double c,double d){
        double r=6371d,dl=Math.toRadians(c-a),dn=Math.toRadians(d-b);
        double q=Math.sin(dl/2)*Math.sin(dl/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(dn/2)*Math.sin(dn/2);
        return 2*r*Math.asin(Math.min(1d,Math.sqrt(q)));
    }

    private static double v896RiverDistanceKm(double lat,double lon,RiverWay r){
        double best=Double.POSITIVE_INFINITY;if(r==null)return best;
        for(double[] p:r.points)if(p!=null&&p.length>=2)best=Math.min(best,v896Km(lat,lon,p[1],p[0]));
        return best;
    }

    private static int v896Severity(String s){String x=normalizeStage(s);return "danger".equals(x)?3:"warning".equals(x)?2:"alert".equals(x)?1:0;}
    private static String v896Stage(int n){return n>=3?"danger":n==2?"warning":n==1?"alert":"normal";}

    private String v896Signature(List<StationDot> list){
        List<String> x=new ArrayList<>();for(StationDot s:list)x.add(v896Name(s.name)+":"+Math.round(s.lat*100000d)+":"+Math.round(s.lon*100000d));Collections.sort(x);return x.toString();
    }

    private void v896ScheduleStationRivers(List<StationDot> stationList){
        if(stationList==null||stationList.isEmpty())return;String sig=v896Signature(stationList);if(sig.equals(v896StationRiverSignature))return;
        v896StationRiverSignature=sig;final int gen=++v896StationRiverGeneration;final List<StationDot> snap=new ArrayList<>(stationList);
        io.execute(()->{
            java.util.HashMap<String,List<RiverWay>> cache=new java.util.HashMap<>();java.util.LinkedHashMap<String,RiverWay> selected=new java.util.LinkedHashMap<>();
            for(StationDot s:snap){
                int cx=v879TileX(s.lon),cy=v879TileY(s.lat);List<RiverWay> local=new ArrayList<>();
                for(int x=Math.max(0,cx-1);x<=Math.min(V879_TILE_NX-1,cx+1);x++)for(int y=Math.max(0,cy-1);y<=Math.min(V879_TILE_NY-1,cy+1);y++){
                    String p="data/nepal-waterways-tiles/"+x+"-"+y+".json";List<RiverWay> z=cache.get(p);
                    if(z==null){try{z=v879ReadRiverAsset(p);}catch(Exception e){z=new ArrayList<>();}cache.put(p,z);}local.addAll(z);
                }
                String sk=v896Name(s.name);RiverWay best=null,bestNamed=null;double bd=Double.POSITIVE_INFINITY,bnd=Double.POSITIVE_INFINITY;
                for(RiverWay r:local){double d=v896RiverDistanceKm(s.lat,s.lon,r);if(d<bd){bd=d;best=r;}String rk=v896Name(r.name);if(!sk.isEmpty()&&!rk.isEmpty()&&(sk.equals(rk)||sk.contains(rk)||rk.contains(sk))&&d<bnd){bnd=d;bestNamed=r;}}
                RiverWay seed=(bestNamed!=null&&bnd<=30d)?bestNamed:best;if(seed==null)continue;
                selected.put(v879RiverKey(seed),seed);String rk=v896Name(seed.name);
                if(!rk.isEmpty()&&!"नदी खोला".equals(rk))for(RiverWay r:local){if(rk.equals(v896Name(r.name))&&v896RiverDistanceKm(s.lat,s.lon,r)<=18d)selected.put(v879RiverKey(r),r);}
            }
            final List<RiverWay> out=new ArrayList<>(selected.values());main.post(()->{
                if(gen!=v896StationRiverGeneration||out.isEmpty())return;rivers.clear();rivers.addAll(out);riversGeoJson=makeRiversGeoJson(out);v879RiverGeometryKey="v896-station-rivers";
                installGeoLayers();setGeo("fs-rivers",riversGeoJson);v896RefreshRiverStages(snap); // V0896_NONEMPTY_STATION_RIVER_SOURCE
            });
        });
    }

    private void v896RefreshRiverStages(List<StationDot> stationList){
        if(rivers.isEmpty())return;
        for(RiverWay r:rivers){int sev=0;String rk=v896Name(r.name);for(StationDot s:stationList){if(!s.fresh)continue;String sk=v896Name(s.name);double d=v896RiverDistanceKm(s.lat,s.lon,r);if((!rk.isEmpty()&&!sk.isEmpty()&&(sk.equals(rk)||sk.contains(rk)||rk.contains(sk)))||d<=3d)sev=Math.max(sev,v896Severity(s.stage));}r.stage=v896Stage(sev);}
        v896PushRiverSources();
    }

    private String v896RiverGeo(String stage){List<RiverWay> z=new ArrayList<>();for(RiverWay r:rivers)if(stage.equals(normalizeStage(r.stage)))z.add(r);return makeRiversGeoJson(z);}
    private void v896PushRiverSources(){
        if(!styleReady||style==null)return;if(riversGeoJson!=null)setGeo("fs-rivers",riversGeoJson);
        setGeo("fs-river-alert",v896RiverGeo("alert"));setGeo("fs-river-warning",v896RiverGeo("warning"));setGeo("fs-river-danger",v896RiverGeo("danger"));
    } // V0896_STATUS_COLOUR_ON_MONITORED_RIVERS
'''
m=m[:insert_at]+helpers+m[insert_at:]

# Version bump after v0.8.79 patch has run.
g=re.sub(r'versionCode\s+99\b','versionCode 116',g,count=1)
g=g.replace("versionName '0.8.79'","versionName '0.8.96'",1)
if 'versionCode 116' not in g or "versionName '0.8.96'" not in g:raise SystemExit('v0896 version bump failed')

for marker in ['V0896_OFFICIAL_STATUS_FIRST','V0896_STATION_RIVERS_ONLY','V0896_BIND_RIVERS_FROM_STATIONS','V0896_NO_CAMERA_RIVER_OVERWRITE','V0896_VISIBLE_RIVER_LAYERS','V0896_NONEMPTY_STATION_RIVER_SOURCE','V0896_STATUS_COLOUR_ON_MONITORED_RIVERS']:
    if marker not in a+m:raise SystemExit('missing '+marker)

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.96 station-river truth patch applied')
