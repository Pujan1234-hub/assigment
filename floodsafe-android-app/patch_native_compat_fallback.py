from pathlib import Path

root = Path(__file__).resolve().parent
main_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
splash_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/PJBuiltsSplashActivity.java'

main = main_path.read_text(encoding='utf-8')
splash = splash_path.read_text(encoding='utf-8')

# MainActivity is patched by the existing WebView stability chain before this file runs.
field_anchor = '    private boolean coldStartRecoveryUsed;\n'
fields = '''    private boolean startupHealthConfirmed;\n    private boolean nativeFallbackStarted;\n    private static final String COMPAT_PREFS = "floodsafe-web-compat";\n    private static final String KEY_FORCE_NATIVE = "force_native";\n    private static final String KEY_WEB_PENDING = "web_pending";\n'''
if 'KEY_FORCE_NATIVE = "force_native"' not in main:
    if field_anchor not in main:
        raise SystemExit('cold-start field marker missing; run v0.7.2 patch first')
    main = main.replace(field_anchor, field_anchor + fields, 1)

# A compositor commit is not enough on low-end/vendor WebViews: the JS thread can still
# wedge immediately while the heavy map/SATHI runtimes start. Confirm the HOME event loop
# responds before declaring WebView healthy.
commit_anchor = '''                    firstPageCommitted = true;\n                    coldStartRecoveryUsed = false;\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n'''
commit_new = '''                    firstPageCommitted = true;\n                    coldStartRecoveryUsed = false;\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n                    if (NavigationPolicy.HOME.equals(url)) {\n                        final WebView committed = view;\n                        committed.postDelayed(() -> confirmStartupHealth(committed), 2200L);\n                        committed.postDelayed(() -> confirmStartupHealth(committed), 5200L);\n                    }\n'''
if 'confirmStartupHealth(committed)' not in main:
    if commit_anchor not in main:
        raise SystemExit('page commit marker missing')
    main = main.replace(commit_anchor, commit_new, 1)

# After the initial HOME navigation, automatically leave WebView if it never becomes healthy.
# This is intentionally later than the existing one-shot reload so normal phones keep the
# full web dashboard while incompatible phones get a native dashboard instead of a freeze.
load_watch_anchor = '''        firstLoad.postDelayed(() -> {\n            if (firstLoad != webView || firstPageCommitted || isFinishing() || isDestroyed()) return;\n            mainFrameError = true;\n            updateConnection();\n        }, 13000L);\n'''
load_watch_new = load_watch_anchor + '''        firstLoad.postDelayed(() -> {\n            if (firstLoad != webView || startupHealthConfirmed || nativeFallbackStarted\n                    || isFinishing() || isDestroyed()) return;\n            launchNativeCompatibilityFallback();\n        }, 9000L);\n'''
if 'launchNativeCompatibilityFallback();' not in main:
    if load_watch_anchor not in main:
        raise SystemExit('cold-start watchdog marker missing')
    main = main.replace(load_watch_anchor, load_watch_new, 1)

# Add the health probe + native fallback methods before SharedPreferences alertPrefs().
method_anchor = '''    private SharedPreferences alertPrefs() {\n'''
methods = '''    private void confirmStartupHealth(WebView candidate) {\n        if (candidate == null || candidate != webView || startupHealthConfirmed\n                || nativeFallbackStarted || isFinishing() || isDestroyed()) return;\n        String url = candidate.getUrl();\n        if (!NavigationPolicy.HOME.equals(url)) return;\n        try {\n            candidate.evaluateJavascript(\n                    "(function(){try{return (document.readyState==='interactive'||document.readyState==='complete')&&!!document.querySelector('.app')&&!!document.getElementById('map')?'ok':'wait'}catch(e){return 'err'}})()",\n                    value -> {\n                        if (candidate != webView || nativeFallbackStarted || isFinishing() || isDestroyed()) return;\n                        if (\"\\\"ok\\\"\".equals(value)) {\n                            startupHealthConfirmed = true;\n                            getSharedPreferences(COMPAT_PREFS, MODE_PRIVATE).edit()\n                                    .putBoolean(KEY_WEB_PENDING, false).apply();\n                        }\n                    });\n        } catch (RuntimeException ignored) { }\n    }\n\n    private void launchNativeCompatibilityFallback() {\n        if (nativeFallbackStarted || isFinishing() || isDestroyed()) return;\n        nativeFallbackStarted = true;\n        getSharedPreferences(COMPAT_PREFS, MODE_PRIVATE).edit()\n                .putBoolean(KEY_FORCE_NATIVE, true)\n                .putBoolean(KEY_WEB_PENDING, false).apply();\n        try {\n            Intent nativeHome = new Intent(this, NativeHomeActivity.class);\n            nativeHome.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);\n            startActivity(nativeHome);\n        } catch (RuntimeException ignored) {\n            nativeFallbackStarted = false;\n            return;\n        }\n        finish();\n    }\n\n'''
if 'private void confirmStartupHealth(WebView candidate)' not in main:
    if method_anchor not in main:
        raise SystemExit('alertPrefs method marker missing')
    main = main.replace(method_anchor, methods + method_anchor, 1)

