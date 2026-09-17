from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.32 field fix:
# - v0.8.31 stopped the foreign-country leak but the new exact clip path could publish an empty river set;
# - use the already-proven dense Nepal district-union clip for EVERY viewport (never the old interior bypass);
# - keep startup source empty until a clipped Nepal-only set is ready;
# - restore the clearly visible v0.8.30 blue core + glow pulse;
# - make the station strip explicit: total station registry != stations with a latest reading.
# Alert/notification freshness + 2 km safety rules are untouched.

old='List<RiverWay> chosen=v0831ClipToNepalExact(candidates,nepal);'
new='List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);'
if old in m:
    m=m.replace(old,new,1)
elif new not in m:
    raise SystemExit('v0.8.32 strict dense clip anchor missing')

# v0.8.31 reduced the halo. Restore the visible treatment once geometry is clipped safely.
m=m.replace('lineWidth((float)(6.4+1.8*wave))','lineWidth((float)(7.4+2.4*wave))',1)
m=m.replace('lineWidth((float)(2.8+0.30*wave))','lineWidth((float)(3.0+0.35*wave))',1)

# Startup retries: geometry and district assets are loaded asynchronously on some phones.
# Keep several strict redraw attempts; camera-idle remains authoritative afterwards.
seq='main.postDelayed(this::refreshVisibleRiverTiles,350L);main.postDelayed(this::refreshVisibleRiverTiles,1200L);main.postDelayed(this::refreshVisibleRiverTiles,3000L);'
seq2='main.postDelayed(this::refreshVisibleRiverTiles,350L);main.postDelayed(this::refreshVisibleRiverTiles,1200L);main.postDelayed(this::refreshVisibleRiverTiles,3000L);main.postDelayed(this::refreshVisibleRiverTiles,5200L);'
if seq in m:
    m=m.replace(seq,seq2,1)
elif seq2 not in m:
    raise SystemExit('v0.8.32 startup refresh sequence missing')

# Rewrite the compact overlay so 285 cannot be mistaken for 285 live measurements.
us=a.find('    private void updateMapLiveOverlay(){')
ue=a.find('    private void refreshCompactRainCounts()',us)
if us<0 or ue<0:
    raise SystemExit('v0.8.32 overlay anchors missing')
overlay=r'''    private void updateMapLiveOverlay(){
        if(mapLiveText==null)return;
        int total=0,latest=0,current=0;
        synchronized(stations){
            total=stations.size();
            for(RiverStation s:stations){
                if(s==null)continue;
                if(s.at>0&&Double.isFinite(s.level))latest++;
                if(s.fresh)current++;
            }
        }
        int missing=Math.max(0,total-latest);
        String rain=(mapRainLatest>=0&&mapRainTotal>=0)?(mapRainLatest+" / "+mapRainTotal):"— / —";
        mapLiveText.setText("🌊 stations "+total+" • latest reading "+latest+" • no latest "+missing+" • current "+current+"   🌧️ rain "+rain);
    }

'''
a=a[:us]+overlay+a[ue:]

# Version bump.
g=g.replace('versionCode 51','versionCode 52',1).replace("versionName '0.8.31'","versionName '0.8.32'",1)
if 'versionCode 52' not in g or "versionName '0.8.32'" not in g:
    raise SystemExit('v0.8.32 version bump failed')

# Hard gates.
for marker in [
    'List<RiverWay> chosen=clipWaysToNepalDense(candidates,nepal);',
    'style.addSource(new GeoJsonSource("fs-rivers", emptyFeatureCollection()))',
    'main.postDelayed(this::refreshVisibleRiverTiles,5200L)',
    'lineColor("#1FC7FF")',
    'lineWidth((float)(7.4+2.4*wave))',
    'lineWidth((float)(3.0+0.35*wave))',
    'map.addOnCameraIdleListener(this::refreshVisibleRiverTiles)',
    'setGeo("fs-flow-particles",emptyFeatureCollection())',
    'sameRiverGaugeFor',
    'routeD<=0.75']:
    if marker not in m:
        raise SystemExit('v0.8.32 map marker missing: '+marker)
if 'viewportInsideNepalStrict(fw,fs,fe,fn,nepal)?copyWaysExact(candidates)' in m:
    raise SystemExit('unsafe interior full-way bypass returned')
for marker in ['latest reading "+latest','no latest "+missing','current "+current']:
    if marker not in a:
        raise SystemExit('v0.8.32 station overlay marker missing: '+marker)
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a:
        raise SystemExit('alert safety changed unexpectedly: '+marker)

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.32 strict Nepal dense clip + restored blue glow PASS')
