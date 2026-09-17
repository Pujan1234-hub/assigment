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

# v0.8.25 field fixes from real-phone screenshots:
# - Interior Nepal viewports publish exact OSM waterway geometry untouched, so urban rivers
#   such as Dhobi/Rudramati do not disappear because of tiny district-polygon seams.
# - Border/national viewports are densely sampled/clipped so no river overlay leaks to India/China.
# - Moving flow beads are generated ONLY from fresh current official same-river gauge segments.
# - Current map truth is recent (<=30m), not any observation from the same calendar day.
# - Same-river gauge matching prefers name, then permits a tight geometry match for aliases
#   such as Rudramati/Dhobi when the official gauge lies on the rendered OSM waterway.

# Current map state must mean current, not merely today's historic observation.
a=a.replace(
    'boolean current=Double.isFinite(level)&&at>0&&sameNepalCalendarDay(at,now)&&at-now<=5L*60L*1000L;',
    'boolean current=Double.isFinite(level)&&at>0&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L;',1)
if 'now-at<=30L*60L*1000L' not in a:
    raise SystemExit('recent-current activity marker missing')

# Exact interior waterway publishing; border-only dense clipping.
old='List<RiverWay> chosen=splitWaysToNepalStrict(candidates,nepal);'
new='List<RiverWay> chosen=viewportInsideNepalStrict(fw,fs,fe,fn,nepal)?copyWaysExact(candidates):clipWaysToNepalDense(candidates,nepal);'
if old not in m: raise SystemExit('v0.8.24 chosen clip anchor missing')
m=m.replace(old,new,1)

anchor='    private static RiverWay copyRiverStrict(RiverWay src){'
helpers=r'''    private static boolean viewportInsideNepalStrict(double west,double south,double east,double north,JSONObject nepal){
        if(nepal==null)return false;
        double mx=(west+east)*0.5,my=(south+north)*0.5;
        double[][] pts={{west,south},{west,north},{east,south},{east,north},{mx,south},{mx,north},{west,my},{east,my},{mx,my}};
        try{for(double[]p:pts)if(!insideDistricts(p[0],p[1],nepal))return false;return true;}catch(Exception e){return false;}
    }

    private static List<RiverWay> copyWaysExact(List<RiverWay> ways){
        List<RiverWay> out=new ArrayList<>();
        for(RiverWay src:ways){if(src==null||src.points.size()<2)continue;out.add(copyRiverStrict(src));}
        return out;
    }

    private static List<RiverWay> clipWaysToNepalDense(List<RiverWay> ways,JSONObject nepal){
        List<RiverWay> out=new ArrayList<>();if(nepal==null)return out;
        for(RiverWay src:ways){
            if(src==null||src.points.size()<2)continue;
            RiverWay cur=null;
            for(int i=1;i<src.points.size();i++){
                double[]a=src.points.get(i-1),b=src.points.get(i);
                double segKm=Math.max(0.001,km(a[1],a[0],b[1],b[0]));
                int steps=Math.max(1,Math.min(120,(int)Math.ceil(segKm/0.35)));
                for(int s=(i==1?0:1);s<=steps;s++){
                    double f=s/(double)steps,lo=a[0]+(b[0]-a[0])*f,la=a[1]+(b[1]-a[1])*f;
                    boolean inside=false;try{inside=insideDistricts(lo,la,nepal);}catch(Exception ignored){}
                    if(inside){
                        if(cur==null){cur=new RiverWay();cur.name=src.name;cur.matchName=src.matchName;cur.type=src.type;}
                        cur.points.add(new double[]{lo,la});
                    }else if(cur!=null){if(cur.points.size()>=2)out.add(cur);cur=null;}
                }
            }
            if(cur!=null&&cur.points.size()>=2)out.add(cur);
        }
        return out;
    }

'''
if anchor not in m: raise SystemExit('copyRiverStrict anchor missing')
m=m.replace(anchor,helpers+anchor,1)

# Static geographic context should not look like a live river. Fresh official status layers
# provide the bright source-exact colour/glow.
m=m.replace('lineColor("#58d9ef"), lineWidth(1.55f), lineOpacity(0.88f)',
            'lineColor("#7897a1"), lineWidth(1.25f), lineOpacity(0.46f)',1)
m=m.replace('lineColor("#0b5060"), lineWidth(3.2f), lineOpacity(0.28f)',
            'lineColor("#274c56"), lineWidth(2.4f), lineOpacity(0.18f)',1)

