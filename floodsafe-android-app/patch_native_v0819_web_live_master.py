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

# v0.8.19 master rule: reproduce the proven web map rather than inventing another map.
# - BIPAD/DHM latest=true is the observation truth.
# - A station is map-current when its latest official observation belongs to the current
#   Nepal calendar day. The exact official measurement time is always shown.
# - Foreground live feed is rechecked every 10 seconds, matching the web runtime cadence.
# - Native visual style mirrors map-gl-v4: dark cyan shadow, #22e7ff river core,
#   white/cyan moving beads (150 ms frames / 6 second route cycle).
# - Normal current stations are visible Nepal-wide; rain stays hidden until local zoom.
# - River clicks keep v0.8.18 strict same-river gauge semantics; no other-river reference.
# Emergency alert freshness/radius are NOT changed here.

# -----------------------------------------------------------------------------
# Activity: latest official observation, not historical endpoint rows.
# -----------------------------------------------------------------------------
old_current='boolean current=Double.isFinite(level)&&at>0&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L;'
new_current='boolean current=Double.isFinite(level)&&at>0&&sameNepalCalendarDay(at,now)&&at-now<=5L*60L*1000L;'
if old_current in a:
    a=a.replace(old_current,new_current,1)
elif new_current not in a:
    raise SystemExit('v0.8.19 current observation anchor missing')

# Web trusted runtime checks fresh source every 10 seconds in foreground.
a=a.replace('main.postDelayed(this,60_000L);','main.postDelayed(this,10_000L);',1)
a=a.replace('main.postDelayed(livePoll,60_000L);','main.postDelayed(livePoll,2_000L);',1)
if 'main.postDelayed(this,10_000L)' not in a:
    raise SystemExit('v0.8.19 10 second live poll not applied')

# Source wording: this is latest official state, not a history/today summary.
a=a.replace('🌊 current official ','🌊 latest official ',2)
a=a.replace('🌊 नदी current ','🌊 नदी latest ',2)
a=a.replace('current ≤30m','latest official',4)
a=a.replace('current official ≤30m','latest official',4)

# -----------------------------------------------------------------------------
# Map visual: exact web-like cyan flow treatment.
# Replace geographic river glow/core by layer id so prior patch values do not matter.
# -----------------------------------------------------------------------------
glow_pat=r'''style\.addLayer\(new LineLayer\("fs-river-glow", "fs-rivers"\)\.withProperties\(.*?\)\);'''
glow_new='''style.addLayer(new LineLayer("fs-river-glow", "fs-rivers").withProperties(
                        lineColor("#003a4b"), lineWidth(5.4f), lineOpacity(0.80f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
m,n=re.subn(glow_pat,glow_new,m,count=1,flags=re.S)
if n!=1: raise SystemExit('fs-river-glow layer anchor missing')

core_pat=r'''style\.addLayer\(new LineLayer\("fs-rivers-layer", "fs-rivers"\)\.withProperties\(.*?\)\);'''
core_new='''style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(
                        lineColor("#22e7ff"), lineWidth(2.20f), lineOpacity(0.98f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
m,n=re.subn(core_pat,core_new,m,count=1,flags=re.S)
if n!=1: raise SystemExit('fs-rivers-layer anchor missing')

# Bright web-style moving bead.
m=re.sub(r'ensurePointSource\("fs-flow-particles", "fs-flow-particles-layer", "#[0-9A-Fa-f]{6}", [0-9.]+f, [0-9.]+f\);',
         'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#ffffff", 3.1f, 0.92f);',m,count=1)
if '"fs-flow-particles-layer", "#ffffff", 3.1f, 0.92f' not in m:
    raise SystemExit('flow particle style anchor missing')

# If a trace layer exists from prior patches, keep it cyan and visible without making it heavy.
trace_pat=r'''style\.addLayer\(new LineLayer\("fs-river-flow-trace", "fs-rivers"\)\.withProperties\(.*?\)\);'''
if re.search(trace_pat,m,flags=re.S):
    m=re.sub(trace_pat,'''style.addLayer(new LineLayer("fs-river-flow-trace", "fs-rivers").withProperties(
                        lineColor("#8ff7ff"), lineWidth(1.05f), lineOpacity(0.36f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));''',m,count=1,flags=re.S)

# -----------------------------------------------------------------------------
# Clean national/local geometry. Keep the v0.8.18 bounded set for smooth Android,
# but expose river names cleanly: major names nationally, all selected local names when zoomed.
# -----------------------------------------------------------------------------
label_line='String geo=makeRiversGeoJson(chosen),labels=zoom<7.0?emptyFeatureCollection():makeRiverLabelsGeoJson(chosen);'
label_new='String geo=makeRiversGeoJson(chosen),labels=zoom<7.0?makeRiverLabelsGeoJson(new ArrayList<>(chosen.subList(0,Math.min(36,chosen.size())))):makeRiverLabelsGeoJson(chosen);'
if label_line in m:
    m=m.replace(label_line,label_new,1)
elif label_new not in m:
    raise SystemExit('river label publish anchor missing')

# Nepal-wide CURRENT official river stations must be visible even at national zoom.
old_normal='setGeo("fs-normal", detail?stationGeo(snapshot, "normal"):emptyFeatureCollection());'
new_normal='setGeo("fs-normal", stationGeo(snapshot, "normal"));'
if old_normal in m:
    m=m.replace(old_normal,new_normal,1)
elif new_normal not in m:
    raise SystemExit('national normal station anchor missing')

# Do not crowd the national map with station text; names appear once user zooms in.
m=m.replace('setGeo("fs-station-labels", zoom>=8.0?stationGeoImportant(snapshot):emptyFeatureCollection());',
            'setGeo("fs-station-labels", zoom>=7.6?stationGeoImportant(snapshot):emptyFeatureCollection());',1)

# Keep rain detail local. This intentionally prevents the 374 rain dots from covering Nepal view.
if 'boolean showRainMarkers=zoom>=8.0;' not in m:
    raise SystemExit('rain zoom gate missing')

# -----------------------------------------------------------------------------
# Web flow animation: no gauge matching in the frame loop. It only moves a few points
# over the already-selected visible river list, so touch/drag remains responsive.
# -----------------------------------------------------------------------------
pt_start=m.find('    private final Runnable particleTick = new Runnable() {')
pt_end=m.find('    private StationDot readStation(Object o) {',pt_start)
if pt_start<0 or pt_end<0: raise SystemExit('particleTick anchors missing')
new_tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                List<RiverWay> visibleSnapshot=new ArrayList<>(rivers);
                double zoom=map==null?6.0:map.getCameraPosition().zoom;
                int maxParticles=zoom<7.0?40:30;
                JSONArray features=new JSONArray();int n=Math.min(maxParticles,visibleSnapshot.size());
                double phase=((System.currentTimeMillis()-particleStart)%6000L)/6000.0;
                for(int i=0;i<n;i++){
                    RiverWay r=visibleSnapshot.get(i);if(r==null||r.points.size()<2)continue;
                    double v=((phase+i*.173)%1.0)*(r.points.size()-1);
                    int ix=Math.min(r.points.size()-2,(int)Math.floor(v));double f=v-ix;
                    double[] p0=r.points.get(ix),p1=r.points.get(ix+1);
                    features.put(pointFeature(p0[0]+(p1[0]-p0[0])*f,p0[1]+(p1[1]-p0[1])*f,"flow"));
                }
                setGeo("fs-flow-particles",new JSONObject().put("type","FeatureCollection").put("features",features).toString());
                try{
                    LineLayer trace=style.getLayerAs("fs-river-flow-trace");
                    if(trace!=null){double ph=(System.currentTimeMillis()%1800L)/1800.0;float op=(float)(0.28+0.18*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));trace.setProperties(lineOpacity(op),lineWidth(1.05f));}
                    double ph=(System.currentTimeMillis()%1800L)/1800.0;float pulse=(float)(0.30+0.18*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));
                    LineLayer warningGlow=style.getLayerAs("fs-river-warning-status-layer-glow");
                    LineLayer dangerGlow=style.getLayerAs("fs-river-danger-status-layer-glow");
                    if(warningGlow!=null)warningGlow.setProperties(lineOpacity(Math.min(0.58f,pulse)),lineWidth(7.6f));
                    if(dangerGlow!=null)dangerGlow.setProperties(lineOpacity(Math.min(0.68f,pulse+0.12f)),lineWidth(9.2f));
                }catch(Exception ignored){}
            }catch(Exception ignored){}
            main.postDelayed(this,150L);
        }
    };

