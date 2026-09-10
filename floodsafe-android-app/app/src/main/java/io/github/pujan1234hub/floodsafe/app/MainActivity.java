package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Message;
import android.provider.Settings;
import android.view.View;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
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
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import com.google.firebase.messaging.FirebaseMessaging;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Bundled hybrid app. No remote top-level page. */
public class MainActivity extends Activity {
    private static final int LOCATION_REQUEST = 40;
    private static final int NOTIFICATION_REQUEST = 41;
    private static final int BACKGROUND_LOCATION_REQUEST = 42;
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
    private volatile long locationTapUntil;
    private boolean mainFrameError;
    private boolean pendingBackgroundLocationEducation;

    /** A narrowly scoped signal from the bundled FloodSafe UI only. */
    private final class LocationTapBridge {
        @JavascriptInterface public void allowLocationPrompt() {
            runOnUiThread(MainActivity.this::beginLocationFromTap);
        }
        @JavascriptInterface public void enableRainAlerts() {
            runOnUiThread(() -> setRainAlerts(true));
        }
        @JavascriptInterface public void setRainAlerts(boolean enabled) {
            runOnUiThread(() -> MainActivity.this.setRainAlerts(enabled));
        }
        @JavascriptInterface public void syncRainAlertsStatus() {
            runOnUiThread(MainActivity.this::syncRainAlertsStatus);
        }
        @JavascriptInterface public void setBackgroundRainAlerts(double lat, double lon) {
            runOnUiThread(() -> enableBackgroundRainAlerts(lat, lon));
        }
        @JavascriptInterface public void disableBackgroundRainAlerts() {
            runOnUiThread(MainActivity.this::disableBackgroundRainAlerts);
        }
        @JavascriptInterface public void syncBackgroundRainAlerts() {
            runOnUiThread(MainActivity.this::syncBackgroundRainAlerts);
        }
        @JavascriptInterface public void requestBackgroundLocationForAlerts() {
            runOnUiThread(MainActivity.this::requestBackgroundLocationForAlerts);
        }
    }

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
        webView.addJavascriptInterface(new LocationTapBridge(), "FloodSafeNative");
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new BundledContent(getAssets())).build();
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                WebResourceResponse local = loader.shouldInterceptRequest(request.getUrl());
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

    private SharedPreferences alertPrefs() {
        return getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE);
    }

    private boolean notificationsAllowed() {
        return Build.VERSION.SDK_INT < 33
                || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private void setRainAlerts(boolean enabled) {
        if (!enabled) {
            FirebaseMessaging.getInstance().unsubscribeFromTopic("nepal-alerts");
            disableBackgroundRainAlerts();
            return;
        }
        alertPrefs().edit().putBoolean("enabled", true).apply();
        if (!notificationsAllowed()) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, NOTIFICATION_REQUEST);
            return;
        }
        scheduleBackgroundRainAlerts();
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        notifyAlertStatus(true);
    }

    private void syncRainAlertsStatus() {
        boolean enabled = alertPrefs().getBoolean("enabled", false) && notificationsAllowed();
        if (enabled) {
            scheduleBackgroundRainAlerts();
            FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        }
        notifyAlertStatus(enabled);
    }

    private void enableBackgroundRainAlerts(double lat, double lon) {
        if (!Double.isFinite(lat) || !Double.isFinite(lon)
                || lat < -90d || lat > 90d || lon < -180d || lon > 180d) {
            notifyAlertStatus(alertPrefs().getBoolean("enabled", false) && notificationsAllowed());
            return;
        }

        long now = System.currentTimeMillis();
        alertPrefs().edit()
                .putBoolean("enabled", true)
                .putBoolean("follow_device", true)
                .putLong("device_lat", Double.doubleToRawLongBits(lat))
                .putLong("device_lon", Double.doubleToRawLongBits(lon))
                .putLong("device_location_time", now)
                .putLong("lat", Double.doubleToRawLongBits(lat))
                .putLong("lon", Double.doubleToRawLongBits(lon))
                .putLong("location_time", now)
                .putBoolean("location_stale", false)
                .apply();

        if (!notificationsAllowed()) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, NOTIFICATION_REQUEST);
            return;
        }
        scheduleBackgroundRainAlerts();
        notifyAlertStatus(true);
        maybeRequestBackgroundLocation();
    }

    private void scheduleBackgroundRainAlerts() {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest rainWork = new PeriodicWorkRequest.Builder(RainAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        PeriodicWorkRequest riverWork = new PeriodicWorkRequest.Builder(RiverAlertWorker.class, 15, TimeUnit.MINUTES)
                .setConstraints(constraints).build();
        OneTimeWorkRequest riverNow = new OneTimeWorkRequest.Builder(RiverAlertWorker.class)
                .setConstraints(constraints).build();
        WorkManager manager = WorkManager.getInstance(this);
        manager.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, rainWork);
        manager.enqueueUniquePeriodicWork("floodsafe-local-river-alerts",
                ExistingPeriodicWorkPolicy.UPDATE, riverWork);
        manager.enqueueUniqueWork("floodsafe-local-river-alert-now",
                ExistingWorkPolicy.REPLACE, riverNow);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        FloodMonitorService.startIfEnabled(this);
    }

    private void disableBackgroundRainAlerts() {
        alertPrefs().edit().putBoolean("enabled", false).apply();
        WorkManager manager = WorkManager.getInstance(this);
        manager.cancelUniqueWork("floodsafe-local-rain-alerts");
        manager.cancelUniqueWork("floodsafe-local-river-alerts");
        manager.cancelUniqueWork("floodsafe-local-river-alert-now");
        FloodMonitorService.stop(this);
        notifyAlertStatus(false);
    }

    private void syncBackgroundRainAlerts() {
        boolean enabled = alertPrefs().getBoolean("enabled", false) && notificationsAllowed();
        if (enabled) scheduleBackgroundRainAlerts();
        notifyAlertStatus(enabled);
    }

    private void requestBackgroundLocationForAlerts() {
        pendingBackgroundLocationEducation = true;
        maybeRequestBackgroundLocation();
    }

    private void maybeRequestBackgroundLocation() {
        if (!pendingBackgroundLocationEducation) return;
        if (!alertPrefs().getBoolean("enabled", false)) {
            pendingBackgroundLocationEducation = false;
            return;
        }
        if (!hasLocation()) {
            beginLocationFromTap();
            return;
        }
        if (Build.VERSION.SDK_INT < 29 || FloodMonitorService.hasBackgroundLocation(this)) {
            pendingBackgroundLocationEducation = false;
            FloodMonitorService.startIfEnabled(this);
            return;
        }

        pendingBackgroundLocationEducation = false;
        if (Build.VERSION.SDK_INT == 29) {
            try {
                requestPermissions(new String[]{Manifest.permission.ACCESS_BACKGROUND_LOCATION},
                        BACKGROUND_LOCATION_REQUEST);
            } catch (RuntimeException ignored) { }
            return;
        }

        String option = "Allow all the time";
        if (Build.VERSION.SDK_INT >= 30) {
            try { option = getPackageManager().getBackgroundPermissionOptionLabel().toString(); }
            catch (RuntimeException ignored) { }
        }
        final String label = option;
        new AlertDialog.Builder(this)
                .setTitle("Background safety monitoring")
                .setMessage("App बन्द/स्क्रिन लक हुँदा पनि नजिकको official flood/rain alert मिलाउन Location मा ‘"
                        + label + "’ अनुमति चाहिन्छ। Location केवल safety monitoring का लागि प्रयोग हुन्छ।")
                .setPositiveButton("Open location settings", (dialog, which) -> openAppSettings())
                .setNegativeButton("Not now", null)
                .show();
    }

    private void openAppSettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException ignored) { }
    }

    private void notifyAlertStatus(boolean enabled) {
        if (webView == null) return;
        webView.post(() -> webView.evaluateJavascript(
                "window.dispatchEvent(new CustomEvent('floodsafe-alerts-status',{detail:{enabled:"
                        + enabled + "}}));", null));
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

    private void beginLocationFromTap() {
        locationTapUntil = System.currentTimeMillis() + 6000L;
        if (hasLocation() || androidLocationPromptOpen) {
            maybeRequestBackgroundLocation();
            return;
        }
        androidLocationPromptOpen = true;
        try {
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_REQUEST);
        } catch (RuntimeException unavailable) {
            finishLocation(false);
        }
    }

    void requestLocation(String origin, GeolocationPermissions.Callback callback) {
        if (!NavigationPolicy.trustedOrigin(origin) || !NavigationPolicy.internalPage(webView.getUrl())) {
            callback.invoke(origin, false, false); return;
        }
        if (System.currentTimeMillis() > locationTapUntil) {
            callback.invoke(origin, false, false); return;
        }
        if (hasLocation()) { callback.invoke(origin, true, false); return; }
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
        return FloodMonitorService.hasForegroundLocation(this);
    }

    private void finishLocation(boolean allowed) {
        androidLocationPromptOpen = false;
        if (!pendingLocations.isEmpty()) {
            List<PendingLocation> callbacks = new ArrayList<>(pendingLocations);
            pendingLocations.clear();
            boolean validPage = allowed && webView != null && NavigationPolicy.internalPage(webView.getUrl());
            for (PendingLocation item : callbacks) {
                item.callback.invoke(item.origin, validPage && NavigationPolicy.trustedOrigin(item.origin), false);
            }
        }
        if (allowed && alertPrefs().getBoolean("enabled", false)) {
            FloodMonitorService.startIfEnabled(this);
        }
    }

    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(code, permissions, grants);
        if (code == LOCATION_REQUEST) {
            boolean allowed = hasLocation() && webView != null && NavigationPolicy.internalPage(webView.getUrl());
            finishLocation(allowed);
            if (allowed) maybeRequestBackgroundLocation();
        }
        if (code == BACKGROUND_LOCATION_REQUEST) {
            if (FloodMonitorService.hasBackgroundLocation(this)) FloodMonitorService.startIfEnabled(this);
            notifyAlertStatus(alertPrefs().getBoolean("enabled", false) && notificationsAllowed());
        }
        if (code == NOTIFICATION_REQUEST) {
            if (notificationsAllowed()) {
                if (alertPrefs().getBoolean("enabled", false)) {
                    scheduleBackgroundRainAlerts();
                    notifyAlertStatus(true);
                    maybeRequestBackgroundLocation();
                } else {
                    setRainAlerts(true);
                }
            } else {
                alertPrefs().edit().putBoolean("enabled", false).apply();
                FloodMonitorService.stop(this);
                notifyAlertStatus(false);
            }
        }
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
        if (alertPrefs().getBoolean("enabled", false) && notificationsAllowed()) {
            FloodMonitorService.startIfEnabled(this);
        }
        if (webView != null) {
            webView.onResume();
            webView.evaluateJavascript("setTimeout(function(){window.FloodSafeRain?.refresh?.(true)},120)", null);
        }
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
