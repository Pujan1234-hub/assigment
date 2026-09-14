package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Locale;
import java.util.UUID;

/** Native Android shell for the original full FloodSafe WebView UI + SATHI voice bridge. */
public final class VoiceMainActivity extends MainActivity {
    private static final int AUDIO_REQUEST = 62;
    private SpeechRecognizer speech;
    private TextToSpeech tts;
    private boolean pendingVoiceStart;
    private String pendingWakeQuery;
    private String pendingWakeEventId;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        clearLegacyMapMonitoringPoint();
        if (webView != null) webView.addJavascriptInterface(new SathiBridge(), "SathiNative");
        initTts();
        consumeWakeIntent(getIntent());
    }

    private void clearLegacyMapMonitoringPoint() {
        SharedPreferences prefs = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
        if (prefs.getBoolean("follow_device", false)) return;
        prefs.edit().remove("lat").remove("lon").remove("location_time")
                .putBoolean("location_stale", true).apply();
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        consumeWakeIntent(intent);
    }

    @Override protected void onResume() {
        super.onResume();
        if (getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE)
                .getBoolean(SathiWakeService.KEY_ENABLED, false)
                && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            startWakeService(SathiWakeService.ACTION_START);
        }
        flushWakeQuery();
    }

    private final class SathiBridge {
        @JavascriptInterface public void startVoiceInput() { runOnUiThread(() -> ensureAudioAndStart(true)); }
        @JavascriptInterface public void setAlwaysOn(boolean enabled) {
            runOnUiThread(() -> {
                if (enabled) ensureAudioAndStart(false);
                else {
                    getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE).edit()
                            .putBoolean(SathiWakeService.KEY_ENABLED, false).apply();
                    startWakeService(SathiWakeService.ACTION_STOP);
                    dispatchState("wake", false, "“Ye Sathi” पृष्ठभूमि आवाज बन्द भयो।");
                }
            });
        }
        @JavascriptInterface public boolean isAlwaysOn() {
            return getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE)
                    .getBoolean(SathiWakeService.KEY_ENABLED, false)
                    && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
        }
        @JavascriptInterface public void speak(String text) { runOnUiThread(() -> speakNepali(text)); }
        @JavascriptInterface public void updateMonitoringPoint(double lat, double lon, boolean followDevice) {
            runOnUiThread(() -> {
                if (!followDevice) return;
                if (!Double.isFinite(lat) || !Double.isFinite(lon) || lat < -90d || lat > 90d || lon < -180d || lon > 180d) return;
                long now = System.currentTimeMillis();
                getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit()
                        .putLong("lat", Double.doubleToRawLongBits(lat)).putLong("lon", Double.doubleToRawLongBits(lon))
                        .putLong("location_time", now).putLong("device_lat", Double.doubleToRawLongBits(lat))
                        .putLong("device_lon", Double.doubleToRawLongBits(lon)).putLong("device_location_time", now)
                        .putBoolean("follow_device", true).putBoolean("location_stale", false).apply();
                if (hasLocationPermission()) startWakeService(SathiWakeService.ACTION_REFRESH);
            });
        }
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void ensureAudioAndStart(boolean immediateQuery) {
        pendingVoiceStart = immediateQuery;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, AUDIO_REQUEST); return;
        }
        enableWakeService();
        if (immediateQuery) {
            startWakeService(SathiWakeService.ACTION_PAUSE);
            if (webView != null) webView.postDelayed(this::startSingleRecognition, 280L);
        } else dispatchState("wake", true, "“Ye Sathi” पृष्ठभूमि आवाज सक्रिय छ।");
    }

    private void enableWakeService() {
        getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE).edit().putBoolean(SathiWakeService.KEY_ENABLED, true).apply();
        startWakeService(SathiWakeService.ACTION_START);
    }

    private void startWakeService(String action) {
        try {
            Intent service = new Intent(this, SathiWakeService.class).setAction(action);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service); else startService(service);
        } catch (RuntimeException e) {
            dispatchState("wake", false, "SATHI background service सुरु हुन सकेन। App खुला राखेर फेरि प्रयास गर्नुहोस्।");
        }
    }

    private void startSingleRecognition() {
        if (isFinishing() || isDestroyed()) return;
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            dispatchState("mic", false, "यो फोनमा Android voice recognition उपलब्ध छैन।");
            startWakeService(SathiWakeService.ACTION_RESUME); return;
        }
        try {
            if (speech != null) { speech.cancel(); speech.destroy(); }
            speech = SpeechRecognizer.createSpeechRecognizer(this);
            speech.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle params) { dispatchState("mic", true, "सुन्दैछु…"); }
                @Override public void onBeginningOfSpeech() {}
                @Override public void onRmsChanged(float rmsdB) {}
                @Override public void onBufferReceived(byte[] buffer) {}
                @Override public void onEndOfSpeech() {}
                @Override public void onError(int error) { dispatchState("mic", false, "आवाज बुझिएन। फेरि माइक थिचेर सोध्नुहोस्।"); startWakeService(SathiWakeService.ACTION_RESUME); }
                @Override public void onResults(Bundle results) {
                    String best = firstResult(results);
                    if (!best.isEmpty()) dispatchTranscript(best, false, UUID.randomUUID().toString());
                    else dispatchState("mic", false, "आवाज स्पष्ट भएन। फेरि प्रयास गर्नुहोस्।");
                    startWakeService(SathiWakeService.ACTION_RESUME);
                }
                @Override public void onPartialResults(Bundle partialResults) { String partial = firstResult(partialResults); if (!partial.isEmpty()) dispatchPartial(partial); }
                @Override public void onEvent(int eventType, Bundle params) {}
            });
            speech.startListening(recognizerIntent());
        } catch (RuntimeException e) { dispatchState("mic", false, "माइक सुरु हुन सकेन। फेरि प्रयास गर्नुहोस्।"); startWakeService(SathiWakeService.ACTION_RESUME); }
    }

    private Intent recognizerIntent() {
        return new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ne-NP").putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ne-NP")
                .putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true).putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
    }

    private static String firstResult(Bundle bundle) {
        if (bundle == null) return "";
        ArrayList<String> list = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        return list == null || list.isEmpty() || list.get(0) == null ? "" : list.get(0).trim();
    }

    private void initTts() {
        tts = new TextToSpeech(getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS && tts != null) {
                int result = tts.setLanguage(Locale.forLanguageTag("ne-NP"));
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) tts.setLanguage(new Locale("ne"));
                tts.setSpeechRate(0.92f);
            }
        });
    }

    private void speakNepali(String text) {
        if (tts == null || text == null || text.trim().isEmpty()) return;
        String cleaned = text.replaceAll("[\\p{So}\\p{Cn}]+", " ").replaceAll("\\s+", " ").trim();
        if (cleaned.length() > 1800) cleaned = cleaned.substring(0, 1800);
        tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, null, "sathi-web-answer");
    }

    private void consumeWakeIntent(Intent intent) {
        if (intent == null) return;
        String q = intent.getStringExtra(SathiWakeService.EXTRA_QUERY), id = intent.getStringExtra(SathiWakeService.EXTRA_EVENT_ID);
        if (q == null || q.trim().isEmpty()) return;
        pendingWakeQuery = q.trim(); pendingWakeEventId = (id == null || id.trim().isEmpty()) ? UUID.randomUUID().toString() : id;
        intent.removeExtra(SathiWakeService.EXTRA_QUERY); intent.removeExtra(SathiWakeService.EXTRA_EVENT_ID); flushWakeQuery();
    }

    private void flushWakeQuery() {
        if (webView == null || pendingWakeQuery == null) return;
        final String q = pendingWakeQuery, id = pendingWakeEventId; pendingWakeQuery = null; pendingWakeEventId = null;
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 450L);
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 1600L);
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 3200L);
    }

    private void dispatchTranscript(String text, boolean wake, String id) {
        if (webView == null || text == null || text.trim().isEmpty()) return;
        webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('sathi-native-transcript',{detail:{text:" + JSONObject.quote(text) + ",wake:" + wake + ",id:" + JSONObject.quote(id) + "}}));", null);
    }
    private void dispatchPartial(String text) { if (webView != null) webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('sathi-native-partial',{detail:{text:" + JSONObject.quote(text) + "}}));", null); }
    private void dispatchState(String kind, boolean active, String message) { if (webView != null) webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('sathi-native-state',{detail:{kind:" + JSONObject.quote(kind) + ",active:" + active + ",message:" + JSONObject.quote(message) + "}}));", null); }

    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(code, permissions, grants);
        if (code != AUDIO_REQUEST) return;
        boolean granted = checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
        if (granted) {
            boolean immediate = pendingVoiceStart; pendingVoiceStart = false; enableWakeService();
            if (immediate) { startWakeService(SathiWakeService.ACTION_PAUSE); if (webView != null) webView.postDelayed(this::startSingleRecognition, 320L); }
            else dispatchState("wake", true, "“Ye Sathi” पृष्ठभूमि आवाज सक्रिय छ।");
        } else { pendingVoiceStart = false; dispatchState("mic", false, "Voice चलाउन microphone अनुमति चाहिन्छ।"); }
    }

    @Override protected void onDestroy() {
        if (speech != null) { try { speech.cancel(); } catch (RuntimeException ignored) {} speech.destroy(); speech = null; }
        if (tts != null) { tts.stop(); tts.shutdown(); tts = null; }
        super.onDestroy();
    }
}
