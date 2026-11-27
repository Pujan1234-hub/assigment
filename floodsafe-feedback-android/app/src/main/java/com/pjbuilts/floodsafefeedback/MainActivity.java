package com.pjbuilts.floodsafefeedback;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;

public final class MainActivity extends Activity {
    static final String API="https://tbsbocnqaufrlgbsnzrf.supabase.co/functions/v1/feedback-api";
    private static final String[] STATUS={"new","reviewing","fixed","closed"};
    private static final int NAVY=Color.rgb(16,49,79), INK=Color.rgb(30,51,74), MUTED=Color.rgb(105,126,144), BG=Color.rgb(244,249,251), GOLD=Color.rgb(223,192,128);
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private String token="",filter="all";
    private JSONArray records=new JSONArray();
    private LinearLayout page,list,summary;
    private TextView state;
    private EditText search;
    private boolean busy=false;
    private boolean visible=false;
    private int session=0;
    private final android.os.Handler timer=new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable tick=new Runnable(){public void run(){if(!visible)return;if(!token.isEmpty())load();timer.postDelayed(this,15000);}};

    @Override public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(NAVY);
        getWindow().setNavigationBarColor(BG);
        showLogin("");
    }
    @Override protected void onResume(){super.onResume();visible=true;timer.removeCallbacks(tick);timer.post(tick);}
    @Override protected void onPause(){visible=false;timer.removeCallbacks(tick);super.onPause();}
    @Override protected void onDestroy(){session++;timer.removeCallbacks(tick);io.shutdownNow();token="";super.onDestroy();}
    @Override public void onRequestPermissionsResult(int code,String[] perms,int[] results){super.onRequestPermissionsResult(code,perms,results);if(code==41&&results.length>0&&results[0]==android.content.pm.PackageManager.PERMISSION_GRANTED&&!token.isEmpty())enableAlerts();}
    private void enableAlerts(){try{FeedbackAlerts.enable(this,token,records);Toast.makeText(this,"Background checks enabled (Android schedules them approximately every 15 minutes or later).",Toast.LENGTH_LONG).show();}catch(Exception e){Toast.makeText(this,"Could not enable background checks",Toast.LENGTH_LONG).show();}}
    private int dp(int n){return (int)(getResources().getDisplayMetrics().density*n+.5f);}
    private GradientDrawable bg(int color,int border){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(17));if(border!=0)d.setStroke(dp(1),border);return d;}
    private TextView t(String s,int size,int color,boolean bold){TextView v=new TextView(this);v.setText(s);v.setTextSize(size);v.setTextColor(color);if(bold)v.setTypeface(null,Typeface.BOLD);return v;}
    private LinearLayout v(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);return l;}
    private LinearLayout h(){LinearLayout l=new LinearLayout(this);l.setGravity(Gravity.CENTER_VERTICAL);return l;}
    private LinearLayout.LayoutParams p(int w,int h,int bottom){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(w<0?w:dp(w),h<0?h:dp(h));p.bottomMargin=dp(bottom);return p;}
    private Button b(String label,boolean primary){Button b=new Button(this);b.setText(label);b.setTextSize(13);b.setAllCaps(false);b.setTextColor(primary?Color.WHITE:NAVY);b.setBackground(bg(primary?NAVY:Color.WHITE,primary?0:0xffd5e2ea));return b;}
    private LinearLayout card(){LinearLayout a=v();a.setPadding(dp(16),dp(15),dp(16),dp(15));a.setBackground(bg(Color.WHITE,0xffdfe9ef));return a;}
    private void base(String subtitle){
        LinearLayout root=v();root.setBackgroundColor(BG);setContentView(root);
        LinearLayout header=v();header.setBackgroundColor(NAVY);header.setPadding(dp(20),dp(19),dp(20),dp(20));
        header.addView(t("PJBUILTS   /   FLOODSAFE NEPAL",11,GOLD,true),p(-1,-2,8));
        header.addView(t("Feedback Inbox",26,Color.WHITE,true),p(-1,-2,4));
        header.addView(t(subtitle,13,0xffd1e5ef,false));
        root.addView(header,p(-1,-2,0));
        ScrollView scroll=new ScrollView(this);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        page=v();page.setPadding(dp(15),dp(17),dp(15),dp(28));scroll.addView(page);
    }
    private void showLogin(String reason){
        session++;busy=false;token="";base("Private owner access · Live submissions");
        LinearLayout box=card();page.addView(box,p(-1,-2,10));
        box.addView(t("Open your admin inbox",20,INK,true),p(-1,-2,7));
        box.addView(t("Enter the SAME private token used on the FloodSafe Nepal feedback admin webpage. No password is built into this APK.",14,MUTED,false),p(-1,-2,17));
        EditText field=new EditText(this);field.setHint("Private feedback admin token");field.setSingleLine(true);
        field.setTextSize(14);field.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        field.setPadding(dp(10),dp(8),dp(10),dp(8));field.setBackground(bg(BG,0xffd7e6ef));
        box.addView(field,p(-1,48,12));
        Button open=b("View live feedback",true);box.addView(open,p(-1,48,12));
        state=t(reason.isEmpty()?"Token stays in memory unless you explicitly enable encrypted background checks. Lock inbox disables them.":reason,13,reason.isEmpty()?MUTED:0xffad3434,false);
        box.addView(state,p(-1,-2,0));
        open.setOnClickListener(view->{String entered=field.getText().toString().trim();if(entered.isEmpty()){state.setText("Please enter your admin token.");return;}token=entered;showInbox();load();});
    }
    private void showInbox(){
        base("Private admin console · Direct API connection");
        LinearLayout tools=h();page.addView(tools,p(-1,-2,12));
        Button refresh=b("↻ Refresh",false),logout=b("Lock inbox",false);
        LinearLayout.LayoutParams a=new LinearLayout.LayoutParams(0,dp(45),1);a.rightMargin=dp(8);
        tools.addView(refresh,a);tools.addView(logout,new LinearLayout.LayoutParams(0,dp(45),1));
        refresh.setOnClickListener(view->load());
        logout.setOnClickListener(view->{FeedbackAlerts.disable(this);records=new JSONArray();showLogin("Inbox locked.");});
        Button alerts=b("Enable background alerts",false);page.addView(alerts,p(-1,45,8));
        alerts.setOnClickListener(view->{if(busy||token.isEmpty())return;if(android.os.Build.VERSION.SDK_INT>=33&&checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.POST_NOTIFICATIONS},41);return;}enableAlerts();});
        Button stopAlerts=b("Disable background alerts",false);page.addView(stopAlerts,p(-1,42,10));stopAlerts.setOnClickListener(view->{FeedbackAlerts.disable(this);Toast.makeText(this,"Background alerts disabled",Toast.LENGTH_SHORT).show();});
        state=t("Loading feedback...",13,MUTED,false);page.addView(state,p(-1,-2,12));
        summary=v();page.addView(summary,p(-1,-2,8));
        LinearLayout filterCard=card();page.addView(filterCard,p(-1,-2,14));
        filterCard.addView(t("Search & filter",15,INK,true),p(-1,-2,9));
        search=new EditText(this);search.setSingleLine(true);search.setTextSize(14);
        search.setHint("Search message, contact, category...");
        search.setBackground(bg(BG,0xffd7e6ef));search.setPadding(dp(10),dp(7),dp(10),dp(7));
        filterCard.addView(search,p(-1,45,8));
        Spinner spinner=new Spinner(this);
        String[] filters={"All","New","Reviewing","Fixed","Closed"};
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,filters);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);spinner.setAdapter(adapter);
        filterCard.addView(spinner,p(-1,43,0));
        spinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> parent,View view,int position,long id){filter=position==0?"all":STATUS[position-1];render();}
            @Override public void onNothingSelected(android.widget.AdapterView<?> parent){}
        });
        search.addTextChangedListener(new android.text.TextWatcher(){
            @Override public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            @Override public void onTextChanged(CharSequence s,int start,int before,int count){render();}
            @Override public void afterTextChanged(android.text.Editable e){}
        });
        list=v();page.addView(list,p(-1,-2,0));render();
    }
    private String get(JSONObject j,String k){return j.optString(k,"").trim();}
    private String when(JSONObject j){String s=get(j,"created_at");try{return DateTimeFormatter.ofPattern("dd MMM yyyy · HH:mm",Locale.UK).withZone(ZoneId.systemDefault()).format(Instant.parse(s));}catch(Exception e){return s;}}
    private String category(JSONObject j){switch(get(j,"category")){case "bug":return "Bug";case "wrong_data":return "Wrong river/weather data";case "notification":return "Notification issue";case "suggestion":return "Suggestion";default:return "Other";}}
    private void render(){
        if(list==null||summary==null)return;
        summary.removeAllViews();list.removeAllViews();
        int[] counts=new int[4];for(int i=0;i<records.length();i++){JSONObject j=records.optJSONObject(i);if(j!=null)for(int k=0;k<4;k++)if(STATUS[k].equals(get(j,"status")))counts[k]++;}
        for(int r=0;r<2;r++){
            LinearLayout line=h();summary.addView(line,p(-1,-2,9));
            for(int k=r*2;k<r*2+2;k++){
                LinearLayout c=card();LinearLayout.LayoutParams col=new LinearLayout.LayoutParams(0,dp(91),1);if(k%2==0)col.rightMargin=dp(9);line.addView(c,col);
                c.addView(t(""+counts[k],25,NAVY,true),p(-1,-2,2));c.addView(t(STATUS[k].toUpperCase(Locale.ROOT),11,MUTED,true));
            }
        }
        String query=search==null?"":search.getText().toString().trim().toLowerCase(Locale.ROOT);
        int shown=0;
        for(int i=0;i<records.length();i++){
            JSONObject j=records.optJSONObject(i);if(j==null)continue;
            String status=get(j,"status");if(!filter.equals("all")&&!filter.equals(status))continue;
            String hay=(get(j,"message")+" "+get(j,"contact")+" "+get(j,"category")).toLowerCase(Locale.ROOT);
            if(!query.isEmpty()&&!hay.contains(query))continue;
            shown++;
            LinearLayout c=card();list.addView(c,p(-1,-2,10));
            c.addView(t(category(j)+"   ·   "+status.toUpperCase(Locale.ROOT),13,NAVY,true),p(-1,-2,6));
            c.addView(t(when(j),12,MUTED,false),p(-1,-2,8));
            String msg=get(j,"message");if(msg.length()>200)msg=msg.substring(0,200)+"…";
            c.addView(t(msg,15,INK,false),p(-1,-2,10));
            c.addView(t("Tap to view details and update status ↗",12,MUTED,false));
            c.setOnClickListener(view->details(j));
        }
        if(shown==0){LinearLayout c=card();c.addView(t(records.length()==0?"No feedback loaded yet. Tap Refresh if needed.":"No matching feedback.",14,MUTED,false));list.addView(c,p(-1,-2,10));}
    }
    private void add(LinearLayout box,String label,String data){if(data.isEmpty())return;box.addView(t(label,12,MUTED,true),p(-1,-2,3));TextView x=t(data,14,INK,false);x.setTextIsSelectable(true);box.addView(x,p(-1,-2,12));}
    private void details(JSONObject j){
        ScrollView scroll=new ScrollView(this);LinearLayout inner=v();inner.setPadding(dp(18),dp(9),dp(18),dp(6));scroll.addView(inner);
        add(inner,category(j)+" · "+when(j),get(j,"message"));
        add(inner,"Contact",get(j,"contact"));add(inner,"App version",get(j,"app_version"));add(inner,"Device",get(j,"user_agent"));
        String link=get(j,"screenshot_url");
        if(!link.isEmpty()){Button screenshot=b("Open screenshot / video ↗",false);inner.addView(screenshot,p(-1,46,14));screenshot.setOnClickListener(view->{try{Uri uri=Uri.parse(link);String scheme=uri.getScheme();if(!"https".equalsIgnoreCase(scheme)&&!"http".equalsIgnoreCase(scheme))throw new IllegalArgumentException();startActivity(new Intent(Intent.ACTION_VIEW,uri));}catch(Exception e){Toast.makeText(this,"Invalid link",Toast.LENGTH_SHORT).show();}});}
        inner.addView(t("Status",13,INK,true),p(-1,-2,5));
        Spinner spinner=new Spinner(this);ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,new String[]{"New","Reviewing","Fixed","Closed"});adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);spinner.setAdapter(adapter);
        for(int k=0;k<4;k++)if(STATUS[k].equals(get(j,"status")))spinner.setSelection(k);
        inner.addView(spinner,p(-1,47,13));inner.addView(t("Private admin note",13,INK,true),p(-1,-2,6));
        EditText note=new EditText(this);note.setText(get(j,"admin_note"));note.setMinLines(2);note.setMaxLines(5);note.setTextSize(14);note.setHint("Optional note...");note.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        inner.addView(note,p(-1,-2,10));
        new AlertDialog.Builder(this).setTitle("Feedback details").setView(scroll)
            .setNegativeButton("Close",null).setPositiveButton("Save changes",(dialog,which)->save(get(j,"id"),STATUS[spinner.getSelectedItemPosition()],note.getText().toString().trim())).show();
    }
    private void load(){
        if(busy||token.isEmpty())return;busy=true;final int current=session;final String entered=token;if(records.length()==0)state.setText("Loading live feedback...");
        io.execute(()->{try{
            Reply r=request("GET",null,entered);
            if(r.code==401||r.code==403){runOnUiThread(()->{if(current!=session)return;busy=false;FeedbackAlerts.disable(this);showLogin("Incorrect or expired admin token.");});return;}
            JSONObject obj=new JSONObject(r.body);if(r.code!=200||!obj.optBoolean("ok"))throw new IllegalStateException("HTTP "+r.code+" — server unavailable");
            JSONArray next=obj.optJSONArray("items");if(next==null)next=new JSONArray();final JSONArray result=next;
            runOnUiThread(()->{if(current!=session)return;busy=false;boolean changed=!records.toString().equals(result.toString());records=result;state.setText("Live feedback · "+records.length()+" reports");if(changed)render();});
        }catch(Exception e){fail(current,"Could not load feedback: "+e.getMessage());}});
    }
    private void save(String id,String status,String note){
        if(busy||id.isEmpty()||token.isEmpty())return;busy=true;final int current=session;final String entered=token;state.setText("Saving...");
        io.execute(()->{try{
            JSONObject body=new JSONObject();body.put("id",id);body.put("status",status);body.put("admin_note",note);
            Reply r=request("PATCH",body.toString(),entered);JSONObject j=new JSONObject(r.body);
            if(r.code==401||r.code==403){runOnUiThread(()->{if(current!=session)return;busy=false;FeedbackAlerts.disable(this);showLogin("Session expired.");});return;}
            if(r.code<200||r.code>299||!j.optBoolean("ok"))throw new IllegalStateException("Server rejected update: "+r.code);
            runOnUiThread(()->{if(current!=session)return;busy=false;Toast.makeText(this,"Saved",Toast.LENGTH_SHORT).show();load();});
        }catch(Exception e){fail(current,"Could not save: "+e.getMessage());}});
    }
    private void fail(int current,String message){runOnUiThread(()->{if(current!=session)return;busy=false;if(state!=null)state.setText(message);});}
    private static final class Reply{final int code;final String body;Reply(int c,String b){code=c;body=b;}}
    private Reply request(String method,String payload,String entered)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(API).openConnection();
        try{
            c.setInstanceFollowRedirects(false);c.setConnectTimeout(12000);c.setReadTimeout(15000);c.setRequestMethod(method);
            c.setRequestProperty("Accept","application/json");c.setRequestProperty("x-admin-token",entered);
            if(payload!=null){byte[] bytes=payload.getBytes(StandardCharsets.UTF_8);c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");c.setFixedLengthStreamingMode(bytes.length);try(OutputStream out=c.getOutputStream()){out.write(bytes);}}
            int status=c.getResponseCode();InputStream in=status>=400?c.getErrorStream():c.getInputStream();
            if(in==null)return new Reply(status,"{}");
            try(InputStream stream=in;ByteArrayOutputStream out=new ByteArrayOutputStream()){
                byte[] buffer=new byte[4096];int n,size=0;
                while((n=stream.read(buffer))!=-1){size+=n;if(size>4_000_000)throw new IOException("Response too large");out.write(buffer,0,n);}
                return new Reply(status,out.toString(StandardCharsets.UTF_8.name()));
            }
        }finally{c.disconnect();}
    }
}
