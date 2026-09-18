from pathlib import Path
import runpy

root=Path(__file__).resolve().parent
src=root/'patch_native_v0861_map_detail_full_language.py'
tmp=root/'_patch_native_v0861_runtime.py'
s=src.read_text(encoding='utf-8')
old="old='Object original; String name, stage; double lat, lon, level; boolean fresh, online;'"
new="old='Object original; String name, stage, rawStatus; double lat, lon, level; boolean fresh, online;'"
if old not in s:
    raise SystemExit('v0861 wrapper StationDot source anchor missing')
s=s.replace(old,new,1)
tmp.write_text(s,encoding='utf-8')
try:
    runpy.run_path(str(tmp),run_name='__main__')
finally:
    try: tmp.unlink()
    except Exception: pass