# Rebuild current status geo and simultaneously retain only those same-river segments as
# animation routes. This makes “flow visible but no current status” impossible.
bstart=m.find('    private String[] buildRiverStatusGeo(List<RiverWay> riverSnapshot,List<StationDot> stationSnapshot) {')
bend=m.find('    private RiverWay nearestMatchingRiverForGauge(',bstart)
if bstart<0 or bend<0: raise SystemExit('river status builder anchors missing')
builder=r'''    private final List<RiverWay> currentFlowRivers=new ArrayList<>();

    private String[] buildRiverStatusGeo(List<RiverWay> riverSnapshot,List<StationDot> stationSnapshot) {
        try{
            JSONArray normal=new JSONArray(),alert=new JSONArray(),warning=new JSONArray(),danger=new JSONArray();
            java.util.HashSet<String> used=new java.util.HashSet<>();List<RiverWay> flow=new ArrayList<>();
            for(StationDot g:stationSnapshot){
                if(g==null||!g.fresh)continue;
                RiverWay r=nearestMatchingRiverForGauge(g,riverSnapshot,used);if(r==null)continue;
                String stage=normalizeStage(g.stage);JSONArray target;
                if("danger".equals(stage))target=danger;else if("warning".equals(stage))target=warning;else if("alert".equals(stage))target=alert;else if("normal".equals(stage))target=normal;else continue;
                JSONArray coords=localRiverSegment(r,g.lat,g.lon);if(coords.length()<2)continue;
                JSONObject geom=new JSONObject().put("type","LineString").put("coordinates",coords);
                JSONObject props=new JSONObject().put("name",r.name).put("status",stage).put("gauge",g.name);
                target.put(new JSONObject().put("type","Feature").put("geometry",geom).put("properties",props));
                RiverWay fr=new RiverWay();fr.name=r.name;fr.matchName=r.matchName;fr.type=r.type;
                for(int i=0;i<coords.length();i++){JSONArray p=coords.optJSONArray(i);if(p!=null&&p.length()>=2)fr.points.add(new double[]{p.optDouble(0),p.optDouble(1)});}
                if(fr.points.size()>=2)flow.add(fr);
            }
            synchronized(currentFlowRivers){currentFlowRivers.clear();currentFlowRivers.addAll(flow);}
            return new String[]{featureCollection(normal),featureCollection(alert),featureCollection(warning),featureCollection(danger)};
        }catch(Exception e){synchronized(currentFlowRivers){currentFlowRivers.clear();}String empty=emptyFeatureCollection();return new String[]{empty,empty,empty,empty};}
    }

'''
m=m[:bstart]+builder+m[bend:]

# Prefer official name matching, but aliases/transliterations may differ. Spatial fallback is
# accepted only when the official gauge sits tightly on the actual OSM river geometry.
ns=m.find('    private RiverWay nearestMatchingRiverForGauge(')
ne=m.find('    private static double riverDistanceToGauge(',ns)
if ns<0 or ne<0: raise SystemExit('nearestMatchingRiverForGauge anchors missing')
nearest=r'''    private RiverWay nearestMatchingRiverForGauge(StationDot g,List<RiverWay> riverSnapshot,java.util.HashSet<String> used){
        if(g==null)return null;String sk=riverNameKey(g.name);RiverWay best=null;double bestScore=Double.MAX_VALUE;String bestId="";
        for(RiverWay r:riverSnapshot){
            if(r==null||r.points.size()<2)continue;String id=riverKey(r);if(used.contains(id))continue;
            String rk=riverMatchKey(r);boolean exact=sk.length()>=3&&rk.length()>=3&&sameRiverKey(rk,sk);
            double d=riverDistanceToGauge(r,g.lat,g.lon);
            double limit=exact?6.0:0.75;if(d>limit)continue;
            double score=d+(exact?0.0:0.40);if(score<bestScore){bestScore=score;best=r;bestId=id;}
        }
        if(best!=null)used.add(bestId);return best;
    }

'''
m=m[:ns]+nearest+m[ne:]

