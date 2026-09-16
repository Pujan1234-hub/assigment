from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
helper = map_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')


def replace_between(text, start, end, replacement, label):
    a = text.find(start)
    if a < 0:
        raise SystemExit(label + ' start anchor missing')
    b = text.find(end, a)
    if b < 0:
        raise SystemExit(label + ' end anchor missing')
    return text[:a] + replacement + text[b:]

# v0.8.11: eliminate map-start ANR. v0.8.10 synchronously scanned all rivers
# four times on the UI thread whenever stations/tiles changed. Build all four
# status collections in one background pass, debounce repeated refresh requests,
# then publish the finished GeoJSON on the main thread.
field_anchor = '    private int riverTileGeneration = 0;'
field_new = field_anchor + '\n    private int riverStatusGeneration = 0;\n    private final Runnable riverStatusKick = this::rebuildRiverStatusAsync;'
if 'riverStatusGeneration = 0' not in helper:
    if field_anchor not in helper:
        raise SystemExit('river status field anchor missing')
    helper = helper.replace(field_anchor, field_new, 1)

new_status = r'''    private void refreshRiverStatusSources() {
        if(!styleReady||style==null)return;
        main.removeCallbacks(riverStatusKick);
        main.postDelayed(riverStatusKick, 240L);
    }

    private void rebuildRiverStatusAsync() {
        if(!styleReady||style==null)return;
        final int generation=++riverStatusGeneration;
        final List<RiverWay> riverSnapshot=new ArrayList<>(rivers);
        final List<StationDot> stationSnapshot=new ArrayList<>();
        synchronized(stations){for(StationDot s:stations)if(s!=null&&s.fresh)stationSnapshot.add(s);}
        io.execute(() -> {
            final String[] geo=buildRiverStatusGeo(riverSnapshot,stationSnapshot);
            main.post(() -> {
                if(generation!=riverStatusGeneration||!styleReady||style==null)return;
                setGeo("fs-river-normal-status",geo[0]);
                setGeo("fs-river-alert-status",geo[1]);
                setGeo("fs-river-warning-status",geo[2]);
                setGeo("fs-river-danger-status",geo[3]);
            });
        });
    }

    private String[] buildRiverStatusGeo(List<RiverWay> riverSnapshot,List<StationDot> stationSnapshot) {
        try{
            JSONArray normal=new JSONArray(),alert=new JSONArray(),warning=new JSONArray(),danger=new JSONArray();
            for(RiverWay r:riverSnapshot){
                if(r==null||r.points.size()<2)continue;
                StationDot g=routeGaugeForSnapshot(r,stationSnapshot);
                if(g==null||!g.fresh)continue;
                String stage=normalizeStage(g.stage);
                JSONArray target;
                if("danger".equals(stage))target=danger;
                else if("warning".equals(stage))target=warning;
                else if("alert".equals(stage))target=alert;
                else if("normal".equals(stage))target=normal;
                else continue;
                JSONArray coords=new JSONArray();
                for(double[]p:r.points)coords.put(new JSONArray().put(p[0]).put(p[1]));
                JSONObject geom=new JSONObject().put("type","LineString").put("coordinates",coords);
                JSONObject props=new JSONObject().put("name",r.name).put("status",stage).put("gauge",g.name);
                target.put(new JSONObject().put("type","Feature").put("geometry",geom).put("properties",props));
            }
            return new String[]{featureCollection(normal),featureCollection(alert),featureCollection(warning),featureCollection(danger)};
        }catch(Exception e){String empty=emptyFeatureCollection();return new String[]{empty,empty,empty,empty};}
    }

    private static String featureCollection(JSONArray features) throws Exception {
        return new JSONObject().put("type","FeatureCollection").put("features",features).toString();
    }

    private StationDot routeGaugeForSnapshot(RiverWay r,List<StationDot> stationSnapshot){
        if(r==null||r.points.isEmpty())return null;
        double[] p=r.points.get(r.points.size()/2);
        String key=riverNameKey(r.name);
        if(key.length()<3)return null;
        StationDot best=null;double bestKm=Double.MAX_VALUE;
        for(StationDot s:stationSnapshot){
            String sk=riverNameKey(s.name);if(sk.length()<3)continue;
            boolean same=sk.equals(key)||sk.contains(key)||key.contains(sk);if(!same)continue;
            double d=km(p[1],p[0],s.lat,s.lon);if(d<bestKm&&d<=40.0){bestKm=d;best=s;}
        }
        return best;
    }

'''
helper = replace_between(
    helper,
    '    private void refreshRiverStatusSources() {',
    '    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {',
    new_status,
    'v0.8.10 synchronous status block')

# Keep flow visible but lightweight enough for mid/low-end Android phones.
helper = helper.replace('int n = Math.min(320, rivers.size());', 'int n = Math.min(120, rivers.size());', 1)
helper = helper.replace('main.postDelayed(this, 180L);', 'main.postDelayed(this, 280L);', 1)

map_path.write_text(helper,encoding='utf-8')

if "versionName '0.8.11'" not in gradle:
    gradle=gradle.replace('versionCode 30','versionCode 31',1)
    gradle=gradle.replace("versionName '0.8.10'","versionName '0.8.11'",1)
if 'versionCode 31' not in gradle or "versionName '0.8.11'" not in gradle:
    raise SystemExit('v0.8.11 version bump failed')
gradle_path.write_text(gradle,encoding='utf-8')

h=map_path.read_text(encoding='utf-8')
for marker in [
    'riverStatusKick = this::rebuildRiverStatusAsync',
    'main.postDelayed(riverStatusKick, 240L)',
    'io.execute(() ->',
    'buildRiverStatusGeo(riverSnapshot,stationSnapshot)',
    'for(StationDot s:stations)if(s!=null&&s.fresh)',
    'Math.min(120, rivers.size())',
    'main.postDelayed(this, 280L)',
    'fs-river-danger-status',
]:
    if marker not in h: raise SystemExit('v0.8.11 marker missing: '+marker)
if 'setGeo("fs-river-normal-status",riverStatusGeo("normal"))' in h:
    raise SystemExit('old synchronous status builder remained')
print('FloodSafe v0.8.11 map ANR fix + lightweight visible flow PASS')
