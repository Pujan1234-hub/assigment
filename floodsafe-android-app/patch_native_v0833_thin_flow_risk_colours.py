from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.33 MAP-ONLY field fix requested from real phone screenshot:
# - every real Nepal river/khola should retain a thin, attractive blue flow/glow effect;
# - if the official CURRENT same-river gauge is alert/warning/danger, that matched river
#   segment changes to yellow/orange/red respectively;
# - if the first viewport selection is empty, fall back to the real bundled overview waterways
#   and still clip them through the existing Nepal district-union clip;
# - never restore moving white dots;
# - do not touch alert/notification/2km safety logic.

# 1) Do not allow a temporary/empty candidate selection to leave the national map blank.
old='List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);'
new='''List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);\n                if(chosen.isEmpty()&&!overviewRivers.isEmpty()){\n                    chosen=clipWaysToNepalDense(new ArrayList<>(overviewRivers),nepal);\n                }'''
if old in m:
    m=m.replace(old,new,1)
elif 'if(chosen.isEmpty()&&!overviewRivers.isEmpty())' not in m:
    raise SystemExit('v0.8.33 Nepal river fallback anchor missing')

# 2) Keep the geographic network thin and crisp instead of a heavy neon band.
m=m.replace('lineColor("#1FC7FF"), lineWidth(3.15f), lineOpacity(1.0f)',
            'lineColor("#24C7FF"), lineWidth(2.05f), lineOpacity(0.98f)',1)
m=m.replace('lineColor("#168BFF"), lineWidth(8.2f), lineOpacity(0.34f)',
            'lineColor("#168BFF"), lineWidth(5.0f), lineOpacity(0.30f)',1)

# 3) Restore semantic current-river colours. Base rivers remain blue; only a CURRENT matched
# same-river status overlay changes colour.
for old_call,new_call in [
    ('ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#168BFF");',
     'ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#24C7FF");'),
    ('ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#168BFF");',
     'ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#FFD447");'),
    ('ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#168BFF");',
     'ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#FF9418");'),
    ('ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#168BFF");',
     'ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#F04444");')]:
    if old_call in m:
        m=m.replace(old_call,new_call,1)
    elif new_call not in m:
        raise SystemExit('v0.8.33 status colour anchor missing: '+old_call)

# 4) Thin blue breathing flow on ALL actual clipped Nepal waterways; status glow follows
# official CURRENT status colours on matched segments.
old_tick='''                LineLayer baseGlow=style.getLayerAs("fs-river-glow");
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
                }'''
new_tick='''                LineLayer baseGlow=style.getLayerAs("fs-river-glow");
                if(baseGlow!=null)baseGlow.setProperties(
                        lineColor("#168BFF"),
                        lineOpacity((float)(0.24+0.16*wave)),
                        lineWidth((float)(4.2+1.25*wave)));
                LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
                if(baseCore!=null)baseCore.setProperties(
                        lineColor("#24C7FF"),
                        lineOpacity((float)(0.90+0.10*wave)),
                        lineWidth((float)(1.85+0.35*wave)));

                // Official CURRENT same-river segments use risk colour + slightly stronger pulse.
                String[] ids={"fs-river-normal-status-layer-glow","fs-river-alert-status-layer-glow",
                              "fs-river-warning-status-layer-glow","fs-river-danger-status-layer-glow"};
                String[] colors={"#24C7FF","#FFD447","#FF9418","#F04444"};
                float[] widths={5.6f,6.2f,7.0f,7.8f};
                for(int i=0;i<ids.length;i++){
                    LineLayer glow=style.getLayerAs(ids[i]);
                    if(glow!=null)glow.setProperties(
                            lineColor(colors[i]),
                            lineOpacity((float)(0.40+0.25*wave)),
                            lineWidth(widths[i]+(float)(1.1*wave)));
                }'''
if old_tick in m:
    m=m.replace(old_tick,new_tick,1)
elif 'String[] colors={"#24C7FF","#FFD447","#FF9418","#F04444"};' not in m:
    raise SystemExit('v0.8.33 flow tick anchor missing')

# 5) More repaint retries for devices where waterways finish loading after style creation.
seq='main.postDelayed(this::refreshVisibleRiverTiles,350L);main.postDelayed(this::refreshVisibleRiverTiles,1200L);main.postDelayed(this::refreshVisibleRiverTiles,3000L);main.postDelayed(this::refreshVisibleRiverTiles,5200L);'
seq2=seq+'main.postDelayed(this::refreshVisibleRiverTiles,8000L);'
if seq in m and '8000L' not in m:
    m=m.replace(seq,seq2,1)

# Version bump only.
g=g.replace('versionCode 52','versionCode 53',1).replace("versionName '0.8.32'","versionName '0.8.33'",1)
if 'versionCode 53' not in g or "versionName '0.8.33'" not in g:
    raise SystemExit('v0.8.33 version bump failed')

# Hard gates: attractive map changes only, safety rules untouched.
for marker in [
    'if(chosen.isEmpty()&&!overviewRivers.isEmpty())',
    'clipWaysToNepalDense(new ArrayList<>(overviewRivers),nepal)',
    'lineColor("#24C7FF")',
    'lineWidth((float)(4.2+1.25*wave))',
    'lineWidth((float)(1.85+0.35*wave))',
    'String[] colors={"#24C7FF","#FFD447","#FF9418","#F04444"};',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'sameRiverGaugeFor',
    'routeD<=0.75']:
    if marker not in m:
        raise SystemExit('v0.8.33 map marker missing: '+marker)
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a:
        raise SystemExit('alert safety changed unexpectedly: '+marker)
if 'viewportInsideNepalStrict(fw,fs,fe,fn,nepal)?copyWaysExact(candidates)' in m:
    raise SystemExit('unsafe foreign-country bypass returned')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.33 thin Nepal-wide blue flow + official risk-colour river overlays PASS')
