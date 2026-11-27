package com.pjbuilts.adminfloodsafe;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.content.SharedPreferences;
import android.content.Context;
import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public final class MainActivity extends Activity {
    private static final String PREFS="admin_floodsafe_private_v1";
    private static final String ALIAS="admin_floodsafe_keystore_2026";
    private static final String OWNER="Pujan1234-hub";
    private static final String REPO="assigment";
    private static final String ACTION="https://api.github.com/repos/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-ota-message-admin.yml/dispatches";
    private static final String HISTORY="https://api.github.com/repos/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-ota-message-admin.yml/runs?per_page=6";
    private static final String PUSH_ACTION="https://api.github.com/repos/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-admin-notice-push.yml/dispatches";
    private static final String PUSH_HISTORY="https://api.github.com/repos/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-admin-notice-push.yml/runs?per_page=6";
    private static final String PUSH_WORKFLOW="https://github.com/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-admin-notice-push.yml";
    private static final String LIVE="https://raw.githubusercontent.com/"+OWNER+"/"+REPO+"/floodsafe-ota-config-v0921/ota/floodsafe-config-v1.json";
    private static final String GUIDE="https://github.com/settings/personal-access-tokens/new";
    private static final String WORKFLOW="https://github.com/"+OWNER+"/"+REPO+"/actions/workflows/floodsafe-ota-message-admin.yml";
    private static final int INK=Color.rgb(23,42,54), MUTED=Color.rgb(101,111,113);
    private static final int PAPER=Color.rgb(249,247,242), GOLD=Color.rgb(188,147,75);
    private LinearLayout root;
    private TextView feedback, liveLabel, historyLabel;
    private EditText title, message, titleNe, messageNe, hours, tokenField;
    private EditText pushTitle, pushMessage, pushTitleNe, pushMessageNe;
    private Button publishButton, removeButton, pushBetaButton, pushPreviewButton, pushDeviceButton;
    private TextView pushFeedback, pushHistoryLabel;
    private volatile int lastLiveRevision=-1;
    private boolean busy=false;
    private String authorizedUser="";

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(PAPER);
        getWindow().setNavigationBarColor(PAPER);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        if(readToken()==null) showLogin(); else showDashboard();
    }
    private int dp(float value){return (int)(value*getResources().getDisplayMetrics().density+0.5f);}
    private GradientDrawable bg(int color,int radius,int outline){
        GradientDrawable d=new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        if(outline!=0)d.setStroke(dp(1),outline);
        return d;
    }
    private LinearLayout column(){
        LinearLayout l=new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }
    private void begin(String section){
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(PAPER);
        root=column();
        root.setPadding(dp(19),dp(24),dp(19),dp(38));
        scroll.addView(root);
        setContentView(scroll);
        TextView brand=text("🇳🇵 PJBUILTS  /  SECURE ADMIN",12,GOLD,true);
        root.addView(brand,wrap(0,7));
        TextView heading=text("Admin FloodSafe",29,INK,true);
        root.addView(heading,wrap(3,1));
        TextView desc=text(section,14,MUTED,false);
        root.addView(desc,wrap(0,16));
    }
    private LinearLayout.LayoutParams wrap(int top,int bottom){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.setMargins(0,dp(top),0,dp(bottom));return p;
    }
    private TextView text(String s,int size,int color,boolean bold){
        TextView t=new TextView(this);
        t.setText(s);t.setTextSize(size);t.setTextColor(color);
        if(bold)t.setTypeface(null,Typeface.BOLD);
        t.setLineSpacing(dp(3),1f);
        return t;
    }
    private LinearLayout card(){
        LinearLayout c=column();c.setPadding(dp(17),dp(17),dp(17),dp(17));
        c.setBackground(bg(Color.WHITE,18,Color.rgb(232,224,207)));
        root.addView(c,wrap(2,14));return c;
    }
    private TextView cardTitle(LinearLayout c,String value){
        TextView t=text(value,18,INK,true);c.addView(t,wrap(0,9));return t;
    }
    private EditText input(LinearLayout parent,String label,String hint,boolean multi){
        TextView lab=text(label,13,INK,true);parent.addView(lab,wrap(9,5));
        EditText field=new EditText(this);
        field.setTextSize(15);field.setTextColor(INK);field.setHintTextColor(Color.rgb(142,146,141));
        field.setHint(hint);field.setPadding(dp(13),dp(12),dp(13),dp(12));
        field.setBackground(bg(PAPER,12,Color.rgb(220,216,204)));
        field.setSingleLine(!multi);
        if(multi){
            field.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
            field.setMinLines(3);
            field.setGravity(Gravity.TOP|Gravity.START);
        }else field.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        parent.addView(field,wrap(0,2));
        return field;
    }
    private Button button(LinearLayout c,String label,boolean primary){
        Button b=new Button(this);
        b.setAllCaps(false);b.setText(label);
        b.setTextSize(15);b.setTypeface(null,Typeface.BOLD);
        b.setTextColor(primary?Color.WHITE:INK);
        b.setBackground(bg(primary?INK:Color.rgb(242,232,210),13,primary?0:Color.rgb(227,211,177)));
        b.setMinHeight(dp(52));b.setPadding(dp(10),dp(12),dp(10),dp(12));
        c.addView(b,wrap(9,1));return b;
    }
    private void showLogin(){
        begin("Private owner console · In-app OTA announcements");
        LinearLayout c=card();
        cardTitle(c,"Connect GitHub securely");
        c.addView(text("Create a fine-grained token for your own repository. Give only Actions → Read and write. No password, Firebase key or GitHub secret is bundled in the APK.",13,MUTED,false),wrap(0,9));
        tokenField=input(c,"Fine-grained GitHub access token","github_pat_...",false);
        tokenField.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        Button connect=button(c,"🔐 Connect & Verify Account",true);
        connect.setOnClickListener(v->connect());
        Button guide=button(c,"Create GitHub Token ↗",false);
        guide.setOnClickListener(v->openUrl(GUIDE));
        feedback=text("",13,INK,false);c.addView(feedback,wrap(10,0));
        LinearLayout guideCard=card();
        cardTitle(guideCard,"First-time setup");
        guideCard.addView(text("1  Resource owner: Pujan1234-hub\n2  Only select repository: assigment\n3  Repository permissions: Actions → Read and write\n4  Generate, copy and paste token above.\n\nThe token is encrypted in the Android Keystore and never saved inside GitHub workflow files.",13,MUTED,false),wrap(0,0));
    }
    private void connect(){
        if(busy)return;
        String proposed=tokenField.getText().toString().trim();
        if(proposed.length()<18){feedback.setText("Please enter a valid GitHub fine-grained token.");return;}
        busy=true;feedback.setText("Checking GitHub account…");
        work(()->{
            Reply res=request("https://api.github.com/user","GET",null,proposed);
            if(res.code!=200)throw new IllegalStateException("GitHub authorization failed (HTTP "+res.code+"). Check token and expiry.");
            String login=new JSONObject(res.body).optString("login","");
            if(!OWNER.equalsIgnoreCase(login))throw new IllegalStateException("Please sign in as "+OWNER+". Account found: "+login);
            saveToken(proposed);
            authorizedUser=login;
            runOnUiThread(()->{busy=false;showDashboard();});
        },feedback);
    }
    private void showDashboard(){
        begin("Private owner console · OTA notices + Firebase push");
        LinearLayout statusCard=card();
        cardTitle(statusCard,"● Live notice status");
        liveLabel=text("Checking remote configuration…",13,MUTED,false);
        statusCard.addView(liveLabel,wrap(2,7));
        Button refresh=button(statusCard,"↻ Refresh Live Status",false);
        refresh.setOnClickListener(v->refreshLive());

        LinearLayout compose=card();
        cardTitle(compose,"Write a new OTA notice");
        compose.addView(text("This appears inside FloodSafe Nepal v0.9.23. Changes reach phones when the app checks the server (currently up to about 5 minutes), not instantly.",13,MUTED,false),wrap(0,5));
        title=input(compose,"Title","FloodSafe Nepal update",false);
        message=input(compose,"Message","Write your announcement here…",true);
        titleNe=input(compose,"Nepali title (optional)","Leave blank to use same title",false);
        messageNe=input(compose,"Nepali message (optional)","Leave blank to use same message",true);
        hours=input(compose,"Duration (hours)","24",false);
        hours.setInputType(InputType.TYPE_CLASS_NUMBER);hours.setText("24");
        publishButton=button(compose,"↗ Publish OTA Message",true);
        publishButton.setOnClickListener(v->askPublish());
        removeButton=button(compose,"✕ Remove Current OTA Message",false);
        removeButton.setOnClickListener(v->confirmRemove());
        feedback=text("Ready. Only general informational notices are allowed.",13,MUTED,false);
        compose.addView(feedback,wrap(12,0));

        LinearLayout pushCard=card();
        cardTitle(pushCard,"🔔 Send phone PUSH notification");
        pushCard.addView(text("FCM notification to Android phones. Not an emergency alert. Play beta devices use the nepal-alerts topic; older installations may also subscribe. Both languages supported.",13,MUTED,false),wrap(0,6));
        pushTitle=input(pushCard,"Push title (English)","FloodSafe Nepal announcement",false);
        pushMessage=input(pushCard,"Push text (English)","Write a short informational message…",true);
        pushTitleNe=input(pushCard,"Push title (Nepali, optional)","Leave blank for English title",false);
        pushMessageNe=input(pushCard,"Push text (Nepali, optional)","Leave blank for English message",true);
        pushDeviceButton=button(pushCard,"🧪 Test on my phone only",true);
        pushDeviceButton.setOnClickListener(v->askDeviceTest());
        pushCard.addView(text("Single-device test uses only the private owner FCM token configured in GitHub. If missing, no notification is sent. Never falls back to all users.",12,MUTED,false),wrap(4,8));
        pushBetaButton=button(pushCard,"🔔 Send to installed Play subscribers",false);
        pushBetaButton.setOnClickListener(v->askPush("all"));
        pushPreviewButton=button(pushCard,"🧪 Send to preview-only devices",false);
        pushPreviewButton.setOnClickListener(v->askPush("preview"));
        pushFeedback=text("Push requires confirmation. Firebase accepts an alert first; handset delivery is verified separately.",13,MUTED,false);
        pushCard.addView(pushFeedback,wrap(9,0));

        LinearLayout historyCard=card();
        cardTitle(historyCard,"Recent publishing history");
        historyLabel=text("Tap to load recent OTA actions.",13,MUTED,false);
        historyCard.addView(historyLabel,wrap(0,5));
        Button history=button(historyCard,"View Action History",false);
        history.setOnClickListener(v->loadHistory());
        Button link=button(historyCard,"Open GitHub Workflow ↗",false);
        link.setOnClickListener(v->openUrl(WORKFLOW));
        pushHistoryLabel=text("No push history loaded.",13,MUTED,false);
        historyCard.addView(pushHistoryLabel,wrap(14,4));
        Button pushHistory=button(historyCard,"View Push History",false);
        pushHistory.setOnClickListener(v->loadPushHistory());
        Button pushLink=button(historyCard,"Open Push Workflow ↗",false);
        pushLink.setOnClickListener(v->openUrl(PUSH_WORKFLOW));

        LinearLayout access=card();
        cardTitle(access,"Account & security");
        access.addView(text("GitHub account: "+(authorizedUser.isEmpty()?OWNER:authorizedUser)+"\nOnly HTTPS GitHub endpoints. Locally encrypted session. No device location, contacts or Firebase credentials required.",12,MUTED,false),wrap(0,8));
        Button signout=button(access,"Disconnect & Forget Token",false);
        signout.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Disconnect GitHub?")
            .setMessage("Remove the locally stored encrypted token from this phone?")
            .setNegativeButton("Cancel",null).setPositiveButton("Disconnect",(a,b)->{
                getSharedPreferences(PREFS,MODE_PRIVATE).edit().clear().apply();authorizedUser="";showLogin();
            }).show());
        refreshLive();
    }
    private void askPublish(){
        if(busy)return;
        String enTitle=title.getText().toString().trim(),enBody=message.getText().toString().trim();
        String npTitle=titleNe.getText().toString().trim(),npBody=messageNe.getText().toString().trim();
        if(enTitle.length()<4||enTitle.length()>120||enBody.length()<4||enBody.length()>700||
            npTitle.length()>120||npBody.length()>700||
            (!npTitle.isEmpty()&&npTitle.length()<4)||(!npBody.isEmpty()&&npBody.length()<4)){
            feedback.setText("Title must be 4–120 characters, message 4–700. Optional Nepali fields must be 4+ characters if used.");return;
        }
        int h;
        try{h=Integer.parseInt(hours.getText().toString().trim());}catch(Exception e){feedback.setText("Choose duration from 1 to 336 hours.");return;}
        if(h<1||h>336){feedback.setText("Choose duration from 1 to 336 hours.");return;}
        new AlertDialog.Builder(this).setTitle("Publish this OTA notice?")
            .setMessage(enTitle+"\n\n"+enBody+"\n\nVisible for "+h+" hours. This is an informational in-app notice, not a flood warning.")
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Publish",(d,w)->dispatch("publish",enTitle,enBody,npTitle,npBody,h)).show();
    }
    private void confirmRemove(){
        if(busy)return;
        new AlertDialog.Builder(this).setTitle("Remove current in-app notice?")
            .setMessage("This disables the notice on the server once the GitHub job completes. Existing FloodSafe v0.9.23 phones poll roughly every 5 minutes, so the screen may not clear immediately. The official flood alerts are unaffected.")
            .setNegativeButton("Cancel",null).setPositiveButton("Remove",(d,w)->dispatch("remove","","","","",24)).show();
    }
    private void dispatch(String action,String t,String b,String tn,String bn,int h){
        if(busy)return;
        final String saved=readToken();
        if(saved==null){showLogin();return;}
        busy=true;
        publishButton.setEnabled(false);removeButton.setEnabled(false);
        feedback.setText("Submitting "+action+" to the private GitHub workflow…");
        work(()->{
            JSONObject inputs=new JSONObject();
            inputs.put("notice_action",action);
            inputs.put("title",t);inputs.put("message",b);
            inputs.put("nepali_title",tn);inputs.put("nepali_message",bn);
            inputs.put("show_hours",String.valueOf(h));
            JSONObject requestBody=new JSONObject();
            requestBody.put("ref","main");requestBody.put("inputs",inputs);
            int beforeRevision=-1;
            try{
                Reply before=request(LIVE+"?revision_before="+System.currentTimeMillis(),"GET",null,null);
                if(before.code==200)beforeRevision=new JSONObject(before.body).optInt("revision",-1);
            }catch(Exception ignored){}
            Reply res=request(ACTION,"POST",requestBody.toString(),saved);
            if(res.code!=204)throw new IllegalStateException("GitHub refused action (HTTP "+res.code+"). "+trim(res.body,220));
            final int startingRevision=beforeRevision;
            runOnUiThread(()->{
                busy=false;publishButton.setEnabled(true);removeButton.setEnabled(true);
                feedback.setText("GitHub accepted "+action+". Confirming that the remote config was actually updated…");
            });
            verifyOtaOutcome(action,startingRevision);
        },feedback);
    }
    private void refreshLive(){
        if(liveLabel==null)return;
        liveLabel.setText("Reading published OTA config…");
        work(()->{
            Reply res=request(LIVE+"?admin_check="+System.currentTimeMillis(),"GET",null,null);
            if(res.code!=200)throw new IllegalStateException("Unable to read OTA config (HTTP "+res.code+")");
            JSONObject obj=new JSONObject(res.body),notice=obj.optJSONObject("app_notice");
            int revision=obj.optInt("revision",-1);
            boolean enabled=obj.optBoolean("enabled",false)&&notice!=null&&notice.optBoolean("enabled",false);
            boolean active=enabled;
            if(enabled){
                try{
                    Instant start=Instant.parse(notice.optString("starts_at"));
                    Instant end=Instant.parse(notice.optString("expires_at"));
                    active=!Instant.now().isBefore(start)&&Instant.now().isBefore(end);
                }catch(Exception ex){active=false;}
            }
            lastLiveRevision=revision;
            String result="OTA revision "+revision+"\n"+(active?"🟢 Notice active: "+notice.optString("title_en")+"\n"+trim(notice.optString("body_en"),350)+"\nExpires: "+notice.optString("expires_at"):"⚪ No active in-app notice");
            runOnUiThread(()->{if(liveLabel!=null)liveLabel.setText(result);});
        },liveLabel);
    }
    private void loadHistory(){
        if(historyLabel==null)return;
        String token=readToken();if(token==null){showLogin();return;}
        historyLabel.setText("Loading recent workflow runs…");
        work(()->{
            Reply res=request(HISTORY,"GET",null,token);
            if(res.code!=200)throw new IllegalStateException("Cannot read workflow history (HTTP "+res.code+")");
            JSONArray runs=new JSONObject(res.body).optJSONArray("workflow_runs");
            StringBuilder out=new StringBuilder();
            if(runs!=null)for(int i=0;i<Math.min(6,runs.length());i++){
                JSONObject row=runs.optJSONObject(i);if(row==null)continue;
                String status=row.optString("conclusion");
                if(status.isEmpty()||status.equals("null"))status=row.optString("status");
                out.append("• ").append(status.toUpperCase(Locale.ROOT))
                    .append("  ·  ").append(row.optString("created_at").replace('T',' ').replace("Z"," UTC"))
                    .append("\n");
            }
            String finalText=out.length()>0?out.toString():"No runs found. Publish a notice first.";
            runOnUiThread(()->{if(historyLabel!=null)historyLabel.setText(finalText);});
        },historyLabel);
    }

    private void verifyOtaOutcome(String action,int previousRevision){
        // A 204 from workflow_dispatch means queued, NOT published. Verify the actual raw config.
        for(int i=0;i<18;i++){
            try{
                Thread.sleep(2500L);
                Reply check=request(LIVE+"?verify="+System.currentTimeMillis()+"-"+i,"GET",null,null);
                if(check.code!=200)continue;
                JSONObject obj=new JSONObject(check.body);
                int revision=obj.optInt("revision",-1);
                JSONObject notice=obj.optJSONObject("app_notice");
                boolean enabled=obj.optBoolean("enabled",false)&&notice!=null&&notice.optBoolean("enabled",false);
                if(revision>previousRevision && ("remove".equals(action)?!enabled:enabled)){
                    runOnUiThread(()->{
                        feedback.setText("✓ CONFIRMED: OTA "+action+" updated on server (revision "+revision+"). FloodSafe v0.9.23 may take up to about 5 minutes to reflect removal on-device.");
                        refreshLive();
                    });
                    return;
                }
            }catch(Exception ignored){}
        }
        runOnUiThread(()->{
            feedback.setText("Action submitted, but the live server change is not verified yet. Use History and Refresh Live Status to check for success/failure.");
            refreshLive();
        });
    }
    private void askDeviceTest(){
        if(busy)return;
        new AlertDialog.Builder(this)
            .setTitle("Test on my phone only")
            .setMessage("Send one clearly labelled test notification to the configured owner FloodSafe device only? If no valid owner token is configured, the server will stop without sending. No other subscribers will receive it.")
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Send test",(d,w)->dispatchPush("device","Sound test","This is a private notification sound test.","ध्वनि परीक्षण","यो निजी सूचना ध्वनि परीक्षण हो।"))
            .show();
    }
    private void askPush(String audience){
        if(busy)return;
        String enTitle=pushTitle.getText().toString().trim();
        String enText=pushMessage.getText().toString().trim();
        String neTitle=pushTitleNe.getText().toString().trim();
        String neText=pushMessageNe.getText().toString().trim();
        // Backend validates each language separately. Use English as fallback for Nepali fields.
        if(neTitle.isEmpty())neTitle=enTitle;
        if(neText.isEmpty())neText=enText;
        if(!validPush(enTitle,90)||!validPush(enText,500)||!validPush(neTitle,90)||!validPush(neText,500)){
            pushFeedback.setText("Both titles must be 4–90 characters and both messages 4–500 characters.");
            return;
        }
        if(("ℹ️ "+neTitle+" / "+enTitle).length()>180||(neText+"\n"+enText).length()>1050){
            pushFeedback.setText("Combined bilingual notification is too long.");return;
        }
        final String fneTitle=neTitle,fneText=neText;
        final boolean all="all".equals(audience);
        String recipient=all?"all devices subscribed to nepal-alerts, including current Play testers and possible older installs":"only .preview devices subscribed to floodsafe-testers";
        new AlertDialog.Builder(this)
            .setTitle(all?"Confirm subscriber-wide push":"Confirm preview-only push")
            .setMessage("This sends a NON-EMERGENCY phone notification to "+recipient+".\n\n"+enTitle+"\n"+enText+"\n\nPush cannot be recalled after delivery. Send?")
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Send Push",(d,w)->dispatchPush(audience,enTitle,enText,fneTitle,fneText))
            .show();
    }
    private static boolean validPush(String input,int max){
        return input!=null && input.length()>=4 && input.length()<=max
            && !input.toLowerCase(Locale.ROOT).contains("<script")&&!input.toLowerCase(Locale.ROOT).contains("javascript:");
    }
    private void dispatchPush(String audience,String titleEn,String bodyEn,String titleNe,String bodyNe){
        if(busy)return;
        String token=readToken();
        if(token==null){showLogin();return;}
        busy=true;
        if(pushBetaButton!=null)pushBetaButton.setEnabled(false);
        if(pushPreviewButton!=null)pushPreviewButton.setEnabled(false);
        if(pushDeviceButton!=null)pushDeviceButton.setEnabled(false);
        pushFeedback.setText("Sending secure request to GitHub Actions. No Firebase credential stored in this APK…");
        work(()->{
            JSONObject inputs=new JSONObject();
            inputs.put("audience",audience);
            inputs.put("title_en",titleEn);
            inputs.put("body_en",bodyEn);
            inputs.put("title_ne",titleNe);
            inputs.put("body_ne",bodyNe);
            inputs.put("confirm_broadcast","all".equals(audience)?"SEND NON-EMERGENCY PUSH":"");
            JSONObject payload=new JSONObject();
            payload.put("ref","main");
            payload.put("inputs",inputs);
            Reply reply=request(PUSH_ACTION,"POST",payload.toString(),token);
            if(reply.code!=204)throw new IllegalStateException("Push workflow not accepted. HTTP "+reply.code+" "+trim(reply.body,200));
            runOnUiThread(()->{
                busy=false;
                if(pushBetaButton!=null)pushBetaButton.setEnabled(true);
                if(pushPreviewButton!=null)pushPreviewButton.setEnabled(true);
                if(pushDeviceButton!=null)pushDeviceButton.setEnabled(true);
                pushFeedback.setText("✓ Push job QUEUED. Open Push History and look for SUCCESS. This confirms Firebase acceptance, not receipt by every phone.");
            });
        },pushFeedback);
    }
    private void loadPushHistory(){
        String token=readToken();
        if(token==null){showLogin();return;}
        pushHistoryLabel.setText("Checking Firebase push workflow runs…");
        work(()->{
            Reply reply=request(PUSH_HISTORY,"GET",null,token);
            if(reply.code!=200)throw new IllegalStateException("Unable to read push history (HTTP "+reply.code+")");
            JSONArray rows=new JSONObject(reply.body).optJSONArray("workflow_runs");
            StringBuilder sb=new StringBuilder();
            if(rows!=null)for(int i=0;i<Math.min(6,rows.length());i++){
                JSONObject row=rows.optJSONObject(i);if(row==null)continue;
                String status=row.optString("conclusion");
                if(status.isEmpty()||status.equals("null"))status=row.optString("status");
                sb.append("• ").append(status.toUpperCase(Locale.ROOT)).append(" · ")
                    .append(row.optString("event")).append(" · ")
                    .append(row.optString("created_at").replace('T',' ').replace("Z"," UTC")).append("\n");
            }
            String result=sb.length()==0?"No push workflow runs found.":sb.toString();
            runOnUiThread(()->{if(pushHistoryLabel!=null)pushHistoryLabel.setText(result);});
        },pushHistoryLabel);
    }
    private static String trim(String source,int max){
        if(source==null)return "";
        return source.length()>max?source.substring(0,max)+"…":source;
    }
    private void openUrl(String url){
        Intent i=new Intent(Intent.ACTION_VIEW,Uri.parse(url));startActivity(i);
    }
    private interface Job{void run()throws Exception;}
    private void work(Job job,TextView error){
        new Thread(()->{
            try{job.run();}
            catch(Exception ex){
                String text=trim(ex.getMessage()==null?ex.toString():ex.getMessage(),360);
                runOnUiThread(()->{
                    busy=false;
                    if(publishButton!=null)publishButton.setEnabled(true);
                    if(removeButton!=null)removeButton.setEnabled(true);
                    if(pushBetaButton!=null)pushBetaButton.setEnabled(true);
                    if(pushPreviewButton!=null)pushPreviewButton.setEnabled(true);
                if(pushDeviceButton!=null)pushDeviceButton.setEnabled(true);
                    if(error!=null)error.setText("⚠ "+text);
                });
            }
        },"AdminFloodSafe-HTTPS").start();
    }
    private static class Reply{
        final int code;final String body;
        Reply(int c,String b){code=c;body=b;}
    }
    private Reply request(String location,String method,String payload,String token)throws Exception{
        if(!(location.startsWith("https://api.github.com/")||location.startsWith("https://raw.githubusercontent.com/")))
            throw new SecurityException("Unsupported endpoint");
        HttpURLConnection c=(HttpURLConnection)new URL(location).openConnection();
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(12000);c.setReadTimeout(15000);
        c.setRequestMethod(method);
        c.setRequestProperty("User-Agent","Admin-FloodSafe-Android/1.0");
        c.setRequestProperty("Accept","application/vnd.github+json");
        c.setRequestProperty("X-GitHub-Api-Version","2022-11-28");
        c.setRequestProperty("Cache-Control","no-cache");
        if(token!=null)c.setRequestProperty("Authorization","Bearer "+token);
        if(payload!=null){
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type","application/json; charset=utf-8");
            try(OutputStream out=c.getOutputStream()){
                out.write(payload.getBytes(StandardCharsets.UTF_8));
            }
        }
        try{
            int code=c.getResponseCode();
            InputStream input=code>=400?c.getErrorStream():c.getInputStream();
            String body="";
            if(input!=null){
                try(InputStream in=input;ByteArrayOutputStream buffer=new ByteArrayOutputStream()){
                    byte[] tmp=new byte[4096];int n;
                    while((n=in.read(tmp))!=-1){
                        if(buffer.size()+n>250000)throw new IllegalStateException("Response exceeds safe size");
                        buffer.write(tmp,0,n);
                    }
                    body=buffer.toString("UTF-8");
                }
            }
            return new Reply(code,body);
        }finally{c.disconnect();}
    }
    private SecretKey key()throws Exception{
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if(!store.containsAlias(ALIAS)){
            KeyGenerator g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            KeyGenParameterSpec spec=new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256).build();
            g.init(spec);g.generateKey();
        }
        return (SecretKey)store.getKey(ALIAS,null);
    }
    private void saveToken(String token)throws Exception{
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE,key());
        byte[] ciphertext=cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
        byte[] iv=cipher.getIV();
        getSharedPreferences(PREFS,MODE_PRIVATE).edit()
            .putString("encrypted_token",Base64.encodeToString(ciphertext,Base64.NO_WRAP))
            .putString("iv",Base64.encodeToString(iv,Base64.NO_WRAP))
            .apply();
    }
    private String readToken(){
        SharedPreferences p=getSharedPreferences(PREFS,MODE_PRIVATE);
        String ct=p.getString("encrypted_token",null),iv=p.getString("iv",null);
        if(ct==null||iv==null)return null;
        try{
            Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(iv,Base64.NO_WRAP)));
            return new String(cipher.doFinal(Base64.decode(ct,Base64.NO_WRAP)),StandardCharsets.UTF_8);
        }catch(Exception ex){
            p.edit().clear().apply();
            return null;
        }
    }
}
