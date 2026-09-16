from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path = src / 'NativeFullActivity.java'
helper_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'

activity = activity_path.read_text(encoding='utf-8')
helper = helper_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# ---------------- MAP: remove invalid outside mask and clip rivers to Nepal districts ----------------
mask_block = '''            if (nepalMaskGeoJson != null && style.getSource("fs-nepal-mask") == null) {\n                style.addSource(new GeoJsonSource("fs-nepal-mask", nepalMaskGeoJson));\n                style.addLayer(new FillLayer("fs-nepal-mask-layer", "fs-nepal-mask").withProperties(\n                        fillColor("#071720"), fillOpacity(0.88f)));\n            }'''
helper = helper.replace(mask_block, '''            // v0.8.4: no polygon-hole overlay mask. Rivers are clipped to Nepal districts during load.\n''')

# Make every district name visible. They are real GeoJSON names, not station/district numeric IDs.
helper = helper.replace(
    'textField("{nameEn}"), textSize(10.5f), textColor("#ffffff"),\n                        textHaloColor("#173646"), textHaloWidth(1.6f), textAllowOverlap(false)))',
    'textField("{nameEn}"), textSize(9.6f), textColor("#ffffff"),\n                        textHaloColor("#173646"), textHaloWidth(1.7f), textAllowOverlap(true)))')

# Add river label GeoJSON state.
if 'private String riverLabelsGeoJson = null;' not in helper:
    helper = helper.replace('private String riversGeoJson = null;', 'private String riversGeoJson = null;\n    private String riverLabelsGeoJson = null;')

# Parse district geometry once for river clipping.
helper = helper.replace(
    'JSONObject root = new JSONObject(raw);\n                JSONArray ways = root.optJSONArray("waterways");',
    'JSONObject root = new JSONObject(raw);\n                JSONObject nepalDistricts = districtGeoJson == null ? null : new JSONObject(districtGeoJson);\n                JSONArray ways = root.optJSONArray("waterways");', 1)

# Reject river points that are outside all 77 Nepal district polygons.
helper = helper.replace(
    'if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo)) rw.points.add(new double[]{lo, la});',
    'if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo) && (nepalDistricts == null || insideDistricts(lo, la, nepalDistricts))) rw.points.add(new double[]{lo, la});')

# Generate labels for named rivers/streams after loading.
helper = helper.replace(
    'riversGeoJson = makeRiversGeoJson(all);',
    'riversGeoJson = makeRiversGeoJson(all);\n                    riverLabelsGeoJson = makeRiverLabelsGeoJson(all);', 1)

# Stronger consistent river glow and a bright inner line.
helper = helper.replace(
    'lineColor("#003d55"), lineWidth(4.0f), lineOpacity(0.55f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)))',
    'lineColor("#008fc7"), lineWidth(6.2f), lineOpacity(0.42f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)))')
helper = helper.replace(
    'lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)))',
    'lineColor("#54e7ff"), lineWidth(2.15f), lineOpacity(1.0f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)))')

# River-name layer. It uses midpoint labels from the bundled named waterway data.
river_layer_anchor = '''            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#d6fbff", 2.7f, 0.90f);'''
river_layer_add = '''            if (riverLabelsGeoJson != null && style.getSource("fs-river-labels") == null) {\n                style.addSource(new GeoJsonSource("fs-river-labels", riverLabelsGeoJson));\n                style.addLayer(new SymbolLayer("fs-river-labels-layer", "fs-river-labels").withProperties(\n                        textField("{name}"), textSize(9.4f), textColor("#bff6ff"),\n                        textHaloColor("#113b4c"), textHaloWidth(1.7f), textAllowOverlap(false)));\n            }\n'''
if 'fs-river-labels-layer' not in helper:
    helper = helper.replace(river_layer_anchor, river_layer_add + river_layer_anchor, 1)

# Keep station names anchored at exact gauge coordinates, but avoid them drowning out district/river labels.
helper = helper.replace(
    'textField("{name}"), textSize(10.0f), textColor("#ffffff"),\n                        textHaloColor("#163846"), textHaloWidth(1.5f), textAllowOverlap(false)))',
    'textField("{name}"), textSize(9.2f), textColor("#ffffff"),\n                        textHaloColor("#163846"), textHaloWidth(1.6f), textAllowOverlap(false)))')

