from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.31 field fix from real-phone screenshot:
# - absolutely no blue river geometry may render in India/China;
# - never publish the initial rectangular-bbox waterway snapshot directly;
# - every visible river/khola is clipped against the exact union of Nepal's 77 district polygons;
# - keep the v0.8.30 blue core + glow styling, but only after exact Nepal clipping;
# - official BIPAD/DHM reading/status/2 km alert truth is untouched.

anchor='    private static RiverWay copyRiverStrict(RiverWay src){'
if anchor not in m:
    raise SystemExit('v0.8.31 copyRiverStrict anchor missing')
helpers=r'''    private static boolean v0831PointInRing(double lon,double lat,JSONArray ring){
        if(ring==null||ring.length()<4)return false;
        boolean inside=false;int n=ring.length();
        for(int i=0,j=n-1;i<n;j=i++){
            JSONArray pi=ring.optJSONArray(i),pj=ring.optJSONArray(j);
            if(pi==null||pj==null||pi.length()<2||pj.length()<2)continue;
            double xi=pi.optDouble(0,Double.NaN),yi=pi.optDouble(1,Double.NaN);
            double xj=pj.optDouble(0,Double.NaN),yj=pj.optDouble(1,Double.NaN);
            if(!Double.isFinite(xi)||!Double.isFinite(yi)||!Double.isFinite(xj)||!Double.isFinite(yj))continue;
            double den=(yj-yi)==0?1e-15:(yj-yi);
            boolean cross=((yi>lat)!=(yj>lat)) && (lon < (xj-xi)*(lat-yi)/den+xi);
            if(cross)inside=!inside;
        }
        return inside;
    }

    private static boolean v0831InsidePolygon(double lon,double lat,JSONArray polygon){
        if(polygon==null||polygon.length()==0)return false;
        JSONArray outer=polygon.optJSONArray(0);if(!v0831PointInRing(lon,lat,outer))return false;
        for(int i=1;i<polygon.length();i++)if(v0831PointInRing(lon,lat,polygon.optJSONArray(i)))return false;
        return true;
    }

    private static boolean v0831InsideNepalExact(double lon,double lat,JSONObject root){
        if(root==null||lon<79.8||lon>88.5||lat<26.0||lat>30.7)return false;
        JSONArray fs=root.optJSONArray("features");if(fs==null)return false;
        for(int i=0;i<fs.length();i++){
            JSONObject f=fs.optJSONObject(i),geom=f==null?null:f.optJSONObject("geometry");if(geom==null)continue;
            String type=geom.optString("type","");JSONArray c=geom.optJSONArray("coordinates");if(c==null)continue;
            if("Polygon".equals(type)){
                if(v0831InsidePolygon(lon,lat,c))return true;
            }else if("MultiPolygon".equals(type)){
                for(int p=0;p<c.length();p++)if(v0831InsidePolygon(lon,lat,c.optJSONArray(p)))return true;
            }
        }
        return false;
    }

    private static List<RiverWay> v0831ClipToNepalExact(List<RiverWay> ways,JSONObject nepal){
        List<RiverWay> out=new ArrayList<>();if(nepal==null)return out;
        for(RiverWay src:ways){
            if(src==null||src.points.size()<2)continue;
            RiverWay cur=null;
            for(int i=1;i<src.points.size();i++){
                double[] a=src.points.get(i-1),b=src.points.get(i);
                double segKm=Math.max(0.001,km(a[1],a[0],b[1],b[0]));
                int steps=Math.max(1,Math.min(180,(int)Math.ceil(segKm/0.20)));
                for(int s=(i==1?0:1);s<=steps;s++){
                    double f=s/(double)steps;
                    double lo=a[0]+(b[0]-a[0])*f,la=a[1]+(b[1]-a[1])*f;
                    boolean inside=v0831InsideNepalExact(lo,la,nepal);
                    if(inside){
                        if(cur==null){cur=new RiverWay();cur.name=src.name;cur.matchName=src.matchName;cur.type=src.type;}
                        cur.points.add(new double[]{lo,la});
                    }else if(cur!=null){
                        if(cur.points.size()>=2)out.add(cur);cur=null;
                    }
                }
            }
            if(cur!=null&&cur.points.size()>=2)out.add(cur);
        }
        return out;
    }

'''
if 'private static boolean v0831InsideNepalExact(' not in m:
    m=m.replace(anchor,helpers+anchor,1)

