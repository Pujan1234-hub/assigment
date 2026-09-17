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

# v0.8.35 FIELD FIX FROM REAL PHONE SCREENSHOT
# Root issue: native startup was opening the ~37.5 MB national snapshot before the
# lightweight tile renderer could publish any river geometry. Gauges therefore appeared
# while fs-rivers remained empty on real devices. Use the prepared OSM overview first,
# then visible small tiles. Restore official rain station tap/details. Safety logic untouched.

# -----------------------------------------------------------------------------
# 1) FAST geometry bootstrap: NEVER parse the 37.5 MB snapshot on app startup.
#    overview.json is the prepared Nepal-wide OSM network; local zoom still reads the
#    dense 12x8 tile files (e.g. 7-2 around Kathmandu).
# -----------------------------------------------------------------------------
ls=m.find('    private void loadBundledGeometry() {')
le=m.find('    private void installGeoLayers()',ls)
if ls<0 or le<0:
    raise SystemExit('v0.8.35 loadBundledGeometry anchors missing')
fast_loader=r'''    private void loadBundledGeometry() {
        io.execute(() -> {
            try {
                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");
            } catch (Exception ignored) {
                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}
            }
            try {
                // FAST_OVERVIEW_FIRST: small prepared OSM overview, not the 37.5 MB snapshot.
                String raw = readAsset("data/nepal-waterways-tiles/overview.json");
                JSONObject root = new JSONObject(raw);
                JSONArray ways = root.optJSONArray("waterways");
                List<RiverWay> all = new ArrayList<>();
                if (ways != null) {
                    for (int i=0;i<ways.length();i++) {
                        JSONObject w=ways.optJSONObject(i); if(w==null)continue;
                        JSONArray pts=w.optJSONArray("pts"); if(pts==null||pts.length()<2)continue;
                        RiverWay rw=new RiverWay();
                        rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");
                        rw.matchName=rw.name;
                        rw.type=w.optString("type","stream");
                        for(int j=0;j<pts.length();j++){
                            JSONArray p=pts.optJSONArray(j);if(p==null||p.length()<2)continue;
                            double lo=p.optDouble(0,Double.NaN),la=p.optDouble(1,Double.NaN);
                            if(Double.isFinite(la)&&Double.isFinite(lo)&&isNepalish(la,lo))rw.points.add(new double[]{lo,la});
                        }
                        if(rw.points.size()>=2)all.add(rw);
                    }
                }
                // Exact 77-district union stays authoritative before anything becomes visible.
                List<RiverWay> safeAll=all;
                try{
                    if(districtGeoJson!=null){
                        JSONObject nepalRoot=new JSONObject(districtGeoJson);
                        List<RiverWay> clipped=clipWaysToNepalDense(all,nepalRoot);
                        if(clipped!=null&&!clipped.isEmpty())safeAll=clipped;
                    }
                }catch(Exception ignoredClip){}
                safeAll.sort(Comparator.comparingInt(FloodSafeNativeMapView::riverScore).reversed());
                rivers.clear();rivers.addAll(safeAll);
                overviewRivers.clear();overviewRivers.addAll(safeAll);
                riversGeoJson=makeRiversGeoJson(safeAll);
                riverLabelsGeoJson=emptyFeatureCollection();
            } catch (Exception ignored) {}
            main.post(()->{
                installGeoLayers();
                if(riversGeoJson!=null&&!riversGeoJson.isEmpty())setGeo("fs-rivers",riversGeoJson);
                refreshRiverStatusSources();
                lastRiverTileKey="";
                main.removeCallbacks(particleTick);
                if(animationRunning)main.post(particleTick);
                main.postDelayed(this::refreshVisibleRiverTiles,80L);
                main.postDelayed(this::refreshVisibleRiverTiles,650L);
                main.postDelayed(this::refreshVisibleRiverTiles,1800L);
            });
        });
    }

'''
m=m[:ls]+fast_loader+m[le:]

