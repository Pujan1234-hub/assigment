package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.webkit.JavascriptInterface;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;

/**
 * Native Android shell for SATHI voice. The existing FloodSafe WebView remains
 * unchanged; this class only adds a native speech/TTS bridge and wake-service handoff.
 */
public final class VoiceMainActivity extends MainActivity {
    private static final int AUDIO_REQUEST = 62;
    private SpeechRecognizer speech;
    private TextToSpeech tts;
    private boolean pendingVoiceStart;
    private String pendingWakeQuery;
    private String pendingWakeEventId;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (webView != null) webView.addJavascriptInterface(new SathiBridge(), "SathiNative");
        initTts();
        consumeWakeIntent(getIntent());
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
        @JavascriptInterface public void startVoiceInput() {
            runOnUiThread(() -> ensureAudioAndStart(true));
        }

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

        @JavascriptInterface public void speak(String text) {
            runOnUiThread(() -> speakNepali(text));
        }

        @JavascriptInterface public void updateMonitoringPoint(double lat, double lon, boolean followDevice) {
            runOnUiThread(() -> {
                if (!Double.isFinite(lat) || !Double.isFinite(lon)) return;
                getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit()
                        .putLong("lat", Double.doubleToRawLongBits(lat))
                        .putLong("lon", Double.doubleToRawLongBits(lon))
                        .putBoolean("follow_device", followDevice)
                        .apply();
                if (followDevice && hasLocationPermission()) startWakeService(SathiWakeService.ACTION_REFRESH);
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
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, AUDIO_REQUEST);
            return;
        }
        enableWakeService();
        if (immediateQuery) {
            startWakeService(SathiWakeService.ACTION_PAUSE);
            if (webView != null) webView.postDelayed(this::startSingleRecognition, 280L);
        } else {
            dispatchState("wake", true, "“Ye Sathi” पृष्ठभूमि आवाज सक्रिय छ।");
        }
    }

