package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Locale;
import java.util.ArrayList;

/** Explicit intent routing for Romanised Nepali / Nepali / English.
 * Only reports loaded observations, never invents a forecast or a government notice.
 */
final class SathiKnowledge {
    private SathiKnowledge(){}
    static String answer(String prompt,boolean en,JSONArray rivers,JSONArray govt,JSONArray weather,
                         JSONArray news,String localWeather,boolean nepalGps){
        return answer(prompt,en,rivers,govt,weather,news,localWeather,nepalGps,0);
    }
    static String answer(String prompt,boolean en,JSONArray rivers,JSONArray govt,JSONArray weather,
                         JSONArray news,String localWeather,boolean nepalGps,int lessonOffset){
        String q=prompt==null?"":prompt.trim().toLowerCase(Locale.ROOT);
        if(q.isEmpty())return en?"Ask about a particular river, district weather, current notice, news or knowledge topic."
                             :"कुन नदी, जिल्लाको मौसम, सरकारी सूचना, समाचार वा ज्ञानको विषय सोध्नुहुन्छ?";
        boolean weatherQ=has(q,"weather","mausam","mousam","मौसम","rain","pani par","badal","बादल","cloud","वर्षा","ghaam","घाम","तापक्रम","temperature");
        boolean newsQ=has(q,"news","समाचार","khabar","खबर","headline");
        boolean knowledgeQ=has(q,"गीता","gita","geeta","भगवद","krishna","कृष्ण","gyan","gyaan","ज्ञान","lesson","पढाइ","study","science","विज्ञान","book","पुस्तक","जीवन","जिन्दगी","karma","कर्म","motivation","बाढीबाट बच्न","flood safety");
        boolean riverQ=has(q,"नदी","खोला","river","khola","nadi","gauge","flood level","पानीको सतह","station","स्टेशन","water level");
        boolean govtQ=has(q,"सरकार","सरकारी","government","official alert","dhm notice","ndrrma","सूचना","notice","bulletin");
        boolean alertQ=has(q,"चेतावनी","chetauni","warning");
        boolean regional=has(q,"kathmandu","katmandu","ktm","काठमाडौं","काठमाडौँ");
        // Weather and news intents MUST win over river name substring matches.
        // Follow-up turns should add context instead of repeating the exact same answer.
        if(lessonOffset>0 && !knowledgeQ) {
            if(weatherQ && !riverQ) {
                int variant=lessonOffset%3;
                if(variant==1)return en?"More detail: the temperature/rain/cloud values in the district view come from the Open-Meteo representative-point model, not a nearby DHM rain gauge. For measured rain, check the Home DHM rain-gauge card."
                                    :"थप जानकारी: जिल्लाको तापक्रम, बादल र वर्षा Open-Meteo को प्रतिनिधि स्थानको मोडेल हो। वास्तविक मापनका लागि Home मा DHM वर्षामापक हेर्नुहोस्।";
                if(variant==2)return en?"For Kathmandu or another district, ask by name to see a loaded model. If it is unavailable, SATHI should not replace it with your phone's GPS weather."
                                    :"काठमाडौँ वा अर्को जिल्लाको नामसहित सोध्दा उपलब्ध भए जिल्लाकै मौसम देखिन्छ। उपलब्ध नभए फोनको GPS मौसमलाई त्यस जिल्लाको भनेर देखाउँदैन।";
                return en?"Weather changes over time. Please compare the model update time with the current reading and check official DHM alerts for hazards."
                          :"मौसम बदलिरहन्छ। अनुमानको अपडेट समय जाँच्नुहोस् र जोखिमका लागि आधिकारिक DHM चेतावनी हेर्नुहोस्।";
            }
            if(newsQ)return en?"SATHI shows only headlines delivered by the existing three-source feed. If there are no fresh verified items, tap Refresh News to check source availability; it does not mean Nepal has no news."
                                :"SATHI ले उपलब्ध तीन स्रोतको समाचार मात्र देखाउँछ। नयाँ खबर नदेखिए News Refresh गरेर स्रोत जाँच्नुहोस्; नेपालमा खबर नै छैन भन्ने होइन।";
            if(govtQ || (alertQ&&!riverQ))return en?"Only government DHM/NDRRMA bulletins within validFrom–validUntil count as active; app refreshes while open. The absence of a verified notice does not prove that river conditions are safe."
                                                    :"validFrom–validUntil भित्रका DHM/NDRRMA सूचना मात्र लागू मानिन्छन्। एप खुला हुँदा पुनः जाँचिन्छ। सूचना नभेटिनु नदी सुरक्षित छ भन्ने प्रमाण होइन।";
            if(riverQ)return en?"River levels are station-specific: compare the measured level, warning/danger threshold, observation timestamp and station location. An old reading cannot establish a live emergency."
                                  :"नदीको जोखिम बुझ्दा स्टेशनको जलस्तर, चेतावनी/खतरा सीमा, मापन समय र स्थान तुलना गर्नुपर्छ। पुरानो मापनलाई live खतरा मानिँदैन।";
        }
        if(weatherQ && !riverQ)return weatherAnswer(q,en,weather,localWeather,regional,nepalGps);
        if(newsQ)return newsAnswer(en,news);
        if(govtQ || (alertQ&&!riverQ))return governmentAnswer(en,govt);
        if(knowledgeQ)return GyanKnowledge.answerWithOffset(prompt,en,lessonOffset);
        if(riverQ)return riverAnswer(q,en,rivers);
        if(has(q,"nasa","landslide","पहिरो","satellite","उपग्रह"))
           return en?"The Advanced → NASA view displays model layers for Nepal. A satellite/model result is not an official flood warning."
                    :"उन्नत → NASA मा नेपालको मोडेल तह हेर्न सकिन्छ। Satellite वा मोडेलको अनुमान सरकारी बाढी चेतावनी होइन।";
        if(has(q,"gps","location","ठाउँ","स्थान","nearby","नजिक"))
           return nepalGps?(en?"Nepal GPS location is available. Check the nearest verified DHM gauges and their observation time."
                              :"नेपालभित्र GPS उपलब्ध छ। नजिकको DHM स्टेशन, मापन र समय जाँच्नुहोस्।")
               :(en?"Nepal nearby-river alert is inactive outside Nepal. Local weather uses GPS, not a Nepal river gauge."
                    :"नेपालबाहिर नेपालको नजिकको नदी अलर्ट लागू हुँदैन। GPS मौसम र नेपालका नदी मापन अलग हुन्।");
        if(has(q,"what can","what do","who are","तिम्रो काम","के गर्न सक्छ","help","मद्दत","feature","फिचर"))
           return en?"I can explain current loaded DHM river levels, district weather models, verified government notices, source-linked news and curated general knowledge. Ask a specific question."
                    :"म उपलब्ध DHM नदी मापन, जिल्लाको मौसम अनुमान, प्रमाणित सरकारी सूचना, स्रोतसहितको समाचार र सामान्य ज्ञान बुझाउँछु। कुनै खास प्रश्न सोध्नुहोस्।";
        return en?"I cannot identify the topic yet. For example ask ‘KTM weather k cha?’, ‘Bagmati river level?’, ‘government notice?’, ‘Gita advice?’ or ‘news?’"
                 :"प्रश्नको विषय स्पष्ट भएन। उदाहरण: ‘ktm weather k cha?’, ‘बागमती नदीको सतह?’, ‘सरकारी सूचना?’, ‘गीता ज्ञान?’ वा ‘समाचार?’";
    }
    private static String weatherAnswer(String q,boolean en,JSONArray weather,String localWeather,boolean ktm,boolean nepalGps){
        String district=ktm?"Kathmandu":"";
        JSONObject found=null;
        if(weather!=null)for(int i=0;i<weather.length();i++){
            JSONObject v=weather.optJSONObject(i);if(v==null)continue;
            String name=v.optString("name","").toLowerCase(Locale.ROOT);
            if(ktm && (name.equals("kathmandu")||name.equals("काठमाडौं")||name.equals("काठमाडौँ"))){found=v;break;}
            if(name.length()>=3&&q.contains(name)){found=v;district=v.optString("name");break;}
        }
        if(found!=null){
            int code=found.optInt("code",-1);
            double rain=found.optDouble("rain",Double.NaN),cloud=found.optDouble("cloud",Double.NaN),temp=found.optDouble("temperature",Double.NaN);
            StringBuilder b=new StringBuilder(en?"🌦 District weather model: ":"🌦 जिल्लाको मौसम अनुमान: ");
            b.append(district.isEmpty()?found.optString("name"):district);
            b.append("\n").append(DistrictWeatherStore.condition(code,en));
            if(Double.isFinite(temp))b.append(String.format(Locale.US," · %.1f°C",temp));
            if(Double.isFinite(rain))b.append(String.format(Locale.US," · %.1f mm",rain));
            if(Double.isFinite(cloud))b.append(String.format(Locale.US," · %.0f%%",cloud)).append(en?" cloud":" बादल");
            return b.toString()+(en?"\nOpen-Meteo estimate for a representative district point, not DHM measured rainfall."
                                 :"\nयो Open-Meteo को प्रतिनिधि स्थानको अनुमान हो, DHM को वास्तविक वर्षामापक होइन।");
        }
        if(ktm)return en?"Kathmandu's current district model is not loaded. Try again after weather refresh or choose Kathmandu in district search; I will not substitute your phone's UK weather."
                        :"काठमाडौँको ताजा जिल्ला मौसम अहिले load भएको छैन। Weather refresh भएपछि पुनः सोध्नुहोस्। UK मा रहेको फोनको मौसमलाई काठमाडौँको भनेर देखाउँदिनँ।";
        // If a location word is specified but its district model is missing, never substitute local GPS data.
        if(has(q,"pokhara","chitwan","biratnagar","butwal","birgunj","dharan","नेपालगञ्ज","बिर्तामोड"))
           return en?"The requested place is not matched in the loaded 77-district model. Choose the relevant district in the app."
                    :"सोधिएको ठाउँको मौसम हालको ७७-जिल्ला मोडेलसँग मिलेन। सम्बन्धित जिल्ला छानेर जाँच्नुहोस्।";
        if(localWeather!=null&&!localWeather.isEmpty())
           return (en?"🌤 Phone GPS weather: ":"🌤 फोनको GPS मौसम: ")+localWeather+
               (en?"\nThis is a local model estimate, not a DHM station reading.":"\nयो स्थानीय मोडेल अनुमान हो, DHM स्टेशनको मापन होइन।");
        return en?"Local weather has not loaded. Allow GPS or select a district to see its model."
                 :"हाल GPS मौसम load भएको छैन। GPS अनुमति दिनुहोस् वा जिल्ला छान्नुहोस्।";
    }
    private static String newsAnswer(boolean en,JSONArray news){
        if(news==null||news.length()==0)return en?"No recent source-linked story is loaded right now. This does not mean no news was published; check the News section's refresh status."
                                                 :"अहिले स्रोतसहितको नयाँ समाचार load भएको छैन। समाचार नै प्रकाशित भएको छैन भन्ने अर्थ होइन; समाचार खण्डमा Refresh अवस्था जाँच्नुहोस्।";
        StringBuilder b=new StringBuilder(en?"📰 Loaded source-linked headlines:":"📰 उपलब्ध स्रोतसहितका समाचार:");
        for(int i=0;i<Math.min(news.length(),4);i++){
            JSONObject x=news.optJSONObject(i);if(x==null)continue;
            b.append("\n• ").append(x.optString("title")).append(" (").append(x.optString("source")).append(")");
        }
        return b.toString();
    }
    private static String governmentAnswer(boolean en,JSONArray govt){
        JSONArray valid=new JSONArray();long now=System.currentTimeMillis();
        if(govt!=null)for(int i=0;i<govt.length();i++){JSONObject o=govt.optJSONObject(i);if(GovernmentNotices.valid(o,now))valid.put(o);}
        if(valid.length()==0)return en?"No active verified government bulletin is loaded. This is not an all-clear; check dhm.gov.np."
                                        :"हाल लागू भएको प्रमाणित सरकारी सूचना load छैन। खतरा छैन भन्ने होइन; dhm.gov.np पनि जाँच्नुहोस्।";
        StringBuilder b=new StringBuilder(en?"Active verified government bulletins:":"हाल लागू प्रमाणित सरकारी सूचना:");
        for(int i=0;i<Math.min(valid.length(),3);i++){JSONObject o=valid.optJSONObject(i);if(o==null)continue;
            b.append("\n• ").append(o.optString("agency")).append(" · ").append(GovernmentNotices.title(o,en))
                .append("\n").append(en?"Until ":"म्याद: ").append(o.optString("validUntil"));}
        return b.toString();
    }
    private static String riverAnswer(String q,boolean en,JSONArray rivers){
        ArrayList<JSONObject> matched=new ArrayList<>();
        if(rivers!=null)for(int i=0;i<rivers.length();i++){
            JSONObject r=rivers.optJSONObject(i);if(r==null)continue;
            String name=r.optString("name","").toLowerCase(Locale.ROOT);
            String district=r.optString("district","").toLowerCase(Locale.ROOT);
            boolean same=district.length()>3&&q.contains(district);
            if(!same){
                // Match distinctive river tokens only, never "at", "river" or "station".
                String[] tokens=name.replaceAll("\\b(river|khola|at|station|bridge|highway)\\b","").split("[ /()-]+");
                for(String tok:tokens)if(tok.length()>=5&&q.contains(tok)){same=true;break;}
            }
            if(same)matched.add(r);
        }
        if(matched.isEmpty()){
            int danger=0,warning=0,alert=0,normal=0,stale=0;
            if(rivers!=null)for(int i=0;i<rivers.length();i++){
                JSONObject r=rivers.optJSONObject(i);if(r==null)continue;
                String stage=r.optString("stage");
                if("danger".equals(stage))danger++;else if("warning".equals(stage))warning++;
                else if("alert".equals(stage))alert++;else if("normal".equals(stage))normal++;else stale++;
            }
            return (en?"DHM river stations loaded: ":"DHM नदी स्टेशन: ")+"🔴 "+danger+" 🟠 "+warning+" 🟡 "+alert+" 🔵 "+normal+
                (en?" · stale/unavailable ":" · पुरानो/नभएको ")+stale+
                (en?"\nName a particular river for exact level and observation time.":"\nठ्याक्कै मापनका लागि नदीको नाम भन्नुहोस्।");
        }
        StringBuilder b=new StringBuilder(en?"Matching verified river stations:":"मिल्दो आधिकारिक नदी स्टेशन:");
        for(int i=0;i<Math.min(matched.size(),5);i++){
            JSONObject r=matched.get(i);double level=r.optDouble("level",Double.NaN);
            b.append("\n• ").append(r.optString("name")).append(": ")
             .append(Double.isFinite(level)?String.format(Locale.US,"%.2f m",level):en?"no measured level":"मापन छैन")
             .append(" · ").append(r.optString("stage")).append(r.optBoolean("fresh")?(en?" (recent)":" (हालको)"):(en?" (stale)":" (पुरानो)"));
        }
        if(matched.size()>5)b.append(en?"\nSearch this district to see remaining stations.":"\nबाँकी हेर्न सम्बन्धित जिल्ला छान्नुहोस्।");
        return b.toString();
    }
    private static boolean has(String q,String...values){for(String x:values)if(q.contains(x))return true;return false;}
}
