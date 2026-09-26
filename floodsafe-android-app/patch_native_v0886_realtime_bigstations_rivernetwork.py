from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

# v0.8.79+ already loads overview.json first. Mark/verify that contract instead of rewriting it.
if 'data/nepal-waterways-tiles/overview.json' not in m: raise SystemExit('overview river asset missing')
if 'V0886_OVERVIEW_FIRST_RIVER_NETWORK' not in m:
    anchor='private void loadBundledGeometry()'
    p=m.find(anchor)
    if p<0: raise SystemExit('loadBundledGeometry missing')
    line=m.rfind('\n',0,p)+1
    m=m[:line]+'    // V0886_OVERVIEW_FIRST_RIVER_NETWORK: progressive overview is loaded immediately, before station matching.\n'+m[line:]

# Enlarge station dots for phone use.
repls={
'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f)':'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 6.8f, 0.96f)',
'ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f)':'ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 7.8f, 1f)',
'ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 5.0f, 1f)':'ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 8.8f, 1f)',
'ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 5.8f, 1f)':'ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 9.8f, 1f)',
'ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f)':'ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 10.8f, 1f)'}
for old,new in repls.items(): m=m.replace(old,new,1)
m=m.replace('circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)','circleStrokeColor("#ffffff"), circleStrokeWidth(2.0f)',1)

# Always-visible river source layers using the same progressive fs-rivers GeoJSON source.
# These layers are deliberately independent of station matching, so the network cannot disappear.
helper='''    private void v886EnsureRiverVisibility(){\n        if(!styleReady||style==null||style.getSource("fs-rivers")==null)return;\n        try{\n            if(style.getLayer("fs-river-force-glow")==null)style.addLayer(new LineLayer("fs-river-force-glow","fs-rivers").withProperties(\n                    lineColor("#00bfe8"),lineWidth(6.0f),lineOpacity(0.34f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n            if(style.getLayer("fs-river-force-core")==null)style.addLayer(new LineLayer("fs-river-force-core","fs-rivers").withProperties(\n                    lineColor("#46e8ff"),lineWidth(2.6f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n        }catch(Exception ignored){}\n    } // V0886_FORCE_VISIBLE_RIVER_NETWORK\n\n'''
if 'V0886_FORCE_VISIBLE_RIVER_NETWORK' not in m:
    anchor='    private static int v879TileX(double lon)'
    if anchor not in m: raise SystemExit('v879 tile helper anchor missing')
    m=m.replace(anchor,helper+anchor,1)

# Call force-visibility after every atomic river-source swap, and after normal layer install.
m=m.replace('if(s!=null)s.setGeoJson(baseGeo);else installGeoLayers();','if(s!=null){s.setGeoJson(baseGeo);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)
m=m.replace('if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();','if(s!=null){s.setGeoJson(riversGeoJson);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)
# Ensure style setup also creates the force layers when fs-rivers already exists.
needle='            refreshStationSources();\n            refreshUserSource();'
if needle in m and 'v886EnsureRiverVisibility();\n            refreshStationSources();' not in m:
    m=m.replace(needle,'            v886EnsureRiverVisibility();\n            refreshStationSources();\n            refreshUserSource();',1)

# Disable HTTP caches in the active native activity. If earlier patches already do this,
# just attach the verification marker near the class constant.
pat=re.compile(r'(?P<indent>\s*)HttpURLConnection\s+(?P<v>\w+)\s*=\s*\(HttpURLConnection\)\s*([^;]+)\.openConnection\(\);')
def add_nocache(mm):
    ind=mm.group('indent'); v=mm.group('v'); base=mm.group(0)
    return base+'\n'+ind+v+'.setUseCaches(false); '+v+'.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0"); '+v+'.setRequestProperty("Pragma","no-cache"); // V0886_NO_HTTP_CACHE'
if 'V0886_NO_HTTP_CACHE' not in a:
    a2,n=pat.subn(add_nocache,a)
    a=a2
    if n==0:
        # Existing helper may already disable caches; preserve that implementation and mark the contract.
        if 'setUseCaches(false)' not in a: raise SystemExit('could not install/verify no-cache HTTP')
        anchor='private static final String BIPAD='
        p=a.find(anchor)
        if p<0: raise SystemExit('BIPAD constant missing')
        line=a.rfind('\n',0,p)+1
        a=a[:line]+'    // V0886_NO_HTTP_CACHE: official HTTP helper already uses setUseCaches(false).\n'+a[line:]

# Cache-bust the authoritative BIPAD river list endpoints on every poll.
a=a.replace('"river/?limit=5000"','"river/?limit=5000&_fs="+System.currentTimeMillis()',1)
a=a.replace('"river-trimed/?limit=5000"','"river-trimed/?limit=5000&_fs="+System.currentTimeMillis()',1)

# Version bump.
g=re.sub(r'versionCode\s+105\b','versionCode 106',g,count=1)
g=g.replace("versionName '0.8.85'","versionName '0.8.86'",1)

for token,where in [('V0886_OVERVIEW_FIRST_RIVER_NETWORK',m),('V0886_FORCE_VISIBLE_RIVER_NETWORK',m),('V0886_NO_HTTP_CACHE',a)]:
    if token not in where: raise SystemExit('missing '+token)
if '7.8f' not in m or '10.8f' not in m: raise SystemExit('big station marker patch missing')
if "versionName '0.8.86'" not in g or 'versionCode 106' not in g: raise SystemExit('version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.86 PASS: force-visible progressive river network + larger station dots + no-cache BIPAD refresh')
