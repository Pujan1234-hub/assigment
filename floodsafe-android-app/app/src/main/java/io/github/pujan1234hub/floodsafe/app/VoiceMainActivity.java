package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/**
 * Legacy compatibility entry point. It intentionally contains no WebView.
 * Any old notification/service intent that still targets this class is forwarded
 * immediately to the native FloodSafe activity.
 */
public final class VoiceMainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        forwardToNative(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        forwardToNative(intent);
    }

    private void forwardToNative(Intent source) {
        Intent nativeIntent = new Intent(this, FloodSafeNativeActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        if (source != null) {
            nativeIntent.setData(source.getData());
            if (source.getExtras() != null) nativeIntent.putExtras(source.getExtras());
        }
        startActivity(nativeIntent);
        finish();
        overridePendingTransition(0, 0);
    }
}