# -----------------------------------------------------------------------------
# 2) Make the blue Nepal water network unmistakably visible over satellite imagery.
#    This is geographic OSM geometry only; official status colours remain source-driven.
# -----------------------------------------------------------------------------
m=m.replace('lineColor("#22C8FF"), lineWidth(2.20f), lineOpacity(1.0f)',
            'lineColor("#22C8FF"), lineWidth(3.20f), lineOpacity(1.0f)',1)
m=m.replace('lineColor("#0D8DFF"), lineWidth(5.6f), lineOpacity(0.34f)',
            'lineColor("#0D8DFF"), lineWidth(8.0f), lineOpacity(0.42f)',1)
m=m.replace('lineWidth((float)(4.7+1.7*wave))','lineWidth((float)(6.8+2.4*wave))',1)
m=m.replace('lineWidth((float)(1.95+0.55*wave))','lineWidth((float)(2.8+0.65*wave))',1)

# Local visible tiles must repaint immediately after a pan/zoom. Rain visibility follows zoom too.
cam='map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);'
if cam not in m: raise SystemExit('v0.8.35 camera river refresh anchor missing')
if 'map.addOnCameraIdleListener(this::refreshRainSources);' not in m:
    m=m.replace(cam,cam+'\n            map.addOnCameraIdleListener(this::refreshRainSources);',1)

# -----------------------------------------------------------------------------
# 3) Restore official rain station layers (v0.8.20 intentionally blanked them).
#    Keep normal/stale rain dots for local zoom; severe source bands may remain visible
#    one step farther out. All values come from the existing BIPAD/DHM rain feed objects.
# -----------------------------------------------------------------------------
rs=m.find('    private void refreshRainSources() {')
re_=m.find('    private void refreshUserSource() {',rs)
if rs<0 or re_<0: raise SystemExit('v0.8.35 refreshRainSources anchors missing')
rain_refresh=r'''    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        List<RainDot> snapshot; synchronized (rainStations) { snapshot = new ArrayList<>(rainStations); }
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        boolean local=zoom>=7.0;
        setGeo("fs-rain-stale", local?rainGeo(snapshot,"stale"):emptyFeatureCollection());
        setGeo("fs-rain-normal", local?rainGeo(snapshot,"normal"):emptyFeatureCollection());
        setGeo("fs-rain-alert", rainGeo(snapshot,"alert"));
        setGeo("fs-rain-warning", rainGeo(snapshot,"warning"));
        setGeo("fs-rain-danger", rainGeo(snapshot,"danger"));
    }

'''
m=m[:rs]+rain_refresh+m[re_:]

# -----------------------------------------------------------------------------
# 4) Tap priority = actual river first, then river gauge, then rain station.
#    River never borrows another river's nearest gauge; showRiver keeps sameRiverGaugeFor().
# -----------------------------------------------------------------------------
cs=m.find('    private boolean onMapClick(LatLng p) {')
ce=m.find('    private static boolean isSevereStage',cs)
if cs<0 or ce<0: raise SystemExit('v0.8.35 onMapClick anchors missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.16,5.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}

        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.30,4.2/Math.pow(2.0,Math.max(0.0,zoom-6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        boolean stationShown=nearest!=null&&(zoom>=8.0||isSevereStage(nearest.stage));
        if(stationShown&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}

        RainDot rain=nearestRain(p.getLatitude(),p.getLongitude());
        double rainThreshold=Math.max(0.34,4.6/Math.pow(2.0,Math.max(0.0,zoom-6.0)));
        double rd=rain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),rain.lat,rain.lon);
        if(rain!=null&&zoom>=7.0&&rd<=rainThreshold){showRain(rain);return true;}
        return false;
    }

