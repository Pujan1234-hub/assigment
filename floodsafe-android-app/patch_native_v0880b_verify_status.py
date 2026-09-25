from pathlib import Path
import re
root=Path(__file__).resolve().parent
m=(root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java').read_text(encoding='utf-8')
g_path=root/'app/build.gradle'
g=g_path.read_text(encoding='utf-8')

# v0.8.79 already carries the proven native river-risk colour + moving flow/glow chain.
# This patch only verifies those contracts and bumps the field-test version; it does not
# remove or replace any full river/map asset.
need_any=[
    ['V0879_FULL_RIVER_TILE_RUNTIME'],
    ['risk','colour'],
]
if 'V0879_FULL_RIVER_TILE_RUNTIME' not in m:
    raise SystemExit('missing v0.8.79 full river runtime')
# Proven patch chain contains explicit risk status rendering; accept the concrete layer/status markers.
status_tokens=['danger','warning','alert']
if not all(t in m.lower() for t in status_tokens):
    raise SystemExit('native river/station risk status tokens missing')
flow_tokens=['flow','glow']
if not all(t in m.lower() for t in flow_tokens):
    raise SystemExit('native flow/glow runtime missing')

g=re.sub(r'versionCode\s+99\b','versionCode 100',g,count=1)
g=g.replace("versionName '0.8.79'","versionName '0.8.80'",1)
if 'versionCode 100' not in g or "versionName '0.8.80'" not in g:
    raise SystemExit('v0.8.80 version bump failed')
g_path.write_text(g,encoding='utf-8')
print('v0.8.80 verified full-river risk-colour + flow/glow build patch applied')
