from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.30 field fix from the real-phone Kathmandu screenshot.
# The v0.8.29 river geometry was present but its base core/halo was too thin/dim on
# satellite imagery. Strong glow was mainly obvious on current matched gauge segments.
# This patch makes EVERY real rendered OSM river/khola line clearly blue + glowing,
# while CURRENT/realtime meaning continues to come only from official BIPAD/DHM data.
# No fake river geometry, no fake gauge status, and no moving white flow dots.

# Bright visible base geometry. This is geographic presentation only, not a live-status claim.
old_core='lineColor("#168BFF"), lineWidth(1.75f), lineOpacity(0.92f)'
new_core='lineColor("#1FC7FF"), lineWidth(3.15f), lineOpacity(1.0f)'
if old_core in m:
    m=m.replace(old_core,new_core,1)
elif new_core not in m:
    raise SystemExit('v0.8.30 base river core anchor missing')

old_glow='lineColor("#0a6f92"), lineWidth(3.0f), lineOpacity(0.28f)'
new_glow='lineColor("#168BFF"), lineWidth(8.2f), lineOpacity(0.34f)'
if old_glow in m:
    m=m.replace(old_glow,new_glow,1)
elif new_glow not in m:
    raise SystemExit('v0.8.30 base river glow anchor missing')

# Replace v0.8.29's very subtle breathing effect with a clearly visible smooth halo.
# The base network breathes gently for visual flow. Official CURRENT same-river segments
# still receive an extra stronger pulse from the existing status sources.
pt=m.find('    private final Runnable particleTick = new Runnable() {')
pe=m.find('    private StationDot readStation(Object o) {',pt)
if pt<0 or pe<0:
    raise SystemExit('v0.8.30 particleTick anchors missing')
tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                // White bead/dot animation stays disabled.
                setGeo("fs-flow-particles",emptyFeatureCollection());
                double phase=(System.currentTimeMillis()%2400L)/2400.0;
                double wave=0.5+0.5*Math.sin(phase*Math.PI*2.0);

                // ALL actual OSM waterways: visible blue core + broad smooth halo.
                // This pulse is only a visual flow effect; it does not represent gauge status.
                LineLayer baseGlow=style.getLayerAs("fs-river-glow");
                if(baseGlow!=null)baseGlow.setProperties(
                        lineColor("#168BFF"),
                        lineOpacity((float)(0.30+0.18*wave)),
                        lineWidth((float)(7.4+2.4*wave)));
                LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
                if(baseCore!=null)baseCore.setProperties(
                        lineColor("#1FC7FF"),
                        lineOpacity(1.0f),
                        lineWidth((float)(3.0+0.35*wave)));

                // Official CURRENT matched segments: stronger overlay pulse on top of the
                // geographic blue network. Status/detail truth remains BIPAD/DHM only.
                String[] ids={"fs-river-normal-status-layer-glow","fs-river-alert-status-layer-glow",
                              "fs-river-warning-status-layer-glow","fs-river-danger-status-layer-glow"};
                float[] widths={9.0f,9.8f,10.8f,12.0f};
                for(int i=0;i<ids.length;i++){
                    LineLayer glow=style.getLayerAs(ids[i]);
                    if(glow!=null)glow.setProperties(
                            lineColor("#168BFF"),
                            lineOpacity((float)(0.38+0.26*wave)),
                            lineWidth(widths[i]+(float)(1.8*wave)));
                }
            }catch(Exception ignored){}
            main.postDelayed(this,120L);
        }
    };

'''
m=m[:pt]+tick+m[pe:]

# Make the first/local draw harder to miss after camera movement. Existing camera-idle
# refresh remains authoritative; this only ensures the style is immediately repainted once
# geometry is published.
publish='setGeo("fs-rivers",geo);setGeo("fs-river-labels",emptyFeatureCollection());refreshRiverStatusSources();'
if publish not in m:
    raise SystemExit('v0.8.30 river publish anchor missing')
m=m.replace(publish,
            'setGeo("fs-rivers",geo);setGeo("fs-river-labels",emptyFeatureCollection());refreshRiverStatusSources();main.removeCallbacks(particleTick);if(animationRunning)main.post(particleTick);',
            1)

# Version bump only. Alert/notification source files are deliberately untouched.
g=g.replace('versionCode 49','versionCode 50',1).replace("versionName '0.8.29'","versionName '0.8.30'",1)
if 'versionCode 50' not in g or "versionName '0.8.30'" not in g:
    raise SystemExit('v0.8.30 version bump failed')

# Hard gates: all-Nepal geometry/source truth + no fake white-dot flow + existing current matcher.
for marker in [
    'viewportInsideNepalStrict(fw,fs,fe,fn,nepal)',
    'clipWaysToNepalDense(candidates,nepal)',
    'cameraTargetInsideNepal',
    'currentFlowRivers',
    'sameRiverGaugeFor',
    'routeD<=0.75',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'lineColor("#1FC7FF")',
    'lineColor("#168BFF")',
    'lineWidth((float)(7.4+2.4*wave))',
    'lineWidth((float)(3.0+0.35*wave))',
    'cellCount=new int[96]',
    'candidates.size()>=1200']:
    if marker not in m:
        raise SystemExit('v0.8.30 map marker missing: '+marker)
if 'features.put(pointFeature(' in tick:
    raise SystemExit('moving point/bead flow animation returned')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.30 visible blue core + glow on all actual rivers PASS')
