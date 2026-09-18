from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path = src / 'NativeFullActivity.java'
g_path = root / 'app/build.gradle'

a = a_path.read_text(encoding='utf-8')
g = g_path.read_text(encoding='utf-8')

old_fresh = 'private static final long RIVER_FRESH_MS=10L*60L*1000L;'
new_fresh = 'private static final long RIVER_FRESH_MS=5L*60L*1000L;'
if old_fresh not in a:
    raise SystemExit('v0.8.36 freshness anchor missing')
a = a.replace(old_fresh, new_fresh, 1)

# Keep any matching safety copy aligned with the actual 5-minute rule when present.
a = a.replace('पछिल्लो ३० मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ',
              'पछिल्लो ५ मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ')
a = a.replace('पछिल्लो १० मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ',
              'पछिल्लो ५ मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ')
a = a.replace('official measurements from the last 30 minutes',
              'official measurements from the last 5 minutes')
a = a.replace('official measurements from the last 10 minutes',
              'official measurements from the last 5 minutes')

if 'RIVER_FRESH_MS=5L*60L*1000L' not in a:
    raise SystemExit('v0.8.36 five-minute freshness not applied')

# Version bump only; all other behavior remains from v0.8.35.
if 'versionCode 55' not in g or "versionName '0.8.35'" not in g:
    raise SystemExit('v0.8.36 version anchors missing')
g = g.replace('versionCode 55', 'versionCode 56', 1)
g = g.replace("versionName '0.8.35'", "versionName '0.8.36'", 1)

a_path.write_text(a, encoding='utf-8')
g_path.write_text(g, encoding='utf-8')
print('FloodSafe v0.8.36 5-minute official river freshness PASS')
