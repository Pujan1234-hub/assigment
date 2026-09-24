from pathlib import Path
p=Path('.github/scripts/patch_floodsafe_v0895_official_mirror_core.py')
s=p.read_text(encoding='utf-8')
old=r'(?:private|public|protected)\s+[^\n;{]*?\b'
new=r'(?:(?:private|public|protected)\s+)?[^\n;{]*?\b'
if old not in s: raise SystemExit('v0895 span visibility anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('V0895_SPAN_VISIBILITY_PREFLIGHT PASS')
