from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.97: the 284-station official inventory is the geometry roster.
# v0.8.82 additionally required exact equality with a separately-normalized active-key set,
# which cut valid catalogue rows (e.g. header 284, map 139). Fresh/current observations still
# control status colours and alerts; they no longer control whether a station/river exists on map.
old='            if(!v882ActiveKeys.contains(key))continue; // V0882_ONLY_BIPAD_RIVER_WATCH_ROWS\n            '
if old not in a:
    # tolerate formatting changes in final patched source
    a,n=re.subn(r'\s*if\s*\(\s*!v882ActiveKeys\.contains\(key\)\s*\)\s*continue;\s*// V0882_ONLY_BIPAD_RIVER_WATCH_ROWS\s*','\n            // V0897_FULL_CATALOG_MAP_ROSTER: no second key gate; catalogue row stays on map.\n            ',a,count=1)
    if n==0: raise SystemExit('v0897 active-key final-loop gate missing')
else:
    a=a.replace(old,'            // V0897_FULL_CATALOG_MAP_ROSTER: no second key gate; catalogue row stays on map.\n            ',1)

# Header truth should describe the roster actually sent to map, not the size of the differently-keyed endpoint set.
a=a.replace('v849CatalogCount=v882ActiveKeys.size(); // V0882_RIVER_WATCH_COUNT_IS_TRUTH','v849CatalogCount=catalog.length(); // V0897_CATALOG_ROSTER_COUNT_IS_TRUTH',1)
if 'V0897_CATALOG_ROSTER_COUNT_IS_TRUTH' not in a:
    raise SystemExit('v0897 catalog count anchor missing')

# Do not allow metadata-only/no-reading rows to be omitted: parseStation decides stale/grey, but coordinates remain.
if 'out.add(s);if(s.fresh)freshCount++' not in a:
    raise SystemExit('v0897 expected catalog out.add anchor missing')

g=re.sub(r'versionCode\s+116\b','versionCode 117',g,count=1)
g=g.replace("versionName '0.8.96'","versionName '0.8.97'",1)

for token in ['V0897_FULL_CATALOG_MAP_ROSTER','V0897_CATALOG_ROSTER_COUNT_IS_TRUTH']:
    if token not in a: raise SystemExit('missing '+token)
if 'V0882_ONLY_BIPAD_RIVER_WATCH_ROWS' in a: raise SystemExit('old key gate still present')
if "versionName '0.8.97'" not in g or 'versionCode 117' not in g: raise SystemExit('version bump failed')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.97 PASS: complete official station catalogue remains in map/river geometry roster; readings only affect status')
