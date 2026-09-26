#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
JAVA = ROOT / "app/src/main/java/io/github/pujan1234hub/floodsafe/app"
ACT = JAVA / "NativeFullActivity.java"
RAIN = JAVA / "RainAlertWorker.java"
RIVER = JAVA / "RiverAlertWorker.java"
GRADLE = ROOT / "app/build.gradle"


def load(path):
    return path.read_text(encoding="utf-8")


def save(path, text):
    path.write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


def regex_once(text, pattern, replacement, label):
    new, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return new


def language():
    s = load(ACT)
    s = replace_once(s,
        "    private FloodSafeNativeMapView map;\n",
        "    private FloodSafeNativeMapView map;\n"
        "    private FloodSafeEnhancements.DistrictWeatherView districtWeather;\n"
        "    private FloodSafeEnhancements.WeatherOverlayView weatherOverlay;\n"
        "    private int currentWeatherCode=-1,currentCloudCover=0;\n"
        "    private double currentPrecipitation=0d;\n",
        "language fields")

    old_listener = "langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();refreshRiverUi();});"
    new_listener = "langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();refreshRiverUi();if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);});"
    s = replace_once(s, old_listener, new_listener, "language toggle")

    replacements = {
        "नेपालको मौसम + official BIPAD/DHM realtime नदी status": "नेपालको मौसम + BIPAD/DHM को आधिकारिक वास्तविक-समय नदी अवस्था",
        "🇳🇵 official नदी स्टेशन र नदी geometry": "🇳🇵 आधिकारिक नदी स्टेशन र नदीको वास्तविक मार्ग",
        "तपाईंको स्थान नजिकको official नदी अवस्था": "तपाईंको स्थान नजिकको आधिकारिक नदी अवस्था",
        "🌊 ७७ जिल्ला — सबै official नदी स्टेशन": "🌊 ७७ जिल्ला — सबै आधिकारिक नदी स्टेशन",
        "Latest official reading; stale data लाई live खतरा मानिँदैन।": "पछिल्लो आधिकारिक मापन; पुरानो डेटा प्रत्यक्ष खतरा मानिँदैन।",
        "Official नदी अवस्था refresh हुँदैछ…": "आधिकारिक नदी अवस्था अद्यावधिक हुँदैछ…",
        "River data refresh हुन सकेन • stale लाई live भनिएको छैन": "नदीको डेटा अद्यावधिक हुन सकेन • पुरानो डेटा प्रत्यक्ष मानिएको छैन",
        "मौसम data refresh हुँदैछ।": "मौसमको डेटा अद्यावधिक हुँदैछ।",
        "मौसम, नदी, warning वा app status सोध्नुहोस्।": "मौसम, नदी, चेतावनी वा एपको अवस्था सोध्नुहोस्।",
        "Fresh official river status: danger ": "हालको आधिकारिक नदी अवस्था: खतरा ",
        ", warning ": ", चेतावनी ",
        ", alert ": ", निगरानी ",
        "२ घण्टाको weather digest र verified Warning/Danger २ km भित्रको emergency river alert सक्रिय छन्।": "हरेक करिब २ घण्टाको मौसम सारांश र प्रमाणित चेतावनी/खतरा अवस्थाका लागि प्रभावित नदीको करिब २ किमि भित्र आपतकालीन सूचना सक्रिय छन्।",
        "मौसम, नदी, flood warning, location वा notification बारे सोध्नुहोस्।": "मौसम, नदी, बाढी चेतावनी, स्थान वा सूचनाबारे सोध्नुहोस्।",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)

    old_end = "privacySub.setText(t(\"Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।\",\"See how location, microphone and alert data are used.\"));updateOutsideNotice();}"
    new_end = "privacySub.setText(t(\"स्थान, माइक्रोफोन र चेतावनीको डेटा कसरी प्रयोग हुन्छ हेर्नुहोस्।\",\"See how location, microphone and alert data are used.\"));FloodSafeEnhancements.applyLanguageTree(root,english);if(districtWeather!=null)districtWeather.setEnglish(english);updateOutsideNotice();}"
    s = replace_once(s, old_end, new_end, "apply language tail")

    s = s.replace("new Geocoder(this,Locale.getDefault())", "new Geocoder(this,english?Locale.UK:new Locale(\"ne\",\"NP\"))")
    s = s.replace("out.setText(\"तपाईं: \"+q+\"\\n\\nSATHI: \"+a);", "out.setText(t(\"तपाईं: \",\"You: \")+q+\"\\n\\nSATHI: \"+a);")
    s = s.replace(".setPositiveButton(\"OK\",null)", ".setPositiveButton(t(\"ठीक छ\",\"OK\"),null)")

    station_method = '''    private String stationLine(RiverStation s){
        long ageMs=s.at>0?Math.max(0,System.currentTimeMillis()-s.at):-1L;
        String age;
        if(ageMs<0)age=t("आधिकारिक समय उपलब्ध छैन","official time unavailable");
        else if(ageMs<60L*60L*1000L)age=(ageMs/60000L)+t(" मिनेट अघि"," min ago");
        else if(ageMs<48L*60L*60L*1000L)age=(ageMs/(60L*60L*1000L))+t(" घण्टा अघि"," hr ago");
        else age=(ageMs/(24L*60L*60L*1000L))+t(" दिन अघि"," days ago");
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("तह —","level —");
        double d=distanceKm(s.lat,s.lon);
        String freshness=s.fresh?t("हालको आधिकारिक","CURRENT official"):t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात","HISTORICAL / STALE • last known");
        return freshness+" • "+lev+" • "+age+(Double.isFinite(d)?t(" • स्टेशन "," • station ")+String.format(Locale.US,"%.1f km",d):"");
    }
    private void showStation'''
    s = regex_once(s, r"    private String stationLine\(RiverStation s\)\{.*?\n    \}\n    private void showStation", station_method, "station line")

    show_station = '''    private void showStation(RiverStation s){
        StringBuilder b=new StringBuilder();
        b.append(s.fresh?stageDot(s.stage)+" "+stageName(s.stage):"⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात मापन","HISTORICAL / STALE • last known reading"));
        if(!s.stationId.isEmpty())b.append("\\n").append(t("स्टेशन ID: ","Station ID: ")).append(s.stationId);
        if(!s.riverName.isEmpty())b.append("\\n").append(t("नदी/खोला: ","River: ")).append(s.riverName);
        b.append("\\n\\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
        b.append("\\n").append(t("आधिकारिक मापन समय: ","Official observation: ")).append(s.at>0?Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime():"—");
        if(!s.fresh)b.append("\\n\\n").append(t("यो पुरानो/ऐतिहासिक मापन चेतावनीको रङ वा अलार्ममा प्रयोग हुँदैन।","This historical/stale reading is not used for warning colours or alarms."));
        String rainDetail=DhmRainMirror.detailFor(s.name,s.district,s.lat,s.lon);
        b.append("\\n\\n").append(rainDetail!=null?rainDetail:t("वर्षा: सुरक्षित रूपमा मिलेको हालको DHM वर्षा मापन उपलब्ध छैन।","Rainfall: no safely matched fresh DHM rainfall reading is available."));
        b.append("\\n\\n").append(t("स्रोत: BIPAD / DHM","Source: BIPAD / DHM"));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0903_COMPLETE_STATION_LANGUAGE


    private void refreshHuman'''
    s = regex_once(s, r"    private void showStation\(RiverStation s\)\{.*?\} // V0899_STATION_STALE_AND_RAIN_DETAIL\n\n\n    private void refreshHuman", show_station, "station dialog")

    save(ACT, s)
    print("V0903 language patch PASS")


