from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.40 real-phone root fix:
# v0.8.39 improved overview selection, but the user's screenshot zoom is still below the
# dense-tile threshold. That means the phone keeps drawing only an overview sample there.
# Add a second lightweight regional tile set that is spatially balanced per source tile.
# It is used from normal regional zoom, only for visible tiles, and cached in memory.
# Full dense source tiles remain reserved for close zoom, so map movement stays light.
# Official BIPAD/DHM values and alert/notification safety are unchanged.

start=m.find('    private void refreshVisibleRiverTiles(){')
end=m.find('    private void installGeoLayers() {',start)
if start<0 or end<0:
    raise SystemExit('v0.8.40 renderer anchors missing')

renderer=r'''    // V0840_LIGHT_REGIONAL_CACHE: real OSM geometry, already Nepal-clipped at build time.
    private final java.util.Map<String,List<RiverWay>> v840RegionalCache=new java.util.HashMap<>();

    private List<RiverWay> v840ReadRegionalTile(int x,int y){
        String k=x+"-"+y;List<RiverWay> cached=v840RegionalCache.get(k);if(cached!=null)return cached;
        List<RiverWay> out=new ArrayList<>();
        try{
            JSONObject root=new JSONObject(readAsset("data/nepal-waterways-tiles-regional/"+k+".json"));
            JSONArray ways=root.optJSONArray("waterways");
            if(ways!=null)for(int i=0;i<ways.length();i++){
                JSONObject w=ways.optJSONObject(i);if(w==null)continue;JSONArray pts=w.optJSONArray("pts");
                if(pts==null||pts.length()<2)continue;
                RiverWay rw=new RiverWay();
                rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");
                rw.matchName=rw.name;rw.type=w.optString("type","stream");
                for(int j=0;j<pts.length();j++){
                    JSONArray p=pts.optJSONArray(j);if(p==null||p.length()<2)continue;
                    double lo=p.optDouble(0,Double.NaN),la=p.optDouble(1,Double.NaN);
                    if(Double.isFinite(lo)&&Double.isFinite(la)&&isNepalish(la,lo))rw.points.add(new double[]{lo,la});
                }
                if(rw.points.size()>=2)out.add(rw);
            }
        }catch(Exception ignored){}
        v840RegionalCache.put(k,out);return out;
    }

    private void refreshVisibleRiverTiles(){
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
        final String key="V840:"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*250d)+":"+Math.round(center.getLongitude()*250d)+":"+Math.round(zoom*5d);
        if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;

        io.execute(()->{
            try{
                List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();

                // Keep the small national overview as instant fallback/context.
                for(RiverWay r:overviewRivers){
                    if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                    if(seen.add(riverKey(r)))candidates.add(r);
                }

                // V0840_REGIONAL_EDGE_TILES: this is the missing layer in v0.8.39.
                // At normal phone/regional zoom, merge evenly sampled REAL OSM waterways from
                // only the visible local tile files. Far-west/far-east no longer depend on a
                // single national overview sample, while each tile stays capped for performance.
                if(zoom>=5.0){
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:v840ReadRegionalTile(x,y)){
                            if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                            if(seen.add(riverKey(r)))candidates.add(r);
                        }
                    }
                }

                // Close zoom still receives every real preclipped OSM waterway in visible tiles.
                if(zoom>=8.0){ // V0840_FULL_DETAIL_CLOSE_ONLY
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

# Keep previous detail-card/X phone fixes.
for marker in ['detailLp.setMargins(dp(12),0,dp(78),dp(12))','mapDetailPanel.setElevation(dp(14))','x.setMinWidth(dp(42))','x.setMinHeight(dp(42))']:
    if marker not in a: raise SystemExit('v0.8.40 popup fix regressed: '+marker)

# Version bump.
g=g.replace('versionCode 59','versionCode 60',1).replace("versionName '0.8.39'","versionName '0.8.40'",1)
if 'versionCode 60' not in g or "versionName '0.8.40'" not in g:
    raise SystemExit('v0.8.40 version bump failed')

for marker in [
    'V0840_LIGHT_REGIONAL_CACHE',
    'data/nepal-waterways-tiles-regional/',
    'V0840_REGIONAL_EDGE_TILES',
    'if(zoom>=5.0)',
    'V0840_FULL_DETAIL_CLOSE_ONLY',
    'v840ReadRegionalTile(x,y)',
    'v835ReadRiverTile(x,y)',
    'PRECLIPPED_BUILD_ASSET',
    'lineColor("#22D7FF")',
    'lineColor("#087CFF")']:
    if marker not in m: raise SystemExit('v0.8.40 marker missing: '+marker)

# Safety remains exactly from previous native pipeline.
for marker in ['bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))']:
    if marker not in a: raise SystemExit('v0.8.40 alert safety changed: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.40 visible lightweight regional edge rivers PASS')
