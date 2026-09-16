package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Regression test for the real user path: launcher -> background/close -> launcher reopen. */
@RunWith(AndroidJUnit4.class)
public final class ReopenSmokeTest {
    private static final String READY_JS =
            "JSON.stringify({title:document.title,app:!!document.querySelector('.app'),"
            + "map:!!document.getElementById('riverMapGL'),"
            + "runtime:!!window.FloodSafeRiverRealtime,body:!!document.body})";

    @Test public void coldAndWarmLauncherReopenKeepWebViewAndSathiResponsive() throws Exception {
        var instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();

        VoiceMainActivity first = launchThroughRealSplash(instrumentation, context);
        waitReady(first, "first cold launch");
        exerciseSathiComposer(first, "first cold launch");

        // Reproduce Home/background -> tapping the actual launcher again.
        instrumentation.runOnMainSync(() -> first.moveTaskToBack(true));
        Thread.sleep(1000L);
        VoiceMainActivity warm1 = launchThroughRealSplash(instrumentation, context);
        waitReady(warm1, "first warm launcher reopen");
        exerciseSathiComposer(warm1, "first warm launcher reopen");

        instrumentation.runOnMainSync(() -> warm1.moveTaskToBack(true));
        Thread.sleep(1000L);
        VoiceMainActivity warm2 = launchThroughRealSplash(instrumentation, context);
        waitReady(warm2, "second warm launcher reopen");
        exerciseSathiComposer(warm2, "second warm launcher reopen");

        // Destroy the content activity and prove the launcher creates a healthy fresh WebView too.
        instrumentation.runOnMainSync(warm2::finish);
        Thread.sleep(900L);
        VoiceMainActivity cold2 = launchThroughRealSplash(instrumentation, context);
        try {
            waitReady(cold2, "second cold launcher launch");
            exerciseSathiComposer(cold2, "second cold launcher launch");
        } finally {
            instrumentation.runOnMainSync(cold2::finish);
        }
    }

    private VoiceMainActivity launchThroughRealSplash(android.app.Instrumentation instrumentation,
                                                       Context context) throws Exception {
        Intent intent = new Intent(context, PJBuiltsSplashActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        instrumentation.startActivitySync(intent);

        AtomicReference<VoiceMainActivity> resumed = new AtomicReference<>();
        for (int i = 0; i < 50; i++) {
            instrumentation.runOnMainSync(() -> {
                for (Activity activity : ActivityLifecycleMonitorRegistry.getInstance()
                        .getActivitiesInStage(Stage.RESUMED)) {
                    if (activity instanceof VoiceMainActivity) {
                        resumed.set((VoiceMainActivity) activity);
                        break;
                    }
                }
            });
            if (resumed.get() != null) return resumed.get();
            Thread.sleep(100L);
        }
        fail("VoiceMainActivity never resumed after real PJBUILTS launcher splash");
        return null;
    }

    private void waitReady(VoiceMainActivity activity, String label) throws Exception {
        String state = "null";
        for (int i = 0; i < 50; i++) {
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

    private void exerciseSathiComposer(VoiceMainActivity activity, String label) throws Exception {
        String state = js(activity,
                "(function(){const i=document.getElementById('sathiFloodInput');"
                + "if(!i)return JSON.stringify({input:false});i.focus();"
                + "for(let n=0;n<36;n++){i.value='FloodSafe test '+n;"
                + "i.dispatchEvent(new Event('input',{bubbles:true}))}"
                + "return JSON.stringify({input:true,typing:window.__fsSathiTyping===true,value:i.value})})()");
        assertTrue(label + " SATHI input missing/unresponsive: " + state,
                state.contains("\\\"input\\\":true"));
        assertTrue(label + " SATHI typing throttle did not engage: " + state,
                state.contains("\\\"typing\\\":true"));
        assertEquals(label + " JS thread stalled after typing", "2", js(activity, "1+1"));
        assertEquals(label + " SATHI blur failed", "false",
                js(activity, "document.getElementById('sathiFloodInput').blur();window.__fsSathiTyping===true"));
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
