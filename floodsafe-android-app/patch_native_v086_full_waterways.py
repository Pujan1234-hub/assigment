from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
helper_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
helper = helper_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# v0.8.6: match the old web map architecture instead of keeping only 1,400 ways.
# Use the bundled 6,279-way overview nationally, then swap in full local tile detail
# after camera movement/zoom. The full snapshot contains ~61k waterways, so rendering
# all of them nationally would regress the smooth native map.
old_load = '''                try { raw = readAsset("data/nepal-waterways-snapshot.json"); }
                catch (Exception e) { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }'''
new_load = '''                try { raw = readAsset("data/nepal-waterways-tiles/overview.json"); }
                catch (Exception e) { raw = readAsset("data/nepal-waterways-snapshot.json"); }'''
if old_load in helper:
    helper = helper.replace(old_load, new_load, 1)
elif 'readAsset("data/nepal-waterways-tiles/overview.json")' not in helper:
    raise SystemExit('waterway overview load anchor missing')

helper = helper.replace(
    'if (all.size() > 1400) all = new ArrayList<>(all.subList(0, 1400));',
    'if (all.size() > 6400) all = new ArrayList<>(all.subList(0, 6400));', 1)

if 'private final List<RiverWay> overviewRivers = new ArrayList<>();' not in helper:
    helper = helper.replace(
        'private final List<RiverWay> rivers = new ArrayList<>();',
        'private final List<RiverWay> rivers = new ArrayList<>();\n    private final List<RiverWay> overviewRivers = new ArrayList<>();\n    private String lastRiverTileKey = "";\n    private int riverTileGeneration = 0;', 1)

if 'overviewRivers.addAll(all);' not in helper:
    helper = helper.replace(
        'rivers.clear();\n                    rivers.addAll(all);',
        'rivers.clear();\n                    rivers.addAll(all);\n                    overviewRivers.clear();\n                    overviewRivers.addAll(all);', 1)

# Refresh detailed local waterway tiles only after the camera stops moving.
if 'addOnCameraIdleListener(this::refreshVisibleRiverTiles)' not in helper:
    helper = helper.replace(
        'map.addOnMapClickListener(this::onMapClick);',
        'map.addOnMapClickListener(this::onMapClick);\n            map.addOnCameraIdleListener(this::refreshVisibleRiverTiles);', 1)

helper = helper.replace(
    'main.post(this::installGeoLayers);',
    'main.post(() -> { installGeoLayers(); lastRiverTileKey=""; refreshVisibleRiverTiles(); });', 1)

methods_anchor = '    private void installGeoLayers() {'
methods = r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp = map.getCameraPosition();
        double zoom = cp.zoom;
        LatLng center = cp.target;
        if (zoom < 7.0) {
            if ("overview".equals(lastRiverTileKey)) return;
            lastRiverTileKey = "overview";
            riverTileGeneration++;
            List<RiverWay> base = new ArrayList<>(overviewRivers);
            rivers.clear(); rivers.addAll(base);
            try {
                riversGeoJson = makeRiversGeoJson(base);
                riverLabelsGeoJson = makeRiverLabelsGeoJson(base);
                setGeo("fs-rivers", riversGeoJson);
                setGeo("fs-river-labels", riverLabelsGeoJson);
            } catch (Exception ignored) {}
            return;
        }
        int cx = Math.max(0, Math.min(11, (int)Math.floor((center.getLongitude()-80.0)/0.7)));
        int cy = Math.max(0, Math.min(7, (int)Math.floor((center.getLatitude()-26.2)/0.6)));
        int radius = zoom < 8.4 ? 1 : 0;
        String key = cx+":"+cy+":"+radius;
        if (key.equals(lastRiverTileKey)) return;
        lastRiverTileKey = key;
        final int generation = ++riverTileGeneration;
        final double z = zoom;
        io.execute(() -> {
            try {
                JSONObject districts = districtGeoJson == null ? null : new JSONObject(districtGeoJson);
                List<RiverWay> merged = new ArrayList<>();
                java.util.HashSet<String> seen = new java.util.HashSet<>();
                int baseCount = Math.min(overviewRivers.size(), z < 8.4 ? 3200 : 1400);
                for (int i=0;i<baseCount;i++) {
                    RiverWay r=overviewRivers.get(i); String k=riverKey(r);
                    if(seen.add(k)) merged.add(r);
                }
                for (int x=Math.max(0,cx-radius); x<=Math.min(11,cx+radius); x++) {
                    for (int y=Math.max(0,cy-radius); y<=Math.min(7,cy+radius); y++) {
                        List<RiverWay> tile = readRiverTile(x,y,districts);
                        for (RiverWay r:tile) if(seen.add(riverKey(r))) merged.add(r);
                    }
                }
                String geo = makeRiversGeoJson(merged);
                String labels = makeRiverLabelsGeoJson(merged);
                main.post(() -> {
                    if (generation != riverTileGeneration) return;
                    rivers.clear(); rivers.addAll(merged);
                    riversGeoJson = geo; riverLabelsGeoJson = labels;
                    setGeo("fs-rivers", geo);
                    setGeo("fs-river-labels", labels);
                });
            } catch (Exception ignored) {}
        });
    }

    private List<RiverWay> readRiverTile(int x,int y,JSONObject districts) {
        List<RiverWay> out=new ArrayList<>();
        try {
            JSONObject root=new JSONObject(readAsset("data/nepal-waterways-tiles/"+x+"-"+y+".json"));
            JSONArray ways=root.optJSONArray("waterways");
            if(ways==null)return out;
            for(int i=0;i<ways.length();i++){
                JSONObject w=ways.optJSONObject(i); if(w==null)continue;
                JSONArray pts=w.optJSONArray("pts"); if(pts==null||pts.length()<2)continue;
                RiverWay rw=new RiverWay();
                rw.name=firstNonEmpty(w.optString("name_ne"),w.optString("name"),w.optString("name_en"),"नदी / खोला");
                rw.type=w.optString("type","stream");
                for(int j=0;j<pts.length();j++){
                    JSONArray p=pts.optJSONArray(j); if(p==null||p.length()<2)continue;
                    double lo=p.optDouble(0,Double.NaN),la=p.optDouble(1,Double.NaN);
                    if(Double.isFinite(la)&&Double.isFinite(lo)&&isNepalish(la,lo))rw.points.add(new double[]{lo,la});
                }
                if(districts!=null&&rw.points.size()>=2)trimRiverToNepal(rw,districts);
                if(rw.points.size()>=2)out.add(rw);
            }
        } catch(Exception ignored) {}
        return out;
    }

    private static String riverKey(RiverWay r) {
        if(r==null||r.points.isEmpty())return "";
        double[] a=r.points.get(0),b=r.points.get(r.points.size()-1);
        return (r.type==null?"":r.type)+"|"+(r.name==null?"":r.name.toLowerCase(Locale.ROOT))+"|"+
                String.format(Locale.US,"%.4f,%.4f|%.4f,%.4f",a[0],a[1],b[0],b[1]);
    }

