package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Content/config OTA, NOT executable code OTA.
 * Only allowlisted schema fields from our pinned HTTPS GitHub source.
 * Never remotely modify river-risk thresholds, alert logic, or permissions.
 * On failure, keep the last validated config or bundled v0.9.21 defaults.
 */
final class FloodSafeRemoteConfig {
    private static final String PREF="floodsafe-safe-content-ota-v1";
    private static final String CACHE="validated_json";
    private static final String RAW="https://raw.githubusercontent.com/Pujan1234-hub/assigment/floodsafe-ota-config-v0921/ota/floodsafe-config-v1.json";
    private static final int MAX_BYTES=64*1024;
    private static final long CHECK_MS=5*60_000L;
    private static final ExecutorService EXEC=Executors.newSingleThreadExecutor(r->{
        Thread t=new Thread(r,"FloodSafe-Safe-Content-OTA");t.setDaemon(true);return t;
    });
    private static final AtomicBoolean FETCHING=new AtomicBoolean(false);
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static volatile Snapshot current=Snapshot.defaults();
    private static volatile boolean initialized=false;
    private static volatile long lastAttemptElapsed=0L;
    private FloodSafeRemoteConfig(){}

    private static final class FAQ {
        final List<String> triggers;final String ne,en;
        FAQ(List<String> t,String n,String e){triggers=t;ne=n;en=e;}
    }
    private static final class Snapshot {
        final int revision,newsPollSeconds,knowledgeSeconds;
        final boolean enabled;
        final List<GyanKnowledge.Entry> lessons;
        final List<FAQ> faqs;
        final String canonical;
        Snapshot(int r,int p,int k,boolean e,List<GyanKnowledge.Entry> l,List<FAQ> f,String c){
            revision=r;newsPollSeconds=p;knowledgeSeconds=k;enabled=e;
            lessons=Collections.unmodifiableList(new ArrayList<>(l));
            faqs=Collections.unmodifiableList(new ArrayList<>(f));
            canonical=c;
        }
        static Snapshot defaults(){return new Snapshot(0,60,11,false,Collections.emptyList(),Collections.emptyList(),"");}
    }

    static void init(Context ctx){
        if(initialized)return;
        synchronized(FloodSafeRemoteConfig.class){
            if(initialized)return;
            Context c=ctx.getApplicationContext();
            String raw=c.getSharedPreferences(PREF,Context.MODE_PRIVATE).getString(CACHE,"");
            if(!raw.isEmpty()){
                try{current=parse(raw);}catch(Exception e){
                    c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().remove(CACHE).apply();
                }
            }
            initialized=true;
        }
    }
    static int revision(){return current.revision;}
    static int newsPollMillis(){return current.newsPollSeconds*1000;}
    static int knowledgeRotateMillis(){return current.knowledgeSeconds*1000;}
    static boolean remoteEnabled(){return current.enabled;}
    static String source(){return RAW;}

    static GyanKnowledge.Entry newsLessonAt(int index){
        Snapshot s=current;
        // Preserve built-in curated lessons; inject newly published content periodically.
        if(s.enabled&&!s.lessons.isEmpty()&&Math.floorMod(index,4)==0)
            return s.lessons.get(Math.floorMod(index/4,s.lessons.size()));
        return GyanKnowledge.ITEMS.get(Math.floorMod(index,GyanKnowledge.ITEMS.size()));
    }
    static String answerFAQ(String prompt,boolean english){
        Snapshot s=current;if(!s.enabled||prompt==null)return null;
        String q=prompt.trim().toLowerCase(Locale.ROOT);
        if(q.length()<3)return null;
        for(FAQ faq:s.faqs)for(String term:faq.triggers)
            if(q.contains(term))return english?faq.en:faq.ne;
        return null;
    }

