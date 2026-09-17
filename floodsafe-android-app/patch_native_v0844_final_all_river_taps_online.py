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

# v0.8.44 FINAL
# - visible river list == touchable river list at every progressive zoom tier
# - exact point-to-segment hit testing instead of sampled-vertex misses
# - BIPAD latest=true rows stay current/online even when a numeric level field is blank
# - official source status remains authoritative; 2 km warning/danger safety untouched

# Mark actual latest=true rows before merging with the catalog.
old='''            for(int i=0;i<latest.length();i++){
                JSONObject r=latest.optJSONObject(i);if(r==null)continue;
                List<String>ids=trustedIds(r);long rt=trustedRowTime(r);'''
new='''            for(int i=0;i<latest.length();i++){
                JSONObject r=latest.optJSONObject(i);if(r==null)continue;
                try{r.put("_floodsafeLatestEndpoint",true);}catch(Exception ignored){}
                List<String>ids=trustedIds(r);long rt=trustedRowTime(r);'''
if old not in a: raise SystemExit('v0.8.44 latest-row merge anchor missing')
a=a.replace(old,new,1)

# Patch only parseStation's `current` expression, regardless of small formatting changes
# introduced by earlier versions.
ps=a.find('    private RiverStation parseStation(')
pe=a.find('    private void refreshRainStations()',ps)
if ps<0 or pe<0: raise SystemExit('v0.8.44 parseStation anchors missing')
block=a[ps:pe]
new_current='boolean current=(Double.isFinite(level)||r.optBoolean("_floodsafeLatestEndpoint",false))&&at>0&&sameNepalCalendarDay(at,now)&&at-now<=5L*60L*1000L; // V0844_LATEST_ENDPOINT_ONLINE'
block,n=re.subn(r'boolean current\s*=\s*[^;]+;',new_current,block,count=1)
if n!=1: raise SystemExit('v0.8.44 parseStation current expression missing')
a=a[:ps]+block+a[pe:]

# Source-truth gate must stay in place: no invented NORMAL/WARNING/DANGER.
if 'raw==null||raw.trim().isEmpty()' not in a: raise SystemExit('v0.8.44 source truth guard missing')

# Convert exactly the painted MAJOR/MEDIUM GeoJSON back into RiverWay objects for hit testing.
anchor='    private void refreshVisibleRiverTiles(){'
if anchor not in m: raise SystemExit('v0.8.44 progressive renderer anchor missing')
helper=r'''    private List<RiverWay> v844RiverWaysFromGeoJson(String geo){
        List<RiverWay> out=new ArrayList<>();if(geo==null||geo.trim().isEmpty())return out;
        try{
            JSONObject root=new JSONObject(geo);JSONArray fs=root.optJSONArray("features");if(fs==null)return out;
            for(int i=0;i<fs.length();i++){
                JSONObject f=fs.optJSONObject(i);if(f==null)continue;JSONObject geom=f.optJSONObject("geometry");if(geom==null)continue;
                JSONObject p=f.optJSONObject("properties");String name=p==null?"नदी / खोला":p.optString("name","नदी / खोला");String type=p==null?"stream":p.optString("type","stream");
                String gt=geom.optString("type","");
                if("LineString".equals(gt)){RiverWay r=v844RiverFromCoords(geom.optJSONArray("coordinates"),name,type);if(r!=null)out.add(r);}
                else if("MultiLineString".equals(gt)){JSONArray ls=geom.optJSONArray("coordinates");if(ls!=null)for(int j=0;j<ls.length();j++){RiverWay r=v844RiverFromCoords(ls.optJSONArray(j),name,type);if(r!=null)out.add(r);}}
            }
        }catch(Exception ignored){}
        return out;
    }

    private RiverWay v844RiverFromCoords(JSONArray coords,String name,String type){
        if(coords==null||coords.length()<2)return null;RiverWay r=new RiverWay();
        r.name=(name==null||name.trim().isEmpty())?"नदी / खोला":name;r.type=(type==null||type.trim().isEmpty())?"stream":type;
        try{r.matchName=riverNameKey(r.name);}catch(Exception ignored){}
        for(int i=0;i<coords.length();i++){JSONArray c=coords.optJSONArray(i);if(c==null||c.length()<2)continue;double lo=c.optDouble(0,Double.NaN),la=c.optDouble(1,Double.NaN);if(Double.isFinite(la)&&Double.isFinite(lo)&&isNepalish(la,lo))r.points.add(new double[]{lo,la});}
        return r.points.size()>=2?r:null;
    }

'''
m=m.replace(anchor,helper+anchor,1)

