from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.42: user-confirmed correction after v0.8.41 proved full geographic coverage.
# v0.8.41 intentionally drew all 54k waterways at Nepal-wide zoom to prove Far West/East
# were present, but that made the map unreadable. Restore the intended progressive UX:
# major network at whole-Nepal zoom -> medium network -> visible regional network -> exact
# local network. Far West/East coverage stays spatially balanced in every national tier.

field='    private String nationalRiversGeoJson = null;'
if field not in m:
    raise SystemExit('v0.8.42 national field missing')
if 'majorRiversGeoJson' not in m:
    m=m.replace(field,field+'\n    private String majorRiversGeoJson = null;\n    private String mediumRiversGeoJson = null;',1)

old='''                try{\n                    nationalRiversGeoJson=readAsset("data/nepal-waterways-national-v0841.geojson");\n                    if(nationalRiversGeoJson==null||nationalRiversGeoJson.length()<1000)nationalRiversGeoJson=null;\n                }catch(Exception ignoredNational){nationalRiversGeoJson=null;}\n                riversGeoJson=nationalRiversGeoJson!=null?nationalRiversGeoJson:overviewGeo;'''
new='''                try{\n                    nationalRiversGeoJson=readAsset("data/nepal-waterways-national-v0841.geojson");\n                    if(nationalRiversGeoJson==null||nationalRiversGeoJson.length()<1000)nationalRiversGeoJson=null;\n                }catch(Exception ignoredNational){nationalRiversGeoJson=null;}\n                try{\n                    majorRiversGeoJson=readAsset("data/nepal-waterways-major-v0842.geojson");\n                    if(majorRiversGeoJson==null||majorRiversGeoJson.length()<1000)majorRiversGeoJson=null;\n                }catch(Exception ignoredMajor){majorRiversGeoJson=null;}\n                try{\n                    mediumRiversGeoJson=readAsset("data/nepal-waterways-medium-v0842.geojson");\n                    if(mediumRiversGeoJson==null||mediumRiversGeoJson.length()<1000)mediumRiversGeoJson=null;\n                }catch(Exception ignoredMedium){mediumRiversGeoJson=null;}\n                riversGeoJson=majorRiversGeoJson!=null?majorRiversGeoJson:(mediumRiversGeoJson!=null?mediumRiversGeoJson:(nationalRiversGeoJson!=null?nationalRiversGeoJson:overviewGeo));'''
if old in m:
    m=m.replace(old,new,1)
elif 'nepal-waterways-major-v0842.geojson' not in m:
    raise SystemExit('v0.8.42 startup tier load anchor missing')

start=m.find('    private void refreshVisibleRiverTiles(){')
end=m.find('    private void installGeoLayers() {',start)
if start<0 or end<0:
    raise SystemExit('v0.8.42 renderer anchors missing')

renderer=r'''    private void refreshVisibleRiverTiles(){
        if(!styleReady||style==null||map==null||overviewRivers.isEmpty())return;
        CameraPosition cp=map.getCameraPosition();final double zoom=cp.zoom;LatLng center=cp.target;

        // V0842_PROGRESSIVE_ZOOM: clear Nepal-wide view first; reveal more real waterways
        // only as the user zooms in. Both national tiers are spatially balanced so western
        // and eastern Nepal never disappear again.
        String tier=null;String tierName="";
        if(zoom<5.75){
            tier=majorRiversGeoJson!=null?majorRiversGeoJson:mediumRiversGeoJson;tierName="MAJOR";
        }else if(zoom<6.65){
            tier=mediumRiversGeoJson!=null?mediumRiversGeoJson:majorRiversGeoJson;tierName="MEDIUM";
        }
        if(tier!=null&&tier.length()>1000){
            final String key="V842"+tierName+":"+Math.round(zoom*10d);
            if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;
            final String publishTier=tier;
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                riversGeoJson=publishTier;
                setGeo("fs-rivers",publishTier);
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
        final String key="V842LOCAL:"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*250d)+":"+Math.round(center.getLongitude()*250d)+":"+Math.round(zoom*5d);
        if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;

        io.execute(()->{
            try{
                List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();

                // Regional zoom: only visible balanced OSM tiles. Do not merge the entire
                // national overview here; that was the source of the blue wall effect.
                for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                    for(RiverWay r:v840ReadRegionalTile(x,y)){
                        if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                        if(seen.add(riverKey(r)))candidates.add(r);
                    }
                }

                // Close zoom: add every exact preclipped OSM waterway only for visible tiles.
                if(zoom>=8.20){
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:v835ReadRiverTile(x,y)){
                            if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                            if(seen.add(riverKey(r)))candidates.add(r);
                        }
                    }
                }

                // Asset failure fallback: use only overview lines intersecting this viewport.
                if(candidates.isEmpty())for(RiverWay r:overviewRivers){
                    if(r!=null&&r.points.size()>=2&&v835Intersects(r,fw,fs,fe,fn)&&seen.add(riverKey(r)))candidates.add(r);
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

# The map should remain readable over satellite imagery. v0.8.41 used thick glow because
# it was proving coverage. Keep the same cyan/blue identity but make the geographic network
# thin; official warning/danger status overlays remain stronger and unchanged.
repls=[
    ('lineColor("#22D7FF"), lineWidth(2.45f), lineOpacity(1.0f)',
     'lineColor("#22D7FF"), lineWidth(1.25f), lineOpacity(0.92f)'),
    ('lineColor("#087CFF"), lineWidth(6.4f), lineOpacity(0.42f)',
     'lineColor("#087CFF"), lineWidth(3.2f), lineOpacity(0.25f)'),
    ('lineWidth((float)(5.3+1.9*wave))','lineWidth((float)(2.9+0.7*wave))'),
    ('lineWidth((float)(2.15+0.50*wave))','lineWidth((float)(1.15+0.22*wave))')]
for a,b in repls:
    if a in m:m=m.replace(a,b,1)

# Version bump.
g=g.replace('versionCode 61','versionCode 62',1).replace("versionName '0.8.41'","versionName '0.8.42'",1)
if 'versionCode 62' not in g or "versionName '0.8.42'" not in g:
    raise SystemExit('v0.8.42 version bump failed')

for marker in [
    'majorRiversGeoJson','mediumRiversGeoJson',
    'data/nepal-waterways-major-v0842.geojson','data/nepal-waterways-medium-v0842.geojson',
    'V0842_PROGRESSIVE_ZOOM','if(zoom<5.75)','else if(zoom<6.65)','if(zoom>=8.20)',
    'v840ReadRegionalTile(x,y)','v835ReadRiverTile(x,y)',
    'lineWidth(1.25f)','lineWidth(3.2f)','lineWidth((float)(2.9+0.7*wave))','lineWidth((float)(1.15+0.22*wave))']:
    if marker not in m: raise SystemExit('v0.8.42 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.42 progressive zoom rivers + thin national map PASS')
