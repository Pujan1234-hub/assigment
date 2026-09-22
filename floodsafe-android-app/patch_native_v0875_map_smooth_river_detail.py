from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.75 real-device smoothness repair on top of the accepted v0.8.74 build.
# Data/source contracts are deliberately untouched:
# - foreground and background official-source recheck remains 1 second
# - exact source values, 2 km verified Warning/Danger alerts, rain-detail-only policy,
#   strict Nepal mask/camera and 77 districts remain unchanged
# This patch only reduces render work and restores the already-accepted geometry-first
# river -> gauge association before delegating to the full live source detail popup.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# 1) Render-control fields: a separate single worker keeps risk matching off the UI thread.
field='    private boolean animationRunning = false;'
extra=r'''
    private volatile boolean v875TouchActive=false; // V0875_TOUCH_PRIORITY_FIELD
    private final ExecutorService v875RenderIo=Executors.newSingleThreadExecutor();
    private int v875RiskGeneration=0;
    private final Runnable v875RiskKick=this::v875StartRiskAsync;
    private String v875LastAlertRisk="",v875LastWarningRisk="",v875LastDangerRisk="";
'''
if 'V0875_TOUCH_PRIORITY_FIELD' not in m:
    if field not in m:raise SystemExit('v0875 animation field anchor missing')
    m=m.replace(field,field+extra,1)

# 2) Prioritize pan/pinch/touch. Rendering updates pause while a gesture is active.
sp=method_span(m,'dispatchTouchEvent')
if not sp:raise SystemExit('v0875 dispatchTouchEvent missing')
dispatch=r'''    @Override public boolean dispatchTouchEvent(MotionEvent ev) {
        int action=ev.getActionMasked();
        v875TouchActive=(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_MOVE||ev.getPointerCount()>1);
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_MOVE||ev.getPointerCount()>1){
            if(getParent()!=null)getParent().requestDisallowInterceptTouchEvent(true);
        }else if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){
            v875TouchActive=false;
            if(getParent()!=null)getParent().requestDisallowInterceptTouchEvent(false);
        }
        return super.dispatchTouchEvent(ev);
    } // V0875_TOUCH_PRIORITY
'''
m=m[:sp[0]]+dispatch+m[sp[1]:]

# 3) v0.8.47's 120ms animation rebuilt up to ~700 river highlight segments as JSON each tick.
# Keep only a lightweight breathing glow. The legacy point-particle source has already been
# empty since v0.8.29, so there is no river-particle loop to cap and no per-frame river
# MultiLineString rebuild remains after this replacement.
sp=method_span(m,'v847UpdateMovingGlow')
if not sp:raise SystemExit('v0875 v847UpdateMovingGlow missing')
light=r'''    private void v847UpdateMovingGlow(long now){
        if(!styleReady||style==null||v875TouchActive)return;
        try{
            double wave=0.5+0.5*Math.sin(now/420.0);
            LineLayer baseGlow=style.getLayerAs("fs-river-glow");
            if(baseGlow!=null)baseGlow.setProperties(
                    lineOpacity((float)(0.42+0.16*wave)),
                    lineWidth((float)(4.4+0.8*wave)));
            LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
            if(baseCore!=null)baseCore.setProperties(
                    lineOpacity((float)(0.93+0.05*wave)),
                    lineWidth((float)(1.75+0.22*wave)));
            LineLayer halo=style.getLayerAs("fs-river-flow-anim-halo");
            if(halo!=null)halo.setProperties(lineOpacity(0.0f));
            LineLayer core=style.getLayerAs("fs-river-flow-anim-core");
            if(core!=null)core.setProperties(lineOpacity(0.0f));
            // V0847_MOVING_GLOW retained as a lightweight native breathing glow.
        }catch(Exception ignored){}
    } // V0875_LIGHTWEIGHT_FLOW_ANIMATION
'''
m=m[:sp[0]]+light+m[sp[1]:]

