from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

# v0.8.35 helper restore.
# The v0.8.35 fast-loader replacement deliberately bypassed the huge startup snapshot,
# but an old broad replacement boundary also removed the viewport renderer/helper block.
# Restore it explicitly here so real devices receive actual river GeoJSON, not just gauge dots.

anchor='    private void installGeoLayers() {'
if anchor not in m:
    raise SystemExit('v0.8.35 helper insert anchor missing')

helpers=r'''    // v0.8.35 RESTORED DEVICE RENDERER -------------------------------------------------
    private static String riverKey(RiverWay r){
        if(r==null)return "";
        String n=riverNameKey(r.matchName);if(n==null||n.isEmpty())n=riverNameKey(r.name);if(n==null)n="";
        if(r.points.isEmpty())return n;
        double[]a=r.points.get(0),b=r.points.get(r.points.size()-1);
        return n+"@"+Math.round(a[0]*10000d)+":"+Math.round(a[1]*10000d)+"-"+
                Math.round(b[0]*10000d)+":"+Math.round(b[1]*10000d);
    }

    private static boolean v835PointInRing(double lon,double lat,JSONArray ring){
        if(ring==null||ring.length()<4)return false;
        boolean inside=false;int n=ring.length();
        for(int i=0,j=n-1;i<n;j=i++){
            JSONArray pi=ring.optJSONArray(i),pj=ring.optJSONArray(j);
            if(pi==null||pj==null||pi.length()<2||pj.length()<2)continue;
            double xi=pi.optDouble(0,Double.NaN),yi=pi.optDouble(1,Double.NaN);
            double xj=pj.optDouble(0,Double.NaN),yj=pj.optDouble(1,Double.NaN);
            if(!Double.isFinite(xi)||!Double.isFinite(yi)||!Double.isFinite(xj)||!Double.isFinite(yj))continue;
            double den=(yj-yi)==0?1e-15:(yj-yi);
            boolean cross=((yi>lat)!=(yj>lat))&&(lon<(xj-xi)*(lat-yi)/den+xi);
            if(cross)inside=!inside;
        }
        return inside;
    }

    private static boolean v835InsidePolygon(double lon,double lat,JSONArray polygon){
        if(polygon==null||polygon.length()==0)return false;
        if(!v835PointInRing(lon,lat,polygon.optJSONArray(0)))return false;
        for(int i=1;i<polygon.length();i++)if(v835PointInRing(lon,lat,polygon.optJSONArray(i)))return false;
        return true;
    }

    private static boolean v835InsideNepal(double lon,double lat,JSONObject root){
        if(root==null||lon<79.8||lon>88.5||lat<26.0||lat>30.7)return false;
        JSONArray fs=root.optJSONArray("features");if(fs==null)return false;
        for(int i=0;i<fs.length();i++){
            JSONObject f=fs.optJSONObject(i),geom=f==null?null:f.optJSONObject("geometry");if(geom==null)continue;
            JSONArray c=geom.optJSONArray("coordinates");if(c==null)continue;String type=geom.optString("type","");
            if("Polygon".equals(type)){
                if(v835InsidePolygon(lon,lat,c))return true;
            }else if("MultiPolygon".equals(type)){
                for(int p=0;p<c.length();p++)if(v835InsidePolygon(lon,lat,c.optJSONArray(p)))return true;
            }
        }
        return false;
    }

    private static List<RiverWay> clipWaysToNepalDense(List<RiverWay> ways,JSONObject nepal){
        List<RiverWay> out=new ArrayList<>();if(ways==null||nepal==null)return out;
        for(RiverWay src:ways){
            if(src==null||src.points.size()<2)continue;
            RiverWay cur=null;
            for(int i=1;i<src.points.size();i++){
                double[]a=src.points.get(i-1),b=src.points.get(i);
                // OSM waterway vertices are already dense. Add intermediate checks on long segments
                // so no visible line can cut across a Nepal border between two source vertices.
                double segKm=Math.max(0.001,km(a[1],a[0],b[1],b[0]));
                int steps=Math.max(1,Math.min(80,(int)Math.ceil(segKm/0.55)));
                for(int s=(i==1?0:1);s<=steps;s++){
                    double f=s/(double)steps,lo=a[0]+(b[0]-a[0])*f,la=a[1]+(b[1]-a[1])*f;
                    if(v835InsideNepal(lo,la,nepal)){
                        if(cur==null){cur=new RiverWay();cur.name=src.name;cur.matchName=src.matchName;cur.type=src.type;}
                        cur.points.add(new double[]{lo,la});
                    }else if(cur!=null){if(cur.points.size()>=2)out.add(cur);cur=null;}
                }
            }
            if(cur!=null&&cur.points.size()>=2)out.add(cur);
        }
        return out;
    }

    private static boolean v835Intersects(RiverWay r,double west,double south,double east,double north){
        if(r==null||r.points.size()<2)return false;
        for(int i=1;i<r.points.size();i++){
            double[]a=r.points.get(i-1),b=r.points.get(i);
            if(Math.max(a[0],b[0])>=west&&Math.min(a[0],b[0])<=east&&
               Math.max(a[1],b[1])>=south&&Math.min(a[1],b[1])<=north)return true;
        }
        return false;
    }

    private List<RiverWay> v835ReadRiverTile(int x,int y){
        List<RiverWay> out=new ArrayList<>();
        try{
            JSONObject root=new JSONObject(readAsset("data/nepal-waterways-tiles/"+x+"-"+y+".json"));
            JSONArray ways=root.optJSONArray("waterways");if(ways==null)return out;
            for(int i=0;i<ways.length();i++){
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
        return out;
    }

    private void refreshVisibleRiverTiles(){
        if(!styleReady||style==null||map==null||overviewRivers.isEmpty())return;
        if(districtGeoJson==null||districtGeoJson.trim().isEmpty())return;
        CameraPosition cp=map.getCameraPosition();final double zoom=cp.zoom;LatLng center=cp.target;
        double west=center.getLongitude()-0.7,east=center.getLongitude()+0.7;
        double south=center.getLatitude()-0.5,north=center.getLatitude()+0.5;
        try{
            LatLngBounds vb=map.getProjection().getVisibleRegion().latLngBounds;
            west=vb.getLonWest();east=vb.getLonEast();south=vb.getLatSouth();north=vb.getLatNorth();
        }catch(Exception ignored){}
        if(east<west){double t=west;west=east;east=t;}if(north<south){double t=south;south=north;north=t;}
        double padLon=Math.max(0.01,(east-west)*0.12),padLat=Math.max(0.01,(north-south)*0.12);
        final double fw=Math.max(79.95,west-padLon),fe=Math.min(88.35,east+padLon);
        final double fs=Math.max(26.15,south-padLat),fn=Math.min(30.60,north+padLat);
        final int minX=Math.max(0,Math.min(11,(int)Math.floor((fw-80.0)/0.7)));
        final int maxX=Math.max(0,Math.min(11,(int)Math.floor((fe-80.0)/0.7)));
        final int minY=Math.max(0,Math.min(7,(int)Math.floor((fs-26.2)/0.6)));
        final int maxY=Math.max(0,Math.min(7,(int)Math.floor((fn-26.2)/0.6)));
        final String key=(zoom<7.15?"N":"L")+":"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*250d)+":"+Math.round(center.getLongitude()*250d)+":"+Math.round(zoom*5d);
        if(key.equals(lastRiverTileKey))return;lastRiverTileKey=key;

        io.execute(()->{
            try{
                JSONObject nepal=new JSONObject(districtGeoJson);
                List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();
                if(zoom<7.15){
                    // National view: show the complete prepared Nepal overview immediately.
                    for(RiverWay r:overviewRivers){
                        if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                        if(seen.add(riverKey(r)))candidates.add(r);
                    }
                }else{
                    // Local view: switch to all real OSM rivers/streams from the visible small tiles.
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:v835ReadRiverTile(x,y)){
                            if(r==null||r.points.size()<2||!v835Intersects(r,fw,fs,fe,fn))continue;
                            if(seen.add(riverKey(r)))candidates.add(r);
                        }
                    }
                    // Never blank the map if a tile is temporarily unavailable.
                    if(candidates.isEmpty())for(RiverWay r:overviewRivers){
                        if(r!=null&&r.points.size()>=2&&v835Intersects(r,fw,fs,fe,fn)&&seen.add(riverKey(r)))candidates.add(r);
                    }
                }
                List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);
                if(chosen.isEmpty())return;
                final String geo=makeRiversGeoJson(chosen);final List<RiverWay> publish=new ArrayList<>(chosen);
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

if 'private void refreshVisibleRiverTiles(){' not in m:
    m=m.replace(anchor,helpers+anchor,1)
else:
    # If another future patch has already restored the renderer, do not create duplicates.
    required=['private static String riverKey(RiverWay r)','private static List<RiverWay> clipWaysToNepalDense']
    for marker in required:
        if marker not in m: raise SystemExit('v0.8.35 partial helper state: '+marker)

for marker in [
    'private void refreshVisibleRiverTiles(){',
    'v835ReadRiverTile',
    'data/nepal-waterways-tiles/"+x+"-"+y+".json',
    'private static List<RiverWay> clipWaysToNepalDense',
    'private static String riverKey(RiverWay r)',
    'setGeo("fs-rivers",geo)',
    'refreshRiverStatusSources()']:
    if marker not in m: raise SystemExit('v0.8.35 helper marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.35 compile helper + real-device river renderer restore PASS')
