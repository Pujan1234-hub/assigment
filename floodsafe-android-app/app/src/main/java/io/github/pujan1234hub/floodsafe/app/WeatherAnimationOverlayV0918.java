package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

/**
 * Restores the native weather animation that previously sat above the existing map.
 * This view is transparent and touch-through. It does not create or modify river,
 * station, BIPAD/DHM, MapLibre source, layer, geometry, marker or status objects.
 */
public final class WeatherAnimationOverlayV0918 extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Handler main = new Handler(Looper.getMainLooper());
    private int weatherCode = -1;
    private int cloudCover = 0;
    private double precipitation = 0d;
    private float phase = 0f;
    private boolean attached = false;

    private final Runnable animate = new Runnable() {
        @Override public void run() {
            if (!attached) return;
            phase = (phase + 1.35f) % 10000f;
            invalidate();
            if (needsMotion()) main.postDelayed(this, 85L);
        }
    };

    public WeatherAnimationOverlayV0918(Context context) {
        super(context);
        setClickable(false);
        setFocusable(false);
        setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        setBackgroundColor(Color.TRANSPARENT);
    }

    public void updateWeather(int code, double rainMm, int clouds) {
        weatherCode = code;
        precipitation = Math.max(0d, rainMm);
        cloudCover = Math.max(0, Math.min(100, clouds));
        setVisibility(needsVisual() ? VISIBLE : INVISIBLE);
        main.removeCallbacks(animate);
        if (attached && needsMotion()) main.post(animate);
        invalidate();
    }

    private boolean isThunder() {
        return weatherCode == 95 || weatherCode == 96 || weatherCode == 99;
    }

    private int rainStrength() {
        if (isThunder() || weatherCode == 65 || weatherCode == 67 || weatherCode == 82 || precipitation >= 2.0d) return 2;
        if ((weatherCode >= 51 && weatherCode <= 67) || (weatherCode >= 80 && weatherCode <= 82) || precipitation >= 0.10d) return 1;
        return 0;
    }

    private boolean needsVisual() {
        return weatherCode >= 2 || precipitation >= 0.10d || cloudCover >= 35;
    }

    private boolean needsMotion() {
        return needsVisual();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        attached = true;
        if (needsMotion()) main.post(animate);
    }

    @Override protected void onDetachedFromWindow() {
        attached = false;
        main.removeCallbacksAndMessages(null);
        super.onDetachedFromWindow();
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (!needsVisual()) return;
        final float w = getWidth();
        final float h = getHeight();
        if (w <= 0f || h <= 0f) return;

        final int rain = rainStrength();
        int alpha = 35 + Math.max(cloudCover, weatherCode == 3 ? 82 : 45);
        alpha = Math.max(45, Math.min(130, alpha));
        if (rain == 2) alpha = Math.max(alpha, 115);

        paint.setStyle(Paint.Style.FILL);
        paint.setColor(Color.argb(alpha, 229, 239, 244));
        for (int i = 0; i < 5; i++) {
            float drift = phase * (0.10f + i * 0.014f);
            float baseX = ((i * 0.24f * w) + drift) % (w + w * .45f) - w * .22f;
            float y = h * (0.08f + (i % 3) * 0.17f);
            float cw = w * (0.25f + (i % 2) * .05f);
            float ch = Math.max(26f, h * .09f);
            canvas.drawOval(new RectF(baseX, y, baseX + cw, y + ch), paint);
            canvas.drawCircle(baseX + cw * .27f, y + ch * .16f, ch * .53f, paint);
            canvas.drawCircle(baseX + cw * .55f, y + ch * .08f, ch * .66f, paint);
        }

        if (rain > 0) {
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(rain == 2 ? 3.1f : 2.0f);
            paint.setColor(Color.argb(rain == 2 ? 160 : 112, 137, 214, 255));
            int count = rain == 2 ? 52 : 28;
            float speed = (phase * (rain == 2 ? 6.8f : 4.1f)) % Math.max(1f, h);
            for (int i = 0; i < count; i++) {
                float x = ((i * 71f + phase * 1.8f) % (w + 34f)) - 17f;
                float y = ((i * 43f + speed) % (h + 48f)) - 44f;
                canvas.drawLine(x, y, x - (rain == 2 ? 9f : 6f), y + (rain == 2 ? 30f : 21f), paint);
            }
            paint.setStyle(Paint.Style.FILL);
        }

        if (isThunder()) {
            float cycle = phase % 120f;
            if (cycle > 90f && cycle < 98f) {
                paint.setColor(Color.argb(52, 255, 255, 255));
                canvas.drawRect(0f, 0f, w, h, paint);
            }
            if (cycle > 91f && cycle < 96f) {
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(5f);
                paint.setStrokeJoin(Paint.Join.MITER);
                paint.setColor(Color.argb(220, 255, 241, 150));
                float x = w * 0.62f;
                float y = h * 0.12f;
                Path bolt = new Path();
                bolt.moveTo(x, y);
                bolt.lineTo(x - w * .055f, y + h * .16f);
                bolt.lineTo(x + w * .008f, y + h * .15f);
                bolt.lineTo(x - w * .045f, y + h * .31f);
                canvas.drawPath(bolt, paint);
                paint.setStyle(Paint.Style.FILL);
            }
        }
    }
}
