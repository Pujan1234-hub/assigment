from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

old='RiverWay seed=bestName!=null?bestName:bestAny;if(seed==null)continue;chosen.add(seed);'
new='RiverWay seed=(bestName!=null&&dn<=6d)?bestName:bestAny; // V0898_PROVEN_LOCAL_RIVER_SEED\n                    if(seed==null)continue;chosen.add(seed);'
if old not in m: raise SystemExit('v0898 seed selector anchor missing')
m=m.replace(old,new,1)

# Keep the exact local-tile method and guaranteed native canvas renderer from v0.8.96.
for token in ['V0896_EXACT_LOCAL_TILE_STATION_RIVERS','V0896_NATIVE_CANVAS_FLOW_GLOW_GUARANTEE','V0898_PROVEN_LOCAL_RIVER_SEED']:
    if token not in m: raise SystemExit('missing '+token)

g=re.sub(r'versionCode\s+117\b','versionCode 118',g,count=1)
g=g.replace("versionName '0.8.97'","versionName '0.8.98'",1)
if "versionName '0.8.98'" not in g or 'versionCode 118' not in g: raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.98 PASS: same-name only when within 6 km; otherwise nearest exact local river seed')
