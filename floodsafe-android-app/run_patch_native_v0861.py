from pathlib import Path
import re, runpy

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
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

# Historical v0.8.36+ uses compact showRiver signature and keeps same-river/rain
# helpers immediately after it. Adapt only the patch anchors; preserve those helpers.
src=root/'patch_native_v0861_map_detail_full_language.py'
tmp=root/'_patch_native_v0861_runtime.py'
s=src.read_text(encoding='utf-8')
s=s.replace("'    private void showRiver(RiverWay r, double la, double lo) {'","'    private void showRiver(RiverWay r,double la,double lo) {'",1)
s=s.replace("'    private void startParticles() {'","'    private StationDot sameRiverGaugeFor('",1)
tmp.write_text(s,encoding='utf-8')
try:
    runpy.run_path(str(tmp),run_name='__main__')
finally:
    try: tmp.unlink()
    except Exception: pass

# v0.8.59 inserted this helper call outside applyLanguage(). The v0.8.61 full
# language method replaces the old helper, so route every leftover call to the
# new helper as well. This is language-only and does not alter river/safety logic.
a=a_path.read_text(encoding='utf-8')
a=a.replace('v0859RefreshStaticText(root);','v0861RefreshStaticText(root);')
if 'v0859RefreshStaticText(root);' in a:
    raise SystemExit('v0861 stale language helper reference remains')
a_path.write_text(a,encoding='utf-8')
