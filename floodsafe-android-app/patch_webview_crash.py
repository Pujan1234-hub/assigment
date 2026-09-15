from pathlib import Path

path = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = path.read_text(encoding='utf-8')

# Import beside an import that is guaranteed to exist in the current activity.
if 'import android.webkit.RenderProcessGoneDetail;' not in text:
    anchor = 'import android.webkit.PermissionRequest;\n'
    if anchor not in text:
        anchor = 'import android.webkit.WebChromeClient;\n'
    if anchor not in text:
        raise SystemExit('WebView import marker not found')
    text = text.replace(anchor, anchor + 'import android.webkit.RenderProcessGoneDetail;\n', 1)

# Recovery state lives in the Activity rather than inside JavaScript so it still
# works when the renderer is blank, wedged, or has died while backgrounded.
field_anchor = '    private boolean pendingBackgroundLocationEducation;\n'
fields = field_anchor + '''    private long webLoadGeneration;\n    private int webLoadRecoveryCount;\n    private boolean webContentVisible;\n'''
if 'private long webLoadGeneration;' not in text:
    if field_anchor not in text:
        raise SystemExit('MainActivity recovery field marker not found')
    text = text.replace(field_anchor, fields, 1)

text = text.replace(
    'retry.setOnClickListener(v -> { if (webView != null) webView.reload(); });',
    'retry.setOnClickListener(v -> { webLoadRecoveryCount = 0; if (webView != null) { mainFrameError = false; webView.loadUrl(NavigationPolicy.HOME); } else recreate(); });',
    1,
)

old_started = '''            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {\n                if (!androidLocationPromptOpen) finishLocation(false);\n                mainFrameError = false;\n                updateConnection();\n            }\n'''
new_started = '''            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {\n                if (!androidLocationPromptOpen) finishLocation(false);\n                mainFrameError = false;\n                webContentVisible = false;\n                final long generation = ++webLoadGeneration;\n                updateConnection();\n                // The top-level page is bundled locally, so it should paint quickly.\n                // If Android System WebView gets stuck on an empty surface, force a\n                // fresh local navigation instead of leaving the user on a blank page.\n                view.postDelayed(() -> {\n                    if (view != webView || generation != webLoadGeneration\n                            || webContentVisible || isFinishing() || isDestroyed()) return;\n                    try {\n                        if (webLoadRecoveryCount < 2) {\n                            webLoadRecoveryCount++;\n                            view.stopLoading();\n                            view.loadUrl(NavigationPolicy.HOME + "?recover=" + System.currentTimeMillis());\n                        } else {\n                            mainFrameError = true;\n                            connection.setText(R.string.load_error);\n                            recovery.setVisibility(View.VISIBLE);\n                        }\n                    } catch (RuntimeException deadRenderer) {\n                        if (view == webView) webView = null;\n                        recreate();\n                    }\n                }, 4500L);\n            }\n            @Override public void onPageCommitVisible(WebView view, String url) {\n                if (view == webView) {\n                    webContentVisible = true;\n                    webLoadRecoveryCount = 0;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n            @Override public void onPageFinished(WebView view, String url) {\n                if (view == webView) {\n                    webContentVisible = true;\n                    webLoadRecoveryCount = 0;\n                    mainFrameError = false;\n                    updateConnection();\n                }\n            }\n'''
if 'view.loadUrl(NavigationPolicy.HOME + "?recover="' not in text:
    if old_started not in text:
        raise SystemExit('Main WebView onPageStarted marker not found')
    text = text.replace(old_started, new_started, 1)

main_marker = '''            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {\n                if (request.isForMainFrame()) { mainFrameError = true; updateConnection(); }\n            }\n'''
main_handler = main_marker + '''            @Override public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {\n                // Handle a crashed/outdated Android System WebView renderer without\n                // killing FloodSafe. The dead instance is never reused.\n                mainFrameError = true;\n                webContentVisible = false;\n                ++webLoadGeneration;\n                finishLocation(false);\n                if (view != null) {\n                    android.view.ViewParent parent = view.getParent();\n                    if (parent instanceof android.view.ViewGroup) {\n                        ((android.view.ViewGroup) parent).removeView(view);\n                    }\n                    try { view.destroy(); } catch (RuntimeException ignored) { }\n                }\n                if (view == webView) webView = null;\n                progress.setVisibility(View.GONE);\n                connection.setText(R.string.load_error);\n                recovery.setVisibility(View.VISIBLE);\n                // Recreate the Activity with a brand-new WebView on the next loop tick.\n                getWindow().getDecorView().post(() -> {\n                    if (!isFinishing() && !isDestroyed()) recreate();\n                });\n                return true;\n            }\n'''
if 'Handle a crashed/outdated Android System WebView renderer' not in text:
    if main_marker not in text:
        raise SystemExit('Main WebViewClient marker not found')
    text = text.replace(main_marker, main_handler, 1)

