package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.SystemClock;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

/**
 * PJBUILTS approved cream + gold launch intro.
 * Intro-only replacement: it hands off to the same NativeFullActivity as the approved build.
 */
public final class PJBuiltsSplashActivity extends Activity {
    private static final int CREAM_TOP = Color.rgb(255, 251, 243);
    private static final int CREAM_BOTTOM = Color.rgb(246, 236, 219);
    private static final int GRAPHITE = Color.rgb(35, 34, 32);
    private static final int GRAPHITE_SOFT = Color.rgb(82, 76, 67);
    private static final int GOLD = Color.rgb(184, 138, 68);
    private static final int GOLD_SOFT = Color.rgb(220, 193, 146);

    private boolean launched;
    private boolean resumed;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable launchTask = this::openApp;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        Window window = getWindow();
        window.setStatusBarColor(CREAM_TOP);
        window.setNavigationBarColor(CREAM_TOP);
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        window.getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);

        if (getActionBar() != null) getActionBar().hide();

        IntroView intro = new IntroView();
        setContentView(intro);
    }

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        if (!launched) {
            handler.removeCallbacks(launchTask);
            handler.postDelayed(launchTask, 3180L);
        }
    }

    @Override
    protected void onPause() {
        resumed = false;
        handler.removeCallbacks(launchTask);
        super.onPause();
    }

    private void openApp() {
        if (launched || !resumed || isFinishing() || isDestroyed()) return;
        launched = true;
        handler.removeCallbacks(launchTask);

        Intent source = getIntent();
        Intent app = new Intent(this, NativeFullActivity.class);
        app.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        if (source != null) {
            app.setData(source.getData());
            if (source.getExtras() != null) app.putExtras(source.getExtras());
        }

        startActivity(app);
        finish();
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
    }

    @Override
    public void onBackPressed() {
        // Keep this short launch animation uninterrupted.
    }

    @Override
    protected void onDestroy() {
        resumed = false;
        handler.removeCallbacks(launchTask);
        super.onDestroy();
    }

    private final class IntroView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Paint bgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final long startedAt = SystemClock.uptimeMillis();
        private final float density = getResources().getDisplayMetrics().density;

        IntroView() {
            super(PJBuiltsSplashActivity.this);
            setLayerType(View.LAYER_TYPE_HARDWARE, null);
        }

        private float clamp(float v) {
            return Math.max(0f, Math.min(1f, v));
        }

        private float easeOut(float v) {
            v = clamp(v);
            float x = 1f - v;
            return 1f - x * x * x;
        }

        private float smooth(float v) {
            v = clamp(v);
            return v * v * (3f - 2f * v);
        }

        private int alpha(float v) {
            return (int) (255f * clamp(v));
        }

        private void drawBackground(Canvas canvas) {
            bgPaint.setShader(new LinearGradient(
                    0f, 0f, 0f, getHeight(),
                    CREAM_TOP, CREAM_BOTTOM, Shader.TileMode.CLAMP));
            canvas.drawRect(0f, 0f, getWidth(), getHeight(), bgPaint);
            bgPaint.setShader(null);
        }

        private void drawSweeps(Canvas canvas, float t) {
            float sweep = smooth(t / 0.95f);

            float x1 = -getWidth() * 0.42f + sweep * getWidth() * 1.85f;
            paint.setShader(null);
            paint.setColor(Color.argb(110, 220, 193, 146));
            canvas.drawRoundRect(
                    x1, getHeight() * 0.20f,
                    x1 + getWidth() * 0.36f, getHeight() * 0.204f,
                    12f * density, 12f * density, paint);

            float x2 = getWidth() * 1.20f - sweep * getWidth() * 1.92f;
            paint.setColor(Color.argb(82, 184, 138, 68));
            canvas.drawRoundRect(
                    x2, getHeight() * 0.79f,
                    x2 + getWidth() * 0.42f, getHeight() * 0.795f,
                    12f * density, 12f * density, paint);
        }

        private void shinyText(
                Canvas canvas,
                String text,
                float centerX,
                float y,
                float textSize,
                float shineProgress,
                float opacity) {

            opacity = clamp(opacity);
            if (opacity <= 0f) return;

            paint.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
            paint.setTextAlign(Paint.Align.CENTER);
            paint.setTextSize(textSize);
            paint.setStyle(Paint.Style.FILL);
            paint.setShader(null);
            paint.clearShadowLayer();
            paint.setColor(Color.argb(alpha(opacity), 35, 34, 32));
            canvas.drawText(text, centerX, y, paint);

            float width = paint.measureText(text);
            float left = centerX - width / 2f;
            float shine = left - width * 0.25f + clamp(shineProgress) * width * 1.50f;
            float band = Math.max(width * 0.12f, 24f * density);

            int transparentGold = Color.argb(0, 220, 193, 146);
            int brightGold = Color.argb(alpha(opacity * 0.98f), 225, 185, 105);

            paint.setShader(new LinearGradient(
                    shine - band, 0f, shine + band, 0f,
                    new int[]{transparentGold, brightGold, transparentGold},
                    new float[]{0f, 0.5f, 1f},
                    Shader.TileMode.CLAMP));

            paint.setShadowLayer(
                    10f * density,
                    0f,
                    0f,
                    Color.argb(alpha(opacity * 0.38f), 220, 176, 92));

            canvas.drawText(text, centerX, y, paint);
            paint.setShader(null);
            paint.clearShadowLayer();
        }

        private void drawPujan(Canvas canvas, float t) {
            float in = easeOut(t / 0.46f);
            float out = t > 1.12f ? 1f - smooth((t - 1.12f) / 0.36f) : 1f;
            float opacity = in * out;
            float scale = 0.87f + 0.13f * in;

            float cx = getWidth() / 2f;
            float cy = getHeight() / 2f;
            float size = getWidth() * 0.135f;

            canvas.save();
            canvas.scale(scale, scale, cx, cy);

            shinyText(
                    canvas,
                    "PUJAN",
                    cx,
                    cy + size * 0.30f,
                    size,
                    smooth((t - 0.10f) / 0.58f),
                    opacity);

            paint.setShader(null);
            paint.setColor(Color.argb(alpha(opacity * 0.90f), 184, 138, 68));
            paint.setStrokeWidth(Math.max(3f * density, getWidth() * 0.006f));
            paint.setStrokeCap(Paint.Cap.ROUND);

            float half = getWidth() * 0.15f * easeOut(t / 0.62f);
            canvas.drawLine(
                    cx - half,
                    cy + size * 0.65f,
                    cx + half,
                    cy + size * 0.65f,
                    paint);

            canvas.restore();
        }

        private void drawPjBuilts(Canvas canvas, float t) {
            float local = t - 1.18f;
            if (local < 0f) return;

            float in = easeOut(local / 0.55f);
            float out = t > 2.88f ? 1f - smooth((t - 2.88f) / 0.28f) : 1f;
            float opacity = in * out;

            float cx = getWidth() / 2f;
            float baseY = getHeight() / 2f - getWidth() * 0.035f;

            shinyText(
                    canvas,
                    "PJ",
                    cx,
                    baseY,
                    getWidth() * 0.205f,
                    smooth((local - 0.05f) / 0.58f),
                    opacity);

            shinyText(
                    canvas,
                    "BUILTS",
                    cx,
                    baseY + getWidth() * 0.125f,
                    getWidth() * 0.072f,
                    smooth((local - 0.20f) / 0.55f),
                    opacity);

            paint.setShader(null);
            paint.clearShadowLayer();
            paint.setColor(Color.argb(alpha(opacity * 0.92f), 184, 138, 68));
            paint.setStrokeWidth(Math.max(3f * density, getWidth() * 0.005f));
            paint.setStrokeCap(Paint.Cap.ROUND);

            float underline = getWidth() * 0.16f * easeOut(local / 0.65f);
            float lineY = baseY + getWidth() * 0.155f;
            canvas.drawLine(cx - underline, lineY, cx + underline, lineY, paint);

            float tagOpacity = opacity * easeOut((local - 0.32f) / 0.42f);
            paint.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
            paint.setTextAlign(Paint.Align.CENTER);
            paint.setTextSize(getWidth() * 0.030f);
            paint.setColor(Color.argb(alpha(tagOpacity), 82, 76, 67));

            canvas.drawText(
                    "IDEA  •  BUILD  •  INNOVATE",
                    cx,
                    baseY + getWidth() * 0.215f,
                    paint);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);

            float t = (SystemClock.uptimeMillis() - startedAt) / 1000f;

            drawBackground(canvas);
            drawSweeps(canvas, t);
            drawPujan(canvas, t);
            drawPjBuilts(canvas, t);

            if (t < 3.14f) postInvalidateOnAnimation();
        }
    }
}
