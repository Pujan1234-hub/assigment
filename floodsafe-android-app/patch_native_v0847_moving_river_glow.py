from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.47 visual-only river animation fix.
# The old animation could look static on a real phone because it mainly breathed line width/opacity.
# Keep every visible river as the real OSM/FloodSafe geometry, but add a true moving cyan/white
# highlight segment on the line itself. Official BIPAD/DHM status/data logic is untouched.

# 1) Ensure an animated line source + two glow layers are installed with the river layers.
install_start=m.find('    private void installGeoLayers()')
install_end=m.find('    private void ensurePointSource(',install_start)
if install_start<0 or install_end<0:
    raise SystemExit('v0.8.47 installGeoLayers anchors missing')
install=m[install_start:install_end]
if 'ensureV847FlowLayers();' not in install:
    anchor='            refreshStationSources();'
    if anchor in install:
        install=install.replace(anchor,'            ensureV847FlowLayers();\n'+anchor,1)
    else:
        # Later patch chains may put river status refresh before station refresh.
        anchor='            refreshRiverStatusSources();'
        if anchor not in install:
            raise SystemExit('v0.8.47 install flow-layer call anchor missing')
        install=install.replace(anchor,'            ensureV847FlowLayers();\n'+anchor,1)
    m=m[:install_start]+install+m[install_end:]

helper=r'''    private void ensureV847FlowLayers(){
        if(!styleReady||style==null)return;
        try{
            if(style.getSource("fs-river-flow-anim")==null){
                style.addSource(new GeoJsonSource("fs-river-flow-anim",emptyFeatureCollection()));
            }
            LineLayer halo=style.getLayerAs("fs-river-flow-anim-halo");
            if(halo==null){
                style.addLayer(new LineLayer("fs-river-flow-anim-halo","fs-river-flow-anim").withProperties(
                        lineColor("#65E9FF"),lineWidth(7.2f),lineOpacity(0.52f),
                        lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            }
            LineLayer core=style.getLayerAs("fs-river-flow-anim-core");
            if(core==null){
                style.addLayer(new LineLayer("fs-river-flow-anim-core","fs-river-flow-anim").withProperties(
                        lineColor("#F0FEFF"),lineWidth(2.15f),lineOpacity(0.96f),
                        lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            }
        }catch(Exception ignored){}
    }

    private void v847UpdateMovingGlow(long now){
        if(!styleReady||style==null)return;
        try{
            ensureV847FlowLayers();

            // Strong breathing halo on the complete visible network so no painted river is static.
            double wave=0.5+0.5*Math.sin(now/260.0);
            LineLayer baseGlow=style.getLayerAs("fs-river-glow");
            if(baseGlow!=null)baseGlow.setProperties(
                    lineOpacity((float)(0.28+0.40*wave)),
                    lineWidth((float)(5.0+2.8*wave)));
            LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
            if(baseCore!=null)baseCore.setProperties(
                    lineOpacity((float)(0.92+0.08*wave)),
                    lineWidth((float)(2.15+0.55*wave)));

            List<RiverWay> snap=new ArrayList<>(rivers);
            if(snap.isEmpty()){
                setGeo("fs-river-flow-anim",emptyFeatureCollection());
                return;
            }

            // One short moving highlight per visible river where practical. On extremely dense
            // local views rotate batches instead of pushing thousands of GeoJSON features/frame.
            int maxAnimated=700;
            int stride=Math.max(1,(int)Math.ceil(snap.size()/(double)maxAnimated));
            int batchOffset=stride<=1?0:(int)((now/480L)%stride);
            double phase=(now%4200L)/4200.0;
            JSONArray lines=new JSONArray();
            for(int ri=batchOffset;ri<snap.size();ri+=stride){
                RiverWay r=snap.get(ri);if(r==null||r.points.size()<2)continue;
                int segs=r.points.size()-1;
                double seed=(ri*0.6180339887498949)%1.0;
                double p=(phase+seed)%1.0;
                int center=Math.min(segs-1,Math.max(0,(int)Math.floor(p*segs)));
                int from=Math.max(0,center-1),to=Math.min(r.points.size()-1,center+2);
                JSONArray coords=new JSONArray();
                for(int j=from;j<=to;j++){
                    double[] q=r.points.get(j);if(q==null||q.length<2)continue;
                    coords.put(new JSONArray().put(q[0]).put(q[1]));
                }
                if(coords.length()>=2)lines.put(coords);
            }
            JSONObject geom=new JSONObject().put("type","MultiLineString").put("coordinates",lines);
            JSONObject feat=new JSONObject().put("type","Feature").put("geometry",geom).put("properties",new JSONObject());
            JSONObject fc=new JSONObject().put("type","FeatureCollection").put("features",new JSONArray().put(feat));
            setGeo("fs-river-flow-anim",fc.toString()); // V0847_MOVING_GLOW

            LineLayer halo=style.getLayerAs("fs-river-flow-anim-halo");
            if(halo!=null)halo.setProperties(
                    lineOpacity((float)(0.46+0.34*wave)),
                    lineWidth((float)(6.2+2.2*wave)));
            LineLayer core=style.getLayerAs("fs-river-flow-anim-core");
            if(core!=null)core.setProperties(
                    lineOpacity((float)(0.88+0.12*wave)),
                    lineWidth((float)(1.8+0.75*wave)));
        }catch(Exception ignored){}
    }

'''
anchor='    private void ensurePointSource('
if 'private void v847UpdateMovingGlow(long now)' not in m:
    if anchor not in m: raise SystemExit('v0.8.47 helper insertion anchor missing')
    m=m.replace(anchor,helper+anchor,1)

# 2) Drive the real line animation from the existing map animation loop.
ps=m.find('    private final Runnable particleTick')
if ps<0: raise SystemExit('v0.8.47 particleTick start missing')
# The Runnable ends before the next private method. Prefer the stable readStation anchor.
pe=m.find('    private StationDot readStation(',ps)
if pe<0:
    pe=m.find('    private RainDot readRain(',ps)
if pe<0: raise SystemExit('v0.8.47 particleTick end anchor missing')
block=m[ps:pe]
if 'V0847_MOVING_GLOW_TICK' not in block:
    delay=block.rfind('main.postDelayed(this,')
    if delay<0: raise SystemExit('v0.8.47 animation delay anchor missing')
    block=block[:delay]+'v847UpdateMovingGlow(System.currentTimeMillis()); /* V0847_MOVING_GLOW_TICK */\n            '+block[delay:]
    # Smooth enough to read as motion while keeping the native map responsive.
    import re
    block=re.sub(r'main\.postDelayed\(this,\s*\d+L\);','main.postDelayed(this,120L);',block,count=1)
    m=m[:ps]+block+m[pe:]

# 3) New APK version so the glow fix is distinguishable from the prior source-parity build.
g=g.replace('versionCode 66','versionCode 67',1).replace("versionName '0.8.46'","versionName '0.8.47'",1)
if 'versionCode 67' not in g or "versionName '0.8.47'" not in g:
    raise SystemExit('v0.8.47 version bump failed')

for marker in [
    'V0847_MOVING_GLOW','V0847_MOVING_GLOW_TICK','fs-river-flow-anim',
    'private void v847UpdateMovingGlow(long now)','lineWidth((float)(5.0+2.8*wave))',
    'main.postDelayed(this,120L);','V0844_VISIBLE_EQUALS_TOUCHABLE','V0845_SCREEN_SCALE_RIVER_TAP']:
    if marker not in m: raise SystemExit('v0.8.47 glow marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.47 true moving river-line glow animation PASS')
