from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- MainActivity: automatic monitoring + immediate rain worker -----------------
path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = path.read_text(encoding='utf-8')

marker = '        webView.loadUrl(NavigationPolicy.HOME);\n'
insert = marker + '        enableAutomaticSafetyMonitoring();\n'
if 'enableAutomaticSafetyMonitoring();' not in text:
    if marker not in text:
        raise SystemExit('MainActivity loadUrl marker not found')
    text = text.replace(marker, insert, 1)

method_marker = '    private SharedPreferences alertPrefs() {\n'
method = '''    private void enableAutomaticSafetyMonitoring() {
        alertPrefs().edit().putBoolean("enabled", true).apply();
        pendingBackgroundLocationEducation = true;
        if (!notificationsAllowed()) {
            if (Build.VERSION.SDK_INT >= 33) {
                try { requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, NOTIFICATION_REQUEST); }
                catch (RuntimeException ignored) { }
            }
            return;
        }
        scheduleBackgroundRainAlerts();
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        notifyAlertStatus(true);
        maybeRequestBackgroundLocation();
    }

'''
if 'private void enableAutomaticSafetyMonitoring()' not in text:
    if method_marker not in text:
        raise SystemExit('alertPrefs marker not found')
    text = text.replace(method_marker, method + method_marker, 1)

if 'floodsafe-local-rain-alert-now' not in text:
    old = '''        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        OneTimeWorkRequest riverNow = new OneTimeWorkRequest.Builder(RiverAlertWorker.class)
                .setConstraints(constraints).build();
'''
    new = '''        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        OneTimeWorkRequest rainNow = new OneTimeWorkRequest.Builder(RainAlertWorker.class)
                .setConstraints(constraints).build();
        OneTimeWorkRequest riverNow = new OneTimeWorkRequest.Builder(RiverAlertWorker.class)
                .setConstraints(constraints).build();
'''
    if old not in text:
        raise SystemExit('MainActivity worker creation marker not found')
    text = text.replace(old, new, 1)
    old = '''        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        manager.enqueueUniqueWork("floodsafe-local-river-alert-now",
                ExistingWorkPolicy.REPLACE, riverNow);
'''
    new = '''        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        manager.enqueueUniqueWork("floodsafe-local-rain-alert-now",
                ExistingWorkPolicy.REPLACE, rainNow);
        manager.enqueueUniqueWork("floodsafe-local-river-alert-now",
                ExistingWorkPolicy.REPLACE, riverNow);
'''
    if old not in text:
        raise SystemExit('MainActivity worker enqueue marker not found')
    text = text.replace(old, new, 1)
    cancel = '        manager.cancelUniqueWork("floodsafe-local-river-alert-now");\n'
    if cancel not in text:
        raise SystemExit('MainActivity worker cancel marker not found')
    text = text.replace(cancel,
        '        manager.cancelUniqueWork("floodsafe-local-rain-alert-now");\n' + cancel, 1)

path.write_text(text, encoding='utf-8')

# --- RainAlertWorker: 4-hour fresh digest, strict safety GPS kept separate ------
path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/RainAlertWorker.java'
text = path.read_text(encoding='utf-8')
text = text.replace('roughly every 3 hours', 'roughly every 4 hours')
text = text.replace('smart_weather_updates_v1', 'smart_weather_updates_v2')
text = text.replace('WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L',
                    'WEATHER_DIGEST_INTERVAL_MS = 4L * 60L * 60L * 1000L')
text = text.replace('"last_weather_digest_at"', '"last_weather_digest_v2_at"')
text = text.replace('आगामी ३ घण्टामा वर्षाको सम्भावना', 'आगामी ४ घण्टामा वर्षाको सम्भावना')
text = text.replace('३ घण्टाको मौसम अपडेट', '४ घण्टाको मौसम अपडेट')
text = text.replace('३ घण्टापछि करिब ', '४ घण्टापछि करिब ')
text = text.replace('now.plusHours(3).plusMinutes(30)', 'now.plusHours(4).plusMinutes(30)')
text = text.replace('3-hour forecast', '4-hour forecast')

