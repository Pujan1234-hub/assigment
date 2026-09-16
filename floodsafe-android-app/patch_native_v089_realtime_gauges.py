from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path = src / 'NativeFullActivity.java'
map_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
activity = activity_path.read_text(encoding='utf-8')
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

# ---------------- Activity: official live feeds ----------------
activity = activity.replace(
    'private static final long RIVER_FRESH_MS=10L*60L*1000L;',
    'private static final long RIVER_FRESH_MS=10L*60L*1000L;\n    private static final long RAIN_FRESH_MS=30L*60L*1000L;',
    1)
activity = activity.replace(
    'private final List<RiverStation> stations=new ArrayList<>();',
    'private final List<RiverStation> stations=new ArrayList<>();\n    private final List<RainStation> rainStations=new ArrayList<>();',
    1)

poll_anchor = '    private boolean showAllStations=false;\n'
poll = '''    private boolean showAllStations=false;\n    private final Runnable livePoll=new Runnable(){@Override public void run(){if(isFinishing()||isDestroyed())return;refreshRivers();refreshRainStations();main.postDelayed(this,60_000L);}};\n'''
if 'private final Runnable livePoll=' not in activity:
    if poll_anchor not in activity: raise SystemExit('live poll anchor missing')
    activity = activity.replace(poll_anchor, poll, 1)

activity = activity.replace('        refreshAll();\n        requestLocation();', '        refreshAll();\n        main.postDelayed(livePoll,60_000L);\n        requestLocation();', 1)
activity = activity.replace(
    'private void refreshAll(){restoreLocation();refreshRivers();refreshHuman();refreshNews();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}',
    'private void refreshAll(){restoreLocation();refreshRivers();refreshRainStations();refreshHuman();refreshNews();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}',
    1)

new_refresh_rivers = r'''    private void refreshRivers(){
        feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));
        io.execute(()->{
            try{
                List<RiverStation> out=new ArrayList<>(); long now=System.currentTimeMillis();
                // Official BIPAD/DHM is primary. Supabase remains a resilient fallback only.
                try{
                    JSONObject official=getJson(BIPAD+"river/?limit=1000&_nativefull="+now);
                    JSONArray rr=rows(official);
                    for(int i=0;i<rr.length();i++){RiverStation s=parseStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
                }catch(Exception ignored){}
                if(out.isEmpty()){
                    JSONObject root=getJson(RIVER_ENDPOINT+"?_nativefull="+now); JSONArray rr=rows(root);
                    for(int i=0;i<rr.length();i++){RiverStation s=parseStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
                }
                out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
                synchronized(stations){stations.clear();stations.addAll(out);} runOnUiThread(this::refreshRiverUi);
            }catch(Exception e){runOnUiThread(()->feedFresh.setText(t("River data refresh हुन सकेन • stale लाई live भनिएको छैन","River refresh failed • stale data is not live")));}
        });
    }
'''
activity = replace_between(activity, '    private void refreshRivers(){', '    private RiverStation parseStation(', new_refresh_rivers, 'refreshRivers')

