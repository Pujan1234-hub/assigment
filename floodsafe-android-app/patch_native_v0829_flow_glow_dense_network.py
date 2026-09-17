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

# v0.8.29 MAP-ONLY polish requested from field video:
# - remove moving white flow beads/dots;
# - use a smooth blue glow pulse instead;
# - make the national river/khola context denser and geographically distributed so
#   western/central/eastern Nepal all retain waterway context;
# - keep exact local OSM geometry, Nepal-only clipping and official current-flow truth;
# - DO NOT change alerts, notifications, 2 km radius, or freshness safety logic.

# -----------------------------------------------------------------------------
# National overview: v0.8.24 intentionally capped at 260 named rivers. That looked
# disconnected on a phone. Keep the real bundled OSM source, but take a balanced
# sample across a 12x8 Nepal grid and allow named streams/khola as context too.
# The strict Nepal clip below remains authoritative, so nothing can render abroad.
# -----------------------------------------------------------------------------
old=r'''                }else{
                    for(RiverWay src:overviewRivers){
                        if(src==null||src.points.size()<2||!"river".equalsIgnoreCase(src.type))continue;
                        if(src.name==null||src.name.trim().isEmpty()||"नदी / खोला".equals(src.name))continue;
                        if(!riverIntersectsBox(src,fw,fs,fe,fn))continue;
                        String k=riverKey(src);if(seen.add(k))candidates.add(copyRiverStrict(src));
                        if(candidates.size()>=260)break;
                    }
                }
'''
new=r'''                }else{
                    // Dense but balanced Nepal-wide context. Never invent geometry: every line
                    // still comes from the bundled OSM river/stream source.
                    int[] cellCount=new int[96];
                    for(RiverWay src:overviewRivers){
                        if(src==null||src.points.size()<2||!riverIntersectsBox(src,fw,fs,fe,fn))continue;
                        boolean named=src.name!=null&&!src.name.trim().isEmpty()&&!"नदी / खोला".equals(src.name);
                        boolean mainRiver="river".equalsIgnoreCase(src.type);
                        if(!mainRiver&&!named)continue;
                        double[] mid=src.points.get(src.points.size()/2);
                        int gx=Math.max(0,Math.min(11,(int)Math.floor((mid[0]-80.0)/0.70)));
                        int gy=Math.max(0,Math.min(7,(int)Math.floor((mid[1]-26.2)/0.55)));
                        int cell=gy*12+gx;
                        if(cellCount[cell]>=14)continue;
                        String k=riverKey(src);if(seen.add(k)){candidates.add(copyRiverStrict(src));cellCount[cell]++;}
                        if(candidates.size()>=1100)break;
                    }
                    // Fill sparse cells with additional real waterways so district edges do not
                    // look disconnected. This remains presentation geometry, not fake live flow.
                    if(candidates.size()<900){
                        for(RiverWay src:overviewRivers){
                            if(src==null||src.points.size()<2||!riverIntersectsBox(src,fw,fs,fe,fn))continue;
                            double[] mid=src.points.get(src.points.size()/2);
                            int gx=Math.max(0,Math.min(11,(int)Math.floor((mid[0]-80.0)/0.70)));
                            int gy=Math.max(0,Math.min(7,(int)Math.floor((mid[1]-26.2)/0.55)));
                            int cell=gy*12+gx;
                            if(cellCount[cell]>=18)continue;
                            String k=riverKey(src);if(seen.add(k)){candidates.add(copyRiverStrict(src));cellCount[cell]++;}
                            if(candidates.size()>=1200)break;
                        }
                    }
                }
'''
if old not in m:
    raise SystemExit('v0.8.29 national 260-river selector anchor missing')
m=m.replace(old,new,1)

