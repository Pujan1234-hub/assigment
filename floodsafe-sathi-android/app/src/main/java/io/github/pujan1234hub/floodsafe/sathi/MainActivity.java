package io.github.pujan1234hub.floodsafe.sathi;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.webkit.WebViewAssetLoader;
import java.util.Locale;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private static final int REQ_AUDIO = 1001;
    private static final int REQ_LOCATION = 1002;
    private static final String HOME = "https://appassets.androidplatform.net/assets/floodsafe-nepal/v25/sathi-flood-ai/index.html";
    private WebView webView;
    private boolean pendingWakeStart;
    private boolean pendingOneShot;
    private GeolocationPermissions.Callback pendingGeoCallback;
    private String pendingGeoOrigin;

    private final BroadcastReceiver wakeReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (WakeWordService.ACTION_WAKE_DETECTED.equals(intent.getAction())) {
                runJs("window.SathiFloodNativeWake&&window.SathiFloodNativeWake();");
            } else if (WakeWordService.ACTION_COMMAND.equals(intent.getAction())) {
                String q = intent.getStringExtra(WakeWordService.EXTRA_COMMAND);
                if (q != null && !q.isBlank()) {
                    runJs("window.SathiFloodNativeReceive&&window.SathiFloodNativeReceive(" + JSONObject.quote(q) + ");");
                }
            } else if (WakeWordService.ACTION_STATE.equals(intent.getAction())) {
                boolean on = intent.getBooleanExtra("enabled", false);
                runJs("window.SathiFloodNativeState&&window.SathiFloodNativeState(" + on + ");");
            }
        }
    };

    public final class SathiBridge {
        @JavascriptInterface public void startWake() {
            runOnUiThread(() -> requestAudioThen(true, false));
        }
        @JavascriptInterface public void stopWake() {
            runOnUiThread(() -> {
                Intent i = new Intent(MainActivity.this, WakeWordService.class).setAction(WakeWordService.ACTION_STOP);
                startService(i);
            });
        }
        @JavascriptInterface public void listenOnce() {
            runOnUiThread(() -> requestAudioThen(false, true));
        }
        @JavascriptInterface public boolean isWakeEnabled() {
            return getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).getBoolean("wake_enabled", false);
        }
        @JavascriptInterface public void syncMonitoringPoint(double lat, double lon, String label) {
            if (!Double.isFinite(lat) || !Double.isFinite(lon)) return;
            getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).edit()
                    .putLong("monitor_lat", Double.doubleToRawLongBits(lat))
                    .putLong("monitor_lon", Double.doubleToRawLongBits(lon))
                    .putString("monitor_label", label == null ? "" : label)
                    .apply();
        }
        @JavascriptInterface public String platform() { return "android-native"; }
    }

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setGeolocationEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        if (Build.VERSION.SDK_INT >= 26) s.setSafeBrowsingEnabled(true);

        webView.addJavascriptInterface(new SathiBridge(), "SathiNative");

        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return loader.shouldInterceptRequest(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                if ("appassets.androidplatform.net".equalsIgnoreCase(u.getHost())) return false;
                if (request.isForMainFrame() && request.hasGesture()) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) {}
                }
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                        || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                    callback.invoke(origin, true, false);
                } else {
                    pendingGeoCallback = callback;
                    pendingGeoOrigin = origin;
                    requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_LOCATION);
                }
            }
            @Override public void onPermissionRequest(PermissionRequest request) {
                request.deny();
            }
        });

        webView.loadUrl(HOME);
    }

    @Override protected void onResume() {
        super.onResume();
        getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).edit().putBoolean("app_visible", true).apply();
        IntentFilter f = new IntentFilter();
        f.addAction(WakeWordService.ACTION_WAKE_DETECTED);
        f.addAction(WakeWordService.ACTION_COMMAND);
        f.addAction(WakeWordService.ACTION_STATE);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(wakeReceiver, f, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(wakeReceiver, f);
        String pending = getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).getString("pending_command", "");
        if (!pending.isBlank()) {
            getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).edit().remove("pending_command").apply();
            final String q = pending;
            webView.postDelayed(() -> runJs("window.SathiFloodNativeReceive&&window.SathiFloodNativeReceive(" + JSONObject.quote(q) + ");"), 500);
        }
    }

    @Override protected void onPause() {
        getSharedPreferences(WakeWordService.PREFS, MODE_PRIVATE).edit().putBoolean("app_visible", false).apply();
        try { unregisterReceiver(wakeReceiver); } catch (Exception ignored) {}
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (webView != null) webView.destroy();
        super.onDestroy();
    }

    private void requestAudioThen(boolean wake, boolean oneShot) {
        pendingWakeStart = wake;
        pendingOneShot = oneShot;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_AUDIO);
            return;
        }
        startVoiceAction(wake, oneShot);
    }

    private void startVoiceAction(boolean wake, boolean oneShot) {
        Intent i = new Intent(this, WakeWordService.class);
        i.setAction(oneShot ? WakeWordService.ACTION_CAPTURE_ONCE : WakeWordService.ACTION_START);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(i); else startService(i);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(requestCode, permissions, grants);
        if (requestCode == REQ_AUDIO) {
            boolean ok = grants.length > 0 && grants[0] == PackageManager.PERMISSION_GRANTED;
            if (ok) startVoiceAction(pendingWakeStart, pendingOneShot);
            else runJs("window.SathiFloodNativeError&&window.SathiFloodNativeError('माइक्रोफोन अनुमति चाहिन्छ।');");
            pendingWakeStart = pendingOneShot = false;
        } else if (requestCode == REQ_LOCATION && pendingGeoCallback != null) {
            boolean ok = false;
            for (int g : grants) if (g == PackageManager.PERMISSION_GRANTED) ok = true;
            pendingGeoCallback.invoke(pendingGeoOrigin, ok, false);
            pendingGeoCallback = null;
            pendingGeoOrigin = null;
        }
    }

    private void runJs(String js) {
        if (webView == null) return;
        webView.post(() -> webView.evaluateJavascript(js, null));
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
