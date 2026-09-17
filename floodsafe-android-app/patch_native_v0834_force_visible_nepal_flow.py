from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.34 MAP-ONLY field fix from the real-phone screenshot:
# v0.8.33 had the right styling code, but fs-rivers could stay empty because v0.8.31
# creates the source empty before bundled geometry finishes loading. installGeoLayers()
# then sees the existing source and does not republish riversGeoJson. This patch fixes the
# actual data-to-layer publication path, not just the styling.
# Alerts / notifications / 2 km emergency safety are deliberately untouched.

# 1) Make the bundled national network Nepal-safe before publishing it.
old='''                    rivers.clear();\n                    rivers.addAll(all);\n                    riversGeoJson = makeRiversGeoJson(all);'''
new='''                    // Publish only geometry clipped to Nepal district polygons.\n                    List<RiverWay> safeAll=all;\n                    try{\n                        if(districtGeoJson!=null){\n                            JSONObject nepalRoot=new JSONObject(districtGeoJson);\n                            List<RiverWay> clipped=clipWaysToNepalDense(all,nepalRoot);\n                            if(clipped!=null&&!clipped.isEmpty())safeAll=clipped;\n                        }\n                    }catch(Exception ignoredClip){}\n                    rivers.clear();\n                    rivers.addAll(safeAll);\n                    riversGeoJson = makeRiversGeoJson(safeAll);'''
if old in m:
    m=m.replace(old,new,1)
elif 'List<RiverWay> safeAll=all;' not in m:
    raise SystemExit('v0.8.34 bundled geometry publish anchor missing')

# 2) Critical bug fix: once async bundled geometry is ready, explicitly populate the already-
# existing fs-rivers source. Do not rely on installGeoLayers() recreating that source.
old_post='main.post(this::installGeoLayers);'
new_post='''main.post(()->{\n                installGeoLayers();\n                if(riversGeoJson!=null&&!riversGeoJson.isEmpty())setGeo("fs-rivers",riversGeoJson);\n                refreshRiverStatusSources();\n                main.removeCallbacks(particleTick);\n                if(animationRunning)main.post(particleTick);\n                main.postDelayed(this::refreshVisibleRiverTiles,700L);\n            });'''
if old_post in m:
    m=m.replace(old_post,new_post,1)
elif 'if(riversGeoJson!=null&&!riversGeoJson.isEmpty())setGeo("fs-rivers",riversGeoJson);' not in m:
    raise SystemExit('v0.8.34 async source republish anchor missing')

# 3) If a viewport tile selection is temporarily empty, retain the already loaded safe national
# network instead of clearing the source again.
anchor='''                if(chosen.isEmpty()&&!overviewRivers.isEmpty()){\n                    chosen=clipWaysToNepalDense(new ArrayList<>(overviewRivers),nepal);\n                }'''
extra=anchor+'''\n                if(chosen.isEmpty()&&!rivers.isEmpty()){\n                    chosen=new ArrayList<>(rivers);\n                }'''
if anchor in m and 'if(chosen.isEmpty()&&!rivers.isEmpty())' not in m:
    m=m.replace(anchor,extra,1)
elif 'if(chosen.isEmpty()&&!rivers.isEmpty())' not in m:
    raise SystemExit('v0.8.34 nonblank fallback anchor missing')

# 4) Make the all-river effect unmistakably visible but still thin/clean on satellite imagery.
m=m.replace('lineColor("#24C7FF"), lineWidth(2.05f), lineOpacity(0.98f)',
            'lineColor("#22C8FF"), lineWidth(2.20f), lineOpacity(1.0f)',1)
m=m.replace('lineColor("#168BFF"), lineWidth(5.0f), lineOpacity(0.30f)',
            'lineColor("#0D8DFF"), lineWidth(5.6f), lineOpacity(0.34f)',1)

