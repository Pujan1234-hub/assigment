from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.38 field fix from the user's real-phone video/screenshot:
# 1) National view must cover the WHOLE Nepal OSM overview network, not only the first
#    320 named `river` features. v0.8.37 assets are already strictly Nepal-preclipped,
#    so national rendering can safely publish every overview river/stream in view.
# 2) The in-map river detail close X must never sit under the native +/- zoom controls.
# MAP/UI ONLY. Official source parsing and 2 km Warning/Danger notification logic untouched.

old_national='''                }else{\n                    // National view is context, not a spaghetti plot: real named rivers only.\n                    for(RiverWay r:overviewRivers){\n                        if(r==null||r.points.size()<2||!\"river\".equalsIgnoreCase(r.type))continue;\n                        if(r.name==null||r.name.trim().isEmpty()||\"नदी / खोला\".equals(r.name))continue;\n                        if(!riverIntersectsBox(r,fw,fs,fe,fn))continue;\n                        String k=riverKey(r); if(seen.add(k))candidates.add(copyRiver(r));\n                        if(candidates.size()>=320)break;\n                    }\n                }'''
new_national='''                }else{\n                    // FULL_NEPAL_OVERVIEW: the build assets are already clipped to Nepal.\n                    // Publish every real OSM river/stream in the visible national bounds.\n                    // Do not cap at 320 or filter unnamed streams; those two filters caused\n                    // large parts of Nepal to look blank on the real phone.\n                    for(RiverWay r:overviewRivers){\n                        if(r==null||r.points.size()<2)continue;\n                        if(!riverIntersectsBox(r,fw,fs,fe,fn))continue;\n                        String k=riverKey(r); if(seen.add(k))candidates.add(copyRiver(r));\n                    }\n                }'''
if old_national not in m:
    raise SystemExit('v0.8.38 national 320-cap block missing')
m=m.replace(old_national,new_national,1)

# Keep the detail card clear of the right-side + / - controls. The card remains anchored
# at the bottom, but its right edge stops before the control rail; elevation keeps it crisp.
old_margin='detailLp.setMargins(dp(12),0,dp(12),dp(12));mapHolder.addView(mapDetailPanel,detailLp);'
new_margin='detailLp.setMargins(dp(12),0,dp(72),dp(12));mapDetailPanel.setElevation(dp(14));mapHolder.addView(mapDetailPanel,detailLp);'
if old_margin not in a:
    raise SystemExit('v0.8.38 detail panel margin anchor missing')
a=a.replace(old_margin,new_margin,1)

# Slightly enlarge the X touch target while keeping the visual size compact.
old_x='x.setPadding(dp(10),dp(5),dp(4),dp(5));'
new_x='x.setPadding(dp(12),dp(8),dp(10),dp(8));x.setMinWidth(dp(42));x.setMinHeight(dp(42));'
if old_x in a:
    a=a.replace(old_x,new_x,1)
elif 'x.setMinWidth(dp(42))' not in a:
    raise SystemExit('v0.8.38 close X padding anchor missing')

# Version bump.
g=g.replace('versionCode 57','versionCode 58',1).replace("versionName '0.8.37'","versionName '0.8.38'",1)
if 'versionCode 58' not in g or "versionName '0.8.38'" not in g:
    raise SystemExit('v0.8.38 version bump failed')

# Hard gates for the two user-reported defects.
for marker in [
    'FULL_NEPAL_OVERVIEW',
    'for(RiverWay r:overviewRivers)',
    'candidates.add(copyRiver(r))',
    'detailLp.setMargins(dp(12),0,dp(72),dp(12))',
    'mapDetailPanel.setElevation(dp(14))',
    'x.setMinWidth(dp(42))',
    'PRECLIPPED_BUILD_ASSET',
    'PRECLIPPED_TILE_ASSET']:
    hay=m if marker in ['FULL_NEPAL_OVERVIEW','for(RiverWay r:overviewRivers)','candidates.add(copyRiver(r))','PRECLIPPED_BUILD_ASSET','PRECLIPPED_TILE_ASSET'] else a
    if marker not in hay: raise SystemExit('v0.8.38 marker missing: '+marker)
if 'if(candidates.size()>=320)break;' in m:
    raise SystemExit('v0.8.38 old national 320 river cap remained')

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.38 FULL Nepal rivers + unobstructed close X PASS')
