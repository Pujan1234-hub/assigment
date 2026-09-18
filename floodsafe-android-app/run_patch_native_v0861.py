from pathlib import Path
import re, runpy

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

# Normalize whatever StationDot field layout the earlier map patches produced.
cs=m.find('    private static final class StationDot')
ce=m.find('    private static final class RiverWay',cs)
if cs<0 or ce<0: raise SystemExit('v0861 wrapper StationDot class missing')
block=m[cs:ce]
if 'V0861_MAP_STATION_DETAIL_FIELDS' not in block:
    dm=re.search(r'double\s+([^;]+);',block)
    if not dm: raise SystemExit('v0861 wrapper StationDot double fields missing')
    names=dm.group(1)
    add=[]
    for x in ['warning','danger']:
        if not re.search(r'\b'+x+r'\b',names): add.append(x)
    if add:
        repl='double '+names+', '+', '.join(add)+';'
        block=block[:dm.start()]+repl+block[dm.end():]
    if not re.search(r'\blong\s+at\s*;',block):
        pos=block.find(';',block.find('double '))+1
        block=block[:pos]+' long at;'+block[pos:]
    block=block.replace('    }','        // V0861_MAP_STATION_DETAIL_FIELDS\n    }',1)
    m=m[:cs]+block+m[ce:]

# Carry retained official measurement fields into the map StationDot.
if 'V0861_READ_STATION_DETAIL' not in m:
    anchor='            s.level = getDouble(c, o, "level");'
    if anchor not in m: raise SystemExit('v0861 wrapper readStation level anchor missing')
    m=m.replace(anchor,anchor+'\n            s.warning = getDouble(c, o, "warning"); s.danger = getDouble(c, o, "danger");\n            s.at = getLong(c, o, "at", 0L); // V0861_READ_STATION_DETAIL',1)

m_path.write_text(m,encoding='utf-8')

# Execute the main v0.8.61 patch. The compatibility markers above make its
# StationDot section idempotent across the historical patch chain.
src=root/'patch_native_v0861_map_detail_full_language.py'
runpy.run_path(str(src),run_name='__main__')
