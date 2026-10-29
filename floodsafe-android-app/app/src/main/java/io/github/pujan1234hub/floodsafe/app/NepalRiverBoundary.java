package io.github.pujan1234hub.floodsafe.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Clips river geometry to Nepal's actual 77 district polygons, not a rectangle.
 * Out-of-Nepal stretches are split rather than reconnecting through India/China.
 * The source is the same bundled district GeoJSON already displayed on the map.
 */
final class NepalRiverBoundary {
    private final List<Polygon> polygons = new ArrayList<>();
    private static final class Ring {
        final double[] longitude, latitude;
        final double minX, maxX, minY, maxY;
        Ring(JSONArray coords) {
            int n=coords.length();
            longitude=new double[n];latitude=new double[n];
            double left=Double.POSITIVE_INFINITY,right=Double.NEGATIVE_INFINITY;
            double bottom=Double.POSITIVE_INFINITY,top=Double.NEGATIVE_INFINITY;
            for(int i=0;i<n;i++) {
                JSONArray xy=coords.optJSONArray(i);
                double x=xy==null?Double.NaN:xy.optDouble(0,Double.NaN);
                double y=xy==null?Double.NaN:xy.optDouble(1,Double.NaN);
                longitude[i]=x;latitude[i]=y;
                if(Double.isFinite(x)&&Double.isFinite(y)) {
                    left=Math.min(left,x);right=Math.max(right,x);
                    bottom=Math.min(bottom,y);top=Math.max(top,y);
                }
            }
            minX=left;maxX=right;minY=bottom;maxY=top;
        }
        boolean contains(double x,double y) {
            if(x<minX||x>maxX||y<minY||y>maxY)return false;
            boolean hit=false;
            for(int i=0,j=longitude.length-1;i<longitude.length;j=i++){
                double ax=longitude[i],ay=latitude[i],bx=longitude[j],by=latitude[j];
                if(!Double.isFinite(ax)||!Double.isFinite(bx)||!Double.isFinite(ay)||!Double.isFinite(by))continue;
                if((ay>y)!=(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)hit=!hit;
            }
            return hit;
        }
    }
    private static final class Polygon {
        final Ring shell;
        final List<Ring> holes=new ArrayList<>();
        Polygon(JSONArray rings) {
            shell=new Ring(rings.optJSONArray(0));
            for(int i=1;i<rings.length();i++){
                JSONArray xy=rings.optJSONArray(i);
                if(xy!=null&&xy.length()>2)holes.add(new Ring(xy));
            }
        }
        boolean contains(double lon,double lat) {
            if(!shell.contains(lon,lat))return false;
            for(Ring hole:holes)if(hole.contains(lon,lat))return false;
            return true;
        }
    }
    NepalRiverBoundary(String geoJson) throws Exception {
        JSONObject input=new JSONObject(geoJson);
        JSONArray features=input.optJSONArray("features");
        if(features==null||features.length()<50)throw new IllegalStateException("Nepal polygons missing");
        for(int i=0;i<features.length();i++){
            JSONObject f=features.optJSONObject(i);
            JSONObject geometry=f==null?null:f.optJSONObject("geometry");
            if(geometry==null)continue;
            String type=geometry.optString("type");
            JSONArray data=geometry.optJSONArray("coordinates");
            if(data==null)continue;
            if("Polygon".equals(type))add(data);
            if("MultiPolygon".equals(type))for(int p=0;p<data.length();p++)add(data.optJSONArray(p));
        }
        if(polygons.size()<50)throw new IllegalStateException("Insufficient Nepal boundary polygons");
    }
    private void add(JSONArray rings){
        if(rings==null||rings.length()==0)return;
        JSONArray shell=rings.optJSONArray(0);
        if(shell!=null&&shell.length()>=4)polygons.add(new Polygon(rings));
    }
    boolean contains(double lon,double lat){
        if(!Double.isFinite(lon)||!Double.isFinite(lat)||lat<26||lat>31||lon<79||lon>89)return false;
        for(Polygon p:polygons)if(p.contains(lon,lat))return true;
        return false;
    }
    static double[] between(double[] a,double[] b,double t){
        return new double[]{a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t};
    }
    private double[] border(double[] a,double[] b,double from,double to,boolean fromInside){
        // Bisection finds a point on the country boundary to sub-metre precision.
        for(int i=0;i<27;i++){
            double mid=(from+to)/2;
            boolean inside=containsBetween(a,b,mid);
            if(inside==fromInside)from=mid;else to=mid;
        }
        return between(a,b,(from+to)/2);
    }
    private boolean containsBetween(double[] a,double[] b,double t){
        double[] p=between(a,b,t);return contains(p[0],p[1]);
    }
    private static void end(List<List<double[]>> parts,List<double[]> active) {
        if(active.size()>1)parts.add(active);
    }
    /**
     * Return only connected in-country polylines; points outside are discarded.
     * Sampling at <= 200m intervals resolves the coast/border between sparse
     * source vertices; border intersection is refined by binary search.
     */
    List<List<double[]>> clip(JSONArray original){
        List<List<double[]>> pieces=new ArrayList<>();
        if(original==null||original.length()<2)return pieces;
        List<double[]> active=new ArrayList<>();
        JSONArray first=original.optJSONArray(0);
        double[] previous=pair(first);
        if(previous==null)return pieces;
        boolean prevInside=contains(previous[0],previous[1]);
        if(prevInside)active.add(previous);
        for(int k=1;k<original.length();k++){
            double[] next=pair(original.optJSONArray(k));
            if(next==null){end(pieces,active);active=new ArrayList<>();prevInside=false;previous=null;continue;}
            if(previous==null){previous=next;prevInside=contains(next[0],next[1]);if(prevInside)active.add(next);continue;}
            final double xKm=(next[0]-previous[0])*111.1*Math.cos(previous[1]*Math.PI/180);
            final double yKm=(next[1]-previous[1])*111.1;
            final double km=Math.hypot(xKm,yKm);
            // Conservative interpolation ensures no river segment bridges outside Nepal.
            int steps=Math.max(1,Math.min(500,(int)Math.ceil(km/0.20)));
            for(int j=1;j<=steps;j++){
                double oldT=(j-1.0)/steps,curT=(double)j/steps;
                double[] position=between(previous,next,curT);
                boolean inside=contains(position[0],position[1]);
                if(prevInside&&inside)active.add(position);
                else if(prevInside) {
                    active.add(border(previous,next,oldT,curT,true));
                    end(pieces,active);active=new ArrayList<>();
                }else if(inside){
                    active=new ArrayList<>();
                    active.add(border(previous,next,oldT,curT,false));active.add(position);
                }
                prevInside=inside;
            }
            previous=next;
        }
        end(pieces,active);
        return pieces;
    }
    private static double[] pair(JSONArray a){
        if(a==null||a.length()<2)return null;
        double x=a.optDouble(0,Double.NaN),y=a.optDouble(1,Double.NaN);
        return Double.isFinite(x)&&Double.isFinite(y)?new double[]{x,y}:null;
    }
}