from pathlib import Path
import re

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
GRADLE = Path("floodsafe-android-app/app/build.gradle")
s = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

def replace_once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f"{label}: expected exactly one match, got {n}")
    s=s.replace(old,new,1)

def sub_once(pattern,new,label):
    global s
    s2,n=re.subn(pattern,new,s,count=1,flags=re.S)
    if n!=1: raise SystemExit(f"{label}: expected exactly one regex match, got {n}")
    s=s2

replace_once('        content.addView(districtWeatherCard());\n','', 'remove district list card')
replace_once('districtWeatherTitle.setText(t("🌦️ ७७ जिल्ला मौसम","🌦️ Weather across 77 districts"));districtWeatherSub.setText(t("Open-Meteo current model • GPS नजिकको जिल्ला highlight हुन्छ","Open-Meteo current model • nearest district to GPS is highlighted"));','', 'remove district list labels')
replace_once('if(districtWeatherList==null)return;List<DistrictWeather> copy;','if(districtWeatherList==null){updateWeatherOverlayOnly();return;}List<DistrictWeather> copy;', 'redirect hidden district renderer')

anchor='    private void showDistrictWeather(DistrictWeather d){'
if anchor not in s: raise SystemExit('weather insertion anchor missing')
map_only=r'''    private void updateWeatherOverlayOnly(){
        List<DistrictWeather> copy;
        synchronized(districtWeatherData){copy=new ArrayList<>(districtWeatherData);}
        if(weatherOverlay!=null){
            List<WeatherMapOverlayController.WeatherPoint> overlay=new ArrayList<>();
            for(DistrictWeather d:copy)overlay.add(new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp));
            weatherOverlay.update(overlay);weatherOverlay.setEnabled(weatherOverlayEnabled);
        }
        updateWeatherLayerUi();
    }

'''
s=s.replace(anchor,map_only+anchor,1)
replace_once('runOnUiThread(this::renderDistrictWeather);','runOnUiThread(this::updateWeatherOverlayOnly);','district fetch map-only callback')
replace_once('reverseGeocode();fetchWeather(lat,lon);renderDistrictWeather();refreshRiverUi();FloodMonitorService.startIfEnabled(this);}','reverseGeocode();fetchWeather(lat,lon);updateWeatherOverlayOnly();refreshRiverUi();FloodMonitorService.startIfEnabled(this);}','GPS map-only weather refresh')

old_weather='    private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☁ बादल + वर्षा layer ON","☁ Cloud + rain layer ON"):t("☁ मौसम layer OFF","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));}'
new_weather='    private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☀ सफा • ☁ खैरो/गाढा = बादल • 🌧 निलो = वर्षा","☀ clear • ☁ grey/dark = cloud • 🌧 blue = rain"):t("☁ मौसम तह बन्द","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));} // V0904_WEATHER_AREA_LEGEND'
replace_once(old_weather,new_weather,'weather area legend')

station_block=r'''    private void refreshRivers(){
        feedFresh.setText(t("BIPAD River watch refresh हुँदैछ…","Refreshing BIPAD River watch…"));
        io.execute(()->{try{
            JSONArray rows=BipadRealtimeStationFeed.fetch();List<RiverStation> out=new ArrayList<>();long now=System.currentTimeMillis();
            for(int i=0;i<rows.length();i++){RiverStation station=parseStation(rows.optJSONObject(i),now);if(station!=null)out.add(station);}
            out.sort(Comparator.comparingInt((RiverStation x)->x.rank).thenComparingDouble(x->distanceKm(x.lat,x.lon)));
            synchronized(stations){stations.clear();stations.addAll(out);}runOnUiThread(this::refreshRiverUi);
        }catch(Exception e){runOnUiThread(()->feedFresh.setText(t("BIPAD River watch refresh हुन सकेन • stale लाई live मानिएको छैन","BIPAD River watch refresh failed • stale data is not live")));}});
    }

    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;
        double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","_lastWaterLevel"),warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=OfficialRiverData.observationTime(r);boolean fresh=OfficialRiverData.isCurrent(at,now);String stage=OfficialRiverData.stage(r,fresh);int rank=OfficialRiverData.rank(stage);
        String stationId=str(r,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","seriesId","series_id","id");
        String riverName=str(r,"river_name","riverName","river","_floodsafeRiverName");String name=str(r,"station_name","stationName","title","name");if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";String district=str(r,"districtName","district_name","district");
        return new RiverStation(stationId,name,riverName,district,a,o,level,warning,danger,at,fresh,stage,rank);
    } // V0904_BIPAD_RIVER_WATCH_FEED
'''
sub_once(r'    private void refreshRivers\(\)\{.*?    \} // V0899_STALE_CURRENT_SEMANTICS\n',station_block,'restore BIPAD River watch feed')

if "versionCode 18" not in g or "versionName '0.9.01-weather'" not in g: raise SystemExit('base version markers missing')
g=g.replace('versionCode 18','versionCode 21',1)
g=g.replace("versionName '0.9.01-weather'","versionName '0.9.04-river-watch-cloud-area'",1)

assert 'BipadRealtimeStationFeed.fetch()' in s
assert 'V0904_BIPAD_RIVER_WATCH_FEED' in s
assert 'V0904_WEATHER_AREA_LEGEND' in s
assert 'content.addView(districtWeatherCard());' not in s
assert 'android.webkit.WebView' not in s
UI.write_text(s,encoding='utf-8');GRADLE.write_text(g,encoding='utf-8')
print('V0904_RIVER_WATCH_CLOUD_AREA_PATCH_OK')
