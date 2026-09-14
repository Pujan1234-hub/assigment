from pathlib import Path

path = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = path.read_text(encoding='utf-8')

marker = '        webView.loadUrl(NavigationPolicy.HOME);\n'
insert = marker + '''        enableAutomaticSafetyMonitoring();\n'''
if 'enableAutomaticSafetyMonitoring();' not in text:
    if marker not in text:
        raise SystemExit('MainActivity loadUrl marker not found')
    text = text.replace(marker, insert, 1)

method_marker = '    private SharedPreferences alertPrefs() {\n'
method = '''    private void enableAutomaticSafetyMonitoring() {\n        alertPrefs().edit().putBoolean("enabled", true).apply();\n        pendingBackgroundLocationEducation = true;\n        if (!notificationsAllowed()) {\n            if (Build.VERSION.SDK_INT >= 33) {\n                try { requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, NOTIFICATION_REQUEST); }\n                catch (RuntimeException ignored) { }\n            }\n            return;\n        }\n        scheduleBackgroundRainAlerts();\n        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");\n        notifyAlertStatus(true);\n        maybeRequestBackgroundLocation();\n    }\n\n'''
if 'private void enableAutomaticSafetyMonitoring()' not in text:
    if method_marker not in text:
        raise SystemExit('alertPrefs marker not found')
    text = text.replace(method_marker, method + method_marker, 1)

path.write_text(text, encoding='utf-8')
print('FloodSafe automatic alert bootstrap applied')
