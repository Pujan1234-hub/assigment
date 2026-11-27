package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Shared, strict mapping for next native release.
 * FloodSafe's web and native clients read the SAME BIPAD -> DHM source-selection API.
 * A position without a verified observation is NEVER converted to a current level.
 * No modelled flow is converted into measured water level or official warning.
 */
final class OfficialStationFeeds {
    private static final String ROOT = "https://pjbuilts.com/api/";
    private static final long MAX_AGE_MS = 30L * 60L * 1000L; // Preview source freshness.
    private static final long RIVER_DISPLAY_MAX_AGE_MS = 30L * 60L * 1000L; // Display only, emergency alerts still require <=10 min.
    private OfficialStationFeeds() {}

    static JSONObject rivers() throws Exception {
        JSONObject src = get(ROOT + "floodsafe-live-preview?kind=stations");
        if (!"catalog_available".equals(src.optString("status"))) {
            throw new IllegalStateException("Official river observations unavailable");
        }
        JSONArray stations = src.optJSONArray("stations"), results = new JSONArray();
        if (stations == null) throw new IllegalStateException("No river catalogue");
        final long now = System.currentTimeMillis();
        for (int i=0;i<stations.length();i++) {
            JSONObject s = stations.optJSONObject(i);
            if (s == null) continue;
            double lat=s.optDouble("lat",Double.NaN),lon=s.optDouble("lon",Double.NaN);
            if (!nepal(lat,lon)) continue;
            JSONObject out = new JSONObject();
            out.put("stationSeriesId", s.optString("id",""));
            out.put("stationName", s.optString("name","River station"));
            out.put("districtName", s.optString("district",""));
            out.put("latitude",lat);out.put("longitude",lon);
            putFinite(out,"warningLevel",s,"warning");
            putFinite(out,"dangerLevel",s,"danger");
            long when=timestamp(s.optString("observed",""));
            // Preserve only an explicitly verified, timestamped original gauge
            // observation for the stale-detail box. Never classify it as live.
            double verifiedLevel=s.optDouble("level",Double.NaN);
            boolean hasLastVerified="observed".equals(s.optString("status"))&&when>0&&
                 when-now<=5L*60L*1000L&&Double.isFinite(verifiedLevel);
            if(hasLastVerified){
                out.put("lastVerifiedWaterLevel",verifiedLevel);
                out.put("lastVerifiedWaterLevelOn",s.optString("observed"));
            }
            boolean recent=hasLastVerified&&now-when<=RIVER_DISPLAY_MAX_AGE_MS;
            if(recent&&Double.isFinite(s.optDouble("level",Double.NaN))) {
                out.put("waterLevel",s.optDouble("level"));
                out.put("waterLevelOn",s.optString("observed"));
                // DHM/BIPAD status is based on current reading and validated thresholds.
                String official=s.optString("reportedStatus","").toUpperCase(java.util.Locale.ROOT);
                // Guard against misreading "BELOW WARNING LEVEL" as a warning.
                if(official.contains("BELOW WARNING")||official.contains("NORMAL")) out.put("_officialStatus","normal");
                else if(official.contains("DANGER")&&!official.contains("BELOW"))out.put("_officialStatus","danger");
                else if(official.contains("WARNING")&&!official.contains("BELOW"))out.put("_officialStatus","warning");
                else if(official.contains("WATCH")||official.contains("ALERT")||official.contains("YELLOW"))out.put("_officialStatus","alert");
            }
            results.put(out);
        }
        JSONObject result=new JSONObject();
        result.put("results",results);
        String srcType=src.optString("activeObservationSource","none");
        if(!"dhm".equals(srcType)&&!"bipad".equals(srcType))srcType="none";
        result.put("activeObservationSource",srcType);
        result.put("source",src.optString("source","Official river observations"));
        result.put("dhmStatus",src.optString("dhmStatus","unknown"));
        result.put("bipadFallbackStatus",src.optString("bipadFallbackStatus","unknown"));
        result.put("count",results.length());
        result.put("watchCount",src.optInt("watchCount",-1));
        return result;
    }

