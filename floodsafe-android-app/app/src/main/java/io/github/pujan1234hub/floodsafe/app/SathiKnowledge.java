package io.github.pujan1234hub.floodsafe.app;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Locale;
import java.util.ArrayList;

/**
 * Source-grounded on-device SATHI Q&A: uses only loaded FloodSafe data,
 * never hallucinates an AI prediction or an official warning.
 */
final class SathiKnowledge {
 private SathiKnowledge(){}
 static String answer(String prompt,boolean en,JSONArray rivers,JSONArray govt,JSONArray weather,JSONArray news,String localWeather,boolean nepalGps){
  String q=prompt==null?"":prompt.trim().toLowerCase(Locale.ROOT);
  if(q.isEmpty())return en?"Ask about a district, river station, weather, government bulletin or app.":"जिल्ला, नदी स्टेशन, मौसम, सरकारी सूचना वा app बारे सोध्नुहोस्।";
  boolean riverQ=contains(q,"नदी","खोला","river","khola","flood","बाढी","level","पानीको सतह","station","स्टेशन");
  boolean explicitGovt=contains(q,"सरकार","सरकारी","government","official alert","dhm","ndrrma","सूचना","notice","bulletin");
  // A river-warning question must consult river gauges, not jump to the government bulletin screen.
  boolean govtQ=explicitGovt||(!riverQ&&contains(q,"चेतावनी","chetauni","warning"));
  boolean weatherQ=contains(q,"मौसम","weather","rain","वर्षा","badal","बादल","cloud","धाम","घाम","हुरी","storm","thunder","चट्याङ","snow","हिमपात");
  if(govtQ){
   JSONArray verified=new JSONArray();long now=System.currentTimeMillis();
   if(govt!=null)for(int i=0;i<govt.length();i++){JSONObject n=govt.optJSONObject(i);if(GovernmentNotices.valid(n,now))verified.put(n);}
   govt=verified;
   if(govt.length()==0)return en?"No currently verified government bulletin in the latest check. This is not an all-clear. Check dhm.gov.np or call 1155.":"हालको जाँचमा लागू भएको प्रमाणित सरकारी बुलेटिन भेटिएन। यसको अर्थ जोखिम छैन भन्ने होइन। dhm.gov.np वा ११५५ मा जाँच्नुहोस्।";
   StringBuilder b=new StringBuilder(en?"Current/upcoming source-linked government advisories (relayed):":"स्रोतसहितका लागू/आगामी सरकारी सूचना (relay):");
   for(int i=0;i<Math.min(3,govt.length());i++){JSONObject g=govt.optJSONObject(i);if(g==null)continue;b.append("\n").append(i+1).append(". ").append(g.optString("agency")).append(": ")
    .append(GovernmentNotices.title(g,en)).append("\n")
    .append(en?"Valid: ":"लागू: ").append(g.optString("validFrom")).append(" – ").append(g.optString("validUntil"));}
   b.append(en?"\nVerify details in Government Advisories above.":"\nमूल विवरण माथिको सरकारी सूचना खण्डमा हेर्नुहोस्।");
   return b.toString();
  }
  // River name or district name explicitly mentioned: match against actual stations.
  ArrayList<JSONObject> matched=new ArrayList<>();
  if(rivers!=null)for(int i=0;i<rivers.length();i++){
   JSONObject r=rivers.optJSONObject(i);if(r==null)continue;
   String name=r.optString("name","").toLowerCase(Locale.ROOT),district=r.optString("district","").toLowerCase(Locale.ROOT);
   String[] words=name.replace("river","").replace("khola","").replaceAll("\\bat\\b","").split("[ /()-]+");
   boolean selected=false;
   for(String w:words)if(w.length()>=4&&q.contains(w)){selected=true;break;}
   if(!selected&&district.length()>=4&&q.contains(district))selected=true;
   if(selected)matched.add(r);
  }
  if(!matched.isEmpty()){
   StringBuilder b=new StringBuilder(en?"Matching official river stations:":"मिल्दो आधिकारिक नदी स्टेशन:");
   for(int i=0;i<Math.min(5,matched.size());i++){
    JSONObject r=matched.get(i);b.append("\n• ").append(r.optString("name"));
    double lev=r.optDouble("level",Double.NaN);
    b.append(" — ").append(Double.isFinite(lev)?String.format(Locale.US,"%.2f m",lev):en?"no current level":"नयाँ मापन छैन");
    b.append(" · ").append(r.optString("stage","unknown"));
    if(r.optBoolean("fresh",false))b.append(en?" · recent reading":" · हालको मापन");
    else b.append(en?" · older/unverified":" · पुरानो/अपुष्ट");
   }
   if(matched.size()>5)b.append(en?"\nSelect a district to see more.":"\nथप हेर्न जिल्ला छान्नुहोस्।");
   return b.toString();
  }
  if(weather!=null)for(int i=0;i<weather.length();i++){
   JSONObject d=weather.optJSONObject(i);if(d==null)continue;
   String name=d.optString("name","").toLowerCase(Locale.ROOT);
   if(name.length()<4||!q.contains(name))continue;
   int code=d.optInt("code",-1);
   return (en?"District model: ":"जिल्लाको मौसम अनुमान: ")+d.optString("name")+
     " · "+DistrictWeatherStore.condition(code,en)+
     " · "+String.format(Locale.US,"%.1f mm",d.optDouble("rain",Double.NaN))+
     " · "+String.format(Locale.US,"%.0f%%",d.optDouble("cloud",Double.NaN))+
     (en?" cloud. Representative point; not an official rain gauge.":" बादल। प्रतिनिधि स्थानको मोडेल हो, आधिकारिक वर्षामापक होइन।");
  }
  if(contains(q,"news","समाचार","khabar","खबर")){
   if(news==null||news.length()==0)return en?"No verified fresh news in the current feed.":"हालको समाचार स्रोतमा नयाँ प्रमाणित खबर छैन।";
   StringBuilder b=new StringBuilder(en?"Latest source-linked news:":"स्रोतसहितका पछिल्ला समाचार:");
   for(int i=0;i<Math.min(3,news.length());i++){JSONObject v=news.optJSONObject(i);if(v!=null)b.append("\n• ").append(v.optString("title")).append(" (").append(v.optString("source")).append(")");}
   return b.toString();
  }
  if(weatherQ)return localWeather==null||localWeather.isEmpty()
    ?(en?"Local weather data not yet available; choose GPS/district.":"हालको मौसम data उपलब्ध छैन; GPS वा जिल्ला छान्नुहोस्।")
    :(en?"Current GPS weather: ":"हालको GPS मौसम: ")+localWeather;
  if(riverQ){
   int danger=0,warning=0,alert=0,normal=0,stale=0;
   if(rivers!=null)for(int i=0;i<rivers.length();i++){
    JSONObject r=rivers.optJSONObject(i);if(r==null)continue;
    String stage=r.optString("stage");
    if("danger".equals(stage))danger++;else if("warning".equals(stage))warning++;
    else if("alert".equals(stage))alert++;else if("normal".equals(stage))normal++;else stale++;
   }
   return (en?"Latest river gauge categories: ":"नदी स्टेशनका पछिल्ला वर्ग: ")+"🔴 "+danger+" 🟠 "+warning+" 🟡 "+alert+" 🔵 "+normal+
     (en?" · no confirmed measurement ":" · अपुष्ट मापन ")+stale+
     (en?". Government weather advisories are separate.": "। सरकारी मौसम चेतावनी यसभन्दा छुट्टै हुन्।");
  }
  if(contains(q,"location","gps","ठाउँ","स्थान","nearby","नजिक")){
   return nepalGps?(en?"Nepal GPS available. Nearby rivers use verified readings within 30 km.":"नेपालको GPS उपलब्ध छ। ३० किमिभित्रको प्रमाणित नदी स्टेशन खोजिन्छ।")
     :(en?"Outside Nepal or GPS unavailable: Nepal-specific nearby river alerts are inactive.":"नेपालबाहिर वा GPS उपलब्ध छैन: नेपालको नजिकका नदी अलर्ट निष्क्रिय छन्।");
  }
  if(contains(q,"nasa","landslide","पहिरो","satellite","उपग्रह"))return en?"Open Advanced > NASA for Nepal-focused rainfall and landslide model layers. Models are not government warnings.":"उन्नत जानकारी > NASA मा नेपालको वर्षा र पहिरोका मोडेल तह हेर्नुहोस्। मोडेल सरकारी चेतावनी होइन।";
  if(contains(q,"app","feature","फिचर","के गर्न","help","सहायता"))return en?"FloodSafe shows DHM/BIPAD river gauges, government weather advisories, district weather, 7-day GloFAS rainfall/flow models and Nepal-only 2 km emergency risk.":"FloodSafe मा DHM/BIPAD नदी मापन, सरकारी मौसम सूचना, जिल्लाको मौसम, ७ दिनको GloFAS पूर्वानुमान र नेपालमा २ किमिभित्रको जोखिम हेर्न सकिन्छ।";
  return en?"I don't have a verified answer in FloodSafe's available data. Please ask about a river, district, DHM notice, weather or news.":"FloodSafe मा उपलब्ध प्रमाणित data बाट यो प्रश्नको उत्तर भेटिएन। नदी, जिल्ला, DHM सूचना, मौसम वा समाचारबारे सोध्नुहोस्।";
 }
 private static boolean contains(String q,String...words){for(String w:words)if(q.contains(w))return true;return false;}
}
