package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Network-independent PJBUILTS launch intro with a hard timeout. */
public final class PJBuiltsSplashActivity extends Activity {
    private boolean launched;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable launchTask = this::openApp;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(2, 7, 18));
        window.setNavigationBarColor(Color.rgb(2, 7, 18));
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        setContentView(buildSplash());
        handler.postDelayed(launchTask, 1450L);
    }

    private View buildSplash() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(2, 7, 18));
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        TextView pujan = label("PUJAN", 42f, Color.rgb(232,251,255));
        TextView pj = label("PJ", 88f, Color.rgb(232,251,255));
        TextView builts = label("BUILTS", 24f, Color.rgb(184,241,255));
        TextView tag = label("IDEA  •  BUILD  •  INNOVATE", 10f, Color.rgb(135,215,237));
        pj.setAlpha(0f); builts.setAlpha(0f); tag.setAlpha(0f);
        box.addView(pujan); box.addView(pj); box.addView(builts); box.addView(tag);
        root.addView(box, new FrameLayout.LayoutParams(-1,-1));
        pujan.animate().alpha(0f).scaleX(.88f).scaleY(.88f).setStartDelay(330).setDuration(230);
        pj.animate().alpha(1f).scaleX(1.08f).scaleY(1.08f).setStartDelay(500).setDuration(230)
                .withEndAction(() -> pj.animate().scaleX(1f).scaleY(1f).setDuration(120));
        builts.animate().alpha(1f).setStartDelay(720).setDuration(220);
        tag.animate().alpha(1f).setStartDelay(850).setDuration(180);
        return root;
    }

    private TextView label(String s, float sp, int color) {
        TextView v = new TextView(this);
        v.setText(s); v.setTextSize(sp); v.setTextColor(color); v.setGravity(Gravity.CENTER);
        v.setTypeface(android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD));
        v.setShadowLayer(18f,0,0,Color.rgb(35,217,255));
        v.setPadding(8,8,8,8);
        return v;
    }

    private void openApp() {
        if (launched || isFinishing() || isDestroyed()) return;
        launched = true;
        handler.removeCallbacks(launchTask);
        Intent source = getIntent();
        Intent app = new Intent(this, VoiceMainActivity.class);
        // Always create a fresh WebView task on launcher open. Reusing a paused
        // WebView can leave some Android System WebView builds on a blank frame
        // after the app was closed from Recents and then reopened.
        app.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        if (source != null) {
            app.setData(source.getData());
            if (source.getExtras() != null) app.putExtras(source.getExtras());
        }
        startActivity(app);
        finish();
        overridePendingTransition(0,0);
    }

    @Override protected void onDestroy() {
        handler.removeCallbacks(launchTask);
        super.onDestroy();
    }
}