    static void refreshAsync(Context ctx,Runnable onChanged){
        init(ctx);
        long elapsed=SystemClock.elapsedRealtime();
        if(lastAttemptElapsed>0 && elapsed-lastAttemptElapsed<CHECK_MS)return;
        if(!FETCHING.compareAndSet(false,true))return;
        lastAttemptElapsed=elapsed;
        final Context app=ctx.getApplicationContext();
        EXEC.execute(()->{
            try{
                // Fixed HTTPS host: no arbitrary URLs, redirects, or executable payloads.
                URL uri=new URL(RAW+"?check="+(System.currentTimeMillis()/60_000L));
                HttpURLConnection c=(HttpURLConnection)uri.openConnection();
                c.setInstanceFollowRedirects(false);
                c.setConnectTimeout(6000);c.setReadTimeout(7000);
                c.setRequestProperty("Accept","application/json");
                c.setUseCaches(false);
                try{
                    if(c.getResponseCode()!=200)throw new IllegalStateException("OTA config unavailable");
                    int length=c.getContentLength();
                    if(length>MAX_BYTES)throw new IllegalStateException("Too large");
                    ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                    try(InputStream input=c.getInputStream()){
                        byte[] buffer=new byte[4096];int n;
                        while((n=input.read(buffer))!=-1){
                            if(bytes.size()+n>MAX_BYTES)throw new IllegalArgumentException("Too large");
                            bytes.write(buffer,0,n);
                        }
                    }
                    String raw=new String(bytes.toByteArray(),StandardCharsets.UTF_8);
                    Snapshot next=parse(raw);
                    Snapshot previous=current;
                    // A config file can be rolled BACK by editing/reverting its GitHub commit.
                    if(!raw.equals(previous.canonical)){
                        app.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit()
                           .putString(CACHE,raw).apply();
                        current=next;
                        if(onChanged!=null)MAIN.post(onChanged);
                    }
                }finally{c.disconnect();}
            }catch(Exception ignored){
                // Offline, malformed or unavailable source: keep last validated config.
            }finally{FETCHING.set(false);}
        });
    }

    private static Snapshot parse(String raw)throws Exception{
        JSONObject o=new JSONObject(raw);
        if(o.optInt("schema",-1)!=1)throw new IllegalArgumentException("schema");
        int revision=o.optInt("revision",-1);
        if(revision<0||revision>1_000_000)throw new IllegalArgumentException("revision");
        boolean enabled=o.optBoolean("enabled",false);
        JSONObject news=o.optJSONObject("news");
        int poll=bounded(news==null?60:news.optInt("poll_seconds",60),60,900,60);
        int rotate=bounded(news==null?11:news.optInt("knowledge_rotate_seconds",11),7,120,11);
        ArrayList<GyanKnowledge.Entry> lessons=new ArrayList<>();
        JSONArray entries=o.optJSONArray("knowledge");
        if(entries!=null){
            if(entries.length()>50)throw new IllegalArgumentException("too many lessons");
            for(int i=0;i<entries.length();i++){
                JSONObject e=entries.optJSONObject(i);
                if(e==null)throw new IllegalArgumentException("lesson");
                String category=safe(e.optString("category"),24);
                if(!category.matches("gita|flood|general|science|life|digital|books"))
                    throw new IllegalArgumentException("unsupported category");
                String neT=required(e,"title_ne",120),enT=required(e,"title_en",120);
                String ne=required(e,"body_ne",1200),en=required(e,"body_en",1200);
                String source=required(e,"source",160);
                lessons.add(new GyanKnowledge.Entry(category,neT,enT,ne,en,source));
            }
        }
        ArrayList<FAQ> faqs=new ArrayList<>();
        JSONArray rows=o.optJSONArray("sathi_faq");
        if(rows!=null){
            if(rows.length()>30)throw new IllegalArgumentException("too many FAQ");
            for(int i=0;i<rows.length();i++){
                JSONObject e=rows.optJSONObject(i);
                if(e==null)throw new IllegalArgumentException("faq");
                String ne=required(e,"answer_ne",1200),en=required(e,"answer_en",1200);
                JSONArray patterns=e.optJSONArray("triggers");
                if(patterns==null||patterns.length()==0||patterns.length()>10)
                    throw new IllegalArgumentException("triggers");
                List<String> triggers=new ArrayList<>();
                for(int j=0;j<patterns.length();j++){
                    String t=safe(patterns.optString(j),80).toLowerCase(Locale.ROOT);
                    if(t.length()<3)throw new IllegalArgumentException("short trigger");
                    triggers.add(t);
                }
                faqs.add(new FAQ(triggers,ne,en));
            }
        }
        return enabled?new Snapshot(revision,poll,rotate,true,lessons,faqs,raw)
                      :new Snapshot(revision,60,11,false,Collections.emptyList(),Collections.emptyList(),raw);
    }
    private static int bounded(int x,int a,int b,int fallback){return x<a||x>b?fallback:x;}
    private static String required(JSONObject o,String key,int max){
        String s=safe(o.optString(key,""),max);
        if(s.length()<4)throw new IllegalArgumentException("Missing "+key);
        return s;
    }
    private static String safe(String s,int max){
        if(s==null||s.length()>max)throw new IllegalArgumentException("length");
        // Only plain text. Prevent HTML/JS injection if ever reused by the web UI.
        if(s.contains("<script")||s.contains("javascript:"))throw new IllegalArgumentException("code");
        return s.trim();
    }
}