old = '''        if (prefs.getBoolean("follow_device", false)) {
            long locationTime = prefs.getLong("location_time", 0L);
            if (!MonitoringLocationPolicy.freshDeviceLocation(
                    locationTime, System.currentTimeMillis(), lat, lon)) return Result.success();
        }

        try {
'''
new = '''        boolean followDevice = prefs.getBoolean("follow_device", false);
        boolean safetyLocationFresh = true;
        long locationTime = prefs.getLong("location_time", 0L);
        if (followDevice) {
            long age = System.currentTimeMillis() - locationTime;
            // A 4-hour general weather digest may use the user's last real GPS for up to
            // 24 hours. Proximity/rain-start safety notifications below still require
            // the strict fresh-device-location policy.
            if (locationTime <= 0L || age < 0L || age > 24L * 60L * 60L * 1000L) {
                return Result.success();
            }
            safetyLocationFresh = MonitoringLocationPolicy.freshDeviceLocation(
                    locationTime, System.currentTimeMillis(), lat, lon);
        }

        try {
'''
if old in text:
    text = text.replace(old, new, 1)
elif 'boolean safetyLocationFresh = true;' not in text:
    raise SystemExit('RainAlertWorker location freshness marker not found')

digest = '''            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode);

            RainEvent event = findEvent(data.optJSONObject("minutely_15"), now);
'''
digest_new = '''            maybeNotifyWeatherDigest(data, prefs, now, temperature, apparent, humidity, wind, weatherCode);

            // Keep safety events strict: stale last-known GPS can power a weather digest,
            // but never a proximity/rain-start warning.
            if (followDevice && !safetyLocationFresh) return Result.success();

            RainEvent event = findEvent(data.optJSONObject("minutely_15"), now);
'''
if digest in text:
    text = text.replace(digest, digest_new, 1)
elif 'if (followDevice && !safetyLocationFresh) return Result.success();' not in text:
    raise SystemExit('RainAlertWorker digest/safety split marker not found')

for required in [
    'WEATHER_DIGEST_INTERVAL_MS = 4L * 60L * 60L * 1000L',
    'smart_weather_updates_v2',
    'last_weather_digest_v2_at',
    'if (followDevice && !safetyLocationFresh) return Result.success();'
]:
    if required not in text:
        raise SystemExit('RainAlertWorker patch missing: ' + required)
path.write_text(text, encoding='utf-8')

# --- Boot/app-update: restore periodic work and kick one fresh weather check -----
path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/BootReceiver.java'
text = path.read_text(encoding='utf-8')
if 'import androidx.work.ExistingWorkPolicy;' not in text:
    text = text.replace('import androidx.work.ExistingPeriodicWorkPolicy;\n',
                        'import androidx.work.ExistingPeriodicWorkPolicy;\nimport androidx.work.ExistingWorkPolicy;\n', 1)
if 'import androidx.work.OneTimeWorkRequest;' not in text:
    text = text.replace('import androidx.work.NetworkType;\n',
                        'import androidx.work.NetworkType;\nimport androidx.work.OneTimeWorkRequest;\n', 1)
if 'floodsafe-local-rain-alert-now' not in text:
    marker = '''        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(
                RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        WorkManager manager = WorkManager.getInstance(context.getApplicationContext());
'''
    replacement = '''        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(
                RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        OneTimeWorkRequest rainNow = new OneTimeWorkRequest.Builder(RainAlertWorker.class)
                .setConstraints(constraints).build();
        WorkManager manager = WorkManager.getInstance(context.getApplicationContext());
'''
    if marker not in text:
        raise SystemExit('BootReceiver worker marker not found')
    text = text.replace(marker, replacement, 1)
    marker = '''        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
'''
    replacement = '''        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        manager.enqueueUniqueWork("floodsafe-local-rain-alert-now",
                ExistingWorkPolicy.REPLACE, rainNow);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
'''
    if marker not in text:
        raise SystemExit('BootReceiver enqueue marker not found')
    text = text.replace(marker, replacement, 1)
path.write_text(text, encoding='utf-8')

print('FloodSafe automatic alerts + 4-hour weather notification bootstrap applied')
