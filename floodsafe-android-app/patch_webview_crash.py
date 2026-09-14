from pathlib import Path

path = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
text = path.read_text(encoding='utf-8')

if 'import android.webkit.RenderProcessGoneDetail;' not in text:
    text = text.replace(
        'import android.webkit.PermissionRequest;\n',
        'import android.webkit.PermissionRequest;\nimport android.webkit.RenderProcessGoneDetail;\n',
        1,
    )

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

if text.count('onRenderProcessGone(') < 2:
    raise SystemExit('WebView renderer crash handlers were not installed')
if 'else recreate();' not in text:
    raise SystemExit('WebView recovery retry was not installed')

path.write_text(text, encoding='utf-8')
print('FloodSafe WebView renderer crash hardening applied')