# Geometry helpers for accurate Nepal clipping and named river midpoint labels.
geo_anchor = '    private static String makeNepalOutsideMask(String districtJson) throws Exception {'
geo_helpers = '''    private static boolean insideDistricts(double lo, double la, JSONObject districtRoot) {\n        try {\n            JSONArray fs = districtRoot.optJSONArray("features");\n            if (fs == null) return true;\n            for (int i=0;i<fs.length();i++) {\n                JSONObject f=fs.optJSONObject(i); if(f==null) continue;\n                JSONObject g=f.optJSONObject("geometry"); if(g!=null && geometryContains(g,lo,la)) return true;\n            }\n        } catch (Exception ignored) {}\n        return false;\n    }\n\n    private static boolean geometryContains(JSONObject g,double x,double y) {\n        try {\n            String type=g.optString("type"); JSONArray c=g.optJSONArray("coordinates"); if(c==null)return false;\n            if("Polygon".equals(type)) return polygonContains(c,x,y);\n            if("MultiPolygon".equals(type)) { for(int i=0;i<c.length();i++){JSONArray p=c.optJSONArray(i);if(p!=null&&polygonContains(p,x,y))return true;} }\n        } catch(Exception ignored){}\n        return false;\n    }\n\n    private static boolean polygonContains(JSONArray poly,double x,double y) {\n        JSONArray ring=poly.optJSONArray(0); if(ring==null||ring.length()<3)return false;\n        boolean inside=false; int j=ring.length()-1;\n        for(int i=0;i<ring.length();j=i++){JSONArray a=ring.optJSONArray(i),b=ring.optJSONArray(j);if(a==null||b==null)continue;double xi=a.optDouble(0),yi=a.optDouble(1),xj=b.optDouble(0),yj=b.optDouble(1);boolean hit=((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/((yj-yi)==0?1e-12:(yj-yi))+xi);if(hit)inside=!inside;}\n        return inside;\n    }\n\n    private static String makeRiverLabelsGeoJson(List<RiverWay> ways) throws Exception {\n        JSONArray out=new JSONArray(); java.util.HashSet<String> seen=new java.util.HashSet<>(); int count=0;\n        for(RiverWay r:ways){\n            String n=r.name==null?"":r.name.trim(); if(n.isEmpty()||n.equals("नदी / खोला")||n.equalsIgnoreCase("river"))continue;\n            String key=n.toLowerCase(Locale.ROOT); if(seen.contains(key)||r.points.size()<2)continue; seen.add(key);\n            double[] p=r.points.get(r.points.size()/2); out.put(pointFeature(p[0],p[1],n)); if(++count>=420)break;\n        }\n        return new JSONObject().put("type","FeatureCollection").put("features",out).toString();\n    }\n\n'''
if 'private static boolean insideDistricts' not in helper:
    helper = helper.replace(geo_anchor, geo_helpers + geo_anchor, 1)

helper_path.write_text(helper, encoding='utf-8')

# ---------------- DISTRICT PICKER: resolve numeric API IDs to actual district names ----------------
if 'private volatile JSONArray districtFeaturesCache;' not in activity:
    activity = activity.replace('private String currentWeather="";', 'private String currentWeather="";\n    private volatile JSONArray districtFeaturesCache;\n    private double lastWeatherTemp=Double.NaN,lastWeatherRain=Double.NaN,lastWeatherHumidity=Double.NaN,lastWeatherWind=Double.NaN;\n    private String lastWeatherTiming="";\n    private final List<NewsItem> latestNews=new ArrayList<>();\n    private String lastSathiQuestion="",lastSathiAnswer="";')

# Replace raw district with coordinate-grounded district name.
activity = activity.replace(
    'String district=str(r,"districtName","district_name","district");return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank);',
    'String district=resolveDistrictName(str(r,"districtName","district_name","district"),a,o);return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank);')

