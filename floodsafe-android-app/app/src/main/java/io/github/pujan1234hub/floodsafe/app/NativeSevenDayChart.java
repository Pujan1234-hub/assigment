package io.github.pujan1234hub.floodsafe.app;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.View;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Locale;
/** Compact native seven-day precipitation/GloFAS forecast inside original blue weather box. */
final class NativeSevenDayChart extends View {
 private final Paint pen=new Paint(Paint.ANTI_ALIAS_FLAG);
 private final double[] rain=new double[7],flow=new double[7],prob=new double[7];
 private final String[] dates=new String[7];
 private boolean english,showFlow=false,hasRain=false,hasFlow=false;
 private String source="";
 NativeSevenDayChart(Context ctx){super(ctx);for(int i=0;i<7;i++){rain[i]=Double.NaN;flow[i]=Double.NaN;prob[i]=Double.NaN;dates[i]="—";}
   setOnClickListener(v->{showFlow=!showFlow;invalidate();});
   setContentDescription("Seven day rain and river flow forecast. Tap to change model.");
 }
 void useLanguage(boolean en){english=en;invalidate();}
 void setForecast(JSONObject j) {
   for(int i=0;i<7;i++){rain[i]=Double.NaN;flow[i]=Double.NaN;prob[i]=Double.NaN;dates[i]="—";}
   JSONArray rr=j.optJSONArray("rainfall"),ff=j.optJSONArray("flow");
   hasRain=rr!=null&&rr.length()>0;hasFlow=ff!=null&&ff.length()>0;
   if(rr!=null)for(int i=0;i<Math.min(7,rr.length());i++){
    JSONObject x=rr.optJSONObject(i);if(x==null)continue;
    rain[i]=x.optDouble("value",Double.NaN);
    prob[i]=x.optDouble("probability",Double.NaN);
    dates[i]=x.optString("date","—");
   }
   if(ff!=null)for(int i=0;i<Math.min(7,ff.length());i++){
    JSONObject x=ff.optJSONObject(i);if(x==null)continue;
    flow[i]=x.optDouble("value",Double.NaN);
    if("—".equals(dates[i]))dates[i]=x.optString("date","—");
   }
   source=j.optJSONObject("sources")==null?"":j.optJSONObject("sources").optString("rainfall","");
   invalidate();
 }
 @Override protected void onDraw(Canvas c){
   super.onDraw(c);
   float den=getResources().getDisplayMetrics().density,w=getWidth(),h=getHeight();
   pen.setColor(Color.argb(60,8,63,104));
   c.drawRoundRect(new RectF(0,0,w,h),12*den,12*den,pen);
   pen.setTypeface(android.graphics.Typeface.create("sans-serif",android.graphics.Typeface.BOLD));
   pen.setTextSize(9*den);pen.setColor(Color.WHITE);
   String title=showFlow?(english?"River flow (m³/s)":"नदी बहाव (m³/s)"):(english?"7-day rain (mm)":"७ दिनको वर्षा (मिमी)");
   c.drawText(title,7*den,13*den,pen);
   boolean available=showFlow?hasFlow:hasRain;
   if(!available){pen.setTextSize(10*den);c.drawText(english?"No model available":"पूर्वानुमान उपलब्ध छैन",7*den,h/2,pen);return;}
   double[] values=showFlow?flow:rain;
   double highest=.01;for(double v:values)if(Double.isFinite(v))highest=Math.max(highest,v);
   float pad=5*den,span=(w-2*pad)/7f;
   float barBottom=h-24*den,maxHeight=Math.max(12*den,h-52*den);
   for(int i=0;i<7;i++){
    double v=values[i];if(!Double.isFinite(v)||v<0)continue;
    float barHeight=(float)Math.max(1*den,maxHeight*v/highest);
    float center=pad+(i+.5f)*span;
    pen.setColor(Color.rgb(143,226,247));
    c.drawRoundRect(new RectF(center-span*.28f,barBottom-barHeight,center+span*.28f,barBottom),3*den,3*den,pen);
    pen.setTextAlign(Paint.Align.CENTER);
    pen.setColor(Color.WHITE);pen.setTextSize(8*den);
    c.drawText(String.format(Locale.US,v>=10?"%.0f":"%.1f",v),center,barBottom-barHeight-3*den,pen);
    String ds=dates[i],label=english?(ds.length()>=10?ds.substring(5):ds):NepalBs.shortDate(ds);
    if(label.length()>6)label=label.substring(0,Math.min(5,label.length()));
    c.drawText(label,center,h-8*den,pen);
   }
   pen.setTextAlign(Paint.Align.LEFT);
 }
}