popup_marker = '''                    @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {\n                        openSource(r.getUrl().toString());\n                        v.post(v::destroy);\n                        return true;\n                    }\n'''
popup_handler = popup_marker + '''                    @Override public boolean onRenderProcessGone(WebView v, RenderProcessGoneDetail detail) {\n                        android.view.ViewParent parent = v.getParent();\n                        if (parent instanceof android.view.ViewGroup) {\n                            ((android.view.ViewGroup) parent).removeView(v);\n                        }\n                        try { v.destroy(); } catch (RuntimeException ignored) { }\n                        return true;\n                    }\n'''
if text.count('onRenderProcessGone(') < 2:
    if popup_marker not in text:
        raise SystemExit('Popup WebViewClient marker not found')
    text = text.replace(popup_marker, popup_handler, 1)

# A renderer can die or remain alive with an empty document while the Activity is
# backgrounded. Probe the DOM on every resume. If the actual FloodSafe root is not
# present, navigate directly to the bundled HOME page. This does not depend on JS
# app state and works even if a previous load was interrupted mid-render.
old_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {\n            FloodMonitorService.startIfEnabled(this);\n        }\n        if (webView != null) {\n            webView.onResume();\n            webView.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);\n        }\n        updateConnection();\n    }\n'''
new_resume = '''    @Override protected void onResume() {\n        super.onResume();\n        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {\n            FloodMonitorService.startIfEnabled(this);\n        }\n        if (webView == null) {\n            recreate();\n            return;\n        }\n        final WebView current = webView;\n        try {\n            current.onResume();\n            current.resumeTimers();\n        } catch (RuntimeException deadRenderer) {\n            webView = null;\n            recreate();\n            return;\n        }\n        current.postDelayed(() -> {\n            if (current != webView || isFinishing() || isDestroyed()) return;\n            try {\n                String url = current.getUrl();\n                if (url == null || url.isEmpty() || "about:blank".equals(url) || mainFrameError) {\n                    mainFrameError = false;\n                    webLoadRecoveryCount = 0;\n                    current.stopLoading();\n                    current.loadUrl(NavigationPolicy.HOME + "?resume=" + System.currentTimeMillis());\n                    return;\n                }\n                current.evaluateJavascript(\n                        "(function(){try{return !!(document.body&&document.querySelector('.app')&&document.body.children.length)}catch(e){return false}})()",\n                        value -> {\n                            if (current != webView || isFinishing() || isDestroyed()) return;\n                            if (!"true".equals(value)) {\n                                webContentVisible = false;\n                                webLoadRecoveryCount = 0;\n                                try {\n                                    current.stopLoading();\n                                    current.loadUrl(NavigationPolicy.HOME + "?resume=" + System.currentTimeMillis());\n                                } catch (RuntimeException dead) {\n                                    webView = null;\n                                    recreate();\n                                }\n                            } else {\n                                webContentVisible = true;\n                                current.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);\n                            }\n                        });\n            } catch (RuntimeException deadRenderer) {\n                webView = null;\n                recreate();\n            }\n        }, 500L);\n        updateConnection();\n    }\n'''
if 'document.querySelector(\'.app\')' not in text:
    if old_resume not in text:
        raise SystemExit('MainActivity onResume marker not found')
    text = text.replace(old_resume, new_resume, 1)

if text.count('onRenderProcessGone(') < 2:
    raise SystemExit('WebView renderer crash handlers were not installed')
if 'import android.webkit.RenderProcessGoneDetail;' not in text:
    raise SystemExit('RenderProcessGoneDetail import was not installed')
if '?recover=' not in text or 'onPageCommitVisible' not in text:
    raise SystemExit('WebView blank-screen watchdog was not installed')
if 'document.querySelector(\'.app\')' not in text or '?resume=' not in text:
    raise SystemExit('WebView resume DOM probe was not installed')

path.write_text(text, encoding='utf-8')
print('FloodSafe WebView renderer + blank-screen recovery applied')