# Add Activity point-in-polygon resolver before refreshRiverUi.
resolve_anchor = '    private void refreshRiverUi(){'
resolve_methods = '''    private String resolveDistrictName(String raw,double la,double lo){\n        String x=raw==null?"":raw.trim();\n        if(!x.isEmpty()&&!x.matches("\\\\d+"))return x;\n        try{\n            JSONArray fs=districtFeaturesCache;\n            if(fs==null){synchronized(this){fs=districtFeaturesCache;if(fs==null){JSONObject j=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");fs=j.optJSONArray("features");districtFeaturesCache=fs;}}}\n            if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i);if(f==null)continue;JSONObject g=f.optJSONObject("geometry");if(g!=null&&activityGeometryContains(g,lo,la)){JSONObject p=f.optJSONObject("properties");String n=p==null?"":p.optString("nameEn",p.optString("name",""));if(!n.trim().isEmpty())return n.trim();}}\n        }catch(Exception ignored){}\n        return x.matches("\\\\d+")?t("जिल्ला अज्ञात","Unknown district"):x;\n    }\n    private static boolean activityGeometryContains(JSONObject g,double x,double y){try{String type=g.optString("type");JSONArray c=g.optJSONArray("coordinates");if(c==null)return false;if("Polygon".equals(type))return activityPolygonContains(c,x,y);if("MultiPolygon".equals(type))for(int i=0;i<c.length();i++){JSONArray p=c.optJSONArray(i);if(p!=null&&activityPolygonContains(p,x,y))return true;}}catch(Exception ignored){}return false;}\n    private static boolean activityPolygonContains(JSONArray poly,double x,double y){JSONArray r=poly.optJSONArray(0);if(r==null||r.length()<3)return false;boolean in=false;int j=r.length()-1;for(int i=0;i<r.length();j=i++){JSONArray a=r.optJSONArray(i),b=r.optJSONArray(j);if(a==null||b==null)continue;double xi=a.optDouble(0),yi=a.optDouble(1),xj=b.optDouble(0),yj=b.optDouble(1);boolean hit=((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/((yj-yi)==0?1e-12:(yj-yi))+xi);if(hit)in=!in;}return in;}\n\n'''
if 'private String resolveDistrictName' not in activity:
    activity = activity.replace(resolve_anchor, resolve_methods + resolve_anchor, 1)

# ---------------- SATHI: app-grounded conversational brain ----------------
# Store richer weather snapshot for conversational answers.
weather_old = 'currentWeather=ws;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);});'
weather_new = 'currentWeather=ws;lastWeatherTemp=te;lastWeatherRain=pr;lastWeatherHumidity=hu;lastWeatherWind=wi;lastWeatherTiming=timing;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);});'
activity = activity.replace(weather_old, weather_new)

# Cache latest news so SATHI can answer from exactly the same app feed.
activity = activity.replace('private void renderNews(List<NewsItem> out){newsList.removeAllViews();', 'private void renderNews(List<NewsItem> out){synchronized(latestNews){latestNews.clear();latestNews.addAll(out);}newsList.removeAllViews();')

# Typed send uses the conversational async brain.
activity = activity.replace('String a=answerSathi(q);answer.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+a);input.setText("");', 'answer.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+t("हेर्दैछु है…","Checking…"));input.setText("");askSathi(q,answer,false);')

# Voice results use the same brain, then speak the grounded answer.
activity = activity.replace('String a=answerSathi(q);out.setText("तपाईं: "+q+"\\n\\nSATHI: "+a);speak(a);', 'out.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+t("हेर्दैछु है…","Checking…"));askSathi(q,out,true);')

# Replace old keyword-only answer function with a richer app-grounded engine.
start = activity.find('    private String answerSathi(String q){')
end = activity.find('    private void consumeSathiIntent(Intent i)', start)
if start < 0 or end < 0:
    raise SystemExit('SATHI answer function anchors missing')

