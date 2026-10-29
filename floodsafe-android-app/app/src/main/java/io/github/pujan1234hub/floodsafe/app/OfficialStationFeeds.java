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
    private static final long MAX_AGE_MS = 2L * 60L * 60L * 1000L;
    private OfficialStationFeeds() {}

    static JSONObject rivers() throws Exception {
        JSONObject src = get(ROOT + "floodsafe-station-details?kind=stations");
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
            boolean recent="observed".equals(s.optString("status"))&&when>0&&
                 now-when<=MAX_AGE_MS&&when-now<5L*60L*1000L;
            if(recent&&Double.isFinite(s.optDouble("level",Double.NaN))) {
                out.put("waterLevel",s.optDouble("level"));
                out.put("waterLevelOn",s.optString("observed"));
                // DHM/BIPAD status is based on current reading and validated thresholds.
                String official=s.optString("reportedStatus","").toUpperCase(java.util.Locale.ROOT);
                // Guard against misreading "BELOW WARNING LEVEL" as a warning.
                if(official.contains("BELOW")||official.contains("NORMAL")) out.put("_officialStatus","normal");
                else if(official.contains("DANGER"))out.put("_officialStatus","danger");
                else if(official.contains("WARNING"))out.put("_officialStatus","warning");
            }
            results.put(out);
        }
        JSONObject result=new JSONObject();
        result.put("results",results);
        result.put("source","FloodSafe BIPAD/DHM official monitoring");
        result.put("count",results.length());
        return result;
    }

    static JSONObject rainfall() throws Exception {
        JSONObject src = get(ROOT + "floodsafe-dhm-stations?kind=rain");
        JSONArray items=src.optJSONArray("items"),results=new JSONArray();
        if(!"live".equals(src.optString("status"))||items==null)
            throw new IllegalStateException("DHM rainfall temporarily unavailable");
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
            out.put("latitude",lat);out.put("longitude",lon);
            out.put("rainfall",rain);out.put("observedAt",s.optString("observedAt"));
            out.put("rainfallHours",s.optJSONObject("rainfallHours"));
            out.put("districtName",s.optString("district",""));
            results.put(out);
        }
        JSONObject result=new JSONObject();
        result.put("results",results);result.put("source","DHM official rainfall");
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
