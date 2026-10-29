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
import android.webkit.WebView;

/** Original offline shiny cream-gold PJBUILTS intro then exact FloodSafe web in its native Android shell. */
public final class PJBuiltsSplashActivity extends Activity {
    private boolean launched;
    private WebView originalIntro;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable launchTask = this::openApp;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(255, 249, 239));
        window.setNavigationBarColor(Color.rgb(255, 249, 239));
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        setContentView(buildSplash());
        handler.postDelayed(launchTask, 2870L);
    }

    private View buildSplash(){
        FrameLayout frame=new FrameLayout(this);
        frame.setBackgroundColor(Color.rgb(255,249,239));
        TextView backup=new TextView(this);
        backup.setText("PJBUILTS");
        backup.setTextSize(34);
        backup.setTextColor(Color.rgb(151,103,40));
        backup.setGravity(Gravity.CENTER);
        frame.addView(backup,new FrameLayout.LayoutParams(-1,-1));
        originalIntro=new WebView(this);
        originalIntro.setBackgroundColor(Color.rgb(255,249,239));
        originalIntro.getSettings().setJavaScriptEnabled(false);
        originalIntro.getSettings().setBlockNetworkLoads(true);
        originalIntro.getSettings().setAllowFileAccess(true);
        originalIntro.getSettings().setAllowContentAccess(false);
        frame.addView(originalIntro,new FrameLayout.LayoutParams(-1,-1));
        originalIntro.loadUrl("file:///android_asset/pjbuilts-original-splash.html");
        return frame;
    }

    private void openApp() {
        if (launched || isFinishing() || isDestroyed()) return;
        launched = true;
        handler.removeCallbacks(launchTask);
        Intent source = getIntent();
        Intent app = new Intent(this, MainActivity.class);
        app.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
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
        if(originalIntro!=null){originalIntro.stopLoading();originalIntro.destroy();originalIntro=null;}
        super.onDestroy();
    }
}
