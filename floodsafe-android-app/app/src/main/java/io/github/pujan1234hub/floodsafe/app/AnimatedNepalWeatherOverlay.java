package io.github.pujan1234hub.floodsafe.app;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Color;
import android.view.View;
/** Real native Canvas weather visuals over Nepal river geometry. No WebView. */
final class AnimatedNepalWeatherOverlay extends View {
 private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
 private float cloud=35f,rain=0f; private boolean thunder=false;
 private final float[] offset={.09f,.37f,.61f,.84f,.19f,.48f,.78f};
 private long since=System.currentTimeMillis();
 AnimatedNepalWeatherOverlay(Context c){super(c);setWillNotDraw(false);setClickable(false);}
 void setConditions(double cloudPct,double rainfall,int weatherCode){
  cloud=(float)Math.max(0,Math.min(100,cloudPct));rain=(float)Math.max(0,Math.min(100,rainfall*25));
  thunder=weatherCode>=95; invalidate();
 }
 @Override protected void onDraw(Canvas c){
  super.onDraw(c);
  float w=getWidth(),h=getHeight();if(w<=0||h<=0)return;
  float scale=getResources().getDisplayMetrics().density;
  long now=System.currentTimeMillis();float t=((now-since)%24000L)/24000f;
  // Sun is visible when sky is clear; rays rotate slowly.
  if(cloud<70f){
   float sx=.83f*w,sy=.16f*h,r=Math.max(13f*scale,.035f*w);
   paint.setStrokeWidth(2f*scale);paint.setStyle(Paint.Style.STROKE);
   paint.setColor(Color.argb((int)(130*(1-cloud/100f)),255,205,58));
   for(int j=0;j<12;j++){double a=j*Math.PI/6+t*Math.PI;float x=(float)Math.cos(a),y=(float)Math.sin(a);
    c.drawLine(sx+x*r*1.3f,sy+y*r*1.3f,sx+x*r*1.65f,sy+y*r*1.65f,paint);}
   paint.setStyle(Paint.Style.FILL);paint.setColor(Color.argb((int)(215*(1-cloud/100f)),255,225,94));c.drawCircle(sx,sy,r,paint);
  }
  // Native cloud layers drift across the river map.
  int count=Math.min(7,Math.max(0,(int)Math.ceil(cloud*7/100f)));
  for(int i=0;i<count;i++){
    float x=(((offset[i]+t*(.25f+i*.01f))%1.35f)-.15f)*w;
    float y=(.14f+(i%4)*.2f)*h;
    float r=Math.max(14f*scale,w*(.045f+(i%3)*.009f));
    paint.setStyle(Paint.Style.FILL);
    paint.setColor(Color.argb(90+(int)(cloud*.7f),248,251,255));
    c.drawOval(x-r,y,x+r,y+r*.6f,paint);
    c.drawCircle(x-r*.37f,y,r*.55f,paint);
    c.drawCircle(x+r*.23f,y-r*.12f,r*.65f,paint);
  }
  if(rain>.1f){
    paint.setStrokeWidth(Math.max(1.1f*scale,w*.003f));paint.setColor(Color.argb(130,47,176,231));
    int n=12+(int)(rain*.7f);
    for(int k=0;k<n;k++){
      float x=(float)((k*57.47 + t*900)%w),y=(float)((k*49.91+t*1350)%h);
      c.drawLine(x,y,x-4*scale,y+10*scale,paint);
    }
  }
  if(thunder&&(now%8400)<110){paint.setStyle(Paint.Style.FILL);paint.setColor(Color.argb(52,255,255,255));c.drawRect(0,0,w,h,paint);}
  if(getWindowToken()!=null)postInvalidateDelayed(60L);
 }
}