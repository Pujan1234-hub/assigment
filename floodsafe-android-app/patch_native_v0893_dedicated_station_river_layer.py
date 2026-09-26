from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Dedicated river render path. It deliberately does NOT depend on fs-rivers/v879 runtime state.
# It reads the build-generated nationwide named medium river asset, matches official station dots
# to those real geometries in the background, and renders the result through its own MapLibre source.
field_anchor='    private boolean animationRunning = false;'
fields='''    private boolean animationRunning = false;\n    private final List<RiverWay> v893AllRivers = new ArrayList<>();\n    private final List<RiverWay> v893StationRivers = new ArrayList<>();\n    private String v893StationRiverGeoJson = null;\n    private boolean v893PulseStarted = false; // V0893_DEDICATED_STATION_RIVER_LAYER\n'''
if field_anchor not in m: raise SystemExit('field anchor missing')
m=m.replace(field_anchor,fields,1)

ctor_anchor='        loadBundledGeometry();'
if ctor_anchor not in m: raise SystemExit('constructor load anchor missing')
m=m.replace(ctor_anchor,ctor_anchor+'\n        v893LoadDedicatedRiverBase(); // V0893_LOAD_NAMED_NATIONWIDE_RIVER_ASSET',1)

# Recompute only the dedicated river layer whenever the official station inventory/readings change.
set_anchor='        refreshUserSource();'
if set_anchor not in m: raise SystemExit('setStations anchor missing')
# First occurrence is inside setStations in the final patched source.
m=m.replace(set_anchor,set_anchor+'\n        v893RefreshDedicatedStationRivers(); // V0893_REFRESH_FROM_OFFICIAL_STATIONS',1)

helper=r'''
    private void v893LoadDedicatedRiverBase(){
        io.execute(()->{
            try{
                String raw=readAsset("data/nepal-waterways-medium-v0842.geojson");
                JSONObject fc=new JSONObject(raw);JSONArray fs=fc.optJSONArray("features");
                List<RiverWay> parsed=new ArrayList<>();
                if(fs!=null) for(int i=0;i<fs.length();i++){
                    JSONObject f=fs.optJSONObject(i);if(f==null)continue;
                    JSONObject geom=f.optJSONObject("geometry");if(geom==null||!"LineString".equals(geom.optString("type")))continue;
                    JSONArray cs=geom.optJSONArray("coordinates");if(cs==null||cs.length()<2)continue;
                    RiverWay r=new RiverWay();JSONObject p=f.optJSONObject("properties");
                    r.name=p==null?"नदी / खोला":firstNonEmpty(p.optString("name"),p.optString("name_en"),p.optString("name_osm"),"नदी / खोला");
                    r.type=p==null?"river":p.optString("type","river");
                    for(int j=0;j<cs.length();j++){JSONArray q=cs.optJSONArray(j);if(q==null||q.length()<2)continue;double lo=q.optDouble(0,Double.NaN),la=q.optDouble(1,Double.NaN);if(Double.isFinite(lo)&&Double.isFinite(la)&&isNepalish(la,lo))r.points.add(new double[]{lo,la});}
                    if(r.points.size()>=2)parsed.add(r);
                }
                synchronized(v893AllRivers){v893AllRivers.clear();v893AllRivers.addAll(parsed);}
                main.post(this::v893EnsureDedicatedLayers);
                v893RefreshDedicatedStationRivers();
            }catch(Exception ignored){}
        });
    } // V0893_LOAD_MEDIUM_NAMED_ASSET_DIRECT

    private void v893RefreshDedicatedStationRivers(){
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        final List<RiverWay> all; synchronized(v893AllRivers){all=new ArrayList<>(v893AllRivers);}
        if(ss.isEmpty()||all.isEmpty())return;
        io.execute(()->{
            java.util.LinkedHashSet<RiverWay> chosen=new java.util.LinkedHashSet<>();
            java.util.LinkedHashSet<String> names=new java.util.LinkedHashSet<>();
            for(StationDot s:ss){
                if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                String sn=v881Norm(s.name);RiverWay bestName=null,bestNear=null;double dn=Double.POSITIVE_INFINITY,da=Double.POSITIVE_INFINITY;
                for(RiverWay r:all){
                    if(r==null||r.points==null||r.points.size()<2)continue;
                    double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(!Double.isFinite(d))continue;
                    String rn=v881Norm(r.name);boolean nm=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                    if(nm&&d<dn){dn=d;bestName=r;}if(d<da){da=d;bestNear=r;}
                }
                RiverWay seed=bestName!=null?bestName:bestNear;
                if(seed!=null){chosen.add(seed);String k=v881Norm(seed.name);if(!k.isEmpty())names.add(k);}
            }
            if(!names.isEmpty())for(RiverWay r:all){String rn=v881Norm(r.name);if(rn.isEmpty())continue;for(String k:names){if(rn.equals(k)||rn.contains(k)||k.contains(rn)){chosen.add(r);break;}}}
            final List<RiverWay> selected=new ArrayList<>(chosen);
            try{
                final String geo=selected.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(selected);
                List<RiverWay> al=new ArrayList<>(),wa=new ArrayList<>(),da=new ArrayList<>();
                for(RiverWay r:selected){String st=v884Stage(r,ss);if("danger".equals(st))da.add(r);else if("warning".equals(st))wa.add(r);else if("alert".equals(st))al.add(r);}
                final String ag=al.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(al),wg=wa.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(wa),dg=da.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(da);
                main.post(()->{
                    v893StationRivers.clear();v893StationRivers.addAll(selected);v893StationRiverGeoJson=geo;
                    v893EnsureDedicatedLayers();v893SetGeo("fs-v893-station-rivers",geo);
                    v893SetGeo("fs-v893-alert",ag);v893SetGeo("fs-v893-warning",wg);v893SetGeo("fs-v893-danger",dg);
                });
            }catch(Exception ignored){}
        });
    } // V0893_EACH_OFFICIAL_STATION_BINDS_REAL_NAMED_OR_NEAREST_RIVER

    private void v893EnsureDedicatedLayers(){
        if(!styleReady||style==null)return;
        try{
            String empty=emptyFeatureCollection();
            if(style.getSource("fs-v893-station-rivers")==null)style.addSource(new GeoJsonSource("fs-v893-station-rivers",v893StationRiverGeoJson==null?empty:v893StationRiverGeoJson));
            if(style.getLayer("fs-v893-river-glow")==null){LineLayer x=new LineLayer("fs-v893-river-glow","fs-v893-station-rivers").withProperties(lineColor("#00bfe8"),lineWidth(12.0f),lineOpacity(.44f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND));style.addLayer(x);}
            if(style.getLayer("fs-v893-river-core")==null){LineLayer x=new LineLayer("fs-v893-river-core","fs-v893-station-rivers").withProperties(lineColor("#63efff"),lineWidth(4.4f),lineOpacity(1f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND));style.addLayer(x);}
            v893StatusLayer("alert","#ffc928");v893StatusLayer("warning","#ff8a1f");v893StatusLayer("danger","#f22f4b");
            if(!v893PulseStarted){v893PulseStarted=true;main.post(v893PulseTick);}
        }catch(Exception ignored){}
    } // V0893_PERMANENT_TOP_MAPLIBRE_SOURCE

    private void v893StatusLayer(String n,String color){
        try{String sid="fs-v893-"+n,lid=sid+"-line";if(style.getSource(sid)==null)style.addSource(new GeoJsonSource(sid,emptyFeatureCollection()));if(style.getLayer(lid)==null)style.addLayer(new LineLayer(lid,sid).withProperties(lineColor(color),lineWidth(6.2f),lineOpacity(1f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));}catch(Exception ignored){}
    }
    private void v893SetGeo(String id,String geo){try{GeoJsonSource s=style==null?null:style.getSourceAs(id);if(s!=null)s.setGeoJson(geo);}catch(Exception ignored){}}

    private final Runnable v893PulseTick=new Runnable(){@Override public void run(){
        if(!v893PulseStarted||!styleReady||style==null)return;try{LineLayer l=style.getLayerAs("fs-v893-river-glow");if(l!=null){double p=(System.currentTimeMillis()%1800L)/1800.0;float wave=(float)((Math.sin(p*Math.PI*2.0)+1.0)/2.0);l.setProperties(lineWidth(9.5f+wave*4.5f),lineOpacity(.30f+wave*.24f));}}catch(Exception ignored){}main.postDelayed(this,90L);
    }}; // V0893_VISIBLE_FLOW_GLOW_PULSE
'''

