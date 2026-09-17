from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.22 fixes the field screenshots:
# 1) remove the invalid district-hole outside mask that produced the dark diagonal band;
# 2) never publish an entire dense Kathmandu tile at local zoom -- publish every actual
#    waterway intersecting the current visible viewport instead (no arbitrary top-N);
# 3) include precise camera position in the refresh key so panning inside one tile refreshes;
# 4) keep national map clean: normal/stale gauge dots are local-only, severe gauges remain;
# 5) status truth remains same-river official BIPAD/DHM: normal blue, alert yellow,
#    warning orange, danger red. Emergency 2 km + 2-hour weather rules are untouched.

start=m.find('    private void refreshVisibleRiverTiles() {')
end=m.find('    private static double webVisibleScore(',start)
if start<0 or end<0: raise SystemExit('refreshVisibleRiverTiles anchors missing')
new_refresh=r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp = map.getCameraPosition();
        LatLng center = cp.target;
        if(!cameraTargetInsideNepal(center)){map.animateCamera(CameraUpdateFactory.newLatLng(NEPAL_CENTER),250);return;}
        final double zoom=cp.zoom;
        final double cla=center.getLatitude(),clo=center.getLongitude();
        final int cx=Math.max(0,Math.min(11,(int)Math.floor((clo-80.0)/0.7)));
        final int cy=Math.max(0,Math.min(7,(int)Math.floor((cla-26.2)/0.6)));
        final int radius=zoom<8.2?1:0;

        double w=clo-0.35,e=clo+0.35,s=cla-0.30,n=cla+0.30;
        try{
            LatLngBounds vb=map.getProjection().getVisibleRegion().latLngBounds;
            w=vb.getLonWest();e=vb.getLonEast();s=vb.getLatSouth();n=vb.getLatNorth();
        }catch(Exception ignored){}
        double padLon=Math.max(0.012,Math.abs(e-w)*0.22);
        double padLat=Math.max(0.010,Math.abs(n-s)*0.22);
        final double fw=w-padLon,fe=e+padLon,fs=s-padLat,fn=n+padLat;

        // Camera position, not just tile id, is part of the key. This fixes the old bug
        // where panning from another Kathmandu neighbourhood to Dhobi Khola reused stale geometry.
        final String key=zoom<7.0?"national":cx+":"+cy+":"+radius+":"+
                Math.round(cla*200.0)+":"+Math.round(clo*200.0)+":"+Math.round(zoom*4.0);
        if(key.equals(lastRiverTileKey))return;
        lastRiverTileKey=key;final int generation=++riverTileGeneration;

        io.execute(()->{
            try{
                List<RiverWay> chosen=new ArrayList<>();
                if(zoom<7.0){
                    int keep=Math.min(180,overviewRivers.size());
                    chosen.addAll(overviewRivers.subList(0,keep));
                }else{
                    JSONObject districts=districtGeoJson==null?null:new JSONObject(districtGeoJson);
                    List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();
                    for(int x=Math.max(0,cx-radius);x<=Math.min(11,cx+radius);x++)for(int y=Math.max(0,cy-radius);y<=Math.min(7,cy+radius);y++){
                        for(RiverWay r:readRiverTile(x,y,districts)){
                            String k=riverKey(r);if(seen.add(k)&&riverIntersectsBox(r,fw,fs,fe,fn))candidates.add(r);
                        }
                    }
                    // No ranking/top-N here: if a real waterway intersects the visible map,
                    // it is rendered. This keeps Dhobi/Rudramati and other small urban khola visible.
                    chosen.addAll(candidates);
                }
                if(districtGeoJson!=null){
                    try{
                        JSONObject clipRoot=new JSONObject(districtGeoJson);List<RiverWay> clipped=new ArrayList<>();
                        for(RiverWay rr:chosen){trimRiverToNepal(rr,clipRoot);if(rr.points.size()>=2)clipped.add(rr);}chosen=clipped;
                    }catch(Exception ignored){}
                }
                String geo=makeRiversGeoJson(chosen),labels=emptyFeatureCollection();
                final List<RiverWay> publish=new ArrayList<>(chosen);
                main.post(()->{
                    if(generation!=riverTileGeneration)return;
                    rivers.clear();rivers.addAll(publish);riversGeoJson=geo;riverLabelsGeoJson=labels;
                    setGeo("fs-rivers",geo);setGeo("fs-river-labels",labels);refreshRiverStatusSources();
                });
            }catch(Exception ignored){}
        });
    }

    private static boolean riverIntersectsBox(RiverWay r,double west,double south,double east,double north){
        if(r==null||r.points.size()<2)return false;
        for(int i=1;i<r.points.size();i++){
            double[] a=r.points.get(i-1),b=r.points.get(i);
            double minX=Math.min(a[0],b[0]),maxX=Math.max(a[0],b[0]);
            double minY=Math.min(a[1],b[1]),maxY=Math.max(a[1],b[1]);
            if(maxX>=west&&minX<=east&&maxY>=south&&minY<=north)return true;
        }
        return false;
    }

