package com.pjbuilts.playbypj;

import org.videolan.libvlc.MediaPlayer;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

/** Compatible with both ID-string and older numeric LibVLC track APIs. */
final class VlcTrackPicker {
    static final class Option {
        final String id, label;
        Option(String i, String n){id=i;label=n;}
    }
    private VlcTrackPicker(){}
    private static Object invoke(Object target,String method){
        try{return target.getClass().getMethod(method).invoke(target);}catch(Exception ignored){return null;}
    }
    private static String attribute(Object obj,String getter,String field){
        Object x=invoke(obj,getter);
        if(x==null)try{Field f=obj.getClass().getField(field);x=f.get(obj);}catch(Exception ignored){}
        return x==null?"":String.valueOf(x);
    }
    static List<Option> available(MediaPlayer p,boolean subtitles){
        ArrayList<Option> out=new ArrayList<>();
        if(p==null)return out;
        String modern=subtitles?"getAllSpuTracks":"getAllAudioTracks";
        Object tracks=invoke(p,modern);
        if(tracks==null)tracks=invoke(p,subtitles?"getSpuTracks":"getAudioTracks");
        if(tracks==null||!tracks.getClass().isArray())return out;
        for(int i=0;i<Array.getLength(tracks);i++){
            Object t=Array.get(tracks,i);
            if(t==null)continue;
            String id=attribute(t,"getId","id");
            if(id.isEmpty())continue;
            String name=attribute(t,"getName","name"),lang=attribute(t,"getLanguage","language");
            if(name.isEmpty())name=(subtitles?"Subtitle ":"Audio ")+(i+1);
            // Use container-provided track name/language; no invented dubbing tracks.
            if(!lang.isEmpty()&&!name.toLowerCase().contains(lang.toLowerCase()))name+=" · "+lang;
            out.add(new Option(id,name));
        }
        return out;
    }
    static String selected(MediaPlayer p,boolean subtitles){
        if(p==null)return "-1";
        Object t=invoke(p,subtitles?"getSelectedSpuTrack":"getSelectedAudioTrack");
        if(t!=null){
            String id=attribute(t,"getId","id");
            if(!id.isEmpty())return id;
        }
        Object old=invoke(p,subtitles?"getSpuTrack":"getAudioTrack");
        return old==null?"-1":String.valueOf(old);
    }
    static boolean choose(MediaPlayer p,boolean subtitles,String id){
        if(p==null)return false;
        if(subtitles&&"-1".equals(id)){
            // LibVLC 3.7 unselectTrackType(2) = subtitle/SPU track type.
            try{
                p.getClass().getMethod("unselectTrackType",int.class).invoke(p,2);
                return true;
            }catch(Exception ignored){}
        }
        String method=subtitles?"setSpuTrack":"setAudioTrack";
        try{
            Object result=p.getClass().getMethod(method,String.class).invoke(p,id);
            return !(result instanceof Boolean)||((Boolean)result);
        }catch(Exception ignored){}
        try{
            Object result=p.getClass().getMethod(method,int.class).invoke(p,Integer.parseInt(id));
            return !(result instanceof Boolean)||((Boolean)result);
        }catch(Exception ignored){}
        return false;
    }
}
