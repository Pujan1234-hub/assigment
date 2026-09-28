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
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.WeakHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * SATHI v0.9.18 overlay.
 * IMPORTANT: this class never reads, writes, replaces, redraws or filters the map.
 * FloodSafeNativeMapView and all river-map code remain owned by NativeFullActivity.
 */
final class SathiNextLevelV0918 {
    private static final String PREFS = "floodsafe-native-full";
    private static final String RIVER = "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String NEWS = "https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three";
    private static final long FRESH_MS = 10L * 60L * 1000L;
    private static final long CACHE_MS = 45_000L;
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final ExecutorService IO = Executors.newFixedThreadPool(3);
    private static final WeakHashMap<View, Boolean> PATCHED = new WeakHashMap<>();
    private static final WeakHashMap<TextView, CloudDrawable> CLOUDS = new WeakHashMap<>();
    private static final Object CACHE_LOCK = new Object();
    private static List<Station> stationCache = new ArrayList<>();
    private static long stationCacheAt;
    private static boolean installed;

    private SathiNextLevelV0918() {}

    static synchronized void install(Context context) {
        if (installed || context == null) return;
        Context app = context.getApplicationContext();
        if (!(app instanceof Application)) return;
        installed = true;
        ((Application) app).registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override public void onActivityCreated(Activity a, Bundle b) {}
            @Override public void onActivityStarted(Activity a) {}
            @Override public void onActivityResumed(Activity a) {
                if (!isTarget(a)) return;
                MAIN.postDelayed(() -> patchUi(a), 250L);
                MAIN.postDelayed(() -> patchUi(a), 900L);
            }
            @Override public void onActivityPaused(Activity a) {}
            @Override public void onActivityStopped(Activity a) {}
            @Override public void onActivitySaveInstanceState(Activity a, Bundle b) {}
            @Override public void onActivityDestroyed(Activity a) {}
        });
    }

    private static boolean isTarget(Activity a) {
        return a != null && a.getClass().getName().endsWith(".NativeFullActivity");
    }

    private static void patchUi(Activity a) {
        if (a == null || a.isFinishing() || a.isDestroyed() || a.getWindow() == null) return;
        List<TextView> all = new ArrayList<>();
        collect(a.getWindow().getDecorView(), all);
        for (TextView v : all) {
            String text = String.valueOf(v.getText()).toUpperCase(Locale.ROOT);
            if (text.contains("SATHI") && v.isClickable()) {
                synchronized (PATCHED) {
                    if (Boolean.TRUE.equals(PATCHED.get(v))) continue;
                    PATCHED.put(v, true);
                }
                v.setOnClickListener(x -> show(a));
            }
        }
        hideOnlyDuplicateLanguageControl(all);
        addCloudAnimationOnlyToWeatherLabel(all);
    }

    private static void collect(View v, List<TextView> out) {
        if (v instanceof TextView) out.add((TextView) v);
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) collect(g.getChildAt(i), out);
        }
    }

    private static void hideOnlyDuplicateLanguageControl(List<TextView> all) {
        List<TextView> candidates = new ArrayList<>();
        for (TextView v : all) {
            if (v.getVisibility() != View.VISIBLE || !v.isClickable()) continue;
            String s = norm(String.valueOf(v.getText()));
            if (s.equals("english") || s.equals("nepali") || s.contains("नेपाली") ||
                    s.contains("अङ्ग्रेजी") || s.contains("अंग्रेजी")) candidates.add(v);
        }
        if (candidates.size() < 2) return;
        candidates.sort(Comparator.comparingInt(SathiNextLevelV0918::screenY));
        int top = screenY(candidates.get(0));
        for (int i = 1; i < candidates.size(); i++) {
            TextView v = candidates.get(i);
            if (screenY(v) > top + dp(v.getContext(), 28)) v.setVisibility(View.GONE);
        }
    }

    private static int screenY(View v) {
        int[] p = new int[]{0, 0};
        try { v.getLocationOnScreen(p); } catch (Exception ignored) {}
        return p[1];
    }

    private static void addCloudAnimationOnlyToWeatherLabel(List<TextView> all) {
        for (TextView v : all) {
            if (v.getVisibility() != View.VISIBLE) continue;
            String s = norm(String.valueOf(v.getText()));
            if (!(s.contains("cloud") || s.contains("overcast") || s.contains("बादल") || s.contains("मेघाच्छन्न"))) continue;
            synchronized (CLOUDS) {
                if (CLOUDS.containsKey(v)) return;
                CloudDrawable d = new CloudDrawable(v.getContext());
                d.setBounds(0, 0, dp(v.getContext(), 48), dp(v.getContext(), 30));
                v.setCompoundDrawablePadding(dp(v.getContext(), 8));
                v.setCompoundDrawables(d, null, null, null);
                CLOUDS.put(v, d);
                d.start();
            }
            return;
        }
    }

    private static void show(Activity a) {
        boolean en = english(a);
        LinearLayout box = new LinearLayout(a);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(a, 18), dp(a, 6), dp(a, 18), 0);

        TextView out = new TextView(a);
        out.setTextSize(15f);
        out.setTextColor(Color.rgb(25, 51, 75));
        out.setLineSpacing(0f, 1.12f);
        out.setText(en
                ? "Hi — I’m SATHI. Ask me about a named river, current warnings, nearby stations, Nepal weather, current news or FloodSafe features."
                : "नमस्ते — म SATHI हुँ। कुनै खोला/नदी, अहिलेको warning/danger, नजिकको station, नेपालको मौसम, ताजा समाचार वा FloodSafe बारे सोध्नुहोस्।");
        box.addView(out);

        EditText input = new EditText(a);
        input.setTextSize(16f);
        input.setMaxLines(3);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        input.setImeOptions(EditorInfo.IME_ACTION_SEND);
        input.setHint(en ? "Ninda Khola status / Kathmandu weather" : "Ninda khola status / Kathmandu ko mausam");
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(-1, -2);
        ip.setMargins(0, dp(a, 13), 0, dp(a, 9));
        box.addView(input, ip);

        LinearLayout row = new LinearLayout(a);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        Button mic = new Button(a);
        mic.setAllCaps(false);
        mic.setText(en ? "🎙 Voice" : "🎙 आवाज");
        Button ask = new Button(a);
        ask.setAllCaps(false);
        ask.setText(en ? "Ask SATHI" : "SATHI लाई सोध्नुहोस्");
        row.addView(mic, new LinearLayout.LayoutParams(0, dp(a, 50), .38f));
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(0, dp(a, 50), .62f);
        ap.setMargins(dp(a, 8), 0, 0, 0);
        row.addView(ask, ap);
        box.addView(row);

        Session session = new Session(a, out, input, en);
        AlertDialog dialog = new AlertDialog.Builder(a)
                .setTitle("🤖 SATHI AI • live app data")
                .setView(box)
                .setNegativeButton(en ? "Close" : "बन्द", null)
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
        dialog.setOnDismissListener(v -> session.close());
        dialog.show();
    }

    private static boolean english(Activity a) {
        return a.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("lang_en", false);
    }

    private static final class Session {
        final Activity activity;
        final TextView output;
        final EditText input;
        final boolean en;
        TextToSpeech tts;
        SpeechRecognizer recognizer;
        boolean closed;
        String lastQuestion = "";

        Session(Activity a, TextView output, EditText input, boolean en) {
            this.activity = a;
            this.output = output;
            this.input = input;
            this.en = en;
            tts = new TextToSpeech(a.getApplicationContext(), status -> {
                if (status != TextToSpeech.SUCCESS || tts == null) return;
                Locale locale = en ? Locale.UK : Locale.forLanguageTag("ne-NP");
                int result = tts.setLanguage(locale);
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED)
                    tts.setLanguage(en ? Locale.UK : new Locale("ne"));
                tts.setSpeechRate(.93f);
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
            String expanded = expandFollowUp(q, lastQuestion);
            lastQuestion = expanded;
            output.setText((en ? "You: " : "तपाईं: ") + q + "\n\nSATHI: " +
                    (en ? "Checking live app data…" : "live app data हेर्दैछु…"));
            IO.execute(() -> {
                String answer;
                try {
                    answer = answer(activity, expanded, en);
                } catch (Exception e) {
                    answer = en
                            ? "I couldn't refresh that live data just now. I won't guess — please try again in a moment."
                            : "अहिले त्यो live data refresh गर्न सकिनँ। म अनुमान गरेर गलत कुरा भन्दिनँ — केही क्षणपछि फेरि सोध्नुहोस्।";
                }
                String finalAnswer = answer;
                MAIN.post(() -> {
                    if (closed || activity.isFinishing() || activity.isDestroyed()) return;
                    output.setText((en ? "You: " : "तपाईं: ") + q + "\n\nSATHI: " + finalAnswer);
                    speak(finalAnswer);
                });
            });
        }

        void listen() {
            if (activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                activity.requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 9182);
                output.setText(en ? "Allow microphone permission, then tap Voice again." : "Microphone permission Allow गरेपछि फेरि आवाज थिच्नुहोस्।");
                return;
            }
            if (!SpeechRecognizer.isRecognitionAvailable(activity)) {
                output.setText(en ? "Voice recognition is unavailable on this phone. Type your question instead." : "यो फोनमा voice recognition उपलब्ध छैन। प्रश्न टाइप गर्नुहोस्।");
                return;
            }
            try { if (recognizer != null) recognizer.destroy(); } catch (Exception ignored) {}
            recognizer = SpeechRecognizer.createSpeechRecognizer(activity);
            recognizer.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle b) { output.setText(en ? "🎙 Listening…" : "🎙 सुन्दैछु…"); }
                @Override public void onBeginningOfSpeech() {}
                @Override public void onRmsChanged(float rmsdB) {}
                @Override public void onBufferReceived(byte[] buffer) {}
                @Override public void onEndOfSpeech() {}
                @Override public void onPartialResults(Bundle partialResults) {}
                @Override public void onEvent(int eventType, Bundle params) {}
                @Override public void onError(int error) { output.setText(en ? "I couldn't understand that. Try once more." : "आवाज बुझ्न सकिनँ। फेरि प्रयास गर्नुहोस्।"); }
                @Override public void onResults(Bundle results) {
                    ArrayList<String> r = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (r != null && !r.isEmpty()) ask(r.get(0));
                }
            });
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE, en ? "en-GB" : "ne-NP")
                    .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
            recognizer.startListening(i);
        }

        void speak(String text) {
            if (tts == null || text == null || text.trim().isEmpty()) return;
            String clean = text.replace("🔴", " ").replace("🟠", " ").replace("🟡", " ")
                    .replace("🔵", " ").replace("⚪", " ").replace("🌧️", " ").replace("☁️", " ")
                    .replace("⚠️", " ").replace("•", " ").replaceAll("\\s+", " ").trim();
            try { tts.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "sathi-v0918"); } catch (Exception ignored) {}
        }

        void close() {
            closed = true;
            try { if (recognizer != null) recognizer.destroy(); } catch (Exception ignored) {}
            try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception ignored) {}
        }
    }

    private static String expandFollowUp(String q, String previous) {
        String n = norm(q);
        if (previous == null || previous.isEmpty()) return q;
        if (n.contains("kun chai") || n.contains("which one") || n.contains("tesko") || n.contains("त्यसको") ||
                n.equals("warning?") || n.equals("danger?")) return previous + " ; follow-up: " + q;
        return q;
    }

    private static String answer(Activity a, String raw, boolean en) throws Exception {
        String q = norm(raw);
        if (q.isEmpty()) return en ? "Ask me a FloodSafe question." : "FloodSafe सम्बन्धी प्रश्न सोध्नुहोस्।";
        if (any(q, "weather", "mausam", "मौसम", "temperature", "temp", "पानी पर्छ", "वर्षा")) return weather(a, raw, en);
        if (any(q, "river", "khola", "nadi", "नदी", "खोला", "जलस्तर", "water level", "flood", "बाढी", "warning", "danger", "चेतावनी", "खतरा", "station", "gauge", "near me", "nearby", "najik", "नजिक")) return rivers(a, raw, en);
        if (any(q, "news", "samachar", "समाचार", "खबर", "khabar", "headline")) return news(en);
        if (any(q, "notification", "alert", "push", "2 km", "2km"))
            return en ? "FloodSafe sends an emergency river alert only for a fresh, verified Warning or Danger gauge within 2 km in Nepal. Weather notifications are separate from that river safety rule."
                    : "FloodSafe ले नेपालभित्र fresh र verified Warning/Danger station २ km भित्र परेमा मात्र emergency river alert दिन्छ। मौसम notification त्यसबाट छुट्टै हुन्छ।";
        if (any(q, "map", "नक्सा", "naksa"))
            return en ? "The map is the app's existing official BIPAD/DHM river-station map. I only read its live data; I do not alter its river geometry, stations or status colours."
                    : "Map app कै existing official BIPAD/DHM river-station map हो। म live data पढ्छु मात्र; river geometry, station वा status colour बदल्दिनँ।";
        if (any(q, "location", "gps", "स्थान", "where am i")) {
            double lat = pref(a, "lat"), lon = pref(a, "lon");
            if (valid(lat, lon)) return en ? String.format(Locale.UK, "Your FloodSafe monitoring coordinate is %.4f, %.4f. It is used for local weather and nearby verified river risk.", lat, lon)
                    : String.format(Locale.US, "FloodSafe को monitoring coordinate %.4f, %.4f छ। यसैबाट local weather र नजिकको verified river risk मिलाइन्छ।", lat, lon);
            return en ? "I don't have a current saved GPS fix yet. Use ‘My current location’ and allow location permission."
                    : "अहिले current GPS fix save भएको छैन। ‘मेरो हालको स्थान’ थिचेर location permission दिनुहोस्।";
        }
        if (any(q, "what can you do", "help", "के गर्न", "के गर्छ", "sathi"))
            return en ? "I can explain current named-river status, warning/danger gauges, nearby stations, Nepal-place weather, current app news, GPS/alert rules and FloodSafe features — by text or voice."
                    : "म named river को current status, warning/danger gauge, नजिकको station, नेपालको कुनै ठाउँको मौसम, ताजा app news, GPS/alert rule र FloodSafe feature text वा voice मा बताउन सक्छु।";
        return en ? "Ask me about a river or station, warning/danger, Nepal weather, current news, GPS, map or FloodSafe alerts."
                : "नदी/station, warning/danger, नेपालको मौसम, ताजा समाचार, GPS, map वा FloodSafe alert बारे सोध्नुहोस्।";
    }

    private static String weather(Activity a, String raw, boolean en) throws Exception {
        String place = cleanPlace(raw);
        double lat, lon;
        String label;
        if (place.isEmpty() || any(norm(raw), "my weather", "mero mausam", "मेरो मौसम", "near me", "यहाँ")) {
            lat = pref(a, "lat"); lon = pref(a, "lon");
            if (!valid(lat, lon)) return en ? "I need a current GPS fix for your local weather, or tell me a Nepal place such as Kathmandu."
                    : "तपाईंको local weather का लागि current GPS चाहिन्छ, वा Kathmandu जस्तो नेपालको ठाउँको नाम भन्नुहोस्।";
            label = en ? "your location" : "तपाईंको स्थान";
        } else {
            JSONObject geo = getJson("https://geocoding-api.open-meteo.com/v1/search?name=" + URLEncoder.encode(place, StandardCharsets.UTF_8) + "&count=8&language=en&format=json");
            JSONArray results = geo.optJSONArray("results");
            JSONObject match = null;
            if (results != null) for (int i = 0; i < results.length(); i++) {
                JSONObject r = results.optJSONObject(i);
                if (r != null && "NP".equalsIgnoreCase(r.optString("country_code"))) { match = r; break; }
            }
            if (match == null) return en ? "I couldn't verify that as a Nepal place, so I won't guess the weather."
                    : "त्यो ठाउँ नेपालमा verify गर्न सकिनँ, त्यसैले मौसम अनुमान गरेर भन्दिनँ।";
            lat = match.optDouble("latitude", Double.NaN); lon = match.optDouble("longitude", Double.NaN);
            label = match.optString("name", place);
        }
        JSONObject root = getJson(String.format(Locale.US,
                "https://api.open-meteo.com/v1/forecast?latitude=%.5f&longitude=%.5f&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m&timezone=auto", lat, lon));
        JSONObject c = root.optJSONObject("current");
        if (c == null) throw new IllegalStateException("weather current missing");
        double t = c.optDouble("temperature_2m", Double.NaN), feels = c.optDouble("apparent_temperature", Double.NaN);
        double hum = c.optDouble("relative_humidity_2m", Double.NaN), rain = c.optDouble("precipitation", Double.NaN);
        double cloud = c.optDouble("cloud_cover", Double.NaN), wind = c.optDouble("wind_speed_10m", Double.NaN);
        if (en) return String.format(Locale.UK, "%s now: %.1f°C, feels %.1f°C, humidity %.0f%%, precipitation %.1f mm, cloud %.0f%%, wind %.1f km/h.", label, t, feels, hum, rain, cloud, wind);
        return String.format(Locale.US, "%s को अहिलेको मौसम: %.1f°C, feels %.1f°C, humidity %.0f%%, वर्षा %.1f mm, बादल %.0f%%, हावा %.1f km/h।", label, t, feels, hum, rain, cloud, wind);
    }

    private static String rivers(Activity a, String raw, boolean en) throws Exception {
        List<Station> stations = stations();
        if (stations.isEmpty()) return en ? "The official river feed returned no usable stations right now. I won't invent a status."
                : "अहिले official river feed बाट usable station आएन। म status बनाएर भन्दिनँ।";
        String q = norm(raw);
        long now = System.currentTimeMillis();

        if (any(q, "near me", "nearby", "najik", "नजिक", "मेरो नजिक")) {
            double lat = pref(a, "lat"), lon = pref(a, "lon");
            if (!valid(lat, lon)) return en ? "I need a current GPS fix to find your nearest official river station."
                    : "नजिकको official river station खोज्न current GPS fix चाहिन्छ।";
            Station best = null; double bestKm = Double.POSITIVE_INFINITY;
            for (Station s : stations) {
                if (!s.fresh(now) || !valid(s.lat, s.lon)) continue;
                double km = km(lat, lon, s.lat, s.lon);
                if (km < bestKm) { bestKm = km; best = s; }
            }
            if (best == null) return en ? "No fresh official station with coordinates is available right now."
                    : "अहिले coordinates सहित fresh official station भेटिएन।";
            return stationSentence(best, en, String.format(Locale.US, "%.1f km", bestKm));
        }

        List<Station> exact = new ArrayList<>();
        List<Station> district = new ArrayList<>();
        for (Station s : stations) {
            String name = norm(s.name), d = norm(s.district);
            if (!name.isEmpty() && containsMeaningful(q, name)) exact.add(s);
            else if (!d.isEmpty() && q.contains(d)) district.add(s);
        }
        List<Station> chosen = !exact.isEmpty() ? exact : district;
        if (!chosen.isEmpty()) {
            chosen.sort((x, y) -> Integer.compare(rank(y.stage), rank(x.stage)));
            Station top = chosen.get(0);
            if (exact.size() == 1) return stationSentence(top, en, null);
            int danger = 0, warning = 0, alert = 0, normal = 0, stale = 0;
            for (Station s : chosen) {
                if (!s.fresh(now)) { stale++; continue; }
                switch (s.stage) {
                    case "danger": danger++; break;
                    case "warning": warning++; break;
                    case "alert": alert++; break;
                    default: normal++;
                }
            }
            String area = !top.district.isEmpty() ? top.district : (exact.isEmpty() ? "requested area" : top.name);
            if (en) return area + ": fresh official stations — danger " + danger + ", warning " + warning + ", alert " + alert + ", normal " + normal + (stale > 0 ? ", stale " + stale : "") + ". Highest current status: " + top.name + " — " + top.stage.toUpperCase(Locale.ROOT) + ".";
            return area + ": fresh official station — danger " + danger + ", warning " + warning + ", alert " + alert + ", normal " + normal + (stale > 0 ? ", stale " + stale : "") + "। अहिलेको highest status: " + top.name + " — " + top.stage.toUpperCase(Locale.ROOT) + "।";
        }

        if (any(q, "warning", "danger", "चेतावनी", "खतरा")) {
            List<Station> risky = new ArrayList<>();
            for (Station s : stations) if (s.fresh(now) && ("warning".equals(s.stage) || "danger".equals(s.stage))) risky.add(s);
            risky.sort((x, y) -> Integer.compare(rank(y.stage), rank(x.stage)));
            if (risky.isEmpty()) return en ? "There are no fresh official Warning/Danger stations in the current feed right now."
                    : "अहिले current official feed मा fresh Warning/Danger station छैन।";
            StringBuilder b = new StringBuilder(en ? "Current fresh risk stations: " : "अहिलेका fresh risk station: ");
            for (int i = 0; i < Math.min(5, risky.size()); i++) {
                if (i > 0) b.append("; ");
                Station s = risky.get(i); b.append(s.name).append(" — ").append(s.stage.toUpperCase(Locale.ROOT));
            }
            return b.append('.').toString();
        }

        String guessedName = cleanRiverName(raw);
        if (!guessedName.isEmpty()) return en ? "I couldn't find a verified current station matching ‘" + guessedName + "’. I won't substitute another river or invent a reading."
                : "‘" + guessedName + "’ सँग मिल्ने verified current station भेटिएन। अर्को नदीको data राखेर वा reading बनाएर भन्दिनँ।";
        return en ? "Tell me a river/station or district name, for example Ninda Khola or Jhapa."
                : "नदी/station वा जिल्ला नाम भन्नुहोस्, जस्तै Ninda Khola वा Jhapa।";
    }

    private static String stationSentence(Station s, boolean en, String distance) {
        long ageMin = s.updatedAt > 0 ? Math.max(0, (System.currentTimeMillis() - s.updatedAt) / 60000L) : -1;
        boolean fresh = s.fresh(System.currentTimeMillis());
        String age = ageMin >= 0 ? ageMin + " min ago" : "time unavailable";
        String level = Double.isFinite(s.level) ? String.format(Locale.US, "%.2f m", s.level) : "level unavailable";
        String dist = distance == null ? "" : " • " + distance;
        if (!fresh) return en ? s.name + " has an official reading, but it is stale (" + age + "). I won't present stale data as live."
                : s.name + " को official reading छ तर stale छ (" + age + ")। stale data लाई live भनेर देखाउँदिनँ।";
        if (en) return s.name + (s.district.isEmpty() ? "" : " • " + s.district) + dist + ": " + s.stage.toUpperCase(Locale.ROOT) + ", level " + level + ", updated " + age + ".";
        return s.name + (s.district.isEmpty() ? "" : " • " + s.district) + dist + ": " + s.stage.toUpperCase(Locale.ROOT) + ", level " + level + ", update " + age + "।";
    }

    private static String news(boolean en) throws Exception {
        JSONObject root = getJson(NEWS + "?_sathi=" + System.currentTimeMillis());
        JSONArray arr = array(root, "items", "results", "news", "data");
        if (arr == null || arr.length() == 0) return en ? "No current app-news items are available right now."
                : "अहिले current app-news item उपलब्ध छैन।";
        StringBuilder b = new StringBuilder(en ? "Latest app news: " : "ताजा app समाचार: ");
        int n = 0;
        for (int i = 0; i < arr.length() && n < 4; i++) {
            JSONObject o = arr.optJSONObject(i); if (o == null) continue;
            String title = first(o, "title", "headline", "name");
            if (title.isEmpty()) continue;
            if (n++ > 0) b.append("; ");
            b.append(title);
        }
        if (n == 0) return en ? "No readable current app-news headlines are available right now."
                : "अहिले readable current app-news headline उपलब्ध छैन।";
        return b.append('.').toString();
    }

    private static List<Station> stations() throws Exception {
        long now = System.currentTimeMillis();
        synchronized (CACHE_LOCK) {
            if (now - stationCacheAt < CACHE_MS && !stationCache.isEmpty()) return new ArrayList<>(stationCache);
        }
        JSONObject root = getJson(RIVER + "?_sathi=" + now);
        JSONArray arr = array(root, "items", "results", "stations", "data");
        if (arr == null) arr = new JSONArray();
        List<Station> out = new ArrayList<>();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i); if (o == null) continue;
            Station s = parseStation(o); if (s != null) out.add(s);
        }
        synchronized (CACHE_LOCK) { stationCache = new ArrayList<>(out); stationCacheAt = now; }
        return out;
    }

    private static Station parseStation(JSONObject o) {
        String name = first(o, "name", "station_name", "stationName", "title", "river_name", "riverName");
        if (name.isEmpty()) return null;
        String district = first(o, "district", "district_name", "districtName");
        double lat = num(o, "latitude", "lat"), lon = num(o, "longitude", "lon", "lng");
        double level = num(o, "water_level", "waterLevel", "level", "current_level", "currentLevel");
        double warning = num(o, "warning_level", "warningLevel", "warning_threshold", "warningThreshold");
        double danger = num(o, "danger_level", "dangerLevel", "danger_threshold", "dangerThreshold");
        String rawStage = norm(first(o, "status", "stage", "state", "risk", "level_status", "levelStatus"));
        String stage = stage(rawStage, level, warning, danger);
        long at = time(first(o, "updated_at", "updatedAt", "observed_at", "observedAt", "datetime", "timestamp", "time", "last_updated", "lastUpdated"));
        return new Station(name, district, lat, lon, level, stage, at);
    }

    private static String stage(String raw, double level, double warning, double danger) {
        if (raw.contains("danger") || raw.contains("खतरा")) return "danger";
        if (raw.contains("warning") || raw.contains("चेतावनी")) return "warning";
        if (raw.contains("alert") || raw.contains("सतर्क")) return "alert";
        if (Double.isFinite(level) && Double.isFinite(danger) && level >= danger) return "danger";
        if (Double.isFinite(level) && Double.isFinite(warning) && level >= warning) return "warning";
        if (raw.contains("normal") || raw.contains("safe")) return "normal";
        return "normal";
    }

    private static int rank(String s) {
        if ("danger".equals(s)) return 4;
        if ("warning".equals(s)) return 3;
        if ("alert".equals(s)) return 2;
        return 1;
    }

    private static JSONArray array(JSONObject root, String... keys) {
        if (root == null) return null;
        for (String k : keys) {
            Object x = root.opt(k);
            if (x instanceof JSONArray) return (JSONArray) x;
            if (x instanceof JSONObject) {
                JSONObject j = (JSONObject) x;
                for (String kk : keys) { JSONArray a = j.optJSONArray(kk); if (a != null) return a; }
            }
        }
        return null;
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15000); c.setReadTimeout(22000); c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line; while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static String cleanPlace(String raw) {
        String s = raw == null ? "" : raw;
        s = s.replaceAll("(?i)\\b(weather|mausam|temperature|temp|forecast|today|now|ko|kasto|cha|please|show|tell|me)\\b", " ");
        s = s.replace("मौसम", " ").replace("आज", " ").replace("अहिले", " ").replace("कस्तो", " ").replace("छ", " ");
        return s.replaceAll("[^\\p{L} .'-]", " ").replaceAll("\\s+", " ").trim();
    }

    private static String cleanRiverName(String raw) {
        String s = raw == null ? "" : raw;
        s = s.replaceAll("(?i)\\b(status|river|station|water|level|warning|danger|flood|ko|kasto|cha|please|show|tell|me|current|now)\\b", " ");
        s = s.replace("स्थिति", " ").replace("अवस्था", " ").replace("चेतावनी", " ").replace("खतरा", " ");
        return s.replaceAll("[^\\p{L} .'-]", " ").replaceAll("\\s+", " ").trim();
    }

    private static boolean containsMeaningful(String query, String candidate) {
        if (candidate.length() >= 4 && query.contains(candidate)) return true;
        String simplified = candidate.replace(" river", "").replace(" khola", "").replace(" nadi", "").trim();
        return simplified.length() >= 4 && query.contains(simplified);
    }

    private static boolean any(String q, String... words) {
        for (String w : words) if (q.contains(norm(w))) return true;
        return false;
    }

    private static String norm(String s) {
        return s == null ? "" : s.toLowerCase(Locale.ROOT).replaceAll("[\\s_/-]+", " ").trim();
    }

    private static String first(JSONObject o, String... keys) {
        for (String k : keys) { String v = o.optString(k, "").trim(); if (!v.isEmpty() && !"null".equalsIgnoreCase(v)) return v; }
        return "";
    }

    private static double num(JSONObject o, String... keys) {
        for (String k : keys) {
            Object v = o.opt(k); if (v == null || v == JSONObject.NULL) continue;
            if (v instanceof Number) return ((Number) v).doubleValue();
            try { return Double.parseDouble(String.valueOf(v).replaceAll("[^0-9+\\-.]", "")); } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    private static long time(String s) {
        if (s == null || s.trim().isEmpty()) return 0L;
        try { return Instant.parse(s).toEpochMilli(); } catch (Exception ignored) {}
        try { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return LocalDateTime.parse(s).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try {
            long n = Long.parseLong(s.replaceAll("[^0-9]", ""));
            if (n < 100000000000L) n *= 1000L;
            return n;
        } catch (Exception ignored) { return 0L; }
    }

    private static double pref(Activity a, String key) {
        long raw = a.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getLong(key, Double.doubleToRawLongBits(Double.NaN));
        return Double.longBitsToDouble(raw);
    }

    private static boolean valid(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
    }

    private static double km(double a1, double o1, double a2, double o2) {
        double r = 6371d, dLat = Math.toRadians(a2 - a1), dLon = Math.toRadians(o2 - o1);
        double x = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(Math.toRadians(a1)) * Math.cos(Math.toRadians(a2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return 2 * r * Math.asin(Math.sqrt(x));
    }

    private static int dp(Context c, int n) { return Math.round(n * c.getResources().getDisplayMetrics().density); }

    private static final class Station {
        final String name, district, stage;
        final double lat, lon, level;
        final long updatedAt;
        Station(String name, String district, double lat, double lon, double level, String stage, long updatedAt) {
            this.name = name; this.district = district; this.lat = lat; this.lon = lon;
            this.level = level; this.stage = stage; this.updatedAt = updatedAt;
        }
        boolean fresh(long now) { return updatedAt > 0 && now >= updatedAt && now - updatedAt <= FRESH_MS; }
    }

    private static final class CloudDrawable extends Drawable {
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        float phase;
        ValueAnimator animator;
        CloudDrawable(Context c) { paint.setColor(Color.argb(235, 245, 252, 255)); }
        void start() {
            animator = ValueAnimator.ofFloat(0f, 1f);
            animator.setDuration(2600L); animator.setRepeatCount(ValueAnimator.INFINITE); animator.setRepeatMode(ValueAnimator.REVERSE);
            animator.addUpdateListener(v -> { phase = (Float) v.getAnimatedValue(); invalidateSelf(); });
            animator.start();
        }
        @Override public void draw(Canvas canvas) {
            RectF b = new RectF(getBounds());
            float dx = (phase - .5f) * b.width() * .12f;
            float cy = b.centerY() + (phase - .5f) * b.height() * .08f;
            float h = b.height();
            canvas.drawCircle(b.left + b.width() * .35f + dx, cy, h * .23f, paint);
            canvas.drawCircle(b.left + b.width() * .52f + dx, cy - h * .09f, h * .30f, paint);
            canvas.drawCircle(b.left + b.width() * .69f + dx, cy, h * .22f, paint);
            canvas.drawOval(b.left + b.width() * .24f + dx, cy, b.left + b.width() * .80f + dx, cy + h * .22f, paint);
        }
        @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(android.graphics.ColorFilter colorFilter) { paint.setColorFilter(colorFilter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