'''
m=m[:pt_start]+new_tick+m[pt_end:]

# -----------------------------------------------------------------------------
# River dialog: current direct gauge means latest=true observation for the same river.
# Do not call it "today"; show exact official measurement time so the user sees NOW/source age.
# -----------------------------------------------------------------------------
m=m.replace('msg.append("आजको direct official gauge: ")','msg.append("अहिलेको latest official gauge: ")',1)
m=m.replace('यसै नदी/खोलाको official gauge छ, तर current realtime reading उपलब्ध छैन।',
            'यसै नदी/खोलाको official gauge छ, तर अहिले latest official reading उपलब्ध छैन।',1)
if 'अहिलेको latest official gauge:' not in m:
    raise SystemExit('direct same-river dialog wording anchor missing')
if 'नजिकको आजको official gauge reference' in m or 'nearest gauge reference' in m.lower():
    raise SystemExit('different-river nearest reference returned')

# Version bump.
if "versionName '0.8.19'" not in g:
    g=g.replace('versionCode 38','versionCode 39',1)
    g=g.replace("versionName '0.8.18'","versionName '0.8.19'",1)
if 'versionCode 39' not in g or "versionName '0.8.19'" not in g:
    raise SystemExit('v0.8.19 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

# Hard gates: web visual/runtime + official truth + smooth frame loop.
a2=a_path.read_text(encoding='utf-8');m2=m_path.read_text(encoding='utf-8')
for marker in ['river-stations/?latest=true','rain-stations/?latest=true','sameNepalCalendarDay(at,now)','main.postDelayed(this,10_000L)']:
    if marker not in a2: raise SystemExit('v0.8.19 activity marker missing: '+marker)
for marker in ['lineColor("#003a4b")','lineColor("#22e7ff")','"#ffffff", 3.1f, 0.92f','maxParticles=zoom<7.0?40:30','%6000L','main.postDelayed(this,150L)','sameRiverGaugeFor','return a.equals(b);','boolean showRainMarkers=zoom>=8.0','setGeo("fs-normal", stationGeo(snapshot, "normal"))','अहिलेको latest official gauge:']:
    if marker not in m2: raise SystemExit('v0.8.19 map marker missing: '+marker)
if 'routeGaugeForSnapshot(rr,flowStations)' in m2: raise SystemExit('heavy per-frame station scan returned')
if 'नजिकको आजको official gauge reference' in m2: raise SystemExit('different river reference returned')
print('FloodSafe v0.8.19 web-live master map PASS')
