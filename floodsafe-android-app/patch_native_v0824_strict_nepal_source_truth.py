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

# v0.8.24 field lock from real-phone screenshots:
# 1. NEVER draw a river coordinate outside the union of Nepal's 77 district polygons.
# 2. Map text = district/place context only; river names appear only after tapping a river.
# 3. Static OSM river geometry is geographic context; live colour/glow comes only from the
#    current, same-river BIPAD/DHM official gauge truth already loaded by NativeFullActivity.
# 4. River tap is river-first and never borrows an unrelated nearest gauge.
# 5. Rain stations stay off the river map; source-exact BIPAD/DHM rain data remains available
#    in the app's rain information pipeline.

# SymbolLayer/text imports are needed for the 77-district labels. Older patches normally
# provide them, but make this patch self-defending against chain changes.
if 'import org.maplibre.android.style.layers.SymbolLayer;' not in m:
    m=m.replace('import org.maplibre.android.style.layers.LineLayer;\n',
                'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.layers.SymbolLayer;\n',1)
for name in ['textField','textSize','textColor','textHaloColor','textHaloWidth','textAllowOverlap']:
    imp='import static org.maplibre.android.style.layers.PropertyFactory.'+name+';'
    if imp not in m:
        anchor='import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;'
        if anchor not in m: raise SystemExit('PropertyFactory import anchor missing')
        m=m.replace(anchor,anchor+'\n'+imp,1)

# The Esri reference raster mixes non-district labels (including waterways/outside-Nepal text).
# Remove that label layer at runtime. We add our own trusted district labels below.
install_try='''    private void installGeoLayers() {
        if (!styleReady || style == null) return;
        try {'''
if install_try not in m: raise SystemExit('installGeoLayers start missing')
if 'v0.8.24 remove mixed Esri label layer' not in m:
    m=m.replace(install_try,install_try+'''\n            // v0.8.24 remove mixed Esri label layer; district names are rendered from Nepal GeoJSON.\n            try { if (style.getLayer("places") != null) style.removeLayer("places"); } catch (Exception ignored) {}''',1)

# Never create the generic river-name text layer. Its GeoJSON may still be retained as a
# harmless compatibility source, but it is always empty.
river_label_block=re.compile(r'''\n\s*if \(riverLabelsGeoJson != null && style\.getSource\("fs-river-labels"\) == null\) \{.*?\n\s*\}\n''',re.S)
m,n=river_label_block.subn('\n            // v0.8.24: river names are shown only in the tap dialog, never painted on the map.\n',m,count=1)
if n==0 and 'new SymbolLayer("fs-river-labels-layer"' in m:
    raise SystemExit('river label layer block could not be removed')
m=m.replace('riverLabelsGeoJson = makeRiverLabelsGeoJson(all);','riverLabelsGeoJson = emptyFeatureCollection();')
m=m.replace('riverLabelsGeoJson=makeRiverLabelsGeoJson(all);','riverLabelsGeoJson=emptyFeatureCollection();')

# Restore clear district names from the same 77-district GeoJSON used for strict clipping.
river_anchor='''            if (riversGeoJson != null && style.getSource("fs-rivers") == null) {'''
district_layer='''            if (districtGeoJson != null && style.getSource("fs-districts") != null && style.getLayer("fs-district-labels") == null) {
                style.addLayer(new SymbolLayer("fs-district-labels", "fs-districts").withProperties(
                        textField("{nameEn}"), textSize(10.4f), textColor("#ffffff"),
                        textHaloColor("#173646"), textHaloWidth(1.8f), textAllowOverlap(false)));
            }
'''
if 'new SymbolLayer("fs-district-labels"' not in m:
    if river_anchor not in m: raise SystemExit('river install anchor missing for district labels')
    m=m.replace(river_anchor,district_layer+river_anchor,1)

