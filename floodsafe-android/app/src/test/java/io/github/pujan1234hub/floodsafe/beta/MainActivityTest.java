package io.github.pujan1234hub.floodsafe.beta;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.TextView;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class MainActivityTest {
    @Test public void customTabUsesOnlyCanonicalHttpsPage() {
        Intent intent = MainActivity.browserIntent("com.android.chrome");
        assertEquals(MainActivity.APP_URL, intent.getDataString());
        assertEquals("https", intent.getData().getScheme());
        assertEquals("com.android.chrome", intent.getPackage());
        assertTrue(intent.hasExtra("android.support.customtabs.extra.SESSION"));
    }

    @Test public void normalBrowserFallbackKeepsExactPage() {
        Intent intent = MainActivity.browserIntent(null);
        assertEquals(Intent.ACTION_VIEW, intent.getAction());
        assertEquals(MainActivity.APP_URL, intent.getDataString());
        assertTrue(intent.hasCategory(Intent.CATEGORY_BROWSABLE));
        assertNull(intent.getPackage());
    }

    @Test public void launchIgnoresIncomingUrl() {
        Intent incoming = new Intent(Intent.ACTION_VIEW, Uri.parse("https://example.com/"));
        MainActivity activity = Robolectric.buildActivity(MainActivity.class, incoming).create().get();
        assertEquals(MainActivity.APP_URL, shadowOf(activity).getNextStartedActivity().getDataString());
        assertNull(shadowOf(activity).getNextStartedActivity());
    }

    @Test public void recreationDoesNotOpenAgainButButtonDoes() {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).create(new Bundle()).get();
        assertNull(shadowOf(activity).getNextStartedActivity());
        activity.findViewById(R.id.open_app).performClick();
        assertEquals(MainActivity.APP_URL, shadowOf(activity).getNextStartedActivity().getDataString());
    }

    public static class NoBrowserActivity extends MainActivity {
        @Override public void startActivity(Intent intent) {
            throw new ActivityNotFoundException("Test fixture: no browser installed");
        }
    }

    @Test public void absentBrowserShowsRecoveryInsteadOfCrashing() {
        MainActivity activity = Robolectric.buildActivity(NoBrowserActivity.class).create().get();
        assertEquals(activity.getString(R.string.browser_missing),
                ((TextView) activity.findViewById(R.id.status)).getText().toString());
    }
}
