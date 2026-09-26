from pathlib import Path
import re

JAVA = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app")
UI = JAVA / "NativeFullActivity.java"
OVERLAY = JAVA / "WeatherMapOverlayController.java"
RAIN = JAVA / "RainAlertWorker.java"
GRADLE = Path("floodsafe-android-app/app/build.gradle")

ui = UI.read_text(encoding="utf-8")
overlay = OVERLAY.read_text(encoding="utf-8")
rain = RAIN.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

# ---------------- UI: pass current WMO weather code to the map overlay ----------------
old_ctor = 'new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp)'
count = ui.count(old_ctor)
if count != 2:
    raise SystemExit(f"WeatherPoint UI constructor expected 2 matches, got {count}")
ui = ui.replace(old_ctor, 'new WeatherMapOverlayController.WeatherPoint(d.name,d.lat,d.lon,d.cloud,d.precip,d.temp,d.code)')

old_legend = 'private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☀ सफा • ☁ बादल क्षेत्र • 🌧 चलिरहेको वर्षा animation","☀ clear • ☁ cloud field • 🌧 animated rain"):t("☁ मौसम तह बन्द","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));} // V0906_ADVANCED_RAIN_LEGEND'
new_legend = 'private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☀ सफा • ☁ बादल • 🌧 वर्षा • ⚡ current storm effect","☀ clear • ☁ cloud • 🌧 rain • ⚡ current storm effect"):t("☁ मौसम तह बन्द","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));} // V0908_STORM_LEGEND'
if old_legend not in ui:
    raise SystemExit("v0906 weather legend anchor missing")
ui = ui.replace(old_legend, new_legend, 1)

refresh_count = ui.count('10L*60L*1000L')
if refresh_count != 2:
    raise SystemExit(f"foreground weather refresh expected 2 x 10min anchors, got {refresh_count}")
ui = ui.replace('10L*60L*1000L', '5L*60L*1000L')

# ---------------- Map weather overlay: current thunderstorm area + flashing lightning ----------------
old_wp = '''        final String district;\n        final double lat, lon, cloud, precipitation, temperature;\n        WeatherPoint(String district, double lat, double lon, double cloud, double precipitation, double temperature) {\n            this.district = district == null ? "" : district;\n            this.lat = lat;\n            this.lon = lon;\n            this.cloud = cloud;\n            this.precipitation = precipitation;\n            this.temperature = temperature;\n        }'''
new_wp = '''        final String district;\n        final double lat, lon, cloud, precipitation, temperature;\n        final int weatherCode;\n        WeatherPoint(String district, double lat, double lon, double cloud, double precipitation, double temperature, int weatherCode) {\n            this.district = district == null ? "" : district;\n            this.lat = lat;\n            this.lon = lon;\n            this.cloud = cloud;\n            this.precipitation = precipitation;\n            this.temperature = temperature;\n            this.weatherCode = weatherCode;\n        }'''
if old_wp not in overlay:
    raise SystemExit("WeatherPoint class anchor missing")
overlay = overlay.replace(old_wp, new_wp, 1)

overlay = overlay.replace(
    '    private static final String SRC_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy";',
    '    private static final String SRC_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy";\n    private static final String SRC_STORM = "fs-weather-storm-current";\n    private static final String SRC_LIGHTNING = "fs-weather-lightning-current";', 1)
overlay = overlay.replace(
    '    private static final String LYR_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy-layer";',
    '    private static final String LYR_RAIN_STREAK_HEAVY = "fs-weather-rain-streak-heavy-layer";\n    private static final String LYR_STORM = "fs-weather-storm-current-layer";\n    private static final String LYR_LIGHTNING = "fs-weather-lightning-current-layer";', 1)

old_ensure = '                ensureRainLine(style, SRC_RAIN_STREAK_HEAVY, LYR_RAIN_STREAK_HEAVY, "#d8f3ff", 2.05f, 0.72f);'
new_ensure = old_ensure + '\n                ensureFill(style, SRC_STORM, LYR_STORM, "#4d4163", 0.15f);\n                ensureRainLine(style, SRC_LIGHTNING, LYR_LIGHTNING, "#fff3a6", 2.6f, 0.96f);'
if old_ensure not in overlay:
    raise SystemExit("overlay layer install anchor missing")
overlay = overlay.replace(old_ensure, new_ensure, 1)

