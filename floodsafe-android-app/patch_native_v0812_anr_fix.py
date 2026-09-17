from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path=src/'FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'
helper=map_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

# v0.8.12 ANR fix:
# v0.8.10 built four river-status GeoJSON layers synchronously on the Android UI
# thread. Each layer walked every visible river and, for every river, scanned up to
# 1000 official stations. With a stale 1000-row BIPAD payload this could do millions
# of name/distance checks on the main thread every refresh and Android reported
# "FloodSafe Nepal isn't responding". Keep exactly the same status semantics, but
# build the overlays on the existing background executor and publish only the final
# GeoJSON strings back to MapLibre on the main thread.
old = r'''    private void refreshRiverStatusSources() {
        if(!styleReady||style==null)return;
        setGeo("fs-river-normal-status",riverStatusGeo("normal"));
        setGeo("fs-river-alert-status",riverStatusGeo("alert"));
        setGeo("fs-river-warning-status",riverStatusGeo("warning"));
        setGeo("fs-river-danger-status",riverStatusGeo("danger"));
    }
'''
new = r'''    private int riverStatusGeneration = 0;

    private void refreshRiverStatusSources() {
        if(!styleReady||style==null)return;
        final int generation=++riverStatusGeneration;
        final List<RiverWay> riverSnapshot=new ArrayList<>(rivers);
        final List<StationDot> freshStations=new ArrayList<>();
        synchronized(stations){for(StationDot s:stations)if(s!=null&&s.fresh)freshStations.add(s);}

        // Most BIPAD rows can legitimately be stale. In that common case there is
        // nothing to colour and, critically, no O(rivers x 1000) work is required.
        if(freshStations.isEmpty()){
            String empty=emptyFeatureCollection();
            setGeo("fs-river-normal-status",empty);
            setGeo("fs-river-alert-status",empty);
            setGeo("fs-river-warning-status",empty);
            setGeo("fs-river-danger-status",empty);
            return;
        }

        try{
            io.execute(()->{
                // If another station/tile refresh superseded this job while it was
                // queued, abandon it before doing any matching work.
                if(generation!=riverStatusGeneration)return;
                try{
                    JSONArray normal=new JSONArray(),alert=new JSONArray(),warning=new JSONArray(),danger=new JSONArray();
                    for(RiverWay r:riverSnapshot){
                        if(generation!=riverStatusGeneration)return;
                        if(r==null||r.points.size()<2)continue;
                        StationDot g=routeGaugeForSnapshot(r,freshStations);
                        if(g==null)continue;
                        String stage=normalizeStage(g.stage);
                        JSONArray coords=new JSONArray();for(double[]p:r.points)coords.put(new JSONArray().put(p[0]).put(p[1]));
                        JSONObject geom=new JSONObject().put("type","LineString").put("coordinates",coords);
                        JSONObject props=new JSONObject().put("name",r.name).put("status",stage).put("gauge",g.name);
                        JSONObject feature=new JSONObject().put("type","Feature").put("geometry",geom).put("properties",props);
                        if("danger".equals(stage))danger.put(feature);
                        else if("warning".equals(stage))warning.put(feature);
                        else if("alert".equals(stage))alert.put(feature);
                        else if("normal".equals(stage))normal.put(feature);
                    }
                    final String n=new JSONObject().put("type","FeatureCollection").put("features",normal).toString();
                    final String a=new JSONObject().put("type","FeatureCollection").put("features",alert).toString();
                    final String w=new JSONObject().put("type","FeatureCollection").put("features",warning).toString();
                    final String d=new JSONObject().put("type","FeatureCollection").put("features",danger).toString();
                    main.post(()->{
                        if(generation!=riverStatusGeneration||!styleReady||style==null)return;
                        setGeo("fs-river-normal-status",n);
                        setGeo("fs-river-alert-status",a);
                        setGeo("fs-river-warning-status",w);
                        setGeo("fs-river-danger-status",d);
                    });
                }catch(Exception ignored){}
            });
        }catch(java.util.concurrent.RejectedExecutionException ignored){}
    }

    private StationDot routeGaugeForSnapshot(RiverWay r,List<StationDot> freshStations){
        if(r==null||r.points.isEmpty()||freshStations==null||freshStations.isEmpty())return null;
        String key=riverNameKey(r.name);if(key.length()<3)return null;
        double[]p=r.points.get(r.points.size()/2);StationDot best=null;double d=Double.MAX_VALUE;
        for(StationDot s:freshStations){
            if(s==null)continue;
            String sk=riverNameKey(s.name);if(sk.length()<3)continue;
            boolean same=sk.equals(key)||sk.contains(key)||key.contains(sk);if(!same)continue;
            double x=km(p[1],p[0],s.lat,s.lon);if(x<d&&x<=40.0){d=x;best=s;}
        }
        return best;
    }
'''
if old not in helper:
    if 'private int riverStatusGeneration = 0;' not in helper:
        raise SystemExit('v0.8.12 refreshRiverStatusSources anchor missing')
else:
    helper=helper.replace(old,new,1)

# Direct river taps should never spend time normalising hundreds of stale station
# names. Stale stations are still shown as grey station dots/list rows, but only a
# fresh reading may be used as a direct realtime river status match.
old_direct='synchronized(stations){for(StationDot s:stations){String sk=riverNameKey(s.name);if(sk.length()<3)continue;boolean same=sk.equals(key)||sk.contains(key)||key.contains(sk);if(!same)continue;double x=km(la,lo,s.lat,s.lon);if(x<d&&x<=40.0){d=x;best=s;}}}return best;'
new_direct='synchronized(stations){for(StationDot s:stations){if(s==null||!s.fresh)continue;String sk=riverNameKey(s.name);if(sk.length()<3)continue;boolean same=sk.equals(key)||sk.contains(key)||key.contains(sk);if(!same)continue;double x=km(la,lo,s.lat,s.lon);if(x<d&&x<=40.0){d=x;best=s;}}}return best;'
if old_direct in helper:
    helper=helper.replace(old_direct,new_direct,1)
elif 'if(s==null||!s.fresh)continue;String sk=riverNameKey(s.name)' not in helper:
    raise SystemExit('v0.8.12 directGaugeFor anchor missing')

map_path.write_text(helper,encoding='utf-8')

if "versionName '0.8.12'" not in gradle:
    gradle=gradle.replace('versionCode 31','versionCode 32',1)
    gradle=gradle.replace("versionName '0.8.11'","versionName '0.8.12'",1)
if 'versionCode 32' not in gradle or "versionName '0.8.12'" not in gradle:
    raise SystemExit('v0.8.12 version bump failed')
gradle_path.write_text(gradle,encoding='utf-8')

h=map_path.read_text(encoding='utf-8')
for marker in ['riverStatusGeneration','routeGaugeForSnapshot','freshStations.isEmpty()','RejectedExecutionException','if(s==null||!s.fresh)continue']:
    if marker not in h: raise SystemExit('v0.8.12 ANR marker missing: '+marker)
print('FloodSafe v0.8.12 native ANR fix PASS: river status matching moved off UI thread')
