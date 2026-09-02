package io.github.pujan1234hub.floodsafe.beta;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.widget.TextView;
import androidx.browser.customtabs.CustomTabColorSchemeParams;
import androidx.browser.customtabs.CustomTabsClient;
import androidx.browser.customtabs.CustomTabsIntent;

/** Testing launcher: uses the real browser origin, not a WebView or copied dataset. */
public class MainActivity extends Activity {
    static final String APP_URL = "https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_main);
        findViewById(R.id.open_app).setOnClickListener(view -> openFloodSafe());
        // Never reopen over the user after Back or a configuration change.
        if (state == null) openFloodSafe();
    }

    static Intent browserIntent(String browserPackage) {
        if (browserPackage == null) {
            return new Intent(Intent.ACTION_VIEW, Uri.parse(APP_URL))
                    .addCategory(Intent.CATEGORY_BROWSABLE);
        }
        CustomTabsIntent tab = new CustomTabsIntent.Builder()
                .setShowTitle(true)
                .setDefaultColorSchemeParams(new CustomTabColorSchemeParams.Builder()
                        .setToolbarColor(Color.rgb(234, 246, 255)).build())
                .build();
        tab.intent.setPackage(browserPackage);
        tab.intent.setData(Uri.parse(APP_URL));
        return tab.intent;
    }

    private void openFloodSafe() {
        // Ignore incoming URLs/extras: only this fixed HTTPS origin can be launched.
        String provider = CustomTabsClient.getPackageName(this, null);
        try {
            startActivity(browserIntent(provider));
        } catch (ActivityNotFoundException | SecurityException unavailable) {
            try {
                // Handles a preferred browser disappearing between discovery and launch.
                startActivity(browserIntent(null));
            } catch (ActivityNotFoundException | SecurityException noBrowser) {
                ((TextView) findViewById(R.id.status)).setText(R.string.browser_missing);
            }
        }
    }
}
