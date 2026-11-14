package com.pjbuilts.playbypj;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.provider.MediaStore;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Private, local-only media list and durable named playlists. */
final class MusicLibrary {
    static final class Track {
        final String name;
        final Uri uri;
        final long duration;
        Track(String n,Uri u,long d){name=n;uri=u;duration=d;}
    }
    private static final String PREF="pj_play_music_v1",KEY="saved_playlists";
    private MusicLibrary(){}
    static List<Track> scan(Context ctx){
        ArrayList<Track> results=new ArrayList<>();
        Uri content=MediaStore.Audio.Media.EXTERNAL_CONTENT_URI;
        String[] cols={MediaStore.Audio.Media._ID,MediaStore.Audio.Media.DISPLAY_NAME,
            MediaStore.Audio.Media.DURATION};
        try(Cursor c=ctx.getContentResolver().query(content,cols,null,null,null)){
            if(c!=null)while(c.moveToNext()){
                String name=c.getString(1);
                if(name==null||name.trim().isEmpty())continue;
                Uri u=ContentUris.withAppendedId(content,c.getLong(0));
                results.add(new Track(name,u,c.isNull(2)?0:c.getLong(2)));
                if(results.size()>=5000)break;
            }
        }catch(SecurityException ignored){}
        catch(Exception ignored){}
        results.sort(Comparator.comparing(t->t.name.toLowerCase(java.util.Locale.ROOT)));
        return results;
    }
    private static JSONObject saved(Context c){
        String raw=c.getSharedPreferences(PREF,Context.MODE_PRIVATE).getString(KEY,"{}");
        try{return new JSONObject(raw);}catch(Exception e){return new JSONObject();}
    }
    private static void write(Context c,JSONObject data){
        c.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().putString(KEY,data.toString()).apply();
    }
    static List<String> names(Context c){
        JSONObject obj=saved(c);
        ArrayList<String> result=new ArrayList<>();
        java.util.Iterator<String> keys=obj.keys();
        while(keys.hasNext())result.add(keys.next());
        result.sort(String.CASE_INSENSITIVE_ORDER);return result;
    }
    static boolean create(Context c,String name){
        name=name==null?"":name.trim();
        if(name.isEmpty()||name.length()>50)return false;
        JSONObject o=saved(c);
        if(o.has(name))return false;
        try{o.put(name,new JSONArray());write(c,o);return true;}catch(Exception e){return false;}
    }
    static boolean add(Context c,String name,Track t){
        JSONObject o=saved(c),a=new JSONObject();
        JSONArray list=o.optJSONArray(name);
        if(t==null||list==null)return false;
        for(int i=0;i<list.length();i++)
            if(t.uri.toString().equals(list.optJSONObject(i)==null?null:list.optJSONObject(i).optString("uri")))
                return true;
        try{
            a.put("name",t.name);a.put("uri",t.uri.toString());a.put("duration",t.duration);
            list.put(a);o.put(name,list);write(c,o);return true;
        }catch(Exception e){return false;}
    }
    static List<Track> tracks(Context c,String name){
        JSONArray list=saved(c).optJSONArray(name);
        ArrayList<Track> result=new ArrayList<>();
        if(list==null)return result;
        for(int i=0;i<list.length();i++){
            JSONObject t=list.optJSONObject(i);
            if(t==null||t.optString("uri").isEmpty())continue;
            try{result.add(new Track(t.optString("name"),Uri.parse(t.optString("uri")),t.optLong("duration",0)));}
            catch(Exception ignored){}
        }
        return result;
    }
}
