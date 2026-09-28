#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ACT = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s = ACT.read_text(encoding='utf-8')

field_old = '    private FloodSafeNativeMapView map;\n'
field_new = ('    private FloodSafeNativeMapView map;\n'
             '    private WeatherAnimationOverlayV0918 weatherAnimation;\n'
             '    private int currentWeatherCode=-1,currentCloudCover=0;\n'
             '    private double currentPrecipitation=0d;\n')
if 'WeatherAnimationOverlayV0918 weatherAnimation' not in s:
    if field_old not in s:
        raise SystemExit('weather field anchor missing')
    s = s.replace(field_old, field_new, 1)

holder_old = 'holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));mapHint='
holder_new = ('holder.addView(map,new FrameLayout.LayoutParams(-1,dp(370)));'
              'weatherAnimation=new WeatherAnimationOverlayV0918(this);'
              'holder.addView(weatherAnimation,new FrameLayout.LayoutParams(-1,dp(370)));'
              'weatherAnimation.updateWeather(currentWeatherCode,currentPrecipitation,currentCloudCover);mapHint=')
if 'weatherAnimation=new WeatherAnimationOverlayV0918(this)' not in s:
    if holder_old not in s:
        raise SystemExit('map holder anchor missing')
    s = s.replace(holder_old, holder_new, 1)

replacement = '''    private void fetchWeather(double a,double o){io.execute(()->{try{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m&hourly=precipitation_probability,precipitation&forecast_hours=6&timezone=auto",a,o);JSONObject j=getJson(u);JSONObject c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),pr=c.optDouble("precipitation",0),hu=c.optDouble("relative_humidity_2m",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);int code=c.optInt("weather_code",-1),cloud=c.optInt("cloud_cover",0);currentWeatherCode=code;currentCloudCover=cloud;currentPrecipitation=Math.max(0d,pr);String ws=pr>=.5?t("अहिले वर्षा भइरहेको छ","Rain now"):t("अहिले वर्षा छैन","No rain now");String timing=rainTiming(j);currentWeather=ws;runOnUiThread(()->{temp.setText(Double.isFinite(te)?Math.round(te)+"°":"—°");weatherText.setText(ws);rain.setText(String.format(Locale.US,"%.1f mm",pr));humidity.setText(Double.isFinite(hu)?Math.round(hu)+"%":"—");wind.setText(Double.isFinite(wi)?Math.round(wi)+" km/h":"—");rainTiming.setText(timing);if(weatherAnimation!=null)weatherAnimation.updateWeather(code,pr,cloud);});}catch(Exception e){runOnUiThread(()->weatherText.setText(t("मौसम refresh हुन सकेन","Weather refresh failed")));}});}'''

if 'current=temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m' not in s:
    pat = re.compile(r'    private void fetchWeather\(double a,double o\)\{.*?(?=    private String rainTiming)', re.S)
    s2, n = pat.subn(replacement + '\n', s, count=1)
    if n != 1:
        raise SystemExit('fetchWeather v0.8.18 method missing')
    s = s2

ACT.write_text(s, encoding='utf-8')

for marker in [
    'WeatherAnimationOverlayV0918 weatherAnimation',
    'weatherAnimation=new WeatherAnimationOverlayV0918(this)',
    'weather_code,cloud_cover',
    'weatherAnimation.updateWeather(code,pr,cloud)'
]:
    if marker not in s:
        raise SystemExit('missing weather restore marker: '+marker)
print('PASS: restored cloud/rain/thunder animation without touching map implementation')
