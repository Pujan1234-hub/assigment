package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.Bundle;
import android.os.Message;
import android.view.View;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.webkit.WebViewAssetLoader;
import java.util.ArrayList;
import java.util.List;

/** Bundled hybrid app. No JavaScript-to-native bridge or remote top-level page. */
public class MainActivity extends Activity {
    private static final int LOCATION_REQUEST = 40;
    WebView webView;
    private TextView connection;
    private LinearLayout recovery;
    private ConnectivityManager connectivity;
    private ConnectivityManager.NetworkCallback networkCallback;
    private static final class PendingLocation {
        final String origin;
        final GeolocationPermissions.Callback callback;
        PendingLocation(String origin, GeolocationPermissions.Callback callback) {
            this.origin = origin;
            this.callback = callback;
        }
    }
    private final List<PendingLocation> pendingLocations = new ArrayList<>();
    private boolean androidLocationPromptOpen;
    private boolean mainFrameError;

    @SuppressLint("SetJavaScriptEnabled")
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(234, 246, 255));
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets.consumeSystemWindowInsets();
        });
        setContentView(root);
        root.requestApplyInsets();
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);

        recovery = new LinearLayout(this);
        recovery.setPadding(16, 8, 16, 8);
        connection = new TextView(this);
        connection.setTextColor(Color.rgb(106, 58, 12));
        recovery.addView(connection, new LinearLayout.LayoutParams(0, -2, 1));
        Button retry = new Button(this);
        retry.setText(R.string.retry);
        retry.setOnClickListener(v -> { if (webView != null) webView.reload(); });
        recovery.addView(retry);
        recovery.setVisibility(View.GONE);
        root.addView(recovery);
        ProgressBar progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        root.addView(progress, new LinearLayout.LayoutParams(-1, 5));
        try { webView = new WebView(this); }
        catch (RuntimeException missingWebView) {
            connection.setText(R.string.webview_missing);
            recovery.setVisibility(View.VISIBLE);
            progress.setVisibility(View.GONE);
            return;
        }
        webView.setBackgroundColor(Color.rgb(234, 246, 255));
        root.addView(webView, new LinearLayout.LayoutParams(-1, 0, 1));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setGeolocationEnabled(true);
        settings.setSupportMultipleWindows(true);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setSafeBrowsingEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new BundledContent(getAssets())).build();
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                WebResourceResponse local = loader.shouldInterceptRequest(request.getUrl());
                // Never fall through to a network page at the privileged local origin.
                return local != null ? local : NavigationPolicy.trustedOrigin(request.getUrl().toString())
                        ? BundledContent.missing() : null;
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (NavigationPolicy.internalPage(url)) return false;
                if (request.isForMainFrame() && request.hasGesture()) openSource(url);
                return true;
            }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {
                // Android's own permission dialog may briefly cause WebView lifecycle
                // callbacks. Do not cancel/re-open the same location prompt then.
                if (!androidLocationPromptOpen) finishLocation(false);
                mainFrameError = false;
                updateConnection();
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) { mainFrameError = true; updateConnection(); }
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view, int value) {
                progress.setProgress(value);
                progress.setVisibility(value == 100 ? View.GONE : View.VISIBLE);
            }
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                requestLocation(origin, callback);
            }
            @Override public void onGeolocationPermissionsHidePrompt() {
                if (!androidLocationPromptOpen) finishLocation(false);
            }
            @Override public void onPermissionRequest(PermissionRequest request) { request.deny(); }
            @Override public boolean onCreateWindow(WebView view, boolean dialog, boolean userGesture, Message result) {
                if (!userGesture) return false;
                // Capture a source link in an unprivileged, script-disabled temporary view.
                WebView popup = new WebView(MainActivity.this);
                popup.getSettings().setJavaScriptEnabled(false);
                popup.getSettings().setAllowFileAccess(false);
                popup.getSettings().setAllowContentAccess(false);
                popup.setWebViewClient(new WebViewClient() {
                    @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                        openSource(r.getUrl().toString());
                        v.post(v::destroy);
                        return true;
                    }
                });
                ((WebView.WebViewTransport) result.obj).setWebView(popup);
                result.sendToTarget();
                popup.postDelayed(popup::destroy, 10000);
                return true;
            }
        });
        webView.setDownloadListener((url, userAgent, disposition, mime, length) -> openSource(url));
        // Always start with the bundled home screen; ignore incoming URLs and persisted pages.
        webView.loadUrl(NavigationPolicy.HOME);
        connectivity = getSystemService(ConnectivityManager.class);
        networkCallback = new ConnectivityManager.NetworkCallback() {
            @Override public void onAvailable(Network network) { refreshConnection(); }
            @Override public void onLost(Network network) { refreshConnection(); }
            @Override public void onCapabilitiesChanged(Network network, NetworkCapabilities caps) { refreshConnection(); }
        };
        connectivity.registerDefaultNetworkCallback(networkCallback);
        updateConnection();
    }

    private void refreshConnection() {
        runOnUiThread(() -> { if (!isFinishing() && !isDestroyed()) updateConnection(); });
    }

    private void updateConnection() {
        if (connection == null) return;
        boolean offline = false;
        if (connectivity != null) {
            NetworkCapabilities caps = connectivity.getNetworkCapabilities(connectivity.getActiveNetwork());
            offline = caps == null || !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);
        }
        connection.setText(mainFrameError ? R.string.load_error : R.string.offline);
        recovery.setVisibility(offline || mainFrameError ? View.VISIBLE : View.GONE);
    }

    void requestLocation(String origin, GeolocationPermissions.Callback callback) {
        if (!NavigationPolicy.trustedOrigin(origin) || !NavigationPolicy.internalPage(webView.getUrl())) {
            callback.invoke(origin, false, false); return;
        }
        if (hasLocation()) { callback.invoke(origin, true, false); return; }
        // A WebView can ask more than once while Android is showing its permission
        // sheet. Queue those callbacks instead of repeatedly opening the sheet.
        pendingLocations.add(new PendingLocation(origin, callback));
        if (androidLocationPromptOpen) return;
        androidLocationPromptOpen = true;
        try {
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_REQUEST);
        } catch (RuntimeException unavailable) {
            finishLocation(false);
        }
    }

    private boolean hasLocation() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private void finishLocation(boolean allowed) {
        androidLocationPromptOpen = false;
        if (pendingLocations.isEmpty()) return;
        List<PendingLocation> callbacks = new ArrayList<>(pendingLocations);
        pendingLocations.clear();
        boolean validPage = allowed && webView != null && NavigationPolicy.internalPage(webView.getUrl());
        for (PendingLocation item : callbacks) {
            item.callback.invoke(item.origin, validPage && NavigationPolicy.trustedOrigin(item.origin), false);
        }
    }

    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(code, permissions, grants);
        if (code == LOCATION_REQUEST) finishLocation(hasLocation() && webView != null
                && NavigationPolicy.internalPage(webView.getUrl()));
    }

    private void openSource(String url) {
        if (!NavigationPolicy.externalHttps(url)) return;
        try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)).addCategory(Intent.CATEGORY_BROWSABLE)); }
        catch (ActivityNotFoundException | SecurityException unavailable) {
            Toast.makeText(this, R.string.browser_missing, Toast.LENGTH_LONG).show();
        }
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
    @Override protected void onPause() {
        if (webView != null) webView.onPause();
        super.onPause();
    }
    @Override protected void onResume() {
        super.onResume();
        if (webView != null) webView.onResume();
        updateConnection();
    }
    @Override protected void onDestroy() {
        finishLocation(false);
        if (connectivity != null && networkCallback != null) connectivity.unregisterNetworkCallback(networkCallback);
        if (webView != null) {
            ((android.view.ViewGroup) webView.getParent()).removeView(webView);
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
