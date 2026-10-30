package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Locale;

/** 
 * Source-backed government advisory relay. Distinct from DHM gauge Warning/Danger.
 * Never treat an old bulletin as current or invent a forecast from the headline.
 */
final class GovernmentNotices {
 static final String ENDPOINT="https://pjbuilts.com/api/floodsafe-official-weather";
 static final String DIRECT_DHM="https://www.dhm.gov.np/";
 private GovernmentNotices(){}
 static JSONObject fetch() throws Exception {
  HttpURLConnection c=(HttpURLConnection)new URL(ENDPOINT).openConnection();
  c.setConnectTimeout(10000);c.setReadTimeout(13000);c.setUseCaches(false);
  c.setRequestProperty("Accept","application/json");
  try{
   if(c.getResponseCode()!=200)throw new IllegalStateException("Notice HTTP "+c.getResponseCode());
   StringBuilder b=new StringBuilder();
   try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){
    String line;while((line=r.readLine())!=null){b.append(line);if(b.length()>600000)throw new IllegalStateException("Oversized official bulletin");}
   }
   JSONObject j=new JSONObject(b.toString());
   if(!"notices_available".equals(j.optString("status")) && !"no_notices".equals(j.optString("status")))throw new IllegalStateException("Notices not verified");
   return j;
  }finally{c.disconnect();}
 }
 static long time(String iso){
  try{return Instant.parse(iso).toEpochMilli();}catch(Exception ignored){return 0;}
 }
 static boolean valid(JSONObject item,long now) {
  if(item==null)return false;
  String issuer=item.optString("agency");
  if(!("DHM".equals(issuer)||"NDRRMA".equals(issuer)))return false;
  String stage=item.optString("status");
  if(!"in_effect".equals(stage))return false;
  long start=time(item.optString("validFrom")),end=time(item.optString("validUntil"));
  long issued=time(item.optString("issuedAt"));
  String url=item.optString("sourceUrl");
  return start>0&&end>start&&issued>0&&issued<=now+5*60000L
      &&start<=now&&now<end
      &&url.startsWith("https://")&&(url.contains("dhm.gov.np")||url.contains("ndrrma")||url.contains("x.com/DHM_")||url.contains("x.com/NMD_Weather")||url.contains("x.com/NDRRMA_"));
 }
 static JSONArray active(JSONObject root,long now){
  JSONArray raw=root.optJSONArray("items"),valid=new JSONArray();if(raw==null)return valid;
  for(int i=0;i<raw.length();i++){JSONObject o=raw.optJSONObject(i);if(valid(o,now))valid.put(o);}
  return valid;
 }
 static String summary(JSONObject o,boolean english){
  return o.optString(english?"summaryEn":"summaryNe", "");
 }
 static String title(JSONObject o,boolean english){
  return o.optString(english?"titleEn":"titleNe", "");
 }
 static String period(JSONObject o,boolean english){
  return (english?"Starts: ":"सुरु: ")+o.optString("validFrom","—")
      +"\n"+(english?"Ends: ":"समाप्त: ")+o.optString("validUntil","—");
 }
}