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
# 1) National view must cover the WHOLE Nepal OSM overview network. v0.8.29 still
#    sampled/capped the national network to a balanced <=1200 subset; on a phone that
#    leaves real rivers/streams missing. v0.8.37 assets are already strictly Nepal-preclipped,
#    so national rendering can safely publish every overview river/stream in view.
# 2) The in-map river detail close X must never sit under the native +/- zoom controls.
# MAP/UI ONLY. Official source parsing and 2 km Warning/Danger notification logic untouched.

old_dense=r'''                }else{
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
old_legacy=r'''                }else{
                    // National view is context, not a spaghetti plot: real named rivers only.
                    for(RiverWay r:overviewRivers){
                        if(r==null||r.points.size()<2||!"river".equalsIgnoreCase(r.type))continue;
                        if(r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name))continue;
                        if(!riverIntersectsBox(r,fw,fs,fe,fn))continue;
                        String k=riverKey(r); if(seen.add(k))candidates.add(copyRiver(r));
                        if(candidates.size()>=320)break;
                    }
                }
'''
new_national=r'''                }else{
                    // FULL_NEPAL_OVERVIEW: build assets are already clipped to Nepal.
                    // Publish EVERY real OSM river/stream in the visible national bounds.
                    // No count cap, no named-only filter, no river-only filter.
                    for(RiverWay src:overviewRivers){
                        if(src==null||src.points.size()<2||!riverIntersectsBox(src,fw,fs,fe,fn))continue;
                        String k=riverKey(src);if(seen.add(k))candidates.add(copyRiverStrict(src));
                    }
                }
'''
if old_dense in m:
    m=m.replace(old_dense,new_national,1)
elif old_legacy in m:
    m=m.replace(old_legacy,new_national,1)
else:
    raise SystemExit('v0.8.38 current national selector block missing')

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
    'for(RiverWay src:overviewRivers)',
    'candidates.add(copyRiverStrict(src))',
    'detailLp.setMargins(dp(12),0,dp(72),dp(12))',
    'mapDetailPanel.setElevation(dp(14))',
    'x.setMinWidth(dp(42))',
    'PRECLIPPED_BUILD_ASSET',
    'PRECLIPPED_TILE_ASSET']:
    hay=m if marker in ['FULL_NEPAL_OVERVIEW','for(RiverWay src:overviewRivers)','candidates.add(copyRiverStrict(src))','PRECLIPPED_BUILD_ASSET','PRECLIPPED_TILE_ASSET'] else a
    if marker not in hay: raise SystemExit('v0.8.38 marker missing: '+marker)
for old_marker in ['cellCount=new int[96]','candidates.size()>=1100','candidates.size()>=1200','if(candidates.size()>=320)break;']:
    if old_marker in m: raise SystemExit('v0.8.38 old national sampling/cap remained: '+old_marker)

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.38 FULL Nepal rivers + unobstructed close X PASS')