old_publish='''            final String publishTier=tier;
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                riversGeoJson=publishTier;
                setGeo("fs-rivers",publishTier);'''
new_publish='''            final String publishTier=tier;
            final List<RiverWay> publishWays=v844RiverWaysFromGeoJson(publishTier);
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                rivers.clear();rivers.addAll(publishWays);riversGeoJson=publishTier; // V0844_VISIBLE_EQUALS_TOUCHABLE
                setGeo("fs-rivers",publishTier);'''
if old_publish not in m: raise SystemExit('v0.8.44 tier publish anchor missing')
m=m.replace(old_publish,new_publish,1)

# True line-segment distance means taps work on the whole visible segment, not just vertices.
start=m.find('    private RiverWay nearestRiver(double la, double lo, double thresholdKm) {')
if start<0:start=m.find('    private RiverWay nearestRiver(double la,double lo,double thresholdKm) {')
end=m.find('    private void showRiver(',start)
if start<0 or end<0: raise SystemExit('v0.8.44 nearestRiver anchors missing')
nearest=r'''    private RiverWay nearestRiver(double la,double lo,double thresholdKm) {
        RiverWay best=null;double bestD=Double.MAX_VALUE;List<RiverWay> snap=new ArrayList<>(rivers);
        double latPad=Math.max(0.001,thresholdKm/110.6),cos=Math.max(0.35,Math.cos(Math.toRadians(la))),lonPad=Math.max(0.001,thresholdKm/(111.3*cos));
        for(RiverWay r:snap){if(r==null||r.points.size()<2)continue;for(int i=1;i<r.points.size();i++){
            double[] a=r.points.get(i-1),b=r.points.get(i);
            if(Math.max(a[1],b[1])<la-latPad||Math.min(a[1],b[1])>la+latPad||Math.max(a[0],b[0])<lo-lonPad||Math.min(a[0],b[0])>lo+lonPad)continue;
            double d=v844PointSegmentKm(la,lo,a[1],a[0],b[1],b[0]);if(d<bestD){bestD=d;best=r;if(bestD<0.012)return best;}
        }}
        return bestD<=thresholdKm?best:null;
    }

    private static double v844PointSegmentKm(double la,double lo,double aLa,double aLo,double bLa,double bLo){
        double cos=Math.max(0.35,Math.cos(Math.toRadians(la))),ax=(aLo-lo)*111.3*cos,ay=(aLa-la)*110.6,bx=(bLo-lo)*111.3*cos,by=(bLa-la)*110.6;
        double dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy;if(den<=1e-12)return Math.sqrt(ax*ax+ay*ay);
        double t=-(ax*dx+ay*dy)/den;t=Math.max(0.0,Math.min(1.0,t));double x=ax+t*dx,y=ay+t*dy;return Math.sqrt(x*x+y*y);
    }

'''
m=m[:start]+nearest+m[end:]

# Keep v0.8.43 visual width and progressive rendering.
for marker in ['V0843_FINGER_FRIENDLY_RIVER_TAP','V0842_PROGRESSIVE_ZOOM']:
    if marker not in m:raise SystemExit('v0.8.44 prior renderer marker missing: '+marker)

# Version.
g=g.replace('versionCode 63','versionCode 64',1).replace("versionName '0.8.43'","versionName '0.8.44'",1)
if 'versionCode 64' not in g or "versionName '0.8.44'" not in g:raise SystemExit('v0.8.44 version bump failed')

# Emergency gates are deliberately unchanged.
joined=a+'\n'+m
for marker in ['_floodsafeLatestEndpoint','V0844_LATEST_ENDPOINT_ONLINE','v844RiverWaysFromGeoJson','V0844_VISIBLE_EQUALS_TOUCHABLE','v844PointSegmentKm','bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))']:
    if marker not in joined:raise SystemExit('v0.8.44 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8');a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.44 FINAL all river taps + latest online station truth PASS')
