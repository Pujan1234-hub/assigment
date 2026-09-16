from pathlib import Path

root = Path(__file__).resolve().parent
main_path = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = main_path.read_text(encoding='utf-8')

# Cold start must not use the warm-resume recovery probe before the first visible page commit.
field = '    private boolean pendingBackgroundLocationEducation;\n'
if 'private boolean firstPageCommitted;' not in text:
    if field not in text:
        raise SystemExit('MainActivity field marker missing')
    text = text.replace(field, field + '    private boolean firstPageCommitted;\n    private boolean coldStartRecoveryUsed;\n', 1)

# Offscreen preraster is useful for offscreen WebViews, but this page is immediately visible
# and very long/heavy (map + national station list + SATHI). On some Samsung devices it can
# consume the renderer before the first composited frame, leaving only the native background.
text = text.replace('        settings.setOffscreenPreRaster(true);\n', '')

# Explicitly keep the visible WebView on the hardware layer.
anchor = '        webView.setBackgroundColor(Color.rgb(234, 246, 255));\n'
layer = '        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null);\n'
if layer not in text:
    if anchor not in text:
        raise SystemExit('WebView background marker missing')
    text = text.replace(anchor, anchor + layer, 1)

# Mark a real compositor commit, not merely DOM availability.
commit_marker = '''            @Override public void onPageCommitVisible(WebView view, String url) {\n                if (view == webView) {\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n'''
commit_new = '''            @Override public void onPageCommitVisible(WebView view, String url) {\n                if (view == webView) {\n                    firstPageCommitted = true;\n                    coldStartRecoveryUsed = false;\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n'''
if 'firstPageCommitted = true;' not in text:
    if commit_marker not in text:
        raise SystemExit('onPageCommitVisible marker missing; run patch_webview_crash.py first')
    text = text.replace(commit_marker, commit_new, 1)

# Do not run warm-resume DOM recovery during the genuine first launch. The old probe could
# restart NavigationPolicy.HOME while dozens of deferred bundled scripts were still starting.
resume_anchor = '''        final WebView current = webView;\n        try {\n            current.onResume();\n            current.resumeTimers();\n            current.invalidate();\n'''
resume_new = '''        final WebView current = webView;\n        try {\n            current.onResume();\n            current.resumeTimers();\n            current.invalidate();\n'''
# We insert the guard immediately before the delayed warm recovery block.
post_anchor = '''        current.postDelayed(() -> {\n            if (current != webView || isFinishing() || isDestroyed()) return;\n'''
post_new = '''        if (!firstPageCommitted) {\n            updateConnection();\n            return;\n        }\n        current.postDelayed(() -> {\n            if (current != webView || isFinishing() || isDestroyed()) return;\n'''
if 'if (!firstPageCommitted)' not in text:
    if post_anchor not in text:
        raise SystemExit('warm-resume recovery marker missing')
    text = text.replace(post_anchor, post_new, 1)

# One bounded cold-start retry if the renderer never produces a visible frame. Never loop.
load_anchor = '        webView.loadUrl(NavigationPolicy.HOME);\n'
load_extra = '''        webView.loadUrl(NavigationPolicy.HOME);\n        final WebView firstLoad = webView;\n        firstLoad.postDelayed(() -> {\n            if (firstLoad != webView || firstPageCommitted || coldStartRecoveryUsed\n                    || isFinishing() || isDestroyed()) return;\n            coldStartRecoveryUsed = true;\n            try {\n                firstLoad.stopLoading();\n                firstLoad.loadUrl(NavigationPolicy.HOME);\n            } catch (RuntimeException deadRenderer) {\n                webView = null;\n                recreate();\n            }\n        }, 6500L);\n        firstLoad.postDelayed(() -> {\n            if (firstLoad != webView || firstPageCommitted || isFinishing() || isDestroyed()) return;\n            mainFrameError = true;\n            updateConnection();\n        }, 13000L);\n'''
if 'coldStartRecoveryUsed = true;' not in text:
    if load_anchor not in text:
        raise SystemExit('initial loadUrl marker missing')
    text = text.replace(load_anchor, load_extra, 1)

# Distinct install version for the blank-screen field fix.
gradle_path = root / 'app/build.gradle'
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 15', 'versionCode 16', 1)
gradle = gradle.replace("versionName '0.7.1'", "versionName '0.7.2'", 1)
if 'versionCode 16' not in gradle or "versionName '0.7.2'" not in gradle:
    raise SystemExit('v0.7.2 version bump did not apply; run reopen patch first')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
index = index_path.read_text(encoding='utf-8')
index = index.replace('<span class="badge green">v0.7.1</span>', '<span class="badge green">v0.7.2</span>', 1)
index = index.replace('<span class="badge green">v0.7.0</span>', '<span class="badge green">v0.7.2</span>', 1)
index_path.write_text(index, encoding='utf-8')

for required in [
    'private boolean firstPageCommitted;',
    'firstPageCommitted = true;',
    'if (!firstPageCommitted)',
    'coldStartRecoveryUsed = true;',
    'setLayerType(View.LAYER_TYPE_HARDWARE, null)',
]:
    if required not in text:
        raise SystemExit('cold-start fix missing: ' + required)
if 'settings.setOffscreenPreRaster(true);' in text:
    raise SystemExit('offscreen preraster still enabled')

main_path.write_text(text, encoding='utf-8')
print('FloodSafe cold-start first-paint / blank-screen fix applied (v0.7.2)')
