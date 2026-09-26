from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')

old='if(!nepal(la,lo))return null;'
new='if(!(Double.isFinite(la)&&Double.isFinite(lo)&&la>=26.2d&&la<=30.5d&&lo>=80.0d&&lo<=88.35d))return null; // V0896_NEPAL_COORD_REPAIR'
if old not in a: raise SystemExit('v0896 compile repair: nepal() anchor missing')
a=a.replace(old,new,1)

old_ctor='return new RiverStation(name,district,basin,id,source,description,river,la,lo,elev,level,warning,danger,rain,at,fresh,stage,rank,raw);'
new_ctor='return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw); // V0896_RIVERSTATION_CTOR_REPAIR'
if old_ctor not in a: raise SystemExit('v0896 compile repair: RiverStation ctor anchor missing')
a=a.replace(old_ctor,new_ctor,1)

# v0.8.79 RiverWay has no status field; v0.8.96 risk overlays need one.
match=re.search(r'(private\s+static\s+final\s+class\s+RiverWay\s*\{)',m)
if not match: raise SystemExit('v0896 compile repair: RiverWay class missing')
if 'V0896_RIVERWAY_STAGE_REPAIR' not in m:
    pos=match.end()
    m=m[:pos]+'\n        String stage="normal"; // V0896_RIVERWAY_STAGE_REPAIR'+m[pos:]

for marker in ['V0896_NEPAL_COORD_REPAIR','V0896_RIVERSTATION_CTOR_REPAIR','V0896_RIVERWAY_STAGE_REPAIR']:
    if marker not in a+m: raise SystemExit('missing '+marker)

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
print('v0.8.96 compile compatibility repair applied')
