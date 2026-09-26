package io.github.pujan1234hub.floodsafe.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * V0903 additive enhancement layer.
 *
 * Deliberately does not depend on, mutate, replace, filter or redraw any BIPAD/DHM
 * river, station, status or MapLibre geometry. Weather visuals are a transparent,
 * touch-through sibling overlay above the existing native map view.
 */
public final class FloodSafeEnhancements {
    private FloodSafeEnhancements() {}

    static final String UI_PREFS = "floodsafe-native-full";
    static final String UI_LANG_EN = "lang_en";
    static final String WEATHER_CHANNEL = "floodsafe_weather_general_v4";
    static final String RAIN_CHANNEL = "floodsafe_rain_updates_v4";
    static final String FLOOD_WARNING_CHANNEL = "flood_warning_v5";
    static final String FLOOD_DANGER_CHANNEL = "flood_danger_emergency_v5";

    public static boolean english(Context context) {
        return context.getSharedPreferences(UI_PREFS, Context.MODE_PRIVATE)
                .getBoolean(UI_LANG_EN, false);
    }

    public static String pick(boolean english, String nepali, String englishText) {
        return english ? englishText : nepali;
    }

    public static String weatherCondition(int code, double precipitation, boolean english) {
        if (code == 0) return pick(english, "मौसम खुला छ", "Clear");
        if (code == 1) return pick(english, "मुख्यतः खुला छ", "Mostly clear");
        if (code == 2) return pick(english, "आंशिक बादल लागेको छ", "Partly cloudy");
        if (code == 3) return pick(english, "बाक्लो बादल लागेको छ", "Overcast");
        if (code == 45 || code == 48) return pick(english, "कुहिरो लागेको छ", "Foggy");
        if (code >= 51 && code <= 57) return pick(english, "सिमसिमे वर्षा भइरहेको छ", "Drizzle");
        if (code == 61 || code == 80) return pick(english, "हल्का वर्षा भइरहेको छ", "Light rain");
        if (code == 63 || code == 81) return pick(english, "वर्षा भइरहेको छ", "Rain");
        if (code == 65 || code == 67 || code == 82 || precipitation >= 2.0d)
            return pick(english, "भारी वर्षा भइरहेको छ", "Heavy rain");
        if (code == 66) return pick(english, "चिसिँदो वर्षा भइरहेको छ", "Freezing rain");
        if (code >= 71 && code <= 77) return pick(english, "हिमपात भइरहेको छ", "Snowing");
        if (code == 85 || code == 86) return pick(english, "हिउँको झरी भइरहेको छ", "Snow showers");
        if (code == 95) return pick(english, "मेघगर्जन भइरहेको छ", "Thunderstorm");
        if (code == 96 || code == 99) return pick(english, "असिना सहित मेघगर्जन भइरहेको छ", "Thunderstorm with hail");
        if (precipitation >= 0.10d) return pick(english, "वर्षा भइरहेको छ", "Raining");
        return pick(english, "मौसम विवरण उपलब्ध छ", "Weather available");
    }

