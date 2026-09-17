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

# v0.8.44 field fixes:
# 1) Every river that is actually visible in the progressive national tiers must also
#    exist in the tap-selection list. v0.8.42 published MAJOR/MEDIUM GeoJSON without
#    replacing `rivers`, so some visible lines could never be selected.
# 2) River hit-testing must measure distance to the LINE SEGMENT, not only sampled
#    vertices. This fixes taps on long/sparse OSM segments.
# 3) Rows returned by BIPAD/DHM latest=true are explicitly tagged as latest-source rows.
#    A station with a current official timestamp must not be shown as stale merely because
#    its water-level numeric field is temporarily blank. Flood status still comes only from
#    the official raw status; no warning/danger is invented.
# 4) Emergency 2 km notification gates are untouched.

# -----------------------------------------------------------------------------
# Activity: mark rows which really came from BIPAD latest=true before catalog merge.
# -----------------------------------------------------------------------------
old='''            for(int i=0;i<latest.length();i++){
                JSONObject r=latest.optJSONObject(i);if(r==null)continue;
                List<String>ids=trustedIds(r);long rt=trustedRowTime(r);'''
new='''            for(int i=0;i<latest.length();i++){
                JSONObject r=latest.optJSONObject(i);if(r==null)continue;
                try{r.put("_floodsafeLatestEndpoint",true);}catch(Exception ignored){}
                List<String>ids=trustedIds(r);long rt=trustedRowTime(r);'''
if old not in a:
    raise SystemExit('v0.8.44 latest merge anchor missing')
a=a.replace(old,new,1)

# v0.8.19 made "latest" current for the Nepal calendar day, but still required a numeric
# level. Some BIPAD/DHM stations are present in latest=true with a current official time and
# source status while the level field is temporarily null. Those are ONLINE/current-source,
# not offline. Keep stage unknown when the source does not publish a flood status.
old_current='boolean current=Double.isFinite(level)&&at>0&&sameNepalCalendarDay(at,now)&&at-now<=5L*60L*1000L;'
new_current='boolean current=(Double.isFinite(level)||r.optBoolean("_floodsafeLatestEndpoint",false))&&at>0&&sameNepalCalendarDay(at,now)&&at-now<=5L*60L*1000L; // V0844_LATEST_ENDPOINT_ONLINE'
if old_current not in a:
    raise SystemExit('v0.8.44 current-source anchor missing')
a=a.replace(old_current,new_current,1)

# Do not label a current latest=true row NORMAL merely because no explicit source status
# exists. v0.8.15 already requires source truth; keep that rule visible here.
if 'raw==null||raw.trim().isEmpty()' not in a:
    raise SystemExit('v0.8.44 source-truth guard missing')

# -----------------------------------------------------------------------------
# Map: parse the same GeoJSON being painted so the clickable list exactly matches it.
# -----------------------------------------------------------------------------
anchor='    private void refreshVisibleRiverTiles(){'
helper=r'''    private List<RiverWay> v844RiverWaysFromGeoJson(String geo){
        List<RiverWay> out=new ArrayList<>();
        if(geo==null||geo.trim().isEmpty())return out;
        try{
            JSONObject root=new JSONObject(geo);JSONArray fs=root.optJSONArray("features");
            if(fs==null)return out;
            for(int i=0;i<fs.length();i++){
                JSONObject f=fs.optJSONObject(i);if(f==null)continue;
                JSONObject geom=f.optJSONObject("geometry");if(geom==null)continue;
                JSONObject p=f.optJSONObject("properties");
                String name=p==null?"नदी / खोला":p.optString("name","नदी / खोला");
                String type=p==null?"stream":p.optString("type","stream");
                String gt=geom.optString("type","");
                if("LineString".equals(gt)){
                    RiverWay r=v844RiverFromCoords(geom.optJSONArray("coordinates"),name,type);
                    if(r!=null)out.add(r);
                }else if("MultiLineString".equals(gt)){
                    JSONArray lines=geom.optJSONArray("coordinates");if(lines==null)continue;
                    for(int j=0;j<lines.length();j++){
                        RiverWay r=v844RiverFromCoords(lines.optJSONArray(j),name,type);
                        if(r!=null)out.add(r);
                    }
                }
            }
        }catch(Exception ignored){}
        return out;
    }

    private RiverWay v844RiverFromCoords(JSONArray coords,String name,String type){
        if(coords==null||coords.length()<2)return null;
        RiverWay r=new RiverWay();r.name=(name==null||name.trim().isEmpty())?"नदी / खोला":name;r.type=(type==null||type.trim().isEmpty())?"stream":type;
        try{r.matchName=riverNameKey(r.name);}catch(Exception ignored){}
        for(int i=0;i<coords.length();i++){
            JSONArray c=coords.optJSONArray(i);if(c==null||c.length()<2)continue;
            double lo=c.optDouble(0,Double.NaN),la=c.optDouble(1,Double.NaN);
            if(Double.isFinite(la)&&Double.isFinite(lo)&&isNepalish(la,lo))r.points.add(new double[]{lo,la});
        }
        return r.points.size()>=2?r:null;
    }

'''
if 'private List<RiverWay> v844RiverWaysFromGeoJson' not in m:
    if anchor not in m: raise SystemExit('v0.8.44 progressive renderer anchor missing')
    m=m.replace(anchor,helper+anchor,1)