old_refresh_geo = '                setGeo(style, SRC_RAIN, polygonBucket(snapshot, 0d, 101d, true));\n                applyPulse();\n                updateRainFrames();'
new_refresh_geo = '                setGeo(style, SRC_RAIN, polygonBucket(snapshot, 0d, 101d, true));\n                setGeo(style, SRC_STORM, stormPolygons(snapshot));\n                applyPulse();\n                updateRainFrames();'
if old_refresh_geo not in overlay:
    raise SystemExit("overlay geo refresh anchor missing")
overlay = overlay.replace(old_refresh_geo, new_refresh_geo, 1)

overlay = overlay.replace(
    '        setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);',
    '        setGeo(style, SRC_RAIN_STREAK_HEAVY, EMPTY);\n        setGeo(style, SRC_STORM, EMPTY);\n        setGeo(style, SRC_LIGHTNING, EMPTY);', 1)

overlay = overlay.replace(
    '            if (style.getLayer(LYR_RAIN) != null) style.getLayer(LYR_RAIN).setProperties(fillOpacity(enabled ? 0.16f + d : 0f));',
    '            if (style.getLayer(LYR_RAIN) != null) style.getLayer(LYR_RAIN).setProperties(fillOpacity(enabled ? 0.16f + d : 0f));\n            if (style.getLayer(LYR_STORM) != null) style.getLayer(LYR_STORM).setProperties(fillOpacity(enabled ? (pulseHigh ? 0.20f : 0.11f) : 0f));', 1)

old_frame_tail = '            setGeo(style, SRC_RAIN_STREAK_LIGHT, rainStreaks(snapshot, false, phase));\n            setGeo(style, SRC_RAIN_STREAK_HEAVY, rainStreaks(snapshot, true, phase));'
new_frame_tail = old_frame_tail + '\n            setGeo(style, SRC_LIGHTNING, lightningBolts(snapshot));'
if old_frame_tail not in overlay:
    raise SystemExit("rain frame tail anchor missing")
overlay = overlay.replace(old_frame_tail, new_frame_tail, 1)

storm_methods = r'''
    private String stormPolygons(List<WeatherPoint> weather) {
        try {
            Map<String, WeatherPoint> byDistrict = new HashMap<>();
            for (WeatherPoint p : weather) if (p != null) byDistrict.put(key(p.district), p);
            JSONArray sourceFeatures = districtGeometry == null ? null : districtGeometry.optJSONArray("features");
            JSONArray selected = new JSONArray();
            if (sourceFeatures != null) {
                for (int i = 0; i < sourceFeatures.length(); i++) {
                    JSONObject f = sourceFeatures.optJSONObject(i); if (f == null) continue;
                    JSONObject props = f.optJSONObject("properties");
                    String name = props == null ? "" : props.optString("nameEn", "");
                    WeatherPoint p = byDistrict.get(key(name));
                    if (p == null || p.weatherCode < 95 || p.weatherCode > 99) continue;
                    JSONObject copy = new JSONObject(f.toString());
                    JSONObject cp = copy.optJSONObject("properties");
                    if (cp == null) { cp = new JSONObject(); copy.put("properties", cp); }
                    cp.put("weatherCode", p.weatherCode); cp.put("precipitation", p.precipitation);
                    selected.put(copy);
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", selected).toString();
        } catch (Exception e) { return EMPTY; }
    }

    private String lightningBolts(List<WeatherPoint> weather) {
        try {
            // Short flashes, not a constant yellow line. Data presence is driven only by
            // current WMO thunderstorm codes 95-99 from the weather model.
            long frame = (System.currentTimeMillis() / RAIN_FRAME_MS) % 14L;
            if (frame > 2L) return EMPTY;
            JSONArray features = new JSONArray();
            for (WeatherPoint p : weather) {
                if (p == null || p.weatherCode < 95 || p.weatherCode > 99 || !Double.isFinite(p.lat) || !Double.isFinite(p.lon)) continue;
                int bolts = p.precipitation >= 2.0d ? 3 : 2;
                for (int i = 0; i < bolts; i++) {
                    long h = ((long)p.district.hashCode() * 1103515245L) + i * 2654435761L;
                    double rx = ((h & 0x7fffffffL) % 1000L) / 999.0d - 0.5d;
                    double ry = (((h >>> 11) & 1023L) / 1023.0d) - 0.5d;
                    double lo = p.lon + rx * 0.34d;
                    double la = p.lat + ry * 0.22d + 0.075d;
                    JSONArray coords = new JSONArray()
                            .put(new JSONArray().put(lo).put(la))
                            .put(new JSONArray().put(lo + 0.018d).put(la - 0.035d))
                            .put(new JSONArray().put(lo - 0.004d).put(la - 0.070d))
                            .put(new JSONArray().put(lo + 0.014d).put(la - 0.112d));
                    JSONObject geom = new JSONObject().put("type", "LineString").put("coordinates", coords);
                    JSONObject props = new JSONObject().put("district", p.district).put("weatherCode", p.weatherCode);
                    features.put(new JSONObject().put("type", "Feature").put("geometry", geom).put("properties", props));
                }
            }
            return new JSONObject().put("type", "FeatureCollection").put("features", features).toString();
        } catch (Exception e) { return EMPTY; }
    }

'''
anchor = '    private String polygonBucket(List<WeatherPoint> weather, double minCloud, double maxCloud, boolean rainOnly) {'
if anchor not in overlay:
    raise SystemExit("storm method insertion anchor missing")
