package io.github.pujan1234hub.floodsafe.app;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PointF;
import android.view.View;
import org.json.JSONArray;
import org.json.JSONObject;

/** Transparent native weather-symbol layer; it does not modify river geometry, glow or flow. */
final class DistrictWeatherOverlay extends View {
 interface Projection {PointF project(double lat,double lon);double zoom();}
 private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
 private final Projection projector;
 private JSONArray districts=new JSONArray();
 private final float den;
 DistrictWeatherOverlay(Context ctx,Projection p){
  super(ctx);projector=p;den=getResources().getDisplayMetrics().density;
  setClickable(false);setWillNotDraw(false);
 }
 void setDistricts(JSONArray weather){districts=weather==null?new JSONArray():weather;invalidate();}
 @Override protected void onDraw(Canvas c){
  super.onDraw(c);
  if(projector==null||districts.length()==0)return;
  final long tick=System.currentTimeMillis();float w=getWidth(),h=getHeight();
  if(w<=0||h<=0)return;
  double zoom=projector.zoom();
  // Collision avoidance keeps full Nepal view legible, but zooming reveals individual districts.
  final float radius=(zoom<6?37:zoom<8?31:24)*den;
  java.util.ArrayList<PointF> used=new java.util.ArrayList<>();
  paint.setTextAlign(Paint.Align.CENTER);paint.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
  for(int i=0;i<districts.length();i++){
   JSONObject d=districts.optJSONObject(i);if(d==null)continue;
   int code=d.optInt("code",-1);if(code<0)continue;
   PointF point=projector.project(d.optDouble("lat"),d.optDouble("lon"));if(point==null)continue;
   float x=point.x,y=point.y;
   if(x<8*den||x>w-8*den||y<20*den||y>h-8*den)continue;
   boolean crowded=false;
   for(PointF p:used)if(Math.abs(p.x-x)<radius&&Math.abs(p.y-y)<radius){crowded=true;break;}
   if(crowded)continue;
   used.add(new PointF(x,y));
   float floatY=(float)Math.sin(tick/1100.0+i*1.3)*1.5f*den;
   paint.setStyle(Paint.Style.FILL);paint.setColor(Color.argb(132,243,252,255));
   c.drawCircle(x,y-7*den+floatY,12*den,paint);
   String icon=DistrictWeatherStore.icon(code);
   paint.setTextSize(17*den);paint.setColor(Color.WHITE);
   c.drawText(icon,x,y+floatY,paint);
   if(code>=51&&code<=67||code>=80&&code<=82||code>=95){
    paint.setColor(Color.argb(205,97,209,251));paint.setStrokeWidth(1.2f*den);
    float shift=(tick%2100)/2100f*8*den;
    for(int k=-1;k<=1;k++)c.drawLine(x+k*4*den,y+7*den+shift,x+k*4*den-2*den,y+11*den+shift,paint);
   }
  }
  if(getWindowToken()!=null)postInvalidateDelayed(650L);
 }
}