'''
m=m[:start]+new_refresh+m[end:]

# Remove the broken outside-mask installation. Per-river Nepal clipping above is the boundary rule.
mask_block=re.compile(r'''\n\s*if \(districtGeoJson != null && style\.getSource\("fs-nepal-outside-mask"\) == null\) \{\n\s*String mask=makeNepalOutsideMask\(districtGeoJson\);\n\s*style\.addSource\(new GeoJsonSource\("fs-nepal-outside-mask", mask\)\);\n\s*style\.addLayer\(new FillLayer\("fs-nepal-outside-mask-layer", "fs-nepal-outside-mask"\)\.withProperties\(\n\s*fillColor\("#071821"\), fillOpacity\(1\.0f\)\)\);\n\s*\}\n''',re.M)
m,nmask=mask_block.subn('\n            // v0.8.22: no outside fill mask; rivers are clipped to Nepal geometry.\n',m,count=1)
if nmask!=1: raise SystemExit('broken Nepal outside mask install block missing')

# Remove our always-on district text layer; Esri places already supplies readable local labels.
dlabel=re.compile(r'''\n\s*style\.addLayer\(new SymbolLayer\("fs-district-labels", "fs-districts"\)\.withProperties\(\n\s*textField\("\{nameEn\}"\), textSize\(9\.6f\), textColor\("#ffffff"\),\n\s*textHaloColor\("#173646"\), textHaloWidth\(1\.7f\), textAllowOverlap\(true\)\)\);''',re.M)
m,_=dlabel.subn('',m,count=1)

# Clean station dots: national map shows only actual alert/warning/danger; normal dots appear locally.
ss=m.find('    private void refreshStationSources() {')
se=m.find('    private void refreshRainSources() {',ss)
if ss<0 or se<0: raise SystemExit('station source anchors missing')
station_block=r'''    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot; synchronized (stations) { snapshot = new ArrayList<>(stations); }
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        boolean local=zoom>=9.0;
        setGeo("fs-stale", emptyFeatureCollection());
        setGeo("fs-normal", local?stationGeo(snapshot, "normal"):emptyFeatureCollection());
        setGeo("fs-alert", stationGeo(snapshot, "alert"));
        setGeo("fs-warning", stationGeo(snapshot, "warning"));
        setGeo("fs-danger", stationGeo(snapshot, "danger"));
        refreshRiverStatusSources();
        setGeo("fs-station-labels", emptyFeatureCollection());
    }

'''
m=m[:ss]+station_block+m[se:]

# Keep the core river line unmistakable on satellite imagery.
m=re.sub(r'''style\.addLayer\(new LineLayer\("fs-river-glow", "fs-rivers"\)\.withProperties\(.*?\)\);''',
         '''style.addLayer(new LineLayer("fs-river-glow", "fs-rivers").withProperties(\n                        lineColor("#003f55"), lineWidth(5.8f), lineOpacity(0.72f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));''',m,count=1,flags=re.S)
m=re.sub(r'''style\.addLayer\(new LineLayer\("fs-rivers-layer", "fs-rivers"\)\.withProperties\(.*?\)\);''',
         '''style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#18e6ff"), lineWidth(2.45f), lineOpacity(1.0f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));''',m,count=1,flags=re.S)

# Version bump.
if "versionName '0.8.22'" not in g:
    g=g.replace('versionCode 41','versionCode 42',1)
    g=g.replace("versionName '0.8.21'","versionName '0.8.22'",1)
if 'versionCode 42' not in g or "versionName '0.8.22'" not in g: raise SystemExit('v0.8.22 version bump failed')

m_path.write_text(m,encoding='utf-8');a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard gates against the exact field regression.
m2=m_path.read_text(encoding='utf-8')
for marker in [
    'riverIntersectsBox(r,fw,fs,fe,fn)',
    'Math.round(cla*200.0)',
    'chosen.addAll(candidates);',
    'lineColor("#18e6ff")',
    'local?stationGeo(snapshot, "normal"):emptyFeatureCollection()',
    'trimRiverToNepal(rr,clipRoot)',
    'sameRiverGaugeFor',
    'fs-river-warning-status-layer',
    'fs-river-danger-status-layer']:
    if marker not in m2: raise SystemExit('v0.8.22 marker missing: '+marker)
if 'style.addLayer(new FillLayer("fs-nepal-outside-mask-layer"' in m2:
    raise SystemExit('broken outside mask layer still installed')
if 'zoom>=10.0?candidates.size()' in m2:
    raise SystemExit('whole dense tile publish logic remained')
print('FloodSafe v0.8.22 viewport-true rivers + clean Nepal map PASS')