overlay = overlay.replace(anchor, storm_methods + anchor, 1)
overlay = overlay.replace('WEATHER_OVERLAY_V4_ANIMATED_RAIN_FIELD', 'WEATHER_OVERLAY_V5_RAIN_THUNDER_FIELD', 1)

# ---------------- Background weather: ~2h digest + rain-stop + thunder event notifications ----------------
rain = rain.replace('smart current-location weather digest roughly every 3 hours', 'smart current-location weather digest roughly every 2 hours', 1)
rain = rain.replace('private static final long WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L;', 'private static final long WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L;', 1)
rain = rain.replace('    private static final String WEATHER_CHANNEL_ID = "smart_weather_updates_v1";', '    private static final String WEATHER_CHANNEL_ID = "smart_weather_updates_v1";\n    private static final String EVENT_CHANNEL_ID = "smart_weather_events_v1";', 1)
rain = rain.replace('                + "&forecast_days=2&timezone=auto";', '                + "&forecast_days=2&past_hours=2&timezone=auto";', 1)

old_now_block = '''            ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));\n            ZonedDateTime now = ZonedDateTime.now(zone);\n\n            // This is deliberately independent from Nepal. If the user is in the UK,\n            // current-location weather notifications still work. Only river alerts are Nepal-only.\n            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode);\n\n            RainEvent event = findEvent(data.optJSONObject("minutely_15"), now);\n            boolean rainingNow = current >= WET_MM || (event != null && event.activeNow);'''
new_now_block = '''            ZoneId zone = safeZone(data.optString("timezone", "Asia/Kathmandu"));\n            ZonedDateTime now = ZonedDateTime.now(zone);\n            ShortForecast eventForecast = shortForecast(data.optJSONObject("hourly"), now);\n\n            // Weather-event notifications run from WorkManager even when the Activity is closed.\n            // They remain model/forecast notifications; official river Warning/Danger logic is separate.\n            maybeNotifyThunderEvent(prefs, now, weatherCode, eventForecast, temperature, current);\n            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode, current);\n\n            RainEvent event = findEvent(data.optJSONObject("minutely_15"), now);\n            boolean rainingNow = current >= WET_MM || (event != null && event.activeNow);\n            boolean rainStateKnown = prefs.contains("last_raining_state");\n            boolean wasRaining = prefs.getBoolean("last_raining_state", false);\n            if (rainStateKnown && wasRaining && !rainingNow) {\n                notifyWeatherEvent(7111, "🌤️ वर्षा रोकिएको देखिन्छ",\n                        "हालको weather model मा वर्षा रोकिएको छ • अहिले " + oneDecimal(current) + " mm।");\n            }\n            prefs.edit().putBoolean("last_raining_state", rainingNow).apply();'''
if old_now_block not in rain:
    raise SystemExit("RainAlertWorker current block anchor missing")
rain = rain.replace(old_now_block, new_now_block, 1)

rain = rain.replace(
    '    private static final class ShortForecast {\n        double temperature3h = Double.NaN;\n        double precipitationMm = 0d;\n        int precipitationProbability = -1;\n    }',
    '    private static final class ShortForecast {\n        double temperature3h = Double.NaN;\n        double precipitationMm = 0d;\n        int precipitationProbability = -1;\n        boolean thunderRisk = false;\n    }', 1)

