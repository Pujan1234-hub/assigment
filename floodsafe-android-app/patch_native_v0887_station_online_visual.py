from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Visual availability must not be the same thing as safety freshness.
# A station with a real official water-level observation is visually online even if that
# observation is older than the strict safety freshness window. Safety/risk code continues
# to use s.fresh unchanged.
old='String g = s.fresh ? normalizeStage(s.stage) : "stale";'
new='String g = s.fresh ? normalizeStage(s.stage) : (Double.isFinite(s.level) ? "normal" : "stale"); // V0887_VISUAL_ONLINE_READING'
if old not in m:
    raise SystemExit('stationGeo freshness expression missing')
m=m.replace(old,new,1)

# Normal/available station dots are green; unavailable/no-reading dots stay dark grey.
m=m.replace('ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5"', 'ensurePointSource("fs-stale", "fs-stale-layer", "#59636d"',1)
m=m.replace('ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff"', 'ensurePointSource("fs-normal", "fs-normal-layer", "#16a36a"',1)

# Preserve strict safety truth in river detail: stale readings never become LIVE.
if 'gauge.fresh ? gauge.stage.toUpperCase(Locale.ROOT) : "STALE / UNKNOWN"' not in m:
    raise SystemExit('strict river detail freshness guard missing')

# Add explicit marker for verification.
anchor='    private static String stationGeo(List<StationDot> list, String group) {'
if 'V0887_STATION_AVAILABILITY_SEPARATED_FROM_SAFETY' not in m:
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
print('v0.8.87 PASS: station visual availability separated from strict safety freshness')
