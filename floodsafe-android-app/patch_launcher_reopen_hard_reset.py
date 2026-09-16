from pathlib import Path

root = Path(__file__).resolve().parent

# A warm launcher reopen on some Samsung devices can leave an otherwise-live WebView
# compositor showing only the app background/progress strip. DOM/JS probes still return
# true in that state, so the conservative MainActivity recovery cannot detect it.
# The launcher splash is the one place where we know the user explicitly reopened the app.
# Recreate only that warm content Activity, giving WebView a fresh renderer/surface while
# keeping all bundled assets and short resource caches for a fast restart.

voice_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/VoiceMainActivity.java'
voice = voice_path.read_text(encoding='utf-8')
class_marker = 'public final class VoiceMainActivity extends MainActivity {\n'
constant = '    static final String EXTRA_LAUNCHER_REOPEN = "io.github.pujan1234hub.floodsafe.LAUNCHER_REOPEN";\n'
if 'EXTRA_LAUNCHER_REOPEN' not in voice:
    if class_marker not in voice:
        raise SystemExit('VoiceMainActivity class marker missing')
    voice = voice.replace(class_marker, class_marker + constant, 1)

old_new_intent = '''    @Override protected void onNewIntent(Intent intent) {\n        super.onNewIntent(intent);\n        setIntent(intent);\n        consumeWakeIntent(intent);\n    }\n'''
new_new_intent = '''    @Override protected void onNewIntent(Intent intent) {\n        super.onNewIntent(intent);\n        setIntent(intent);\n        if (intent != null && intent.getBooleanExtra(EXTRA_LAUNCHER_REOPEN, false)) {\n            intent.removeExtra(EXTRA_LAUNCHER_REOPEN);\n            // Warm launcher reopen: replace the WebView/activity surface once. This fixes\n            // Samsung blank-compositor resumes that still have a live DOM/JS runtime.\n            recreate();\n            return;\n        }\n        consumeWakeIntent(intent);\n    }\n'''
if 'Samsung blank-compositor resumes' not in voice:
    if old_new_intent not in voice:
        raise SystemExit('VoiceMainActivity onNewIntent marker missing')
    voice = voice.replace(old_new_intent, new_new_intent, 1)
voice_path.write_text(voice, encoding='utf-8')

splash_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/PJBuiltsSplashActivity.java'
splash = splash_path.read_text(encoding='utf-8')
app_marker = '        Intent app = new Intent(this, VoiceMainActivity.class);\n'
extra_line = '        app.putExtra(VoiceMainActivity.EXTRA_LAUNCHER_REOPEN, true);\n'
if extra_line not in splash:
    if app_marker not in splash:
        raise SystemExit('PJBuiltsSplashActivity app intent marker missing')
    splash = splash.replace(app_marker, app_marker + extra_line, 1)
splash_path.write_text(splash, encoding='utf-8')

# Give this field-test build a distinct install version so Android package installer can
# update the currently installed APK cleanly.
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
if 'versionCode 14' in gradle:
    gradle = gradle.replace('versionCode 14', 'versionCode 15', 1)
if "versionName '0.7.0'" in gradle:
    gradle = gradle.replace("versionName '0.7.0'", "versionName '0.7.1'", 1)
if 'versionCode 15' not in gradle or "versionName '0.7.1'" not in gradle:
    raise SystemExit('FloodSafe version bump did not apply')
gradle_path.write_text(gradle, encoding='utf-8')

# Keep the visible privacy/version card aligned with the APK build.
index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.0</span>', '<span class="badge green">v0.7.1</span>', 1)
index_path.write_text(index, encoding='utf-8')

# Build-time assertions: fail CI rather than shipping another undetectable warm-reopen blank.
voice_check = voice_path.read_text(encoding='utf-8')
splash_check = splash_path.read_text(encoding='utf-8')
if 'EXTRA_LAUNCHER_REOPEN' not in voice_check or 'recreate();' not in voice_check:
    raise SystemExit('Warm launcher hard reset missing from VoiceMainActivity')
if 'putExtra(VoiceMainActivity.EXTRA_LAUNCHER_REOPEN, true)' not in splash_check:
    raise SystemExit('Launcher reopen marker missing from splash')

print('FloodSafe warm launcher reopen hard-reset fix applied (v0.7.1)')