# 5) Replace the v0.8.33 pulse with a clear thin breathing-flow effect on every actual Nepal
# waterway. Current official risk overlays get semantic colours and a stronger pulse.
old_tick='''                LineLayer baseGlow=style.getLayerAs("fs-river-glow");\n                if(baseGlow!=null)baseGlow.setProperties(\n                        lineColor("#168BFF"),\n                        lineOpacity((float)(0.24+0.16*wave)),\n                        lineWidth((float)(4.2+1.25*wave)));\n                LineLayer baseCore=style.getLayerAs("fs-rivers-layer");\n                if(baseCore!=null)baseCore.setProperties(\n                        lineColor("#24C7FF"),\n                        lineOpacity((float)(0.90+0.10*wave)),\n                        lineWidth((float)(1.85+0.35*wave)));\n\n                // Official CURRENT same-river segments use risk colour + slightly stronger pulse.\n                String[] ids={"fs-river-normal-status-layer-glow","fs-river-alert-status-layer-glow",\n                              "fs-river-warning-status-layer-glow","fs-river-danger-status-layer-glow"};\n                String[] colors={"#24C7FF","#FFD447","#FF9418","#F04444"};\n                float[] widths={5.6f,6.2f,7.0f,7.8f};\n                for(int i=0;i<ids.length;i++){\n                    LineLayer glow=style.getLayerAs(ids[i]);\n                    if(glow!=null)glow.setProperties(\n                            lineColor(colors[i]),\n                            lineOpacity((float)(0.40+0.25*wave)),\n                            lineWidth(widths[i]+(float)(1.1*wave)));\n                }'''
new_tick='''                LineLayer baseGlow=style.getLayerAs("fs-river-glow");\n                if(baseGlow!=null)baseGlow.setProperties(\n                        lineColor("#0D8DFF"),\n                        lineOpacity((float)(0.26+0.22*wave)),\n                        lineWidth((float)(4.7+1.7*wave)));\n                LineLayer baseCore=style.getLayerAs("fs-rivers-layer");\n                if(baseCore!=null)baseCore.setProperties(\n                        lineColor("#22C8FF"),\n                        lineOpacity((float)(0.90+0.10*wave)),\n                        lineWidth((float)(1.95+0.55*wave)));\n\n                // Official CURRENT same-river segments: status colour on both core and halo.\n                String[] glowIds={"fs-river-normal-status-layer-glow","fs-river-alert-status-layer-glow",\n                                  "fs-river-warning-status-layer-glow","fs-river-danger-status-layer-glow"};\n                String[] coreIds={"fs-river-normal-status-layer","fs-river-alert-status-layer",\n                                  "fs-river-warning-status-layer","fs-river-danger-status-layer"};\n                String[] colors={"#22C8FF","#FFD447","#FF9418","#F04444"};\n                float[] glowWidths={5.7f,6.5f,7.5f,8.6f};\n                float[] coreWidths={2.3f,2.7f,3.1f,3.5f};\n                for(int i=0;i<glowIds.length;i++){\n                    LineLayer glow=style.getLayerAs(glowIds[i]);\n                    if(glow!=null)glow.setProperties(\n                            lineColor(colors[i]),\n                            lineOpacity((float)(0.44+0.30*wave)),\n                            lineWidth(glowWidths[i]+(float)(1.35*wave)));\n                    LineLayer core=style.getLayerAs(coreIds[i]);\n                    if(core!=null)core.setProperties(\n                            lineColor(colors[i]),\n                            lineOpacity(1.0f),\n                            lineWidth(coreWidths[i]+(float)(0.35*wave)));\n                }'''
if old_tick in m:
    m=m.replace(old_tick,new_tick,1)
elif 'String[] coreIds={"fs-river-normal-status-layer"' not in m:
    raise SystemExit('v0.8.34 flow/risk pulse anchor missing')

# Risk layer declarations must retain semantic colours.
for old_call,new_call in [
    ('ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#24C7FF");',
     'ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#22C8FF");'),
    ('ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#FFD447");',
     'ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#FFD447");'),
    ('ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#FF9418");',
     'ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#FF9418");'),
    ('ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#F04444");',
     'ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#F04444");')]:
    if old_call in m and old_call!=new_call:m=m.replace(old_call,new_call,1)

# Version bump only.
g=g.replace('versionCode 53','versionCode 54',1).replace("versionName '0.8.33'","versionName '0.8.34'",1)
if 'versionCode 54' not in g or "versionName '0.8.34'" not in g:
    raise SystemExit('v0.8.34 version bump failed')

# Hard gates: actual map pipeline fixed; no alert/notification behaviour changed.
for marker in [
    'List<RiverWay> safeAll=all;',
    'if(riversGeoJson!=null&&!riversGeoJson.isEmpty())setGeo("fs-rivers",riversGeoJson);',
    'if(chosen.isEmpty()&&!rivers.isEmpty())',
    'lineColor("#22C8FF")',
    'lineWidth((float)(4.7+1.7*wave))',
    'String[] coreIds={"fs-river-normal-status-layer"',
    'String[] colors={"#22C8FF","#FFD447","#FF9418","#F04444"};',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'sameRiverGaugeFor',
    'routeD<=0.75']:
    if marker not in m: raise SystemExit('v0.8.34 marker missing: '+marker)
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a: raise SystemExit('alert safety changed unexpectedly: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.34 FORCE visible Nepal river flow + official risk colours PASS')
