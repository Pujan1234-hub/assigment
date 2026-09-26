from pathlib import Path

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
GRADLE = Path("floodsafe-android-app/app/build.gradle")
s = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")


def repl(old: str, new: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"UI expected exactly one match, got {count}: {old[:180]!r}")
    s = s.replace(old, new, 1)


def replg(old: str, new: str) -> None:
    global g
    count = g.count(old)
    if count != 1:
        raise SystemExit(f"Gradle expected exactly one match, got {count}: {old!r}")
    g = g.replace(old, new, 1)

# Keep all river/map implementation untouched. Weather is added in NativeFullActivity plus a separate
# WeatherMapOverlayController which attaches native MapLibre style layers through the public MapView API.
repl(
    'private LinearLayout content,nearList,nationalList,newsList,humanCard,alarmBanner;',
    'private LinearLayout content,nearList,nationalList,newsList,humanCard,alarmBanner,districtWeatherList;'
)
repl(
    'private TextView newsTitle,newsSub,privacyTitle,privacySub,mapTitle,mapSub,mapHint;',
    'private TextView newsTitle,newsSub,privacyTitle,privacySub,mapTitle,mapSub,mapHint,districtWeatherTitle,districtWeatherSub,districtWeatherFresh,weatherLayerStatus;'
)
repl(
    'private FloodSafeNativeMapView map;',
    'private FloodSafeNativeMapView map;\n    private WeatherMapOverlayController weatherOverlay;\n    private Button districtWeatherMore,weatherLayerButton;'
)
repl(
    'private String currentWeather="";\n    private boolean showAllStations=false;',
    'private String currentWeather="";\n    private final List<DistrictWeather> districtWeatherData=new ArrayList<>();\n    private boolean showAllStations=false,showAllDistrictWeather=false,weatherOverlayEnabled=true;\n    private long districtWeatherAt=0L;'
)

repl(
    'main.post(clockTick);',
    'main.post(clockTick);main.postDelayed(weatherRefreshTick,10L*60L*1000L);'
)

repl(
    'content.addView(hero(),lp(-1,-2,0,0,0,dp(12)));\n        Button locate=',
    'content.addView(hero(),lp(-1,-2,0,0,0,dp(12)));\n        content.addView(districtWeatherCard());\n        Button locate='
)

# Create weather overlay controller against the existing native MapLibre view. The map source is not edited.
repl(
    'FrameLayout holder=new FrameLayout(this);map=new FloodSafeNativeMapView(this, stationObject -> { if(stationObject instanceof RiverStation) showStation((RiverStation)stationObject); });holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));',
    'FrameLayout holder=new FrameLayout(this);map=new FloodSafeNativeMapView(this, stationObject -> { if(stationObject instanceof RiverStation) showStation((RiverStation)stationObject); });weatherOverlay=new WeatherMapOverlayController(map);weatherOverlay.setEnabled(weatherOverlayEnabled);holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));'
)
repl(
    'holder.addView(mapHint,hp);c.addView(holder);\n        zi.setOnClickListener',
    'holder.addView(mapHint,hp);c.addView(holder);\n        LinearLayout weatherRow=new LinearLayout(this);weatherRow.setOrientation(LinearLayout.HORIZONTAL);weatherRow.setGravity(Gravity.CENTER_VERTICAL);weatherLayerStatus=text("",11,true,Color.rgb(84,115,137));weatherLayerButton=smallButton("");weatherRow.addView(weatherLayerStatus,new LinearLayout.LayoutParams(0,-2,1f));weatherRow.addView(weatherLayerButton,new LinearLayout.LayoutParams(dp(128),dp(44)));c.addView(weatherRow,lp(-1,-2,0,dp(8),0,0));weatherLayerButton.setOnClickListener(v->{weatherOverlayEnabled=!weatherOverlayEnabled;if(weatherOverlay!=null)weatherOverlay.setEnabled(weatherOverlayEnabled);updateWeatherLayerUi();});updateWeatherLayerUi();\n        zi.setOnClickListener'
)