'''
if 'private void refreshVisibleRiverTiles()' not in helper:
    if methods_anchor not in helper: raise SystemExit('installGeoLayers anchor missing')
    helper = helper.replace(methods_anchor, methods + methods_anchor, 1)

# All displayed rivers get a bright animated trace; particles remain a secondary
# directional visual cue. Official station status remains the only realtime risk truth.
core = '''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(
                        lineColor("#7ceeff"), lineWidth(2.65f), lineOpacity(1.0f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
trace = core + '''
                style.addLayer(new LineLayer("fs-river-flow-trace", "fs-rivers").withProperties(
                        lineColor("#e9fdff"), lineWidth(0.9f), lineOpacity(0.62f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
if 'fs-river-flow-trace' not in helper:
    if core not in helper: raise SystemExit('v0.8.5 core river layer anchor missing')
    helper = helper.replace(core, trace, 1)

helper = helper.replace('if(++count>=420)break;', 'if(++count>=900)break;', 1)
helper = helper.replace('int n = Math.min(96, rivers.size());', 'int n = Math.min(220, rivers.size());', 1)

pulse_anchor = '                JSONArray features = new JSONArray();\n                int n = Math.min(220, rivers.size());'
pulse = '''                JSONArray features = new JSONArray();
                try {
                    LineLayer flowTrace = style.getLayerAs("fs-river-flow-trace");
                    if(flowTrace!=null){double ph=(System.currentTimeMillis()%1800L)/1800.0;float glow=(float)(0.42+0.42*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(0.75f+0.45f*glow));}
                } catch(Exception ignored) {}
                int n = Math.min(220, rivers.size());'''
if pulse_anchor in helper:
    helper = helper.replace(pulse_anchor, pulse, 1)

helper_path.write_text(helper,encoding='utf-8')

if "versionName '0.8.6'" not in gradle:
    gradle=gradle.replace('versionCode 25','versionCode 26',1)
    gradle=gradle.replace("versionName '0.8.5'","versionName '0.8.6'",1)
if 'versionCode 26' not in gradle or "versionName '0.8.6'" not in gradle:
    raise SystemExit('v0.8.6 version bump failed')
gradle_path.write_text(gradle,encoding='utf-8')

index_path=root.parent/'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index=index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.5</span>','<span class="badge green">v0.8.6</span>')
    index_path.write_text(index,encoding='utf-8')

h=helper_path.read_text(encoding='utf-8')
for marker in ['overviewRivers','refreshVisibleRiverTiles','readRiverTile','data/nepal-waterways-tiles/','fs-river-flow-trace','Math.min(220, rivers.size())','all.size() > 6400']:
    if marker not in h: raise SystemExit('v0.8.6 marker missing: '+marker)
print('FloodSafe v0.8.6 progressive full waterways + all-river animated glow patch PASS')