main_path.write_text(main, encoding='utf-8')

# Splash remembers a previous unfinished WebView launch. If one exists, skip WebView entirely
# on the next launcher open. This makes a failed field launch self-healing even if Android
# kills the activity before the 9-second in-process watchdog fires.
if 'import android.content.SharedPreferences;' not in splash:
    splash = splash.replace('import android.content.Intent;\n', 'import android.content.Intent;\nimport android.content.SharedPreferences;\n', 1)

old_app = '        Intent app = new Intent(this, VoiceMainActivity.class);\n'
new_app = '''        SharedPreferences compat = getSharedPreferences("floodsafe-web-compat", MODE_PRIVATE);\n        boolean forceNative = compat.getBoolean("force_native", false)\n                || compat.getBoolean("web_pending", false);\n        Intent app;\n        if (forceNative) {\n            compat.edit().putBoolean("force_native", true).putBoolean("web_pending", false).apply();\n            app = new Intent(this, NativeHomeActivity.class);\n        } else {\n            compat.edit().putBoolean("web_pending", true).apply();\n            app = new Intent(this, VoiceMainActivity.class);\n        }\n'''
if 'boolean forceNative = compat.getBoolean("force_native", false)' not in splash:
    if old_app not in splash:
        raise SystemExit('splash target marker missing')
    splash = splash.replace(old_app, new_app, 1)

# Only VoiceMainActivity understands the launcher-reopen marker.
old_extra = '        app.putExtra(VoiceMainActivity.EXTRA_LAUNCHER_REOPEN, true);\n'
new_extra = '''        if (app.getComponent() != null\n                && VoiceMainActivity.class.getName().equals(app.getComponent().getClassName())) {\n            app.putExtra(VoiceMainActivity.EXTRA_LAUNCHER_REOPEN, true);\n        }\n'''
if old_extra in splash:
    splash = splash.replace(old_extra, new_extra, 1)

splash_path.write_text(splash, encoding='utf-8')

# Distinct install version for the automatic compatibility fallback build.
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 17', 'versionCode 18', 1)
gradle = gradle.replace("versionName '0.7.3'", "versionName '0.7.4'", 1)
if 'versionCode 18' not in gradle or "versionName '0.7.4'" not in gradle:
    raise SystemExit('v0.7.4 version bump did not apply; run v0.7.3 patch first')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.3</span>', '<span class="badge green">v0.7.4</span>', 1)
index = index.replace('<span class="badge green">v0.7.2</span>', '<span class="badge green">v0.7.4</span>', 1)
index_path.write_text(index, encoding='utf-8')

main_check = main_path.read_text(encoding='utf-8')
splash_check = splash_path.read_text(encoding='utf-8')
for required in [
    'confirmStartupHealth(committed)',
    'launchNativeCompatibilityFallback()',
    'KEY_FORCE_NATIVE = "force_native"',
    'new Intent(this, NativeHomeActivity.class)',
]:
    if required not in main_check:
        raise SystemExit('native compatibility fallback missing: ' + required)
for required in [
    'boolean forceNative = compat.getBoolean("force_native", false)',
    'new Intent(this, NativeHomeActivity.class)',
    'putBoolean("web_pending", true)',
]:
    if required not in splash_check:
        raise SystemExit('splash compatibility routing missing: ' + required)

print('FloodSafe automatic native compatibility fallback applied (v0.7.4)')
