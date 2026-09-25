from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.82: BIPAD River Watch membership decides whether a station/river is shown.
# Freshness remains reading/safety metadata only; it must never hide a station-bearing river.

# Scope all loader surgery to the trusted loader using stable end marker from v0.8.78.
start=a.find('private List<RiverStation> loadTrustedRiverStationsV862')
if start<0:
    start=a.find('List<RiverStation> loadTrustedRiverStationsV862')
end=a.find('// V0878_RESILIENT_STATION_REFRESH',start)
if start<0 or end<0: raise SystemExit('v0882 trusted loader bounds missing')
end=a.find('\n',end)
if end<0:end=len(a)
loader=a[start:end]

# Add two active-source sets immediately before the BIPAD observation path list.
paths_re=r'(\s*)String\[\]\s+paths\s*=\s*\{"river/\?limit=5000"'
pm=re.search(paths_re,loader)
if not pm: raise SystemExit('v0882 paths declaration missing')
indent=pm.group(1)
sets=(indent+'java.util.LinkedHashSet<String> v882RiverWatchKeys=new java.util.LinkedHashSet<>();\n'
      +indent+'java.util.LinkedHashSet<String> v882TrimedKeys=new java.util.LinkedHashSet<>(); // V0882_BIPAD_ACTIVE_SETS\n')
loader=loader[:pm.start()]+sets+loader[pm.start():]

# Collect membership after a BIPAD row has matched official station metadata and key.
# metadataMatch.put(key,merged) is inside the observation-path loop and therefore has path in scope.
needle='metadataMatch.put(key,merged);'
pos=loader.find(needle)
if pos<0: raise SystemExit('v0882 metadataMatch anchor missing')
pos2=pos+len(needle)
loader=loader[:pos2]+'\n                    if(path.startsWith("river/?"))v882RiverWatchKeys.add(key);else if(path.startsWith("river-trimed/?"))v882TrimedKeys.add(key); // V0882_ACTIVE_BIPAD_MEMBERSHIP'+loader[pos2:]

# Freeze the active set before the DHM enrichment section. Primary truth is river/, fallback river-trimed/.
dhm=loader.find('String[] dhmUrls=')
if dhm<0: raise SystemExit('v0882 DHM anchor missing')
line_start=loader.rfind('\n',0,dhm)+1
active=('        final java.util.LinkedHashSet<String> v882ActiveKeys=!v882RiverWatchKeys.isEmpty()?v882RiverWatchKeys:v882TrimedKeys;\n'
        '        if(v882ActiveKeys.isEmpty())throw new IllegalStateException("BIPAD River Watch returned no active station rows"); // V0882_NO_ZERO_WIPE\n\n')
loader=loader[:line_start]+active+loader[line_start:]

# In the final catalog->RiverStation loop, keep only current BIPAD River Watch members.
# Target the last occurrence because earlier key calculations belong to cache/metadata merges.
needle='String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));'
pos=loader.rfind(needle)
if pos<0: raise SystemExit('v0882 final station key missing')
pos2=pos+len(needle)
loader=loader[:pos2]+'\n            if(!v882ActiveKeys.contains(key))continue; // V0882_ONLY_BIPAD_RIVER_WATCH_ROWS'+loader[pos2:]

# Active River Watch count becomes the display count; 284 remains only the metadata universe internally.
count_marker='v877FreshObservationCount=freshCount;'
pos=loader.rfind(count_marker)
if pos<0: raise SystemExit('v0882 count marker missing')
loader=loader[:pos]+'v849CatalogCount=v882ActiveKeys.size(); // V0882_RIVER_WATCH_COUNT_IS_TRUTH\n        '+loader[pos:]
loader=loader.replace('Math.max(0,catalog.length()-latestCount)','Math.max(0,v849CatalogCount-latestCount)',1)
loader=loader.replace('// V0878_RESILIENT_STATION_REFRESH','// V0882_BIPAD_RIVER_WATCH_DISPLAY_TRUTH',1)
a=a[:start]+loader+a[end:]

# Replace only the visible banner text, leaving the existing method body/counters intact.
a=a.replace('"🌊 आधिकारिक catalog "+v849CatalogCount+" • map मा "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount',
            '"🌊 BIPAD River Watch "+v849CatalogCount+" • map मा "+mapRiverTotal+" • recent reading "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount',1)
a=a.replace('"🌊 Official catalog "+v849CatalogCount+" • mapped "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • no reading "+v877NoObservationCount',
            '"🌊 BIPAD River Watch "+v849CatalogCount+" • mapped "+mapRiverTotal+" • recent reading "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount',1)
# Marker can be independent of exact bilingual string shape.
if 'V0882_RIVER_WATCH_HEADER' not in a:
    marker='private void updateMapHintCounts()'
    p=a.find(marker)
    if p>=0:a=a[:p]+'/* V0882_RIVER_WATCH_HEADER */\n    '+a[p:]

# Critical v0.8.81 regression: remove freshness from station-presence matching.
old='s==null||!s.fresh||!Double.isFinite(s.lat)||!Double.isFinite(s.lon)'
new='s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon)'
if old not in m: raise SystemExit('v0882 fresh-gate anchor missing')
m=m.replace(old,new,1)
m=m.replace('// V0881_LIVE_STATION_MATCH','// V0882_ACTIVE_STATION_RIVER_MATCH',1)

# Version bump after v0.8.81.
g=re.sub(r'versionCode\s+101\b','versionCode 102',g,count=1)
g=g.replace("versionName '0.8.81'","versionName '0.8.82'",1)

for x in ['V0882_BIPAD_ACTIVE_SETS','V0882_ACTIVE_BIPAD_MEMBERSHIP','V0882_NO_ZERO_WIPE','V0882_ONLY_BIPAD_RIVER_WATCH_ROWS','V0882_RIVER_WATCH_COUNT_IS_TRUTH','V0882_BIPAD_RIVER_WATCH_DISPLAY_TRUTH']:
    if x not in a:raise SystemExit('missing '+x)
if 'V0882_ACTIVE_STATION_RIVER_MATCH' not in m:raise SystemExit('missing river matcher contract')
if old in m:raise SystemExit('freshness still hides station-bearing river')
if 'versionCode 102' not in g or "versionName '0.8.82'" not in g:raise SystemExit('v0882 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.82 BIPAD River Watch membership + station-bearing river visibility fix applied')
