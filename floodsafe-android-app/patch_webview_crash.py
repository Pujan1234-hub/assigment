from pathlib import Path

path = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = path.read_text(encoding='utf-8')

if 'import android.webkit.RenderProcessGoneDetail;' not in text:
    anchor = 'import android.webkit.PermissionRequest;\n'
    if anchor not in text:
        anchor = 'import android.webkit.WebChromeClient;\n'
    if anchor not in text:
        raise SystemExit('WebView import marker not found')
    text = text.replace(anchor, anchor + 'import android.webkit.RenderProcessGoneDetail;\n', 1)

# Keep one conservative recovery flag. Normal warm resumes must never reload the page.
field_anchor = '    private boolean pendingBackgroundLocationEducation;\n'
if 'private boolean resumeRecoveryUsed;' not in text:
    if field_anchor not in text:
        raise SystemExit('MainActivity recovery field marker not found')
    text = text.replace(field_anchor, field_anchor + '    private boolean resumeRecoveryUsed;\n', 1)

# Retry always performs a clean local navigation, not WebView.reload() on a bad document.
text = text.replace(
    'retry.setOnClickListener(v -> { if (webView != null) webView.reload(); });',
    'retry.setOnClickListener(v -> { resumeRecoveryUsed = false; mainFrameError = false; if (webView != null) webView.loadUrl(NavigationPolicy.HOME); else recreate(); });',
    1,
)

# Keep the renderer bound to the app process and preraster the WebView. This avoids
# Android reclaiming the renderer immediately after the app is backgrounded, which
# was the main source of white/skeleton reopen states on some Samsung devices.
webview_anchor = '        webView.setBackgroundColor(Color.rgb(234, 246, 255));\n'
if 'setRendererPriorityPolicy' not in text:
    if webview_anchor not in text:
        raise SystemExit('WebView setup marker not found')
    text = text.replace(
        webview_anchor,
        webview_anchor + '        webView.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_BOUND, false);\n',
        1,
    )
settings_anchor = '        settings.setCacheMode(WebSettings.LOAD_DEFAULT);\n'
if 'settings.setOffscreenPreRaster(true);' not in text:
    if settings_anchor not in text:
        raise SystemExit('WebSettings cache marker not found')
    text = text.replace(settings_anchor, settings_anchor + '        settings.setOffscreenPreRaster(true);\n', 1)

# A visible commit proves the top-level bundled page painted. Reset recovery state.
started = '''            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {\n                if (!androidLocationPromptOpen) finishLocation(false);\n                mainFrameError = false;\n                updateConnection();\n            }\n'''
started_plus = started + '''            @Override public void onPageCommitVisible(WebView view, String url) {\n                if (view == webView) {\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n            @Override public void onPageFinished(WebView view, String url) {\n                if (view == webView) {\n                    resumeRecoveryUsed = false;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n'''
if 'onPageCommitVisible(WebView view' not in text:
    if started not in text:
        raise SystemExit('Main WebView onPageStarted marker not found')
    text = text.replace(started, started_plus, 1)

main_marker = '''            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {\n                if (request.isForMainFrame()) { mainFrameError = true; updateConnection(); }\n            }\n'''
main_handler = main_marker + '''            @Override public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {\n                // This is the only eager recreate path. A dead renderer cannot recover.\n                finishLocation(false);\n                if (view != null) {\n                    android.view.ViewParent parent = view.getParent();\n                    if (parent instanceof android.view.ViewGroup) {\n                        ((android.view.ViewGroup) parent).removeView(view);\n                    }\n                    try { view.destroy(); } catch (RuntimeException ignored) { }\n                }\n                if (view == webView) webView = null;\n                getWindow().getDecorView().post(() -> {\n                    if (!isFinishing() && !isDestroyed()) recreate();\n                });\n                return true;\n            }\n'''
if 'This is the only eager recreate path' not in text:
    if main_marker not in text:
        raise SystemExit('Main WebViewClient marker not found')
    text = text.replace(main_marker, main_handler, 1)

