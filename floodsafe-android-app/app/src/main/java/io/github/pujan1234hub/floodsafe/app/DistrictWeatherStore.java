package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Live Open-Meteo model estimates for representative points in Nepal's 77 districts. No gauge assertions. */
final class DistrictWeatherStore {
 static final String PREFS="floodsafe-district-model";
 static final long CACHE_MS=20L*60*1000;
 private DistrictWeatherStore(){}
 static JSONArray districts(Context ctx)throws Exception{
  try(InputStream in=ctx.getAssets().open("district-weather-points.json")){
   ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] x=new byte[8192];int n;
   while((n=in.read(x))!=-1)b.write(x,0,n);
   return new JSONObject(b.toString("UTF-8")).getJSONArray("districts");
  }
 }
 static JSONArray fetch(Context ctx)throws Exception {
  SharedPreferences p=ctx.getSharedPreferences(PREFS,Context.MODE_PRIVATE);
  long now=System.currentTimeMillis();
  if(now-p.getLong("when",0)<CACHE_MS){
   try{return new JSONArray(p.getString("data","[]"));}catch(Exception ignored){}
  }
  JSONArray districts=districts(ctx),output=new JSONArray();
  for(int start=0;start<districts.length();start+=15){
   int stop=Math.min(start+15,districts.length());StringBuilder la=new StringBuilder(),lo=new StringBuilder();
   for(int i=start;i<stop;i++){
    JSONObject d=districts.getJSONObject(i);
    if(i>start){la.append(',');lo.append(',');}
    la.append(String.format(Locale.US,"%.4f",d.getDouble("lat")));
    lo.append(String.format(Locale.US,"%.4f",d.getDouble("lon")));
   }
   String url="https://api.open-meteo.com/v1/forecast?latitude="+la+"&longitude="+lo+"&current=weather_code,cloud_cover,precipitation,temperature_2m&timezone=Asia%2FKathmandu&forecast_days=1";
   HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();c.setConnectTimeout(11000);c.setReadTimeout(16000);
   try{
    if(c.getResponseCode()!=200)throw new IllegalStateException("Weather HTTP "+c.getResponseCode());
    ByteArrayOutputStream buf=new ByteArrayOutputStream();
    try(InputStream in=c.getInputStream()){byte[] q=new byte[8192];int n;while((n=in.read(q))!=-1){buf.write(q,0,n);if(buf.size()>1800000)throw new IllegalStateException("Weather response too large");}}
    Object parsed=new org.json.JSONTokener(buf.toString("UTF-8")).nextValue();
    JSONArray batch=parsed instanceof JSONArray?(JSONArray)parsed:new JSONArray().put(parsed);
    if(batch.length()!=stop-start)throw new IllegalStateException("District response incomplete");
    for(int k=0;k<batch.length();k++){
     JSONObject local=districts.getJSONObject(start+k),weather=batch.optJSONObject(k);
     if(weather==null||weather.optJSONObject("current")==null)continue;
     JSONObject cur=weather.getJSONObject("current");
     JSONObject v=new JSONObject(local.toString());
     v.put("code",cur.optInt("weather_code",-1));
     v.put("cloud",cur.optDouble("cloud_cover",Double.NaN));
     v.put("rain",cur.optDouble("precipitation",Double.NaN));
     v.put("temperature",cur.optDouble("temperature_2m",Double.NaN));
     v.put("observedAt",cur.optString("time",""));
     v.put("source","Open-Meteo weather model (representative district point)");
     output.put(v);
    }
   }finally{c.disconnect();}
  }
  if(output.length()<70)throw new IllegalStateException("District forecast is incomplete");
  p.edit().putLong("when",now).putString("data",output.toString()).apply();
  return output;
 }
 static String condition(int code,boolean en){
  if(code>=95)return en?"Thunderstorm":"चट्याङ";
  if(code==71||code==73||code==75||code==77||code>=85&&code<=86)return en?"Snow":"हिमपात";
  if(code>=51&&code<=67||code>=80&&code<=82)return en?"Rain":"वर्षा";
  if(code==45||code==48)return en?"Fog":"कुहिरो";
  if(code>=2&&code<=3)return en?"Cloudy":"बादल";
  if(code==1)return en?"Partly cloudy":"आंशिक बादल";
  if(code==0)return en?"Sunny":"घाम";
  return en?"Unavailable":"उपलब्ध छैन";
 }
 static String icon(int code){
  if(code>=95)return "⛈";
  if(code>=71&&code<=77||code==85||code==86)return "❄";
  if(code>=51&&code<=67||code>=80&&code<=82)return "🌧";
  if(code==45||code==48)return "🌫";
  if(code>=2&&code<=3)return "☁";
  if(code==1)return "⛅";
  return code==0?"☀":"?";
 }
}