# -----------------------------------------------------------------------------
# STRICT Nepal-only visible renderer.
# v0.8.23 skipped polygon clipping for an "interior" viewport; field screenshots proved
# that tile contents can still contain cross-border waterways. v0.8.24 clips EVERY route,
# local or national, against the actual district union and publishes only inside points.
# -----------------------------------------------------------------------------
start=m.find('    private void refreshVisibleRiverTiles() {')
end=m.find('    private static double webVisibleScore(',start)
if start<0 or end<0: raise SystemExit('refreshVisibleRiverTiles anchors missing')
new_refresh=r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp=map.getCameraPosition();
        final double zoom=cp.zoom; final LatLng center=cp.target;
        if(!cameraTargetInsideNepal(center)){map.animateCamera(CameraUpdateFactory.newLatLng(NEPAL_CENTER),250);return;}
        // No district polygon = no cyan river publish. A missing mask must fail closed, not leak abroad.
        if(districtGeoJson==null||districtGeoJson.trim().isEmpty())return;

        double west=center.getLongitude()-0.40,east=center.getLongitude()+0.40;
        double south=center.getLatitude()-0.32,north=center.getLatitude()+0.32;
        try{
            LatLngBounds vb=map.getProjection().getVisibleRegion().latLngBounds;
            west=vb.getLonWest();east=vb.getLonEast();south=vb.getLatSouth();north=vb.getLatNorth();
        }catch(Exception ignored){}
        if(east<west){double t=west;west=east;east=t;} if(north<south){double t=south;south=north;north=t;}
        double padLon=Math.max(0.006,(east-west)*0.08),padLat=Math.max(0.006,(north-south)*0.08);
        final double fw=Math.max(79.95,west-padLon),fe=Math.min(88.30,east+padLon);
        final double fs=Math.max(26.25,south-padLat),fn=Math.min(30.55,north+padLat);
        final int minX=Math.max(0,Math.min(11,(int)Math.floor((fw-80.0)/0.7)));
        final int maxX=Math.max(0,Math.min(11,(int)Math.floor((fe-80.0)/0.7)));
        final int minY=Math.max(0,Math.min(7,(int)Math.floor((fs-26.2)/0.6)));
        final int maxY=Math.max(0,Math.min(7,(int)Math.floor((fn-26.2)/0.6)));
        final String key=(zoom<7.7?"national":"local")+":"+minX+":"+maxX+":"+minY+":"+maxY+":"+
                Math.round(center.getLatitude()*400.0)+":"+Math.round(center.getLongitude()*400.0)+":"+Math.round(zoom*8.0);
        if(key.equals(lastRiverTileKey))return; lastRiverTileKey=key; final int generation=++riverTileGeneration;

        io.execute(()->{
            try{
                JSONObject nepal=new JSONObject(districtGeoJson);
                List<RiverWay> candidates=new ArrayList<>(); java.util.HashSet<String> seen=new java.util.HashSet<>();
                if(zoom>=7.7){
                    for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++){
                        for(RiverWay r:readRiverTile(x,y,null)){
                            if(r==null||r.points.size()<2||!riverIntersectsBox(r,fw,fs,fe,fn))continue;
                            // Mid zoom remains readable. Close zoom includes every real OSM stream/river.
                            if(zoom<9.0&&!"river".equalsIgnoreCase(r.type)&&(r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name)))continue;
                            String k=riverKey(r);if(seen.add(k))candidates.add(r);
                        }
                    }
                }else{
                    for(RiverWay src:overviewRivers){
                        if(src==null||src.points.size()<2||!"river".equalsIgnoreCase(src.type))continue;
                        if(src.name==null||src.name.trim().isEmpty()||"नदी / खोला".equals(src.name))continue;
                        if(!riverIntersectsBox(src,fw,fs,fe,fn))continue;
                        String k=riverKey(src);if(seen.add(k))candidates.add(copyRiverStrict(src));
                        if(candidates.size()>=260)break;
                    }
                }
                // ABSOLUTE RULE: every published coordinate must lie inside one of Nepal's 77 districts.
                List<RiverWay> chosen=splitWaysToNepalStrict(candidates,nepal);
                String geo=makeRiversGeoJson(chosen); final List<RiverWay> publish=new ArrayList<>(chosen);
                main.post(()->{
                    if(generation!=riverTileGeneration)return;
                    rivers.clear();rivers.addAll(publish);riversGeoJson=geo;riverLabelsGeoJson=emptyFeatureCollection();
                    setGeo("fs-rivers",geo);setGeo("fs-river-labels",emptyFeatureCollection());refreshRiverStatusSources();
                });
            }catch(Exception ignored){}
        });
    }

    private static RiverWay copyRiverStrict(RiverWay src){
        RiverWay r=new RiverWay();r.name=src.name;r.matchName=src.matchName;r.type=src.type;
        for(double[]p:src.points)r.points.add(new double[]{p[0],p[1]});return r;
    }

    private static List<RiverWay> splitWaysToNepalStrict(List<RiverWay> ways,JSONObject nepal){
        List<RiverWay> out=new ArrayList<>();if(nepal==null)return out;
        for(RiverWay src:ways){
            RiverWay cur=null;
            for(double[]p:src.points){
                boolean inside=false;try{inside=insideDistricts(p[0],p[1],nepal);}catch(Exception ignored){}
                if(inside){
                    if(cur==null){cur=new RiverWay();cur.name=src.name;cur.matchName=src.matchName;cur.type=src.type;}
                    cur.points.add(new double[]{p[0],p[1]});
                }else if(cur!=null){if(cur.points.size()>=2)out.add(cur);cur=null;}
            }
            if(cur!=null&&cur.points.size()>=2)out.add(cur);
        }
        return out;
    }

    private static boolean riverIntersectsBox(RiverWay r,double west,double south,double east,double north){
        if(r==null||r.points.size()<2)return false;
        for(int i=1;i<r.points.size();i++){
            double[]a=r.points.get(i-1),b=r.points.get(i);
            double minX=Math.min(a[0],b[0]),maxX=Math.max(a[0],b[0]),minY=Math.min(a[1],b[1]),maxY=Math.max(a[1],b[1]);
            if(maxX>=west&&minX<=east&&maxY>=south&&minY<=north)return true;
        }return false;
    }

