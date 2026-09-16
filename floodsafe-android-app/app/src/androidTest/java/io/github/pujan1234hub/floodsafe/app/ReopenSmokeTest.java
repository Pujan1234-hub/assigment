package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.content.Intent;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Regression test for the real failure users reported: open -> background -> reopen. */
@RunWith(AndroidJUnit4.class)
public final class ReopenSmokeTest {
    private static final String READY_JS =
            "JSON.stringify({title:document.title,app:!!document.querySelector('.app'),"
            + "map:!!document.getElementById('riverMapGL'),"
            + "runtime:!!window.FloodSafeRiverRealtime,body:!!document.body})";

    @Test public void coldAndWarmReopenKeepWebViewResponsive() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();

        VoiceMainActivity first = launch(instrumentation, context);
        waitReady(first, "first cold launch");

        // Reproduce the launcher-return path without killing the process.
        instrumentation.runOnMainSync(() -> first.moveTaskToBack(true));
        Thread.sleep(1200L);
        VoiceMainActivity warm1 = launch(instrumentation, context);
        waitReady(warm1, "first warm reopen");

        instrumentation.runOnMainSync(() -> warm1.moveTaskToBack(true));
        Thread.sleep(1200L);
        VoiceMainActivity warm2 = launch(instrumentation, context);
        waitReady(warm2, "second warm reopen");

        // Then destroy the activity and prove a fresh WebView still starts in the same process.
        instrumentation.runOnMainSync(warm2::finish);
        Thread.sleep(900L);
        VoiceMainActivity cold2 = launch(instrumentation, context);
        try {
            waitReady(cold2, "second cold launch");
        } finally {
            instrumentation.runOnMainSync(cold2::finish);
        }
    }

    private VoiceMainActivity launch(android.app.Instrumentation instrumentation, Context context) {
        Intent intent = new Intent(context, VoiceMainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        return (VoiceMainActivity) instrumentation.startActivitySync(intent);
    }

    private void waitReady(VoiceMainActivity activity, String label) throws Exception {
        String state = "null";
        for (int i = 0; i < 45; i++) {
            state = js(activity, READY_JS);
            if (state.contains("FloodSafe Nepal")
                    && state.contains("\\\"app\\\":true")
                    && state.contains("\\\"map\\\":true")
                    && state.contains("\\\"runtime\\\":true")
                    && state.contains("\\\"body\\\":true")) return;
            Thread.sleep(300L);
        }
        fail(label + " did not become responsive: " + state);
    }

    private String js(VoiceMainActivity activity, String expression) throws Exception {
        CountDownLatch done = new CountDownLatch(1);
        AtomicReference<String> value = new AtomicReference<>("<no callback>");
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            if (activity.webView == null) {
                value.set("<null webview>");
                done.countDown();
                return;
            }
            activity.webView.evaluateJavascript(expression, result -> {
                value.set(result);
                done.countDown();
            });
        });
        assertTrue("WebView JavaScript callback timed out: " + value.get(),
                done.await(8, TimeUnit.SECONDS));
        return value.get();
    }
}