# Language refresh adds district/weather controls. The language patch recreates the Activity, so created labels follow t(ne,en).
repl(
    'privacySub.setText(t("Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used."));updateOutsideNotice();}',
    'privacySub.setText(t("Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used."));districtWeatherTitle.setText(t("🌦️ ७७ जिल्ला मौसम","🌦️ Weather across 77 districts"));districtWeatherSub.setText(t("Open-Meteo current model • GPS नजिकको जिल्ला highlight हुन्छ","Open-Meteo current model • nearest district to GPS is highlighted"));updateWeatherLayerUi();updateOutsideNotice();}'
)

repl(
    'private void refreshAll(){restoreLocation();refreshRivers();refreshHuman();refreshNews();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}',
    'private void refreshAll(){restoreLocation();refreshRivers();refreshHuman();refreshNews();refreshDistrictWeather();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);}'
)

repl(
    'reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();FloodMonitorService.startIfEnabled(this);}',
    'reverseGeocode();fetchWeather(lat,lon);renderDistrictWeather();refreshRiverUi();FloodMonitorService.startIfEnabled(this);}'
)

# Upgrade GPS weather to include condition, apparent temperature and cloud cover while preserving the existing hero metrics.
repl(
    'private void fetchWeather(double a,double o){io.execute(()->{try{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),pr=c.optDouble("precipitation",0),hu=c.optDouble("relative_humidity_2m",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);String ws=pr>=.5?t("अहिले वर्षा भइरहेको छ","Rain now"):t("अहिले वर्षा छैन","No rain now");String timing=rainTiming(j);currentWeather=ws;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);});}catch(Exception e){runOnUiThread(()->weatherText.setText(t("मौसम refresh हुन सकेन","Weather refresh failed")));}});}',
    'private void fetchWeather(double a,double o){io.execute(()->{try{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),feels=c.optDouble("apparent_temperature",Double.NaN),pr=c.optDouble("precipitation",0),hu=c.optDouble("relative_humidity_2m",Double.NaN),cloud=c.optDouble("cloud_cover",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);int code=c.optInt("weather_code",-1);String ws=weatherCodeText(code,pr);String timing=rainTiming(j);currentWeather=ws;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);weatherSupport.setText(t("GPS मौसम • महसुस ","GPS weather • feels ")+(Double.isFinite(feels)?Math.round(feels)+"°":"—")+t(" • बादल "," • cloud ")+(Double.isFinite(cloud)?Math.round(cloud)+"%":"—"));rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);});}catch(Exception e){runOnUiThread(()->weatherText.setText(t("मौसम refresh हुन सकेन","Weather refresh failed")));}});}'
)

# Add district weather + live cloud/precipitation model layer implementation before river refresh.
anchor = '    private void refreshRivers(){feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));'
if anchor not in s:
    raise SystemExit("weather insertion anchor missing")
