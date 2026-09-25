from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.80: keep v0.8.79 full 60k+ river tile runtime, then add live station-driven
# river status overlays without removing any bundled map/river assets.

if 'V0880_RIVER_STATUS_OVERLAY' not in m:
    # Add three status sources/layers after the base river layer is installed.
    anchor='''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));\n'''
    insert=anchor+'''                if(style.getSource("fs-river-alert")==null) style.addSource(new GeoJsonSource("fs-river-alert", emptyFeatureCollection()));\n                if(style.getSource("fs-river-warning")==null) style.addSource(new GeoJsonSource("fs-river-warning", emptyFeatureCollection()));\n                if(style.getSource("fs-river-danger")==null) style.addSource(new GeoJsonSource("fs-river-danger", emptyFeatureCollection()));\n                style.addLayer(new LineLayer("fs-river-alert-layer","fs-river-alert").withProperties(lineColor("#ffc928"),lineWidth(3.2f),lineOpacity(0.98f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n                style.addLayer(new LineLayer("fs-river-warning-layer","fs-river-warning").withProperties(lineColor("#ff8a1f"),lineWidth(3.8f),lineOpacity(0.99f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n                style.addLayer(new LineLayer("fs-river-danger-layer","fs-river-danger").withProperties(lineColor("#f22f4b"),lineWidth(4.6f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND))); // V0880_RIVER_STATUS_OVERLAY\n'''
    if anchor not in m:
        raise SystemExit('v0880 base river layer anchor missing')
    m=m.replace(anchor,insert,1)

    # Refresh status overlays whenever live station data changes.
    anchor2='''        refreshStationSources();\n        refreshUserSource();\n    }\n\n    void zoomBy'''
    repl2='''        refreshStationSources();\n        refreshUserSource();\n        refreshRiverRiskSources(); // V0880_LIVE_RIVER_STATUS_REFRESH\n    }\n\n    void zoomBy'''
    if anchor2 not in m:
        raise SystemExit('v0880 setStations anchor missing')
    m=m.replace(anchor2,repl2,1)

    # Keep overlays in sync after camera-driven v0.8.79 river tile swaps too.
    anchor3='''                if(styleReady&&style!=null){GeoJsonSource s=style.getSourceAs("fs-rivers");if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();}\n                else installGeoLayers();\n'''
    repl3='''                if(styleReady&&style!=null){GeoJsonSource s=style.getSourceAs("fs-rivers");if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();refreshRiverRiskSources();}\n                else installGeoLayers(); // V0880_TILE_SWAP_STATUS_REFRESH\n'''
    if anchor3 not in m:
        raise SystemExit('v0880 v879 swap anchor missing')
    m=m.replace(anchor3,repl3,1)

    # Insert matching helpers before ensurePointSource.
    helper_anchor='''    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {'''
    helpers=r'''    private void refreshRiverRiskSources(){
        if(!styleReady||style==null)return;
        List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);} 
        List<RiverWay> rr=new ArrayList<>(rivers);
        StringBuilder alert=new StringBuilder("{\"type\":\"FeatureCollection\",\"features\":[");
        StringBuilder warning=new StringBuilder("{\"type\":\"FeatureCollection\",\"features\":[");
        StringBuilder danger=new StringBuilder("{\"type\":\"FeatureCollection\",\"features\":[");
        boolean aa=false,ww=false,dd=false;
        for(RiverWay r:rr){
            String stage=v880RiverStage(r,ss); if(stage==null)continue;
            String feat=v880RiverFeature(r,stage); if(feat==null)continue;
            if("danger".equals(stage)){if(dd)danger.append(',');danger.append(feat);dd=true;}
            else if("warning".equals(stage)){if(ww)warning.append(',');warning.append(feat);ww=true;}
            else if("alert".equals(stage)){if(aa)alert.append(',');alert.append(feat);aa=true;}
        }
        alert.append("]}");warning.append("]}");danger.append("]}");
        setGeo("fs-river-alert",alert.toString());setGeo("fs-river-warning",warning.toString());setGeo("fs-river-danger",danger.toString());
    } // V0880_RIVER_STATUS_OVERLAY_REFRESH

    private String v880RiverStage(RiverWay r,List<StationDot> ss){
        int best=0;String rn=v880Norm(r==null?null:r.name);
        if(r==null||r.points==null||r.points.size()<2)return null;
        for(StationDot s:ss){
            if(s==null||s.stage==null)continue;int rank=v880StageRank(s.stage);if(rank<=0)continue;
            boolean match=false;String sn=v880Norm(s.name);
            if(!rn.isEmpty()&&!sn.isEmpty()&&(rn.contains(sn)||sn.contains(rn)))match=true;
            if(!match&&Double.isFinite(s.lat)&&Double.isFinite(s.lon)){
                double d=v880DistanceToRiverKm(s.lat,s.lon,r); if(Double.isFinite(d)&&d<=2.5)match=true;
            }
            if(match&&rank>best)best=rank;
        }
        return best>=3?"danger":best==2?"warning":best==1?"alert":null;
    } // V0880_HIGHEST_SEVERITY_WINS

    private static int v880StageRank(String s){String x=s==null?"":s.toLowerCase(Locale.ROOT);if(x.contains("danger")||x.contains("red"))return 3;if(x.contains("warning")||x.contains("orange"))return 2;if(x.contains("alert")||x.contains("watch")||x.contains("yellow"))return 1;return 0;}
    private static String v880Norm(String s){if(s==null)return "";return s.toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]","").replace("river","").replace("khola","").replace("nadi","").replace("नदी","").replace("खोला","");}
    private static double v880DistanceToRiverKm(double lat,double lon,RiverWay r){
        double best=Double.POSITIVE_INFINITY, cos=Math.cos(Math.toRadians(lat));
        for(int i=1;i<r.points.size();i++){
            double[] a=r.points.get(i-1),b=r.points.get(i);
            double ax=(a[0]-lon)*111.320*cos, ay=(a[1]-lat)*110.574, bx=(b[0]-lon)*111.320*cos, by=(b[1]-lat)*110.574;
            double dx=bx-ax,dy=by-ay,t=(dx*dx+dy*dy)>0?-(ax*dx+ay*dy)/(dx*dx+dy*dy):0;t=Math.max(0,Math.min(1,t));
            double px=ax+t*dx,py=ay+t*dy,d=Math.sqrt(px*px+py*py);if(d<best)best=d;
        }
        return best;
    }
    private static String v880Esc(String s){return s==null?"":s.replace("\\","\\\\").replace("\"","\\\"");}
    private static String v880RiverFeature(RiverWay r,String stage){
        try{StringBuilder sb=new StringBuilder("{\"type\":\"Feature\",\"properties\":{\"stage\":\"").append(v880Esc(stage)).append("\",\"name\":\"").append(v880Esc(r.name)).append("\"},\"geometry\":{\"type\":\"LineString\",\"coordinates\":[");
            for(int i=0;i<r.points.size();i++){if(i>0)sb.append(',');double[] p=r.points.get(i);sb.append('[').append(p[0]).append(',').append(p[1]).append(']');}
            return sb.append("]}}" ).toString();}catch(Exception e){return null;}
    }

'''
    if helper_anchor not in m:
        raise SystemExit('v0880 helper anchor missing')
    m=m.replace(helper_anchor,helpers+helper_anchor,1)

# Version bump while preserving full packaged v0.8.79 asset pipeline.
g=re.sub(r'versionCode\s+99\b','versionCode 100',g,count=1)
g=g.replace("versionName '0.8.79'","versionName '0.8.80'",1)
if 'versionCode 100' not in g or "versionName '0.8.80'" not in g:
    raise SystemExit('v0880 version bump failed')

need=['V0880_RIVER_STATUS_OVERLAY','V0880_LIVE_RIVER_STATUS_REFRESH','V0880_TILE_SWAP_STATUS_REFRESH','V0880_RIVER_STATUS_OVERLAY_REFRESH','V0880_HIGHEST_SEVERITY_WINS']
for x in need:
    if x not in m: raise SystemExit('missing '+x)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.80 live river status colour patch applied')
