package io.github.pujan1234hub.floodsafe.sathi;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class WakeWordService extends Service {
    static final String PREFS = "sathi_native";
    static final String ACTION_START = "io.github.pujan1234hub.floodsafe.sathi.START_WAKE";
    static final String ACTION_STOP = "io.github.pujan1234hub.floodsafe.sathi.STOP_WAKE";
    static final String ACTION_CAPTURE_ONCE = "io.github.pujan1234hub.floodsafe.sathi.CAPTURE_ONCE";
    static final String ACTION_WAKE_DETECTED = "io.github.pujan1234hub.floodsafe.sathi.WAKE_DETECTED";
    static final String ACTION_COMMAND = "io.github.pujan1234hub.floodsafe.sathi.COMMAND";
    static final String ACTION_STATE = "io.github.pujan1234hub.floodsafe.sathi.STATE";
    static final String EXTRA_COMMAND = "command";

    private static final String CHANNEL = "sathi_wake";
    private static final int NOTIFICATION_ID = 2608;
    private static final int MODE_WAKE = 1;
    private static final int MODE_COMMAND = 2;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private SpeechRecognizer recognizer;
    private TextToSpeech tts;
    private boolean ttsReady;
    private boolean persistent;
    private boolean stopping;
    private int mode = MODE_WAKE;
    private long generation;

    @Override public void onCreate() {
        super.onCreate();
        createChannel();
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                ttsReady = true;
                int result = tts.setLanguage(new Locale("ne", "NP"));
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED)
                    tts.setLanguage(Locale.US);
                tts.setSpeechRate(0.94f);
            }
        });
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? ACTION_START : intent.getAction();
        if (ACTION_STOP.equals(action)) {
            persistent = false;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean("wake_enabled", false).apply();
            broadcastState(false);
            shutdown();
            return START_NOT_STICKY;
        }

        startForeground(NOTIFICATION_ID, notification("SATHI तयार छ", persistent ? "‘Ye Sathi’ भन्नुहोस्" : "आवाज सुन्न तयार"));
        stopping = false;
        if (ACTION_CAPTURE_ONCE.equals(action)) {
            persistent = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean("wake_enabled", false);
            mode = MODE_COMMAND;
            updateNotification("SATHI सुन्दैछ", "बाढी वा वर्षाबारे प्रश्न भन्नुहोस्");
            startListening(MODE_COMMAND, 120);
        } else {
            persistent = true;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean("wake_enabled", true).apply();
            broadcastState(true);
            mode = MODE_WAKE;
            updateNotification("SATHI सक्रिय", "पृष्ठभूमिमा ‘Ye Sathi’ सुन्दैछ");
            startListening(MODE_WAKE, 150);
        }
        return START_STICKY;
    }

    private void startListening(int requestedMode, long delay) {
        long g = ++generation;
        handler.postDelayed(() -> {
            if (stopping || g != generation) return;
            mode = requestedMode;
            destroyRecognizer();
            if (!SpeechRecognizer.isRecognitionAvailable(this)) {
                updateNotification("Voice recognition उपलब्ध छैन", "फोनको speech service जाँच गर्नुहोस्");
                if (!persistent) stopSelf();
                return;
            }
            recognizer = SpeechRecognizer.createSpeechRecognizer(this);
            recognizer.setRecognitionListener(new Listener(g));
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            i.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
            i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
            i.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, requestedMode == MODE_COMMAND ? 1200L : 800L);
            i.putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 700L);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE, requestedMode == MODE_WAKE ? "ne-NP" : "ne-NP");
            try { recognizer.startListening(i); }
            catch (Exception e) { scheduleRetry(requestedMode, 1200); }
        }, delay);
    }

    private final class Listener implements RecognitionListener {
        private final long ownGeneration;
        Listener(long g) { ownGeneration = g; }
        @Override public void onReadyForSpeech(android.os.Bundle params) {}
        @Override public void onBeginningOfSpeech() {}
        @Override public void onRmsChanged(float rmsdB) {}
        @Override public void onBufferReceived(byte[] buffer) {}
        @Override public void onEndOfSpeech() {}
        @Override public void onEvent(int eventType, android.os.Bundle params) {}

        @Override public void onError(int error) {
            if (stopping || ownGeneration != generation) return;
            if (mode == MODE_COMMAND) {
                updateNotification("आवाज बुझिएन", persistent ? "फेरि ‘Ye Sathi’ भन्नुहोस्" : "SATHI खोलेर फेरि प्रयास गर्नुहोस्");
                if (persistent) startListening(MODE_WAKE, 800); else stopSelf();
            } else scheduleRetry(MODE_WAKE, error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY ? 1500 : 700);
        }

        @Override public void onPartialResults(android.os.Bundle partialResults) {
            if (mode != MODE_WAKE || ownGeneration != generation) return;
            String text = first(partialResults);
            if (wakeMatch(text)) onWake();
        }

        @Override public void onResults(android.os.Bundle results) {
            if (stopping || ownGeneration != generation) return;
            String text = first(results);
            if (mode == MODE_WAKE) {
                if (wakeMatch(text)) onWake();
                else if (persistent) startListening(MODE_WAKE, 300);
            } else {
                if (text == null || text.isBlank()) {
                    if (persistent) startListening(MODE_WAKE, 500); else stopSelf();
                } else onCommand(text.trim());
            }
        }
    }

    private void onWake() {
        generation++;
        destroyRecognizer();
        sendBroadcast(new Intent(ACTION_WAKE_DETECTED).setPackage(getPackageName()));
        updateNotification("Ye Sathi सुनेँ", "अब आफ्नो प्रश्न भन्नुहोस्");
        speak("भन्नुहोस्");
        startListening(MODE_COMMAND, 950);
    }

    private void onCommand(String command) {
        generation++;
        destroyRecognizer();
        boolean visible = getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean("app_visible", false);
        if (visible) {
            Intent b = new Intent(ACTION_COMMAND).setPackage(getPackageName()).putExtra(EXTRA_COMMAND, command);
            sendBroadcast(b);
            if (persistent) startListening(MODE_WAKE, 1200); else stopSelf();
            return;
        }

        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString("pending_command", command).apply();
        updateNotification("SATHI ले जाँच गर्दैछ", command);
        executor.execute(() -> {
            String reply = NativeDataAnswerer.answer(getApplicationContext(), command);
            handler.post(() -> {
                updateNotification("SATHI को उत्तर", reply);
                speak(reply);
                if (persistent) startListening(MODE_WAKE, 1800); else handler.postDelayed(this::stopSelf, 2500);
            });
        });
    }

    private void scheduleRetry(int m, long delay) {
        if (stopping) return;
        if (m == MODE_WAKE && !persistent) { stopSelf(); return; }
        startListening(m, delay);
    }

    private static String first(android.os.Bundle b) {
        if (b == null) return "";
        ArrayList<String> a = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        return a == null || a.isEmpty() ? "" : a.get(0);
    }

    private static boolean wakeMatch(String text) {
        if (text == null) return false;
        String s = text.toLowerCase(Locale.ROOT).replaceAll("[\\p{Punct}]", " ").replaceAll("\\s+", " ").trim();
        return s.contains("ye sathi") || s.contains("hey sathi") || s.contains("ए साथी") || s.contains("ये साथी")
                || s.contains("ए साठी") || s.contains("ये साठी") || s.equals("साथी") || s.endsWith(" साथी");
    }

    private void speak(String text) {
        if (!ttsReady || text == null || text.isBlank()) return;
        try { tts.speak(text.replaceAll("[🔴🟠🟡🟢🌊🌧️🌤️⚠️🚗⚡🥤🐄]", ""), TextToSpeech.QUEUE_FLUSH, null, "sathi"); }
        catch (Exception ignored) {}
    }

    private void createChannel() {
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "SATHI आवाज", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("FloodSafe Nepal SATHI wake phrase service");
            nm.createNotificationChannel(ch);
        }
    }

    private Notification notification(String title, String text) {
        Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent content = PendingIntent.getActivity(this, 1, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Intent stop = new Intent(this, WakeWordService.class).setAction(ACTION_STOP);
        PendingIntent stopPi = PendingIntent.getService(this, 2, stop, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        return b.setSmallIcon(R.drawable.ic_sathi)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setOngoing(persistent)
                .setContentIntent(content)
                .addAction(new Notification.Action.Builder(null, "बन्द", stopPi).build())
                .setCategory(Notification.CATEGORY_SERVICE)
                .build();
    }

    private void updateNotification(String title, String text) {
        getSystemService(NotificationManager.class).notify(NOTIFICATION_ID, notification(title, text));
    }

    private void broadcastState(boolean enabled) {
        sendBroadcast(new Intent(ACTION_STATE).setPackage(getPackageName()).putExtra("enabled", enabled));
    }

    private void destroyRecognizer() {
        if (recognizer != null) {
            try { recognizer.cancel(); } catch (Exception ignored) {}
            try { recognizer.destroy(); } catch (Exception ignored) {}
            recognizer = null;
        }
    }

    private void shutdown() {
        stopping = true;
        generation++;
        handler.removeCallbacksAndMessages(null);
        destroyRecognizer();
        stopForeground(STOP_FOREGROUND_REMOVE);
        stopSelf();
    }

    @Override public void onDestroy() {
        stopping = true;
        generation++;
        handler.removeCallbacksAndMessages(null);
        destroyRecognizer();
        if (tts != null) { try { tts.stop(); tts.shutdown(); } catch (Exception ignored) {} }
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
