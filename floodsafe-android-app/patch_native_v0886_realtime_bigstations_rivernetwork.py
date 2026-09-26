from pathlib import Path
import re
root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'; m_path=src/'FloodSafeNativeMapView.java'; g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8'); m=m_path.read_text(encoding='utf-8'); g=g_path.read_text(encoding='utf-8')

# v0.8.79+ already loads the verified overview network first.
if 'data/nepal-waterways-tiles/overview.json' not in m: raise SystemExit('overview river asset missing')
if 'V0886_OVERVIEW_FIRST_RIVER_NETWORK' not in m:
    p=m.find('private void loadBundledGeometry()')
    if p<0: raise SystemExit('loadBundledGeometry missing')
    line=m.rfind('\n',0,p)+1
    m=m[:line]+'    // V0886_OVERVIEW_FIRST_RIVER_NETWORK: progressive overview loads before station matching.\n'+m[line:]

# Larger station markers, independent of earlier radius values.
radii={'fs-stale':('6.8','0.96'),'fs-normal':('7.8','1'),'fs-alert':('8.8','1'),'fs-warning':('9.8','1'),'fs-danger':('10.8','1')}
for sid,(radius,opacity) in radii.items():
    pat=re.compile(r'(ensurePointSource\("'+re.escape(sid)+r'"\s*,\s*"[^"]+"\s*,\s*"#[0-9A-Fa-f]+"\s*,\s*)([0-9.]+f)(\s*,\s*)([0-9.]+f)(\s*\))')
    m,n=pat.subn(lambda x:x.group(1)+radius+'f'+x.group(3)+opacity+'f'+x.group(5),m,count=1)
    if n==0: raise SystemExit('station source missing '+sid)
m=m.replace('circleStrokeColor("#ffffff"), circleStrokeWidth(1.0f)','circleStrokeColor("#ffffff"), circleStrokeWidth(2.0f)',1)
if 'V0886_BIG_STATION_MARKERS' not in m:
    p=m.find('private void ensurePointSource(')
    if p<0: raise SystemExit('ensurePointSource missing')
    line=m.rfind('\n',0,p)+1
    m=m[:line]+'    // V0886_BIG_STATION_MARKERS: 6.8-10.8dp station dots for phone visibility.\n'+m[line:]

# Force-visible line layers on the progressive fs-rivers source.
helper='''    private void v886EnsureRiverVisibility(){\n        if(!styleReady||style==null||style.getSource("fs-rivers")==null)return;\n        try{\n            if(style.getLayer("fs-river-force-glow")==null)style.addLayer(new LineLayer("fs-river-force-glow","fs-rivers").withProperties(\n                    lineColor("#00bfe8"),lineWidth(6.0f),lineOpacity(0.34f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n            if(style.getLayer("fs-river-force-core")==null)style.addLayer(new LineLayer("fs-river-force-core","fs-rivers").withProperties(\n                    lineColor("#46e8ff"),lineWidth(2.6f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n        }catch(Exception ignored){}\n    } // V0886_FORCE_VISIBLE_RIVER_NETWORK\n\n'''
if 'V0886_FORCE_VISIBLE_RIVER_NETWORK' not in m:
    anchor='    private static int v879TileX(double lon)'
    if anchor not in m: raise SystemExit('v879 tile anchor missing')
    m=m.replace(anchor,helper+anchor,1)

# The v0.8.84 method is intentionally compact. Patch that exact safe form with braces.
bad='if(rs!=null)rs.setGeoJson(bg);else installGeoLayers();'
good='if(rs!=null){rs.setGeoJson(bg);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}'
if bad in m:
    m=m.replace(bad,good,1)
else:
    # Alternative earlier source variable forms.
    m=m.replace('if(s!=null)s.setGeoJson(baseGeo);else installGeoLayers();','if(s!=null){s.setGeoJson(baseGeo);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)
    m=m.replace('if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();','if(s!=null){s.setGeoJson(riversGeoJson);v886EnsureRiverVisibility();}else{installGeoLayers();v886EnsureRiverVisibility();}',1)

# Existing source loaders already contain setUseCaches(false); don't inject statements into compact Java methods.
if 'setUseCaches(false)' not in a: raise SystemExit('existing no-cache transport missing')
if 'V0886_NO_HTTP_CACHE' not in a:
    p=a.find('private static final String BIPAD=')
    if p<0: p=a.find('private static final String BIPAD =')
    if p<0: raise SystemExit('BIPAD constant missing')
    line=a.rfind('\n',0,p)+1
    a=a[:line]+'    // V0886_NO_HTTP_CACHE: preserve existing setUseCaches(false) transport; cache-bust River Watch polls below.\n'+a[line:]

# Cache-bust the authoritative BIPAD list polls while preserving valid Java array syntax.
a=a.replace('"river/?limit=5000"','"river/?limit=5000&_fs="+System.currentTimeMillis()',1)
a=a.replace('"river-trimed/?limit=5000"','"river-trimed/?limit=5000&_fs="+System.currentTimeMillis()',1)

# Version bump.
g=re.sub(r'versionCode\s+105\b','versionCode 106',g,count=1)
g=g.replace("versionName '0.8.85'","versionName '0.8.86'",1)

for token,where in [('V0886_OVERVIEW_FIRST_RIVER_NETWORK',m),('V0886_FORCE_VISIBLE_RIVER_NETWORK',m),('V0886_BIG_STATION_MARKERS',m),('V0886_NO_HTTP_CACHE',a)]:
    if token not in where: raise SystemExit('missing '+token)
for val in ['6.8f','7.8f','8.8f','9.8f','10.8f']:
    if val not in m: raise SystemExit('station radius missing '+val)
if 'v886EnsureRiverVisibility();else' in m: raise SystemExit('invalid river if/else patch')
if "versionName '0.8.86'" not in g or 'versionCode 106' not in g: raise SystemExit('version bump failed')
a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.86 PASS: force-visible river network + larger station dots + cache-busted BIPAD polls')