weather_methods = r'''
    private View districtWeatherCard(){
        LinearLayout c=card();districtWeatherTitle=text("",20,true,Color.rgb(16,39,70));districtWeatherSub=text("",12,true,Color.rgb(100,130,151));districtWeatherFresh=text(t("मौसम data लोड हुँदैछ…","Loading weather data…"),11,true,Color.rgb(74,118,146));c.addView(districtWeatherTitle);c.addView(districtWeatherSub);c.addView(districtWeatherFresh,lp(-1,-2,0,dp(4),0,0));districtWeatherList=new LinearLayout(this);districtWeatherList.setOrientation(LinearLayout.VERTICAL);c.addView(districtWeatherList,lp(-1,-2,0,dp(9),0,0));districtWeatherMore=smallButton(t("सबै जिल्ला देखाउनुहोस्","Show all districts"));districtWeatherMore.setOnClickListener(v->{showAllDistrictWeather=!showAllDistrictWeather;districtWeatherMore.setText(showAllDistrictWeather?t("कम देखाउनुहोस्","Show less"):t("सबै जिल्ला देखाउनुहोस्","Show all districts"));renderDistrictWeather();});c.addView(districtWeatherMore);return c;
    }

    private void refreshDistrictWeather(){
        if(districtWeatherFresh!=null)districtWeatherFresh.setText(t("७७ जिल्ला मौसम refresh हुँदैछ…","Refreshing all 77 districts…"));
        io.execute(()->{try{
            List<DistrictPoint> points=loadDistrictPoints();
            if(points.isEmpty())throw new IllegalStateException("district centroids missing");
            StringBuilder la=new StringBuilder(),lo=new StringBuilder();
            for(int i=0;i<points.size();i++){if(i>0){la.append(',');lo.append(',');}la.append(String.format(Locale.US,"%.4f",points.get(i).lat));lo.append(String.format(Locale.US,"%.4f",points.get(i).lon));}
            String u="https://api.open-meteo.com/v1/forecast?latitude="+la+"&longitude="+lo+"&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&timezone=Asia%2FKathmandu&forecast_days=1";
            String raw=getText(u).trim();JSONArray arr;if(raw.startsWith("["))arr=new JSONArray(raw);else{arr=new JSONArray();arr.put(new JSONObject(raw));}
            List<DistrictWeather> out=new ArrayList<>();int n=Math.min(points.size(),arr.length());
            for(int i=0;i<n;i++){JSONObject row=arr.optJSONObject(i);if(row==null)continue;JSONObject cur=row.optJSONObject("current");if(cur==null)continue;DistrictPoint p=points.get(i);out.add(new DistrictWeather(p.name,p.lat,p.lon,cur.optDouble("temperature_2m",Double.NaN),cur.optDouble("apparent_temperature",Double.NaN),cur.optDouble("relative_humidity_2m",Double.NaN),cur.optDouble("precipitation",0),cur.optDouble("wind_speed_10m",Double.NaN),cur.optDouble("cloud_cover",Double.NaN),cur.optInt("weather_code",-1)));}
            out.sort(Comparator.comparing(x->x.name));synchronized(districtWeatherData){districtWeatherData.clear();districtWeatherData.addAll(out);}districtWeatherAt=System.currentTimeMillis();runOnUiThread(this::renderDistrictWeather);
        }catch(Exception e){runOnUiThread(()->{if(districtWeatherFresh!=null)districtWeatherFresh.setText(t("जिल्ला मौसम refresh हुन सकेन","District weather refresh failed"));updateWeatherLayerUi();});}});
    }

    private List<DistrictPoint> loadDistrictPoints()throws Exception{
        JSONObject root;try{root=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");}catch(Exception e){root=assetJson("floodsafe-nepal/v24/nepal-districts.json");}
        JSONArray fs=root.optJSONArray("features");List<DistrictPoint> out=new ArrayList<>();if(fs==null)return out;
        for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i);if(f==null)continue;JSONObject props=f.optJSONObject("properties"),geo=f.optJSONObject("geometry");String name=props==null?"":props.optString("nameEn","").trim();if(name.isEmpty()||geo==null)continue;double[] sum=new double[3];collectCoordinatePairs(geo.optJSONArray("coordinates"),sum);if(sum[2]>0)out.add(new DistrictPoint(name,sum[1]/sum[2],sum[0]/sum[2]));}
        return out;
    }
    private static void collectCoordinatePairs(Object node,double[] sum){if(!(node instanceof JSONArray))return;JSONArray a=(JSONArray)node;if(a.length()>=2&&a.opt(0) instanceof Number&&a.opt(1) instanceof Number){double lo=a.optDouble(0,Double.NaN),la=a.optDouble(1,Double.NaN);if(Double.isFinite(la)&&Double.isFinite(lo)){sum[0]+=lo;sum[1]+=la;sum[2]++;}return;}for(int i=0;i<a.length();i++)collectCoordinatePairs(a.opt(i),sum);}

    private void renderDistrictWeather(){
        if(districtWeatherList==null)return;List<DistrictWeather> copy;synchronized(districtWeatherData){copy=new ArrayList<>(districtWeatherData);}districtWeatherList.removeAllViews();
        if(copy.isEmpty()){districtWeatherList.addView(empty(t("जिल्ला मौसम data आउँदैछ…","District weather data is loading…")));updateWeatherLayerUi();return;}
        DistrictWeather nearest=null;double nd=Double.POSITIVE_INFINITY;if(isNepal(lat,lon)){for(DistrictWeather d:copy){double km=distanceRawKm(lat,lon,d.lat,d.lon);if(km<nd){nd=km;nearest=d;}}}
        int max=showAllDistrictWeather?copy.size():Math.min(12,copy.size());for(int i=0;i<max;i++){DistrictWeather d=copy.get(i);boolean here=d==nearest;String line=(here?"📍 ":"🌦️ ")+d.name+" • "+(Double.isFinite(d.temp)?Math.round(d.temp)+"°":"—")+" • "+weatherCodeText(d.code,d.precip)+"\n"+t("☁ बादल ","☁ cloud ")+(Double.isFinite(d.cloud)?Math.round(d.cloud)+"%":"—")+t(" • वर्षा "," • rain ")+String.format(Locale.US,"%.1f mm",d.precip)+t(" • आर्द्रता "," • humidity ")+(Double.isFinite(d.humidity)?Math.round(d.humidity)+"%":"—");TextView v=text(line,13,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(here?Color.rgb(230,247,255):Color.rgb(248,252,254),16,here?Color.rgb(70,165,216):Color.rgb(216,234,243),here?2:1));v.setOnClickListener(x->showDistrictWeather(d));districtWeatherList.addView(v,lp(-1,-2,0,0,0,dp(7)));}
        if(districtWeatherFresh!=null)districtWeatherFresh.setText(t("Open-Meteo current model • "+copy.size()+" जिल्ला • ","Open-Meteo current model • "+copy.size()+" districts • ")+weatherAge());
        if(weatherOverlay!=null){List<WeatherMapOverlayController.WeatherPoint> overlay=new ArrayList<>();for(DistrictWeather d:copy)overlay.add(new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp));weatherOverlay.update(overlay);weatherOverlay.setEnabled(weatherOverlayEnabled);}updateWeatherLayerUi();
    }

    private void showDistrictWeather(DistrictWeather d){String msg=t("तापक्रम: ","Temperature: ")+(Double.isFinite(d.temp)?Math.round(d.temp)+"°C":"—")+t("\nमहसुस: ","\nFeels like: ")+(Double.isFinite(d.feels)?Math.round(d.feels)+"°C":"—")+t("\nअवस्था: ","\nCondition: ")+weatherCodeText(d.code,d.precip)+t("\nबादल: ","\nCloud cover: ")+(Double.isFinite(d.cloud)?Math.round(d.cloud)+"%":"—")+t("\nवर्षा: ","\nPrecipitation: ")+String.format(Locale.US,"%.1f mm",d.precip)+t("\nआर्द्रता: ","\nHumidity: ")+(Double.isFinite(d.humidity)?Math.round(d.humidity)+"%":"—")+t("\nहावा: ","\nWind: ")+(Double.isFinite(d.wind)?Math.round(d.wind)+" km/h":"—")+"\n\n"+t("स्रोत: Open-Meteo current weather model","Source: Open-Meteo current weather model");new AlertDialog.Builder(this).setTitle("🌦️ "+d.name).setMessage(msg).setPositiveButton("OK",null).show();}

    private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☁ बादल + वर्षा layer ON","☁ Cloud + rain layer ON"):t("☁ मौसम layer OFF","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));}
    private String weatherAge(){if(districtWeatherAt<=0)return t("प्रतीक्षा","waiting");long m=Math.max(0,(System.currentTimeMillis()-districtWeatherAt)/60000L);return m<1?t("अहिले","now"):t(m+" मिनेट अघि",m+" min ago");}
    private String weatherCodeText(int code,double precipitation){if(precipitation>=0.5)return t("वर्षा","Rain");if(code==0)return t("खुला आकाश","Clear");if(code==1||code==2)return t("आंशिक बादल","Partly cloudy");if(code==3)return t("बादल","Cloudy");if(code==45||code==48)return t("कुहिरो","Fog");if(code>=51&&code<=57)return t("सिमसिमे वर्षा","Drizzle");if(code>=61&&code<=67)return t("वर्षा","Rain");if(code>=71&&code<=77)return t("हिउँ","Snow");if(code>=80&&code<=82)return t("वर्षाको झरी","Showers");if(code>=85&&code<=86)return t("हिउँको झरी","Snow showers");if(code>=95&&code<=99)return t("मेघगर्जन","Thunderstorm");return t("मौसम सामान्य","Weather normal");}
    private static double distanceRawKm(double a1,double o1,double a2,double o2){double R=6371,dLat=Math.toRadians(a2-a1),dLon=Math.toRadians(o2-o1),q=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(Math.toRadians(a1))*Math.cos(Math.toRadians(a2))*Math.sin(dLon/2)*Math.sin(dLon/2);return 2*R*Math.asin(Math.min(1,Math.sqrt(q)));}
    private static String getText(String u)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(15000);c.setReadTimeout(25000);c.setUseCaches(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store");int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}finally{c.disconnect();}return b.toString();}

'''
s = s.replace(anchor, weather_methods + anchor, 1)

