from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.22 screenshot-driven fix:
# 1) remove the invalid multi-district "holes" mask that produced the black diagonal band;
# 2) at local zoom, keep the exact OSM tile geometry untouched instead of re-clipping each
#    river against 77 separate district polygons (which can erase/fragment urban streams);
# 3) make the actual local river core/glow unmistakable over satellite imagery.

# Remove the v0.8.20 outside-mask install block entirely. River geometry itself is still
# restricted to Nepal source tiles / Nepalish coordinates, so a visual cover layer is not needed.
mask_pat=r'''\s*if \(districtGeoJson != null && style\.getSource\("fs-nepal-outside-mask"\) == null\) \{\n\s*String mask=makeNepalOutsideMask\(districtGeoJson\);\n\s*style\.addSource\(new GeoJsonSource\("fs-nepal-outside-mask", mask\)\);\n\s*style\.addLayer\(new FillLayer\("fs-nepal-outside-mask-layer", "fs-nepal-outside-mask"\)\.withProperties\(\n\s*fillColor\("#071821"\), fillOpacity\(1\.0f\)\)\);\n\s*\}\n'''
m,n=re.subn(mask_pat,'\n            // v0.8.22: invalid outside-mask removed; exact river geometry remains Nepal-sourced.\n',m,count=1)
if n!=1 and 'fs-nepal-outside-mask-layer' in m:
    raise SystemExit('v0.8.22 could not remove broken Nepal mask install block')

# Do not run the 77-district polygon clipping pass on local tile routes. The local tile geometry
# already comes from the bundled Nepal waterway snapshot and is the actual OSM channel shape.
old='''                if(districtGeoJson!=null){
                    try{JSONObject clipRoot=new JSONObject(districtGeoJson);List<RiverWay> clipped=new ArrayList<>();for(RiverWay rr:chosen){trimRiverToNepal(rr,clipRoot);if(rr.points.size()>=2)clipped.add(rr);}chosen=clipped;}catch(Exception ignored){}
                }'''
new='''                if(districtGeoJson!=null && zoom<8.0){
                    try{JSONObject clipRoot=new JSONObject(districtGeoJson);List<RiverWay> clipped=new ArrayList<>();for(RiverWay rr:chosen){trimRiverToNepal(rr,clipRoot);if(rr.points.size()>=2)clipped.add(rr);}chosen=clipped;}catch(Exception ignored){}
                }'''
if old in m:
    m=m.replace(old,new,1)
elif new not in m:
    raise SystemExit('v0.8.22 local clip anchor missing')

# Stronger local visibility over Esri satellite, without changing status semantics.
m=re.sub(r'lineColor\("#003a4b"\), lineWidth\([0-9.]+f\), lineOpacity\([0-9.]+f\)',
         'lineColor("#003a4b"), lineWidth(7.0f), lineOpacity(0.90f)',m,count=1)
m=re.sub(r'lineColor\("#22e7ff"\), lineWidth\([0-9.]+f\), lineOpacity\([0-9.]+f\)',
         'lineColor("#22e7ff"), lineWidth(3.2f), lineOpacity(1.0f)',m,count=1)
# Trace remains subtle but visible.
m=re.sub(r'lineColor\("#8ff7ff"\), lineWidth\([0-9.]+f\), lineOpacity\([0-9.]+f\)',
         'lineColor("#8ff7ff"), lineWidth(1.35f), lineOpacity(0.55f)',m,count=1)

# Version bump.
if "versionName '0.8.22'" not in g:
    g=g.replace('versionCode 41','versionCode 42',1)
    g=g.replace("versionName '0.8.21'","versionName '0.8.22'",1)
if 'versionCode 42' not in g or "versionName '0.8.22'" not in g:
    raise SystemExit('v0.8.22 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

h=m_path.read_text(encoding='utf-8')
for marker in [
    'zoom>=10.0?candidates.size():Math.min(zoom>=8.0?900:320,candidates.size())',
    'districtGeoJson!=null && zoom<8.0',
    'lineColor("#22e7ff"), lineWidth(3.2f), lineOpacity(1.0f)',
    'lineColor("#003a4b"), lineWidth(7.0f), lineOpacity(0.90f)',
    'sameRiverGaugeFor','fs-river-danger-status-layer']:
    if marker not in h: raise SystemExit('v0.8.22 marker missing: '+marker)
if 'style.addLayer(new FillLayer("fs-nepal-outside-mask-layer"' in h:
    raise SystemExit('broken black outside mask still installed')
print('FloodSafe v0.8.22 black-mask removal + visible exact local rivers PASS')
