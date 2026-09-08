package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import androidx.annotation.Nullable;
import androidx.work.ExistingWorkPolicy;
import androidx.work.OneTimeWorkRequest;
import androidx.work.WorkManager;
import java.util.ArrayList;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * User-enabled foreground service for the "Ye Sathi" wake phrase.
 *
 * It also keeps the selected/current GPS point fresh for rain alerts and asks
 * WorkManager for an immediate rain check every five minutes while the service
 * is alive. Force-stop still disables the service by Android design.
 */
public final class SathiWakeService extends Service implements LocationListener {
    public static final String PREFS = "sathi_voice";
    public static final String KEY_ENABLED = "enabled";
    public static final String EXTRA_QUERY = "sathi_query";
    public static final String EXTRA_EVENT_ID = "sathi_event_id";

    public static final String ACTION_START = "io.github.pujan1234hub.floodsafe.SATHI_START";
    public static final String ACTION_STOP = "io.github.pujan1234hub.floodsafe.SATHI_STOP";
    public static final String ACTION_PAUSE = "io.github.pujan1234hub.floodsafe.SATHI_PAUSE";
    public static final String ACTION_RESUME = "io.github.pujan1234hub.floodsafe.SATHI_RESUME";
    public static final String ACTION_REFRESH = "io.github.pujan1234hub.floodsafe.SATHI_REFRESH";

    private static final String CHANNEL_ID = "sathi_voice_service_v1";
    private static final String WAKE_CHANNEL_ID = "sathi_wake_prompt_v1";
    private static final int SERVICE_NOTIFICATION_ID = 7200;
    private static final long RESTART_MS = 1200L;
    private static final long COMMAND_WINDOW_MS = 12000L;
    private static final long RAIN_TICK_MS = 5L * 60L * 1000L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private SpeechRecognizer recognizer;
    private TextToSpeech tts;
    private boolean paused;
    private boolean listening;
    private long awaitingCommandUntil;
    private LocationManager locationManager;

    private final Runnable restartListening = () -> {
        if (!paused && isVoiceEnabled()) beginListening();
    };

