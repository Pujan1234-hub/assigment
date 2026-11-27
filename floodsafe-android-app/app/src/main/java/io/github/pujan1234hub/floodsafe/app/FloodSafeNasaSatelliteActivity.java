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
    private boolean expanded=false;
    private boolean english;
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private String tr(String ne,String en){return english?en:ne;}
    @Override public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        english=getSharedPreferences("floodsafe-native-full",MODE_PRIVATE).getBoolean("lang_en",false);
        getWindow().setStatusBarColor(Color.rgb(14,44,62));
        getWindow().setNavigationBarColor(Color.rgb(14,44,62));
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(245,250,252));
        LinearLayout top=new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(14,9,14,9);
        Button back=new Button(this);
        back.setText(tr("← फर्कनुहोस्","← Back"));
        back.setOnClickListener(v->finish());
        TextView title=new TextView(this);
        title.setText(tr("🛰 NASA • नेपाल भू–उपग्रह","🛰 NASA • Nepal satellite"));
        title.setTextSize(16);title.setTextColor(Color.rgb(19,65,84));
        title.setGravity(Gravity.CENTER_VERTICAL);
        title.setTypeface(null,android.graphics.Typeface.BOLD);
        Button reload=new Button(this);
        reload.setText("↻");
        reload.setContentDescription("Reload NASA map");
        reload.setOnClickListener(v->{if(browser!=null)browser.reload();});
        top.addView(back,new LinearLayout.LayoutParams(-2,-2));
        top.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        top.addView(reload,new LinearLayout.LayoutParams(-2,-2));
        root.addView(top,new LinearLayout.LayoutParams(-1,-2));
        TextView detail=new TextView(this);
        detail.setText(tr("NASA GPM वर्षा र LHASA पहिरो · नेपालका ७७ जिल्ला","NASA GPM rain and LHASA landslide exposure · Nepal districts"));
        detail.setTextSize(12);detail.setTextColor(Color.rgb(65,96,111));
        detail.setPadding(15,1,15,7);
        root.addView(detail,new LinearLayout.LayoutParams(-1,-2));
        LinearLayout actions=new LinearLayout(this);actions.setPadding(dp(6),0,dp(6),dp(4));
        Button expand=new Button(this);expand.setAllCaps(false);expand.setText(tr("⛶ ठूलो नक्सा","⛶ Expand map"));expand.setOnClickListener(v->{expanded=!expanded;detail.setVisibility(expanded?View.GONE:View.VISIBLE);title.setVisibility(expanded?View.GONE:View.VISIBLE);expand.setText(expanded?tr("सामान्य दृश्य","Normal view"):tr("⛶ ठूलो नक्सा","⛶ Expand map"));if(browser!=null)browser.evaluateJavascript(expanded?"document.getElementById(\"satMap\")?.scrollIntoView({block:\"start\"});":"window.scrollTo(0,0);",null);});
        Button worldview=new Button(this);worldview.setAllCaps(false);worldview.setText("NASA Worldview ↗");worldview.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://worldview.earthdata.nasa.gov/?v=79.8,26.1,88.5,30.8")));}catch(Exception ignored){}});
        actions.addView(expand,new LinearLayout.LayoutParams(0,dp(48),1));actions.addView(worldview,new LinearLayout.LayoutParams(0,dp(48),1));root.addView(actions);
        browser=new WebView(this);
        WebSettings opts=browser.getSettings();
        opts.setJavaScriptEnabled(true);
        opts.setDomStorageEnabled(true);
        opts.setBuiltInZoomControls(true);opts.setDisplayZoomControls(false);
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
        SafeInsets.apply(root);
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
