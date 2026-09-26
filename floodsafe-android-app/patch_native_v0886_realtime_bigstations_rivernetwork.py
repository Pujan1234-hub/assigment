from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

# Prefer the lightweight verified overview network at startup so rivers appear immediately.
old='''                try { raw = readAsset("data/nepal-waterways-snapshot.json"); }\n                catch (Exception e) { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }'''
new='''                try { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }\n                catch (Exception e) { raw = readAsset("data/nepal-waterways-snapshot.json"); } // V0886_OVERVIEW_FIRST_RIVER_NETWORK'''
if old in m:m=m.replace(old,new,1)
else:
    # tolerate compact formatting from earlier patches
    m=m.replace('try { raw = readAsset("data/nepal-waterways-snapshot.json"); }','try { raw = readAsset("data/nepal-waterways-tiles/overview.json"); } // V0886_OVERVIEW_FIRST_RIVER_NETWORK',1)
    m=m.replace('catch (Exception e) { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }','catch (Exception e) { raw = readAsset("data/nepal-waterways-snapshot.json"); }',1)

# Keep more overview lines if present and make the base network unmistakably visible.
m=m.replace('if (all.size() > 1400) all = new ArrayList<>(all.subList(0, 1400));','if (all.size() > 3600) all = new ArrayList<>(all.subList(0, 3600)); // V0886_DENSE_VISIBLE_NETWORK',1)
for o,n in [
('ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f)','ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 6.8f, 0.96f)'),
('ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f)','ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 7.8f, 1f)'),
('ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 5.0f, 1f)','ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 8.8f, 1f)'),
('ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 5.8f, 1f)','ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 9.8f, 1f)'),
('ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f)','ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 10.8f, 1f)')]:
    m=m.replace(o,n,1)
# Strong white outline so dots remain visible over satellite imagery.
m=m.replace('circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)','circleStrokeColor("#ffffff"), circleStrokeWidth(2.0f)',1)
# Bright persistent base network. Later status layers still override matching rivers.
m=m.replace('lineColor("#003d55"), lineWidth(4.0f), lineOpacity(0.55f)','lineColor("#007c9e"), lineWidth(5.2f), lineOpacity(0.58f)',1)
m=m.replace('lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f)','lineColor("#36e6ff"), lineWidth(2.35f), lineOpacity(1.0f)',1)
m=m.replace('lineWidth(3.0f), lineOpacity(0.30f)','lineWidth(5.2f), lineOpacity(0.58f)',1)
m=m.replace('lineWidth(1.45f), lineOpacity(0.82f)','lineWidth(2.35f), lineOpacity(1.0f)',1)

# Disable URLConnection caches in the active native activity and request fresh network responses.
pat=re.compile(r'(?P<indent>\s*)HttpURLConnection\s+(?P<v>\w+)\s*=\s*\(HttpURLConnection\)\s*([^;]+)\.openConnection\(\);')
def add_nocache(mm):
    ind=mm.group('indent'); v=mm.group('v'); base=mm.group(0)
    if 'V0886_NO_HTTP_CACHE' in base:return base
    return base+'\n'+ind+v+'.setUseCaches(false); '+v+'.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0"); '+v+'.setRequestProperty("Pragma","no-cache"); // V0886_NO_HTTP_CACHE'
a=pat.sub(add_nocache,a)
# Also cache-bust BIPAD list paths used by the official loader when they are constructed as path strings.
a=a.replace('"river/?limit=5000"','"river/?limit=5000&_fs="+System.currentTimeMillis()',1)
a=a.replace('"river-trimed/?limit=5000"','"river-trimed/?limit=5000&_fs="+System.currentTimeMillis()',1)

# Version bump.
g=re.sub(r'versionCode\s+105\b','versionCode 106',g,count=1)
g=g.replace("versionName '0.8.85'","versionName '0.8.86'",1)

if 'V0886_OVERVIEW_FIRST_RIVER_NETWORK' not in m: raise SystemExit('overview-first river network patch missing')
if '7.8f' not in m or '10.8f' not in m: raise SystemExit('big station marker patch missing')
if 'V0886_NO_HTTP_CACHE' not in a: raise SystemExit('no-cache network patch missing')
if "versionName '0.8.86'" not in g or 'versionCode 106' not in g: raise SystemExit('version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.86 PASS: overview-first river network + larger station markers + no-cache BIPAD refresh')
