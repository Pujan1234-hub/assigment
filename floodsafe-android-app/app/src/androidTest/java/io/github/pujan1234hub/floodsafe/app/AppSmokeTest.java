package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AppSmokeTest {
    @Test public void bundledAppLoadsOfflineWithoutOpeningBrowserOrRequestingGps() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        Intent intent = new Intent(context, MainActivity.class)
                .setData(Uri.parse("https://example.com/untrusted-incoming-url"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        MainActivity activity = (MainActivity) instrumentation.startActivitySync(intent);
        try {
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION));
            String state = "null";
            for (int i = 0; i < 60; i++) {
                state = js(activity, "JSON.stringify({title:document.title,closed:document.getElementById('map')?.classList.contains('fsMapClosed'),ready:!!window.FloodSafeRiverRealtime && !!window.FloodSafeCurrentLocation && !!window.FloodSafeRain,buttons:!!document.getElementById('fsOpenMapBtn'),push:document.getElementById('rainAlertStatus')?.textContent})");
                if (state.contains("\\\"ready\\\":true") && state.contains("\\\"buttons\\\":true")) break;
                Thread.sleep(500);
            }
            assertTrue(state, state.contains("FloodSafe Nepal"));
            assertTrue(state, state.contains("\\\"closed\\\":true"));
            assertTrue(state, state.contains("\\\"ready\\\":true"));
            assertTrue(state, state.contains("\\\"buttons\\\":true"));
            assertEquals("true", js(activity, "location.href === '" + NavigationPolicy.HOME + "'"));
            assertEquals("true", js(activity, "window.isSecureContext"));
            assertEquals("true", js(activity, "document.getElementById('fsOpenMapBtn').click(); window.FloodSafeMobileMap.isOpen"));
            assertEquals("false", js(activity, "document.getElementById('fsOpenMapBtn').click(); window.FloodSafeMobileMap.isOpen"));
            assertEquals("\"en\"", js(activity, "document.getElementById('langBtn').click(); window.FloodSafe.state.lang"));
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION));
            AtomicReference<Boolean> allowed = new AtomicReference<>();
            instrumentation.runOnMainSync(() -> activity.requestLocation("https://example.com", (origin, allow, retain) -> allowed.set(allow)));
            assertEquals(Boolean.FALSE, allowed.get());
        } finally { instrumentation.runOnMainSync(activity::finish); }
    }

    private String js(MainActivity activity, String expression) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<String> value = new AtomicReference<>();
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> activity.webView.evaluateJavascript(expression, result -> {
            value.set(result); done.countDown();
        }));
        assertTrue("WebView JavaScript callback", done.await(10, TimeUnit.SECONDS));
        return value.get();
    }
}
