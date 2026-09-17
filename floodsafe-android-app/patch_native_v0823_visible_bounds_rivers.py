from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.23: field fix for the user's Kathmandu/Dhobi screenshots.
# Source-of-truth contract:
# - Geometry: bundled OpenStreetMap waterway coordinates (exact polyline points).
# - Status: latest BIPAD/DHM river gauge feed only.
# - At local zoom, publish ONLY waterways from tiles intersecting the actual visible bounds.
# - Never retain the national overview as a local substitute.
# - Keep exact local geometry untouched when the whole viewport is inside Nepal.
# - Near the border / national view, split geometry by the Nepal district-union polygon
#   instead of the old black outside mask.

start=m.find('    private void refreshVisibleRiverTiles() {')
end=m.find('    private static double webVisibleScore(',start)
if start<0 or end<0:
    raise SystemExit('refreshVisibleRiverTiles anchors missing')

new_block=r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp = map.getCameraPosition();
        final double zoom = cp.zoom;
        final LatLng center = cp.target;
        if(!cameraTargetInsideNepal(center)){map.animateCamera(CameraUpdateFactory.newLatLng(NEPAL_CENTER),250);return;}

        double west=center.getLongitude()-0.40,east=center.getLongitude()+0.40;
        double south=center.getLatitude()-0.32,north=center.getLatitude()+0.32;
        try{
            LatLngBounds vb=map.getProjection().getVisibleRegion().latLngBounds;
            west=vb.getLonWest(); east=vb.getLonEast(); south=vb.getLatSouth(); north=vb.getLatNorth();
        }catch(Exception ignored){}
        if(east<west){double t=west;west=east;east=t;}
        if(north<south){double t=south;south=north;north=t;}
        double padLon=Math.max(0.006,(east-west)*0.08);
        double padLat=Math.max(0.006,(north-south)*0.08);
        final double fw=Math.max(79.95,west-padLon), fe=Math.min(88.30,east+padLon);
        final double fs=Math.max(26.25,south-padLat), fn=Math.min(30.55,north+padLat);

        final int minX=Math.max(0,Math.min(11,(int)Math.floor((fw-80.0)/0.7)));
        final int maxX=Math.max(0,Math.min(11,(int)Math.floor((fe-80.0)/0.7)));
        final int minY=Math.max(0,Math.min(7,(int)Math.floor((fs-26.2)/0.6)));
        final int maxY=Math.max(0,Math.min(7,(int)Math.floor((fn-26.2)/0.6)));
        final String key=(zoom<7.7?"national":"local")+":"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*400.0)+":"+Math.round(center.getLongitude()*400.0)+":"+Math.round(zoom*8.0);
        if(key.equals(lastRiverTileKey))return;
        lastRiverTileKey=key;
        final int generation=++riverTileGeneration;

        io.execute(()->{
            try{
                JSONObject nepal=districtGeoJson==null?null:new JSONObject(districtGeoJson);
                final boolean local=zoom>=7.7;
                final boolean fullyInside=local&&viewportFullyInsideNepal(fw,fs,fe,fn,nepal);
                List<RiverWay> candidates=new ArrayList<>();
                java.util.HashSet<String> seen=new java.util.HashSet<>();

                if(local){
                    // Read every custom data tile touched by the real screen bounds.
                    // This fixes the old center-tile/radius guess which could show a wrong/empty river set.
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:readRiverTile(x,y,null)){
                            if(r==null||r.points.size()<2||!riverIntersectsBox(r,fw,fs,fe,fn))continue;
                            // Mid zoom: keep rivers and named streams. Close zoom: every real OSM waterway.
                            if(zoom<9.0 && !"river".equalsIgnoreCase(r.type) && (r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name)))continue;
                            String k=riverKey(r); if(seen.add(k))candidates.add(r);
                        }
                    }
                }else{
                    // National view is context, not a spaghetti plot: real named rivers only.
                    for(RiverWay r:overviewRivers){
                        if(r==null||r.points.size()<2||!"river".equalsIgnoreCase(r.type))continue;
                        if(r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name))continue;
                        if(!riverIntersectsBox(r,fw,fs,fe,fn))continue;
                        String k=riverKey(r); if(seen.add(k))candidates.add(copyRiver(r));
                        if(candidates.size()>=320)break;
                    }
                }

                List<RiverWay> chosen;
                if(fullyInside || nepal==null){
                    // Kathmandu/Dhobi and other interior views keep OSM coordinates byte-for-byte exact.
                    chosen=candidates;
                }else{
                    chosen=splitWaysToNepal(candidates,nepal);
                }

                String geo=makeRiversGeoJson(chosen);
                final List<RiverWay> publish=new ArrayList<>(chosen);
                main.post(()->{
                    if(generation!=riverTileGeneration)return;
                    rivers.clear();rivers.addAll(publish);
                    riversGeoJson=geo;riverLabelsGeoJson=emptyFeatureCollection();
                    setGeo("fs-rivers",geo);setGeo("fs-river-labels",riverLabelsGeoJson);
                    refreshRiverStatusSources();
                });
            }catch(Exception ignored){}
        });
    }

    private static RiverWay copyRiver(RiverWay src){
        RiverWay r=new RiverWay();r.name=src.name;r.type=src.type;
        for(double[] p:src.points)r.points.add(new double[]{p[0],p[1]});
        return r;
    }

    private static boolean viewportFullyInsideNepal(double west,double south,double east,double north,JSONObject root){
        if(root==null)return false;
        try{
            double cx=(west+east)*0.5,cy=(south+north)*0.5;
            return insideNepalSoft(west,south,root)&&insideNepalSoft(west,north,root)&&
                   insideNepalSoft(east,south,root)&&insideNepalSoft(east,north,root)&&insideNepalSoft(cx,cy,root);
        }catch(Exception e){return false;}
    }

    private static List<RiverWay> splitWaysToNepal(List<RiverWay> ways,JSONObject root){
        List<RiverWay> out=new ArrayList<>();
        if(root==null){out.addAll(ways);return out;}
        for(RiverWay src:ways){
            RiverWay cur=null;
            for(double[] p:src.points){
                boolean inside=false;try{inside=insideNepalSoft(p[0],p[1],root);}catch(Exception ignored){}
                if(inside){
                    if(cur==null){cur=new RiverWay();cur.name=src.name;cur.type=src.type;}
                    cur.points.add(new double[]{p[0],p[1]});
                }else if(cur!=null){
                    if(cur.points.size()>=2)out.add(cur);cur=null;
                }
            }
            if(cur!=null&&cur.points.size()>=2)out.add(cur);
        }
        return out;
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
m=m[:start]+new_block+m[end:]

# Make the static geometry clear but not so thick that it hides the satellite channel.
m=re.sub(r'lineColor\("#18e6ff"\), lineWidth\(3\.2f\), lineOpacity\(1\.0f\)',
         'lineColor("#1edcff"), lineWidth(2.35f), lineOpacity(0.98f)',m,count=1)
m=re.sub(r'lineColor\("#003f55"\), lineWidth\(7\.0f\), lineOpacity\(0\.88f\)',
         'lineColor("#003f55"), lineWidth(5.2f), lineOpacity(0.72f)',m,count=1)

# Re-assert the camera-idle refresh in case an earlier patch chain changes around it.
if 'map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);' not in m:
    anchor='map.addOnMapClickListener(this::onMapClick);'
    if anchor not in m: raise SystemExit('camera listener anchor missing')
    m=m.replace(anchor,anchor+'\n            map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);',1)

if "versionName '0.8.23'" not in g:
    g=g.replace('versionCode 42','versionCode 43',1)
    g=g.replace("versionName '0.8.22'","versionName '0.8.23'",1)
if 'versionCode 43' not in g or "versionName '0.8.23'" not in g:
    raise SystemExit('v0.8.23 version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

m2=m_path.read_text(encoding='utf-8')
for marker in [
    'viewportFullyInsideNepal','splitWaysToNepal','for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++)',
    'readRiverTile(x,y,null)','riverIntersectsBox(r,fw,fs,fe,fn)','map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);',
    'lineColor("#1edcff"), lineWidth(2.35f)','sameRiverGaugeFor','fs-river-warning-status-layer','fs-river-danger-status-layer']:
    if marker not in m2: raise SystemExit('v0.8.23 marker missing: '+marker)
if 'final int radius=zoom<8.2?1:0;' in m2: raise SystemExit('old center-tile radius selector remained')
if 'style.addLayer(new FillLayer("fs-nepal-outside-mask-layer"' in m2: raise SystemExit('broken black outside mask returned')
print('FloodSafe v0.8.23 visible-bounds exact river geometry PASS')
