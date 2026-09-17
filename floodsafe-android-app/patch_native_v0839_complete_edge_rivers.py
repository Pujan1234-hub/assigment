from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.39 real-phone regional coverage fix:
# v0.8.38 kept the lightweight overview but delayed dense visible OSM tiles until zoom 7.8.
# On the user's regional view this exposed sparse parts of the old overview in far-west/east.
# The build now also creates a spatially balanced overview. Restore detailed visible-tile merge
# earlier (7.15, the proven v0.8.35 regional threshold) while retaining overview as the base.
# Dense tiles are local assets and were preclipped in CI, so there is no phone-side polygon clip.
# Official BIPAD/DHM values and 2 km fresh Warning/Danger alert logic are untouched.

old='''                if(zoom>=7.8){\n                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){'''
new='''                if(zoom>=7.15){ // V0839_EARLY_REGIONAL_DETAIL\n                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){'''
if old not in m:
    raise SystemExit('v0.8.39 v0.8.38 detail threshold anchor missing')
m=m.replace(old,new,1)

# Preserve the popup close-button fix from v0.8.38; fail rather than silently regress it.
for marker in [
    'detailLp.setMargins(dp(12),0,dp(78),dp(12))',
    'mapDetailPanel.setElevation(dp(14))',
    'x.setMinWidth(dp(42))',
    'x.setMinHeight(dp(42))']:
    if marker not in a:
        raise SystemExit('v0.8.39 popup close fix missing: '+marker)

# Version bump.
g=g.replace('versionCode 58','versionCode 59',1).replace("versionName '0.8.38'","versionName '0.8.39'",1)
if 'versionCode 59' not in g or "versionName '0.8.39'" not in g:
    raise SystemExit('v0.8.39 version bump failed')

# Safety/renderer gates.
for marker in [
    'FULL_NEPAL_OVERVIEW',
    'FULL_NEPAL_DETAIL_MERGE',
    'PRECLIPPED_RENDER_DIRECT',
    'V0839_EARLY_REGIONAL_DETAIL',
    'for(RiverWay r:overviewRivers)',
    'for(RiverWay r:v835ReadRiverTile(x,y))',
    'PRECLIPPED_BUILD_ASSET',
    'PRECLIPPED_TILE_ASSET']:
    if marker not in m:
        raise SystemExit('v0.8.39 river marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.39 balanced overview + earlier regional detailed rivers PASS')