'''
m=m[:start]+new_refresh+m[end:]

# Base geometry = thin geographic cyan, not a giant false-live glow. Current official
# same-river status overlays below are what provide strong colour/glow.
m=re.sub(r'lineColor\("#1edcff"\), lineWidth\(2\.35f\), lineOpacity\(0\.98f\)',
         'lineColor("#58d9ef"), lineWidth(1.55f), lineOpacity(0.88f)',m,count=1)
m=re.sub(r'lineColor\("#003f55"\), lineWidth\(5\.2f\), lineOpacity\(0\.72f\)',
         'lineColor("#0b5060"), lineWidth(3.2f), lineOpacity(0.28f)',m,count=1)
# Compatibility with nearby generated variants.
m=m.replace('lineColor("#003f55"), lineWidth(7.0f), lineOpacity(0.88f)',
            'lineColor("#0b5060"), lineWidth(3.2f), lineOpacity(0.28f)',1)
m=m.replace('lineColor("#18e6ff"), lineWidth(3.2f), lineOpacity(1.0f)',
            'lineColor("#58d9ef"), lineWidth(1.55f), lineOpacity(0.88f)',1)

# Exact official status overlays. Raw source status remains the text truth; this palette
# only visualizes the current same-river match.
status_pat=r'''    private void ensureRiverStatusLayer\(String sourceId,String layerId,String color\) \{.*?\n    \}\n'''
status_new=r'''    private void ensureRiverStatusLayer(String sourceId,String layerId,String color) {
        if(style==null||style.getSource(sourceId)!=null)return;
        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        boolean normal=layerId.contains("normal"),alert=layerId.contains("alert"),warning=layerId.contains("warning"),danger=layerId.contains("danger");
        float glowOpacity=normal?0.16f:(alert?0.24f:(warning?0.34f:0.44f));
        float glowWidth=normal?5.0f:(alert?6.0f:(warning?7.6f:9.0f));
        float coreWidth=normal?2.5f:(alert?2.9f:(warning?3.4f:4.0f));
        style.addLayer(new LineLayer(layerId+"-glow",sourceId).withProperties(lineColor(color),lineWidth(glowWidth),lineOpacity(glowOpacity),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(coreWidth),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }
'''
m,n=re.subn(status_pat,status_new,m,count=1,flags=re.S)
if n!=1: raise SystemExit('ensureRiverStatusLayer block missing')

# Tap the actual river first. Hidden/nearby gauge dots must not steal the river tap.
click_start=m.find('    private boolean onMapClick(LatLng p) {')
click_end=m.find('    private static boolean isSevereStage',click_start)
if click_start<0 or click_end<0: raise SystemExit('onMapClick anchors missing')
click_block=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.18,5.0/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.35,4.0/Math.pow(2.0,Math.max(0.0,zoom-6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        boolean stationShown=nearest!=null&&(zoom>=9.0||isSevereStage(nearest.stage));
        if(stationShown&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}
        return false;
    }

'''
m=m[:click_start]+click_block+m[click_end:]

# River popup = exact same-river current official reading. Never substitute a different river.
show_start=m.find('    private void showRiver(RiverWay r, double la, double lo) {')
show_end=m.find('    private StationDot sameRiverGaugeFor(',show_start)
if show_start<0 or show_end<0: raise SystemExit('showRiver/sameRiverGaugeFor anchors missing')
show_block=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot current=sameRiverGaugeFor(r,la,lo,true);
        StationDot known=current!=null?current:sameRiverGaugeFor(r,la,lo,false);
        String title=(r==null||r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name))?"नदी / खोला":r.name;
        StringBuilder x=new StringBuilder();
        if(current!=null){
            x.append("Current BIPAD/DHM official reading");
            x.append("\nGauge: ").append(current.name).append(String.format(Locale.US," • %.1f km",km(la,lo,current.lat,current.lon)));
            if(Double.isFinite(current.level))x.append(String.format(Locale.US,"\nWater level: %.2f m",current.level));
            if(Double.isFinite(current.warning))x.append(String.format(Locale.US,"\nWarning level: %.2f m",current.warning));
            if(Double.isFinite(current.danger))x.append(String.format(Locale.US,"\nDanger level: %.2f m",current.danger));
            String source=current.rawStatus==null?"":current.rawStatus.trim();
            x.append("\nSource status: ").append(source.isEmpty()?current.stage.toUpperCase(Locale.ROOT):source);
            x.append("\nOfficial time: ").append(formatOfficialTime(current.at));
        }else if(known!=null){
            x.append("यसै नदी/खोलाको official gauge छ, तर अहिले current official reading उपलब्ध छैन।")
             .append("\nGauge: ").append(known.name).append("\nStatus: STALE / UNKNOWN");
        }else{
            x.append("यो नदी/खोलामा matching official gauge भेटिएन।")
             .append("\nअर्को नदीको nearest gauge यहाँ देखाइँदैन।");
        }
        x.append("\n\nRiver geometry: OpenStreetMap • realtime status: BIPAD/DHM official source");
        new AlertDialog.Builder(getContext()).setTitle(title).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
m=m[:show_start]+show_block+m[show_end:]

# Flow/glow animation is only an animation of already-built current official status layers.
# Never animate every static waterway as if it were realtime.
pt_start=m.find('    private final Runnable particleTick = new Runnable() {')
pt_end=m.find('    private StationDot readStation(Object o) {',pt_start)
if pt_start<0 or pt_end<0: raise SystemExit('particleTick anchors missing')
pt_block=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                double ph=(System.currentTimeMillis()%1800L)/1800.0;
                float wave=(float)(0.5+0.5*Math.sin(ph*Math.PI*2.0));
                LineLayer ng=style.getLayerAs("fs-river-normal-status-layer-glow");
                LineLayer ag=style.getLayerAs("fs-river-alert-status-layer-glow");
                LineLayer wg=style.getLayerAs("fs-river-warning-status-layer-glow");
                LineLayer dg=style.getLayerAs("fs-river-danger-status-layer-glow");
                if(ng!=null)ng.setProperties(lineOpacity(0.10f+0.10f*wave),lineWidth(4.6f+0.8f*wave));
                if(ag!=null)ag.setProperties(lineOpacity(0.16f+0.14f*wave),lineWidth(5.5f+1.0f*wave));
                if(wg!=null)wg.setProperties(lineOpacity(0.22f+0.20f*wave),lineWidth(6.8f+1.5f*wave));
                if(dg!=null)dg.setProperties(lineOpacity(0.30f+0.24f*wave),lineWidth(8.0f+2.0f*wave));
                setGeo("fs-flow-particles",emptyFeatureCollection());
            }catch(Exception ignored){}
            main.postDelayed(this,320L);
        }
    };