    /**
     * Keep official station LOCATIONS visible when the online station-detail service
     * is unavailable. Offline catalogue entries NEVER contain live levels or alerts.
     * Normal live observations still come exclusively from rivers() above.
     */
    static JSONObject rivers(android.content.Context context) throws Exception {
        try {
            JSONObject online = rivers();
            JSONArray items = online.optJSONArray("results");
            if (items != null && items.length() > 0) return online;
        } catch (Exception ignored) {
            // A failed online request must not make the entire station map disappear.
        }
        return packagedRiverCatalogue(context);
    }

    private static JSONObject packagedRiverCatalogue(android.content.Context context) throws Exception {
        byte[] buffer = new byte[8192];
        java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
        try (java.io.InputStream stream = context.getAssets().open("data/floodsafe-core.json")) {
            int count;
            while ((count = stream.read(buffer)) != -1) bytes.write(buffer, 0, count);
        }
        JSONObject snapshot = new JSONObject(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
        JSONArray catalog = snapshot.optJSONArray("river_stations");
        if (catalog == null || catalog.length() == 0) catalog = snapshot.optJSONArray("rivers");
        if (catalog == null) throw new IllegalStateException("Bundled river catalogue missing");
        JSONArray results = new JSONArray();
        java.util.HashSet<String> unique = new java.util.HashSet<>();
        for (int i=0; i<catalog.length(); i++) {
            JSONObject raw = catalog.optJSONObject(i);
            if (raw == null) continue;
            JSONObject fields = raw.optJSONObject("fields");
            JSONObject station = raw.optJSONObject("station");
            double latitude = firstNumber(raw,"latitude","lat","stationLatitude","station_latitude");
            double longitude = firstNumber(raw,"longitude","lon","lng","stationLongitude","station_longitude");
            if (fields != null) {
                if (!Double.isFinite(latitude))
                    latitude = firstNumber(fields,"latitude","lat","stationLatitude","station_latitude");
                if (!Double.isFinite(longitude))
                    longitude = firstNumber(fields,"longitude","lon","lng","stationLongitude","station_longitude");
            }
            if (station != null) {
                if (!Double.isFinite(latitude))
                    latitude = firstNumber(station,"latitude","lat","stationLatitude","station_latitude");
                if (!Double.isFinite(longitude))
                    longitude = firstNumber(station,"longitude","lon","lng","stationLongitude","station_longitude");
            }
            if (!nepal(latitude,longitude)) {
                for (String locationKey : new String[]{"point","location","geometry","centroid"}) {
                    JSONObject obj = raw.optJSONObject(locationKey);
                    if (obj == null && fields != null) obj = fields.optJSONObject(locationKey);
                    JSONArray coordinate = obj == null ? null : obj.optJSONArray("coordinates");
                    if (coordinate == null || coordinate.length() < 2) continue;
                    double a = coordinate.optDouble(0,Double.NaN);
                    double b = coordinate.optDouble(1,Double.NaN);
                    if (nepal(b,a)) {latitude=b; longitude=a; break;}
                    if (nepal(a,b)) {latitude=a; longitude=b; break;}
                }
            }
            if (!nepal(latitude,longitude)) {
                JSONArray coordinate = raw.optJSONArray("_stationCoordinate");
                if (coordinate != null && coordinate.length() >= 2) {
                    double a=coordinate.optDouble(0,Double.NaN), b=coordinate.optDouble(1,Double.NaN);
                    if (nepal(b,a)) {latitude=b;longitude=a;}
                    else if(nepal(a,b)) {latitude=a;longitude=b;}
                }
            }
            if (!nepal(latitude,longitude)) continue;
            String name = firstText(raw,"stationName","station_name","river_name","riverName","title","name");
            if (name.isEmpty() && fields!=null)
                name=firstText(fields,"stationName","station_name","river_name","riverName","title","name");
            if (name.isEmpty() && station!=null)
                name=firstText(station,"stationName","station_name","river_name","riverName","title","name");
            if (name.isEmpty()) continue;
            String id=firstText(raw,"stationSeriesId","station_series_id","stationId","station_id","id");
            if (id.isEmpty() && fields!=null)
                id=firstText(fields,"stationSeriesId","station_series_id","stationId","station_id","id");
            String key=id.isEmpty()?name+"|"+latitude+"|"+longitude:id;
            if (!unique.add(key)) continue;
            JSONObject item = new JSONObject();
            item.put("stationName",name);
            item.put("stationSeriesId",id);
            item.put("latitude",latitude);
            item.put("longitude",longitude);
            String district=firstText(raw,"districtName","district_name","district");
            if (district.isEmpty() && fields!=null)
                district=firstText(fields,"districtName","district_name","district");
            item.put("districtName",district);
            // Intentionally omit waterLevel, observation time, and risk status.
            // The caller must render these catalogue-only markers as grey/unknown.
            results.put(item);
        }
        if (results.length()==0)
            throw new IllegalStateException("No usable coordinates in bundled station catalogue");
        JSONObject response=new JSONObject();
        response.put("results",results);
        response.put("count",results.length());
        response.put("activeObservationSource","none");
        response.put("source","Bundled BIPAD station catalogue; not live");
        response.put("catalogueOnly",true);
        return response;
    }

    private static String firstText(JSONObject o,String... keys) {
        if (o==null) return "";
        for(String key:keys) {
            String value=o.optString(key,"").trim();
            if (!value.isEmpty() && !"null".equalsIgnoreCase(value)) return value;
        }
        return "";
    }

    private static double firstNumber(JSONObject o,String... keys) {
        if (o==null) return Double.NaN;
        for(String key:keys) {
            double value=o.optDouble(key,Double.NaN);
            if (Double.isFinite(value)) return value;
        }
        return Double.NaN;
    }

    static JSONObject rainfall() throws Exception {
        JSONObject src = get(ROOT + "floodsafe-live-preview?kind=rain");
        JSONArray items=src.optJSONArray("items"),results=new JSONArray();
        if(!"live".equals(src.optString("status"))||items==null)
            throw new IllegalStateException("Official rainfall temporarily unavailable");
        long now=System.currentTimeMillis();
        for(int i=0;i<items.length();i++){
            JSONObject s=items.optJSONObject(i);if(s==null)continue;
            double lat=s.optDouble("lat",Double.NaN),lon=s.optDouble("lon",Double.NaN);
            double rain=s.optDouble("value",Double.NaN);
            long observed=timestamp(s.optString("observedAt",""));
            if(!nepal(lat,lon)||!Double.isFinite(rain)||rain<0||observed<=0||
                now-observed>MAX_AGE_MS||observed-now>5L*60L*1000L)continue;
            JSONObject out=new JSONObject();
            out.put("stationName",s.optString("name","Rainfall station"));
            out.put("source",s.optString("source",src.optString("source","Official rainfall")));
            out.put("latitude",lat);out.put("longitude",lon);
            out.put("rainfall",rain);out.put("observedAt",s.optString("observedAt"));
            out.put("rainfallHours",s.optJSONObject("rainfallHours"));
            out.put("districtName",s.optString("district",""));
            results.put(out);
        }
        JSONObject result=new JSONObject();
        result.put("results",results);result.put("source",src.optString("source","Official rainfall"));result.put("activeObservationSource",src.optString("activeObservationSource","none"));result.put("watchCount",src.optInt("watchCount",-1));
        return result;
    }

    private static void putFinite(JSONObject dest,String target,JSONObject src,String source)throws Exception{
        double n=src.optDouble(source,Double.NaN);
        if(Double.isFinite(n)&&n>0)dest.put(target,n);
    }
    private static long timestamp(String t){
        if(t==null||t.isEmpty())return 0;
        try{return java.time.Instant.parse(t).toEpochMilli();}catch(Exception ignored){return 0;}
    }
    private static boolean nepal(double lat,double lon){
        return Double.isFinite(lat)&&Double.isFinite(lon)&&lat>=26.1&&lat<=30.8&&lon>=79.8&&lon<=88.5;
    }
    private static JSONObject get(String url)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();
        c.setConnectTimeout(10000);c.setReadTimeout(19000);c.setUseCaches(false);
        c.setRequestProperty("Accept","application/json");
        try {
            if(c.getResponseCode()!=200)throw new IllegalStateException("Monitoring source unavailable");
            try(BufferedReader reader=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){
                StringBuilder body=new StringBuilder();
                String line;while((line=reader.readLine())!=null){
                    body.append(line);
                    if(body.length()>4000000)throw new IllegalStateException("Response too large");
                }
                return new JSONObject(body.toString());
            }
        } finally {c.disconnect();}
    }
}
