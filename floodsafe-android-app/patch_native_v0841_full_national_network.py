from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.41: eliminate overview-sampling holes completely at whole-Nepal/regional zoom.
# The build creates one compact MultiLineString from EVERY Nepal-clipped OSM waterway.
# Android loads that raw GeoJSON directly for zoom < 6.65, avoiding thousands of Feature
# objects and avoiding any async regional-tile race. At closer zoom we keep the proven
# visible regional + dense tile renderer. Official BIPAD/DHM status and alert safety are untouched.

field='    private String riversGeoJson = null;'
if field not in m:
    raise SystemExit('v0.8.41 riversGeoJson field missing')
if 'nationalRiversGeoJson' not in m:
    m=m.replace(field, field+'\n    private String nationalRiversGeoJson = null;',1)

old='''                rivers.clear();rivers.addAll(safeAll);\n                overviewRivers.clear();overviewRivers.addAll(safeAll);\n                riversGeoJson=makeRiversGeoJson(safeAll);\n                riverLabelsGeoJson=emptyFeatureCollection();'''
new='''                rivers.clear();rivers.addAll(safeAll);\n                overviewRivers.clear();overviewRivers.addAll(safeAll);\n                String overviewGeo=makeRiversGeoJson(safeAll);\n                try{\n                    nationalRiversGeoJson=readAsset("data/nepal-waterways-national-v0841.geojson");\n                    if(nationalRiversGeoJson==null||nationalRiversGeoJson.length()<1000)nationalRiversGeoJson=null;\n                }catch(Exception ignoredNational){nationalRiversGeoJson=null;}\n                riversGeoJson=nationalRiversGeoJson!=null?nationalRiversGeoJson:overviewGeo;\n                riverLabelsGeoJson=emptyFeatureCollection();'''
if old in m:
    m=m.replace(old,new,1)
elif 'nepal-waterways-national-v0841.geojson' not in m:
    raise SystemExit('v0.8.41 startup publication anchor missing')

start=m.find('    private void refreshVisibleRiverTiles(){')
end=m.find('    private void installGeoLayers() {',start)
if start<0 or end<0:
    raise SystemExit('v0.8.41 renderer anchors missing')

renderer=r'''    private void refreshVisibleRiverTiles(){
        if(!styleReady||style==null||map==null||overviewRivers.isEmpty())return;
        CameraPosition cp=map.getCameraPosition();final double zoom=cp.zoom;LatLng center=cp.target;

        // V0841_FULL_NATIONAL_SOURCE: whole-Nepal and normal regional zoom always use
        // ONE raw MultiLineString containing every build-time Nepal-clipped OSM waterway.
        // No ranking, no overview sampling, no missing Far West/Far East, and no repeated
        // JSON reconstruction while the user pans. Dense local detail still takes over below.
        if(zoom<6.65&&nationalRiversGeoJson!=null&&nationalRiversGeoJson.length()>1000){
            final String key="V841N:"+Math.round(zoom*5d);
            if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;
            final String national=nationalRiversGeoJson;
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                rivers.clear();rivers.addAll(overviewRivers);
                riversGeoJson=national;
                setGeo("fs-rivers",national);
                setGeo("fs-river-labels",emptyFeatureCollection());
                refreshRiverStatusSources();
            });
            return;
        }

        double west=center.getLongitude()-0.7,east=center.getLongitude()+0.7;
        double south=center.getLatitude()-0.5,north=center.getLatitude()+0.5;
        try{
            LatLngBounds vb=map.getProjection().getVisibleRegion().latLngBounds;
            west=vb.getLonWest();east=vb.getLonEast();south=vb.getLatSouth();north=vb.getLatNorth();
        }catch(Exception ignored){}
        if(east<west){double t=west;west=east;east=t;}if(north<south){double t=south;south=north;north=t;}
        double padLon=Math.max(0.012,(east-west)*0.14),padLat=Math.max(0.012,(north-south)*0.14);
        final double fw=Math.max(79.95,west-padLon),fe=Math.min(88.35,east+padLon);
        final double fs=Math.max(26.15,south-padLat),fn=Math.min(30.60,north+padLat);
        final int minX=Math.max(0,Math.min(11,(int)Math.floor((fw-80.0)/0.7)));
        final int maxX=Math.max(0,Math.min(11,(int)Math.floor((fe-80.0)/0.7)));
        final int minY=Math.max(0,Math.min(7,(int)Math.floor((fs-26.2)/0.6)));
        final int maxY=Math.max(0,Math.min(7,(int)Math.floor((fn-26.2)/0.6)));
        final String key="V841L:"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*250d)+":"+Math.round(center.getLongitude()*250d)+":"+Math.round(zoom*5d);
        if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;

        io.execute(()->{
            try{
                List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();

                // Keep overview context so no temporary hole appears during local tile loading.
                for(RiverWay r:overviewRivers){
                    if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                    if(seen.add(riverKey(r)))candidates.add(r);
                }

                // Normal regional/local zoom: lightweight visible OSM tile set.
                for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                    for(RiverWay r:v840ReadRegionalTile(x,y)){
                        if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                        if(seen.add(riverKey(r)))candidates.add(r);
                    }
                }

                // Close zoom: every exact preclipped OSM waterway in visible tiles.
                if(zoom>=8.0){
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:v835ReadRiverTile(x,y)){
                            if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                            if(seen.add(riverKey(r)))candidates.add(r);
                        }
                    }
                }
                if(candidates.isEmpty())return;

                final String geo=makeRiversGeoJson(candidates);final List<RiverWay> publish=new ArrayList<>(candidates);
                main.post(()->{
                    if(!key.equals(lastRiverTileKey))return;
                    rivers.clear();rivers.addAll(publish);riversGeoJson=geo;riverLabelsGeoJson=emptyFeatureCollection();
                    setGeo("fs-rivers",geo);setGeo("fs-river-labels",emptyFeatureCollection());
                    refreshRiverStatusSources();
                });
            }catch(Exception ignored){}
        });
    }

'''
m=m[:start]+renderer+m[end:]

# Version bump.
g=g.replace('versionCode 60','versionCode 61',1).replace("versionName '0.8.40'","versionName '0.8.41'",1)
if 'versionCode 61' not in g or "versionName '0.8.41'" not in g:
    raise SystemExit('v0.8.41 version bump failed')

for marker in [
    'nationalRiversGeoJson',
    'data/nepal-waterways-national-v0841.geojson',
    'V0841_FULL_NATIONAL_SOURCE',
    'if(zoom<6.65',
    'v840ReadRegionalTile(x,y)',
    'v835ReadRiverTile(x,y)',
    'setGeo("fs-rivers",national)',
    'lineColor("#22D7FF")',
    'lineColor("#087CFF")']:
    if marker not in m: raise SystemExit('v0.8.41 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.41 FULL national MultiLineString + local detail PASS')
