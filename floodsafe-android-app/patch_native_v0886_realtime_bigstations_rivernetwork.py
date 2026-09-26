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

# Enlarge station dots regardless of radius values left by earlier patches.
radii={'fs-stale':('6.8','0.96'),'fs-normal':('7.8','1'),'fs-alert':('8.8','1'),'fs-warning':('9.8','1'),'fs-danger':('10.8','1')}
for sid,(radius,opacity) in radii.items():
    pat=re.compile(r'(ensurePointSource\("'+re.escape(sid)+r'"\s*,\s*"[^"]+"\s*,\s*"#[0-9A-Fa-f]+"\s*,\s*)([0-9.]+f)(\s*,\s*)([0-9.]+f)(\s*\))')
    m,n=pat.subn(lambda x:x.group(1)+radius+'f'+x.group(3)+opacity+'f'+x.group(5),m,count=1)
    if n==0: raise SystemExit('station source missing '+sid)
m=m.replace('circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)','circleStrokeColor("#ffffff"), circleStrokeWidth(2.0f)',1)
if 'V0886_BIG_STATION_MARKERS' not in m:
    marker='    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity)'
    p=m.find(marker)
    if p<0: raise SystemExit('ensurePointSource method missing')
    line=m.rfind('\n',0,p)+1
    m=m[:line]+'    // V0886_BIG_STATION_MARKERS: 6.8–10.8dp status dots for phone visibility.\n'+m[line:]

# Always-visible river source layers using the same progressive fs-rivers GeoJSON source.
helper='''    private void v886EnsureRiverVisibility(){\n        if(!styleReady||style==null||style.getSource("fs-rivers")==null)return;\n        try{\n            if(style.getLayer("fs-river-force-glow")==null)style.addLayer(new LineLayer("fs-river-force-glow","fs-rivers").withProperties(\n                    lineColor("#00bfe8"),lineWidth(6.0f),lineOpacity(0.34f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n            if(style.getLayer("fs-river-force-core")==null)style.addLayer(new LineLayer("fs-river-force-core","fs-rivers").withProperties(\n                    lineColor("#46e8ff"),lineWidth(2.6f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n        }catch(Exception ignored){}\n    } // V0886_FORCE_VISIBLE_RIVER_NETWORK\n\n'''
if 'V0886_FORCE_VISIBLE_RIVER_NETWORK' not in m:
    anchor='    private static int v879TileX(double lon)'
    if anchor not in m: raise SystemExit('v879 tile helper anchor missing')
    m=m.replace(anchor,helper+anchor,1)

# Call force-visibility after river source swaps. Cover the v0.8.84 baseGeo form and the v0.8.79 riversGeoJson form.
m=m.replace('if(s!=null)s.setGeoJson(baseGeo);else installGeoLayers();','if(s!=null){s.setGeoJson(baseGeo);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)
m=m.replace('if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();','if(s!=null){s.setGeoJson(riversGeoJson);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)
# If the source update is multiline/expanded, append after setGeoJson calls instead.
if 'v886EnsureRiverVisibility();' not in m[m.find('private void v879ApplyRiverGeometry'):m.find('private static int v879TileX')]:
    region_start=m.find('private void v879ApplyRiverGeometry')
    region_end=m.find('private static int v879TileX',region_start)
    if region_start>=0 and region_end>region_start:
        region=m[region_start:region_end]
        region2=re.sub(r'(s\.setGeoJson\([^;]+\);)',r'\1v886EnsureRiverVisibility();',region,count=1)
        m=m[:region_start]+region2+m[region_end:]
# Ensure style setup also creates force layers.
needle='            refreshStationSources();\n            refreshUserSource();'
if needle in m and 'v886EnsureRiverVisibility();\n            refreshStationSources();' not in m:
    m=m.replace(needle,'            v886EnsureRiverVisibility();\n            refreshStationSources();\n            refreshUserSource();',1)

# Disable HTTP caches in the active native activity. If an existing helper already does so, mark it.
pat=re.compile(r'(?P<indent>\s*)HttpURLConnection\s+(?P<v>\w+)\s*=\s*\(HttpURLConnection\)\s*([^;]+)\.openConnection\(\);')
def add_nocache(mm):
    ind=mm.group('indent'); v=mm.group('v'); base=mm.group(0)
    return base+'\n'+ind+v+'.setUseCaches(false); '+v+'.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0"); '+v+'.setRequestProperty("Pragma","no-cache"); // V0886_NO_HTTP_CACHE'
if 'V0886_NO_HTTP_CACHE' not in a:
    a2,n=pat.subn(add_nocache,a)
    a=a2
    if n==0:
        if 'setUseCaches(false)' not in a: raise SystemExit('could not install/verify no-cache HTTP')
        anchor='private static final String BIPAD='
        p=a.find(anchor)
        if p<0: raise SystemExit('BIPAD constant missing')
        line=a.rfind('\n',0,p)+1
        a=a[:line]+'    // V0886_NO_HTTP_CACHE: official HTTP helper already uses setUseCaches(false).\n'+a[line:]

# Cache-bust authoritative BIPAD River Watch requests on each source poll.
a=a.replace('"river/?limit=5000"','"river/?limit=5000&_fs="+System.currentTimeMillis()',1)
a=a.replace('"river-trimed/?limit=5000"','"river-trimed/?limit=5000&_fs="+System.currentTimeMillis()',1)

# Version bump.
g=re.sub(r'versionCode\s+105\b','versionCode 106',g,count=1)
g=g.replace("versionName '0.8.85'","versionName '0.8.86'",1)

for token,where in [('V0886_OVERVIEW_FIRST_RIVER_NETWORK',m),('V0886_FORCE_VISIBLE_RIVER_NETWORK',m),('V0886_BIG_STATION_MARKERS',m),('V0886_NO_HTTP_CACHE',a)]:
    if token not in where: raise SystemExit('missing '+token)
for val in ['6.8f','7.8f','8.8f','9.8f','10.8f']:
    if val not in m: raise SystemExit('station radius missing '+val)
if "versionName '0.8.86'" not in g or 'versionCode 106' not in g: raise SystemExit('version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.86 PASS: force-visible progressive river network + larger station dots + no-cache BIPAD refresh')
