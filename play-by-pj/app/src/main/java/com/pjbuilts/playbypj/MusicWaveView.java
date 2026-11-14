package com.pjbuilts.playbypj;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Shader;
import android.view.View;

/** Decorative, low-overhead animation for audio-only playback. No microphone input. */
final class MusicWaveView extends View {
    private boolean active;
    private final Paint brush=new Paint(Paint.ANTI_ALIAS_FLAG);
    private long started=android.os.SystemClock.uptimeMillis();
    MusicWaveView(Context context){super(context);setLayerType(View.LAYER_TYPE_SOFTWARE,null);}
    void setActive(boolean enabled){active=enabled;setVisibility(enabled?VISIBLE:GONE);invalidate();}
    @Override protected void onDraw(Canvas c){
        super.onDraw(c);
        int w=getWidth(),h=getHeight();
        if(w<=0||h<=0)return;
        c.drawColor(Color.rgb(15,23,37));
        brush.setShader(new LinearGradient(0,0,w,h,
            new int[]{0xffddac61,0xffffe4a5,0xff43c3b7},null,Shader.TileMode.CLAMP));
        float centerY=h*.53f,step=w/38f;
        double t=(android.os.SystemClock.uptimeMillis()-started)/670.0;
        for(int i=0;i<38;i++){
            double falloff=Math.pow(Math.sin(Math.PI*(i+1)/39),0.6);
            float height=(float)((.08+.22*(1+Math.sin(i*.74+t*2)))*h*falloff);
            float x=(i+.5f)*step;
            c.drawRoundRect(x-step*.26f,centerY-height,x+step*.26f,centerY+height,
                step*.2f,step*.2f,brush);
        }
        brush.setShader(null);
        if(active&&getVisibility()==VISIBLE)postInvalidateDelayed(40);
    }
}