old='List<RiverWay> chosen=viewportInsideNepalStrict(fw,fs,fe,fn,nepal)?copyWaysExact(candidates):clipWaysToNepalDense(candidates,nepal);'
new='List<RiverWay> chosen=v0831ClipToNepalExact(candidates,nepal);'
if old in m:
    m=m.replace(old,new,1)
elif new not in m:
    raise SystemExit('v0.8.31 chosen clip anchor missing')

# Critical startup fix: the visible source starts EMPTY. The old snapshot was bbox-filtered and
# could include India/China before the strict viewport refresh ran.
source_old='style.addSource(new GeoJsonSource("fs-rivers", riversGeoJson));'
source_new='style.addSource(new GeoJsonSource("fs-rivers", emptyFeatureCollection()));'
if source_old in m:
    m=m.replace(source_old,source_new,1)
elif source_new not in m:
    raise SystemExit('v0.8.31 fs-rivers source init anchor missing')

# Re-run strict renderer several times during startup. If bundled geometry is still loading on
# the first callback, later callbacks render it; camera-idle keeps subsequent pans/zooms strict.
style_anchor='startParticles();'
style_extra='startParticles();main.postDelayed(this::refreshVisibleRiverTiles,350L);main.postDelayed(this::refreshVisibleRiverTiles,1200L);main.postDelayed(this::refreshVisibleRiverTiles,3000L);'
if style_extra not in m:
    if style_anchor not in m: raise SystemExit('v0.8.31 startParticles anchor missing')
    m=m.replace(style_anchor,style_extra,1)

# Camera: show Nepal larger, with less surrounding India/China background.
m=re.sub(r'\.target\(NEPAL_CENTER\)\.zoom\([0-9.]+\)', '.target(NEPAL_CENTER).zoom(6.0)', m, count=1)
m=m.replace('map.setMinZoomPreference(5.35);','map.setMinZoomPreference(5.65);',1)
m=m.replace('Math.max(5.35, Math.min(19.0, current + delta))','Math.max(5.65, Math.min(19.0, current + delta))',1)

# Keep the visible blue style, but avoid an oversized halo after clipping.
m=m.replace('lineWidth((float)(7.4+2.4*wave))','lineWidth((float)(6.4+1.8*wave))',1)
m=m.replace('lineWidth((float)(3.0+0.35*wave))','lineWidth((float)(2.8+0.30*wave))',1)

g=g.replace('versionCode 50','versionCode 51',1).replace("versionName '0.8.30'","versionName '0.8.31'",1)
if 'versionCode 51' not in g or "versionName '0.8.31'" not in g:
    raise SystemExit('v0.8.31 version bump failed')

for marker in [
    'v0831InsideNepalExact',
    'v0831ClipToNepalExact(candidates,nepal)',
    'style.addSource(new GeoJsonSource("fs-rivers", emptyFeatureCollection()))',
    'main.postDelayed(this::refreshVisibleRiverTiles,3000L)',
    'map.addOnCameraIdleListener(this::refreshVisibleRiverTiles)',
    'lineColor("#1FC7FF")',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'currentFlowRivers',
    'sameRiverGaugeFor',
    'routeD<=0.75']:
    if marker not in m:
        raise SystemExit('v0.8.31 marker missing: '+marker)
if 'viewportInsideNepalStrict(fw,fs,fe,fn,nepal)?copyWaysExact(candidates)' in m:
    raise SystemExit('v0.8.31 unsafe interior full-way publish remained')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.31 HARD Nepal-only river clip PASS')