anchor='    private StationDot readStation(Object o)'
if anchor not in m: raise SystemExit('readStation anchor missing')
m=m.replace(anchor,helper+'\n'+anchor,1)

# Existing moving particles must prefer the dedicated station-river list, so actual movement follows
# the same cyan network rather than an older fs-rivers list.
old='''                int n = Math.min(36, rivers.size());'''
new='''                List<RiverWay> flowWays = v893StationRivers.isEmpty() ? rivers : v893StationRivers;\n                int n = Math.min(48, flowWays.size());'''
if old not in m: raise SystemExit('particle count anchor missing')
m=m.replace(old,new,1)
if 'RiverWay r = rivers.get(i);' not in m: raise SystemExit('particle river anchor missing')
m=m.replace('RiverWay r = rivers.get(i);','RiverWay r = flowWays.get(i);',1)

# Version only. No station loader, Supabase, alert worker, UI card, or other behavior is modified here.
g=re.sub(r'versionCode\s+112\b','versionCode 113',g,count=1)
g=g.replace("versionName '0.8.92'","versionName '0.8.93'",1)

for token in ['V0893_DEDICATED_STATION_RIVER_LAYER','V0893_LOAD_MEDIUM_NAMED_ASSET_DIRECT','V0893_EACH_OFFICIAL_STATION_BINDS_REAL_NAMED_OR_NEAREST_RIVER','V0893_PERMANENT_TOP_MAPLIBRE_SOURCE','V0893_VISIBLE_FLOW_GLOW_PULSE']:
    if token not in m: raise SystemExit('missing '+token)
if 'data/nepal-waterways-medium-v0842.geojson' not in m: raise SystemExit('dedicated river asset path missing')
if "versionName '0.8.93'" not in g or 'versionCode 113' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.93 PASS: dedicated station-river asset/source + forced cyan flow/glow + independent status overlays')
