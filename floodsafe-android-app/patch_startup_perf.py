from pathlib import Path

ROOT = Path(__file__).resolve().parent
main_path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
voice_path = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/VoiceMainActivity.java'

# MainActivity: keep first frame/WebView startup free of WorkManager, Firebase topic,
# foreground-location service, and expensive offscreen preraster work.
text = main_path.read_text(encoding='utf-8')
text = text.replace('        settings.setOffscreenPreRaster(true);\n',
                    '        settings.setOffscreenPreRaster(false);\n', 1)

startup = '''        webView.loadUrl(NavigationPolicy.HOME);\n        enableAutomaticSafetyMonitoring();\n'''
startup_new = '''        webView.loadUrl(NavigationPolicy.HOME);\n        // STARTUP_PERF_V1: the page must paint before WorkManager/Firebase/location\n        // bootstrap. On budget phones doing all of that inside Activity startup can\n        // starve WebView and trigger a startup ANR. Existing workers remain persisted.\n        webView.postDelayed(() -> {\n            if (webView != null && !isFinishing() && !isDestroyed()) {\n                enableAutomaticSafetyMonitoring();\n            }\n        }, 12_000L);\n'''
if startup in text:
    text = text.replace(startup, startup_new, 1)
elif 'STARTUP_PERF_V1' not in text:
    raise SystemExit('automatic monitoring startup marker not found')

resume_heavy = '''        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {\n            FloodMonitorService.startIfEnabled(this);\n        }\n'''
resume_light = '''        final boolean resumeMonitoringEnabled =\n                alertPrefs().getBoolean("enabled", false) && notificationsAllowed();\n        if (resumeMonitoringEnabled) {\n            getWindow().getDecorView().postDelayed(() -> {\n                if (!isFinishing() && !isDestroyed()) {\n                    FloodMonitorService.startIfEnabled(MainActivity.this);\n                }\n            }, 8_000L);\n        }\n'''
if resume_heavy in text:
    text = text.replace(resume_heavy, resume_light, 1)
elif 'resumeMonitoringEnabled' not in text:
    raise SystemExit('onResume monitoring marker not found')

# A weather refresh on every resume is useful, but it must not compete with the
# launcher transition / first frame / map creation.
text = text.replace(
    'current.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);',
    'current.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},2200)", null);',
)

for required in ['STARTUP_PERF_V1', 'settings.setOffscreenPreRaster(false);',
                 'resumeMonitoringEnabled', '}, 12_000L);', '}, 8_000L);']:
    if required not in text:
        raise SystemExit('MainActivity startup performance patch missing: ' + required)
main_path.write_text(text, encoding='utf-8')

# VoiceMainActivity: TextToSpeech binds to another service; wake-word service can
# also start an FGS. Neither is required to draw the app, so initialize them lazily.
text = voice_path.read_text(encoding='utf-8')
if 'import android.os.Handler;' not in text:
    text = text.replace('import android.os.Bundle;\n',
                        'import android.os.Bundle;\nimport android.os.Handler;\nimport android.os.Looper;\n', 1)

field_anchor = '    private String pendingWakeEventId;\n'
if 'STARTUP_PERF_VOICE_V1' not in text:
    if field_anchor not in text:
        raise SystemExit('VoiceMainActivity field marker not found')
    text = text.replace(field_anchor, field_anchor + '''    // STARTUP_PERF_VOICE_V1: keep TTS/wake-service binding off the launch critical path.\n    private final Handler startupHandler = new Handler(Looper.getMainLooper());\n    private String pendingSpeech;\n''', 1)

text = text.replace('        initTts();\n', '', 1)

