package io.github.pujan1234hub.floodsafe.app;

import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

/** Native, network-independent PJBUILTS electric launch intro. */
public final class PJBuiltsSplashActivity extends Activity {
    private boolean launched;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(2, 7, 18));
        window.setNavigationBarColor(Color.rgb(2, 7, 18));
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        window.getDecorView().setSystemUiVisibility(0);
        boolean reduceMotion = Build.VERSION.SDK_INT >= 26 && !ValueAnimator.areAnimatorsEnabled();
        setContentView(new ElectricBrandView(reduceMotion ? 260L : 1150L));
    }

    private void openApp() {
        if (launched || isFinishing() || isDestroyed()) return;
        launched = true;
        Intent source = getIntent();
        // Restore the proven full FloodSafe experience while the 1:1 native clone is built.
        // This prevents the temporary native prototype from replacing the real map/features.
        Intent app = new Intent(this, VoiceMainActivity.class);
        if (source != null) {
            app.setAction(source.getAction());
            app.setData(source.getData());
            if (source.getExtras() != null) app.putExtras(source.getExtras());
        }
        startActivity(app);
        finish();
        overridePendingTransition(0, 0);
    }

    private final class ElectricBrandView extends View {
        private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Paint accent = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Paint bolt = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint grid = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path path = new Path();
        private final long durationMs;
        private final float density;
        private long startedAt;

        ElectricBrandView(long durationMs) {
            super(PJBuiltsSplashActivity.this);
            this.durationMs = durationMs;
            this.density = getResources().getDisplayMetrics().density;
            setBackgroundColor(Color.rgb(2, 7, 18));
            setLayerType(View.LAYER_TYPE_SOFTWARE, null);
            Typeface face = Typeface.create("sans-serif", Typeface.BOLD);
            text.setTypeface(face);
            text.setTextAlign(Paint.Align.LEFT);
            accent.setTypeface(face);
            accent.setTextAlign(Paint.Align.CENTER);
            bolt.setStyle(Paint.Style.STROKE);
            bolt.setStrokeCap(Paint.Cap.ROUND);
            grid.setStrokeWidth(dp(.7f));
            grid.setColor(Color.argb(20, 72, 196, 230));
            setContentDescription("PJBUILTS");
        }

        @Override protected void onAttachedToWindow() {
            super.onAttachedToWindow();
            startedAt = SystemClock.uptimeMillis();
            postInvalidateOnAnimation();
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            if (getWidth() <= 0 || getHeight() <= 0) return;
            float t = clamp((SystemClock.uptimeMillis() - startedAt) / (float) durationMs);
            drawBackground(canvas, t);
            drawBrand(canvas, t);
            if (t < 1f) postInvalidateOnAnimation();
            else post(PJBuiltsSplashActivity.this::openApp);
        }

        private void drawBackground(Canvas canvas, float t) {
            float cx = getWidth() * .5f, cy = getHeight() * .47f;
            float max = Math.max(getWidth(), getHeight());
            Paint halo = accent;
            halo.setShader(new android.graphics.RadialGradient(cx, cy, max * .36f,
                    new int[]{Color.argb((int)(56 * pulse(t)), 25, 207, 255), Color.TRANSPARENT},
                    new float[]{0f, 1f}, android.graphics.Shader.TileMode.CLAMP));
            canvas.drawCircle(cx, cy, max * .36f, halo);
            halo.setShader(null);
            float spacing = dp(32f);
            for (float x = cx - dp(145f); x <= cx + dp(145f); x += spacing) canvas.drawLine(x, cy-dp(150f), x, cy+dp(150f), grid);
            for (float y = cy - dp(150f); y <= cy + dp(150f); y += spacing) canvas.drawLine(cx-dp(145f), y, cx+dp(145f), y, grid);
        }

        private void drawBrand(Canvas canvas, float t) {
            float cx = getWidth() * .5f;
            float baseY = getHeight() * .47f;
            float size = Math.min(sp(92f), getWidth() * .22f);
            text.setTextSize(size);
            float pW = text.measureText("P"), jW = text.measureText("J");
            float gap = dp(5f);
            float targetP = cx - (pW + jW + gap) / 2f;
            float targetJ = targetP + pW + gap;

            float enterP = easeOut(clamp(t / .28f));
            float enterJ = easeOut(clamp((t - .08f) / .30f));
            float lock = easeOut(clamp((t - .28f) / .20f));
            float reveal = easeOut(clamp((t - .45f) / .25f));
            float fade = 1f - easeIn(clamp((t - .90f) / .10f));

            float pX = lerp(-pW - dp(28f), targetP, enterP);
            float jX = lerp(getWidth() + dp(28f), targetJ, enterJ);
            float y = baseY;

            drawCurrent(canvas, pX + pW * .5f, jX + jW * .5f, baseY - size * .38f, t, lock, fade);
            drawNeon(canvas, "P", pX, y, enterP * fade, 1f + .25f * pulse(t));
            drawNeon(canvas, "J", jX, y, enterJ * fade, 1f + .25f * pulse(t + .13f));

            if (lock > 0f) {
                bolt.setStyle(Paint.Style.STROKE);
                bolt.setStrokeWidth(dp(1.3f));
                bolt.setColor(Color.argb((int)(115 * (1f-lock) * fade), 109, 231, 255));
                canvas.drawCircle(cx, baseY - size * .35f, dp(48f) + dp(38f) * lock, bolt);
            }

            if (reveal > 0f) {
                accent.setShader(null);
                accent.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
                accent.setTextSize(sp(24f));
                accent.setColor(Color.argb((int)(255 * reveal * fade), 184, 241, 255));
                accent.setShadowLayer(dp(10f), 0, 0, Color.argb((int)(150 * reveal * fade), 35, 217, 255));
                canvas.drawText("BUILTS", cx, baseY + dp(58f), accent);
                accent.clearShadowLayer();
                accent.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
                accent.setTextSize(sp(10f));
                accent.setColor(Color.argb((int)(150 * reveal * fade), 135, 215, 237));
                canvas.drawText("IDEA  •  BUILD  •  INNOVATE", cx, baseY + dp(84f), accent);
            }
        }

        private void drawCurrent(Canvas canvas, float pCenter, float jCenter, float y, float t, float lock, float fade) {
            if (lock <= 0f || fade <= 0f) return;
            float flicker = (float)Math.sin(t * 110f) > -.15f ? 1f : .2f;
            int alpha = (int)(230 * (1f-lock*.35f) * flicker * fade);
            bolt.setStrokeWidth(dp(2.1f));
            bolt.setColor(Color.argb(alpha, 230, 252, 255));
            bolt.setShadowLayer(dp(10f), 0, 0, Color.argb(alpha, 40, 220, 255));
            path.reset();
            float left = pCenter + dp(4f), right = jCenter - dp(4f), span = right-left;
            path.moveTo(left, y);
            path.lineTo(left + span*.20f, y-dp(9f));
            path.lineTo(left + span*.38f, y+dp(7f));
            path.lineTo(left + span*.57f, y-dp(6f));
            path.lineTo(left + span*.76f, y+dp(8f));
            path.lineTo(right, y);
            canvas.drawPath(path, bolt);
            bolt.clearShadowLayer();
        }

        private void drawNeon(Canvas canvas, String value, float x, float y, float alphaF, float glow) {
            int a = (int)(255 * clamp(alphaF));
            if (a <= 0) return;
            text.setColor(Color.argb(a, 232, 251, 255));
            text.setShadowLayer(dp(11f * glow), 0, 0, Color.argb((int)(205 * alphaF), 31, 217, 255));
            canvas.drawText(value, x, y, text);
            text.setShadowLayer(dp(2.5f), 0, 0, Color.argb((int)(230 * alphaF), 124, 115, 255));
            canvas.drawText(value, x, y, text);
            text.clearShadowLayer();
        }

        private float dp(float v) { return v * density; }
        private float sp(float v) { return v * getResources().getDisplayMetrics().scaledDensity; }
        private float clamp(float v) { return Math.max(0f, Math.min(1f, v)); }
        private float lerp(float a, float b, float t) { return a + (b-a) * t; }
        private float easeOut(float v) { return 1f - (1f-v)*(1f-v)*(1f-v); }
        private float easeIn(float v) { return v*v*v; }
        private float pulse(float v) { return .66f + .34f * (float)Math.sin(Math.PI * clamp(v)); }
    }
}
