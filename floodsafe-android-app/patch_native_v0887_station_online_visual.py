from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Visual station availability is separate from safety freshness.
# If a station carries a real official water-level value it is visually online/green.
# The underlying s.fresh flag remains untouched and continues to protect safety logic.
pat=re.compile(r'String\s+g\s*=\s*[^;]+;')
span_start=m.find('private static String stationGeo(')
if span_start<0: raise SystemExit('stationGeo method missing')
span_end=m.find('private static JSONObject pointFeature',span_start)
if span_end<0: raise SystemExit('stationGeo end anchor missing')
region=m[span_start:span_end]
region2,n=pat.subn('String g = Double.isFinite(s.level) ? normalizeStage(s.stage) : "stale"; // V0887_VISUAL_ONLINE_READING',region,count=1)
if n==0: raise SystemExit('stationGeo group assignment missing')
m=m[:span_start]+region2+m[span_end:]

# Normal/available station dots are green; unavailable/no-reading dots stay dark grey.
m=re.sub(r'(ensurePointSource\("fs-stale"\s*,\s*"fs-stale-layer"\s*,\s*)"#[0-9A-Fa-f]+"',r'\1"#59636d"',m,count=1)
m=re.sub(r'(ensurePointSource\("fs-normal"\s*,\s*"fs-normal-layer"\s*,\s*)"#[0-9A-Fa-f]+"',r'\1"#16a36a"',m,count=1)

# River/safety freshness must remain strict and independent from visual station colour.
if 'boolean fresh' not in m or 's.fresh' not in m:
    raise SystemExit('freshness field/logic missing')

anchor='    private static String stationGeo(List<StationDot> list, String group) {'
if 'V0887_STATION_AVAILABILITY_SEPARATED_FROM_SAFETY' not in m:
    if anchor not in m: raise SystemExit('stationGeo exact anchor missing')
    m=m.replace(anchor,'    // V0887_STATION_AVAILABILITY_SEPARATED_FROM_SAFETY: green=has official reading, grey=no reading; safety still uses fresh.\n'+anchor,1)

# Bump app version after v0.8.86 patch.
g=re.sub(r'versionCode\s+106\b','versionCode 107',g,count=1)
g=g.replace("versionName '0.8.86'","versionName '0.8.87'",1)

for token in ['V0887_VISUAL_ONLINE_READING','V0887_STATION_AVAILABILITY_SEPARATED_FROM_SAFETY','"#16a36a"','"#59636d"']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.87'" not in g or 'versionCode 107' not in g:
    raise SystemExit('version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.87 PASS: official-reading stations green; no-reading stations grey; safety freshness preserved')
