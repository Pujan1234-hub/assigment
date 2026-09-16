from pathlib import Path

root = Path(__file__).resolve().parent
voice_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/VoiceMainActivity.java'
main_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'

voice = voice_path.read_text(encoding='utf-8')
main = main_path.read_text(encoding='utf-8')

# patch_launcher_reopen_hard_reset.py runs first. Keep its blank-compositor recreate for
# a healthy HOME page, but do not recreate/restore a stale internal page such as privacy.
old_reopen = '''        if (intent != null && intent.getBooleanExtra(EXTRA_LAUNCHER_REOPEN, false)) {\n            intent.removeExtra(EXTRA_LAUNCHER_REOPEN);\n            // Warm launcher reopen: replace the WebView/activity surface once. This fixes\n            // Samsung blank-compositor resumes that still have a live DOM/JS runtime.\n            recreate();\n            return;\n        }\n'''
new_reopen = '''        if (intent != null && intent.getBooleanExtra(EXTRA_LAUNCHER_REOPEN, false)) {\n            intent.removeExtra(EXTRA_LAUNCHER_REOPEN);\n            // Launcher means HOME. Some vendor WebViews preserve the last internal page\n            // (notably privacy.html) across an APK update/reopen. Reset that navigation\n            // in-place; only recreate when we are already on HOME and need the existing\n            // Samsung blank-compositor recovery.\n            if (webView != null) {\n                String currentUrl = webView.getUrl();\n                if (currentUrl != null && !currentUrl.equals(NavigationPolicy.HOME)) {\n                    try {\n                        webView.stopLoading();\n                        webView.loadUrl(NavigationPolicy.HOME);\n                        webView.postDelayed(() -> {\n                            if (webView != null) {\n                                try { webView.clearHistory(); } catch (RuntimeException ignored) { }\n                            }\n                        }, 700L);\n                        return;\n                    } catch (RuntimeException ignored) { }\n                }\n            }\n            // Already on HOME (or renderer unavailable): replace the surface once.\n            recreate();\n            return;\n        }\n'''
if 'vendor WebViews preserve the last internal page' not in voice:
    if old_reopen not in voice:
        raise SystemExit('launcher reopen patch marker missing; run patch_launcher_reopen_hard_reset.py first')
    voice = voice.replace(old_reopen, new_reopen, 1)
voice_path.write_text(voice, encoding='utf-8')

# Android system Back must always escape privacy.html even if a vendor WebView reports a
# broken/empty history stack. This does not alter normal in-app HOME/map behavior.
old_back = '''    @Override public void onBackPressed() {\n        if (webView != null && webView.canGoBack()) webView.goBack();\n        else super.onBackPressed();\n    }\n'''
new_back = '''    @Override public void onBackPressed() {\n        if (webView != null) {\n            String currentUrl = webView.getUrl();\n            if (currentUrl != null && currentUrl.endsWith("/privacy.html")) {\n                try {\n                    webView.stopLoading();\n                    webView.loadUrl(NavigationPolicy.HOME);\n                    webView.postDelayed(() -> {\n                        if (webView != null) {\n                            try { webView.clearHistory(); } catch (RuntimeException ignored) { }\n                        }\n                    }, 500L);\n                    return;\n                } catch (RuntimeException ignored) { }\n            }\n            if (webView.canGoBack()) { webView.goBack(); return; }\n        }\n        super.onBackPressed();\n    }\n'''
if 'currentUrl.endsWith("/privacy.html")' not in main:
    if old_back not in main:
        raise SystemExit('MainActivity back-navigation marker missing')
    main = main.replace(old_back, new_back, 1)
main_path.write_text(main, encoding='utf-8')

# Give the cross-device field build a distinct install version.
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 16', 'versionCode 17', 1)
gradle = gradle.replace("versionName '0.7.2'", "versionName '0.7.3'", 1)
if 'versionCode 17' not in gradle or "versionName '0.7.3'" not in gradle:
    raise SystemExit('v0.7.3 version bump did not apply; run v0.7.2 patches first')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.2</span>', '<span class="badge green">v0.7.3</span>', 1)
index = index.replace('<span class="badge green">v0.7.1</span>', '<span class="badge green">v0.7.3</span>', 1)
index = index.replace('<span class="badge green">v0.7.0</span>', '<span class="badge green">v0.7.3</span>', 1)
index_path.write_text(index, encoding='utf-8')

voice_check = voice_path.read_text(encoding='utf-8')
main_check = main_path.read_text(encoding='utf-8')
for required in [
    'vendor WebViews preserve the last internal page',
    'webView.loadUrl(NavigationPolicy.HOME)',
]:
    if required not in voice_check:
        raise SystemExit('cross-device launcher HOME recovery missing: ' + required)
if 'currentUrl.endsWith("/privacy.html")' not in main_check:
    raise SystemExit('privacy native back recovery missing')

print('FloodSafe cross-device HOME/privacy navigation recovery applied (v0.7.3)')
