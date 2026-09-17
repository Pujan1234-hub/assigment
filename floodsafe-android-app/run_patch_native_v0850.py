from pathlib import Path
import runpy

root = Path(__file__).resolve().parent
p = root / 'patch_native_v0850_official_parity_sathi_language.py'
s = p.read_text(encoding='utf-8')

old = '''old='                String g = s.fresh ? normalizeStage(s.stage) : "stale";'
new='                String g = s.online ? "normal" : "stale"; // V0850_MAP_AVAILABILITY_GROUP'
if old in m:m=m.replace(old,new,1)
elif 'V0850_MAP_AVAILABILITY_GROUP' not in m:raise SystemExit('v0850 stationGeo group anchor')'''
new = '''if 'V0850_MAP_AVAILABILITY_GROUP' not in m:
    pat=r'String\\s+g\\s*=\\s*s\\.fresh\\s*\\?\\s*normalizeStage\\(s\\.stage\\)\\s*:\\s*"stale"\\s*;'
    m,n=re.subn(pat,'String g = s.online ? "normal" : "stale"; // V0850_MAP_AVAILABILITY_GROUP',m,count=1)
    if n!=1: raise SystemExit('v0850 stationGeo group anchor')'''

if old not in s:
    raise SystemExit('v0850 runner could not find strict stationGeo block')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
runpy.run_path(str(p), run_name='__main__')
