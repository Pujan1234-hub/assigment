package io.github.pujan1234hub.floodsafe.app;

import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import java.util.Locale;

/**
 * Lightweight native PJBUILTS launch animation.
 *
 * The existing FloodSafe/voice activity starts underneath no extra framework or
 * network dependency.  The sequence is intentionally short so safety features
 * are never held behind a long branded screen.
 */
public final class PJBuiltsSplashActivity extends Activity {
    private boolean launched;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        Window window = getWindow();
        window.setStatusBarColor(Color.rgb(3, 7, 18));
        window.setNavigationBarColor(Color.rgb(3, 7, 18));
        window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        window.getDecorView().setSystemUiVisibility(0);

        boolean reduceMotion = Build.VERSION.SDK_INT >= 26 && !ValueAnimator.areAnimatorsEnabled();
        setContentView(new BrandSplashView(reduceMotion ? 420L : 2550L));
    }

    private void openApp() {
        if (launched || isFinishing() || isDestroyed()) return;
        launched = true;

        Intent source = getIntent();
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

    private final class BrandSplashView extends View {
        private static final String NAME = "PUJAN";
        private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Paint accent = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        private final Paint particle = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final long durationMs;
        private long startedAt;
        private float density;

        BrandSplashView(long durationMs) {
            super(PJBuiltsSplashActivity.this);
            this.durationMs = durationMs;
            density = getResources().getDisplayMetrics().density;
            setBackgroundColor(Color.rgb(3, 7, 18));
            setLayerType(View.LAYER_TYPE_SOFTWARE, null);

            Typeface face = Typeface.create("sans-serif", Typeface.BOLD);
            text.setTypeface(face);
            text.setTextAlign(Paint.Align.LEFT);
            accent.setTypeface(face);
            accent.setTextAlign(Paint.Align.LEFT);
            particle.setStyle(Paint.Style.FILL);
            line.setStrokeWidth(dp(1f));
            line.setColor(Color.argb(28, 80, 218, 255));
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

            long elapsed = SystemClock.uptimeMillis() - startedAt;
            float t = clamp(elapsed / (float) durationMs);
            drawBackdrop(canvas, t);
            drawLogo(canvas, t);

            if (t < 1f) postInvalidateOnAnimation();
            else post(PJBuiltsSplashActivity.this::openApp);
        }

        private void drawBackdrop(Canvas canvas, float t) {
            float cx = getWidth() * .5f;
            float cy = getHeight() * .48f;
            float max = Math.max(getWidth(), getHeight());

            Paint halo = particle;
            halo.setShader(new android.graphics.RadialGradient(
                    cx, cy, max * .42f,
                    new int[]{Color.argb((int) (42 * pulse(t)), 37, 211, 255), Color.TRANSPARENT},
                    new float[]{0f, 1f}, android.graphics.Shader.TileMode.CLAMP));
            canvas.drawCircle(cx, cy, max * .42f, halo);
            halo.setShader(null);

            float spacing = dp(28f);
            for (float y = cy - dp(170f); y <= cy + dp(170f); y += spacing) {
                canvas.drawLine(cx - dp(150f), y, cx + dp(150f), y, line);
            }
            for (float x = cx - dp(140f); x <= cx + dp(140f); x += spacing) {
                canvas.drawLine(x, cy - dp(180f), x, cy + dp(180f), line);
            }

            int scanAlpha = (int) (18 * (1f - t * .6f));
            line.setColor(Color.argb(scanAlpha, 112, 232, 255));
            float scanY = (getHeight() * ((t * 2.2f) % 1f));
            canvas.drawLine(0, scanY, getWidth(), scanY, line);
            line.setColor(Color.argb(28, 80, 218, 255));
        }

        private void drawLogo(Canvas canvas, float t) {
            final float cx = getWidth() * .5f;
            final float baseY = getHeight() * .49f;
            final float size = Math.min(sp(58f), getWidth() * .14f);
            final float gap = dp(5f);
            text.setTextSize(size);
            accent.setTextSize(size);

            float intro = easeOut(clamp(t / .20f));
            float split = easeInOut(clamp((t - .22f) / .29f));
            float lock = easeOut(clamp((t - .43f) / .22f));
            float reveal = easeOut(clamp((t - .58f) / .22f));
            float exit = 1f - easeIn(clamp((t - .90f) / .10f));

            float[] pos = letterPositions(cx, gap);
            float initialP = pos[0];
            float initialJ = pos[2];
            float pjWidth = text.measureText("PJ");
            float finalP = cx - pjWidth * .5f;
            float finalJ = finalP + text.measureText("P");

            float pX = lerp(initialP, finalP, split);
            float jX = lerp(initialJ, finalJ, split);
            float y = baseY + dp(10f) * (1f - intro);

            if (split < .98f) {
                drawFadingLetter(canvas, "U", pos[1], y, 1, intro, split);
                drawFadingLetter(canvas, "A", pos[3], y, 3, intro, split);
                drawFadingLetter(canvas, "N", pos[4], y, 4, intro, split);
                drawGlitchParticles(canvas, pos, baseY, split);
            }

            float brandAlpha = Math.min(intro, exit);
            float glow = .48f + .52f * pulse(lock);
            drawNeonText(canvas, "P", pX, y, brandAlpha, glow);
            drawNeonText(canvas, "J", jX, y, brandAlpha, glow);

            if (reveal > 0f) {
                String built = "BUILTS";
                float builtSize = size * .47f;
                accent.setTextSize(builtSize);
                float wordWidth = accent.measureText(built);
                float x = cx - wordWidth * .5f;
                float wordY = baseY + dp(58f);
                int alpha = (int) (255 * reveal * exit);
                accent.setColor(Color.argb(alpha, 192, 239, 255));
                accent.setShadowLayer(dp(12f) * reveal, 0, 0, Color.argb(alpha / 2, 46, 215, 255));
                float trackingSpread = dp(16f) * (1f - reveal);
                canvas.drawText(built, x + trackingSpread, wordY, accent);
                accent.clearShadowLayer();

                accent.setTextSize(sp(10f));
                accent.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
                accent.setColor(Color.argb((int) (145 * reveal * exit), 125, 211, 238));
                String tag = "IDEA  •  BUILD  •  INNOVATE";
                float tagWidth = accent.measureText(tag);
                canvas.drawText(tag, cx - tagWidth / 2f, wordY + dp(29f), accent);
                accent.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
            }

            if (lock > 0f && lock < 1f) {
                float radius = dp(54f) + dp(44f) * lock;
                particle.setStyle(Paint.Style.STROKE);
                particle.setStrokeWidth(dp(1.2f));
                particle.setColor(Color.argb((int) (130 * (1f - lock)), 92, 226, 255));
                canvas.drawCircle(cx, baseY - size * .35f, radius, particle);
                particle.setStyle(Paint.Style.FILL);
            }
        }

        private float[] letterPositions(float cx, float gap) {
            float total = 0f;
            for (int i = 0; i < NAME.length(); i++) total += text.measureText(NAME.substring(i, i + 1));
            total += gap * (NAME.length() - 1);
            float cursor = cx - total / 2f;
            float[] out = new float[NAME.length()];
            for (int i = 0; i < NAME.length(); i++) {
                out[i] = cursor;
                cursor += text.measureText(NAME.substring(i, i + 1)) + gap;
            }
            return out;
        }

        private void drawFadingLetter(Canvas canvas, String letter, float x, float y, int seed,
                                      float intro, float split) {
            float alphaF = intro * (1f - split);
            float jitter = dp(5f) * split;
            float dx = (float) Math.sin(split * 38f + seed * 2.1f) * jitter;
            float dy = (float) Math.cos(split * 31f + seed) * jitter * .6f;
            drawNeonText(canvas, letter, x + dx, y + dy, alphaF, .45f);
        }

        private void drawGlitchParticles(Canvas canvas, float[] pos, float baseY, float split) {
            int[] ids = {1, 3, 4};
            for (int id : ids) {
                float center = pos[id] + text.measureText(NAME.substring(id, id + 1)) * .5f;
                for (int i = 0; i < 9; i++) {
                    float phase = split * (1.1f + i * .035f);
                    float angle = (id * 1.9f + i * 2.399f);
                    float distance = dp(8f + i * 4.2f) * phase;
                    float px = center + (float) Math.cos(angle) * distance;
                    float py = baseY - text.getTextSize() * .35f + (float) Math.sin(angle) * distance;
                    int a = (int) (150 * (1f - split));
                    particle.setColor(Color.argb(Math.max(0, a), i % 2 == 0 ? 78 : 135, 222, 255));
                    canvas.drawCircle(px, py, dp(1.1f + (i % 3) * .45f), particle);
                }
            }
        }

        private void drawNeonText(Canvas canvas, String value, float x, float y, float alphaF, float glow) {
            int a = (int) (255 * clamp(alphaF));
            if (a <= 0) return;
            text.setColor(Color.argb(a, 222, 249, 255));
            text.setShadowLayer(dp(8f + 10f * glow), 0, 0, Color.argb((int) (190 * alphaF), 41, 212, 255));
            canvas.drawText(value, x, y, text);
            text.setShadowLayer(dp(2f), 0, 0, Color.argb((int) (235 * alphaF), 123, 103, 255));
            canvas.drawText(value, x, y, text);
            text.clearShadowLayer();
        }

        private float pulse(float t) {
            return .62f + .38f * (float) Math.sin(Math.PI * clamp(t));
        }

        private float dp(float v) { return v * density; }
        private float sp(float v) { return v * getResources().getDisplayMetrics().scaledDensity; }
        private float clamp(float v) { return Math.max(0f, Math.min(1f, v)); }
        private float lerp(float a, float b, float t) { return a + (b - a) * t; }
        private float easeOut(float v) { return 1f - (1f - v) * (1f - v) * (1f - v); }
        private float easeIn(float v) { return v * v * v; }
        private float easeInOut(float v) {
            return v < .5f ? 4f * v * v * v : 1f - (float) Math.pow(-2f * v + 2f, 3) / 2f;
        }
    }
}