'''
m=m[:pt_start]+pt_block+m[pt_end:]

# Rain dots/click targets remain OFF the river map. The Activity still fetches the official
# latest rain feed and retains exact basin/time/status/1h-24h fields for rain information.
rain_start=m.find('    private void refreshRainSources() {')
rain_end=m.find('    private void refreshUserSource() {',rain_start)
if rain_start<0 or rain_end<0: raise SystemExit('rain source anchors missing')
rain_block=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;String e=emptyFeatureCollection();
        setGeo("fs-rain-stale",e);setGeo("fs-rain-normal",e);setGeo("fs-rain-alert",e);setGeo("fs-rain-warning",e);setGeo("fs-rain-danger",e);
    }

'''
m=m[:rain_start]+rain_block+m[rain_end:]

# Make the contract visible and unambiguous in the map subtitle.
sub_ne='जिल्ला नाम + नेपालभित्र actual नदी • पातलो cyan=geometry • Glow/रङ=current official gauge • नदीको नाम tap गर्दा • rain station mapमा छैन'
sub_en='District names + Nepal-only actual rivers • thin cyan=geometry • glow/colour=current official gauge • river name on tap • rain stations off-map'
# Replace the first map subtitle assignment regardless of the exact previous wording.
a,nsub=re.subn(r'mapSub\.setText\(t\("[^"\\]*(?:\\.[^"\\]*)*","[^"\\]*(?:\\.[^"\\]*)*"\)\);',
               'mapSub.setText(t("'+sub_ne+'","'+sub_en+'"));',a,count=1)
