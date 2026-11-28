package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Display-only historical station metadata. Never supplies a risk or alert calculation. */
final class RiverThresholdCatalogue {
    private static RiverThresholdCatalogue cached;
    private final JSONArray rows;
    private RiverThresholdCatalogue(JSONArray rows){this.rows=rows;}
    static synchronized RiverThresholdCatalogue load(Context context){
        if(cached!=null)return cached;
        JSONArray rows=new JSONArray();
        try(InputStream in=context.getAssets().open("data/floodsafe-core.json");
            ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[8192]; int n;
            while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
            JSONArray source=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8)).optJSONArray("river_stations");
            if(source!=null)rows=source;
        }catch(Exception ignored){}
        return cached=new RiverThresholdCatalogue(rows);
    }
    static boolean positive(double n){return Double.isFinite(n)&&n>0;}
    static String key(String s){return s==null?"":s.trim().toLowerCase(Locale.ROOT).replaceAll("\\s+"," ");}
    static boolean sameGauge(String a,String b,double lat,double lon,double x,double y){
        return !key(a).isEmpty()&&key(a).equals(key(b))&&Double.isFinite(lat)&&Double.isFinite(lon)&&Double.isFinite(x)&&Double.isFinite(y)&&Math.abs(lat-x)<=0.0001&&Math.abs(lon-y)<=0.0001;
    }
    static final class Match{
        final double warning,danger;
        Match(double warning,double danger){this.warning=warning;this.danger=danger;}
    }
    static Match merge(double w,double d,double cw,double cd){
        if(RiverThresholdPolicy.conflicts(w,d)||RiverThresholdPolicy.conflicts(cw,cd))return null;
        if(positive(w)&&positive(cw)&&Math.abs(w-cw)>0.00001)return null;
        if(positive(d)&&positive(cd)&&Math.abs(d-cd)>0.00001)return null;
        // Do not construct a pair using independent records unless their shared limit agrees.
        if(positive(w)&&!positive(d)&&positive(cd)&&!positive(cw))return null;
        if(positive(d)&&!positive(w)&&positive(cw)&&!positive(cd))return null;
        double a=positive(w)?w:positive(cw)?cw:Double.NaN;
        double b=positive(d)?d:positive(cd)?cd:Double.NaN;
        if(RiverThresholdPolicy.conflicts(a,b))return null;
        if((!positive(w)&&positive(a))||(!positive(d)&&positive(b)))return new Match(a,b);
        return null;
    }
    Match find(String name,double lat,double lon,double w,double d){
        JSONObject found=null;
        for(int i=0;i<rows.length();i++){
            JSONObject row=rows.optJSONObject(i);if(row==null)continue;
            JSONObject point=row.optJSONObject("point");
            JSONArray coord=point==null?null:point.optJSONArray("coordinates");
            if(coord==null||coord.length()<2)continue;
            if(!sameGauge(name,row.optString("title"),lat,lon,coord.optDouble(1,Double.NaN),coord.optDouble(0,Double.NaN)))continue;
            if(found!=null)return null;
            found=row;
        }
        return found==null?null:merge(w,d,found.optDouble("warningLevel",Double.NaN),found.optDouble("dangerLevel",Double.NaN));
    }
}