def gps_weather():
    s = load(ACT)
    new_method = '''    private void fetchWeather(double a,double o){
        io.execute(()->{try{
            String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&hourly=precipitation_probability,precipitation,weather_code,cloud_cover&forecast_hours=10&timezone=auto",a,o);
            JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");
            double te=c.optDouble("temperature_2m",Double.NaN),pr=Math.max(0d,c.optDouble("precipitation",0)),hu=c.optDouble("relative_humidity_2m",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);
            int code=c.optInt("weather_code",-1),cloud=c.optInt("cloud_cover",0);
            currentWeatherCode=code;currentCloudCover=cloud;currentPrecipitation=pr;
            String ws=FloodSafeEnhancements.weatherCondition(code,pr,english);String timing=rainTiming(j);currentWeather=ws;
            runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);if(weatherOverlay!=null)weatherOverlay.updateWeather(code,pr,cloud);});
        }catch(Exception e){runOnUiThread(()->weatherText.setText(t("मौसम अद्यावधिक हुन सकेन","Weather refresh failed")));}});
    }
    private String rainTiming'''
    s = regex_once(s, r"    private void fetchWeather\(double a,double o\)\{.*?\n    private String rainTiming", new_method, "gps weather")
    save(ACT, s)
    print("V0903 GPS weather patch PASS")


