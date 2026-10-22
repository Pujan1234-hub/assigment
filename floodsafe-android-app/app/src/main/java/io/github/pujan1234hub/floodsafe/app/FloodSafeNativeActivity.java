package io.github.pujan1234hub.floodsafe.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * FloodSafe Nepal native-only screen.
 * No WebView is used anywhere in this Activity.
 */
public final class FloodSafeNativeActivity extends Activity implements LocationListener {
    private static final int REQ_LOCATION = 911;
    private static final int REQ_NOTIFY = 912;
    private static final String RIVER_ENDPOINT = "https://camkoacuokffryyrygda.supabase.co/functions/v1/sync-bipad-rivers";
    private static final String BIPAD_RAIN_ENDPOINT = "https://bipadportal.gov.np/api/v1/rain/?limit=500";
    private static final long FRESH_MS = 10L * 60L * 1000L;

    private final ExecutorService io = Executors.newFixedThreadPool(4);
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<LiveStation> stations = new ArrayList<>();
    private final List<RainStation> rainStations = new ArrayList<>();

    private LocationManager locationManager;
    private double userLat = Double.NaN;
    private double userLon = Double.NaN;
    private long userLocationAt;

    private FloodSafeNativeMapView map;
    private CloudFieldView clouds;
    private TextView place;
    private TextView weather;
    private TextView feed;
    private TextView gps;
    private TextView counts;
    private TextView nearby;
    private TextView rainDetail;
    private TextView alertBox;
    private double cloudCover = 0d;
    private double currentRainMm = 0d;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(6, 23, 35));
        getWindow().setNavigationBarColor(Color.rgb(6, 23, 35));
        locationManager = getSystemService(LocationManager.class);
        setContentView(buildUi());
        enableBackgroundMonitoring();
        refreshAll();
        requestLocation();
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(14), dp(12), dp(28));
        root.setBackgroundColor(Color.rgb(225, 243, 250));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView title = text("FloodSafe Nepal", 26, true, Color.rgb(12, 42, 65));
        TextView sub = text("PJBUILTS • Native Android • BIPAD/DHM live monitoring", 12, true, Color.rgb(66, 105, 128));
        root.addView(title);
        root.addView(sub, margin(-1, -2, 0, 0, 0, 10));

        LinearLayout status = card();
        place = text("📍 Location खोज्दै…", 16, true, Color.rgb(17, 53, 77));
        weather = text("☁️ Weather refresh हुँदैछ…", 14, false, Color.rgb(50, 85, 108));
        gps = text("GPS: waiting", 12, false, Color.rgb(76, 109, 129));
        status.addView(place);
        status.addView(weather, margin(-1, -2, 0, 6, 0, 0));
        status.addView(gps, margin(-1, -2, 0, 4, 0, 0));
        root.addView(status, margin(-1, -2, 0, 0, 0, 10));

        FrameLayout mapBox = new FrameLayout(this);
        mapBox.setBackground(round(Color.rgb(9, 31, 43), 24, Color.rgb(92, 139, 160), 1));
        map = new FloodSafeNativeMapView(this, this::showStationObject);
        mapBox.addView(map, new FrameLayout.LayoutParams(-1, dp(470)));
        clouds = new CloudFieldView(this);
        clouds.setClickable(false);
        mapBox.addView(clouds, new FrameLayout.LayoutParams(-1, dp(470)));
        TextView legend = text("🔵 Normal   🟡 Alert   🟠 Warning   🔴 Danger   ◉ You", 11, true, Color.rgb(18, 50, 68));
        legend.setPadding(dp(10), dp(8), dp(10), dp(8));
        legend.setBackground(round(Color.argb(235, 255, 255, 255), 16, Color.rgb(207, 226, 236), 1));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        lp.setMargins(dp(8), 0, dp(8), dp(10));
        mapBox.addView(legend, lp);
        root.addView(mapBox, margin(-1, dp(470), 0, 0, 0, 10));

        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.HORIZONTAL);
        Button locate = button("◎ मेरो GPS");
        Button refresh = button("↻ Live refresh");
        Button nepal = button("🇳🇵 Nepal");
        controls.addView(locate, weight());
        controls.addView(refresh, weight());
        controls.addView(nepal, weight());
        locate.setOnClickListener(v -> requestLocation());
        refresh.setOnClickListener(v -> refreshAll());
        nepal.setOnClickListener(v -> map.resetView());
        root.addView(controls, margin(-1, dp(52), 0, 0, 0, 10));

        alertBox = text("", 14, true, Color.rgb(139, 30, 47));
        alertBox.setPadding(dp(14), dp(12), dp(14), dp(12));
        alertBox.setBackground(round(Color.rgb(255, 232, 236), 18, Color.rgb(234, 129, 145), 2));
        alertBox.setVisibility(View.GONE);
        root.addView(alertBox, margin(-1, -2, 0, 0, 0, 10));

        LinearLayout liveCard = card();
        TextView liveTitle = text("Official river status", 19, true, Color.rgb(16, 46, 68));
        feed = text("BIPAD/DHM feed refresh हुँदैछ…", 12, false, Color.rgb(77, 108, 128));
        counts = text("—", 15, true, Color.rgb(31, 73, 97));
        nearby = text("नजिकको station: —", 13, false, Color.rgb(53, 86, 108));
        liveCard.addView(liveTitle);
        liveCard.addView(feed, margin(-1, -2, 0, 4, 0, 0));
        liveCard.addView(counts, margin(-1, -2, 0, 9, 0, 0));
        liveCard.addView(nearby, margin(-1, -2, 0, 9, 0, 0));
        root.addView(liveCard, margin(-1, -2, 0, 0, 0, 10));

        LinearLayout rainCard = card();
        TextView rainTitle = text("Rainfall detail", 19, true, Color.rgb(16, 46, 68));
        TextView rainSub = text("Rainfall station marker map मा देखाइँदैन। नजिकको/सम्बन्धित rainfall detail यहाँ मात्र देखिन्छ।", 12, false, Color.rgb(77, 108, 128));
        rainDetail = text("Rainfall data refresh हुँदैछ…", 14, true, Color.rgb(45, 80, 103));
        rainCard.addView(rainTitle);
        rainCard.addView(rainSub, margin(-1, -2, 0, 4, 0, 0));
        rainCard.addView(rainDetail, margin(-1, -2, 0, 10, 0, 0));
        root.addView(rainCard);
        return scroll;
    }

    private void refreshAll() {
        refreshRivers();
        refreshRain();
        if (isNepal(userLat, userLon)) refreshWeather(userLat, userLon);
    }

    private void refreshRivers() {
        feed.setText("BIPAD/DHM river feed refresh हुँदैछ…");
        io.execute(() -> {
            try {
                JSONObject root = getJson(RIVER_ENDPOINT + "?_native=" + System.currentTimeMillis());
                JSONArray rows = arrayFrom(root);
                List<LiveStation> out = new ArrayList<>();
                long now = System.currentTimeMillis();
                for (int i = 0; i < rows.length(); i++) {
                    LiveStation s = parseRiver(rows.optJSONObject(i), now);
                    if (s != null) out.add(s);
                }
                out.sort(Comparator.comparingInt((LiveStation s) -> s.rank).thenComparingDouble(this::distanceToUser));
                synchronized (stations) {
                    stations.clear();
                    stations.addAll(out);
                }
                runOnUiThread(this::renderRiverData);
            } catch (Exception e) {
                runOnUiThread(() -> feed.setText("River refresh failed • stale data लाई live देखाइएको छैन"));
            }
        });
    }

    private void refreshRain() {
        io.execute(() -> {
            try {
                JSONObject root = getJson(BIPAD_RAIN_ENDPOINT + "&_fs=" + System.currentTimeMillis());
                JSONArray rows = arrayFrom(root);
                List<RainStation> out = new ArrayList<>();
                for (int i = 0; i < rows.length(); i++) {
                    RainStation r = parseRain(rows.optJSONObject(i));
                    if (r != null) out.add(r);
                }
                synchronized (rainStations) {
                    rainStations.clear();
                    rainStations.addAll(out);
                }
                runOnUiThread(this::renderRainData);
            } catch (Exception e) {
                runOnUiThread(() -> rainDetail.setText("BIPAD rainfall station detail अहिले fetch हुन सकेन। GPS weather rainfall भने live छ।"));
            }
        });
    }

    private void renderRiverData() {
        List<LiveStation> copy;
        synchronized (stations) { copy = new ArrayList<>(stations); }
        map.setStations(copy, userLat, userLon);
        int danger = 0, warning = 0, alert = 0, normal = 0, stale = 0;
        for (LiveStation s : copy) {
            switch (s.stage) {
                case "danger": danger++; break;
                case "warning": warning++; break;
                case "alert": alert++; break;
                case "normal": normal++; break;
                default: stale++;
            }
        }
        counts.setText("🔴 " + danger + "   🟠 " + warning + "   🟡 " + alert + "   🔵 " + normal + "   ⚪ stale " + stale);
        feed.setText("Fresh official stations: " + (danger + warning + alert + normal) + " / total " + copy.size());

        LiveStation closest = null;
        double closestKm = Double.POSITIVE_INFINITY;
        LiveStation emergency = null;
        double emergencyKm = Double.POSITIVE_INFINITY;
        for (LiveStation s : copy) {
            double d = distanceToUser(s);
            if (d < closestKm) { closestKm = d; closest = s; }
            if (s.fresh && ("warning".equals(s.stage) || "danger".equals(s.stage))) {
                double riverDistance = NativeRiverRiskDistance.distanceKm(this, userLat, userLon, s.name);
                double effective = Double.isFinite(riverDistance) ? riverDistance : d;
                if (effective <= 2d && effective < emergencyKm) { emergencyKm = effective; emergency = s; }
            }
        }
        if (closest != null && Double.isFinite(closestKm)) {
            nearby.setText("नजिकको official station: " + closest.name + " • " + String.format(Locale.US, "%.1f km", closestKm) + " • " + closest.stage.toUpperCase(Locale.ROOT));
        } else nearby.setText("GPS location लिएपछि नजिकको station देखिन्छ।");
        if (emergency != null) {
            String prefix = "danger".equals(emergency.stage) ? "🚨 DANGER" : "⚠️ WARNING";
            alertBox.setText(prefix + " • " + emergency.name + " • प्रभावित नदीबाट " + String.format(Locale.US, "%.1f km", emergencyKm) + "\n2 km safety alert active");
            alertBox.setVisibility(View.VISIBLE);
        } else alertBox.setVisibility(View.GONE);
    }

    private void renderRainData() {
        RainStation best = nearestRainStation(userLat, userLon);
        if (best == null) {
            rainDetail.setText(String.format(Locale.US, "GPS weather precipitation: %.1f mm • nearby BIPAD rainfall station उपलब्ध छैन", currentRainMm));
            return;
        }
        double d = km(userLat, userLon, best.lat, best.lon);
        StringBuilder b = new StringBuilder();
        b.append("नजिकको rainfall station: ").append(best.name);
        if (Double.isFinite(d)) b.append(String.format(Locale.US, " • %.1f km", d));
        if (Double.isFinite(best.rainfallMm)) b.append(String.format(Locale.US, "\nOfficial rainfall: %.1f mm", best.rainfallMm));
        if (!best.status.isEmpty()) b.append("\nStatus: ").append(best.status);
        b.append(String.format(Locale.US, "\nGPS weather precipitation now: %.1f mm", currentRainMm));
        rainDetail.setText(b.toString());
    }

    private void refreshWeather(double lat, double lon) {
        io.execute(() -> {
            try {
                String url = String.format(Locale.US,
                        "https://api.open-meteo.com/v1/forecast?latitude=%.5f&longitude=%.5f&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m&timezone=auto",
                        lat, lon);
                JSONObject root = getJson(url);
                JSONObject c = root.optJSONObject("current");
                if (c == null) return;
                double temp = c.optDouble("temperature_2m", Double.NaN);
                double humidity = c.optDouble("relative_humidity_2m", Double.NaN);
                double rain = c.optDouble("precipitation", 0d);
                double cloud = c.optDouble("cloud_cover", 0d);
                double wind = c.optDouble("wind_speed_10m", Double.NaN);
                currentRainMm = rain;
                cloudCover = Math.max(0d, Math.min(100d, cloud));
                runOnUiThread(() -> {
                    weather.setText((cloudCover >= 75 ? "☁️" : cloudCover >= 35 ? "⛅" : "☀️") + " "
                            + (Double.isFinite(temp) ? Math.round(temp) + "°C" : "—")
                            + " • Cloud " + Math.round(cloudCover) + "%"
                            + " • Rain " + String.format(Locale.US, "%.1f mm", rain)
                            + (Double.isFinite(humidity) ? " • Humidity " + Math.round(humidity) + "%" : "")
                            + (Double.isFinite(wind) ? " • Wind " + Math.round(wind) + " km/h" : ""));
                    clouds.setCloudCover((float) cloudCover);
                    renderRainData();
                });
            } catch (Exception e) {
                runOnUiThread(() -> weather.setText("Weather refresh failed"));
            }
        });
    }

    private LiveStation parseRiver(JSONObject r, long now) {
        if (r == null) return null;
        double lat = num(r, "latitude", "lat", "stationLatitude", "station_latitude");
        double lon = num(r, "longitude", "lon", "lng", "stationLongitude", "station_longitude");
        if (!isNepal(lat, lon)) return null;
        double level = num(r, "waterLevel", "water_level", "currentWaterLevel", "current_water_level", "currentLevel", "current_level", "level", "_lastWaterLevel");
        double warning = num(r, "warningLevel", "warning_level", "warningThreshold", "warning_threshold", "_lastWarningLevel");
        double danger = num(r, "dangerLevel", "danger_level", "dangerThreshold", "danger_threshold", "_lastDangerLevel");
        long at = parseTime(str(r, "waterLevelOn", "water_level_on", "measuredOn", "measured_on", "measurementTime", "measurement_time", "observationTime", "observation_time", "observedAt", "observed_at", "datetime", "timestamp", "_measurementTime"));
        boolean fresh = at > 0L && now - at <= FRESH_MS && at - now <= 5L * 60L * 1000L;
        String raw = str(r, "status", "status_name", "alertStatus", "alert_status", "riskLevel", "risk_level", "_officialStatus").toUpperCase(Locale.ROOT);
        String stage = "unknown";
        int rank = 4;
        if (fresh) {
            if ((Double.isFinite(level) && Double.isFinite(danger) && danger > 0 && level >= danger) || (raw.contains("DANGER") && !raw.contains("BELOW DANGER")) || raw.contains("RED")) { stage = "danger"; rank = 0; }
            else if ((Double.isFinite(level) && Double.isFinite(warning) && warning > 0 && level >= warning) || (raw.contains("WARNING") && !raw.contains("BELOW WARNING")) || raw.contains("ORANGE")) { stage = "warning"; rank = 1; }
            else if ((Double.isFinite(level) && Double.isFinite(warning) && warning > 0 && level >= warning * .8) || raw.contains("ALERT") || raw.contains("WATCH") || raw.contains("YELLOW")) { stage = "alert"; rank = 2; }
            else { stage = "normal"; rank = 3; }
        }
        String name = str(r, "river_name", "riverName", "station_name", "stationName", "title", "name");
        if (name.isEmpty()) name = "Official river station";
        String district = str(r, "districtName", "district_name", "district");
        double rainfall = num(r, "rainfall", "rainfallMm", "rainfall_mm", "rain24h", "rainfall24h");
        return new LiveStation(name, district, lat, lon, level, warning, danger, rainfall, at, fresh, stage, rank);
    }

    private RainStation parseRain(JSONObject r) {
        if (r == null) return null;
        double lat = num(r, "latitude", "lat", "stationLatitude", "station_latitude");
        double lon = num(r, "longitude", "lon", "lng", "stationLongitude", "station_longitude");
        if (!isNepal(lat, lon)) return null;
        String name = str(r, "station_name", "stationName", "title", "name");
        if (name.isEmpty()) name = "Rainfall station";
        double rainfall = num(r, "rainfall", "rainfall_mm", "value", "amount", "rainfall24h", "rain24h", "_lastRainfall");
        String status = str(r, "status", "status_name", "alertStatus", "alert_status");
        return new RainStation(name, lat, lon, rainfall, status);
    }

    private void showStationObject(Object object) {
        if (!(object instanceof LiveStation)) return;
        LiveStation s = (LiveStation) object;
        RainStation r = nearestRainStation(s.lat, s.lon);
        StringBuilder b = new StringBuilder();
        b.append(s.stage.toUpperCase(Locale.ROOT));
        if (Double.isFinite(s.level)) b.append(String.format(Locale.US, "\nWater level: %.2f m", s.level));
        if (Double.isFinite(s.warning)) b.append(String.format(Locale.US, "\nWarning: %.2f m", s.warning));
        if (Double.isFinite(s.danger)) b.append(String.format(Locale.US, "\nDanger: %.2f m", s.danger));
        if (s.at > 0L) b.append("\nObserved: ").append(Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
        if (r != null) {
            double d = km(s.lat, s.lon, r.lat, r.lon);
            b.append("\n\nNearby rainfall: ").append(r.name);
            if (Double.isFinite(d)) b.append(String.format(Locale.US, " • %.1f km", d));
            if (Double.isFinite(r.rainfallMm)) b.append(String.format(Locale.US, "\nRainfall: %.1f mm", r.rainfallMm));
            if (!r.status.isEmpty()) b.append("\nRain status: ").append(r.status);
        }
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton("ठीक छ", null).show();
    }

    private void requestLocation() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED
                && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_LOCATION);
            return;
        }
        try {
            if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 4000L, 8f, this);
                Location last = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (last != null) onLocationChanged(last);
            }
            if (locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 6000L, 15f, this);
                Location last = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
                if (last != null) onLocationChanged(last);
            }
            gps.setText("GPS active • Nepal location भए map मा ◉ देखिन्छ");
        } catch (Exception e) {
            gps.setText("GPS सुरु हुन सकेन");
        }
    }

    @Override public void onLocationChanged(Location location) {
        if (location == null) return;
        double lat = location.getLatitude(), lon = location.getLongitude();
        if (!isNepal(lat, lon)) {
            gps.setText("GPS: Nepal बाहिर • Nepal map monitoring inactive");
            return;
        }
        userLat = lat;
        userLon = lon;
        userLocationAt = System.currentTimeMillis();
        gps.setText(String.format(Locale.US, "GPS: %.5f, %.5f • ±%.0f m", lat, lon, location.hasAccuracy() ? location.getAccuracy() : 0f));
        SharedPreferences.Editor e = getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit();
        e.putBoolean("enabled", true).putBoolean("follow_device", true)
                .putLong("lat", Double.doubleToRawLongBits(lat)).putLong("lon", Double.doubleToRawLongBits(lon))
                .putLong("location_time", userLocationAt)
                .putLong("device_lat", Double.doubleToRawLongBits(lat)).putLong("device_lon", Double.doubleToRawLongBits(lon))
                .putLong("device_location_time", userLocationAt).putBoolean("location_stale", false).apply();
        map.setStations(snapshotStations(), userLat, userLon);
        reverseGeocode(lat, lon);
        refreshWeather(lat, lon);
        renderRiverData();
        renderRainData();
    }

    private void reverseGeocode(double lat, double lon) {
        io.execute(() -> {
            try {
                List<android.location.Address> a = new Geocoder(this, Locale.getDefault()).getFromLocation(lat, lon, 1);
                if (a == null || a.isEmpty()) return;
                android.location.Address x = a.get(0);
                String name = x.getLocality();
                if (name == null) name = x.getSubAdminArea();
                if (name == null) name = x.getAdminArea();
                final String label = name;
                if (label != null) runOnUiThread(() -> place.setText("📍 " + label));
            } catch (Exception ignored) {}
        });
    }

    private void enableBackgroundMonitoring() {
        getSharedPreferences(RainAlertWorker.PREFS, MODE_PRIVATE).edit().putBoolean("enabled", true).apply();
        Constraints c = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        WorkManager wm = WorkManager.getInstance(getApplicationContext());
        wm.enqueueUniquePeriodicWork("floodsafe-local-river-alerts", ExistingPeriodicWorkPolicy.UPDATE,
                new PeriodicWorkRequest.Builder(RiverAlertWorker.class, 15, TimeUnit.MINUTES).setConstraints(c).build());
        wm.enqueueUniquePeriodicWork("floodsafe-local-rain-alerts", ExistingPeriodicWorkPolicy.UPDATE,
                new PeriodicWorkRequest.Builder(RainAlertWorker.class, 15, TimeUnit.MINUTES).setConstraints(c).build());
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFY);
        }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_LOCATION) requestLocation();
    }

    @Override protected void onDestroy() {
        try { if (locationManager != null) locationManager.removeUpdates(this); } catch (Exception ignored) {}
        main.removeCallbacksAndMessages(null);
        io.shutdownNow();
        super.onDestroy();
    }

    private List<LiveStation> snapshotStations() {
        synchronized (stations) { return new ArrayList<>(stations); }
    }

    private RainStation nearestRainStation(double lat, double lon) {
        if (!isNepal(lat, lon)) return null;
        RainStation best = null;
        double bestD = Double.POSITIVE_INFINITY;
        synchronized (rainStations) {
            for (RainStation r : rainStations) {
                double d = km(lat, lon, r.lat, r.lon);
                if (d < bestD) { bestD = d; best = r; }
            }
        }
        return best;
    }

    private double distanceToUser(LiveStation s) {
        return isNepal(userLat, userLon) ? km(userLat, userLon, s.lat, s.lon) : 99999d;
    }

    private static JSONArray arrayFrom(JSONObject root) {
        if (root == null) return new JSONArray();
        JSONArray a = root.optJSONArray("results");
        if (a == null) a = root.optJSONArray("data");
        if (a == null) a = root.optJSONArray("items");
        return a == null ? new JSONArray() : a;
    }

    private static JSONObject getJson(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(22000);
        c.setUseCaches(false);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-cache, no-store");
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) { c.disconnect(); throw new IllegalStateException("HTTP " + code); }
        StringBuilder b = new StringBuilder();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) b.append(line);
        } finally { c.disconnect(); }
        return new JSONObject(b.toString());
    }

    private static double num(JSONObject o, String... keys) {
        for (String k : keys) {
            if (o == null || !o.has(k) || o.isNull(k)) continue;
            Object v = o.opt(k);
            if (v instanceof Number) {
                double d = ((Number) v).doubleValue();
                if (Double.isFinite(d)) return d;
            }
            try {
                double d = Double.parseDouble(String.valueOf(v).replace("mm", "").replace("m", "").trim());
                if (Double.isFinite(d)) return d;
            } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    private static String str(JSONObject o, String... keys) {
        for (String k : keys) {
            if (o == null || !o.has(k) || o.isNull(k)) continue;
            String s = String.valueOf(o.opt(k)).trim();
            if (!s.isEmpty() && !"null".equalsIgnoreCase(s)) return s;
        }
        return "";
    }

    private static long parseTime(String value) {
        if (value == null || value.trim().isEmpty()) return -1L;
        String s = value.trim();
        try { long n = Long.parseLong(s); return n < 10_000_000_000L ? n * 1000L : n; } catch (Exception ignored) {}
        try { return Instant.parse(s).toEpochMilli(); } catch (Exception ignored) {}
        try { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return ZonedDateTime.parse(s).toInstant().toEpochMilli(); } catch (Exception ignored) {}
        try { return LocalDateTime.parse(s.replace(' ', 'T'), DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli(); }
        catch (Exception ignored) { return -1L; }
    }

    private static boolean isNepal(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon) && lat >= 26.2d && lat <= 30.5d && lon >= 80d && lon <= 88.35d;
    }

    private static double km(double a, double b, double c, double d) {
        if (!Double.isFinite(a) || !Double.isFinite(b) || !Double.isFinite(c) || !Double.isFinite(d)) return Double.NaN;
        double r = 6371d, dLat = Math.toRadians(c - a), dLon = Math.toRadians(d - b);
        double q = Math.sin(dLat / 2d) * Math.sin(dLat / 2d) + Math.cos(Math.toRadians(a)) * Math.cos(Math.toRadians(c)) * Math.sin(dLon / 2d) * Math.sin(dLon / 2d);
        return 2d * r * Math.asin(Math.sqrt(q));
    }

    private LinearLayout card() {
        LinearLayout v = new LinearLayout(this);
        v.setOrientation(LinearLayout.VERTICAL);
        v.setPadding(dp(16), dp(14), dp(16), dp(14));
        v.setBackground(round(Color.WHITE, 22, Color.rgb(203, 225, 236), 1));
        return v;
    }

    private TextView text(String s, float sp, boolean bold, int color) {
        TextView v = new TextView(this);
        v.setText(s); v.setTextSize(sp); v.setTextColor(color);
        if (bold) v.setTypeface(Typeface.DEFAULT_BOLD);
        return v;
    }

    private Button button(String s) {
        Button b = new Button(this);
        b.setText(s); b.setAllCaps(false); b.setTextSize(12); b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setTextColor(Color.rgb(21, 57, 80));
        b.setBackground(round(Color.WHITE, 16, Color.rgb(190, 218, 231), 1));
        return b;
    }

    private LinearLayout.LayoutParams weight() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -1, 1f);
        p.setMargins(dp(2), 0, dp(2), 0);
        return p;
    }

    private LinearLayout.LayoutParams margin(int w, int h, int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.setMargins(dp(l), dp(t), dp(r), dp(b));
        return p;
    }

    private GradientDrawable round(int color, int radius, int stroke, int sw) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color); g.setCornerRadius(dp(radius));
        if (sw > 0) g.setStroke(dp(sw), stroke);
        return g;
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    static final class LiveStation {
        final String name, district, stage;
        final double lat, lon, level, warning, danger, rainfallMm;
        final long at;
        final boolean fresh;
        final int rank;
        LiveStation(String name, String district, double lat, double lon, double level, double warning, double danger,
                    double rainfallMm, long at, boolean fresh, String stage, int rank) {
            this.name = name; this.district = district; this.lat = lat; this.lon = lon; this.level = level;
            this.warning = warning; this.danger = danger; this.rainfallMm = rainfallMm; this.at = at;
            this.fresh = fresh; this.stage = stage; this.rank = rank;
        }
    }

    static final class RainStation {
        final String name, status;
        final double lat, lon, rainfallMm;
        RainStation(String name, double lat, double lon, double rainfallMm, String status) {
            this.name = name; this.lat = lat; this.lon = lon; this.rainfallMm = rainfallMm; this.status = status == null ? "" : status;
        }
    }

    /** Weather-derived native cloud animation around the user's current monitored area. */
    private static final class CloudFieldView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Random random = new Random(7411L);
        private final List<Cloud> cloudList = new ArrayList<>();
        private float cloudCover;
        private long last = System.currentTimeMillis();

        CloudFieldView(Context context) {
            super(context);
            setWillNotDraw(false);
            for (int i = 0; i < 18; i++) cloudList.add(new Cloud(random.nextFloat(), random.nextFloat(), .06f + random.nextFloat() * .09f, .00002f + random.nextFloat() * .000045f));
        }

        void setCloudCover(float cover) {
            cloudCover = Math.max(0f, Math.min(100f, cover));
            invalidate();
        }

        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            long now = System.currentTimeMillis();
            float dt = Math.min(80f, now - last);
            last = now;
            int visible = Math.max(0, Math.min(cloudList.size(), Math.round(cloudList.size() * cloudCover / 100f)));
            paint.setColor(Color.argb((int) (35 + cloudCover * .65f), 245, 250, 255));
            for (int i = 0; i < visible; i++) {
                Cloud c = cloudList.get(i);
                c.x += c.speed * dt;
                if (c.x > 1.15f) c.x = -.15f;
                float x = c.x * getWidth(), y = c.y * getHeight(), r = c.size * getWidth();
                canvas.drawCircle(x, y, r * .42f, paint);
                canvas.drawCircle(x + r * .35f, y + r * .05f, r * .52f, paint);
                canvas.drawCircle(x - r * .34f, y + r * .10f, r * .34f, paint);
                canvas.drawOval(x - r * .62f, y + r * .08f, x + r * .82f, y + r * .62f, paint);
            }
            if (visible > 0) postInvalidateDelayed(45L);
        }

        private static final class Cloud {
            float x, y, size, speed;
            Cloud(float x, float y, float size, float speed) { this.x = x; this.y = y; this.size = size; this.speed = speed; }
        }
    }
}