popup_marker = '''                    @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {\n                        openSource(r.getUrl().toString());\n                        v.post(v::destroy);\n                        return true;\n                    }\n'''
popup_handler = popup_marker + '''                    @Override public boolean onRenderProcessGone(WebView v, RenderProcessGoneDetail detail) {\n                        android.view.ViewParent parent = v.getParent();\n                        if (parent instanceof android.view.ViewGroup) {\n                            ((android.view.ViewGroup) parent).removeView(v);\n                        }\n                        try { v.destroy(); } catch (RuntimeException ignored) { }\n                        return true;\n                    }\n'''
if text.count('onRenderProcessGone(') < 2:
    if popup_marker not in text:
        raise SystemExit('Popup WebViewClient marker not found')
    text = text.replace(popup_marker, popup_handler, 1)

old_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {\n            FloodMonitorService.startIfEnabled(this);\n        }\n        if (webView != null) {\n            webView.onResume();\n            webView.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);\n        }\n        updateConnection();\n    }\n'''
new_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {\n            FloodMonitorService.startIfEnabled(this);\n        }\n        if (webView == null) {\n            recreate();\n            return;\n        }\n        final WebView current = webView;\n        try {\n            current.onResume();\n            current.resumeTimers();\n            current.invalidate();\n        } catch (RuntimeException deadRenderer) {\n            webView = null;\n            recreate();\n            return;\n        }\n\n        // Root-cause fix: never reload a healthy WebView merely because the app resumed.\n        // The previous 500 ms probe + cache-busting navigation restarted every heavy map,\n        // river, news and SATHI script and left the user staring at the skeleton UI.\n        current.postDelayed(() -> {\n            if (current != webView || isFinishing() || isDestroyed()) return;\n            try {\n                String url = current.getUrl();\n                if (url == null || url.isEmpty() || "about:blank".equals(url)) {\n                    if (!resumeRecoveryUsed) {\n                        resumeRecoveryUsed = true;\n                        current.loadUrl(NavigationPolicy.HOME);\n                    }\n                    return;\n                }\n                current.evaluateJavascript(\n                        "(function(){try{return !!(document.body&&document.querySelector('.app'))}catch(e){return false}})()",\n                        value -> {\n                            if (current != webView || isFinishing() || isDestroyed()) return;\n                            if ("true".equals(value)) {\n                                resumeRecoveryUsed = false;\n                                current.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);\n                                return;\n                            }\n                            // One delayed second chance only. Do not loop or cache-bust.\n                            current.postDelayed(() -> {\n                                if (current != webView || isFinishing() || isDestroyed() || resumeRecoveryUsed) return;\n                                try {\n                                    current.evaluateJavascript(\n                                            "(function(){try{return !!(document.body&&document.querySelector('.app'))}catch(e){return false}})()",\n                                            second -> {\n                                                if (current != webView || isFinishing() || isDestroyed()) return;\n                                                if (!"true".equals(second) && !resumeRecoveryUsed) {\n                                                    resumeRecoveryUsed = true;\n                                                    current.loadUrl(NavigationPolicy.HOME);\n                                                }\n                                            });\n                                } catch (RuntimeException dead) {\n                                    webView = null;\n                                    recreate();\n                                }\n                            }, 1800L);\n                        });\n            } catch (RuntimeException deadRenderer) {\n                webView = null;\n                recreate();\n            }\n        }, 1400L);\n        updateConnection();\n    }\n'''
if 'Root-cause fix: never reload a healthy WebView' not in text:
    if old_resume not in text:
        raise SystemExit('MainActivity onResume marker not found')
    text = text.replace(old_resume, new_resume, 1)

if text.count('onRenderProcessGone(') < 2:
    raise SystemExit('WebView renderer crash handlers were not installed')
if 'setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_BOUND, false)' not in text:
    raise SystemExit('Renderer retention policy missing')
if 'settings.setOffscreenPreRaster(true);' not in text:
    raise SystemExit('WebView preraster setting missing')
if 'Root-cause fix: never reload a healthy WebView' not in text:
    raise SystemExit('Conservative resume recovery missing')
if '?resume=' in text or '?recover=' in text:
    raise SystemExit('Aggressive cache-busting recovery is still present')

path.write_text(text, encoding='utf-8')
print('FloodSafe stable WebView reopen recovery applied')