    private final Runnable rainTick = new Runnable() {
        @Override public void run() {
            try {
                if (getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).getBoolean("enabled", false)) {
                    OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(RainAlertWorker.class).build();
                    WorkManager.getInstance(getApplicationContext()).enqueueUniqueWork(
                            "floodsafe-rain-live-check", ExistingWorkPolicy.REPLACE, request);
                }
            } catch (RuntimeException ignored) {}
            main.postDelayed(this, RAIN_TICK_MS);
        }
    };

    @Override public void onCreate() {
        super.onCreate();
        createChannels();
        if (!ensureForeground()) {
            stopSelf();
            return;
        }
        initTts();
        startLocationTracking();
        main.postDelayed(rainTick, 1200L);
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? ACTION_REFRESH : intent.getAction();
        if (action == null) action = ACTION_REFRESH;
        if (ACTION_STOP.equals(action)) {
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(KEY_ENABLED, false).apply();
            paused = true;
            cancelRecognition();
            stopLocationTracking();
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return START_NOT_STICKY;
        }

        // Permissions may have changed since the service was first started.
        if (!ensureForeground()) {
            stopSelf();
            return START_NOT_STICKY;
        }
        startLocationTracking();

        if (ACTION_PAUSE.equals(action)) {
            paused = true;
            cancelRecognition();
            return START_STICKY;
        }
        if (ACTION_RESUME.equals(action)) {
            paused = false;
            awaitingCommandUntil = 0L;
            scheduleRestart(250L);
            return START_STICKY;
        }
        if (ACTION_REFRESH.equals(action)) {
            if (!paused) scheduleRestart(250L);
            return START_STICKY;
        }

        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(KEY_ENABLED, true).apply();
        paused = false;
        scheduleRestart(250L);
        return START_STICKY;
    }

    private boolean ensureForeground() {
        boolean mic = checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
        boolean loc = hasLocationPermission()
                && getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).getBoolean("follow_device", false);
        if (!mic && !loc) return false;

        Intent launch = new Intent(this, VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 7200, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        String detail = mic
                ? "“Ye Sathi” सुन्दैछ • वर्षा/स्थान निगरानी तयार"
                : "वर्षा/स्थान निगरानी सक्रिय";
        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(this, CHANNEL_ID)
                : new android.app.Notification.Builder(this);
        android.app.Notification n = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle("FloodSafe Nepal • SATHI")
                .setContentText(detail)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setContentIntent(open)
                .setCategory(android.app.Notification.CATEGORY_SERVICE)
                .setPriority(android.app.Notification.PRIORITY_LOW)
                .build();

        try {
            if (Build.VERSION.SDK_INT >= 29) {
                int type = 0;
                if (loc) type |= ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION;
                if (Build.VERSION.SDK_INT >= 30 && mic) type |= ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE;
                if (type != 0) startForeground(SERVICE_NOTIFICATION_ID, n, type);
                else startForeground(SERVICE_NOTIFICATION_ID, n);
            } else {
                startForeground(SERVICE_NOTIFICATION_ID, n);
            }
            return true;
        } catch (RuntimeException denied) {
            return false;
        }
    }

    private void createChannels() {
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager == null || Build.VERSION.SDK_INT < 26) return;

        NotificationChannel service = new NotificationChannel(
                CHANNEL_ID, "SATHI voice and live location", NotificationManager.IMPORTANCE_LOW);
        service.setDescription("Keeps user-enabled Ye Sathi listening and FloodSafe live monitoring active.");
        service.setShowBadge(false);
        manager.createNotificationChannel(service);

        NotificationChannel wake = new NotificationChannel(
                WAKE_CHANNEL_ID, "SATHI wake requests", NotificationManager.IMPORTANCE_HIGH);
        wake.setDescription("Backup prompt when Android does not allow the app to open automatically.");
        manager.createNotificationChannel(wake);
    }

    private boolean isVoiceEnabled() {
        return getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(KEY_ENABLED, false)
                && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
    }

    private void beginListening() {
        if (paused || listening || !isVoiceEnabled()) return;
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return;
        try {
            if (recognizer == null) {
                recognizer = SpeechRecognizer.createSpeechRecognizer(this);
                recognizer.setRecognitionListener(new RecognitionListener() {
                    @Override public void onReadyForSpeech(Bundle params) { listening = true; }
                    @Override public void onBeginningOfSpeech() {}
                    @Override public void onRmsChanged(float rmsdB) {}
                    @Override public void onBufferReceived(byte[] buffer) {}
                    @Override public void onEndOfSpeech() { listening = false; }
                    @Override public void onError(int error) {
                        listening = false;
                        if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS) return;
                        scheduleRestart(error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY ? 2200L : RESTART_MS);
                    }
                    @Override public void onResults(Bundle results) {
                        listening = false;
                        String text = firstResult(results);
                        if (!text.isEmpty()) handleFinal(text);
                        else scheduleRestart(RESTART_MS);
                    }
                    @Override public void onPartialResults(Bundle partialResults) {}
                    @Override public void onEvent(int eventType, Bundle params) {}
                });
            }
            recognizer.startListening(recognizerIntent());
            listening = true;
        } catch (RuntimeException busy) {
            listening = false;
            scheduleRestart(2200L);
        }
    }

    private Intent recognizerIntent() {
        return new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ne-NP")
                .putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ne-NP")
                .putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
                .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5);
    }

    private void handleFinal(String heard) {
        long now = System.currentTimeMillis();
        if (awaitingCommandUntil > now) {
            awaitingCommandUntil = 0L;
            deliverQuery(heard);
            return;
        }

        WakeMatch match = findWake(heard);
        if (match == null) {
            scheduleRestart(450L);
            return;
        }
        if (!match.rest.isEmpty()) {
            deliverQuery(match.rest);
            return;
        }

        awaitingCommandUntil = now + COMMAND_WINDOW_MS;
        paused = true;
        cancelRecognition();
        speak("सुन्दैछु");
        main.postDelayed(() -> {
            paused = false;
            scheduleRestart(100L);
        }, 1150L);
    }

    private void deliverQuery(String query) {
        String q = query == null ? "" : query.trim();
        if (q.isEmpty()) {
            scheduleRestart(RESTART_MS);
            return;
        }
        String eventId = UUID.randomUUID().toString();
        paused = true;
        cancelRecognition();

        Intent launch = new Intent(this, VoiceMainActivity.class)
                .putExtra(EXTRA_QUERY, q)
                .putExtra(EXTRA_EVENT_ID, eventId)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try {
            startActivity(launch);
        } catch (RuntimeException ignored) {
            postWakeFallback(q, eventId);
        }

        // Always leave a tap fallback because recent Android versions may block
        // background activity launches even when startActivity does not throw.
        postWakeFallback(q, eventId);
        main.postDelayed(() -> {
            paused = false;
            awaitingCommandUntil = 0L;
            scheduleRestart(100L);
        }, 18000L);
    }

    private void postWakeFallback(String query, String eventId) {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager == null) return;
        Intent launch = new Intent(this, VoiceMainActivity.class)
                .putExtra(EXTRA_QUERY, query)
                .putExtra(EXTRA_EVENT_ID, eventId)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 7201, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String shown = query.length() > 100 ? query.substring(0, 100) + "…" : query;
        android.app.Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(this, WAKE_CHANNEL_ID)
                : new android.app.Notification.Builder(this);
        android.app.Notification n = builder
                .setSmallIcon(R.drawable.ic_floodsafe)
                .setContentTitle("🤖 SATHI ले तपाईंको प्रश्न सुन्यो")
                .setContentText(shown)
                .setStyle(new android.app.Notification.BigTextStyle().bigText(shown))
                .setAutoCancel(true)
                .setContentIntent(open)
                .setPriority(android.app.Notification.PRIORITY_HIGH)
                .build();
        manager.notify(7201, n);
    }

    private void scheduleRestart(long delayMs) {
        main.removeCallbacks(restartListening);
        main.postDelayed(restartListening, Math.max(100L, delayMs));
    }

    private void cancelRecognition() {
        main.removeCallbacks(restartListening);
        listening = false;
        if (recognizer != null) {
            try { recognizer.cancel(); } catch (RuntimeException ignored) {}
        }
    }

    private static String firstResult(Bundle bundle) {
        if (bundle == null) return "";
        ArrayList<String> list = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        if (list == null || list.isEmpty() || list.get(0) == null) return "";
        return list.get(0).trim();
    }

    private static final class WakeMatch {
        final String rest;
        WakeMatch(String rest) { this.rest = rest; }
    }

    private static WakeMatch findWake(String raw) {
        if (raw == null) return null;
        String lower = raw.toLowerCase(Locale.ROOT).trim()
                .replaceAll("[,!?।]+", " ")
                .replaceAll("\\s+", " ");
        String[] phrases = {
                "ye sathi", "hey sathi", "hey sati", "ye sati",
                "ए साथी", "हे साथी", "ए सथि", "हे सथि", "ये साथी"
        };
        for (String phrase : phrases) {
            int i = lower.indexOf(phrase);
            if (i < 0) continue;
            String rest = lower.substring(i + phrase.length()).trim();
            return new WakeMatch(rest);
        }
        return null;
    }

    private void initTts() {
        tts = new TextToSpeech(getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS && tts != null) {
                int result = tts.setLanguage(Locale.forLanguageTag("ne-NP"));
                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    tts.setLanguage(new Locale("ne"));
                }
                tts.setSpeechRate(0.92f);
            }
        });
    }

    private void speak(String text) {
        if (tts == null || text == null || text.trim().isEmpty()) return;
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "sathi-wake");
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void startLocationTracking() {
        if (!hasLocationPermission()) return;
        if (!getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).getBoolean("follow_device", false)) return;
        if (locationManager == null) locationManager = getSystemService(LocationManager.class);
        if (locationManager == null) return;
        try {
            locationManager.removeUpdates(this);
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER,
                        TimeUnit.MINUTES.toMillis(2), 100f, this, Looper.getMainLooper());
            }
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER,
                        TimeUnit.MINUTES.toMillis(2), 150f, this, Looper.getMainLooper());
            }
            Location best = newest(
                    locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER),
                    locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER));
            if (best != null) saveLocation(best);
        } catch (SecurityException | IllegalArgumentException ignored) {}
    }

    private void stopLocationTracking() {
        if (locationManager == null) return;
        try { locationManager.removeUpdates(this); } catch (SecurityException ignored) {}
    }

    private static Location newest(Location a, Location b) {
        if (a == null) return b;
        if (b == null) return a;
        return a.getTime() >= b.getTime() ? a : b;
    }

    @Override public void onLocationChanged(Location location) {
        if (location != null) saveLocation(location);
    }

    @Override public void onProviderEnabled(String provider) {}
    @Override public void onProviderDisabled(String provider) {}
    @Override public void onStatusChanged(String provider, int status, Bundle extras) {}

    private void saveLocation(Location location) {
        if (!getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).getBoolean("follow_device", false)) return;
        double lat = location.getLatitude(), lon = location.getLongitude();
        // FloodSafe Nepal only.
        if (!Double.isFinite(lat) || !Double.isFinite(lon)
                || lat < 26.0 || lat > 31.0 || lon < 79.5 || lon > 89.0) return;
        getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit()
                .putLong("lat", Double.doubleToRawLongBits(lat))
                .putLong("lon", Double.doubleToRawLongBits(lon))
                .putLong("location_time", location.getTime())
                .apply();
    }

    @Nullable @Override public IBinder onBind(Intent intent) { return null; }

    @Override public void onDestroy() {
        main.removeCallbacksAndMessages(null);
        stopLocationTracking();
        cancelRecognition();
        if (recognizer != null) {
            recognizer.destroy();
            recognizer = null;
        }
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }
        super.onDestroy();
    }
}
