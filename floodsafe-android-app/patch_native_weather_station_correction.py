from pathlib import Path
import re

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
GRADLE = Path("floodsafe-android-app/app/build.gradle")
s = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {n}")
    s = s.replace(old, new, 1)


def sub_once(pattern: str, new: str, label: str) -> None:
    global s
    s2, n = re.subn(pattern, new, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {n}")
    s = s2


# CORRECTION 1: district weather remains a data model for the map overlay only.
# Remove the long 77-district card from the home screen.
replace_once(
    '        content.addView(districtWeatherCard());\n',
    '',
    'remove district list card'
)

# The labels belonged only to the removed card. Keep language refresh safe when those views are not created.
replace_once(
    'districtWeatherTitle.setText(t("🌦️ ७७ जिल्ला मौसम","🌦️ Weather across 77 districts"));districtWeatherSub.setText(t("Open-Meteo current model • GPS नजिकको जिल्ला highlight हुन्छ","Open-Meteo current model • nearest district to GPS is highlighted"));',
    '',
    'remove district list language labels'
)

# If any residual path asks the old renderer to run, feed the weather layer instead of returning early.
replace_once(
    'if(districtWeatherList==null)return;List<DistrictWeather> copy;',
    'if(districtWeatherList==null){updateWeatherOverlayOnly();return;}List<DistrictWeather> copy;',
    'redirect hidden district renderer'
)

# Add a dedicated map-only updater. This never changes river/station/map implementation code.
anchor = '    private void showDistrictWeather(DistrictWeather d){'
if anchor not in s:
    raise SystemExit('weather overlay insertion anchor missing')
map_only = r'''    private void updateWeatherOverlayOnly(){
        List<DistrictWeather> copy;
        synchronized(districtWeatherData){copy=new ArrayList<>(districtWeatherData);}
        if(weatherOverlay!=null){
            List<WeatherMapOverlayController.WeatherPoint> overlay=new ArrayList<>();
            for(DistrictWeather d:copy){
                overlay.add(new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp));
            }
            weatherOverlay.update(overlay);
            weatherOverlay.setEnabled(weatherOverlayEnabled);
        }
        updateWeatherLayerUi();
    }

'''
s = s.replace(anchor, map_only + anchor, 1)

# Successful 77-district fetch updates the map layer directly. No district rows are rendered.
replace_once(
    'runOnUiThread(this::renderDistrictWeather);',
    'runOnUiThread(this::updateWeatherOverlayOnly);',
    'district fetch map-only callback'
)
replace_once(
    'reverseGeocode();fetchWeather(lat,lon);renderDistrictWeather();refreshRiverUi();FloodMonitorService.startIfEnabled(this);}',
    'reverseGeocode();fetchWeather(lat,lon);updateWeatherOverlayOnly();refreshRiverUi();FloodMonitorService.startIfEnabled(this);}',
    'GPS map-only weather refresh'
)

# CORRECTION 2: restore the intended official station truth chain already present in the project.
# BIPAD direct latest observations are primary; the existing mirror remains the station inventory/fallback.
station_block = r'''    private void refreshRivers(){
        feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));
        io.execute(()->{try{
            OfficialRiverData.Snapshot snapshot=OfficialRiverData.fetch();
            JSONArray rows=snapshot.rows;
            List<RiverStation> out=new ArrayList<>();
            long now=System.currentTimeMillis();
            for(int i=0;i<rows.length();i++){
                RiverStation station=parseStation(rows.optJSONObject(i),now);
                if(station!=null)out.add(station);
            }
            out.sort(Comparator.comparingInt((RiverStation x)->x.rank).thenComparingDouble(x->distanceKm(x.lat,x.lon)));
            synchronized(stations){stations.clear();stations.addAll(out);}
            runOnUiThread(this::refreshRiverUi);
        }catch(Exception e){
            runOnUiThread(()->feedFresh.setText(t("Official river refresh हुन सकेन • पुरानो data लाई live मानिएको छैन","Official river refresh failed • stale data is not treated as live")));
        }});
    }

    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;
        double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","_lastWaterLevel"),
                warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),
                danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=OfficialRiverData.observationTime(r);
        boolean fresh=OfficialRiverData.isCurrent(at,now);
        String stage=OfficialRiverData.stage(r,fresh);
        int rank=OfficialRiverData.rank(stage);
        String stationId=str(r,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","seriesId","series_id","id");
        String riverName=str(r,"river_name","riverName","river");
        String name=str(r,"station_name","stationName","title","name");
        if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";
        String district=str(r,"districtName","district_name","district");
        return new RiverStation(stationId,name,riverName,district,a,o,level,warning,danger,at,fresh,stage,rank);
    } // V0902_DIRECT_BIPAD_TRUTH_CHAIN
'''
sub_once(
    r'    private void refreshRivers\(\)\{.*?    \} // V0899_STALE_CURRENT_SEMANTICS\n',
    station_block,
    'restore official river truth chain'
)

# Distinguish this corrected field build from the rejected list-based weather build.
if "versionCode 18" not in g or "versionName '0.9.01-weather'" not in g:
    raise SystemExit('expected v0.9.01 weather version markers missing')
g = g.replace('versionCode 18', 'versionCode 19', 1)
g = g.replace("versionName '0.9.01-weather'", "versionName '0.9.02-map-weather-station-fix'", 1)

# Build-time invariants.
assert 'OfficialRiverData.fetch()' in s
assert 'V0902_DIRECT_BIPAD_TRUTH_CHAIN' in s
assert 'content.addView(districtWeatherCard());' not in s
assert 'updateWeatherOverlayOnly()' in s
assert 'WeatherMapOverlayController weatherOverlay' in s
assert 'android.webkit.WebView' not in s

UI.write_text(s, encoding='utf-8')
GRADLE.write_text(g, encoding='utf-8')
print('CORRECTED_MAP_WEATHER_AND_STATION_TRUTH_PATCH_OK')