def district_weather():
    s = load(ACT)
    old = "        content.addView(hero(),lp(-1,-2,0,0,0,dp(12)));\n"
    new = old + "        districtWeather=new FloodSafeEnhancements.DistrictWeatherView(this,english);content.addView(districtWeather,lp(-1,-2,0,0,0,dp(12)));\n"
    s = replace_once(s, old, new, "district weather card")
    save(ACT, s)
    print("V0903 district weather patch PASS")


def weather_overlay():
    s = load(ACT)
    old = "holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));mapHint="
    new = "holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));weatherOverlay=new FloodSafeEnhancements.WeatherOverlayView(this);holder.addView(weatherOverlay,new FrameLayout.LayoutParams(-1,dp(370)));weatherOverlay.updateWeather(currentWeatherCode,currentPrecipitation,currentCloudCover);mapHint="
    s = replace_once(s, old, new, "weather overlay")
    save(ACT, s)
    print("V0903 weather overlay patch PASS")


def weather_notifications():
    s = load(RAIN)
    s = s.replace("smart current-location weather digest roughly every 3 hours", "smart current-location weather digest roughly every 2 hours")
    s = s.replace("private static final long WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L;", "private static final long WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L;")
    s = s.replace("relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m", "relative_humidity_2m,precipitation,rain,showers,weather_code,cloud_cover,wind_speed_10m")
    old = "            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode);"
    new = "            FloodSafeEnhancements.processWeatherNotifications(app, data, prefs, now, temperature, apparent, humidity, wind, weatherCode, current);"
    s = replace_once(s, old, new, "weather notification engine")
    s = regex_once(s,
        r"\n\s*notifyRain\(rainingNow, lead, event, nextHour, temperature, humidity, wind, zone\);",
        "\n            // V0903 rain start/stop/intensity notifications are handled once by FloodSafeEnhancements above.",
        "disable duplicate rain notifier")
    save(RAIN, s)
    print("V0903 two-hour + rain-change notification patch PASS")


def flood_alerts():
    s = load(RIVER)
    method = '''    private void notifyHazard(Hazard hazard) {
        int requestCode = 7200 + Math.abs(hazard.stationId.hashCode() % 500);
        FloodSafeEnhancements.notifyFloodHazard(getApplicationContext(), hazard.stage,
                hazard.stationName, hazard.riverName, hazard.distanceKm, hazard.level,
                hazard.warning, hazard.danger, hazard.measuredAt, requestCode);
    }

    private static double firstNumber'''
    s = regex_once(s, r"    private void notifyHazard\(Hazard hazard\) \{.*?\n    \}\n\n    private static double firstNumber", method, "flood alert channels")
    save(RIVER, s)
    print("V0903 Warning/Danger notification patch PASS")


def version():
    s = load(GRADLE)
    s = re.sub(r"versionCode\s+\d+", "versionCode 18", s, count=1)
    s = re.sub(r"versionName\s+'[^']+'", "versionName '0.9.03-native'", s, count=1)
    save(GRADLE, s)
    print("V0903 version patch PASS")


MODES = {
    "language": language,
    "gps-weather": gps_weather,
    "district-weather": district_weather,
    "weather-overlay": weather_overlay,
    "weather-notifications": weather_notifications,
    "flood-alerts": flood_alerts,
    "version": version,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in MODES:
        raise SystemExit("usage: patch_v0903_language_weather_safety.py " + "|".join(MODES))
    MODES[sys.argv[1]]()