# Refresh district/weather model every ten minutes while the Activity is alive.
repl(
    'private final Runnable clockTick=new Runnable(){@Override public void run(){try{java.time.ZonedDateTime z=java.time.ZonedDateTime.now(java.time.ZoneId.of("Asia/Kathmandu"));clock.setText(String.format(Locale.US,"%02d:%02d:%02d NPT",z.getHour(),z.getMinute(),z.getSecond()));}catch(Exception ignored){}main.postDelayed(this,1000);}};',
    'private final Runnable weatherRefreshTick=new Runnable(){@Override public void run(){refreshDistrictWeather();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);main.postDelayed(this,10L*60L*1000L);}};\n    private final Runnable clockTick=new Runnable(){@Override public void run(){try{java.time.ZonedDateTime z=java.time.ZonedDateTime.now(java.time.ZoneId.of("Asia/Kathmandu"));clock.setText(String.format(Locale.US,"%02d:%02d:%02d NPT",z.getHour(),z.getMinute(),z.getSecond()));}catch(Exception ignored){}main.postDelayed(this,1000);}};'
)

# Add compact district weather model classes beside existing native DTOs.
repl(
    'private static final class NewsItem{final String title,source,url;final long at;NewsItem(String t,String s,String u,long a){title=t;source=s;url=u;at=a;}}',
    'private static final class DistrictPoint{final String name;final double lat,lon;DistrictPoint(String n,double a,double o){name=n;lat=a;lon=o;}}\n    private static final class DistrictWeather{final String name;final double lat,lon,temp,feels,humidity,precip,wind,cloud;final int code;DistrictWeather(String n,double a,double o,double t,double f,double h,double p,double w,double c,int x){name=n;lat=a;lon=o;temp=t;feels=f;humidity=h;precip=p;wind=w;cloud=c;code=x;}}\n    private static final class NewsItem{final String title,source,url;final long at;NewsItem(String t,String s,String u,long a){title=t;source=s;url=u;at=a;}}'
)

repl(
    '@Override protected void onDestroy(){main.removeCallbacksAndMessages(null);if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}if(tts!=null){tts.stop();tts.shutdown();}io.shutdownNow();super.onDestroy();}',
    '@Override protected void onDestroy(){main.removeCallbacksAndMessages(null);if(weatherOverlay!=null)weatherOverlay.destroy();if(speech!=null){try{speech.destroy();}catch(Exception ignored){}}if(tts!=null){tts.stop();tts.shutdown();}io.shutdownNow();super.onDestroy();}'
)

# Version bump so the field-test APK is distinguishable/installable as a newer build.
replg('versionCode 17', 'versionCode 18')
replg("versionName '0.9.00-native'", "versionName '0.9.01-weather'")

UI.write_text(s, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("WEATHER_COMPLETE_PATCH PASS")