'''
m=m[:cs]+click+m[ce:]

# Rain detail uses the same non-dimming in-map white panel as river/station details.
ss=m.find('    private void showRain(RainDot r){')
se=m.find('    private void startParticles() {',ss)
if ss<0 or se<0: raise SystemExit('v0.8.35 showRain anchors missing')
show_rain=r'''    private void showRain(RainDot r){
        if(r==null)return;
        StringBuilder x=new StringBuilder();
        x.append("BIPAD/DHM official rain station");
        if(r.basin!=null&&!r.basin.isEmpty())x.append("\nBasin: ").append(r.basin);
        if(Double.isFinite(r.rainfall))x.append(String.format(Locale.US,"\nRain 1h: %.1f mm",r.rainfall));
        if(Double.isFinite(r.rain3))x.append(String.format(Locale.US,"\nRain 3h: %.1f mm",r.rain3));
        if(Double.isFinite(r.rain6))x.append(String.format(Locale.US,"\nRain 6h: %.1f mm",r.rain6));
        if(Double.isFinite(r.rain12))x.append(String.format(Locale.US,"\nRain 12h: %.1f mm",r.rain12));
        if(Double.isFinite(r.rain24))x.append(String.format(Locale.US,"\nRain 24h: %.1f mm",r.rain24));
        x.append("\nReading: ").append(r.fresh?"LATEST":"STALE / OLD");
        x.append("\nOfficial time: ").append(formatOfficialTime(r.at));
        if(r.rawStatus!=null&&!r.rawStatus.isEmpty())x.append("\nSource status: ").append(r.rawStatus);
        if(stationTapListener!=null){stationTapListener.onStationTap(new RiverTapInfo("🌧️ "+r.name,x.toString()));return;}
        new AlertDialog.Builder(getContext()).setTitle("Rain • "+r.name).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
m=m[:ss]+show_rain+m[se:]

# Give river detail its own icon now that the shared Activity card also accepts rain.
m=m.replace('new RiverTapInfo(title,x.toString())','new RiverTapInfo("🌊 "+title,x.toString())',1)
a=a.replace('TextView h=text("🌊 "+(title==null?"":title),20,true,Color.rgb(16,39,70));',
            'TextView h=text(title==null?"":title,20,true,Color.rgb(16,39,70));',1)
a=a.replace('स्रोत: BIPAD / DHM official • source मा matching current gauge नभए app ले अर्को स्टेशनको data राख्दैन।',
            'स्रोत: BIPAD / DHM official • source मा जे उपलब्ध छ त्यही मात्र देखाइन्छ; app ले data बनाउँदैन।',1)
a=a.replace('Source: BIPAD / DHM official • if no matching current gauge exists, the app does not substitute another station.',
            'Source: BIPAD / DHM official • only source-provided values are shown; the app does not invent data.',1)

# Version bump only.
g=g.replace('versionCode 54','versionCode 55',1).replace("versionName '0.8.34'","versionName '0.8.35'",1)
if 'versionCode 55' not in g or "versionName '0.8.35'" not in g:
    raise SystemExit('v0.8.35 version bump failed')

# Hard gates: fast OSM network, local dense tiles, source-truth details, rain taps, safety unchanged.
for marker in [
    'FAST_OVERVIEW_FIRST',
    'readAsset("data/nepal-waterways-tiles/overview.json")',
    'overviewRivers.addAll(safeAll)',
    'readRiverTile(x,y,null)',
    'setGeo("fs-rivers",riversGeoJson)',
    'lineWidth((float)(6.8+2.4*wave))',
    'lineWidth((float)(2.8+0.65*wave))',
    'map.addOnCameraIdleListener(this::refreshRainSources)',
    'setGeo("fs-rain-normal", local?rainGeo(snapshot,"normal")',
    'RainDot rain=nearestRain',
    'new RiverTapInfo("🌧️ "+r.name',
    'sameRiverGaugeFor',
    'routeD<=0.75']:
    if marker not in m: raise SystemExit('v0.8.35 map marker missing: '+marker)
if 'readAsset("data/nepal-waterways-snapshot.json")' in fast_loader:
    raise SystemExit('v0.8.35 huge startup snapshot returned')
for marker in ['bestD<=2d','best.fresh','best.stage.equals("warning")','best.stage.equals("danger")']:
    if marker not in a: raise SystemExit('alert safety changed unexpectedly: '+marker)

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.35 FAST overview + visible Nepal rivers + rain tap details PASS')
