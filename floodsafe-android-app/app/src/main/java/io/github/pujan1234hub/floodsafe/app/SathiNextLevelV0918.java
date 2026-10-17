package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.WeakHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** v0.9.18: SATHI-only upgrade plus the two requested native presentation repairs. */
final class SathiNextLevelV0918 {
    private static final String PREFS="floodsafe-native-full";
    private static final String RIVER="https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String NEWS="https://camkoacuokffryyrygda.supabase.co/functions/v1/news-live-three";
    private static final long FRESH=10L*60L*1000L, CACHE=45_000L;
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static final ExecutorService IO=Executors.newFixedThreadPool(3);
    private static final WeakHashMap<View,Boolean> patched=new WeakHashMap<>();
    private static final WeakHashMap<TextView,CloudDrawable> clouds=new WeakHashMap<>();
    private static final Object cacheLock=new Object();
    private static List<Station> cache=new ArrayList<>();
    private static long cacheAt;
    private static boolean installed;

    private SathiNextLevelV0918(){}

    static synchronized void install(Context context){
        if(installed||context==null)return;
        Context c=context.getApplicationContext();
        if(!(c instanceof Application))return;
        installed=true;
        ((Application)c).registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks(){
            public void onActivityCreated(Activity a,Bundle b){}
            public void onActivityStarted(Activity a){}
            public void onActivityResumed(Activity a){if(target(a)){MAIN.postDelayed(()->patch(a),250);MAIN.postDelayed(()->patch(a),900);}}
            public void onActivityPaused(Activity a){}
            public void onActivityStopped(Activity a){}
            public void onActivitySaveInstanceState(Activity a,Bundle b){}
            public void onActivityDestroyed(Activity a){}
        });
    }

    private static boolean target(Activity a){return a!=null&&a.getClass().getName().endsWith(".NativeFullActivity");}

    private static void patch(Activity a){
        if(a==null||a.isFinishing()||a.isDestroyed()||a.getWindow()==null)return;
        View root=a.getWindow().getDecorView();
        List<TextView> all=new ArrayList<>(); collect(root,all);
        for(TextView v:all){
            String t=String.valueOf(v.getText()).toUpperCase(Locale.ROOT);
            if(t.contains("SATHI")&&v.isClickable()){
                synchronized(patched){if(Boolean.TRUE.equals(patched.get(v)))continue;patched.put(v,true);}
                v.setOnClickListener(x->show(a));
            }
        }
        dedupeLanguage(all);
        animateCloud(all);
    }

    private static void collect(View v,List<TextView> out){
        if(v instanceof TextView)out.add((TextView)v);
        if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)collect(g.getChildAt(i),out);}
    }

    private static void dedupeLanguage(List<TextView> all){
        List<TextView> x=new ArrayList<>();
        for(TextView v:all){if(v.getVisibility()!=View.VISIBLE||!v.isClickable())continue;String s=norm(String.valueOf(v.getText()));if(s.contains("नेपाली")||s.contains("अङ्ग्रेजी")||s.contains("अंग्रेजी")||s.equals("english")||s.equals("nepali")||s.contains(" english")||s.contains(" nepali"))x.add(v);}
        if(x.size()<2)return;
        x.sort(Comparator.comparingInt(SathiNextLevelV0918::screenY));
        int top=screenY(x.get(0));
        for(int i=1;i<x.size();i++)if(screenY(x.get(i))>top+dp(x.get(i).getContext(),28))x.get(i).setVisibility(View.GONE);
    }

    private static int screenY(View v){int[]p={0,0};try{v.getLocationOnScreen(p);}catch(Exception ignored){}return p[1];}

    private static void animateCloud(List<TextView> all){
        for(TextView v:all){
            if(v.getVisibility()!=View.VISIBLE)continue;
            String s=norm(String.valueOf(v.getText()));
            if(!(s.contains("cloud")||s.contains("overcast")||s.contains("बादल")||s.contains("मेघाच्छन्न")))continue;
            synchronized(clouds){
                if(clouds.containsKey(v))return;
                CloudDrawable d=new CloudDrawable(v.getContext());d.setBounds(0,0,dp(v.getContext(),48),dp(v.getContext(),30));
                v.setCompoundDrawablePadding(dp(v.getContext(),8));v.setCompoundDrawables(d,null,null,null);clouds.put(v,d);d.start();
            }
            return;
        }
    }

    private static void show(Activity a){
        boolean en=en(a);
        LinearLayout box=new LinearLayout(a);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(a,18),dp(a,6),dp(a,18),0);
        TextView out=new TextView(a);out.setTextSize(15);out.setTextColor(Color.rgb(25,51,75));out.setLineSpacing(0,1.12f);
        out.setText(en?"Hi — I’m SATHI. Ask me about a named river, warnings, Nepal weather, current app news, nearby stations or FloodSafe features.":"नमस्ते — म SATHI हुँ। नदी/खोला, चेतावनी, नेपालको कुनै ठाउँको मौसम, ताजा app समाचार वा FloodSafe data बारे सोध्नुहोस्।");box.addView(out);
        EditText in=new EditText(a);in.setTextSize(16);in.setMaxLines(3);in.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);in.setImeOptions(EditorInfo.IME_ACTION_SEND);in.setHint(en?"Ninda Khola status / Kathmandu weather":"Ninda khola status / Kathmandu ko mausam");
        LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(-1,-2);ip.setMargins(0,dp(a,13),0,dp(a,9));box.addView(in,ip);
        LinearLayout row=new LinearLayout(a);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);
        Button mic=new Button(a);mic.setAllCaps(false);mic.setText(en?"🎙 Voice":"🎙 आवाज");Button ask=new Button(a);ask.setAllCaps(false);ask.setText(en?"Ask SATHI":"SATHI लाई सोध्नुहोस्");
        row.addView(mic,new LinearLayout.LayoutParams(0,dp(a,50),.38f));LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(0,dp(a,50),.62f);ap.setMargins(dp(a,8),0,0,0);row.addView(ask,ap);box.addView(row);
        Session s=new Session(a,out,in,en);
        AlertDialog d=new AlertDialog.Builder(a).setTitle("🤖 SATHI AI • live app data").setView(box).setNegativeButton(en?"Close":"बन्द",null).create();
        ask.setOnClickListener(v->s.askTyped());mic.setOnClickListener(v->s.listen());in.setOnEditorActionListener((v,id,e)->{if(id==EditorInfo.IME_ACTION_SEND){s.askTyped();return true;}return false;});d.setOnDismissListener(v->s.close());d.show();
    }

    private static boolean en(Activity a){return a.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getBoolean("lang_en",false);}

    private static final class Session{
        final Activity a;final TextView out;final EditText in;final boolean en;TextToSpeech tts;SpeechRecognizer sr;boolean closed;
        Session(Activity a,TextView out,EditText in,boolean en){this.a=a;this.out=out;this.in=in;this.en=en;tts=new TextToSpeech(a.getApplicationContext(),st->{if(st==TextToSpeech.SUCCESS&&tts!=null){Locale l=en?Locale.UK:Locale.forLanguageTag("ne-NP");int r=tts.setLanguage(l);if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(en?Locale.UK:new Locale("ne"));tts.setSpeechRate(.93f);tts.setPitch(1.02f);}});}
        void askTyped(){String q=in.getText()==null?"":in.getText().toString().trim();if(q.isEmpty())return;in.setText("");ask(q);}
        void ask(String q){out.setText((en?"You: ":"तपाईं: ")+q+"\n\nSATHI: "+(en?"Checking live app data…":"live app data हेर्दैछु…"));IO.execute(()->{String r;try{r=answer(a,q,en);}catch(Exception e){r=en?"I couldn't refresh that data just now. I won't guess; please try again in a moment.":"अहिले त्यो data refresh गर्न सकिनँ। म अनुमान गरेर गलत कुरा भन्दिनँ; केही क्षणपछि फेरि सोध्नुहोस्।";}String result=r;MAIN.post(()->{if(closed||a.isFinishing()||a.isDestroyed())return;out.setText((en?"You: ":"तपाईं: ")+q+"\n\nSATHI: "+result);speak(result);});});}
        void listen(){
            if(a.checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){a.requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},9182);out.setText(en?"Allow microphone permission, then tap Voice again.":"Microphone permission Allow गरेपछि फेरि आवाज थिच्नुहोस्।");return;}
            if(!SpeechRecognizer.isRecognitionAvailable(a)){out.setText(en?"Voice recognition is unavailable on this phone. Type your question instead.":"यो फोनमा voice recognition उपलब्ध छैन। प्रश्न टाइप गर्नुहोस्।");return;}
            try{if(sr!=null)sr.destroy();}catch(Exception ignored){}sr=SpeechRecognizer.createSpeechRecognizer(a);sr.setRecognitionListener(new RecognitionListener(){
                public void onReadyForSpeech(Bundle b){out.setText(en?"🎙 Listening…":"🎙 सुन्दैछु…");}public void onBeginningOfSpeech(){}public void onRmsChanged(float x){}public void onBufferReceived(byte[]b){}public void onEndOfSpeech(){}public void onPartialResults(Bundle b){}public void onEvent(int t,Bundle b){}
                public void onError(int e){out.setText(en?"I couldn't understand that. Try once more.":"आवाज बुझ्न सकिनँ। फेरि प्रयास गर्नुहोस्।");}
                public void onResults(Bundle b){ArrayList<String>r=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);if(r!=null&&!r.isEmpty())ask(r.get(0));}
            });
            Intent i=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,en?"en-GB":"ne-NP").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,5);sr.startListening(i);
        }
        void speak(String text){if(tts==null||text==null||text.trim().isEmpty())return;String c=text.replace("🔴"," ").replace("🟠"," ").replace("🟡"," ").replace("🔵"," ").replace("⚪"," ").replace("🌧️"," ").replace("☁️"," ").replace("⚠️"," ").replace("•"," ").replaceAll("\\s+"," ").trim();try{tts.speak(c,TextToSpeech.QUEUE_FLUSH,null,"sathi-v0918");}catch(Exception ignored){}}
        void close(){closed=true;try{if(sr!=null)sr.destroy();}catch(Exception ignored){}try{if(tts!=null){tts.stop();tts.shutdown();}}catch(Exception ignored){}}
    }

    private static String answer(Activity a,String raw,boolean en)throws Exception{
        String q=norm(raw);if(q.isEmpty())return en?"Ask me a FloodSafe question.":"FloodSafe सम्बन्धी प्रश्न सोध्नुहोस्।";
        if(any(q,"weather","mausam","मौसम","temperature","temp","पानी पर्छ","वर्षा"))return weather(a,raw,en);
        if(any(q,"river","khola","nadi","नदी","खोला","जलस्तर","water level","flood","बाढी","warning","danger","चेतावनी","खतरा","station","gauge","near me","nearby","najik","नजिक"))return rivers(a,raw,en);
        if(any(q,"news","samachar","समाचार","खबर","khabar","headline"))return news(en);
        if(any(q,"notification","alert","push","2 km","2km"))return en?"FloodSafe sends the emergency river alert only for a fresh, verified Warning or Danger gauge within 2 km in Nepal. Weather notifications are separate from that river safety rule.":"FloodSafe ले नेपालभित्र fresh र verified Warning/Danger station २ km भित्र परेमा मात्र emergency river alert दिन्छ। मौसम notification त्यसबाट छुट्टै हुन्छ।";
        if(any(q,"map","नक्सा","naksa"))return en?"The map uses the app's official BIPAD/DHM station feed and named river geometry. Tap a station for its level, status and official measurement time; I do not invent missing readings.":"Map मा app कै official BIPAD/DHM station feed र named river geometry प्रयोग हुन्छ। Station थिच्दा level, status र official time देखिन्छ; reading नभए म बनाउँदिनँ।";
        if(any(q,"location","gps","स्थान","where am i")){double lat=pref(a,"lat"),lon=pref(a,"lon");if(valid(lat,lon))return en?String.format(Locale.UK,"Your FloodSafe monitoring coordinate is %.4f, %.4f. It is used for local weather and nearby verified river risk.",lat,lon):String.format(Locale.US,"FloodSafe को monitoring coordinate %.4f, %.4f छ। यसलाई local weather र nearby verified river risk मिलाउन प्रयोग हुन्छ।",lat,lon);return en?"FloodSafe does not currently have a fresh monitoring location. Tap My current location first.":"FloodSafe मा अहिले fresh monitoring location छैन। पहिले My current location थिच्नुहोस्।";}
        if(any(q,"what can you","what do you","help","sathi","app","floodsafe","के गर्छ","k garxa","k garna"))return en?"I can answer from FloodSafe's current app data: named river or district status, Warning/Danger lists, nearby stations, Nepal-place weather such as Kathmandu, latest app news, GPS/location rules, alerts and map features. Type or speak naturally; I also read the final answer aloud.":"म FloodSafe को current app data बाट named river/district status, Warning/Danger, nearby station, Kathmandu जस्ता ठाउँको मौसम, ताजा app समाचार, GPS/alert/map सम्बन्धी उत्तर दिन सक्छु। टाइप वा आवाजमा सोध्नुस्; final answer म बोल्छु पनि।";
        return en?"Ask naturally about FloodSafe data, for example: “Ninda Khola status”, “rivers in Jhapa”, “Kathmandu weather”, “latest news” or “which rivers are in warning?”. I use current app/official data and won't invent a missing reading.":"FloodSafe data बारे सामान्य तरिकाले सोध्नुस्: “Ninda khola status”, “Jhapa ko river status”, “Kathmandu ko mausam”, “aile samachar k cha” वा “kun khola warning ma cha?”। reading नभए म बनाउँदिनँ।";
    }

    private static String weather(Activity a,String raw,boolean en)throws Exception{
        String place=weatherPlace(raw);double lat,lon;String label;
        if(place.isEmpty()||currentWord(place)){lat=pref(a,"lat");lon=pref(a,"lon");if(!valid(lat,lon))return en?"Tap My current location for local weather, or ask for a named Nepal place such as Kathmandu weather.":"Local weather का लागि My current location थिच्नुहोस्, वा “Kathmandu ko mausam” जस्तो ठाउँको नाम लिएर सोध्नुहोस्।";label=en?"your monitoring location":"तपाईंको monitoring location";}
        else{Geo g=geocode(place);if(g==null)return en?"I couldn't verify that place inside Nepal, so I won't guess its weather. Try the municipality or district name.":"त्यो ठाउँ नेपालभित्र verify गर्न सकिनँ, त्यसैले मौसम अनुमान गर्दिनँ। Municipality वा district name ले फेरि सोध्नुहोस्।";lat=g.lat;lon=g.lon;label=g.name;}
        String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&forecast_days=1&timezone=Asia%%2FKathmandu",lat,lon);
        JSONObject c=get(u).optJSONObject("current");if(c==null)throw new IllegalStateException("weather missing");double t=c.optDouble("temperature_2m",Double.NaN),r=c.optDouble("precipitation",Double.NaN),h=c.optDouble("relative_humidity_2m",Double.NaN),w=c.optDouble("wind_speed_10m",Double.NaN);String condition=condition(c.optInt("weather_code",-1),en);
        return en?String.format(Locale.UK,"%s: %s, %s°C, rain %.1f mm, humidity %s%%, wind %s km/h. This is the current weather feed, not a river warning.",label,condition,f0(t),finite(r),f0(h),f0(w)):String.format(Locale.US,"%s: %s, तापक्रम %s°C, वर्षा %.1f mm, humidity %s%%, हावा %s km/h। यो current weather feed हो, river warning होइन।",label,condition,f0(t),finite(r),f0(h),f0(w));
    }

    private static String news(boolean en)throws Exception{
        JSONObject j=get(NEWS+"?_sathi="+System.currentTimeMillis());JSONArray a=j.optJSONArray("items");if(a==null)a=j.optJSONArray("results");if(a==null)a=j.optJSONArray("news");if(a==null||a.length()==0)return en?"The app has no fresh live story in its current news feed right now.":"App को current news feed मा अहिले fresh live story भेटिएन।";
        List<String>l=new ArrayList<>();for(int i=0;i<a.length()&&l.size()<4;i++){JSONObject o=a.optJSONObject(i);if(o==null)continue;String t=text(o,"title","headline"),s=text(o,"source","publisher");if(!t.isEmpty())l.add((s.isEmpty()?"":s+": ")+t);}if(l.isEmpty())return en?"The current app news feed returned no readable headline.":"Current app news feed बाट readable headline आएन।";
        StringBuilder b=new StringBuilder(en?"Latest stories in the FloodSafe feed: ":"FloodSafe feed का ताजा समाचार: ");for(int i=0;i<l.size();i++){if(i>0)b.append(" • ");b.append(i+1).append(". ").append(l.get(i));}return b.toString();
    }

    private static String rivers(Activity a,String raw,boolean en)throws Exception{
        List<Station>rows=stations();if(rows.isEmpty())return en?"The official river feed did not return a usable station reading right now. I won't substitute a fake status.":"Official river feed बाट अहिले usable station reading आएन। म fake status बनाउँदिनँ।";String q=norm(raw);
        if(any(q,"nearby","near me","najik","नजिक")){double lat=pref(a,"lat"),lon=pref(a,"lon");if(!valid(lat,lon))return en?"Set a current Nepal location first so I can rank nearby official stations.":"Nearby official station बताउन पहिले current Nepal location सेट गर्नुहोस्।";List<Station>x=new ArrayList<>(rows);x.sort(Comparator.comparingDouble(s->km(lat,lon,s.lat,s.lon)));StringBuilder b=new StringBuilder(en?"Nearest official stations: ":"नजिकका official station: ");for(int i=0;i<Math.min(3,x.size());i++){if(i>0)b.append(" • ");Station s=x.get(i);b.append(s.name).append(" — ").append(stage(s.stage,en)).append(", ").append(String.format(Locale.US,"%.1f km",km(lat,lon,s.lat,s.lon)));}return b.toString();}
        if(any(q,"which","kun","कुन","all warning","all danger","warning ma","danger ma","चेतावनीमा","खतरामा")){List<Station>x=new ArrayList<>();for(Station s:rows)if(s.fresh&&(s.stage.equals("danger")||s.stage.equals("warning")||s.stage.equals("alert")))x.add(s);x.sort(Comparator.comparingInt(s->rank(s.stage)));if(x.isEmpty())return en?"In the current fresh official feed I don't see a station at Alert, Warning or Danger.":"अहिलेको fresh official feed मा Alert, Warning वा Danger मा पुगेको station देखिएन।";StringBuilder b=new StringBuilder(en?"Current risk stations: ":"अहिले risk मा रहेका station: ");for(int i=0;i<Math.min(8,x.size());i++){if(i>0)b.append(" • ");b.append(x.get(i).name).append(" — ").append(stage(x.get(i).stage,en));}return b.toString();}
        String target=riverTarget(raw);Station best=null;int score=0;for(Station s:rows){int z=score(q,target,s);if(z>score){score=z;best=s;}}if(best!=null&&score>=18)return format(best,en);
        List<Station>d=new ArrayList<>();for(Station s:rows){String district=norm(s.district);if(!district.isEmpty()&&(q.contains(district)||(!target.isEmpty()&&district.contains(target))))d.add(s);}if(!d.isEmpty()){d.sort(Comparator.comparingInt(s->rank(s.stage)));StringBuilder b=new StringBuilder(en?"Official stations in "+d.get(0).district+": ":d.get(0).district+" का official station: ");for(int i=0;i<Math.min(6,d.size());i++){if(i>0)b.append(" • ");Station s=d.get(i);b.append(s.name).append(" — ").append(stage(s.stage,en));if(Double.isFinite(s.level))b.append(String.format(Locale.US," %.2f m",s.level));}return b.toString();}
        return en?"I couldn't match that river/station to a verified reading in the current app feed. Try the official station or river name; I won't answer with a different river.":"Current app feed मा त्यो नदी/खोलालाई verified reading सँग match गर्न सकिनँ। Official station/river name ले फेरि सोध्नुहोस्; म अर्को खोलाको data मिसाउँदिनँ।";
    }

    private static int score(String q,String target,Station s){String n=norm(s.name),d=norm(s.district);if(n.isEmpty())return 0;if(q.contains(n))return 120+n.length();if(!target.isEmpty()&&n.contains(target))return 90+target.length();String nn=stripRiver(n),tt=stripRiver(target);if(!tt.isEmpty()&&nn.contains(tt))return 75+tt.length();int z=0;for(String t:tt.split(" ")){if(t.length()<3)continue;if(nn.contains(t))z+=18;if(!d.isEmpty()&&d.contains(t))z+=4;}return z;}

    private static String format(Station s,boolean en){StringBuilder b=new StringBuilder(s.name);if(!s.district.isEmpty())b.append(" (").append(s.district).append(")");b.append(" — ").append(stage(s.stage,en)).append(". ");if(!s.fresh){b.append(en?"The measurement is stale/unknown, so I am not calling it live.":"यो measurement stale/unknown छ, त्यसैले म यसलाई live भन्दिनँ।");return b.toString();}if(Double.isFinite(s.level))b.append(en?"Level ":"जलस्तर ").append(String.format(Locale.US,"%.2f m. ",s.level));if(Double.isFinite(s.warning))b.append(en?"Warning ":"Warning तह ").append(String.format(Locale.US,"%.2f m. ",s.warning));if(Double.isFinite(s.danger))b.append(en?"Danger ":"Danger तह ").append(String.format(Locale.US,"%.2f m. ",s.danger));if(s.at>0)b.append("Official measurement ").append(time(s.at)).append(". ");if(s.stage.equals("danger"))b.append(en?"Danger is active: stay away from the river edge and follow local official instructions.":"Danger active छ: नदी/खोला किनारबाट टाढा रहनुहोस् र local official निर्देशन पालना गर्नुहोस्।");else if(s.stage.equals("warning"))b.append(en?"Warning is active: stay alert and be ready to move to a safer place.":"Warning active छ: सतर्क रहनुहोस् र सुरक्षित ठाउँतर्फ जान तयार रहनुहोस्।");return b.toString().trim();}

    private static List<Station> stations()throws Exception{
        long now=System.currentTimeMillis();synchronized(cacheLock){if(!cache.isEmpty()&&now-cacheAt<CACHE)return new ArrayList<>(cache);}JSONObject root=get(RIVER+"?_sathi="+now);JSONArray a=root.optJSONArray("results");if(a==null)a=root.optJSONArray("data");if(a==null)a=root.optJSONArray("stations");if(a==null)a=new JSONArray();List<Station>out=new ArrayList<>();
        for(int i=0;i<a.length();i++){JSONObject r=a.optJSONObject(i);if(r==null)continue;double lat=num(r,"latitude","lat","stationLatitude","station_latitude"),lon=num(r,"longitude","lon","lng","stationLongitude","station_longitude");if(!valid(lat,lon))continue;double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","_lastWaterLevel"),warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");long at=parseTime(text(r,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));boolean fresh=at>0&&now-at<=FRESH&&at-now<=5L*60L*1000L;String raw=text(r,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus").toUpperCase(Locale.ROOT),st="unknown";if(fresh){if((Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED"))st="danger";else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE"))st="warning";else if((Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning*.8)||raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW"))st="alert";else if(Double.isFinite(level)||raw.contains("NORMAL")||raw.contains("BLUE"))st="normal";}String name=text(r,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official river station";out.add(new Station(name,text(r,"districtName","district_name","district"),lat,lon,level,warning,danger,at,fresh,st));}
        synchronized(cacheLock){cache=new ArrayList<>(out);cacheAt=now;}return out;
    }

    private static Geo geocode(String q)throws Exception{String x=q.trim();if(x.equalsIgnoreCase("kathmandu")||x.equals("काठमाडौं"))return new Geo("Kathmandu",27.7172,85.3240);if(x.equalsIgnoreCase("pokhara")||x.equals("पोखरा"))return new Geo("Pokhara",28.2096,83.9856);String u="https://geocoding-api.open-meteo.com/v1/search?name="+URLEncoder.encode(x,StandardCharsets.UTF_8.name())+"&count=10&language=en&format=json";JSONArray a=get(u).optJSONArray("results");if(a==null)return null;for(int i=0;i<a.length();i++){JSONObject o=a.optJSONObject(i);if(o==null)continue;double lat=o.optDouble("latitude",Double.NaN),lon=o.optDouble("longitude",Double.NaN);if((o.optString("country_code","").equalsIgnoreCase("NP")||o.optString("country","").equalsIgnoreCase("Nepal"))&&valid(lat,lon)){String name=o.optString("name",x),admin=o.optString("admin1","");if(!admin.isEmpty()&&!admin.equalsIgnoreCase(name))name+=", "+admin;return new Geo(name,lat,lon);}}return null;}

    private static String weatherPlace(String raw){String s=norm(raw);String[]r={"weather","mausam","मौसम","temperature","temp","rain","वर्षा","पानी","ko","को","ma","मा","kasto","कस्तो","cha","xa","chha","छ","ahile","aile","अहिले","today","now","please","bhana","भन"};for(String x:r)s=removeToken(s,x);return s.replaceAll("\\s+"," ").trim();}
    private static String riverTarget(String raw){String s=norm(raw);String[]r={"river","khola","nadi","नदी","खोला","station","gauge","status","level","water","जलस्तर","flood","बाढी","warning","danger","alert","चेतावनी","खतरा","ko","को","ma","मा","k","ke","के","kasto","कस्तो","cha","xa","chha","छ","ahile","aile","अहिले","please","bhana","भन"};for(String x:r)s=removeToken(s,x);return s.replaceAll("\\s+"," ").trim();}
    private static String stripRiver(String s){String x=norm(s);for(String w:new String[]{"river","khola","nadi","नदी","खोला","station","gauge"})x=removeToken(x,w);return x.replaceAll("\\s+"," ").trim();}
    private static String removeToken(String s,String token){String x=" "+s+" ";while(x.contains(" "+token+" "))x=x.replace(" "+token+" "," ");return x.trim();}
    private static boolean currentWord(String s){String q=norm(s);return q.isEmpty()||any(q,"my","current","here","mero","yaha","यहाँ","मेरो");}
    private static double pref(Activity a,String key){long x=a.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong(key,Double.doubleToRawLongBits(Double.NaN));return Double.longBitsToDouble(x);}
    private static String condition(int c,boolean en){if(c==0)return en?"clear":"सफा";if(c>=1&&c<=3)return en?"cloudy":"बादल";if(c==45||c==48)return en?"foggy":"कुहिरो";if((c>=51&&c<=67)||(c>=80&&c<=82))return en?"rain":"वर्षा";if(c>=71&&c<=77)return en?"snow":"हिउँ";if(c>=95)return en?"thunderstorm":"मेघगर्जन";return en?"current conditions":"हालको मौसम";}
    private static String stage(String s,boolean en){if(s.equals("danger"))return en?"DANGER":"खतरा";if(s.equals("warning"))return en?"WARNING":"चेतावनी";if(s.equals("alert"))return en?"ALERT":"सतर्क";if(s.equals("normal"))return en?"NORMAL":"सामान्य";return en?"STALE/UNKNOWN":"stale/unknown";}
    private static int rank(String s){return s.equals("danger")?0:s.equals("warning")?1:s.equals("alert")?2:s.equals("normal")?3:4;}
    private static String time(long ms){try{return DateTimeFormatter.ofPattern("HH:mm 'NPT'").withZone(ZoneId.of("Asia/Kathmandu")).format(Instant.ofEpochMilli(ms));}catch(Exception e){return "";}}
    private static long parseTime(String s){if(s==null||s.trim().isEmpty())return 0;String x=s.trim();try{long n=Long.parseLong(x);return x.length()<=10?n*1000L:n;}catch(Exception ignored){}try{return Instant.parse(x).toEpochMilli();}catch(Exception ignored){}try{return OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}try{return LocalDateTime.parse(x).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}return 0;}
    private static JSONObject get(String u)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(14000);c.setReadTimeout(20000);c.setUseCaches(false);c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store");int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null)b.append(line);}finally{c.disconnect();}return new JSONObject(b.toString());}
    private static String text(JSONObject o,String...k){for(String x:k){Object v=o.opt(x);if(v!=null&&v!=JSONObject.NULL&&!String.valueOf(v).trim().isEmpty())return String.valueOf(v).trim();}return "";}
    private static double num(JSONObject o,String...k){for(String x:k){Object v=o.opt(x);if(v==null||v==JSONObject.NULL)continue;try{double n=Double.parseDouble(String.valueOf(v).replace(",","").trim());if(Double.isFinite(n))return n;}catch(Exception ignored){}}return Double.NaN;}
    private static String norm(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[?!.:,;()\\[\\]{}\"'`]"," ").replaceAll("\\s+"," ").trim();}
    private static boolean any(String q,String...x){for(String s:x)if(q.contains(s))return true;return false;}
    private static boolean valid(double lat,double lon){return Double.isFinite(lat)&&Double.isFinite(lon)&&lat>=26.2&&lat<=30.5&&lon>=80&&lon<=88.35;}
    private static double km(double a,double o,double b,double p){double R=6371,d1=Math.toRadians(b-a),d2=Math.toRadians(p-o),z=Math.sin(d1/2)*Math.sin(d1/2)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(b))*Math.sin(d2/2)*Math.sin(d2/2);return 2*R*Math.asin(Math.sqrt(z));}
    private static String f0(double n){return Double.isFinite(n)?String.valueOf(Math.round(n)):"—";}
    private static double finite(double n){return Double.isFinite(n)?n:0;}
    private static int dp(Context c,int n){return Math.round(n*c.getResources().getDisplayMetrics().density);}

    private static final class Station{final String name,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;Station(String n,String d,double a,double o,double l,double w,double g,long t,boolean f,String s){name=n;district=d;lat=a;lon=o;level=l;warning=w;danger=g;at=t;fresh=f;stage=s;}}
    private static final class Geo{final String name;final double lat,lon;Geo(String n,double a,double o){name=n;lat=a;lon=o;}}

    private static final class CloudDrawable extends Drawable{
        final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);final ValueAnimator anim;float phase;
        CloudDrawable(Context c){p.setColor(Color.WHITE);p.setShadowLayer(dp(c,3),0,dp(c,2),0x33000000);anim=ValueAnimator.ofFloat(0,1);anim.setDuration(2400);anim.setRepeatCount(ValueAnimator.INFINITE);anim.setRepeatMode(ValueAnimator.REVERSE);anim.addUpdateListener(v->{phase=(float)v.getAnimatedValue();invalidateSelf();});}
        void start(){if(!anim.isStarted())anim.start();}
        public void draw(Canvas c){android.graphics.Rect b=getBounds();float w=b.width(),h=b.height(),dx=(phase-.5f)*w*.08f,y=h*(.60f-phase*.03f);c.save();c.translate(b.left+dx,b.top);c.drawOval(new RectF(w*.16f,y-h*.19f,w*.84f,y+h*.18f),p);c.drawCircle(w*.38f,y-h*.16f,h*.25f,p);c.drawCircle(w*.57f,y-h*.23f,h*.31f,p);c.drawCircle(w*.70f,y-h*.10f,h*.21f,p);c.restore();}
        public void setAlpha(int a){p.setAlpha(a);invalidateSelf();}public void setColorFilter(android.graphics.ColorFilter f){p.setColorFilter(f);invalidateSelf();}public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
}
