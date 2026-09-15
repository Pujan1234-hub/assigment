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

text = text.replace(
    'retry.setOnClickListener(v -> { if (webView != null) webView.reload(); });',
    'retry.setOnClickListener(v -> { if (webView != null) webView.reload(); else recreate(); });',
    1,
)

main_marker = '''            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) { mainFrameError = true; updateConnection(); }
            }
'''
main_handler = main_marker + '''            @Override public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
                // Handle a crashed/outdated Android System WebView renderer without
                // killing FloodSafe. The dead instance is never reused.
                mainFrameError = true;
                finishLocation(false);
                if (view != null) {
                    android.view.ViewParent parent = view.getParent();
                    if (parent instanceof android.view.ViewGroup) {
                        ((android.view.ViewGroup) parent).removeView(view);
                    }
                    try { view.destroy(); } catch (RuntimeException ignored) { }
                }
                if (view == webView) webView = null;
                progress.setVisibility(View.GONE);
                connection.setText(R.string.load_error);
                recovery.setVisibility(View.VISIBLE);
                return true;
            }
'''
if 'Handle a crashed/outdated Android System WebView renderer' not in text:
    if main_marker not in text:
        raise SystemExit('Main WebViewClient marker not found')
    text = text.replace(main_marker, main_handler, 1)

popup_marker = '''                    @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                        openSource(r.getUrl().toString());
                        v.post(v::destroy);
                        return true;
                    }
'''
popup_handler = popup_marker + '''                    @Override public boolean onRenderProcessGone(WebView v, RenderProcessGoneDetail detail) {
                        android.view.ViewParent parent = v.getParent();
                        if (parent instanceof android.view.ViewGroup) {
                            ((android.view.ViewGroup) parent).removeView(v);
                        }
                        try { v.destroy(); } catch (RuntimeException ignored) { }
                        return true;
                    }
'''
if text.count('onRenderProcessGone(') < 2:
    if popup_marker not in text:
        raise SystemExit('Popup WebViewClient marker not found')
    text = text.replace(popup_marker, popup_handler, 1)

# A renderer can die while the activity is in the background. The crash callback
# then leaves webView == null. Previously, reopening the app resumed the same
# activity with an empty content area. Recreate immediately in that case, and
# also self-heal about:blank / failed main-frame resumes.
old_resume = '''    @Override protected void onResume() {
        super.onResume();
        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {
            FloodMonitorService.startIfEnabled(this);
        }
        if (webView != null) {
            webView.onResume();
            webView.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);
        }
        updateConnection();
    }
'''
new_resume = '''    @Override protected void onResume() {
        super.onResume();
        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {
            FloodMonitorService.startIfEnabled(this);
        }
        if (webView == null) {
            recreate();
            return;
        }
        final WebView current = webView;
        try {
            current.onResume();
            current.resumeTimers();
        } catch (RuntimeException deadRenderer) {
            recreate();
            return;
        }
        current.postDelayed(() -> {
            if (current != webView || isFinishing() || isDestroyed()) return;
            try {
                String url = current.getUrl();
                if (url == null || url.isEmpty() || "about:blank".equals(url) || mainFrameError) {
                    mainFrameError = false;
                    current.loadUrl(NavigationPolicy.HOME);
                    return;
                }
                current.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);
            } catch (RuntimeException deadRenderer) {
                recreate();
            }
        }, 180L);
        updateConnection();
    }
'''
if 'current.resumeTimers();' not in text:
    if old_resume not in text:
        raise SystemExit('MainActivity onResume marker not found')
    text = text.replace(old_resume, new_resume, 1)

if text.count('onRenderProcessGone(') < 2:
    raise SystemExit('WebView renderer crash handlers were not installed')
if 'import android.webkit.RenderProcessGoneDetail;' not in text:
    raise SystemExit('RenderProcessGoneDetail import was not installed')
if 'else recreate();' not in text:
    raise SystemExit('WebView recovery retry was not installed')
if 'current.resumeTimers();' not in text or '"about:blank".equals(url)' not in text:
    raise SystemExit('WebView resume self-heal was not installed')

path.write_text(text, encoding='utf-8')
print('FloodSafe WebView renderer crash hardening applied')
