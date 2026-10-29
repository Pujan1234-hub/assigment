package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.text.TextWatcher;
import android.text.Editable;
import org.json.JSONArray;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
/** Actual native Android advanced data explorer; all values come from the web's existing validated APIs. */
public final class FloodSafeAdvancedActivity extends Activity {
 private static final String API="https://pjbuilts.com/api/";
 private final ExecutorService pool=Executors.newFixedThreadPool(2);
 private final int ink=Color.rgb(19,53,74),muted=Color.rgb(99,125,145);
 private LinearLayout content,controls,holder;
 private EditText search;
 private TextView summary;
 private JSONArray entries;
 private String mode="river";
 private boolean english;
 private double lat=Double.NaN,lon=Double.NaN;
 private int requestSeq=0;
 private int dp(float v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
 private String tr(String ne,String en){return english?en:ne;}
 @Override public void onCreate(Bundle state){
  super.onCreate(state);
  english=getSharedPreferences("floodsafe-native-full",MODE_PRIVATE).getBoolean("lang_en",false);
  lat=getIntent().getDoubleExtra("lat",Double.NaN);
  lon=getIntent().getDoubleExtra("lon",Double.NaN);
  getWindow().setStatusBarColor(Color.rgb(224,243,252));
  LinearLayout page=new LinearLayout(this);page.setOrientation(1);page.setPadding(dp(12),dp(12),dp(12),0);page.setBackgroundColor(Color.rgb(232,246,253));
  Button back=button("← "+tr("गृह","Home"));back.setOnClickListener(v->finish());page.addView(back,new LinearLayout.LayoutParams(-1,dp(45)));
  TextView title=label(tr("FloodSafe Nepal · उन्नत जानकारी","FloodSafe Nepal · Advanced"),22,true);page.addView(title);
  TextView desc=label(tr("नदी, वर्षा र पूर्वानुमानको आधिकारिक/मोडेल विवरण","River, rainfall, forecasts and verified source details"),11,false);page.addView(desc);
  ScrollView scroll=new ScrollView(this);page.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  content=new LinearLayout(this);content.setOrientation(1);content.setPadding(0,dp(10),0,dp(30));scroll.addView(content);
  controls=new LinearLayout(this);controls.setOrientation(1);content.addView(controls);
  for(String[] segment:new String[][]{
    {"river","🌊 "+tr("नदी स्टेशन","Rivers")},
    {"rain","🌧 "+tr("वर्षा स्टेशन","Rainfall")},
    {"forecast","📈 "+tr("७ दिनको पूर्वानुमान","7-day forecast")},
    {"warning","⚠ "+tr("सरकारी चेतावनी","Govt warning")},
    {"events","⚡ "+tr("घटनाहरू","Events")}
  }){
    final String key=segment[0];
    Button btn=button(segment[1]);btn.setOnClickListener(v->showMode(key));
    controls.addView(btn,new LinearLayout.LayoutParams(-1,dp(45)));
  }
  Button nasa=button("🛰 NASA "+tr("नेपालको वर्षा/पहिरो नक्सा","Rain/landslide map"));
  nasa.setOnClickListener(v->startActivity(new Intent(this,FloodSafeNasaSatelliteActivity.class)));
  controls.addView(nasa,new LinearLayout.LayoutParams(-1,dp(45)));
  search=new EditText(this);search.setSingleLine(true);search.setTextSize(14);
  search.setHint(tr("जिल्ला वा नदी/स्टेशनको नाम लेख्नुहोस्","Type district or station"));
  content.addView(search,new LinearLayout.LayoutParams(-1,dp(52)));
  summary=label("",12,false);content.addView(summary);
  holder=new LinearLayout(this);holder.setOrientation(1);content.addView(holder);
  search.addTextChangedListener(new TextWatcher(){
    @Override public void beforeTextChanged(CharSequence s,int start,int count,int after){}
    @Override public void onTextChanged(CharSequence s,int start,int before,int count){if(entries!=null)renderEntries();}
    @Override public void afterTextChanged(Editable e){}
  });
  setContentView(page);
  showMode("river");
 }
 private TextView label(String val,int sp,boolean bold){
   TextView t=new TextView(this);t.setText(val);t.setTextColor(bold?ink:muted);t.setTextSize(sp);
   t.setPadding(dp(12),dp(10),dp(8),dp(10));
   if(bold)t.setTypeface(null,1);
   return t;
 }
 private Button button(String text){
   Button b=new Button(this);b.setText(text);b.setTextSize(12);b.setAllCaps(false);b.setTextColor(ink);
   b.setBackgroundColor(Color.WHITE);return b;
 }
 private void card(String heading,String body){
   LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setPadding(dp(12),dp(9),dp(12),dp(8));
   GradientDrawable g=new GradientDrawable();g.setColor(Color.WHITE);g.setCornerRadius(dp(14));g.setStroke(dp(1),Color.rgb(208,227,239));box.setBackground(g);
   box.addView(label(heading,15,true));box.addView(label(body,12,false));
   LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(6),0,dp(6));holder.addView(box,lp);
 }
 private void reset(){
   holder.removeAllViews();entries=null;summary.setText(tr("नयाँ मापन जाँच्दै…","Checking latest data…"));
   boolean filtered=mode.equals("river")||mode.equals("rain");search.setVisibility(filtered?View.VISIBLE:View.GONE);search.setText("");
 }
 private String urlFor(String k){
   if(k.equals("river"))return API+"floodsafe-station-details?kind=stations";
   if(k.equals("rain"))return API+"floodsafe-dhm-stations?kind=rain";
   if(k.equals("warning"))return API+"floodsafe-official-weather";
   if(k.equals("events"))return API+"floodsafe-live-feeds?kind=quake";
   if(Double.isFinite(lat)&&Double.isFinite(lon))
     return String.format(Locale.US,API+"floodsafe-station-details?kind=hero&lat=%.5f&lon=%.5f",lat,lon);
   return null;
 }
 private void showMode(String newMode){
   mode=newMode;reset();
   final int seq=++requestSeq;String url=urlFor(mode);
   if(url==null){summary.setText(tr("GPS अनुमति लिएपछि स्थानीय पूर्वानुमान देखिन्छ।","Enable GPS to see your local forecast."));return;}
   pool.execute(()->{
     try{JSONObject j=get(url);runOnUiThread(()->{
       if(seq!=requestSeq||isFinishing()||isDestroyed())return;
       if(mode.equals("river")||mode.equals("rain")){
         entries=j.optJSONArray(mode.equals("river")?"stations":"items");
         if(entries==null)entries=new JSONArray();renderEntries();
       }else if(mode.equals("forecast"))renderForecast(j);
       else renderNotices(j);
     });}catch(Exception e){runOnUiThread(()->{if(seq==requestSeq&&!isFinishing()&&!isDestroyed())summary.setText(tr("मापन उपलब्ध छैन। फेरि प्रयास गर्नुहोस्।","Data unavailable. Try again."));});}
   });
 }
 private void renderEntries(){
   holder.removeAllViews();JSONArray data=entries;if(data==null)return;
   String q=search.getText().toString().trim().toLowerCase(Locale.ROOT);
   int found=0,displayed=0;
   for(int i=0;i<data.length();i++){
     JSONObject r=data.optJSONObject(i);if(r==null)continue;
     String name=r.optString("name"),district=r.optString("district"),basin=r.optString("basin");
     if(!q.isEmpty()&&!(name+" "+district+" "+basin).toLowerCase(Locale.ROOT).contains(q))continue;
     found++;
     if(displayed>=8)continue;
     displayed++;
     String stamp=r.optString(mode.equals("river")?"observed":"observedAt","");
     String val=mode.equals("river")?number(r,"level")+" m":number(r,"value")+" mm";
     if(mode.equals("river")&&!"observed".equals(r.optString("status")))val=tr("नयाँ मापन छैन","No current reading");
     final JSONObject station=r;
     LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setBackgroundColor(Color.WHITE);
     TextView header=label("🌊 "+name,15,true);box.addView(header);
     box.addView(label(district+" · "+val,12,false));
     box.setPadding(dp(5),dp(4),dp(5),dp(4));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(5),0,dp(5));holder.addView(box,p);
     box.setOnClickListener(v->showStation(station));
   }
   summary.setText(tr("जम्मा "+found+" स्टेशन · एउटा छानेर विवरण हेर्नुहोस्","Found "+found+" stations · Tap one for details"));
   if(found>8)card(tr("स्टेशन खोज्नुहोस्","Search stations"),tr("माथि जिल्ला वा स्टेशनको नाम लेख्दा सूची छोटिन्छ।","Type a district or station name above to narrow results."));
 }
 private static String number(JSONObject j,String key){
   double v=j.optDouble(key,Double.NaN);
   return Double.isFinite(v)?String.format(Locale.US,"%.2f",v):"—";
 }
 private void showStation(JSONObject r){
   holder.removeAllViews();
   String name=r.optString("name"),district=r.optString("district"),basin=r.optString("basin");
   String text;
   if(mode.equals("river")){
     text=tr("जिल्ला: ","District: ")+district+"\n"+
     tr("जलाधार: ","Basin: ")+basin+"\n"+
     tr("पानीको सतह: ","Water level: ")+number(r,"level")+" m\n"+
     "Warning: "+number(r,"warning")+" m · Danger: "+number(r,"danger")+" m\n"+
     tr("मापन समय: ","Observed: ")+r.optString("observed","—")+"\n"+
     tr("स्रोत: ","Source: ")+r.optString("measurementSource","DHM/BIPAD");
   }else{
     StringBuilder sb=new StringBuilder(tr("जिल्ला: ","District: ")+district+"\n");
     JSONObject hours=r.optJSONObject("rainfallHours");
     if(hours!=null)for(int n:new int[]{1,3,6,12,24})sb.append(n).append("h: ").append(number(hours,String.valueOf(n))).append(" mm\n");
     sb.append(tr("मापन समय: ","Observed: ")).append(r.optString("observedAt","—"));
     text=sb.toString();
   }
   card(name,text);
   Button change=button(tr("← अर्को स्टेशन छान्नुहोस्","← Choose another station"));
   change.setOnClickListener(v->renderEntries());holder.addView(change);
 }
 private void renderForecast(JSONObject j){
   holder.removeAllViews();summary.setText(tr("वर्षा mm र GloFAS नदी बहाव m³/s फरक हुन्; आधिकारिक मापन होइन।","Rain mm and GloFAS discharge m³/s are distinct model predictions."));
   JSONArray rain=j.optJSONArray("rainfall"),flow=j.optJSONArray("flow");
   int size=Math.max(rain==null?0:rain.length(),flow==null?0:flow.length());
   if(size==0){card(tr("पूर्वानुमान छैन","No forecast"),tr("यो स्थानमा मोडेल उपलब्ध छैन।","No model available here."));return;}
   for(int i=0;i<Math.min(7,size);i++){
     JSONObject a=rain==null?null:rain.optJSONObject(i),b=flow==null?null:flow.optJSONObject(i);
     String date=a==null?(b==null?"—":b.optString("date","—")):a.optString("date","—");
     String day=english?date:NepalBs.shortDate(date);
     String r=a==null?"—":number(a,"value")+" mm",f=b==null?"—":number(b,"value")+" m³/s";
     card(day,tr("अनुमानित वर्षा: ","Rain: ")+r+"\n"+tr("अनुमानित नदी बहाव: ","Discharge: ")+f);
   }
 }
 private void renderNotices(JSONObject j){
   holder.removeAllViews();entries=null;
   JSONArray rows=mode.equals("warning")?GovernmentNotices.active(j,System.currentTimeMillis()):j.optJSONArray("items");
   if(rows==null||rows.length()==0){summary.setText(tr("नयाँ घटना वा सूचना भेटिएन।","No recent events or notices found."));return;}
   summary.setText(tr(rows.length()+" उपलब्ध सूचना",""+rows.length()+" entries"));
   for(int i=0;i<Math.min(15,rows.length());i++){
     JSONObject row=rows.optJSONObject(i);if(row==null)continue;
     String title=row.optString(english?"titleEn":"titleNe",row.optString("title",row.optString("place","")));
     String time=row.optString("validFrom",row.optString("time",""));
     String until=row.optString("validUntil","");
     String body=(time.isEmpty()?"":tr("सुरु: ","From: ")+time+"\n")+
                  (until.isEmpty()?"":tr("समाप्त: ","Until: ")+until+"\n")+
                  row.optString(english?"summaryEn":"summaryNe",row.optString("place",""));
     card(title,body);
     String link=row.optString("sourceUrl","");
     if(link.startsWith("https://")){
       Button source=button(tr("मूल सरकारी सूचना ↗","Original source ↗"));
       source.setOnClickListener(v->startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(link))));
       holder.addView(source);
     }
   }
 }
 private JSONObject get(String url)throws Exception{
   HttpURLConnection conn=(HttpURLConnection)new URL(url).openConnection();
   conn.setConnectTimeout(12000);conn.setReadTimeout(14000);conn.setUseCaches(false);
   try{
     if(conn.getResponseCode()!=200)throw new IllegalStateException("HTTP unavailable");
     StringBuilder body=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(conn.getInputStream(),StandardCharsets.UTF_8))){
       String l;while((l=r.readLine())!=null){body.append(l);if(body.length()>4_000_000)throw new IllegalStateException("Too large");}
     }
     return new JSONObject(body.toString());
   }finally{conn.disconnect();}
 }
 @Override public void onDestroy(){requestSeq++;pool.shutdownNow();super.onDestroy();}
}