    public static int rainState(int code, double precipitation) {
        if (code == 65 || code == 67 || code == 82 || code == 86 || code == 96 || code == 99 || precipitation >= 2.0d) return 2;
        if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82) || precipitation >= 0.10d) return 1;
        return 0;
    }

    /** Updates text-only widgets in place; it never recreates or reloads the map. */
    public static void applyLanguageTree(View root, boolean english) {
        if (root == null) return;
        if (root instanceof TextView) {
            TextView text = (TextView) root;
            CharSequence raw = text.getText();
            if (raw != null) text.setText(localizeKnownUi(raw.toString(), english));
        }
        if (root instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) root;
            for (int i = 0; i < group.getChildCount(); i++) applyLanguageTree(group.getChildAt(i), english);
        }
    }

    private static String localizeKnownUi(String s, boolean english) {
        final String[][] pairs = new String[][]{
                {"◎ मेरो हालको स्थान", "◎ My current location"},
                {"आधिकारिक", "OFFICIAL"},
                {"＋ ठूलो", "＋ Zoom"},
                {"− सानो", "− Out"},
                {"🇳🇵 नेपाल", "🇳🇵 Nepal"},
                {"🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम", "🛡️ Flood risk near me"},
                {"सबै official स्टेशन", "Official stations"},
                {"चेतावनी", "Warning"},
                {"खतरा", "Danger"},
                {"सबै स्टेशन देखाउनुहोस्", "Show all stations"},
                {"कम देखाउनुहोस्", "Show less"},
                {"मृतक", "Deaths"},
                {"घाइते", "Injured"},
                {"बेपत्ता", "Missing"},
                {"उद्धार", "Rescued"},
                {"गोपनीयता नीति हेर्नुहोस् →", "View privacy policy →"},
                {"⌂\nगृह", "⌂\nHome"},
                {"🗺️\nनदी नक्सा", "🗺️\nRiver map"},
                {"🔔\nसमाचार", "🔔\nNews"},
                {"वर्षा", "Rain"},
                {"आर्द्रता", "Humidity"},
                {"हावा", "Wind"},
                {"बन्द", "Close"},
                {"🎙️ माइकबाट सोध्नुहोस्", "🎙️ Ask by voice"}
        };
        for (String[] pair : pairs) {
            if (s.equals(pair[0]) || s.equals(pair[1])) return english ? pair[1] : pair[0];
        }
        return s;
    }

    /** Screen-space atmospheric overlay. It is independent of all river/station map layers. */
    public static final class WeatherOverlayView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Handler handler = new Handler(Looper.getMainLooper());
        private int weatherCode = 0;
        private double precipitation = 0d;
        private int cloudCover = 0;
        private float phase = 0f;
        private boolean attached;

        private final Runnable animate = new Runnable() {
            @Override public void run() {
                if (!attached) return;
                phase = (phase + 1.4f) % 1000f;
                invalidate();
                if (needsMotion()) handler.postDelayed(this, 90L);
            }
        };

        public WeatherOverlayView(Context context) {
            super(context);
            setClickable(false);
            setFocusable(false);
            setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            setBackgroundColor(Color.TRANSPARENT);
        }

        public void updateWeather(int code, double rainMm, int clouds) {
            weatherCode = code;
            precipitation = Math.max(0d, rainMm);
            cloudCover = Math.max(0, Math.min(100, clouds));
            setVisibility(needsVisual() ? VISIBLE : INVISIBLE);
            handler.removeCallbacks(animate);
            if (attached && needsMotion()) handler.post(animate);
            invalidate();
        }

        private boolean needsVisual() {
            return weatherCode >= 2 || precipitation >= 0.10d || cloudCover >= 45;
        }

        private boolean needsMotion() {
            return needsVisual();
        }

        @Override protected void onAttachedToWindow() {
            super.onAttachedToWindow();
            attached = true;
            if (needsMotion()) handler.post(animate);
        }

        @Override protected void onDetachedFromWindow() {
            attached = false;
            handler.removeCallbacksAndMessages(null);
            super.onDetachedFromWindow();
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            if (!needsVisual()) return;
            final float w = getWidth(), h = getHeight();
            if (w <= 0 || h <= 0) return;

            int rain = rainState(weatherCode, precipitation);
            int cloudAlpha = Math.min(110, 32 + Math.max(cloudCover, weatherCode == 3 ? 85 : 45));
            if (rain == 2) cloudAlpha = Math.max(cloudAlpha, 118);
            paint.setColor(Color.argb(cloudAlpha, 225, 238, 244));
            paint.setStyle(Paint.Style.FILL);

            for (int i = 0; i < 5; i++) {
                float baseX = ((i * 0.23f * w) + phase * (0.12f + i * 0.015f)) % (w + w * .35f) - w * .18f;
                float y = h * (0.10f + (i % 3) * 0.16f);
                float cw = w * (0.24f + (i % 2) * .06f);
                float ch = Math.max(26f, h * .10f);
                canvas.drawOval(new RectF(baseX, y, baseX + cw, y + ch), paint);
                canvas.drawCircle(baseX + cw * .28f, y + ch * .12f, ch * .55f, paint);
                canvas.drawCircle(baseX + cw * .58f, y + ch * .05f, ch * .68f, paint);
            }

            if (rain > 0) {
                paint.setStrokeWidth(rain == 2 ? 3.2f : 2.0f);
                paint.setColor(Color.argb(rain == 2 ? 145 : 100, 155, 220, 255));
                int count = rain == 2 ? 46 : 24;
                float speedOffset = (phase * (rain == 2 ? 7f : 4f)) % Math.max(1f, h);
                for (int i = 0; i < count; i++) {
                    float x = ((i * 73f + phase * 2.1f) % (w + 30f)) - 15f;
                    float y = ((i * 47f + speedOffset) % (h + 45f)) - 40f;
                    canvas.drawLine(x, y, x - (rain == 2 ? 8f : 5f), y + (rain == 2 ? 28f : 20f), paint);
                }
            }
        }
    }

    public static final class DistrictWeatherView extends LinearLayout {
        private final ExecutorService io = Executors.newSingleThreadExecutor();
        private final LinearLayout rows;
        private final TextView title;
        private final TextView subtitle;
        private final TextView status;
        private final Button toggle;
        private volatile boolean showAll;
        private volatile boolean english;
        private List<DistrictWeather> cached = new ArrayList<>();

        public DistrictWeatherView(Context context, boolean english) {
            super(context);
            this.english = english;
            setOrientation(VERTICAL);
            int p = dp(16);
            setPadding(p, p, p, p);
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.argb(248, 255, 255, 255));
            bg.setCornerRadius(dp(24));
            bg.setStroke(dp(1), Color.rgb(207, 229, 239));
            setBackground(bg);
            setElevation(dp(3));

            title = label("", 20, true, Color.rgb(16, 39, 70));
            subtitle = label("", 12, false, Color.rgb(91, 123, 145));
            status = label("", 11, true, Color.rgb(91, 123, 145));
            addView(title);
            addView(subtitle);
            addView(status, lp(-1, -2, 0, dp(5), 0, dp(8)));
            rows = new LinearLayout(context);
            rows.setOrientation(VERTICAL);
            addView(rows);
            toggle = new Button(context);
            toggle.setAllCaps(false);
            toggle.setOnClickListener(v -> { showAll = !showAll; render(); });
            addView(toggle, lp(-1, dp(48), 0, dp(8), 0, 0));
            updateLabels();
            refresh();
        }

        public void setEnglish(boolean english) {
            this.english = english;
            updateLabels();
            render();
        }

        public void refresh() {
            status.setText(pick(english, "७७ जिल्लाको वास्तविक मौसम लोड हुँदैछ…", "Loading real weather for all 77 districts…"));
            io.execute(() -> {
                try {
                    List<DistrictPoint> points = loadDistrictPoints(getContext());
                    List<DistrictWeather> result = fetchDistrictWeather(points);
                    post(() -> {
                        cached = result;
                        status.setText(pick(english,
                                "Open-Meteo • हालको वास्तविक मौसम • " + result.size() + " जिल्ला",
                                "Open-Meteo • current real weather • " + result.size() + " districts"));
                        render();
                    });
                } catch (Exception e) {
                    post(() -> status.setText(pick(english,
                            "जिल्ला मौसम अहिले लोड हुन सकेन। नक्कली डेटा देखाइएको छैन।",
                            "District weather is unavailable right now. No fake data is shown.")));
                }
            });
        }

        private void updateLabels() {
            title.setText(pick(english, "🌦️ ७७ जिल्लाको हालको मौसम", "🌦️ Current weather in Nepal's 77 districts"));
            subtitle.setText(pick(english,
                    "तापक्रम • वर्षा • आर्द्रता • हावा • मौसम अवस्था",
                    "Temperature • precipitation • humidity • wind • condition"));
            toggle.setText(showAll ? pick(english, "कम जिल्ला देखाउनुहोस्", "Show fewer districts")
                    : pick(english, "सबै ७७ जिल्ला देखाउनुहोस्", "Show all 77 districts"));
        }

        private void render() {
            rows.removeAllViews();
            updateLabels();
            int limit = showAll ? cached.size() : Math.min(12, cached.size());
            for (int i = 0; i < limit; i++) {
                DistrictWeather d = cached.get(i);
                String name = english ? d.name : districtNepali(d.name);
                String detail = weatherCondition(d.code, d.precipitation, english)
                        + " • " + (Double.isFinite(d.temperature) ? Math.round(d.temperature) + "°C" : "—")
                        + " • " + pick(english, "वर्षा ", "rain ") + oneDecimal(d.precipitation) + " mm"
                        + " • " + pick(english, "आर्द्रता ", "humidity ") + (Double.isFinite(d.humidity) ? Math.round(d.humidity) + "%" : "—")
                        + " • " + pick(english, "हावा ", "wind ") + (Double.isFinite(d.wind) ? Math.round(d.wind) + " km/h" : "—");
                TextView row = label(name + "\n" + detail, 12, false, Color.rgb(36, 72, 96));
                row.setPadding(dp(10), dp(9), dp(10), dp(9));
                GradientDrawable bg = new GradientDrawable();
                bg.setColor(Color.rgb(246, 251, 254));
                bg.setCornerRadius(dp(14));
                bg.setStroke(dp(1), Color.rgb(220, 236, 244));
                row.setBackground(bg);
                rows.addView(row, lp(-1, -2, 0, 0, 0, dp(6)));
            }
        }

        @Override protected void onDetachedFromWindow() {
            io.shutdownNow();
            super.onDetachedFromWindow();
        }

        private static final class DistrictPoint {
            final String name;
            final double lat, lon;
            DistrictPoint(String name, double lat, double lon) { this.name = name; this.lat = lat; this.lon = lon; }
        }

        private static final class DistrictWeather {
            final String name;
            final double temperature, precipitation, humidity, wind;
            final int code;
            DistrictWeather(String name, double temperature, double precipitation, double humidity, double wind, int code) {
                this.name = name; this.temperature = temperature; this.precipitation = precipitation;
                this.humidity = humidity; this.wind = wind; this.code = code;
            }
        }

        private static List<DistrictPoint> loadDistrictPoints(Context context) throws Exception {
            JSONObject root = new JSONObject(readAsset(context, "floodsafe-nepal/v24/nepal-districts.json"));
            JSONArray features = root.optJSONArray("features");
            List<DistrictPoint> out = new ArrayList<>();
            if (features == null) return out;
            for (int i = 0; i < features.length(); i++) {
                JSONObject f = features.optJSONObject(i);
                if (f == null) continue;
                JSONObject props = f.optJSONObject("properties");
                JSONObject geometry = f.optJSONObject("geometry");
                if (props == null || geometry == null) continue;
                String name = props.optString("nameEn", "").trim();
                JSONArray coordinates = geometry.optJSONArray("coordinates");
                if (name.isEmpty() || coordinates == null) continue;
                double[] acc = new double[]{0d, 0d, 0d};
                collectCoordinates(coordinates, acc);
                if (acc[2] <= 0d) continue;
                double lon = acc[0] / acc[2], lat = acc[1] / acc[2];
                if (lat >= 25.5 && lat <= 31.0 && lon >= 79.4 && lon <= 89.0) out.add(new DistrictPoint(name, lat, lon));
            }
            return out;
        }

        private static void collectCoordinates(JSONArray a, double[] acc) {
            if (a.length() >= 2 && a.opt(0) instanceof Number && a.opt(1) instanceof Number) {
                double lon = a.optDouble(0, Double.NaN), lat = a.optDouble(1, Double.NaN);
                if (Double.isFinite(lat) && Double.isFinite(lon) && lat >= 25.0 && lat <= 32.0 && lon >= 79.0 && lon <= 90.0) {
                    acc[0] += lon; acc[1] += lat; acc[2] += 1d;
                }
                return;
            }
            for (int i = 0; i < a.length(); i++) {
                Object child = a.opt(i);
                if (child instanceof JSONArray) collectCoordinates((JSONArray) child, acc);
            }
        }

        private static List<DistrictWeather> fetchDistrictWeather(List<DistrictPoint> points) throws Exception {
            if (points.isEmpty()) return new ArrayList<>();
            StringBuilder lats = new StringBuilder(), lons = new StringBuilder();
            for (int i = 0; i < points.size(); i++) {
                if (i > 0) { lats.append(','); lons.append(','); }
                lats.append(String.format(Locale.US, "%.4f", points.get(i).lat));
                lons.append(String.format(Locale.US, "%.4f", points.get(i).lon));
            }
            String url = "https://api.open-meteo.com/v1/forecast?latitude=" + lats
                    + "&longitude=" + lons
                    + "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m"
                    + "&timezone=Asia%2FKathmandu";
            HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(20000); c.setUseCaches(false);
            c.setRequestProperty("Accept", "application/json");
            int response = c.getResponseCode();
            if (response != 200) { c.disconnect(); throw new IllegalStateException("Weather HTTP " + response); }
            StringBuilder body = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
                String line; while ((line = r.readLine()) != null) body.append(line);
            } finally { c.disconnect(); }
            Object decoded = new JSONTokener(body.toString()).nextValue();
            JSONArray list = decoded instanceof JSONArray ? (JSONArray) decoded : new JSONArray().put(decoded);
            List<DistrictWeather> out = new ArrayList<>();
            int n = Math.min(points.size(), list.length());
            for (int i = 0; i < n; i++) {
                JSONObject item = list.optJSONObject(i);
                JSONObject current = item == null ? null : item.optJSONObject("current");
                if (current == null) continue;
                out.add(new DistrictWeather(points.get(i).name,
                        current.optDouble("temperature_2m", Double.NaN),
                        Math.max(0d, current.optDouble("precipitation", 0d)),
                        current.optDouble("relative_humidity_2m", Double.NaN),
                        current.optDouble("wind_speed_10m", Double.NaN),
                        current.optInt("weather_code", -1)));
            }
            return out;
        }

        private TextView label(String text, float sp, boolean bold, int color) {
            TextView v = new TextView(getContext());
            v.setText(text); v.setTextSize(sp); v.setTextColor(color); v.setLineSpacing(0f, 1.08f);
            if (bold) v.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            return v;
        }

        private LayoutParams lp(int w, int h, int l, int t, int r, int b) {
            LayoutParams p = new LayoutParams(w, h); p.setMargins(l, t, r, b); return p;
        }

        private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    }

    /** One engine for 2-hour summaries plus meaningful rain start/stop/intensity changes. */
    public static void processWeatherNotifications(Context app, JSONObject data, SharedPreferences prefs,
                                                   ZonedDateTime now, double temperature, double apparent,
                                                   double humidity, double wind, int code, double precipitation) {
        boolean en = english(app);
        long nowMs = System.currentTimeMillis();
        int state = rainState(code, precipitation);
        int previous = prefs.getInt("wx_rain_state_v4", -1);
        long lastEvent = prefs.getLong("wx_rain_event_at_v4", 0L);

        if (previous >= 0 && previous != state && (lastEvent <= 0L || nowMs - lastEvent >= 20L * 60L * 1000L)) {
            String title;
            String text;
            if (previous == 0 && state == 1) {
                title = pick(en, "🌧️ तपाईंको स्थान नजिक वर्षा सुरु भएको छ", "🌧️ Rain has started near your location");
                text = pick(en, "हालको मौसम मापनले वर्षा सुरु भएको देखाउँछ। बाहिर निस्कँदा सतर्क रहनुहोस्।",
                        "Current weather data shows rain has started. Take care if you are heading outside.");
            } else if (state == 2 && previous < 2) {
                title = pick(en, "⛈️ तपाईंको क्षेत्रमा भारी वर्षा सुरु भएको छ", "⛈️ Heavy rain has started in your area");
                text = pick(en, "वर्षाको तीव्रता बढेको छ। नदी/खोलाको आधिकारिक चेतावनी छुट्टै FloodSafe alert बाट आउँछ।",
                        "Rain intensity has increased. Official river warnings are delivered separately by FloodSafe alerts.");
            } else if (previous == 2 && state == 1) {
                title = pick(en, "🌦️ वर्षाको तीव्रता घटेको छ", "🌦️ Rainfall intensity has reduced");
                text = pick(en, "भारी वर्षा कमजोर भएको छ, तर हल्का/मध्यम वर्षा अझै जारी छ।",
                        "Heavy rain has eased, but light or moderate rain is still continuing.");
            } else if (previous > 0 && state == 0) {
                title = pick(en, "🌤️ तपाईंको क्षेत्रमा वर्षा रोकिएको छ", "🌤️ Rain has stopped near your location");
                text = pick(en, "हालको मौसम मापनमा अब उल्लेख्य वर्षा देखिएको छैन।",
                        "Current weather data no longer shows meaningful rainfall.");
            } else {
                title = pick(en, "🌦️ स्थानीय मौसम परिवर्तन", "🌦️ Local weather change");
                text = weatherCondition(code, precipitation, en);
            }
            notifyEvent(app, RAIN_CHANNEL, pick(en, "वर्षा अपडेट", "Rain updates"),
                    NotificationManager.IMPORTANCE_HIGH, title, text, false, true);
            prefs.edit().putLong("wx_rain_event_at_v4", nowMs).apply();
        }
        prefs.edit().putInt("wx_rain_state_v4", state).apply();

        JSONObject current = data == null ? null : data.optJSONObject("current");
        int cloud = current == null ? -1 : current.optInt("cloud_cover", -1);
        int oldCloud = prefs.getInt("wx_cloud_v4", -1);
        prefs.edit().putInt("wx_cloud_v4", cloud).apply();

        long lastDigest = prefs.getLong("last_weather_digest_v4_at", 0L);
        long twoHours = 2L * 60L * 60L * 1000L;
        int shortRainChance = nextHoursRainChance(data == null ? null : data.optJSONObject("hourly"), now, 4);
        String signature = conditionBucket(code) + ":" + state + ":" + (Double.isFinite(temperature) ? Math.round(temperature / 2d) : -99)
                + ":" + (cloud < 0 ? -1 : cloud / 20) + ":" + (shortRainChance < 0 ? -1 : shortRainChance / 20);
        String previousSignature = prefs.getString("wx_digest_signature_v4", "");
        boolean changed = !signature.equals(previousSignature);
        boolean cloudJump = oldCloud >= 0 && cloud >= 0 && cloud - oldCloud >= 25;
        boolean intervalDue = lastDigest <= 0L || nowMs - lastDigest >= twoHours;
        boolean changedAndUseful = changed && (lastDigest <= 0L || nowMs - lastDigest >= 45L * 60L * 1000L);
        boolean periodicSummary = intervalDue && (changed || lastDigest <= 0L || nowMs - lastDigest >= 6L * 60L * 60L * 1000L);
        if (!changedAndUseful && !periodicSummary && !cloudJump) return;

        int hour = now.getHour();
        String title;
        if (hour >= 5 && hour < 12) title = pick(en, "शुभ प्रभात • स्थानीय मौसम", "Good morning • Local weather");
        else if (hour >= 12 && hour < 17) title = pick(en, "दिउँसोको मौसम अपडेट", "Afternoon weather update");
        else if (hour >= 17 && hour < 23) title = pick(en, "साँझको मौसम सारांश", "Evening weather summary");
        else title = pick(en, "स्थानीय मौसम अपडेट", "Local weather update");

        StringBuilder text = new StringBuilder(weatherCondition(code, precipitation, en));
        if (Double.isFinite(temperature)) text.append(" • ").append(Math.round(temperature)).append("°C");
        if (precipitation >= 0.05d) text.append(" • ").append(pick(en, "वर्षा ", "rain ")).append(oneDecimal(precipitation)).append(" mm");
        if (Double.isFinite(humidity)) text.append(" • ").append(pick(en, "आर्द्रता ", "humidity ")).append(Math.round(humidity)).append("%");
        if (Double.isFinite(wind)) text.append(" • ").append(pick(en, "हावा ", "wind ")).append(Math.round(wind)).append(" km/h");
        if (shortRainChance >= 0) {
            text.append(" • ").append(pick(en, "आउँदो केही घण्टामा वर्षा सम्भावना ", "rain chance next few hours "))
                    .append(shortRainChance).append("%");
        }
        if (cloudJump) text.append(pick(en, " • बादलको मात्रा बढ्दैछ", " • cloud cover is increasing"));
        if (hour >= 17 && hour < 23) {
            int overnight = nextHoursRainChance(data == null ? null : data.optJSONObject("hourly"), now, 10);
            if (overnight >= 0) text.append(" • ").append(pick(en, "रातभर वर्षा सम्भावना ", "overnight rain chance ")).append(overnight).append("%");
        }

        notifyEvent(app, WEATHER_CHANNEL, pick(en, "सामान्य मौसम अपडेट", "General weather updates"),
                NotificationManager.IMPORTANCE_DEFAULT, title, text.toString(), false, false);
        prefs.edit().putLong("last_weather_digest_v4_at", nowMs).putString("wx_digest_signature_v4", signature).apply();
    }

    private static int nextHoursRainChance(JSONObject hourly, ZonedDateTime now, int hours) {
        if (hourly == null) return -1;
        JSONArray times = hourly.optJSONArray("time");
        JSONArray chance = hourly.optJSONArray("precipitation_probability");
        if (times == null || chance == null) return -1;
        int max = -1;
        ZonedDateTime end = now.plusHours(hours);
        for (int i = 0; i < Math.min(times.length(), chance.length()); i++) {
            try {
                ZonedDateTime t = java.time.LocalDateTime.parse(times.optString(i)).atZone(now.getZone());
                if (t.isBefore(now.minusMinutes(30)) || t.isAfter(end)) continue;
                max = Math.max(max, chance.optInt(i, -1));
            } catch (Exception ignored) {}
        }
        return max;
    }

    private static int conditionBucket(int code) {
        if (code == 0) return 0;
        if (code <= 2) return 1;
        if (code == 3 || code == 45 || code == 48) return 2;
        if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return 3;
        if (code >= 95) return 4;
        return 5;
    }

    public static void notifyFloodHazard(Context app, String stage, String stationName,
                                         String riverName, double distanceKm, double level,
                                         double warningLevel, double dangerLevel, long measuredAt,
                                         int requestCode) {
        NotificationManager manager = app.getSystemService(NotificationManager.class);
        if (manager == null) return;
        boolean danger = "danger".equals(stage);
        boolean en = english(app);
        String channelId = danger ? FLOOD_DANGER_CHANNEL : FLOOD_WARNING_CHANNEL;
        String channelName = danger ? pick(en, "बाढी खतरा / आपतकालीन अलार्म", "Flood Danger / Emergency Alarm")
                : pick(en, "बाढी चेतावनी", "Flood Warning");

        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(channelId, channelName,
                    danger ? NotificationManager.IMPORTANCE_HIGH : NotificationManager.IMPORTANCE_HIGH);
            channel.enableVibration(true);
            channel.setVibrationPattern(danger
                    ? new long[]{0, 700, 250, 700, 250, 1000, 300, 1000}
                    : new long[]{0, 300, 220, 450});
            if (danger) {
                Uri alarm = Settings.System.DEFAULT_ALARM_ALERT_URI;
                AudioAttributes attrs = new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                channel.setSound(alarm, attrs);
                channel.setDescription(pick(en,
                        "प्रभावित नदी geometry बाट करिब २ km भित्रको verified current Danger अलार्म",
                        "Verified current Danger alarm within about 2 km of the affected river geometry"));
            } else {
                Uri sound = Settings.System.DEFAULT_NOTIFICATION_URI;
                AudioAttributes attrs = new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
                channel.setSound(sound, attrs);
                channel.setDescription(pick(en,
                        "प्रभावित नदी geometry बाट करिब २ km भित्रको verified current Warning",
                        "Verified current Warning within about 2 km of the affected river geometry"));
            }
            manager.createNotificationChannel(channel);
        }

        String river = riverName == null || riverName.trim().isEmpty()
                ? pick(en, "प्रभावित नदी", "affected river") : riverName.trim();
        String title = danger
                ? pick(en, "🚨 खतरा: " + river + " आपतकालीन बाढी अलार्म", "🚨 DANGER: " + river + " flood emergency")
                : pick(en, "⚠️ चेतावनी: " + river, "⚠️ WARNING: " + river);
        String reading = Double.isFinite(level) ? String.format(Locale.US, "%.2f m", level) : "—";
        String distance = Double.isFinite(distanceKm) ? String.format(Locale.US, "%.1f km", distanceKm) : "—";
        String text;
        if (danger) {
            text = pick(en,
                    river + " आधिकारिक खतरा अवस्थामा पुगेको छ। तपाईं प्रभावित नदीको बाढी जोखिम corridor बाट करिब " + distance
                            + " भित्र हुनुहुन्छ। हालको आधिकारिक तह " + reading + "। सुरक्षित स्थानतर्फ जानुहोस् र आधिकारिक निर्देशन पालना गर्नुहोस्।",
                    river + " has reached an official Danger condition. You are about " + distance
                            + " from the affected river flood-risk corridor. Current official level: " + reading
                            + ". Move to a safer location and follow official instructions.");
        } else {
            text = pick(en,
                    river + " मा आधिकारिक चेतावनी अवस्था छ। तपाईं प्रभावित नदीको करिब " + distance
                            + " भित्र हुनुहुन्छ। हालको आधिकारिक तह " + reading
                            + "। नदी किनार, पुलमुनि र तल्लो भूभागबाट टाढा रहनुहोस् र नयाँ आधिकारिक अपडेट हेर्नुहोस्।",
                    river + " is in an official Warning condition. You are about " + distance
                            + " from the affected river. Current official level: " + reading
                            + ". Stay away from river banks, under-bridge areas and low ground, and follow new official updates.");
        }

        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(app, requestCode, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(app, channelId) : new Notification.Builder(app);
        builder.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true)
                .setContentIntent(open)
                .setCategory(danger ? Notification.CATEGORY_ALARM : Notification.CATEGORY_EVENT)
                .setPriority(danger ? Notification.PRIORITY_MAX : Notification.PRIORITY_HIGH);
        if (Build.VERSION.SDK_INT < 26) {
            builder.setVibrate(danger ? new long[]{0, 700, 250, 700, 250, 1000} : new long[]{0, 300, 220, 450});
            builder.setSound(danger ? Settings.System.DEFAULT_ALARM_ALERT_URI : Settings.System.DEFAULT_NOTIFICATION_URI);
        }
        manager.notify(requestCode, builder.build());
    }

    private static void notifyEvent(Context app, String channelId, String channelName, int importance,
                                    String title, String text, boolean alarm, boolean vibrate) {
        NotificationManager manager = app.getSystemService(NotificationManager.class);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(channelId, channelName, importance);
            channel.enableVibration(vibrate);
            if (vibrate) channel.setVibrationPattern(new long[]{0, 220, 180, 320});
            manager.createNotificationChannel(channel);
        }
        Intent launch = new Intent(app, NativeFullActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        int id = 8000 + (int) (System.currentTimeMillis() % 800000L);
        PendingIntent open = PendingIntent.getActivity(app, id, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(app, channelId) : new Notification.Builder(app);
        builder.setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle(title).setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setAutoCancel(true).setContentIntent(open)
                .setOnlyAlertOnce(false);
        if (Build.VERSION.SDK_INT < 26 && vibrate) builder.setVibrate(new long[]{0, 220, 180, 320});
        manager.notify(id, builder.build());
    }

    private static String readAsset(Context context, String path) throws Exception {
        try (InputStream in = context.getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder out = new StringBuilder();
            String line; while ((line = r.readLine()) != null) out.append(line);
            return out.toString();
        }
    }

    private static String oneDecimal(double value) {
        return String.format(Locale.US, "%.1f", Math.max(0d, value));
    }

    private static String districtNepali(String name) {
        if (name == null) return "";
        String k = name.toLowerCase(Locale.ROOT).replaceAll("[^a-z]", "");
        if (k.contains("nawalparasi") && (k.contains("east") || k.contains("nawalpur"))) return "नवलपुर";
        if (k.contains("nawalparasi") && (k.contains("west") || k.contains("parasi"))) return "परासी";
        if (k.contains("easternrukum") || k.contains("rukumeast")) return "रुकुम पूर्व";
        if (k.contains("westernrukum") || k.contains("rukumwest")) return "रुकुम पश्चिम";
        String[][] pairs = new String[][]{
                {"taplejung","ताप्लेजुङ"},{"panchthar","पाँचथर"},{"ilam","इलाम"},{"jhapa","झापा"},{"morang","मोरङ"},{"sunsari","सुनसरी"},{"dhankuta","धनकुटा"},{"terhathum","तेह्रथुम"},{"sankhuwasabha","संखुवासभा"},{"bhojpur","भोजपुर"},{"solukhumbu","सोलुखुम्बु"},{"khotang","खोटाङ"},{"okhaldhunga","ओखलढुङ्गा"},{"udayapur","उदयपुर"},
                {"saptari","सप्तरी"},{"siraha","सिरहा"},{"dhanusha","धनुषा"},{"mahottari","महोत्तरी"},{"sarlahi","सर्लाही"},{"sindhuli","सिन्धुली"},{"ramechhap","रामेछाप"},{"dolakha","दोलखा"},{"sindhupalchok","सिन्धुपाल्चोक"},{"kavrepalanchok","काभ्रेपलाञ्चोक"},{"kavre","काभ्रेपलाञ्चोक"},{"lalitpur","ललितपुर"},{"bhaktapur","भक्तपुर"},{"kathmandu","काठमाडौं"},{"nuwakot","नुवाकोट"},{"rasuwa","रसुवा"},{"dhading","धादिङ"},{"makwanpur","मकवानपुर"},{"rautahat","रौतहट"},{"bara","बारा"},{"parsa","पर्सा"},{"chitwan","चितवन"},
                {"gorkha","गोरखा"},{"lamjung","लमजुङ"},{"tanahun","तनहुँ"},{"syangja","स्याङ्जा"},{"kaski","कास्की"},{"manang","मनाङ"},{"mustang","मुस्ताङ"},{"myagdi","म्याग्दी"},{"parbat","पर्वत"},{"baglung","बागलुङ"},{"nawalpur","नवलपुर"},
                {"parasi","परासी"},{"rupandehi","रुपन्देही"},{"kapilvastu","कपिलवस्तु"},{"palpa","पाल्पा"},{"arghakhanchi","अर्घाखाँची"},{"gulmi","गुल्मी"},{"pyuthan","प्युठान"},{"rolpa","रोल्पा"},{"dang","दाङ"},{"banke","बाँके"},{"bardiya","बर्दिया"},
                {"salyan","सल्यान"},{"dolpa","डोल्पा"},{"jumla","जुम्ला"},{"mugu","मुगु"},{"humla","हुम्ला"},{"kalikot","कालिकोट"},{"jajarkot","जाजरकोट"},{"dailekh","दैलेख"},{"surkhet","सुर्खेत"},
                {"bajura","बाजुरा"},{"bajhang","बझाङ"},{"darchula","दार्चुला"},{"baitadi","बैतडी"},{"dadeldhura","डडेलधुरा"},{"doti","डोटी"},{"achham","अछाम"},{"kailali","कैलाली"},{"kanchanpur","कञ्चनपुर"}
        };
        for (String[] p : pairs) if (k.equals(p[0]) || k.contains(p[0])) return p[1];
        return name;
    }
}