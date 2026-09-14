package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Activity;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONObject;

/** Native Android FloodSafe home. No WebView/HTML/JS is used here. */
public final class NativeHomeActivity extends Activity implements LocationListener {
    private static final int LOCATION_REQUEST = 740;
    private static final String PREFS = "floodsafe-native-home";
    private static final String KEY_LAT = "last_lat";
    private static final String KEY_LON = "last_lon";
    private static final String KEY_AT = "last_at";
    private static final long LAST_LOCATION_MAX_AGE_MS = 7L * 24L * 60L * 60L * 1000L;

    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private LocationManager locationManager;
    private TextView locationText;
    private TextView temperatureText;
    private TextView weatherText;
    private TextView detailText;
    private TextView statusText;
    private double cachedLat = Double.NaN;
    private double cachedLon = Double.NaN;
    private long cachedAt;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(234, 246, 255));
        getWindow().setNavigationBarColor(Color.rgb(234, 246, 255));
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        locationManager = getSystemService(LocationManager.class);
        setContentView(buildUi());
        restoreLastLocationAndWeather();
        requestCurrentLocation();
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(28));
        root.setBackgroundColor(Color.rgb(234, 246, 255));
        scroll.addView(root);

        TextView title = text("FloodSafe Nepal", 28, true);
        title.setTextColor(Color.rgb(13, 42, 87));
        root.addView(title);

        TextView subtitle = text("Native Android safety monitoring", 13, false);
        subtitle.setTextColor(Color.rgb(72, 95, 120));
        root.addView(subtitle, lp(-1, dp(34)));

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20), dp(22), dp(20), dp(22));
        card.setBackgroundColor(Color.rgb(31, 139, 191));
        root.addView(card, lp(-1, -2));

        locationText = text("📍 Location जाँच हुँदैछ…", 16, true);
        locationText.setTextColor(Color.WHITE);
        card.addView(locationText);

        temperatureText = text("—°", 48, false);
        temperatureText.setTextColor(Color.WHITE);
        card.addView(temperatureText);

        weatherText = text("मौसम लोड हुँदैछ…", 27, true);
        weatherText.setTextColor(Color.WHITE);
        card.addView(weatherText);

        detailText = text("", 15, false);
        detailText.setTextColor(Color.rgb(230, 248, 255));
        detailText.setPadding(0, dp(16), 0, 0);
        card.addView(detailText);

        Button locate = new Button(this);
        locate.setText("◎ मेरो हालको स्थान");
        locate.setOnClickListener(v -> requestCurrentLocation());
        root.addView(locate, lp(-1, dp(58)));

        statusText = text("🛡️ Flood/rain alerts native background service बाट चल्छन्।", 15, false);
        statusText.setTextColor(Color.rgb(28, 58, 85));
        statusText.setPadding(dp(4), dp(18), dp(4), dp(18));
        root.addView(statusText);

        TextView river = text("🌊 Native river dashboard migration", 20, true);
        river.setTextColor(Color.rgb(13, 42, 87));
        root.addView(river);

        TextView riverInfo = text("Official BIPAD/DHM river status, 2 km verified Warning/Danger rule, notifications and background monitor use the existing native safety workers while the WebView UI is removed.", 14, false);
        riverInfo.setTextColor(Color.rgb(72, 95, 120));
        root.addView(riverInfo);
        return scroll;
    }

    private TextView text(String value, int sp, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setGravity(Gravity.START);
        if (bold) t.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        return t;
    }

    private LinearLayout.LayoutParams lp(int w, int h) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.setMargins(0, 0, 0, dp(14));
        return p;
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    private void restoreLastLocationAndWeather() {
        SharedPreferences p = getSharedPreferences(PREFS, MODE_PRIVATE);
        cachedAt = p.getLong(KEY_AT, 0L);
        cachedLat = Double.longBitsToDouble(p.getLong(KEY_LAT, Double.doubleToRawLongBits(Double.NaN)));
        cachedLon = Double.longBitsToDouble(p.getLong(KEY_LON, Double.doubleToRawLongBits(Double.NaN)));
        if (hasUsableCache()) {
            showCachedLocationLabel();
            fetchWeather(cachedLat, cachedLon, true);
        } else {
            cachedLat = Double.NaN;
            cachedLon = Double.NaN;
            cachedAt = 0L;
            locationText.setText("📍 Location उपलब्ध छैन");
            weatherText.setText("Location अनुमति दिनुहोस्");
            temperatureText.setText("—°");
        }
    }

    private boolean hasUsableCache() {
        return Double.isFinite(cachedLat) && Double.isFinite(cachedLon) && cachedAt > 0L
                && System.currentTimeMillis() - cachedAt <= LAST_LOCATION_MAX_AGE_MS;
    }

    private void showCachedLocationLabel() {
        if (!hasUsableCache()) return;
        boolean nepal = isNepal(cachedLat, cachedLon);
        locationText.setText(nepal
                ? "📍 पछिल्लो verified GPS • weather यही स्थानको हो"
                : "🌍 पछिल्लो verified GPS Nepal बाहिर • weather यही स्थानको हो");
    }

    private void requestCurrentLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            if (!hasUsableCache()) {
                locationText.setText("📍 Location अनुमति आवश्यक छ");
                weatherText.setText("Location अनुमति दिनुहोस्");
            }
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_REQUEST);
            return;
        }
        if (locationManager == null) {
            showCachedLocationLabel();
            return;
        }
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationText.setText("📍 हालको GPS खोजिँदैछ…");
                locationManager.requestSingleUpdate(LocationManager.GPS_PROVIDER, this, getMainLooper());
            } else if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationText.setText("📍 हालको network location खोजिँदैछ…");
                locationManager.requestSingleUpdate(LocationManager.NETWORK_PROVIDER, this, getMainLooper());
            } else {
                // Critical: GPS OFF must never recurse or jump to Kathmandu.
                if (hasUsableCache()) {
                    showCachedLocationLabel();
                    statusText.setText("📍 GPS बन्द छ • पछिल्लो verified location सुरक्षित रूपमा प्रयोग भइरहेको छ।");
                } else {
                    locationText.setText("📍 GPS बन्द छ • पछिल्लो location छैन");
                    weatherText.setText("Location unavailable");
                    temperatureText.setText("—°");
                }
            }
        } catch (SecurityException ignored) {
            showCachedLocationLabel();
        }
    }

    @Override public void onLocationChanged(Location location) {
        if (location == null) return;
        cachedLat = location.getLatitude();
        cachedLon = location.getLongitude();
        cachedAt = System.currentTimeMillis();
        getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                .putLong(KEY_LAT, Double.doubleToRawLongBits(cachedLat))
                .putLong(KEY_LON, Double.doubleToRawLongBits(cachedLon))
                .putLong(KEY_AT, cachedAt).apply();
        locationText.setText(isNepal(cachedLat, cachedLon)
                ? "📍 हालको GPS • Nepal"
                : "🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो");
        fetchWeather(cachedLat, cachedLon, false);
    }

    private static boolean isNepal(double lat, double lon) {
        return lat >= 26.2 && lat <= 30.5 && lon >= 80.0 && lon <= 88.35;
    }

    private void fetchWeather(double lat, double lon, boolean cachedLocation) {
        io.execute(() -> {
            try {
                String url = String.format(Locale.US,
                        "https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=auto",
                        lat, lon);
                HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                c.setConnectTimeout(9000);
                c.setReadTimeout(9000);
                c.setRequestProperty("Accept", "application/json");
                try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream()))) {
                    StringBuilder b = new StringBuilder();
                    String line;
                    while ((line = r.readLine()) != null) b.append(line);
                    JSONObject j = new JSONObject(b.toString());
                    JSONObject cur = j.getJSONObject("current");
                    double temp = cur.optDouble("temperature_2m", Double.NaN);
                    double rain = cur.optDouble("precipitation", 0d);
                    double humidity = cur.optDouble("relative_humidity_2m", Double.NaN);
                    double wind = cur.optDouble("wind_speed_10m", Double.NaN);
                    String zone = j.optString("timezone", "local");
                    runOnUiThread(() -> {
                        if (isFinishing() || isDestroyed()) return;
                        temperatureText.setText(Double.isFinite(temp) ? Math.round(temp) + "°" : "—°");
                        weatherText.setText(rain >= .5 ? "पूर्वानुमान: वर्षा" : "पूर्वानुमान: अहिले वर्षा छैन");
                        detailText.setText(String.format(Locale.US,
                                "%.1f mm वर्षा  •  %.0f%% आर्द्रता  •  %.0f km/h हावा\n%s%s",
                                rain, humidity, wind, zone,
                                cachedLocation ? " • last verified GPS" : ""));
                    });
                } finally {
                    c.disconnect();
                }
            } catch (Exception e) {
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (!hasUsableCache()) {
                        weatherText.setText("मौसम अपडेट उपलब्ध छैन");
                    }
                    statusText.setText("Network/weather retry आवश्यक छ; verified GPS cache सुरक्षित छ।");
                });
            }
        });
    }

    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(code, permissions, grants);
        if (code != LOCATION_REQUEST) return;
        boolean granted = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
        if (granted) requestCurrentLocation();
        else if (hasUsableCache()) showCachedLocationLabel();
        else {
            locationText.setText("📍 Location अनुमति दिइएको छैन");
            weatherText.setText("Location unavailable");
        }
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }
}