# Slow only the visual animation cadence, not official data polling. During a touch gesture,
# skip all visual tick work so MapLibre gets the UI thread first. The legacy point-particle
# source remains empty; this is the verified lightweight-particle contract.
ps=m.find('    private final Runnable particleTick')
if ps<0:raise SystemExit('v0875 particleTick missing')
pe=m.find('    private StationDot readStation(',ps)
if pe<0:pe=m.find('    private RainDot readRain(',ps)
if pe<0:raise SystemExit('v0875 particleTick end missing')
block=m[ps:pe]
block=re.sub(r'main\.postDelayed\(this,\s*\d+L\);','main.postDelayed(this,360L);',block)
guard=re.search(r'if\s*\(\s*!animationRunning\s*\|\|\s*!styleReady\s*\|\|\s*style\s*==\s*null\s*\)\s*return\s*;',block)
if not guard:raise SystemExit('v0875 particle guard missing')
if 'V0875_LIGHT_PARTICLES' not in block:
    ins=guard.end()
    block=block[:ins]+'\n            // V0875_LIGHT_PARTICLES: legacy point-particle source is empty; visual tick only.'+block[ins:]
if 'V0875_TOUCH_SKIPS_ANIMATION_WORK' not in block:
    guard2=re.search(r'V0875_LIGHT_PARTICLES[^\n]*\n?',block)
    if not guard2:raise SystemExit('v0875 lightweight particle marker insertion failed')
    ins=guard2.end()
    block=block[:ins]+'            if(v875TouchActive){main.postDelayed(this,360L);return;} // V0875_TOUCH_SKIPS_ANIMATION_WORK\n'+block[ins:]
if 'main.postDelayed(this,360L);' not in block:raise SystemExit('v0875 particle cadence repair failed')
# The old v0.8.29 contract intentionally keeps the point-particle source empty. If a later
# historical patch changed that, do not silently claim this build is lightweight.
if 'setGeo("fs-flow-particles",emptyFeatureCollection())' not in block:
    raise SystemExit('v0875 expected empty legacy particle source missing')
m=m[:ps]+block+m[pe:]

# 4) River risk colouring remains exact but its expensive river x station geometry matching
# is debounced and built on a dedicated worker. Only finished GeoJSON is published on main.
sp=method_span(m,'refreshRiverRiskSources')
if not sp:raise SystemExit('v0875 refreshRiverRiskSources missing')
risk=r'''    private void refreshRiverRiskSources(){
        if(!styleReady||style==null)return;
        main.removeCallbacks(v875RiskKick);
        main.postDelayed(v875RiskKick,280L);
    } // V0875_ASYNC_RISK_REBUILD

    private void v875StartRiskAsync(){
        if(!styleReady||style==null)return;
        if(v875TouchActive){main.removeCallbacks(v875RiskKick);main.postDelayed(v875RiskKick,420L);return;}
        final int generation=++v875RiskGeneration;
        final List<StationDot> ss;
        synchronized(stations){ss=new ArrayList<>(stations);}
        final List<RiverWay> rr=new ArrayList<>(rivers);
        try{
            v875RenderIo.execute(()->{
                final String alert=v875RiskGeo(rr,ss,"alert");
                final String warning=v875RiskGeo(rr,ss,"warning");
                final String danger=v875RiskGeo(rr,ss,"danger");
                main.post(()->{
                    if(generation!=v875RiskGeneration||!styleReady||style==null)return;
                    if(v875TouchActive){main.removeCallbacks(v875RiskKick);main.postDelayed(v875RiskKick,420L);return;}
                    if(!alert.equals(v875LastAlertRisk)){v875LastAlertRisk=alert;setGeo("fs-river-alert-risk",alert);}
                    if(!warning.equals(v875LastWarningRisk)){v875LastWarningRisk=warning;setGeo("fs-river-warning-risk",warning);}
                    if(!danger.equals(v875LastDangerRisk)){v875LastDangerRisk=danger;setGeo("fs-river-danger-risk",danger);}
                });
            });
        }catch(Exception ignored){}
    }

    private String v875RiskGeo(List<RiverWay> rr,List<StationDot> ss,String group){
        try{
            List<RiverWay> selected=new ArrayList<>();
            for(RiverWay r:rr)if(v872RiskGaugeForRiver(r,ss,group)!=null)selected.add(r);
            return makeRiversGeoJson(selected);
        }catch(Exception e){return emptyFeatureCollection();}
    }
'''
m=m[:sp[0]]+risk+m[sp[1]:]