if nsub!=1: raise SystemExit('map subtitle assignment missing')

# Version bump.
if "versionName '0.8.24'" not in g:
    g=g.replace('versionCode 43','versionCode 44',1)
    g=g.replace("versionName '0.8.23'","versionName '0.8.24'",1)
if 'versionCode 44' not in g or "versionName '0.8.24'" not in g: raise SystemExit('v0.8.24 version bump failed')

m_path.write_text(m,encoding='utf-8');a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard truth gates. If any of these fail, CI must refuse to ship the APK.
m2=m_path.read_text(encoding='utf-8');a2=a_path.read_text(encoding='utf-8')
for marker in [
    'splitWaysToNepalStrict(candidates,nepal)','inside=insideDistricts(p[0],p[1],nepal)',
    'new SymbolLayer("fs-district-labels"','textField("{nameEn}")',
    'style.removeLayer("places")','riverLabelsGeoJson=emptyFeatureCollection()',
    'setGeo("fs-river-labels",emptyFeatureCollection())','sameRiverGaugeFor(r,la,lo,true)',
    'Current BIPAD/DHM official reading','अर्को नदीको nearest gauge यहाँ देखाइँदैन',
    'fs-river-normal-status-layer-glow','fs-river-warning-status-layer-glow','fs-river-danger-status-layer-glow',
    'setGeo("fs-flow-particles",emptyFeatureCollection())','setGeo("fs-rain-stale",e)']:
    if marker not in m2: raise SystemExit('v0.8.24 map marker missing: '+marker)
for bad in [
    'new SymbolLayer("fs-river-labels-layer"','fullyInside || nepal==null','chosen=candidates;',
    'boolean rainShown=','showRain(nearestRain)']:
    if bad in m2: raise SystemExit('v0.8.24 forbidden map behavior remained: '+bad)
for marker in ['rain-stations/?latest=true&limit=2000','rainAverage(r,1)','rainAverage(r,24)','rawStatus','basin']:
    if marker not in a2: raise SystemExit('v0.8.24 official rain pipeline marker missing: '+marker)
print('FloodSafe v0.8.24 STRICT Nepal-only + district labels + same-river realtime truth PASS')