rain = rain.replace(
    '                                          double apparent, double humidity, double wind,\n                                          int weatherCode) {',
    '                                          double apparent, double humidity, double wind,\n                                          int weatherCode, double currentPrecipitation) {', 1)

old_sf_start = '''        ShortForecast shortForecast = shortForecast(data.optJSONObject("hourly"), now);\n        DailyForecast today = dailyForecast(data.optJSONObject("daily"), now.toLocalDate());'''
new_sf_start = '''        ShortForecast shortForecast = shortForecast(data.optJSONObject("hourly"), now);\n        double pastTwoHours = pastTwoHourRain(data.optJSONObject("hourly"), now);\n        DailyForecast today = dailyForecast(data.optJSONObject("daily"), now.toLocalDate());'''
if old_sf_start not in rain:
    raise SystemExit("digest forecast anchor missing")
rain = rain.replace(old_sf_start, new_sf_start, 1)

old_title_branch = '''            if (shortForecast.precipitationProbability >= 60 || shortForecast.precipitationMm >= 0.5d) {\n                title = "🌧️ आगामी ३ घण्टामा वर्षाको सम्भावना";'''
new_title_branch = '''            if (shortForecast.thunderRisk) {\n                title = "⚡ आगामी ३ घण्टामा मेघगर्जन/चट्याङ सम्भावना";\n            } else if (shortForecast.precipitationProbability >= 60 || shortForecast.precipitationMm >= 0.5d) {\n                title = "🌧️ आगामी ३ घण्टामा वर्षाको सम्भावना";'''
if old_title_branch not in rain:
    raise SystemExit("digest title anchor missing")
rain = rain.replace(old_title_branch, new_title_branch, 1)

old_body_tail = '            if (Double.isFinite(wind)) body.append(" • हावा ").append(Math.round(wind)).append(" km/h");\n            if (Double.isFinite(humidity)) body.append(" • आर्द्रता ").append(Math.round(humidity)).append("%");'
new_body_tail = '            if (pastTwoHours > 0.05d) body.append(" • पछिल्लो २ घण्टा model ≈ ").append(oneDecimal(pastTwoHours)).append(" mm");\n            if (currentPrecipitation > 0.05d) body.append(" • अहिले ").append(oneDecimal(currentPrecipitation)).append(" mm");\n            if (Double.isFinite(wind)) body.append(" • हावा ").append(Math.round(wind)).append(" km/h");\n            if (Double.isFinite(humidity)) body.append(" • आर्द्रता ").append(Math.round(humidity)).append("%");'
if old_body_tail not in rain:
    raise SystemExit("digest body anchor missing")
rain = rain.replace(old_body_tail, new_body_tail, 1)

old_short_arrays = '''        JSONArray probabilities = hourly.optJSONArray("precipitation_probability");\n        JSONArray precipitation = hourly.optJSONArray("precipitation");'''
new_short_arrays = '''        JSONArray probabilities = hourly.optJSONArray("precipitation_probability");\n        JSONArray precipitation = hourly.optJSONArray("precipitation");\n        JSONArray weatherCodes = hourly.optJSONArray("weather_code");'''
if old_short_arrays not in rain:
    raise SystemExit("short forecast arrays anchor missing")
rain = rain.replace(old_short_arrays, new_short_arrays, 1)

old_short_loop = '''            int probability = intAt(probabilities, i);\n            if (probability >= 0) out.precipitationProbability = Math.max(out.precipitationProbability, probability);\n            out.precipitationMm += valueAt(precipitation, i);'''
new_short_loop = '''            int probability = intAt(probabilities, i);\n            if (probability >= 0) out.precipitationProbability = Math.max(out.precipitationProbability, probability);\n            int code = intAt(weatherCodes, i);\n            if (code >= 95 && code <= 99) out.thunderRisk = true;\n            out.precipitationMm += valueAt(precipitation, i);'''
if old_short_loop not in rain:
    raise SystemExit("short forecast loop anchor missing")
rain = rain.replace(old_short_loop, new_short_loop, 1)