# Same rule for tap popup: exact-name first; otherwise only a gauge physically on this route.
ss=m.find('    private StationDot sameRiverGaugeFor(')
se=m.find('    private static String formatOfficialTime(',ss)
if se<0: se=m.find('    private StationDot directGaugeFor(',ss)
if ss<0 or se<0: raise SystemExit('sameRiverGaugeFor anchors missing')
# Preserve methods after sameRiverGaugeFor by replacing only through the next known method.
same=r'''    private StationDot sameRiverGaugeFor(RiverWay r,double la,double lo,boolean freshOnly){
        if(r==null)return null;String key=riverMatchKey(r);StationDot exactBest=null,spatialBest=null;double exactScore=Double.MAX_VALUE,spatialScore=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||(freshOnly&&!s.fresh))continue;String sk=riverNameKey(s.name);double routeD=riverDistanceToGauge(r,s.lat,s.lon);
            if(key.length()>=3&&sk.length()>=3&&sameRiverKey(key,sk)){double x=km(la,lo,s.lat,s.lon);if(x<exactScore){exactScore=x;exactBest=s;}}
            else if(routeD<=0.75){double x=routeD+0.015*km(la,lo,s.lat,s.lon);if(x<spatialScore){spatialScore=x;spatialBest=s;}}
        }}
        return exactBest!=null?exactBest:spatialBest;
    }

'''
m=m[:ss]+same+m[se:]

# Animate only the fresh matched river segments built above.
pt=m.find('    private final Runnable particleTick = new Runnable() {')
pe=m.find('    private StationDot readStation(Object o) {',pt)
if pt<0 or pe<0: raise SystemExit('particleTick anchors missing')
tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                List<RiverWay> flowSnapshot; synchronized(currentFlowRivers){flowSnapshot=new ArrayList<>(currentFlowRivers);}
                JSONArray features=new JSONArray();int n=Math.min(34,flowSnapshot.size());double phase=((System.currentTimeMillis()-particleStart)%6000L)/6000.0;
                for(int i=0;i<n;i++){
                    RiverWay r=flowSnapshot.get(i);if(r==null||r.points.size()<2)continue;
                    double v=((phase+i*.173)%1.0)*(r.points.size()-1);int ix=Math.min(r.points.size()-2,(int)Math.floor(v));double f=v-ix;
                    double[]p0=r.points.get(ix),p1=r.points.get(ix+1);features.put(pointFeature(p0[0]+(p1[0]-p0[0])*f,p0[1]+(p1[1]-p0[1])*f,"flow"));
                }
                setGeo("fs-flow-particles",new JSONObject().put("type","FeatureCollection").put("features",features).toString());
                double ph=(System.currentTimeMillis()%1800L)/1800.0;float pulse=(float)(0.30+0.18*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));
                LineLayer warningGlow=style.getLayerAs("fs-river-warning-status-layer-glow"),dangerGlow=style.getLayerAs("fs-river-danger-status-layer-glow");
                if(warningGlow!=null)warningGlow.setProperties(lineOpacity(Math.min(0.58f,pulse)),lineWidth(7.6f));
                if(dangerGlow!=null)dangerGlow.setProperties(lineOpacity(Math.min(0.68f,pulse+0.12f)),lineWidth(9.2f));
            }catch(Exception ignored){}
            main.postDelayed(this,180L);
        }
    };

'''
m=m[:pt]+tick+m[pe:]

# Version bump from generated v0.8.24.
g=g.replace('versionCode 44','versionCode 45',1).replace("versionName '0.8.24'","versionName '0.8.25'",1)
if 'versionCode 45' not in g or "versionName '0.8.25'" not in g: raise SystemExit('v0.8.25 version bump failed')

m_path.write_text(m,encoding='utf-8');a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard gates.
m2=m_path.read_text(encoding='utf-8');a2=a_path.read_text(encoding='utf-8')
for marker in ['viewportInsideNepalStrict(fw,fs,fe,fn,nepal)','clipWaysToNepalDense(candidates,nepal)','currentFlowRivers','flowSnapshot=new ArrayList<>(currentFlowRivers)','routeD<=0.75','riverLabelsGeoJson=emptyFeatureCollection()']:
    if marker not in m2: raise SystemExit('v0.8.25 map marker missing: '+marker)
for marker in ['now-at<=30L*60L*1000L','rain-stations/?latest=true']:
    if marker not in a2: raise SystemExit('v0.8.25 activity marker missing: '+marker)
if 'List<RiverWay> visibleSnapshot=new ArrayList<>(rivers);' in m2: raise SystemExit('all-river fake flow animation remained')
print('FloodSafe v0.8.25 actual-river + current-only flow PASS')