    private void enableWakeService() {
        getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE).edit()
                .putBoolean(SathiWakeService.KEY_ENABLED, true).apply();
        startWakeService(SathiWakeService.ACTION_START);
    }

    private void startWakeService(String action) {
        try {
            Intent service = new Intent(this, SathiWakeService.class).setAction(action);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service);
            else startService(service);
        } catch (RuntimeException e) {
            dispatchState("wake", false, "SATHI background service सुरु हुन सकेन। App खुला राखेर फेरि प्रयास गर्नुहोस्।");
        }
    }

    private void startSingleRecognition() {
        if (isFinishing() || isDestroyed()) return;
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            dispatchState("mic", false, "यो फोनमा Android voice recognition उपलब्ध छैन।");
            startWakeService(SathiWakeService.ACTION_RESUME);
            return;
        }
        try {
            if (speech != null) {
                speech.cancel();
                speech.destroy();
            }
            speech = SpeechRecognizer.createSpeechRecognizer(this);
            speech.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle params) {
                    dispatchState("mic", true, "सुन्दैछु…");
                }
                @Override public void onBeginningOfSpeech() {}
                @Override public void onRmsChanged(float rmsdB) {}
                @Override public void onBufferReceived(byte[] buffer) {}
                @Override public void onEndOfSpeech() {}
                @Override public void onError(int error) {
                    dispatchState("mic", false, "आवाज बुझिएन। फेरि माइक थिचेर सोध्नुहोस्।");
                    startWakeService(SathiWakeService.ACTION_RESUME);
                }
                @Override public void onResults(Bundle results) {
                    String best = firstResult(results);
                    if (!best.isEmpty()) {
                        dispatchTranscript(best, false, UUID.randomUUID().toString());
                    } else {
                        dispatchState("mic", false, "आवाज स्पष्ट भएन। फेरि प्रयास गर्नुहोस्।");
                    }
                    startWakeService(SathiWakeService.ACTION_RESUME);
                }
                @Override public void onPartialResults(Bundle partialResults) {
                    String partial = firstResult(partialResults);
                    if (!partial.isEmpty()) dispatchPartial(partial);
                }
                @Override public void onEvent(int eventType, Bundle params) {}
            });
            speech.startListening(recognizerIntent());
        } catch (RuntimeException e) {
            dispatchState("mic", false, "माइक सुरु हुन सकेन। फेरि प्रयास गर्नुहोस्।");
            startWakeService(SathiWakeService.ACTION_RESUME);
        }
    }

    private Intent recognizerIntent() {
        return new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ne-NP")
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ne-NP")
                .putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
    }

    private static String firstResult(Bundle bundle) {
        if (bundle == null) return "";
        ArrayList<String> list = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        if (list == null || list.isEmpty() || list.get(0) == null) return "";
        return list.get(0).trim();
    }

    private void initTts() {
        tts = new TextToSpeech(getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS && tts != null) {
                int result = tts.setLanguage(Locale.forLanguageTag("ne-NP"));
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts.setLanguage(new Locale("ne"));
                }
                selectBestNepaliVoice();
                tts.setSpeechRate(0.96f);
                tts.setPitch(1.02f);
            }
        });
    }

    private void selectBestNepaliVoice() {
        if (tts == null || Build.VERSION.SDK_INT < 21) return;
        try {
            Set<Voice> voices = tts.getVoices();
            if (voices == null || voices.isEmpty()) return;
            Voice best = null;
            int bestScore = Integer.MIN_VALUE;
            for (Voice voice : voices) {
                if (voice == null || voice.getLocale() == null
                        || !"ne".equalsIgnoreCase(voice.getLocale().getLanguage())) continue;
                int score = voice.getQuality() * 100 - voice.getLatency() * 8;
                if ("NP".equalsIgnoreCase(voice.getLocale().getCountry())) score += 40;
                if (!voice.isNetworkConnectionRequired()) score += 8;
                String name = voice.getName() == null ? "" : voice.getName().toLowerCase(Locale.ROOT);
                if (name.contains("natural") || name.contains("neural") || name.contains("premium")) score += 25;
                if (score > bestScore) {
                    best = voice;
                    bestScore = score;
                }
            }
            if (best != null) tts.setVoice(best);
        } catch (RuntimeException ignored) {}
    }

    private void speakNepali(String text) {
        if (tts == null || text == null || text.trim().isEmpty()) return;
        String cleaned = text
                .replaceAll("[\\p{So}\\p{Cn}]+", " ")
                .replace("°C", " डिग्री सेल्सियस")
                .replace("km/h", " किलोमिटर प्रति घण्टा")
                .replace("mm", " मिलिमिटर")
                .replace("%", " प्रतिशत")
                .replaceAll("\\s+", " ")
                .trim();
        if (cleaned.length() > 1800) cleaned = cleaned.substring(0, 1800);
        tts.stop();
        String[] parts = cleaned.split("(?<=[।.!?])\\s+");
        boolean first = true;
        int count = 0;
        for (String part : parts) {
            String spoken = part == null ? "" : part.trim();
            if (spoken.isEmpty()) continue;
            tts.speak(spoken, first ? TextToSpeech.QUEUE_FLUSH : TextToSpeech.QUEUE_ADD,
                    null, "sathi-web-answer-" + count);
            first = false;
            count++;
            if (count < parts.length) {
                tts.playSilentUtterance(105L, TextToSpeech.QUEUE_ADD, "sathi-pause-" + count);
            }
        }
    }

    private void consumeWakeIntent(Intent intent) {
        if (intent == null) return;
        String q = intent.getStringExtra(SathiWakeService.EXTRA_QUERY);
        String id = intent.getStringExtra(SathiWakeService.EXTRA_EVENT_ID);
        if (q == null || q.trim().isEmpty()) return;
        pendingWakeQuery = q.trim();
        pendingWakeEventId = (id == null || id.trim().isEmpty()) ? UUID.randomUUID().toString() : id;
        intent.removeExtra(SathiWakeService.EXTRA_QUERY);
        intent.removeExtra(SathiWakeService.EXTRA_EVENT_ID);
        flushWakeQuery();
    }

    private void flushWakeQuery() {
        if (webView == null || pendingWakeQuery == null) return;
        final String q = pendingWakeQuery;
        final String id = pendingWakeEventId;
        pendingWakeQuery = null;
        pendingWakeEventId = null;
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 450L);
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 1600L);
        webView.postDelayed(() -> dispatchTranscript(q, true, id), 3200L);
    }

    private void dispatchTranscript(String text, boolean wake, String id) {
        if (webView == null || text == null || text.trim().isEmpty()) return;
        String js = "window.dispatchEvent(new CustomEvent('sathi-native-transcript',{detail:{text:"
                + JSONObject.quote(text) + ",wake:" + wake + ",id:" + JSONObject.quote(id) + "}}));";
        webView.evaluateJavascript(js, null);
    }

    private void dispatchPartial(String text) {
        if (webView == null) return;
        String js = "window.dispatchEvent(new CustomEvent('sathi-native-partial',{detail:{text:"
                + JSONObject.quote(text) + "}}));";
        webView.evaluateJavascript(js, null);
    }

    private void dispatchState(String kind, boolean active, String message) {
        if (webView == null) return;
        String js = "window.dispatchEvent(new CustomEvent('sathi-native-state',{detail:{kind:"
                + JSONObject.quote(kind) + ",active:" + active + ",message:" + JSONObject.quote(message) + "}}));";
        webView.evaluateJavascript(js, null);
    }

    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(code, permissions, grants);
        if (code != AUDIO_REQUEST) return;
        boolean granted = checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
        if (granted) {
            boolean immediate = pendingVoiceStart;
            pendingVoiceStart = false;
            enableWakeService();
            if (immediate) {
                startWakeService(SathiWakeService.ACTION_PAUSE);
                if (webView != null) webView.postDelayed(this::startSingleRecognition, 320L);
            } else {
                dispatchState("wake", true, "“Ye Sathi” पृष्ठभूमि आवाज सक्रिय छ।");
            }
        } else {
            pendingVoiceStart = false;
            dispatchState("mic", false, "Voice चलाउन microphone अनुमति चाहिन्छ।");
        }
    }

    @Override protected void onDestroy() {
        if (speech != null) {
            try { speech.cancel(); } catch (RuntimeException ignored) {}
            speech.destroy();
            speech = null;
        }
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }
        super.onDestroy();
    }
}