new_parse = r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null; JSONObject f=r.optJSONObject("fields");
        double[] c=officialCoord(r); double a=c[0],o=c[1]; if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=numDeep(r,f,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel","level"),
               warning=numDeep(r,f,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel","warning"),
               danger=numDeep(r,f,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel","danger");
        long at=parseTime(strDeep(r,f,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime","time"));
        boolean fresh=at>0&&now-at<=RIVER_FRESH_MS&&at-now<=5*60_000L;
        String raw=strDeep(r,f,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(fresh){
            if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("BELOW WARNING")){stage="normal";rank=3;}
        }
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");
        JSONObject station=r.optJSONObject("station"); if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName");
        if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district");
        return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank);
    }

    private void refreshRainStations(){
        io.execute(()->{
            try{
                long now=System.currentTimeMillis(); JSONArray rr=new JSONArray();
                try{rr=rows(getJson(BIPAD+"rain/?limit=1000&_nativefull="+now));}catch(Exception ignored){}
                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain-trimed/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}
                List<RainStation> out=new ArrayList<>();
                for(int i=0;i<rr.length();i++){RainStation s=parseRainStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
                synchronized(rainStations){rainStations.clear();rainStations.addAll(out);} runOnUiThread(this::refreshRainUi);
            }catch(Exception ignored){runOnUiThread(this::refreshRainUi);}
        });
    }

    private RainStation parseRainStation(JSONObject r,long now){
        if(r==null)return null; JSONObject f=r.optJSONObject("fields"); double[] c=officialCoord(r); double a=c[0],o=c[1];
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double mm=numDeep(r,f,"rainfall","rainFall","rain","rainfall24h","rainfall_24h","value","currentRainfall");
        long at=parseTime(strDeep(r,f,"measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","createdOn","updatedOn","time"));
        boolean fresh=at>0&&now-at<=RAIN_FRESH_MS&&at-now<=5*60_000L;
        String name=strDeep(r,f,"stationName","station_name","title","name","locationName","location_name");
        JSONObject station=r.optJSONObject("station"); if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName"); if(name.isEmpty())name="Official rain station";
        String raw=strDeep(r,f,"status","status_name").toUpperCase(Locale.ROOT), band="normal";
        if(fresh){if(raw.contains("ABOVE WARNING")||Double.isFinite(mm)&&mm>=140)band="danger";else if(Double.isFinite(mm)&&mm>=120)band="warning";else if(Double.isFinite(mm)&&mm>=80)band="alert";else band="normal";}else band="stale";
        String basin=strDeep(r,f,"basin","basin_name"); return new RainStation(name,basin,a,o,mm,at,fresh,band,raw);
    }

    private void refreshRainUi(){
        List<RainStation> copy; synchronized(rainStations){copy=new ArrayList<>(rainStations);} map.setRainStations(copy);
        int fresh=0;for(RainStation s:copy)if(s.fresh)fresh++;
        if(mapHint!=null)mapHint.setText(t("🌊 official नदी gauge • 🌧️ वर्षा स्टेशन "+fresh+" fresh / "+copy.size()+" total","🌊 official river gauges • 🌧️ rain stations "+fresh+" fresh / "+copy.size()+" total"));
    }

    private static double[] officialCoord(JSONObject r){
        JSONObject f=r.optJSONObject("fields"); JSONArray c=r.optJSONArray("_stationCoordinate"); if(c==null&&f!=null)c=f.optJSONArray("_stationCoordinate");
        if(c==null){JSONObject p=r.optJSONObject("point");if(p!=null)c=p.optJSONArray("coordinates");}
        if(c==null){JSONObject g=r.optJSONObject("geometry");if(g!=null)c=g.optJSONArray("coordinates");}
        if(c==null){JSONObject l=r.optJSONObject("location");if(l!=null)c=l.optJSONArray("coordinates");}
        if(c!=null&&c.length()>=2){double x=c.optDouble(0,Double.NaN),y=c.optDouble(1,Double.NaN);if(x>=79&&x<=90&&y>=25&&y<=32)return new double[]{y,x};if(y>=79&&y<=90&&x>=25&&x<=32)return new double[]{x,y};}
        double a=numDeep(r,f,"latitude","lat","stationLatitude","station_latitude"),o=numDeep(r,f,"longitude","lon","lng","long","stationLongitude","station_longitude"); return new double[]{a,o};
    }
    private static double numDeep(JSONObject r,JSONObject f,String...k){double n=num(r,k);if(Double.isFinite(n))return n;return f==null?Double.NaN:num(f,k);}
    private static String strDeep(JSONObject r,JSONObject f,String...k){String s=str(r,k);if(!s.isEmpty())return s;return f==null?"":str(f,k);}

'''
activity = replace_between(activity, '    private RiverStation parseStation(', '    private void refreshRiverUi(){', new_parse, 'parseStation/rain block')

activity = activity.replace(
    'map.setStations(copy,lat,lon);',
    'map.setStations(copy,lat,lon);List<RainStation> rainCopy;synchronized(rainStations){rainCopy=new ArrayList<>(rainStations);}map.setRainStations(rainCopy);',
    1)
activity = activity.replace(
    'mapTitle.setText(t("🇳🇵 BIPAD नदी प्रत्यक्ष नक्सा","🇳🇵 BIPAD live river map"));mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, चेतावनी र official time हेर्नुहोस्।","Tap a river station for level, warning and official time."));mapHint.setText(t("🇳🇵 official नदी स्टेशन र नदी geometry","🇳🇵 official stations and river geometry"));',
    'mapTitle.setText(t("🇳🇵 BIPAD/DHM नदी + वर्षा प्रत्यक्ष नक्सा","🇳🇵 BIPAD/DHM live river + rain map"));mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, वर्षा, चेतावनी र official time हेर्नुहोस्।","Tap rivers/stations for water level, rainfall, warning and official time."));mapHint.setText(t("🌊 official नदी gauge • 🌧️ official वर्षा station","🌊 official river gauges • 🌧️ official rain stations"));',
    1)

class_anchor = '    private static final class RiverStation{final String name,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;}}\n'
rain_class = class_anchor + '    private static final class RainStation{final String name,basin,band,rawStatus;final double lat,lon,rainfall;final long at;final boolean fresh;RainStation(String n,String b,double a,double o,double mm,long tm,boolean f,String bd,String rs){name=n;basin=b;lat=a;lon=o;rainfall=mm;at=tm;fresh=f;band=bd;rawStatus=rs;}}\n'
if 'private static final class RainStation' not in activity:
    if class_anchor not in activity: raise SystemExit('RainStation class anchor missing')
    activity = activity.replace(class_anchor, rain_class, 1)

# ---------------- Native map: rain stations + direct river gauge truth ----------------
helper = helper.replace(
    'private final List<StationDot> stations = new ArrayList<>();',
    'private final List<StationDot> stations = new ArrayList<>();\n    private final List<RainDot> rainStations = new ArrayList<>();',
    1)

setter_anchor = '    void zoomBy(float factor) {'
setter = r'''    void setRainStations(List<?> source) {
        List<RainDot> next = new ArrayList<>();
        if (source != null) for (Object o : source) { RainDot r = readRain(o); if (r != null) next.add(r); }
        synchronized (rainStations) { rainStations.clear(); rainStations.addAll(next); }
        refreshRainSources();
    }

'''
if 'void setRainStations(List<?> source)' not in helper:
    if setter_anchor not in helper: raise SystemExit('map rain setter anchor missing')
    helper = helper.replace(setter_anchor, setter + setter_anchor, 1)

layer_anchor = '            ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5",'
rain_layers = '''            ensurePointSource("fs-rain-stale", "fs-rain-stale-layer", "#8e99a5", 2.5f, 0.42f);\n            ensurePointSource("fs-rain-normal", "fs-rain-normal-layer", "#26a7ff", 3.2f, 0.92f);\n            ensurePointSource("fs-rain-alert", "fs-rain-alert-layer", "#ffd23f", 4.0f, 1.0f);\n            ensurePointSource("fs-rain-warning", "fs-rain-warning-layer", "#ff8a1f", 4.8f, 1.0f);\n            ensurePointSource("fs-rain-danger", "fs-rain-danger-layer", "#f22f4b", 5.5f, 1.0f);\n'''
if 'fs-rain-normal-layer' not in helper:
    if layer_anchor not in helper: raise SystemExit('rain layer anchor missing')
    helper = helper.replace(layer_anchor, rain_layers + layer_anchor, 1)

helper = helper.replace('            refreshStationSources();\n            refreshUserSource();', '            refreshStationSources();\n            refreshRainSources();\n            refreshUserSource();', 1)

rain_refresh_anchor = '    private void refreshUserSource() {'
rain_refresh = r'''    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        List<RainDot> snapshot; synchronized (rainStations) { snapshot = new ArrayList<>(rainStations); }
        setGeo("fs-rain-stale", rainGeo(snapshot, "stale"));
        setGeo("fs-rain-normal", rainGeo(snapshot, "normal"));
        setGeo("fs-rain-alert", rainGeo(snapshot, "alert"));
        setGeo("fs-rain-warning", rainGeo(snapshot, "warning"));
        setGeo("fs-rain-danger", rainGeo(snapshot, "danger"));
    }

'''
if 'private void refreshRainSources()' not in helper:
    if rain_refresh_anchor not in helper: raise SystemExit('rain refresh anchor missing')
    helper = helper.replace(rain_refresh_anchor, rain_refresh + rain_refresh_anchor, 1)

new_click = r'''    private boolean onMapClick(LatLng p) {
        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        RainDot nearestRain = nearestRain(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        double stationThreshold = Math.max(0.6, 28.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        double rd=nearestRain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearestRain.lat,nearestRain.lon);
        if (nearestRain != null && rd <= stationThreshold && rd < sd) { showRain(nearestRain); return true; }
        if (nearest != null && sd <= stationThreshold) { if (stationTapListener != null) stationTapListener.onStationTap(nearest.original); return true; }
        if (nearestRain != null && rd <= stationThreshold) { showRain(nearestRain); return true; }
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.35, 18.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) { showRiver(rw, p.getLatitude(), p.getLongitude()); return true; }
        return false;
    }

'''
helper = replace_between(helper, '    private boolean onMapClick(LatLng p) {', '    private StationDot nearestStation(', new_click, 'map click')

nearest_rain_anchor = '    private RiverWay nearestRiver('
nearest_rain = r'''    private RainDot nearestRain(double la,double lo){RainDot best=null;double d=Double.MAX_VALUE;synchronized(rainStations){for(RainDot r:rainStations){double x=km(la,lo,r.lat,r.lon);if(x<d){d=x;best=r;}}}return best;}

'''
if 'private RainDot nearestRain(' not in helper:
    if nearest_rain_anchor not in helper: raise SystemExit('nearest rain anchor missing')
    helper = helper.replace(nearest_rain_anchor, nearest_rain + nearest_rain_anchor, 1)

new_show = r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot direct = directGaugeFor(r, la, lo);
        StationDot near = nearestStation(la, lo);
        StringBuilder msg = new StringBuilder();
        if (direct != null) {
            double d=km(la,lo,direct.lat,direct.lon);
            msg.append("प्रत्यक्ष official gauge: ").append(direct.name).append(String.format(Locale.US," • %.1f km",d));
            if(Double.isFinite(direct.level))msg.append(String.format(Locale.US,"\nपानीको सतह: %.2f m",direct.level));
            if(Double.isFinite(direct.warning))msg.append(String.format(Locale.US,"\nWarning सीमा: %.2f m",direct.warning));
            if(Double.isFinite(direct.danger))msg.append(String.format(Locale.US,"\nDanger सीमा: %.2f m",direct.danger));
            msg.append("\nStatus: ").append(direct.fresh?direct.stage.toUpperCase(Locale.ROOT):"STALE / UNKNOWN");
            msg.append("\nOfficial time: ").append(formatOfficialTime(direct.at));
        } else {
            msg.append("यो नदी/खोलामा direct official realtime gauge भेटिएन।");
            if(near!=null){double d=km(la,lo,near.lat,near.lon);msg.append("\n\nनजिकको gauge reference मात्र: ").append(near.name).append(String.format(Locale.US," • %.1f km",d));if(Double.isFinite(near.level))msg.append(String.format(Locale.US,"\nपानीको सतह: %.2f m",near.level));msg.append("\nStatus: ").append(near.fresh?near.stage.toUpperCase(Locale.ROOT):"STALE / UNKNOWN").append("\nOfficial time: ").append(formatOfficialTime(near.at));}
        }
        msg.append("\n\nRiver geometry: OpenStreetMap / FloodSafe bundled network");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ", null).show();
    }

    private StationDot directGaugeFor(RiverWay r,double la,double lo){
        String key=riverNameKey(r==null?"":r.name);if(key.length()<3)return null;StationDot best=null;double d=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){String sk=riverNameKey(s.name);if(sk.length()<3)continue;boolean same=sk.equals(key)||sk.contains(key)||key.contains(sk);if(!same)continue;double x=km(la,lo,s.lat,s.lon);if(x<d&&x<=40.0){d=x;best=s;}}}return best;
    }
    private static String riverNameKey(String s){if(s==null)return"";String x=s.toLowerCase(Locale.ROOT).replaceAll("\\bat\\b.*$","").replaceAll("\\b(river|khola|nadi|stream|station|gauge|hs|highway)\\b"," ").replaceAll("[^a-z0-9]"," ").replaceAll("\\s+"," ").trim();return x.replace(" ","");}
    private static String formatOfficialTime(long at){if(at<=0)return"उपलब्ध छैन";try{java.text.SimpleDateFormat f=new java.text.SimpleDateFormat("dd MMM yyyy HH:mm:ss",Locale.US);f.setTimeZone(java.util.TimeZone.getTimeZone("Asia/Kathmandu"));return f.format(new java.util.Date(at))+" NPT";}catch(Exception e){return String.valueOf(at);}}
    private void showRain(RainDot r){StringBuilder m=new StringBuilder();m.append("Official rain station");if(Double.isFinite(r.rainfall))m.append(String.format(Locale.US,"\nवर्षा: %.1f mm",r.rainfall));m.append("\nStatus: ").append(r.fresh?r.band.toUpperCase(Locale.ROOT):"STALE / UNKNOWN");m.append("\nOfficial time: ").append(formatOfficialTime(r.at));if(r.rawStatus!=null&&!r.rawStatus.isEmpty())m.append("\nBIPAD: ").append(r.rawStatus);new AlertDialog.Builder(getContext()).setTitle("🌧️ "+r.name).setMessage(m.toString()).setPositiveButton("ठीक छ",null).show();}

'''
helper = replace_between(helper, '    private void showRiver(RiverWay r, double la, double lo) {', '    private void startParticles() {', new_show, 'showRiver')

helper = helper.replace(
    's.level = getDouble(c, o, "level");\n            return s;',
    's.level = getDouble(c, o, "level");\n            s.warning = getDouble(c,o,"warning"); s.danger=getDouble(c,o,"danger"); s.at=getLong(c,o,"at",-1L);\n            return s;',
    1)

read_rain_anchor = '    private static double getDouble(Class<?> c, Object o, String name) throws Exception {'
read_rain = r'''    private RainDot readRain(Object o){if(o==null)return null;try{Class<?> c=o.getClass();RainDot r=new RainDot();r.lat=getDouble(c,o,"lat");r.lon=getDouble(c,o,"lon");if(!Double.isFinite(r.lat)||!Double.isFinite(r.lon))return null;r.name=getString(c,o,"name","Official rain station");r.band=getString(c,o,"band","stale");r.rawStatus=getString(c,o,"rawStatus","");r.fresh=getBoolean(c,o,"fresh",false);r.rainfall=getDouble(c,o,"rainfall");r.at=getLong(c,o,"at",-1L);return r;}catch(Exception e){return null;}}
    private static long getLong(Class<?> c,Object o,String name,long fallback){try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.getLong(o);}catch(Exception e){return fallback;}}

'''
if 'private RainDot readRain(' not in helper:
    if read_rain_anchor not in helper: raise SystemExit('read rain anchor missing')
    helper = helper.replace(read_rain_anchor, read_rain + read_rain_anchor, 1)

rain_geo_anchor = '    private static JSONObject pointFeature(double lo, double la, String name) throws Exception {'
rain_geo = r'''    private static String rainGeo(List<RainDot> list,String group){try{JSONArray f=new JSONArray();for(RainDot r:list){String g=r.fresh?normalizeStage(r.band):"stale";if(!group.equals(g))continue;f.put(pointFeature(r.lon,r.lat,r.name));}return new JSONObject().put("type","FeatureCollection").put("features",f).toString();}catch(Exception e){return emptyFeatureCollection();}}

'''
if 'private static String rainGeo(' not in helper:
    if rain_geo_anchor not in helper: raise SystemExit('rain geo anchor missing')
    helper = helper.replace(rain_geo_anchor, rain_geo + rain_geo_anchor, 1)

helper = helper.replace(
    'Object original; String name, stage; double lat, lon, level; boolean fresh;',
    'Object original; String name, stage; double lat, lon, level, warning, danger; long at; boolean fresh;',
    1)
helper = helper.replace(
    '    private static final class RiverWay {\n        String name, type; final List<double[]> points = new ArrayList<>();\n    }',
    '    private static final class RainDot { String name,band,rawStatus; double lat,lon,rainfall; long at; boolean fresh; }\n    private static final class RiverWay {\n        String name, type; final List<double[]> points = new ArrayList<>();\n    }',
    1)

activity_path.write_text(activity, encoding='utf-8')
map_path.write_text(helper, encoding='utf-8')

# Version bump.
if "versionName '0.8.9'" not in gradle:
    gradle = gradle.replace('versionCode 28', 'versionCode 29', 1)
    gradle = gradle.replace("versionName '0.8.8'", "versionName '0.8.9'", 1)
if 'versionCode 29' not in gradle or "versionName '0.8.9'" not in gradle: raise SystemExit('v0.8.9 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

# Hard gates: official feed, rain layer, truthful direct-gauge wording, safety untouched.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for marker in ['BIPAD+"river/?limit=1000', 'BIPAD+"rain/?limit=1000', 'RAIN_FRESH_MS=30L*60L*1000L', 'main.postDelayed(livePoll,60_000L)', 'map.setRainStations', 'private static final class RainStation']:
    if marker not in a: raise SystemExit('v0.8.9 activity marker missing: '+marker)
for marker in ['fs-rain-normal-layer','void setRainStations(List<?> source)','directGaugeFor','direct official realtime gauge','formatOfficialTime','private static final class RainDot']:
    if marker not in h: raise SystemExit('v0.8.9 map marker missing: '+marker)
print('FloodSafe v0.8.9 official river + rain realtime native map PASS')
