package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Separate NASA GIBS precipitation and LHASA map.
 * Uses the already maintained PJBUILTS NASA satellite page; it DOES NOT replace
 * the native DHM/BIPAD river map. Online imagery and internet are required.
 */
public final class FloodSafeNasaSatelliteActivity extends Activity {
    private static final String NASA_URL="https://pjbuilts.com/floodsafe-nepal/monitor/satellite.html";
    private WebView browser;
    @Override public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(14,44,62));
        getWindow().setNavigationBarColor(Color.rgb(14,44,62));
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245,250,252));
        LinearLayout top=new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(14,9,14,9);
        Button back=new Button(this);
        back.setText("← फर्कनुहोस्");
        back.setOnClickListener(v->finish());
        TextView title=new TextView(this);
        title.setText("🛰 NASA • नेपाल भू–उपग्रह");
        title.setTextSize(16);title.setTextColor(Color.rgb(19,65,84));
        title.setGravity(Gravity.CENTER_VERTICAL);
        title.setTypeface(null,1);
        Button reload=new Button(this);
        reload.setText("↻");
        reload.setContentDescription("Reload NASA map");
        reload.setOnClickListener(v->{if(browser!=null)browser.reload();});
        top.addView(back,new LinearLayout.LayoutParams(-2,-2));
        top.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        top.addView(reload,new LinearLayout.LayoutParams(-2,-2));
        root.addView(top,new LinearLayout.LayoutParams(-1,-2));
        TextView detail=new TextView(this);
        detail.setText("NASA GPM वर्षा र LHASA पहिरो · नेपालका ७७ जिल्ला");
        detail.setTextSize(12);detail.setTextColor(Color.rgb(65,96,111));
        detail.setPadding(15,1,15,7);
        root.addView(detail,new LinearLayout.LayoutParams(-1,-2));
        browser=new WebView(this);
        WebSettings opts=browser.getSettings();
        opts.setJavaScriptEnabled(true);
        opts.setDomStorageEnabled(true);
        opts.setAllowFileAccess(false);opts.setAllowContentAccess(false);
        opts.setGeolocationEnabled(false);
        opts.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        browser.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){
                Uri u=r.getUrl();
                if(!r.isForMainFrame())return false;
                if("https".equals(u.getScheme())&&"pjbuilts.com".equalsIgnoreCase(u.getHost())
                   &&u.getPath()!=null&&u.getPath().startsWith("/floodsafe-nepal/monitor/"))return false;
                startActivity(new Intent(Intent.ACTION_VIEW,u));
                return true;
            }
        });
        browser.setWebChromeClient(new WebChromeClient());
        root.addView(browser,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        if(savedInstanceState!=null)browser.restoreState(savedInstanceState);
        else browser.loadUrl(NASA_URL);
    }
    @Override protected void onSaveInstanceState(Bundle out){
        if(browser!=null)browser.saveState(out);
        super.onSaveInstanceState(out);
    }
    @Override public void onBackPressed(){
        if(browser!=null&&browser.canGoBack())browser.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy(){
        if(browser!=null){
            browser.stopLoading();
            browser.loadUrl("about:blank");
            browser.destroy();browser=null;
        }
        super.onDestroy();
    }
}
