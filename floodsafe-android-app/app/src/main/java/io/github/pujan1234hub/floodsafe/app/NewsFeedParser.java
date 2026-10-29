package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.HashSet;
import java.util.Set;

/** Normalize existing trusted three-source news API responses without fabricating headlines.
 * An empty source feed and an unavailable API are different states.
 */
final class NewsFeedParser {
    private NewsFeedParser(){}
    static final long RECENT_MS=24L*60L*60L*1000L;
    static final class Item {
        final String title,source,url;
        final long at;
        Item(String t,String s,String u,long a){title=t;source=s;url=u;at=a;}
    }
    static List<Item> parse(JSONObject response,long now){
        ArrayList<Item> out=new ArrayList<>();
        if(response==null)return out;
        JSONArray items=findArray(response);
        if(items==null)return out;
        Set<String> dedup=new HashSet<>();
        for(int i=0;i<items.length()&&out.size()<15;i++){
            JSONObject row=items.optJSONObject(i);
            if(row==null)continue;
            String title=value(row,"title","headline","heading","text","name");
            String url=value(row,"url","link","articleUrl","article_url","permalink");
            String source=value(row,"source","publisher","sourceName","source_name","publication","outlet");
            if(source.isEmpty()){
                JSONObject publisher=row.optJSONObject("publisher");
                if(publisher!=null)source=value(publisher,"name","title");
            }
            source=normalizeSource(source);
            if(source.isEmpty()||title.isEmpty()||!url.startsWith("https://"))continue;
            long timestamp=parseTime(value(row,"published_at","publishedAt","published","published_on","publishedOn","pubDate","created_at","createdAt","date","timestamp","time"));
            if(timestamp>now+5L*60L*1000L)continue;
            if(timestamp>0 && now-timestamp>RECENT_MS)continue;
            // Missing timestamp can be shown only as undated, never 'live'.
            String key=url.toLowerCase(Locale.ROOT).trim();
            if(!dedup.add(key))continue;
            out.add(new Item(title,source,url,timestamp));
        }
        out.sort((a,b)->Long.compare(b.at,a.at));
        return out;
    }
    private static JSONArray findArray(JSONObject o){
        for(String key:new String[]{"items","results","news","articles","stories","posts"}){
            JSONArray a=o.optJSONArray(key);if(a!=null)return a;
        }
        JSONObject data=o.optJSONObject("data");
        if(data!=null)return findArray(data);
        return null;
    }
    private static String normalizeSource(String raw){
        String s=(raw==null?"":raw).trim().toLowerCase(Locale.ROOT);
        if(s.contains("routine of nepal")||s.contains("ronb"))return "RONB Post";
        if(s.contains("radio nepal")||s.contains("रेडियो नेपाल"))return "Radio Nepal";
        if(s.contains("news24")||s.contains("news 24")||s.contains("न्यूज२४"))return "News24 Nepal";
        return "";
    }
    private static String value(JSONObject o,String...names){
        if(o==null)return "";
        for(String key:names){Object item=o.opt(key);if(item==null||item==JSONObject.NULL)continue;
            String s=String.valueOf(item).trim();if(!s.isEmpty()&&!"null".equalsIgnoreCase(s))return s;}
        return "";
    }
    private static long parseTime(String t){
        if(t==null||t.isEmpty())return 0L;
        try{long n=Long.parseLong(t);return n<10_000_000_000L?n*1000L:n;}catch(Exception ignored){}
        try{return Instant.parse(t).toEpochMilli();}catch(Exception ignored){}
        try{return OffsetDateTime.parse(t).toInstant().toEpochMilli();}catch(Exception ignored){}
        return 0L;
    }
}
