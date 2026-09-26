from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.90 already rewrites the station-only river selector. Remove its distance cutoffs directly:
# every official station must seed a real river geometry. Prefer same-name; otherwise nearest.
old='RiverWay seed=(bestName!=null&&bestNameKm<=25d)?bestName:((bestNear!=null&&bestNearKm<=10d)?bestNear:null);'
new='RiverWay seed=bestName!=null?bestName:bestNear; // V0891_EVERY_STATION_FORCES_NEAREST_REAL_RIVER'
if old not in m:
    raise SystemExit('v0.8.90 river seed expression missing')
m=m.replace(old,new,1)

# Make the station-river source unmistakably visible over satellite imagery.
# These are only the force-visible river layers; no data/Supabase/UI/alert logic changes.
changed=0
m,n=re.subn(r'lineColor\("#00bfe8"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)',
            'lineColor("#00c8ff"),lineWidth(9.0f),lineOpacity(0.50f)',m,count=1); changed+=n
m,n=re.subn(r'lineColor\("#46e8ff"\),lineWidth\([0-9.]+f\),lineOpacity\([0-9.]+f\)',
            'lineColor("#68efff"),lineWidth(3.8f),lineOpacity(1.0f)',m,count=1); changed+=n
if changed<2:
    raise SystemExit('force river glow/core layers missing')

# Re-assert force-visible layers shortly after station-driven geometry refresh.
anchor='v879RefreshRiverGeometryForCamera();'
if anchor not in m:
    raise SystemExit('station river refresh anchor missing')
# Add only once and only to the first station-refresh occurrence.
if 'V0891_FORCE_LAYER_AFTER_STATION_REFRESH' not in m:
    m=m.replace(anchor,anchor+'\n        main.postDelayed(this::v886EnsureRiverVisibility, 250L); // V0891_FORCE_LAYER_AFTER_STATION_REFRESH',1)

# Version bump only.
g=re.sub(r'versionCode\s+110\b','versionCode 111',g,count=1)
g=g.replace("versionName '0.8.90'","versionName '0.8.91'",1)

for token in ['V0891_EVERY_STATION_FORCES_NEAREST_REAL_RIVER','V0891_FORCE_LAYER_AFTER_STATION_REFRESH']:
    if token not in m: raise SystemExit('missing '+token)
if 'lineWidth(9.0f),lineOpacity(0.50f)' not in m or 'lineWidth(3.8f),lineOpacity(1.0f)' not in m:
    raise SystemExit('force flow/glow styling missing')
if "versionName '0.8.91'" not in g or 'versionCode 111' not in g:
    raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.91 PASS: station river cutoff removed + forced cyan river glow/core')
