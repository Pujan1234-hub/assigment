from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.38 real-device fix:
# - v0.8.35 restores a lightweight renderer after replacing the older renderer, so patch the
#   renderer that ACTUALLY ships on the phone.
# - Always retain the complete preclipped Nepal overview as the base network. At local zoom,
#   ADD detailed visible tiles instead of replacing the overview; this prevents blank/missing
#   river regions while panning/zooming.
# - Move the river detail card left of the native +/- control rail and enlarge its X target.
# Official BIPAD/DHM parsing and 2 km Warning/Danger alert logic are untouched.

start=m.find('    private void refreshVisibleRiverTiles(){')
end=m.find('    private void installGeoLayers() {',start)
if start<0 or end<0:
    raise SystemExit('v0.8.38 restored renderer anchors missing')

renderer=r'''    private void refreshVisibleRiverTiles(){
        if(!styleReady||style==null||map==null||overviewRivers.isEmpty())return;
        CameraPosition cp=map.getCameraPosition();final double zoom=cp.zoom;LatLng center=cp.target;
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
        final String key="FULL:"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*250d)+":"+Math.round(center.getLongitude()*250d)+":"+Math.round(zoom*5d);
        if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;

        io.execute(()->{
            try{
                List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();

                // FULL_NEPAL_OVERVIEW: these overview assets were already intersected with the
                // Nepal 77-district union by CI. Keep every real OSM river/stream that touches
                // the visible bounds. No national sampling/count cap and no named-only filter.
                for(RiverWay r:overviewRivers){
                    if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                    if(seen.add(riverKey(r)))candidates.add(r);
                }

                // FULL_NEPAL_DETAIL_MERGE + PRECLIPPED_TILE_ASSET: at closer zoom, add all
                // visible build-time Nepal-clipped tile geometry instead of replacing overview.
                // The overview therefore prevents holes while detailed OSM streams/rivers appear.
                if(zoom>=7.8){
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:v835ReadRiverTile(x,y)){
                            if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                            if(seen.add(riverKey(r)))candidates.add(r);
                        }
                    }
                }
                if(candidates.isEmpty())return;

                // PRECLIPPED_RENDER_DIRECT: v0.8.37 clips overview + every tile at build time,
                // so the phone can publish immediately without an expensive polygon pass.
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

# Keep the detail card clear of the right-side + / - controls.
old_margin='detailLp.setMargins(dp(12),0,dp(12),dp(12));mapHolder.addView(mapDetailPanel,detailLp);'
new_margin='detailLp.setMargins(dp(12),0,dp(78),dp(12));mapDetailPanel.setElevation(dp(14));mapHolder.addView(mapDetailPanel,detailLp);'
if old_margin not in a:
    raise SystemExit('v0.8.38 detail panel margin anchor missing')
a=a.replace(old_margin,new_margin,1)

# Larger X target so it is easy to close on a phone.
old_x='x.setPadding(dp(10),dp(5),dp(4),dp(5));'
new_x='x.setPadding(dp(12),dp(8),dp(10),dp(8));x.setMinWidth(dp(42));x.setMinHeight(dp(42));'
if old_x in a:
    a=a.replace(old_x,new_x,1)
elif 'x.setMinWidth(dp(42))' not in a:
    raise SystemExit('v0.8.38 close X padding anchor missing')

# Version bump.
g=g.replace('versionCode 57','versionCode 58',1).replace("versionName '0.8.37'","versionName '0.8.38'",1)
if 'versionCode 58' not in g or "versionName '0.8.38'" not in g:
    raise SystemExit('v0.8.38 version bump failed')

for marker in [
    'FULL_NEPAL_OVERVIEW',
    'FULL_NEPAL_DETAIL_MERGE',
    'PRECLIPPED_RENDER_DIRECT',
    'for(RiverWay r:overviewRivers)',
    'for(RiverWay r:v835ReadRiverTile(x,y))',
    'detailLp.setMargins(dp(12),0,dp(78),dp(12))',
    'mapDetailPanel.setElevation(dp(14))',
    'x.setMinWidth(dp(42))',
    'PRECLIPPED_BUILD_ASSET',
    'PRECLIPPED_TILE_ASSET']:
    hay=m if marker in ['FULL_NEPAL_OVERVIEW','FULL_NEPAL_DETAIL_MERGE','PRECLIPPED_RENDER_DIRECT','for(RiverWay r:overviewRivers)','for(RiverWay r:v835ReadRiverTile(x,y))','PRECLIPPED_BUILD_ASSET','PRECLIPPED_TILE_ASSET'] else a
    if marker not in hay: raise SystemExit('v0.8.38 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.38 COMPLETE Nepal overview + merged detail + clear close X PASS')
