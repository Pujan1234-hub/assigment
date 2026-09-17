from pathlib import Path
root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')
if 'private void v848PromoteRiskLayers()' not in m:
 h=r'''    private void v848PromoteRiskLayers(){if(!styleReady||style==null)return;String[] src={"fs-river-normal-status","fs-river-alert-status","fs-river-warning-status","fs-river-danger-status"};String[] id={"fs-river-normal-status-layer","fs-river-alert-status-layer","fs-river-warning-status-layer","fs-river-danger-status-layer"};String[] col={"#22C8FF","#FFD447","#FF9418","#F04444"};float[] cw={2.8f,3.2f,3.7f,4.2f},gw={6.4f,7.2f,8.2f,9.3f};try{for(int i=0;i<src.length;i++){if(style.getSource(src[i])==null)continue;try{style.removeLayer(id[i]);}catch(Exception ignored){}try{style.removeLayer(id[i]+"-glow");}catch(Exception ignored){}style.addLayer(new LineLayer(id[i]+"-glow",src[i]).withProperties(lineColor(col[i]),lineWidth(gw[i]),lineOpacity(0.58f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));style.addLayer(new LineLayer(id[i],src[i]).withProperties(lineColor(col[i]),lineWidth(cw[i]),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));}}catch(Exception ignored){}} // V0848_FLOOD_COLOUR_PRIORITY

'''
 m=m.replace('    private void ensurePointSource(',h+'    private void ensurePointSource(',1)
# Put risk layers above moving cyan flow layers after style install.
is_=m.find('    private void installGeoLayers()');ie=m.find('    private void ensurePointSource(',is_);b=m[is_:ie]
if 'v848PromoteRiskLayers();' not in b:
 if 'ensureV847FlowLayers();' not in b:raise SystemExit('v0847 flow install anchor')
 b=b.replace('ensureV847FlowLayers();','ensureV847FlowLayers();\n            v848PromoteRiskLayers();',1);m=m[:is_]+b+m[ie:]
# Re-assert after each source/status refresh, not every animation frame.
for anchor in ['            refreshRiverStatusSources();','                refreshRiverStatusSources();']:
 if anchor in m and 'V0848_STATUS_COLOUR_REFRESH' not in m:
  m=m.replace(anchor,anchor+'\n            v848PromoteRiskLayers(); // V0848_STATUS_COLOUR_REFRESH',1);break
# version
g=g.replace('versionCode 67','versionCode 68',1).replace("versionName '0.8.47'","versionName '0.8.48'",1)
if 'versionCode 68' not in g or "versionName '0.8.48'" not in g:raise SystemExit('version bump')
for x in ['V0848_FLOOD_COLOUR_PRIORITY','V0847_MOVING_GLOW','V0844_VISIBLE_EQUALS_TOUCHABLE']:
 if x not in m:raise SystemExit('missing '+x)
m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.48 flood colours over moving flow PASS')