brain = r'''    private void askSathi(String q,TextView out,boolean speakOut){
        final String question=q==null?"":q.trim();if(question.isEmpty())return;lastSathiQuestion=question;
        String nq=sathiNorm(question);
        String local=answerSathiLocal(question,nq);
        if(local!=null&&!local.isEmpty()){deliverSathi(question,local,out,speakOut);return;}
        PlacePoint pp=sathiPlace(question,nq);
        if(pp!=null&&(hasAny(nq,"weather","mausam","temp","temperature","tapkram","तापक्रम","मौसम","वर्षा","rain","bholi","भोलि"))){
            out.setText(t("तपाईं: ","You: ")+question+"\n\nSATHI: "+t(pp.name+" को live weather हेर्दैछु है…","Checking live weather for "+pp.name+"…"));
            io.execute(()->{String a;try{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.5f&longitude=%.5f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&forecast_days=2&timezone=auto",pp.lat,pp.lon);JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),hu=c.optDouble("relative_humidity_2m",Double.NaN),pr=c.optDouble("precipitation",0),wi=c.optDouble("wind_speed_10m",Double.NaN);StringBuilder b=new StringBuilder();b.append(t("हो 😄 ","Sure 🙂 ")).append(pp.name).append(t(" मा अहिले "," is currently ")).append(Double.isFinite(te)?Math.round(te)+"°C":"temperature unavailable");if(Double.isFinite(hu))b.append(t(", आर्द्रता ",", humidity ")).append(Math.round(hu)).append("%");if(Double.isFinite(wi))b.append(t(", हावा ",", wind ")).append(Math.round(wi)).append(" km/h");b.append(pr>=.2?t(" र हल्का/मापनयोग्य वर्षा "+String.format(Locale.US,"%.1f",pr)+" mm छ।"," with "+String.format(Locale.US,"%.1f",pr)+" mm precipitation."):t(" र अहिले उल्लेख्य वर्षा छैन।"," with no significant rain right now."));JSONObject d=j.optJSONObject("daily");if(d!=null){JSONArray mx=d.optJSONArray("temperature_2m_max"),mn=d.optJSONArray("temperature_2m_min"),rp=d.optJSONArray("precipitation_probability_max");if(mx!=null&&mx.length()>1){b.append(t(" भोलि करिब "," Tomorrow around ")).append(Math.round(mx.optDouble(1))).append("°/").append(Math.round(mn.optDouble(1))).append("°C");if(rp!=null)b.append(t(", rain chance ",", rain chance ")).append(rp.optInt(1)).append("%");b.append("।");}}a=b.toString();}catch(Exception e){a=t("त्यो ठाउँको live weather अहिले fetch हुन सकेन। App को हालको-location weather चाहिँ फेरि सोध्न सक्नुहुन्छ।","I couldn't fetch live weather for that place just now. You can still ask for the app's current-location weather.");}final String ans=a;runOnUiThread(()->deliverSathi(question,ans,out,speakOut));});return;
        }
        String fallback=t("म FloodSafe Nepal को SATHI हुँ 🙂 म app भित्रको live मौसम, नदी/खोला station, water level, Warning/Danger, तपाईंको नजिकको risk, Human Status, समाचार र notification बारे मात्र verified app data बाट उत्तर दिन्छु। त्यो दायराभित्र जे सोध्नुभयो म बुझेर भन्न खोज्छु।","I'm FloodSafe Nepal's SATHI 🙂 I answer from the app's own weather, river stations, water levels, Warning/Danger, nearby risk, Human Status, news and notifications. Ask me anything within that app data.");
        deliverSathi(question,fallback,out,speakOut);
    }

    private void deliverSathi(String q,String a,TextView out,boolean speakOut){lastSathiAnswer=a;out.setText(t("तपाईं: ","You: ")+q+"\n\nSATHI: "+a);if(speakOut)speak(a);}

    private String answerSathiLocal(String q,String x){
        if(hasAny(x,"hello","hi","hey","namaste","नमस्ते","sathi")){if(x.length()<24)return t("नमस्ते 😄 म यतै छु। मौसम, नदी, risk, समाचार वा app को status के हेर्ने?","Hi 😄 I'm here. Want weather, river risk, news, or app status?");}
        if(hasAny(x,"thank","thanks","dhanyabad","धन्यवाद"))return t("स्वागत छ 😄 FloodSafe को data चाहिँदा सोधिरहनु है।","You're welcome 😄 Ask anytime about FloodSafe data.");
        if(hasAny(x,"notification","notif","सूचना","alert kati","2 hour","2hr","२ घण्टा"))return t("हो, routine weather digest करिब २-२ घण्टामा आउँछ। Verified fresh नदी Warning/Danger चाहिँ सम्बन्धित station/river को २ km भित्र भए २ घण्टा कुर्दैन—emergency alert छुट्टै आउँछ।","Routine weather digests are about every 2 hours. A verified fresh river Warning/Danger within 2 km is separate and does not wait for the 2-hour cycle.");
        if(hasAny(x,"human status","human","मानवीय","death","deaths","injured","missing","rescued")){String d=humanDeaths==null?"—":String.valueOf(humanDeaths.getText()),i=humanInjured==null?"—":String.valueOf(humanInjured.getText()),m=humanMissing==null?"—":String.valueOf(humanMissing.getText()),r=humanRescued==null?"—":String.valueOf(humanRescued.getText());return t("App को हालको Human Status card अनुसार: मृत्यु "+d+", घाइते "+i+", बेपत्ता "+m+", उद्धार "+r+"। यो card disaster हुँदा latest 10-day data का लागि देखिन्छ।","Current Human Status card: deaths "+d+", injured "+i+", missing "+m+", rescued "+r+". This card is for the latest 10-day disaster status when active.");}
        if(hasAny(x,"news","samachar","समाचार","खबर")){synchronized(latestNews){if(!latestNews.isEmpty()){StringBuilder b=new StringBuilder(t("App मा अहिले देखिएका fresh खबरमध्ये: ","Fresh stories currently in the app: "));for(int n=0;n<Math.min(3,latestNews.size());n++){NewsItem z=latestNews.get(n);if(n>0)b.append(" • ");b.append(z.title).append(" — ").append(z.source);}return b.toString();}}return t("अहिले fresh live news छैन, त्यसैले app ले ज्ञानको कुरा देखाइरहेको हुन सक्छ।","There is no fresh live news right now, so the app may be showing a knowledge tip instead.");}
        if(hasAny(x,"app le k","feature","features","ke garxa","k garxa","के गर्छ","के के"))return t("FloodSafe Nepal ले current-location weather, rain timing, official नदी station/water level, 2 km verified Warning/Danger alert, nearby risk, Nepal river map, district-wise stations, 10-day Human Status, fresh news/ज्ञानको कुरा, background monitoring र SATHI दिन्छ।","FloodSafe Nepal provides current-location weather, rain timing, official river stations/water levels, verified Warning/Danger alerts within 2 km, nearby risk, Nepal river map, district-wise stations, 10-day Human Status, fresh news/knowledge tips, background monitoring and SATHI.");

        if(hasAny(x,"river","nadi","khola","flood","बाढी","नदी","खोला","warning","danger","water level","jalastar","जलस्तर")){
            List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}if(copy.isEmpty())return t("Official नदी data refresh हुँदैछ। Reading आएपछि म यहीँबाट बताउँछु।","Official river data is refreshing. I'll answer from it as soon as readings arrive.");
            RiverStation matched=findSathiStation(x,copy);if(matched!=null)return sathiStationAnswer(matched);
            if(hasAny(x,"near","najik","nजिक","नजिक","mero","मेरो")){copy.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));StringBuilder b=new StringBuilder(t("तपाईंको app-location नजिकका station: ","Nearest stations to your app location: "));int shown=0;for(RiverStation s:copy){double km=distanceKm(s.lat,s.lon);if(!Double.isFinite(km))continue;if(shown++>0)b.append(" • ");b.append(s.name).append(String.format(Locale.US," %.1f km",km)).append(" ").append(stageName(s.stage));if(shown>=3)break;}return shown==0?t("नेपालभित्र current GPS आएपछि नजिकको station बताउँछु।","Once the app has a Nepal GPS location, I can tell you the nearest stations."):b.toString();}
            int d=0,w=0,a=0,n=0,st=0;List<String> hot=new ArrayList<>();for(RiverStation s:copy){if("danger".equals(s.stage)){d++;hot.add("🔴 "+s.name);}else if("warning".equals(s.stage)){w++;hot.add("🟠 "+s.name);}else if("alert".equals(s.stage))a++;else if("normal".equals(s.stage))n++;else st++;}StringBuilder b=new StringBuilder(t("Official river feed अहिले: ","Official river feed now: ")).append("🔴 ").append(d).append("  🟠 ").append(w).append("  🟡 ").append(a).append("  🔵 ").append(n).append(t(" • stale/unknown "," • stale/unknown ")).append(st);if(!hot.isEmpty()){b.append(t("। ध्यान दिनुपर्ने: ",". Needs attention: "));for(int i=0;i<Math.min(4,hot.size());i++){if(i>0)b.append(", ");b.append(hot.get(i));}}return b.toString();
        }

        if(hasAny(x,"weather","mausam","temp","temperature","tapkram","तापक्रम","मौसम","वर्षा","rain","humidity","wind","हावा")){
            if(Double.isFinite(lastWeatherTemp)){String label=place==null?t("हालको app location","current app location"):String.valueOf(place.getText());StringBuilder b=new StringBuilder(t("हो 😄 ","Sure 🙂 ")).append(label).append(t(" मा अहिले "," is currently ")).append(Math.round(lastWeatherTemp)).append("°C");if(Double.isFinite(lastWeatherHumidity))b.append(t(", आर्द्रता ",", humidity ")).append(Math.round(lastWeatherHumidity)).append("%");if(Double.isFinite(lastWeatherWind))b.append(t(", हावा ",", wind ")).append(Math.round(lastWeatherWind)).append(" km/h");if(Double.isFinite(lastWeatherRain))b.append(t(", वर्षा ",", precipitation ")).append(String.format(Locale.US,"%.1f mm",lastWeatherRain));if(lastWeatherTiming!=null&&!lastWeatherTiming.isEmpty())b.append("। ").append(lastWeatherTiming);return b.toString();}return t("हालको location को weather data refresh हुँदैछ।","Current-location weather is refreshing.");
        }
        if(hasAny(x,"location","gps","स्थान","ठाउँ"))return isNepal(lat,lon)?t("App को current GPS नेपालभित्र set छ। River warning matching यही location बाट २ km radius मा हुन्छ।","The app has a current GPS location in Nepal. River-warning matching uses this location within a 2 km radius."):t("अहिले GPS नेपालभित्र छैन/उपलब्ध छैन, त्यसैले nearby river emergency matching सक्रिय हुँदैन। Weather चाहिँ current location अनुसार देखिन सक्छ।","GPS is not currently available inside Nepal, so nearby river emergency matching is not active. Weather can still use the current location.");
        return null;
    }

    private RiverStation findSathiStation(String x,List<RiverStation> list){RiverStation best=null;int score=0;for(RiverStation s:list){String n=sathiNorm(s.name),d=sathiNorm(s.district);int sc=0;for(String tok:x.split(" ")){if(tok.length()<3)continue;if(n.contains(tok))sc+=4;if(d.contains(tok))sc+=2;}if(x.contains(n)&&n.length()>3)sc+=20;if(sc>score){score=sc;best=s;}}return score>=4?best:null;}
    private String sathiStationAnswer(RiverStation s){StringBuilder b=new StringBuilder();b.append(t("हेरें है 🙂 ","I checked 🙂 ")).append(s.name);if(s.district!=null&&!s.district.isEmpty())b.append(" (").append(s.district).append(")");b.append(t(" को status "," status is ")).append(stageName(s.stage));if(Double.isFinite(s.level))b.append(t(", जलस्तर ",", level ")).append(String.format(Locale.US,"%.2f m",s.level));if(s.at>0)b.append(t(", reading ",", reading ")).append(Math.max(0,(System.currentTimeMillis()-s.at)/60000)).append(t(" मिनेटअघि"," min ago"));if(!s.fresh)b.append(t("। यो stale/unknown हो—live खतरा भनेर म भन्दिनँ।",". This is stale/unknown, so I won't present it as a live threat."));else if("danger".equals(s.stage)||"warning".equals(s.stage))b.append(t("। Fresh official warning भएकाले ध्यान दिनुहोस्।",". This is a fresh official warning, so pay attention."));return b.toString();}
    private static boolean hasAny(String x,String...a){for(String s:a)if(x.contains(s))return true;return false;}
    private static String sathiNorm(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]+"," ").trim();}

    private PlacePoint sathiPlace(String q,String x){
        if(hasAny(x,"ktm","kathmandu","काठमाडौं","काठमाण्डौ"))return new PlacePoint("Kathmandu",27.7172,85.3240);
        if(hasAny(x,"pokhara","पोखरा"))return new PlacePoint("Pokhara",28.2096,83.9856);
        if(hasAny(x,"biratnagar","विराटनगर"))return new PlacePoint("Biratnagar",26.4525,87.2718);
        if(hasAny(x,"bharatpur","भरतपुर"))return new PlacePoint("Bharatpur",27.6766,84.4359);
        if(hasAny(x,"butwal","बुटवल"))return new PlacePoint("Butwal",27.7006,83.4484);
        if(hasAny(x,"nepalgunj","नेपालगन्ज","नेपालगञ्ज"))return new PlacePoint("Nepalgunj",28.0500,81.6167);
        if(hasAny(x,"dhangadhi","धनगढी"))return new PlacePoint("Dhangadhi",28.6950,80.5930);
        if(hasAny(x,"janakpur","जनकपुर"))return new PlacePoint("Janakpur",26.7288,85.9250);
        if(hasAny(x,"hetauda","हेटौडा","हेटौँडा"))return new PlacePoint("Hetauda",27.4284,85.0322);
        if(hasAny(x,"dharan","धरान"))return new PlacePoint("Dharan",26.8065,87.2846);
        try{JSONArray fs=districtFeaturesCache;if(fs==null){JSONObject j=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");fs=j.optJSONArray("features");districtFeaturesCache=fs;}if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i),p=f==null?null:f.optJSONObject("properties");String n=p==null?"":p.optString("nameEn","");if(n.length()>2&&x.contains(n.toLowerCase(Locale.ROOT))){double[] c=activityCentroid(f.optJSONObject("geometry"));if(c!=null)return new PlacePoint(n,c[1],c[0]);}}}catch(Exception ignored){}
        return null;
    }
    private static double[] activityCentroid(JSONObject g){try{JSONArray c=g.optJSONArray("coordinates");if(c==null)return null;JSONArray ring;if("Polygon".equals(g.optString("type")))ring=c.optJSONArray(0);else{JSONArray p=c.optJSONArray(0);ring=p==null?null:p.optJSONArray(0);}if(ring==null||ring.length()==0)return null;double sx=0,sy=0;int n=0;for(int i=0;i<ring.length();i++){JSONArray a=ring.optJSONArray(i);if(a!=null){sx+=a.optDouble(0);sy+=a.optDouble(1);n++;}}return n==0?null:new double[]{sx/n,sy/n};}catch(Exception e){return null;}}
    private static final class PlacePoint{final String name;final double lat,lon;PlacePoint(String n,double a,double o){name=n;lat=a;lon=o;}}

    private String answerSathi(String q){String x=sathiNorm(q);String a=answerSathiLocal(q,x);return a==null?t("म app भित्रको मौसम, नदी, risk, Human Status, समाचार वा notification बारे verified data बाट उत्तर दिन्छु 🙂","I answer from verified in-app weather, river risk, Human Status, news and notification data 🙂"):a;}
'''
activity = activity[:start] + brain + activity[end:]