extra_methods = r'''
    private static double pastTwoHourRain(JSONObject hourly, ZonedDateTime now) {
        if (hourly == null) return 0d;
        JSONArray times = hourly.optJSONArray("time");
        JSONArray precipitation = hourly.optJSONArray("precipitation");
        if (times == null || precipitation == null) return 0d;
        ZonedDateTime start = now.minusHours(2).minusMinutes(5);
        double total = 0d;
        for (int i = 0; i < times.length(); i++) {
            ZonedDateTime slot = parseSlot(times.optString(i), now.getZone());
            if (slot == null || slot.isBefore(start) || slot.isAfter(now.plusMinutes(5))) continue;
            total += valueAt(precipitation, i);
        }
        return Math.max(0d, total);
    }

    private void maybeNotifyThunderEvent(SharedPreferences prefs, ZonedDateTime now,
                                         int currentCode, ShortForecast forecast,
                                         double temperature, double currentPrecipitation) {
        boolean currentStorm = currentCode >= 95 && currentCode <= 99;
        boolean risk = currentStorm || (forecast != null && forecast.thunderRisk);
        if (!risk) return;
        String key = now.toLocalDate() + "-" + (now.getHour() / 3);
        if (key.equals(prefs.getString("last_thunder_event_key", ""))) return;
        prefs.edit().putString("last_thunder_event_key", key).putLong("last_thunder_alert_at", System.currentTimeMillis()).apply();
        String title = currentStorm ? "⚡ अहिले मेघगर्जन/चट्याङ संकेत" : "⚡ आगामी ३ घण्टामा चट्याङ सम्भावना";
        String text = (currentStorm ? "हालको weather model ले thunderstorm देखाएको छ।" : "आगामी ३ घण्टाको weather model मा thunderstorm code देखिएको छ।")
                + (currentPrecipitation > 0.05d ? " • वर्षा " + oneDecimal(currentPrecipitation) + " mm" : "")
                + (Double.isFinite(temperature) ? " • तापक्रम " + Math.round(temperature) + "°C" : "")
                + " • यो weather-model event हो; official emergency warning भए सरकारी सूचनालाई प्राथमिकता दिनुहोस्।";
        notifyWeatherEvent(7112, title, text);
    }

    private void notifyWeatherEvent(int id, String title, String text) {
        Context app = getApplicationContext();
        NotificationManager manager = app.getSystemService(NotificationManager.class);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    EVENT_CHANNEL_ID, "FloodSafe weather events", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Rain start/stop and thunderstorm model-event notifications");
            channel.enableVibration(true);
            manager.createNotificationChannel(channel);
        }
        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(app, id, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(app, EVENT_CHANNEL_ID)
                : new android.app.Notification.Builder(app);
        android.app.Notification notification = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setOnlyAlertOnce(false)
                .setContentIntent(open)
                .build();
        manager.notify(id, notification);
    }

'''
anchor2 = '    private static DailyForecast dailyForecast(JSONObject daily, LocalDate target) {'
if anchor2 not in rain:
    raise SystemExit("worker extra methods anchor missing")
rain = rain.replace(anchor2, extra_methods + anchor2, 1)
rain = rain.replace('Current-location weather change and tomorrow forecast updates about every 3 hours', 'Current-location weather change and tomorrow forecast updates about every 2 hours', 1)

# Version bump only after all three verified steps are applied.
if "versionCode 24" not in g or "versionName '0.9.07-district-click'" not in g:
    raise SystemExit("v0.9.07 version markers missing")
g = g.replace('versionCode 24', 'versionCode 25', 1)
g = g.replace("versionName '0.9.07-district-click'", "versionName '0.9.08-storm-events-compact-gauge'", 1)

for marker in [
    "V0908_STORM_LEGEND",
    "WEATHER_OVERLAY_V5_RAIN_THUNDER_FIELD",
    "fs-weather-lightning-current",
    "WEATHER_DIGEST_INTERVAL_MS = 2L",
    "last_raining_state",
    "last_thunder_event_key",
]:
    if marker not in (ui + overlay + rain):
        raise SystemExit("missing v0908 marker: " + marker)
if 'android.webkit.WebView' in ui:
    raise SystemExit('WebView introduced')

UI.write_text(ui, encoding="utf-8")
OVERLAY.write_text(overlay, encoding="utf-8")
RAIN.write_text(rain, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")
print("V0908_STEP3_STORM_NOTIFICATIONS_OK")