old_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        if (getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE)\n                .getBoolean(SathiWakeService.KEY_ENABLED, false)\n                && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {\n            startWakeService(SathiWakeService.ACTION_START);\n        }\n        flushWakeQuery();\n    }\n'''
new_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        startupHandler.postDelayed(() -> {\n            if (isFinishing() || isDestroyed()) return;\n            if (getSharedPreferences(SathiWakeService.PREFS, MODE_PRIVATE)\n                    .getBoolean(SathiWakeService.KEY_ENABLED, false)\n                    && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {\n                startWakeService(SathiWakeService.ACTION_START);\n            }\n        }, 8_500L);\n        flushWakeQuery();\n    }\n'''
if old_resume in text:
    text = text.replace(old_resume, new_resume, 1)
elif '}, 8_500L);' not in text:
    raise SystemExit('VoiceMainActivity onResume marker not found')

old_init = '''    private void initTts() {\n        tts = new TextToSpeech(getApplicationContext(), status -> {\n            if (status == TextToSpeech.SUCCESS && tts != null) {\n                int result = tts.setLanguage(Locale.forLanguageTag("ne-NP"));\n                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) tts.setLanguage(new Locale("ne"));\n                tts.setSpeechRate(0.92f);\n            }\n        });\n    }\n\n    private void speakNepali(String text) {\n        if (tts == null || text == null || text.trim().isEmpty()) return;\n        String cleaned = text.replaceAll("[\\\\p{So}\\\\p{Cn}]+", " ").replaceAll("\\\\s+", " ").trim();\n        if (cleaned.length() > 1800) cleaned = cleaned.substring(0, 1800);\n        tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, null, "sathi-web-answer");\n    }\n'''
new_init = '''    private void initTts() {\n        if (tts != null) return;\n        tts = new TextToSpeech(getApplicationContext(), status -> {\n            if (status == TextToSpeech.SUCCESS && tts != null) {\n                int result = tts.setLanguage(Locale.forLanguageTag("ne-NP"));\n                if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) tts.setLanguage(new Locale("ne"));\n                tts.setSpeechRate(0.92f);\n                String queued = pendingSpeech;\n                pendingSpeech = null;\n                if (queued != null && !queued.trim().isEmpty()) speakNepali(queued);\n            } else {\n                pendingSpeech = null;\n            }\n        });\n    }\n\n    private void speakNepali(String text) {\n        if (text == null || text.trim().isEmpty()) return;\n        if (tts == null) {\n            pendingSpeech = text;\n            initTts();\n            return;\n        }\n        String cleaned = text.replaceAll("[\\\\p{So}\\\\p{Cn}]+", " ").replaceAll("\\\\s+", " ").trim();\n        if (cleaned.length() > 1800) cleaned = cleaned.substring(0, 1800);\n        tts.speak(cleaned, TextToSpeech.QUEUE_FLUSH, null, "sathi-web-answer");\n    }\n'''
if old_init in text:
    text = text.replace(old_init, new_init, 1)
elif 'pendingSpeech = text;' not in text:
    raise SystemExit('VoiceMainActivity TTS marker not found')

old_destroy = '''    @Override protected void onDestroy() {\n        if (speech != null) { try { speech.cancel(); } catch (RuntimeException ignored) {} speech.destroy(); speech = null; }\n'''
new_destroy = '''    @Override protected void onDestroy() {\n        startupHandler.removeCallbacksAndMessages(null);\n        if (speech != null) { try { speech.cancel(); } catch (RuntimeException ignored) {} speech.destroy(); speech = null; }\n'''
if old_destroy in text:
    text = text.replace(old_destroy, new_destroy, 1)
elif 'startupHandler.removeCallbacksAndMessages(null);' not in text:
    raise SystemExit('VoiceMainActivity destroy marker not found')

for required in ['STARTUP_PERF_VOICE_V1', 'pendingSpeech = text;', '}, 8_500L);',
                 'startupHandler.removeCallbacksAndMessages(null);']:
    if required not in text:
        raise SystemExit('Voice startup performance patch missing: ' + required)
voice_path.write_text(text, encoding='utf-8')

print('FloodSafe startup critical-path deferral PASS')
