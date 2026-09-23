from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.79: use the progressive national/regional/exact river assets that are already
# bundled for FloodSafe. The previous native MapLibre path parsed the huge snapshot and
# then globally retained only 1,400 OSM ways, creating disconnected/half river lines.

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
    if not sp:raise SystemExit('v0879 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

field_anchor='    private String riversGeoJson = null;\n'
fields='''    private String riversGeoJson = null;\n    private static final double V879_TILE_MIN_LON=80.0, V879_TILE_MIN_LAT=26.2, V879_TILE_STEP_LON=0.70, V879_TILE_STEP_LAT=0.60;\n    private static final int V879_TILE_NX=12, V879_TILE_NY=8;\n    private volatile int v879RiverLoadGeneration=0;\n    private volatile String v879RiverGeometryKey=""; // V0879_FULL_RIVER_TILE_RUNTIME\n'''
if 'V0879_FULL_RIVER_TILE_RUNTIME' not in m:
    if field_anchor not in m:raise SystemExit('v0879 field anchor missing')
    m=m.replace(field_anchor,fields,1)

click_anchor='            map.addOnMapClickListener(this::onMapClick);\n'
if 'V0879_CAMERA_IDLE_RIVER_DETAIL' not in m:
    if click_anchor not in m:raise SystemExit('v0879 camera listener anchor missing')
    m=m.replace(click_anchor,click_anchor+'            map.addOnCameraIdleListener(this::v879RefreshRiverGeometryForCamera); // V0879_CAMERA_IDLE_RIVER_DETAIL\n',1)

loader=r'''    private void loadBundledGeometry() {
        io.execute(() -> {
            try {
                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");
            } catch (Exception ignored) {
                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}
            }
            int gen=++v879RiverLoadGeneration;
            try {
                List<RiverWay> all=v879ReadRiverAsset("data/nepal-waterways-tiles/overview.json");
                v879ApplyRiverGeometry(all,"overview",gen);
            } catch (Exception ignored) {
                try {
                    List<RiverWay> all=v879ReadRiverAsset("data/nepal-waterways-snapshot.json");
                    v879ApplyRiverGeometry(all,"snapshot-fallback",gen);
                } catch (Exception ignored2) { main.post(this::installGeoLayers); }
            }
        });
    } // V0879_NO_GLOBAL_1400_TRUNCATION
'''
m=replace_method(m,'loadBundledGeometry',loader)

sp=method_span(m,'loadBundledGeometry')
if not sp:raise SystemExit('v0879 loader span missing after replacement')
helpers=r'''

    private List<RiverWay> v879ReadRiverAsset(String path) throws Exception {
        JSONObject root=new JSONObject(readAsset(path));
        JSONArray ways=root.optJSONArray("waterways");
        List<RiverWay> out=new ArrayList<>();
        if(ways==null)return out;
        for(int i=0;i<ways.length();i++){
            JSONObject w=ways.optJSONObject(i);if(w==null)continue;
            JSONArray pts=w.optJSONArray("pts");if(pts==null||pts.length()<2)continue;
            RiverWay rw=new RiverWay();
            Object rid=w.opt("id");rw.id=rid==null||rid==JSONObject.NULL?"":String.valueOf(rid);
            rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");
            rw.type=w.optString("type","stream");
            for(int j=0;j<pts.length();j++){
                JSONArray p=pts.optJSONArray(j);if(p==null||p.length()<2)continue;
                double lo=p.optDouble(0,Double.NaN),la=p.optDouble(1,Double.NaN);
                if(Double.isFinite(la)&&Double.isFinite(lo)&&isNepalish(la,lo))rw.points.add(new double[]{lo,la});
            }
            if(rw.points.size()>=2)out.add(rw);
        }
        return out;
    } // V0879_PARSE_ALL_RIVER_WAYS

    private static String v879RiverKey(RiverWay r){
        if(r==null)return "";if(r.id!=null&&!r.id.isEmpty())return "id:"+r.id;
        if(r.points.size()<2)return "";double[] a=r.points.get(0),b=r.points.get(r.points.size()-1);
        return (r.type==null?"stream":r.type)+"|"+Math.round(a[0]*100000d)+":"+Math.round(a[1]*100000d)+"|"+Math.round(b[0]*100000d)+":"+Math.round(b[1]*100000d);
    }

    private static List<RiverWay> v879Dedup(List<RiverWay> input){
        java.util.LinkedHashMap<String,RiverWay> by=new java.util.LinkedHashMap<>();
        if(input!=null)for(RiverWay r:input){String k=v879RiverKey(r);if(!k.isEmpty()&&!by.containsKey(k))by.put(k,r);}
        return new ArrayList<>(by.values());
    } // V0879_DEDUP_TILE_OVERLAP

    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> next=v879Dedup(input);
        main.post(()->{
            if(generation!=v879RiverLoadGeneration||next.isEmpty())return;
            try{
                rivers.clear();rivers.addAll(next);riversGeoJson=makeRiversGeoJson(next);v879RiverGeometryKey=key;
                if(styleReady&&style!=null){GeoJsonSource s=style.getSourceAs("fs-rivers");if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();}
                else installGeoLayers();
            }catch(Exception ignored){}
        });
    } // V0879_ATOMIC_RIVER_SOURCE_SWAP

    private static int v879TileX(double lon){return Math.max(0,Math.min(V879_TILE_NX-1,(int)Math.floor((lon-V879_TILE_MIN_LON)/V879_TILE_STEP_LON)));}
    private static int v879TileY(double lat){return Math.max(0,Math.min(V879_TILE_NY-1,(int)Math.floor((lat-V879_TILE_MIN_LAT)/V879_TILE_STEP_LAT)));}

    private void v879RefreshRiverGeometryForCamera(){
        if(map==null)return;CameraPosition cp=map.getCameraPosition();if(cp==null||cp.target==null)return;
        final double zoom=cp.zoom,lon=cp.target.getLongitude(),lat=cp.target.getLatitude();if(!isNepalish(lat,lon))return;
        if(zoom<7.35){v879QueueRiverAssets("overview",java.util.Collections.singletonList("data/nepal-waterways-tiles/overview.json"));return;}
        int cx=v879TileX(lon),cy=v879TileY(lat);
        if(zoom<10.0){
            List<String> paths=new ArrayList<>();
            for(int x=Math.max(0,cx-1);x<=Math.min(V879_TILE_NX-1,cx+1);x++)for(int y=Math.max(0,cy-1);y<=Math.min(V879_TILE_NY-1,cy+1);y++)paths.add("data/nepal-waterways-tiles-regional/"+x+"-"+y+".json");
            v879QueueRiverAssets("regional:"+cx+":"+cy,paths);return;
        }
        List<Integer> xs=new ArrayList<>(),ys=new ArrayList<>();xs.add(cx);ys.add(cy);
        double qx=(lon-V879_TILE_MIN_LON)/V879_TILE_STEP_LON,qy=(lat-V879_TILE_MIN_LAT)/V879_TILE_STEP_LAT;
        double fx=qx-Math.floor(qx),fy=qy-Math.floor(qy);
        if(fx<0.22&&cx>0)xs.add(cx-1);else if(fx>0.78&&cx<V879_TILE_NX-1)xs.add(cx+1);
        if(fy<0.22&&cy>0)ys.add(cy-1);else if(fy>0.78&&cy<V879_TILE_NY-1)ys.add(cy+1);
        List<String> paths=new ArrayList<>();for(int x:xs)for(int y:ys)paths.add("data/nepal-waterways-tiles/"+x+"-"+y+".json");
        java.util.Collections.sort(paths);v879QueueRiverAssets("exact:"+cx+":"+cy+":"+paths.toString(),paths);
    } // V0879_PROGRESSIVE_77_DISTRICT_GEOMETRY

    private void v879QueueRiverAssets(String key,List<String> paths){
        if(key.equals(v879RiverGeometryKey))return;final int gen=++v879RiverLoadGeneration;
        io.execute(()->{
            List<RiverWay> all=new ArrayList<>();
            if(paths!=null)for(String p:paths){try{all.addAll(v879ReadRiverAsset(p));}catch(Exception ignored){}}
            if(all.isEmpty()&&!"overview".equals(key)){try{all.addAll(v879ReadRiverAsset("data/nepal-waterways-tiles/overview.json"));}catch(Exception ignored){}}
            v879ApplyRiverGeometry(all,key,gen);
        });
    } // V0879_VISIBLE_TILE_LOADER
'''
m=m[:sp[1]]+helpers+m[sp[1]:]

# Patch whatever RiverWay shape the proven v0.8.77 chain produced; preserve all its
# existing fields and only add the stable OSM id used to deduplicate overlapping tiles.
if 'V0879_RIVER_IDENTITY' not in m:
    q=re.search(r'private static final class RiverWay\s*\{',m)
    if not q:raise SystemExit('v0879 RiverWay class missing')
    pos=q.end()
    m=m[:pos]+'\n        String id; // V0879_RIVER_IDENTITY'+m[pos:]

# Distinguishable field-test version.
g=re.sub(r'versionCode\s+98\b','versionCode 99',g,count=1)
g=g.replace("versionName '0.8.78'","versionName '0.8.79'",1)
if 'versionCode 99' not in g or "versionName '0.8.79'" not in g:raise SystemExit('v0879 version bump failed')

need=['V0879_FULL_RIVER_TILE_RUNTIME','V0879_CAMERA_IDLE_RIVER_DETAIL','V0879_NO_GLOBAL_1400_TRUNCATION','V0879_PARSE_ALL_RIVER_WAYS','V0879_DEDUP_TILE_OVERLAP','V0879_ATOMIC_RIVER_SOURCE_SWAP','V0879_PROGRESSIVE_77_DISTRICT_GEOMETRY','V0879_VISIBLE_TILE_LOADER','V0879_RIVER_IDENTITY']
for x in need:
    if x not in m:raise SystemExit('missing '+x)
if 'if (all.size() > 1400)' in m:raise SystemExit('old 1400-river truncation still present')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.79 full river geometry patch applied')