# -----------------------------------------------------------------------------
# Hide the old white/cyan point-particle layer. Keep the source/layer itself for
# compatibility with older generated code, but make it invisible.
# -----------------------------------------------------------------------------
pat=r'''ensurePointSource\("fs-flow-particles",\s*"fs-flow-particles-layer",\s*"#[0-9A-Fa-f]{6}",\s*([0-9.]+)f,\s*([0-9.]+)f\);'''
m,n=re.subn(pat,'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#168BFF", 0.1f, 0.0f);',m,count=1)
if n!=1 and '"fs-flow-particles", "fs-flow-particles-layer", "#168BFF", 0.1f, 0.0f' not in m:
    raise SystemExit('v0.8.29 flow particle layer anchor missing')

# Replace moving beads with a lightweight line glow pulse. The whole geographic network
# gets only a subtle breathing glow. Stronger pulse is restricted to official CURRENT
# same-river segments already held in currentFlowRivers/status sources.
pt=m.find('    private final Runnable particleTick = new Runnable() {')
pe=m.find('    private StationDot readStation(Object o) {',pt)
if pt<0 or pe<0:
    raise SystemExit('v0.8.29 particleTick anchors missing')
tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                // No moving white dots: keep the compatibility source empty.
                setGeo("fs-flow-particles",emptyFeatureCollection());
                double phase=(System.currentTimeMillis()%2200L)/2200.0;
                double wave=0.5+0.5*Math.sin(phase*Math.PI*2.0);

                // Subtle blue breathing glow on actual OSM water geometry only.
                LineLayer baseGlow=style.getLayerAs("fs-river-glow");
                if(baseGlow!=null)baseGlow.setProperties(
                        lineOpacity((float)(0.20+0.12*wave)),
                        lineWidth((float)(3.0+0.9*wave)));

                // CURRENT official same-river segments get the stronger live glow.
                String[] ids={"fs-river-normal-status-layer-glow","fs-river-alert-status-layer-glow",
                              "fs-river-warning-status-layer-glow","fs-river-danger-status-layer-glow"};
                float[] widths={5.4f,6.2f,7.3f,8.6f};
                for(int i=0;i<ids.length;i++){
                    LineLayer glow=style.getLayerAs(ids[i]);
                    if(glow!=null)glow.setProperties(
                            lineOpacity((float)(0.24+0.28*wave)),
                            lineWidth(widths[i]+(float)(1.2*wave)));
                }
            }catch(Exception ignored){}
            main.postDelayed(this,420L);
        }
    };

'''
m=m[:pt]+tick+m[pe:]

# v0.8.28 keeps all river lines FloodSafe blue; make the core a touch clearer against
# satellite imagery while retaining the separate glow layer.
m=m.replace('lineColor("#168BFF"), lineWidth(1.55f), lineOpacity(0.82f)',
            'lineColor("#168BFF"), lineWidth(1.75f), lineOpacity(0.92f)',1)

# Version bump. Alert/notification classes are deliberately not opened by this patch.
g=g.replace('versionCode 48','versionCode 49',1).replace("versionName '0.8.28'","versionName '0.8.29'",1)
if 'versionCode 49' not in g or "versionName '0.8.29'" not in g:
    raise SystemExit('v0.8.29 version bump failed')

# Hard gates: Nepal/source truth and alert safety must survive this presentation patch.
for marker in [
    'viewportInsideNepalStrict(fw,fs,fe,fn,nepal)',
    'clipWaysToNepalDense(candidates,nepal)',
    'cameraTargetInsideNepal',
    'currentFlowRivers',
    'sameRiverGaugeFor',
    'routeD<=0.75',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'cellCount=new int[96]',
    'candidates.size()>=1200',
    '#168BFF']:
    if marker not in m:
        raise SystemExit('v0.8.29 map marker missing: '+marker)
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a:
        raise SystemExit('v0.8.29 alert safety marker changed unexpectedly: '+marker)
if 'features.put(pointFeature(' in tick:
    raise SystemExit('moving white flow bead generation remained')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.29 flow-glow + dense Nepal-wide river network PASS')