# Shut down the new renderer with the map view.
sp=method_span(m,'onDetachedFromWindow')
if not sp:raise SystemExit('v0875 onDetachedFromWindow missing')
detach=m[sp[0]:sp[1]]
if 'V0875_RENDER_WORKER_SHUTDOWN' not in detach:
    anchor='        io.shutdownNow();'
    if anchor not in detach:raise SystemExit('v0875 detach io shutdown anchor missing')
    detach=detach.replace(anchor,'        try{v875RenderIo.shutdownNow();}catch(Exception ignored){} // V0875_RENDER_WORKER_SHUTDOWN\n'+anchor,1)
    m=m[:sp[0]]+detach+m[sp[1]:]

# 5) Restore geometry-first river -> official gauge association that v0.8.66 introduced.
# v0.8.71 later replaced showRiver while adding the full source detail popup and fell back
# to name-only matching. Use the accepted geometry gate, then delegate to that full popup.
sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0875 showRiver missing')
show=r'''    private void showRiver(RiverWay r,double la,double lo){
        StationDot gauge=v866RiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        if(gauge!=null&&stationTapListener!=null){
            stationTapListener.onStationTap(gauge.original);
            return;
        } // V0875_RIVER_TAP_GEOMETRY_SOURCE_DETAIL
        StringBuilder msg=new StringBuilder();
        if(named)msg.append(englishUi?
                "No safely matched official source reading is currently available for this exact river segment.":
                "यो नदीको यही खण्डसँग सुरक्षित रूपमा मिल्ने आधिकारिक source reading अहिले उपलब्ध छैन।");
        else msg.append(englishUi?
                "This map segment has no usable river name and no official gauge close enough to its geometry.":
                "यो नक्सा खण्डमा प्रयोग गर्न मिल्ने नदी नाम छैन र geometry नजिक सुरक्षित रूपमा मिल्ने official gauge पनि छैन।");
        msg.append("\n\n").append(englishUi?
                "Tap the station dot for that exact station. FloodSafe will not attach a distant or different-river gauge.":
                "ठ्याक्कै station को जानकारीका लागि station dot थिच्नुहोस्। FloodSafe ले टाढाको वा अर्को नदीको gauge जोड्दैन।");
        msg.append("\n\n").append(englishUi?
                "River geometry: OpenStreetMap / FloodSafe Nepal network":
                "नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString())
                .setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0875_RIVER_GEOMETRY_DETAIL_REPAIR
'''
m=m[:sp[0]]+show+m[sp[1]:]

# Release identity.
if 'versionCode 94' in g:g=g.replace('versionCode 94','versionCode 95',1)
elif 'versionCode 95' not in g:raise SystemExit('v0875 versionCode anchor missing')
if "versionName '0.8.74'" in g:g=g.replace("versionName '0.8.74'","versionName '0.8.75'",1)
elif "versionName '0.8.75'" not in g:raise SystemExit('v0875 versionName anchor missing')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

for x in [
    'V0875_TOUCH_PRIORITY','V0875_LIGHTWEIGHT_FLOW_ANIMATION','V0875_LIGHT_PARTICLES',
    'V0875_TOUCH_SKIPS_ANIMATION_WORK','V0875_ASYNC_RISK_REBUILD',
    'V0875_RENDER_WORKER_SHUTDOWN','V0875_RIVER_TAP_GEOMETRY_SOURCE_DETAIL',
    'V0874_HIDE_RAIN_ONLY_MAP_STATIONS','V0874_NEPAL_FIXED_CAMERA',
    'V0874_FLOW_BELOW_NEPAL_MASK','V0874_RISK_BELOW_NEPAL_MASK'
]:
    if x not in m:raise SystemExit('v0875 map contract missing: '+x)
for bad in ['maxAnimated=700','main.postDelayed(this,120L);']:
    if bad in m:raise SystemExit('v0875 heavy animation regression remained: '+bad)
if 'versionCode 95' not in g or "versionName '0.8.75'" not in g:
    raise SystemExit('v0875 version verification failed')
print('FloodSafe v0.8.75 PASS: touch-first smooth map + lightweight flow + async risk geometry + geometry-safe full river detail')