# In the MAJOR/MEDIUM national branch, publish the exact same list to hit testing.
old='''            final String publishTier=tier;
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                riversGeoJson=publishTier;
                setGeo("fs-rivers",publishTier);'''
new='''            final String publishTier=tier;
            final List<RiverWay> publishWays=v844RiverWaysFromGeoJson(publishTier);
            main.post(()->{
                if(!key.equals(lastRiverTileKey))return;
                rivers.clear();rivers.addAll(publishWays);riversGeoJson=publishTier; // V0844_VISIBLE_EQUALS_TOUCHABLE
                setGeo("fs-rivers",publishTier);'''
if old not in m:
    raise SystemExit('v0.8.44 national tier publish anchor missing')
m=m.replace(old,new,1)

# Replace vertex-sampling hit test with true point-to-segment distance. A line that the user
# can see is now selectable even if the nearest OSM vertex is far from the finger.
start=m.find('    private RiverWay nearestRiver(double la, double lo, double thresholdKm) {')
if start<0:
    start=m.find('    private RiverWay nearestRiver(double la,double lo,double thresholdKm) {')
end=m.find('    private void showRiver(',start)
if start<0 or end<0:
    raise SystemExit('v0.8.44 nearestRiver anchors missing')
nearest=r'''    private RiverWay nearestRiver(double la,double lo,double thresholdKm) {
        RiverWay best=null;double bestD=Double.MAX_VALUE;
        // Visible list is already progressive/viewport bounded, so exact segment testing is
        // cheap enough on tap and avoids the old sampled-vertex miss.
        List<RiverWay> snap=new ArrayList<>(rivers);
        double latPad=Math.max(0.001,thresholdKm/110.6);
        double cos=Math.max(0.35,Math.cos(Math.toRadians(la)));
        double lonPad=Math.max(0.001,thresholdKm/(111.3*cos));
        for(RiverWay r:snap){
            if(r==null||r.points.size()<2)continue;
            for(int i=1;i<r.points.size();i++){
                double[] a=r.points.get(i-1),b=r.points.get(i);
                if(Math.max(a[1],b[1])<la-latPad||Math.min(a[1],b[1])>la+latPad||
                   Math.max(a[0],b[0])<lo-lonPad||Math.min(a[0],b[0])>lo+lonPad)continue;
                double d=v844PointSegmentKm(la,lo,a[1],a[0],b[1],b[0]);
                if(d<bestD){bestD=d;best=r;if(bestD<0.012)return best;}
            }
        }
        return bestD<=thresholdKm?best:null;
    }

    private static double v844PointSegmentKm(double la,double lo,double aLa,double aLo,double bLa,double bLo){
        double cos=Math.max(0.35,Math.cos(Math.toRadians(la)));
        double ax=(aLo-lo)*111.3*cos, ay=(aLa-la)*110.6;
        double bx=(bLo-lo)*111.3*cos, by=(bLa-la)*110.6;
        double dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy;
        if(den<=1e-12)return Math.sqrt(ax*ax+ay*ay);
        double t=-(ax*dx+ay*dy)/den;t=Math.max(0.0,Math.min(1.0,t));
        double x=ax+t*dx,y=ay+t*dy;return Math.sqrt(x*x+y*y);
    }

'''
m=m[:start]+nearest+m[end:]

# Keep v0.8.43 visual width; only make the actual hit target reliable.
if 'V0843_FINGER_FRIENDLY_RIVER_TAP' not in m:
    raise SystemExit('v0.8.44 expected v0.8.43 tap marker missing')

# Version bump.
g=g.replace('versionCode 63','versionCode 64',1).replace("versionName '0.8.43'","versionName '0.8.44'",1)
if 'versionCode 64' not in g or "versionName '0.8.44'" not in g:
    raise SystemExit('v0.8.44 version bump failed')

# Safety gates: 2 km + warning/danger + fresh remains exactly as before.
for marker in [
    '_floodsafeLatestEndpoint',
    'V0844_LATEST_ENDPOINT_ONLINE',
    'v844RiverWaysFromGeoJson',
    'V0844_VISIBLE_EQUALS_TOUCHABLE',
    'v844PointSegmentKm',
    'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))']:
    text=(a+'\n'+m)
    if marker not in text:raise SystemExit('v0.8.44 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.44 all-visible-river taps + latest online station fix PASS')