activity_path.write_text(activity, encoding='utf-8')

# ---------------- VERSION ----------------
gradle = gradle.replace('versionCode 23', 'versionCode 24', 1)
gradle = gradle.replace("versionName '0.8.3'", "versionName '0.8.4'", 1)
if 'versionCode 24' not in gradle or "versionName '0.8.4'" not in gradle:
    raise SystemExit('v0.8.4 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index=index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.3</span>','<span class="badge green">v0.8.4</span>')
    index_path.write_text(index,encoding='utf-8')

# Locked markers.
fh=helper_path.read_text(encoding='utf-8');fa=activity_path.read_text(encoding='utf-8')
for m in ['insideDistricts(lo, la, nepalDistricts)','fs-river-labels-layer','textAllowOverlap(true)','lineWidth(6.2f)']:
    if m not in fh: raise SystemExit('v0.8.4 map marker missing: '+m)
if 'fs-nepal-mask-layer' in fh: raise SystemExit('Invalid Nepal overlay mask remained')
for m in ['resolveDistrictName(','askSathi(q,answer,false)','askSathi(q,out,true)','PlacePoint("Kathmandu"','latestNews']:
    if m not in fa: raise SystemExit('v0.8.4 SATHI/district marker missing: '+m)
print('FloodSafe v0.8.4 district names + clipped detailed map + grounded conversational SATHI patch PASS')
