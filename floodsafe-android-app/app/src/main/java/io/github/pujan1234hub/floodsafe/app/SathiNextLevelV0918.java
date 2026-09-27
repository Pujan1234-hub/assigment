package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * v0.9.18 scoped SATHI upgrade.
 *
 * This class intentionally does not replace the native map, BIPAD station rendering,
 * river geometry, warning logic or background monitoring. It only upgrades the SATHI
 * interaction and performs two small presentation repairs requested for the native UI:
 * duplicate language control suppression and a real animated cloud glyph when the
 * weather label reports cloudy/overcast conditions.
 */
final class SathiNextLevelV0918 {
    private static final String PREFS = "floodsafe-native-full";
    private static final String RIVER_ENDPOINT = "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String NEWS_ENDPOINT = "https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three";
    private static final long RIVER_FRESH_MS = 10L * 60L * 1000L;
    private static final long CACHE_MS = 45_000L;
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final ExecutorService IO = Executors.newFixedThreadPool(3);
    private static final WeakHashMap<View, Boolean> PATCHED_SATHI = new WeakHashMap<>();
    private static final WeakHashMap<TextView, CloudDrawable> CLOUDS = new WeakHashMap<>();
    private static volatile boolean installed;
    private static final Object CACHE_LOCK = new Object();
    private static List<Station> riverCache = new ArrayList<>();
    private static long riverCacheAt;

    private SathiNextLevelV0918() {}

    static void install(Context context) {
        if (installed || context == null) return;
        Context appContext = context.getApplicationContext();
        if (!(appContext instanceof Application)) return;
        installed = true;
        ((Application) appContext).registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override public void onActivityCreated(Activity activity, Bundle state) {}
            @Override public void onActivityStarted(Activity activity) {}
            @Override public void onActivityResumed(Activity activity) {
                if (!isTarget(activity)) return;
                MAIN.postDelayed(() -> patch(activity), 260L);
                MAIN.postDelayed(() -> patch(activity), 900L);
            }
            @Override public void onActivityPaused(Activity activity) {}
            @Override public void onActivityStopped(Activity activity) {}
            @Override public void onActivitySaveInstanceState(Activity activity, Bundle outState) {}
            @Override public void onActivityDestroyed(Activity activity) {}
        });
    }

    private static boolean isTarget(Activity activity) {
        return activity != null && activity.getClass().getName().endsWith(".NativeFullActivity");
    }

    private static void patch(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        View root = activity.getWindow() == null ? null : activity.getWindow().getDecorView();
        if (root == null) return;
        patchSathiButtons(activity, root);
        hideDuplicateLanguageControls(root);
        patchCloudLabels(activity, root);
    }

    private static void patchSathiButtons(Activity activity, View root) {
        List<TextView> textViews = new ArrayList<>();
        collectTextViews(root, textViews);
        for (TextView v : textViews) {
            String text = String.valueOf(v.getText()).toUpperCase(Locale.ROOT);
            if (!text.contains("SATHI") || !v.isClickable()) continue;
            synchronized (PATCHED_SATHI) {
                if (Boolean.TRUE.equals(PATCHED_SATHI.get(v))) continue;
                PATCHED_SATHI.put(v, true);
            }
            v.setOnClickListener(ignored -> showSathi(activity));
        }
    }

    private static void hideDuplicateLanguageControls(View root) {
        List<TextView> candidates = new ArrayList<>();
        collectTextViews(root, candidates);
        List<TextView> langs = new ArrayList<>();
        for (TextView v : candidates) {
            if (v.getVisibility() != View.VISIBLE || !v.isClickable()) continue;
            String s = normalize(String.valueOf(v.getText()));
            if (s.contains("नेपाली") || s.contains("अङ्ग्रेजी") || s.contains("अंग्रेजी") ||
                    s.equals("english") || s.equals("nepali") || s.contains(" english") || s.contains(" nepali")) {
                langs.add(v);
            }
        }
        if (langs.size() < 2) return;
        langs.sort(Comparator.comparingInt(SathiNextLevelV0918::screenY));
        TextView keep = langs.get(0);
        for (int i = 1; i < langs.size(); i++) {
            TextView extra = langs.get(i);
            if (extra == keep) continue;
            // Only suppress a clearly lower duplicate; never remove the header selector.
            if (screenY(extra) > screenY(keep) + dp(extra.getContext(), 28)) extra.setVisibility(View.GONE);
        }
    }

    private static int screenY(View v) {
        int[] p = new int[2];
        try { v.getLocationOnScreen(p); } catch (Exception ignored) {}
        return p[1];
    }

    private static void patchCloudLabels(Activity activity, View root) {
        List<TextView> all = new ArrayList<>();
        collectTextViews(root, all);
        for (TextView tv : all) {
            if (tv.getVisibility() != View.VISIBLE) continue;
            String s = normalize(String.valueOf(tv.getText()));
            boolean cloudy = s.contains("cloudy") || s.contains("overcast") || s.contains("cloud") ||
                    s.contains("बादल") || s.contains("मेघाच्छन्न");
            if (!cloudy) continue;
            synchronized (CLOUDS) {
                if (CLOUDS.containsKey(tv)) continue;
                CloudDrawable cloud = new CloudDrawable(tv.getContext());
                int w = dp(tv.getContext(), 48), h = dp(tv.getContext(), 30);
                cloud.setBounds(0, 0, w, h);
                tv.setCompoundDrawablePadding(dp(tv.getContext(), 8));
                tv.setCompoundDrawables(cloud, null, null, null);
                CLOUDS.put(tv, cloud);
                cloud.start();
            }
            break;
        }
    }

    private static void collectTextViews(View v, List<TextView> out) {
        if (v instanceof TextView) out.add((TextView) v);
        if (!(v instanceof ViewGroup)) return;
        ViewGroup g = (ViewGroup) v;
        for (int i = 0; i < g.getChildCount(); i++) collectTextViews(g.getChildAt(i), out);
    }

    private static void showSathi(Activity activity) {
        final boolean english = isEnglish(activity);
        LinearLayout box = new LinearLayout(activity);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(activity, 18), dp(activity, 6), dp(activity, 18), 0);

        TextView answer = new TextView(activity);
        answer.setTextColor(Color.rgb(25, 51, 75));
        answer.setTextSize(15f);
        answer.setLineSpacing(0f, 1.12f);
        answer.setText(english
                ? "Hi — I’m SATHI. Ask me about a named river, current warnings, Nepal weather, latest app news, nearby river status, or how FloodSafe works."
                : "नमस्ते — म SATHI हुँ। कुनै खोला/नदीको अवस्था, चेतावनी, नेपालको कुनै ठाउँको मौसम, ताजा समाचार वा FloodSafe को data बारे सोध्नुहोस्।");
        box.addView(answer, new LinearLayout.LayoutParams(-1, -2));

        EditText input = new EditText(activity);
        input.setSingleLine(false);
        input.setMaxLines(3);
        input.setTextSize(16f);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        input.setImeOptions(EditorInfo.IME_ACTION_SEND);
        input.setHint(english ? "e.g. Ninda Khola status / Kathmandu weather" : "जस्तै: Ninda khola status / Kathmandu ko mausam");
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(-1, -2);
        ip.setMargins(0, dp(activity, 13), 0, dp(activity, 9));
        box.addView(input, ip);

        LinearLayout row = new LinearLayout(activity);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        Button mic = new Button(activity);
        mic.setAllCaps(false);
        mic.setText(english ? "🎙 Voice" : "🎙 आवाज");
        Button ask = new Button(activity);
        ask.setAllCaps(false);
        ask.setText(english ? "Ask SATHI" : "SATHI लाई सोध्नुहोस्");
        row.addView(mic, new LinearLayout.LayoutParams(0, dp(activity, 50), 0.38f));
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(0, dp(activity, 50), 0.62f);
        ap.setMargins(dp(activity, 8), 0, 0, 0);
        row.addView(ask, ap);
        box.addView(row);

        SathiSession session = new SathiSession(activity, answer, input, english);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("🤖 SATHI AI • live app data")
                .setView(box)
                .setNegativeButton(english ? "Close" : "बन्द", null)
                .create();
        ask.setOnClickListener(v -> session.askTyped());
        mic.setOnClickListener(v -> session.listen());
        input.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                session.askTyped();
                return true;
            }
            return false;
        });
        dialog.setOnDismissListener(d -> session.close());
        dialog.show();
    }

    private static boolean isEnglish(Activity activity) {
        return activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("lang_en", false);
    }

    private static final class SathiSession {
        final Activity activity;
        final TextView output;
        final EditText input;
        final boolean english;
        TextToSpeech tts;
        SpeechRecognizer speech;
        volatile boolean closed;

        SathiSession(Activity activity, TextView output, EditText input, boolean english) {
            this.activity = activity;
            this.output = output;
            this.input = input;
            this.english = english;
            tts = new TextToSpeech(activity.getApplicationContext(), status -> {
                if (status != TextToSpeech.SUCCESS || tts == null) return;
                Locale locale = english ? Locale.UK : Locale.forLanguageTag("ne-NP");
                int result = tts.setLanguage(locale);
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts.setLanguage(english ? Locale.UK : new Locale("ne"));
                }
                tts.setSpeechRate(0.93f);
                tts.setPitch(1.02f);
            });
        }

        void askTyped() {
            String q = input.getText() == null ? "" : input.getText().toString().trim();
            if (q.isEmpty()) return;
            input.setText("");
            ask(q);
        }

        void ask(String q) {
            output.setText((english ? "You: " : "तपाईं: ") + q + "\n\n" +
                    (english ? "SATHI: Checking the live app data…" : "SATHI: app को live data हेर्दैछु…"));
            IO.execute(() -> {
                String a;
                try { a = answerQuestion(activity, q, english); }
                catch (Exception e) {
                    a = english
                            ? "I could not refresh that data just now. I will not guess; please try again in a moment."
                            : "अहिले त्यो data refresh गर्न सकिनँ। म अनुमान गरेर गलत कुरा भन्दिनँ; केही क्षणपछि फेरि सोध्नुहोस्।";
                }
                final String result = a;
                MAIN.post(() -> {
                    if (closed || activity.isFinishing() || activity.isDestroyed()) return;
                    output.setText((english ? "You: " : "तपाईं: ") + q + "\n\nSATHI: " + result);
                    speak(result);
                });
            });
        }

        void listen() {
            if (activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                activity.requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 9182);
                output.setText(english ? "Microphone permission is needed. Allow it, then tap Voice again."
                        : "आवाजबाट सोध्न microphone permission चाहिन्छ। Allow गरेपछि फेरि आवाज थिच्नुहोस्।");
                return;
            }
            if (!SpeechRecognizer.isRecognitionAvailable(activity)) {
                output.setText(english ? "Voice recognition is not available on this phone. You can type your question."
                        : "यो फोनमा voice recognition उपलब्ध छैन। प्रश्न टाइप गरेर सोध्न सक्नुहुन्छ।");
                return;
            }
            try { if (speech != null) speech.destroy(); } catch (Exception ignored) {}
            speech = SpeechRecognizer.createSpeechRecognizer(activity);
            speech.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle params) { output.setText(english ? "🎙 Listening…" : "🎙 सुन्दैछु…"); }
                @Override public void onBeginningOfSpeech() {}
                @Override public void onRmsChanged(float rmsdB) {}
                @Override public void onBufferReceived(byte[] buffer) {}
                @Override public void onEndOfSpeech() {}
                @Override public void onError(int error) { output.setText(english ? "I couldn't understand that. Try once more." : "आवाज बुझ्न सकिनँ। फेरि प्रयास गर्नुहोस्।"); }
                @Override public void onResults(Bundle results) {
                    ArrayList<String> list = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (list == null || list.isEmpty()) return;
                    ask(list.get(0));
                }
                @Override public void onPartialResults(Bundle partialResults) {}
                @Override public void onEvent(int eventType, Bundle params) {}
            });
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE, english ? "en-GB" : "ne-NP")
                    .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
            speech.startListening(intent);
        }

        void speak(String text) {
            if (tts == null || text == null || text.trim().isEmpty()) return;
            String clean = text.replace('•', ' ').replace('🔴', ' ').replace('🟠', ' ')
                    .replace('🟡', ' ').replace('🔵', ' ').replace('⚪', ' ')
                    .replace('🌧', ' ').replace('☁', ' ').replace('⚠', ' ')
                    .replaceAll("\\s+", " ").trim();
            try { tts.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "sathi-v0918"); } catch (Exception ignored) {}
        }

        void close() {
            closed = true;
            try { if (speech != null) speech.destroy(); } catch (Exception ignored) {}
            try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception ignored) {}
        }
    }

    private static String answerQuestion(Activity activity, String raw, boolean english) throws Exception {
        String q = normalize(raw);
        if (q.isEmpty()) return english ? "Ask me a FloodSafe question." : "FloodSafe सम्बन्धी प्रश्न सोध्नुहोस्।";

        if (containsAny(q, "weather", "mausam", "मौसम", "temperature", "temp", "rain in", "पानी पर्छ", "वर्षा")) {
            return weatherAnswer(activity, raw, english);
        }
        if (containsAny(q, "news", "samachar", "समाचार", "खबर", "khabar", "latest story", "latest update")) {
            return newsAnswer(english);
        }
        if (containsAny(q, "river", "khola", "nadi", "नदी", "खोला", "जलस्तर", "water level", "flood", "बाढी",
                "warning", "danger", "चेतावनी", "खतरा", "station", "gauge")) {
            return riverAnswer(activity, raw, english);
        }
        if (containsAny(q, "near me", "nearby", "najik", "नजिक")) return riverAnswer(activity, "nearby river", english);
        if (containsAny(q, "notification", "alert", "push", "2 km", "2km")) {
            return english
                    ? "FloodSafe only sends the emergency river alert for a fresh, verified Warning or Danger gauge within 2 km in Nepal. Weather notifications are separate from that river safety rule."
                    : "FloodSafe ले नेपालभित्र ताजा र verified Warning/Danger station २ km भित्र परेमा मात्र emergency river alert दिन्छ। मौसम notification त्यसबाट छुट्टै हुन्छ।";
        }
        if (containsAny(q, "map", "नक्सा", "naksa")) {
            return english
                    ? "The river map uses the app's official BIPAD/DHM station feed and named river geometry. Tap a station for its measured level, status and official time. I do not replace or estimate missing station data."
                    : "River map मा app कै official BIPAD/DHM station feed र named river geometry प्रयोग हुन्छ। Station थिच्दा measured level, status र official time देखिन्छ। data नभएको ठाउँमा म अनुमान गर्दिनँ।";
        }
        if (containsAny(q, "location", "gps", "स्थान", "ठेगाना", "where am i")) {
            double lat = prefDouble(activity, "lat"), lon = prefDouble(activity, "lon");
            if (valid(lat, lon)) return english
                    ? String.format(Locale.UK, "Your current FloodSafe monitoring coordinate is %.4f, %.4f. I use it for local weather and nearby verified river risk.", lat, lon)
                    : String.format(Locale.US, "FloodSafe मा अहिलेको monitoring coordinate %.4f, %.4f छ। यसलाई स्थानीय मौसम र नजिकको verified river risk मिलाउन प्रयोग हुन्छ।", lat, lon);
            return english ? "FloodSafe does not currently have a fresh monitoring location. Use My current location first."
                    : "FloodSafe मा अहिले fresh monitoring location छैन। पहिले My current location प्रयोग गर्नुहोस्।";
        }
        if (containsAny(q, "what can you", "what do you", "help", "sathi", "app", "floodsafe", "के गर्न", "के गर्छ", "k garna", "k garxa")) {
            return english
                    ? "I can answer from FloodSafe's live app data: a named river or district status, Warning/Danger lists, nearby stations, current station freshness, weather for a Nepal place such as Kathmandu, latest app news, GPS/location rules, alerts and map/app features. Type or speak naturally; I will also read my answer aloud."
                    : "म FloodSafe को live app data बाट नामै लिएर नदी/खोलाको status, जिल्लाको station अवस्था, Warning/Danger, नजिकका station, data freshness, Kathmandu जस्ता नेपालको ठाउँको मौसम, ताजा app समाचार, GPS/alert/map सम्बन्धी कुरा बताउन सक्छु। टाइप वा आवाजमा सोध्नुस्; उत्तर म बोल्छु पनि।";
        }
        return english
                ? "Ask me naturally about any FloodSafe data shown in the app — for example: “Ninda Khola status”, “rivers in Jhapa”, “Kathmandu weather”, “latest news”, “which rivers are in warning?”, or “what does the 2 km alert mean?”. I will use current app/official data and will not invent a reading that is missing."
                : "FloodSafe मा देखिने data बारे सामान्य तरिकाले सोध्नुस् — जस्तै “Ninda khola status”, “Jhapa ko river status”, “Kathmandu ko mausam”, “aile samachar k cha”, “kun khola warning ma cha?” वा “2 km alert k ho?”। म app/official data बाट उत्तर दिन्छु; reading नभए बनाउँदिनँ।";
    }

    private static String weatherAnswer(Activity activity, String raw, boolean english) throws Exception {
        String place = extractWeatherPlace(raw);
        double lat, lon;
        String label;
        if (place.isEmpty() || isCurrentPlaceWord(place)) {
            lat = prefDouble(activity, "lat");
            lon = prefDouble(activity, "lon");
            if (!valid(lat, lon)) return english ? "I need a current Nepal monitoring location for local weather. Tap My current location, or ask for a named place such as Kathmandu weather."
                    : "स्थानीय मौसमका लागि current Nepal monitoring location चाहिन्छ। My current location थिच्नुहोस्, वा “Kathmandu ko mausam” जस्तो ठाउँको नाम लिएर सोध्नुहोस्।";
            label = english ? "your monitoring location" : "तपाईंको monitoring location";
        } else {
            Geo g = geocodeNepal(place);
            if (g == null) return english ? "I could not verify that place inside Nepal, so I will not guess its weather. Try the municipality/district name."
                    : "त्यो ठाउँ नेपालभित्र verify गर्न सकिनँ, त्यसैले मौसम अनुमान गरेर भन्दिनँ। Municipality वा district को नामले फेरि सोध्नुहोस्।";
            lat = g.lat; lon = g.lon; label = g.name;
        }
        String u = String.format(Locale.US,
                "https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&forecast_days=1&timezone=Asia%%2FKathmandu",
                lat, lon);
        JSONObject j = getJson(u).optJSONObject("current");
        if (j == null) throw new IllegalStateException("weather missing");
        double t = j.optDouble("temperature_2m", Double.NaN);
        double rain = j.optDouble("precipitation", Double.NaN);
        double hum = j.optDouble("relative_humidity_2m", Double.NaN);
        double wind = j.optDouble("wind_speed_10m", Double.NaN);
        int code = j.optInt("weather_code", -1);
        String condition = weatherCode(code, english);
        if (english) return String.format(Locale.UK, "%s: %s, %s°C, rain %.1f mm, humidity %s%%, wind %s km/h. This is the current weather feed, not a river warning.",
                label, condition, fmt0(t), safe1(rain), fmt0(hum), fmt0(wind));
        return String.format(Locale.US, "%s: %s, तापक्रम %s°C, वर्षा %.1f mm, humidity %s%%, हावा %s km/h। यो current weather feed हो, river warning होइन।",
                label, condition, fmt0(t), safe1(rain), fmt0(hum), fmt0(wind));
    }

    private static String newsAnswer(boolean english) throws Exception {
        JSONObject root = getJson(NEWS_ENDPOINT + "?_sathi=" + System.currentTimeMillis());
        JSONArray a = root.optJSONArray("items");
        if (a == null) a = root.optJSONArray("results");
        if (a == null) a = root.optJSONArray("news");
        if (a == null || a.length() == 0) return english ? "The app has no fresh live story in its current news feed right now."
                : "App को current news feed मा अहिले fresh live story भेटिएन।";
        List<String> lines = new ArrayList<>();
        for (int i = 0; i < a.length() && lines.size() < 4; i++) {
            JSONObject o = a.optJSONObject(i);
            if (o == null) continue;
            String title = text(o, "title", "headline");
            String source = text(o, "source", "publisher");
            if (title.isEmpty()) continue;
            lines.add((source.isEmpty() ? "" : source + ": ") + title);
        }
        if (lines.isEmpty()) return english ? "The current app news feed did not return a readable fresh headline."
                : "App को current news feed बाट readable fresh headline आएन।";
        StringBuilder b = new StringBuilder(english ? "Latest stories in the FloodSafe feed: " : "FloodSafe feed का ताजा समाचार: ");
        for (int i = 0; i < lines.size(); i++) {
            if (i > 0) b.append(" • ");
            b.append(i + 1).append(". ").append(lines.get(i));
        }
        return b.toString();
    }

    private static String riverAnswer(Activity activity, String raw, boolean english) throws Exception {
        List<Station> rows = rivers();
        if (rows.isEmpty()) return english ? "The official river feed did not return a usable station reading right now. I will not substitute a fake status."
                : "Official river feed बाट अहिले usable station reading आएन। म त्यसको सट्टा fake status बनाउँदिनँ।";
        String q = normalize(raw);

        if (containsAny(q, "nearby", "near me", "najik", "नजिक")) {
            double lat = prefDouble(activity, "lat"), lon = prefDouble(activity, "lon");
            if (!valid(lat, lon)) return english ? "Set a current Nepal location first so I can rank nearby official river stations."
                    : "नजिकको official river station बताउन पहिले current Nepal location सेट गर्नुहोस्।";
            List<Station> copy = new ArrayList<>(rows);
            copy.sort(Comparator.comparingDouble(s -> distanceKm(lat, lon, s.lat, s.lon)));
            StringBuilder b = new StringBuilder(english ? "Nearest official stations: " : "नजिकका official station: ");
            for (int i = 0; i < Math.min(3, copy.size()); i++) {
                Station s = copy.get(i);
                if (i > 0) b.append(" • ");
                b.append(s.name).append(" — ").append(stageName(s.stage, english)).append(", ")
                        .append(String.format(Locale.US, "%.1f km", distanceKm(lat, lon, s.lat, s.lon)));
            }
            return b.toString();
        }

        if (containsAny(q, "which", "kun", "कुन", "all warning", "all danger", "warning ma", "danger ma", "चेतावनीमा", "खतरामा")) {
            List<Station> risky = new ArrayList<>();
            for (Station s : rows) if (s.fresh && (s.stage.equals("danger") || s.stage.equals("warning") || s.stage.equals("alert"))) risky.add(s);
            risky.sort(Comparator.comparingInt(s -> rank(s.stage)));
            if (risky.isEmpty()) return english ? "In the current fresh official feed I do not see a station at Alert, Warning or Danger."
                    : "अहिलेको fresh official feed मा Alert, Warning वा Danger मा पुगेको station देखिएन।";
            StringBuilder b = new StringBuilder(english ? "Current risk stations: " : "अहिले risk मा रहेका station: ");
            for (int i = 0; i < Math.min(8, risky.size()); i++) {
                if (i > 0) b.append(" • ");
                Station s = risky.get(i);
                b.append(s.name).append(" — ").append(stageName(s.stage, english));
            }
            return b.toString();
        }

        String target = extractRiverTarget(raw);
        Station best = null;
        int bestScore = 0;
        for (Station s : rows) {
            int score = matchScore(q, target, s);
            if (score > bestScore) { bestScore = score; best = s; }
        }
        if (best != null && bestScore >= 18) return formatStation(best, english);

        // District fallback: “Jhapa khola status” should summarize verified Jhapa stations,
        // without pretending that “Jhapa” itself is a station name.
        List<Station> district = new ArrayList<>();
        for (Station s : rows) {
            String d = normalize(s.district);
            if (!d.isEmpty() && (q.contains(d) || (!target.isEmpty() && d.contains(target)))) district.add(s);
        }
        if (!district.isEmpty()) {
            district.sort(Comparator.comparingInt(s -> rank(s.stage)));
            String dname = district.get(0).district;
            StringBuilder b = new StringBuilder(english ? "Official stations in " + dname + ": " : dname + " का official station: ");
            for (int i = 0; i < Math.min(6, district.size()); i++) {
                if (i > 0) b.append(" • ");
                Station s = district.get(i);
                b.append(s.name).append(" — ").append(stageName(s.stage, english));
                if (Double.isFinite(s.level)) b.append(" ").append(String.format(Locale.US, "%.2f m", s.level));
            }
            return b.toString();
        }

        return english
                ? "I could not match that river/station to a verified reading in the current app feed. Try the official station/river name; I will not answer with a different river."
                : "Current app feed मा त्यो नदी/खोलालाई verified reading सँग match गर्न सकिनँ। Official station/river name ले फेरि सोध्नुहोस्; म अर्को खोलाको data मिसाएर उत्तर दिँदिनँ।";
    }

    private static int matchScore(String q, String target, Station s) {
        String n = normalize(s.name), d = normalize(s.district);
        if (n.isEmpty()) return 0;
        if (q.contains(n)) return 120 + n.length();
        if (!target.isEmpty() && n.contains(target)) return 90 + target.length();
        String compactName = stripRiverWords(n), compactTarget = stripRiverWords(target);
        if (!compactTarget.isEmpty() && compactName.contains(compactTarget)) return 75 + compactTarget.length();
        int score = 0;
        for (String tok : compactTarget.split(" ")) {
            if (tok.length() < 3) continue;
            if (compactName.contains(tok)) score += 18;
            if (!d.isEmpty() && d.contains(tok)) score += 4;
        }
        return score;
    }

    private static String formatStation(Station s, boolean english) {
        StringBuilder b = new StringBuilder();
        b.append(s.name);
        if (!s.district.isEmpty()) b.append(" (").append(s.district).append(")");
        b.append(" — ").append(stageName(s.stage, english)).append(". ");
        if (!s.fresh) {
            b.append(english ? "The measurement is stale/unknown, so I am not calling it live."
                    : "यो measurement stale/unknown छ, त्यसैले म यसलाई live भन्दिनँ।");
            return b.toString();
        }
        if (Double.isFinite(s.level)) b.append(english ? "Level " : "जलस्तर ").append(String.format(Locale.US, "%.2f m. ", s.level));
        if (Double.isFinite(s.warning)) b.append(english ? "Warning " : "Warning तह ").append(String.format(Locale.US, "%.2f m. ", s.warning));
        if (Double.isFinite(s.danger)) b.append(english ? "Danger " : "Danger तह ").append(String.format(Locale.US, "%.2f m. ", s.danger));
        if (s.at > 0) b.append(english ? "Official measurement " : "Official measurement ").append(timeText(s.at)).append(". ");
        if (s.stage.equals("danger")) b.append(english ? "Danger is active: stay away from the river edge and follow local official instructions."
                : "Danger active छ: नदी/खोला किनारबाट टाढा रहनुहोस् र स्थानीय official निर्देशन पालना गर्नुहोस्।");
        else if (s.stage.equals("warning")) b.append(english ? "Warning is active: stay alert and be ready to move to a safer place."
                : "Warning active छ: सतर्क रहनुहोस् र सुरक्षित ठाउँतर्फ जान तयार रहनुहोस्।");
        return b.toString().trim();
    }

    private static List<Station> rivers() throws Exception {
        long now = System.currentTimeMillis();
        synchronized (CACHE_LOCK) {
            if (!riverCache.isEmpty() && now - riverCacheAt < CACHE_MS) return new ArrayList<>(riverCache);
        }
        JSONObject root = getJson(RIVER_ENDPOINT + "?_sathi=" + now);
        JSONArray a = root.optJSONArray("results");
        if (a == null) a = root.optJSONArray("data");
        if (a == null) a = root.optJSONArray("stations");
        if (a == null) a = new JSONArray();
        List<Station> out = new ArrayList<>();
        for (int i = 0; i < a.length(); i++) {
            JSONObject r = a.optJSONObject(i);
            if (r == null) continue;
            double lat = number(r, "latitude", "lat", "stationLatitude", "station_latitude");
            double lon = number(r, "longitude", "lon", "lng", "stationLongitude", "station_longitude");
            if (!valid(lat, lon)) continue;
            double level = number(r, "waterLevel", "water_level", "currentWaterLevel", "current_water_level", "currentLevel", "current_level", "_lastWaterLevel");
            double warning = number(r, "warningLevel", "warning_level", "warningThreshold", "warning_threshold", "_lastWarningLevel");
            double danger = number(r, "dangerLevel", "danger_level", "dangerThreshold", "danger_threshold", "_lastDangerLevel");
            long at = parseTime(text(r, "waterLevelOn", "water_level_on", "measuredOn", "measured_on", "measurementTime", "measurement_time", "observationTime", "observation_time", "observedAt", "observed_at", "datetime", "timestamp", "_measurementTime"));
            boolean fresh = at > 0 && now - at <= RIVER_FRESH_MS && at - now <= 5L * 60L * 1000L;
            String raw = text(r, "status", "status_name", "alertStatus", "alert_status", "riskLevel", "risk_level", "_officialStatus").toUpperCase(Locale.ROOT);
            String stage = "unknown";
            if (fresh) {
                if ((Double.isFinite(level) && Double.isFinite(danger) && danger > 0 && level >= danger) || (raw.contains("DANGER") && !raw.contains("BELOW DANGER")) || raw.contains("RED")) stage = "danger";
                else if ((Double.isFinite(level) && Double.isFinite(warning) && warning > 0 && level >= warning) || (raw.contains("WARNING") && !raw.contains("BELOW WARNING")) || raw.contains("ORANGE")) stage = "warning";
                else if ((Double.isFinite(level) && Double.isFinite(warning) && warning > 0 && level >= warning * .8) || raw.contains("ALERT") || raw.contains("WATCH") || raw.contains("YELLOW")) stage = "alert";
                else if (Double.isFinite(level) || raw.contains("NORMAL") || raw.contains("BLUE")) stage = "normal";
            }
            String name = text(r, "river_name", "riverName", "station_name", "stationName", "title", "name");
            if (name.isEmpty()) name = "Official river station";
            out.add(new Station(name, text(r, "districtName", "district_name", "district"), lat, lon, level, warning, danger, at, fresh, stage));
        }
        synchronized (CACHE_LOCK) {
            riverCache = new ArrayList<>(out);
            riverCacheAt = now;
        }
        return out;
    }

    private static Geo geocodeNepal(String query) throws Exception {
        String q = query.trim();
        if (q.equalsIgnoreCase("kathmandu") || q.equals("काठमाडौं")) return new Geo("Kathmandu", 27.7172, 85.3240);
        if (q.equalsIgnoreCase("pokhara") || q.equals("पोखरा")) return new Geo("Pokhara", 28.2096, 83.9856);
        String u = "https://geocoding-api.open-meteo.com/v1/search?name=" + URLEncoder.encode(q, StandardCharsets.UTF_8.name()) + "&count=10&language=en&format=json";
        JSONArray a = getJson(u).optJSONArray("results");
        if (a == null) return null;
        for (int i = 0; i < a.length(); i++) {
            JSONObject o = a.optJSONObject(i);
            if (o == null) continue;
            String cc = o.optString("country_code", "");
            double lat = o.optDouble("latitude", Double.NaN), lon = o.optDouble("longitude", Double.NaN);
            if ((cc.equalsIgnoreCase("NP") || o.optString("country", "").equalsIgnoreCase("Nepal")) && valid(lat, lon)) {
                String name = o.optString("name", q);
                String admin = o.optString("admin1", "");
                if (!admin.isEmpty() && !admin.equalsIgnoreCase(name)) name += ", " + admin;
                return new Geo(name, lat, lon);
            }
        }
        return null;
    }

    private static String extractWeatherPlace(String raw) {
        String s = normalize(raw);
        String[] remove = {"weather", "mausam", "मौसम", "temperature", "temp", "rain", "वर्षा", "पानी", "ko", "को", "ma", "मा", "kasto", "कस्तो", "cha", "xa", "chha", "छ", "ahile", "aile", "अहिले", "today", "now", "please", "bhana", "भन"};
        for (String x : remove) s = tokenRemove(s, x);
        return s.replaceAll("\\s+", " ").trim();
    }

    private static String extractRiverTarget(String raw) {
        String s = normalize(raw);
        String[] remove = {"river", "khola", "nadi", "नदी", "खोला", "station", "gauge", "status", "level", "water", "जलस्तर", "flood", "बाढी", "warning", "danger", "alert", "चेतावनी", "खतरा", "ko", "को", "ma", "मा", "k", "ke", "के", "kasto", "कस्तो", "cha", "xa", "chha", "छ", "ahile", "aile", "अहिले", "please", "bhana", "भन"};
        for (String x : remove) s = tokenRemove(s, x);
        return s.replaceAll("\\s+", " ").trim();
    }

    private static String stripRiverWords(String s) {
        if (s == null) return "";
        String x = normalize(s);
        String[] words = {"river", "khola", "nadi", "नदी", "खोला", "station", "gauge"};
        for (String w : words) x = tokenRemove(x, w);
        return x.replaceAll("\\s+", " ").trim();
    }

    private static String tokenRemove(String source, String token) {
        return (" " + source + " ").replace(" " + token + " ", " ").trim();
    }

    private static boolean isCurrentPlaceWord(String s) {
        String q = normalize(s);
        return q.isEmpty() || containsAny(q, "my", "current", "here", "mero", "yaha", "यहाँ", "मेरो");
    }

    private static double prefDouble(Activity activity, String key) {
        long raw = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getLong(key, Double.doubleToRawLongBits(Double.NaN));
        return Double.longBitsToDouble(raw);
    }

    private static String weatherCode(int c, boolean en) {
        if (c == 0) return en ? "clear" : "सफा";
        if (c == 1 || c == 2 || c == 3) return en ? "cloudy" : "बादल";
        if (c == 45 || c == 48) return en ? "foggy" : "कुहिरो";
        if ((c >= 51 && c <= 67) || (c >= 80 && c <= 82)) return en ? "rain" : "वर्षा";
        if (c >= 71 && c <= 77) return en ? "snow" : "हिउँ";
        if (c >= 95) return en ? "thunderstorm" : "मेघगर्जन";
        return en ? "current conditions" : "हालको मौसम";
    }

    private static String stageName(String s, boolean en) {
        switch (s) {
            case "danger": return en ? "DANGER" : "खतरा";
            case "warning": return en ? "WARNING" : "चेतावनी";
            case "alert": return en ? "ALERT" : "सतर्क";
            case "normal": return en ? "NORMAL" : "सामान्य";
            default: return en ? "STALE/UNKNOWN" : "stale/unknown";
        }
    }

    private static int rank(String s) {
        if ("danger".equals(s)) return 0;
        if ("warning".equals(s)) return 1;
        if ("alert".equals(s)) return 2;
        if ("normal".equals(s)) return 3;
        return 4;
    }

    private static String timeText(long at) {
        try {
            return DateTimeFormatter.ofPattern("HH:mm 'NPT'")
                    .withZone(ZoneId.of("Asia/Kathmandu"))
                    .format(Instant.ofEpochMilli(at));
        } catch (Exception e) { return new Date(at).toString(); }
    }

    private static long parseTime(String value) {
        if (value == null || value.trim().isEmpty()) return 0L;
        String s = value.trim();
        try { return Long.parseLong(s.length() <= 10 ? s) * (s.length() <= 10 ? 1000L : 1L); } catch (Exception ignored) {}
        try { return Instant.parse(s).toEpochMilli(); } catch (Exception ignored) {}
        try { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return LocalDateTime.parse(s).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        return 0L;
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(14_000);
        c.setReadTimeout(20_000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static String text(JSONObject o, String... keys) {
        for (String k : keys) {
            Object v = o.opt(k);
            if (v != null && v != JSONObject.NULL && !String.valueOf(v).trim().isEmpty()) return String.valueOf(v).trim();
        }
        return "";
    }

    private static double number(JSONObject o, String... keys) {
        for (String k : keys) {
            Object v = o.opt(k);
            if (v == null || v == JSONObject.NULL) continue;
            try {
                double n = Double.parseDouble(String.valueOf(v).replace(",", "").trim());
                if (Double.isFinite(n)) return n;
            } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    private static String normalize(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT).replaceAll("[?!.:,;()\\[\\]{}\"'`]", " ")
                .replaceAll("\\s+", " ").trim();
    }

    private static boolean containsAny(String q, String... values) {
        for (String v : values) if (q.contains(v)) return true;
        return false;
    }

    private static boolean valid(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon) && lat >= 26.2 && lat <= 30.5 && lon >= 80.0 && lon <= 88.35;
    }

    private static double distanceKm(double lat1, double lon1, double lat2, double lon2) {
        double r = 6371.0, dLat = Math.toRadians(lat2 - lat1), dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return 2 * r * Math.asin(Math.sqrt(a));
    }

    private static String fmt0(double n) { return Double.isFinite(n) ? String.valueOf(Math.round(n)) : "—"; }
    private static double safe1(double n) { return Double.isFinite(n) ? n : 0d; }
    private static int dp(Context c, int v) { return Math.round(v * c.getResources().getDisplayMetrics().density); }

    private static final class Station {
        final String name, district, stage;
        final double lat, lon, level, warning, danger;
        final long at;
        final boolean fresh;
        Station(String name, String district, double lat, double lon, double level, double warning, double danger, long at, boolean fresh, String stage) {
            this.name = name; this.district = district; this.lat = lat; this.lon = lon;
            this.level = level; this.warning = warning; this.danger = danger; this.at = at; this.fresh = fresh; this.stage = stage;
        }
    }

    private static final class Geo {
        final String name; final double lat, lon;
        Geo(String name, double lat, double lon) { this.name = name; this.lat = lat; this.lon = lon; }
    }

    /** Lightweight animated cloud icon; no map or river layer is modified. */
    private static final class CloudDrawable extends Drawable {
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final ValueAnimator animator;
        float phase;
        CloudDrawable(Context context) {
            paint.setColor(Color.WHITE);
            paint.setShadowLayer(dp(context, 3), 0, dp(context, 2), 0x33000000);
            animator = ValueAnimator.ofFloat(0f, 1f);
            animator.setDuration(2400L);
            animator.setRepeatCount(ValueAnimator.INFINITE);
            animator.setRepeatMode(ValueAnimator.REVERSE);
            animator.addUpdateListener(a -> { phase = (float) a.getAnimatedValue(); invalidateSelf(); });
        }
        void start() { if (!animator.isStarted()) animator.start(); }
        @Override public void draw(Canvas canvas) {
            android.graphics.Rect b = getBounds();
            float w = b.width(), h = b.height();
            float dx = (phase - .5f) * w * .08f;
            float y = h * (.60f - phase * .03f);
            canvas.save();
            canvas.translate(b.left + dx, b.top);
            canvas.drawOval(new RectF(w*.16f, y-h*.19f, w*.84f, y+h*.18f), paint);
            canvas.drawCircle(w*.38f, y-h*.16f, h*.25f, paint);
            canvas.drawCircle(w*.57f, y-h*.23f, h*.31f, paint);
            canvas.drawCircle(w*.70f, y-h*.10f, h*.21f, paint);
            canvas.restore();
        }
        @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(android.graphics.ColorFilter colorFilter) { paint.setColorFilter(colorFilter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
        @Override public int getIntrinsicWidth() { return getBounds().width(); }
        @Override public int getIntrinsicHeight() { return getBounds().height(); }
    }
}
