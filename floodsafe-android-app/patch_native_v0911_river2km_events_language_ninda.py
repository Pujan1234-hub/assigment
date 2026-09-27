from pathlib import Path
import re

JAVA = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app")
UI = JAVA / "NativeFullActivity.java"
RAIN = JAVA / "RainAlertWorker.java"
FAST = JAVA / "FloodLiveGaugeMonitor.java"
MATCHER = JAVA / "AffectedRiverAlertMatcher.java"
GRADLE = Path("floodsafe-android-app/app/build.gradle")

ui = UI.read_text(encoding="utf-8")
rain = RAIN.read_text(encoding="utf-8")
fast = FAST.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# v0.9.11 scope: ONLY the four user-requested fixes.
# 1) fast Warning/Danger alarm distance is to the affected SAME river geometry
# 2) 2-hour weather digest + distinct rain start/stop events
# 3) always-visible language control without Activity/map recreation
# 4) stale station detail must never say Normal when the last numeric reading
#    was above an official warning/danger threshold (Ninda screenshot case)
# -----------------------------------------------------------------------------

# ---- version -----------------------------------------------------------------
if "versionName '0.9.10-sathi-chat-map-labels'" not in g:
    raise SystemExit("v0.9.10 version anchor missing")
g = g.replace("versionCode 25", "versionCode 26", 1)
g = g.replace("versionName '0.9.10-sathi-chat-map-labels'", "versionName '0.9.11-river2km-events-language-ninda'", 1)

# ---- STEP 1: exact affected-river geometry matching for fast alerts ----------
matcher_java = r'''package io.github.pujan1234hub.floodsafe.app;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * V0911_AFFECTED_RIVER_2KM_MATCHER
 *
 * Safety-only matcher for emergency push decisions. A station is never used as
 * the user's distance target. We first prove the official station belongs to a
 * same-named bundled river geometry, then measure the user's distance to that
 * affected river geometry. If the same-river match is not safe, return NaN and
 * do not send an emergency alert.
 */
final class AffectedRiverAlertMatcher {
    private static final double MAX_STATION_TO_SAME_RIVER_KM = 8.0d;
    private static volatile List<RiverShape> cached;

    private AffectedRiverAlertMatcher() {}

    static double distanceToAffectedRiverKm(Context context,
                                            String riverName,
                                            String stationName,
                                            double stationLat,
                                            double stationLon,
                                            double userLat,
                                            double userLon) {
        if (context == null || !finiteNepal(stationLat, stationLon) || !finiteNepal(userLat, userLon)) {
            return Double.NaN;
        }
        String wanted = canonical(riverName);
        if (wanted.isEmpty()) wanted = canonical(riverFromStationTitle(stationName));
        if (wanted.isEmpty()) return Double.NaN;

        RiverShape best = null;
        double bestStationDistance = Double.POSITIVE_INFINITY;
        for (RiverShape shape : shapes(context.getApplicationContext())) {
            if (!shape.matches(wanted)) continue;
            double d = distanceToRiverKm(stationLat, stationLon, shape);
            if (Double.isFinite(d) && d <= MAX_STATION_TO_SAME_RIVER_KM && d < bestStationDistance) {
                best = shape;
                bestStationDistance = d;
            }
        }
        if (best == null) return Double.NaN; // no unrelated nearest-river fallback
        return distanceToRiverKm(userLat, userLon, best);
    }

    private static List<RiverShape> shapes(Context app) {
        List<RiverShape> ready = cached;
        if (ready != null) return ready;
        synchronized (AffectedRiverAlertMatcher.class) {
            ready = cached;
            if (ready != null) return ready;
            ArrayList<RiverShape> out = new ArrayList<>();
            try {
                String raw;
                try { raw = readAsset(app, "data/nepal-waterways-tiles/overview.json"); }
                catch (Exception e) { raw = readAsset(app, "data/nepal-waterways-snapshot.json"); }
                JSONArray ways = new JSONObject(raw).optJSONArray("waterways");
                if (ways != null) {
                    for (int i = 0; i < ways.length(); i++) {
                        JSONObject w = ways.optJSONObject(i);
                        if (w == null) continue;
                        JSONArray pts = w.optJSONArray("pts");
                        if (pts == null || pts.length() < 2) continue;
                        RiverShape shape = new RiverShape();
                        shape.addAlias(w.optString("name_en", ""));
                        shape.addAlias(w.optString("name", ""));
                        shape.addAlias(w.optString("name_ne", ""));
                        if (shape.keys.isEmpty()) continue;
                        for (int j = 0; j < pts.length(); j++) {
                            JSONArray p = pts.optJSONArray(j);
                            if (p == null || p.length() < 2) continue;
                            double lo = p.optDouble(0, Double.NaN);
                            double la = p.optDouble(1, Double.NaN);
                            if (finiteNepalLoose(la, lo)) shape.points.add(new double[]{lo, la});
                        }
                        if (shape.points.size() >= 2) out.add(shape);
                    }
                }
            } catch (Exception ignored) { }
            cached = out;
            return out;
        }
    }

    private static final class RiverShape {
        final List<String> keys = new ArrayList<>();
        final List<double[]> points = new ArrayList<>();
        void addAlias(String value) {
            String k = canonical(value);
            if (!k.isEmpty() && !keys.contains(k)) keys.add(k);
        }
        boolean matches(String wanted) {
            for (String k : keys) if (sameRiverKey(wanted, k)) return true;
            return false;
        }
    }

    private static String readAsset(Context app, String path) throws Exception {
        try (InputStream in = app.getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder b = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) b.append(line);
            return b.toString();
        }
    }

    private static String riverFromStationTitle(String value) {
        if (value == null) return "";
        String s = value.trim();
        String lower = s.toLowerCase(Locale.ROOT);
        int at = lower.indexOf(" at ");
        if (at > 0) s = s.substring(0, at);
        return s;
    }

    private static String canonical(String value) {
        String s = riverFromStationTitle(value).toLowerCase(Locale.ROOT);
        s = s.replace("river", "").replace("khola", "").replace("nadi", "")
                .replace("nadhi", "").replace("stream", "")
                .replace("नदी", "").replace("खोला", "");
        return s.replaceAll("[^a-z0-9\\p{L}]", "");
    }

    private static boolean sameRiverKey(String a, String b) {
        if (a == null || b == null || a.isEmpty() || b.isEmpty()) return false;
        if (a.equals(b)) return true;
        int min = Math.min(a.length(), b.length());
        return min >= 5 && (a.contains(b) || b.contains(a));
    }

    private static double distanceToRiverKm(double lat, double lon, RiverShape shape) {
        if (shape == null || shape.points.size() < 2) return Double.NaN;
        double best = Double.POSITIVE_INFINITY;
        for (int i = 0; i < shape.points.size() - 1; i++) {
            double[] a = shape.points.get(i), b = shape.points.get(i + 1);
            best = Math.min(best, pointSegmentKm(lat, lon, a[1], a[0], b[1], b[0]));
        }
        return best;
    }

    private static double pointSegmentKm(double lat, double lon,
                                         double lat1, double lon1,
                                         double lat2, double lon2) {
        double cos = Math.max(0.20d, Math.cos(Math.toRadians(lat)));
        double x1 = (lon1 - lon) * 111.320d * cos;
        double y1 = (lat1 - lat) * 110.574d;
        double x2 = (lon2 - lon) * 111.320d * cos;
        double y2 = (lat2 - lat) * 110.574d;
        double dx = x2 - x1, dy = y2 - y1;
        double len2 = dx * dx + dy * dy;
        double t = len2 <= 1e-12d ? 0d : -(x1 * dx + y1 * dy) / len2;
        t = Math.max(0d, Math.min(1d, t));
        double x = x1 + t * dx, y = y1 + t * dy;
        return Math.sqrt(x * x + y * y);
    }

    private static boolean finiteNepal(double la, double lo) {
        return Double.isFinite(la) && Double.isFinite(lo)
                && la >= 26.2d && la <= 30.5d && lo >= 80.0d && lo <= 88.35d;
    }

    private static boolean finiteNepalLoose(double la, double lo) {
        return Double.isFinite(la) && Double.isFinite(lo)
                && la >= 25.5d && la <= 31.2d && lo >= 79.2d && lo <= 89.0d;
    }
}
'''
MATCHER.write_text(matcher_java, encoding="utf-8")

old_fast_distance = 'JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");double[] p=coord(row,f);double la=p[0],lo=p[1];double distance=haversineKm(homeLat,homeLon,la,lo);if(!insideNepal(la,lo)||distance>RADIUS_KM)continue;'
new_fast_distance = 'JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");double[] p=coord(row,f);double la=p[0],lo=p[1];if(!insideNepal(la,lo))continue;'
if old_fast_distance not in fast:
    raise SystemExit("fast station-dot distance anchor missing")
fast = fast.replace(old_fast_distance, new_fast_distance, 1)

old_identity = 'String id=str(row,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),name=str(row,f,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official hydrology station";if(id.isEmpty())id=name+"@"+String.format(Locale.US,"%.5f,%.5f",la,lo);'
new_identity = '''String id=str(row,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),stationName=str(row,f,"station_name","stationName","title","name"),riverName=str(row,f,"river_name","riverName","river");String name=!riverName.isEmpty()?riverName:stationName;if(name.isEmpty())name="Official hydrology station";if(id.isEmpty())id=name+"@"+String.format(Locale.US,"%.5f,%.5f",la,lo);double distance=AffectedRiverAlertMatcher.distanceToAffectedRiverKm(app,riverName,stationName,la,lo,homeLat,homeLon);if(!Double.isFinite(distance)||distance>RADIUS_KM)continue; // V0911_FAST_ALERT_USES_AFFECTED_RIVER_GEOMETRY'''
if old_identity not in fast:
    raise SystemExit("fast station identity anchor missing")
fast = fast.replace(old_identity, new_identity, 1)

# ---- STEP 2: weather notifications -------------------------------------------
# v0.9.08 already changed the digest to 2h. Make that contract explicit and fail
# the build instead of silently regressing it.
if 'private static final long WEATHER_DIGEST_INTERVAL_MS = 2L * 60L * 60L * 1000L;' not in rain:
    raise SystemExit("2-hour weather digest contract missing")

old_state = '''            boolean rainStateKnown = prefs.contains("last_raining_state");
            boolean wasRaining = prefs.getBoolean("last_raining_state", false);
            if (rainStateKnown && wasRaining && !rainingNow) {
                notifyWeatherEvent(7111, "🌤️ वर्षा रोकिएको देखिन्छ",
                        "हालको weather model मा वर्षा रोकिएको छ • अहिले " + oneDecimal(current) + " mm।");
            }
            prefs.edit().putBoolean("last_raining_state", rainingNow).apply();'''
new_state = '''            boolean rainStateKnown = prefs.contains("last_raining_state");
            boolean wasRaining = prefs.getBoolean("last_raining_state", false);
            boolean rainStartedNow = rainStateKnown && !wasRaining && rainingNow;
            boolean rainStoppedNow = rainStateKnown && wasRaining && !rainingNow;
            if (rainStartedNow) {
                notifyWeatherEvent(7110, "🌧️ वर्षा सुरु भएको देखिन्छ",
                        "हालको weather model अनुसार तपाईंको स्थानमा वर्षा सुरु भएको छ • अहिले " + oneDecimal(current) + " mm।");
            }
            if (rainStoppedNow) {
                notifyWeatherEvent(7111, "🌤️ वर्षा रोकिएको देखिन्छ",
                        "हालको weather model मा वर्षा रोकिएको छ • अहिले " + oneDecimal(current) + " mm।");
            }
            prefs.edit().putBoolean("last_raining_state", rainingNow).apply(); // V0911_RAIN_START_STOP_EVENTS'''
if old_state not in rain:
    raise SystemExit("rain state transition anchor missing")
rain = rain.replace(old_state, new_state, 1)

# The transition notification above is the single start event. Keep the existing
# forecast/lead notification, but avoid a duplicate at the exact start transition.
old_notify = '            notifyRain(rainingNow, lead, event, nextHour, temperature, humidity, wind, zone);'
new_notify = '            if (!rainStartedNow) notifyRain(rainingNow, lead, event, nextHour, temperature, humidity, wind, zone); // V0911_NO_DUPLICATE_RAIN_START'
if old_notify not in rain:
    raise SystemExit("notifyRain anchor missing")
rain = rain.replace(old_notify, new_notify, 1)

# ---- STEP 3: always-visible language toggle, no map/activity restart ----------
field_anchor = '    private FloodSafeNativeMapView map;'
if field_anchor not in ui:
    raise SystemExit("map field anchor missing")
ui = ui.replace(field_anchor, field_anchor + '\n    private Button quickLang; // V0911_ALWAYS_VISIBLE_LANGUAGE', 1)

sathi_anchor = 'Button sathi=button("🤖 SATHI");sathi.setTextSize(13);sathi.setOnClickListener(v->showSathiDialog(null));FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(dp(104),dp(48),Gravity.END|Gravity.BOTTOM);fp.setMargins(0,0,dp(18),dp(82));root.addView(sathi,fp);'
if sathi_anchor not in ui:
    raise SystemExit("SATHI floating button anchor missing")
quick = sathi_anchor + 'quickLang=button(english?"🌐 नेपाली":"🌐 EN");quickLang.setTextSize(11);quickLang.setOnClickListener(v->langBtn.performClick());FrameLayout.LayoutParams qlp=new FrameLayout.LayoutParams(dp(92),dp(48),Gravity.START|Gravity.BOTTOM);qlp.setMargins(dp(18),0,0,dp(82));root.addView(quickLang,qlp); // V0911_LANGUAGE_BUTTON_PERSISTENT'
ui = ui.replace(sathi_anchor, quick, 1)

lang_anchor = 'langBtn.setText(t("अङ्ग्रेजी","नेपाली"));'
if lang_anchor not in ui:
    raise SystemExit("language label anchor missing")
ui = ui.replace(lang_anchor, lang_anchor + 'if(quickLang!=null)quickLang.setText(english?"🌐 नेपाली":"🌐 EN");', 1)

# ---- STEP 4: Ninda / threshold-safe station detail ----------------------------
# Do not turn stale measurements into live emergency states. Instead, never call
# a stale threshold-crossing measurement "Normal": label it historical and state
# what the last official numeric reading was relative to the official thresholds.
show_pattern = re.compile(
    r'(private void showStation\(RiverStation s\)\{\s*StringBuilder b=new StringBuilder\(\);\s*)'
    r'b\.append\(s\.fresh\?stageDot\(s\.stage\)\+" "\+stageName\(s\.stage\):"⚪ "\+t\("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading"\)\);'
)
replacement = r'''\1b.append(stationDialogStatus(s));'''
ui, count = show_pattern.subn(replacement, ui, count=1)
if count != 1:
    raise SystemExit(f"showStation status anchor expected once, got {count}")

helper_anchor = '    private void showStation(RiverStation s){'
helper = r'''    private String stationDialogStatus(RiverStation s){
        boolean aboveDanger=Double.isFinite(s.level)&&Double.isFinite(s.danger)&&s.danger>0d&&s.level>=s.danger;
        boolean aboveWarning=Double.isFinite(s.level)&&Double.isFinite(s.warning)&&s.warning>0d&&s.level>=s.warning;
        if(s.fresh){
            if(aboveDanger)return "🔴 "+t("खतरा","DANGER");
            if(aboveWarning)return "🟠 "+t("चेतावनी","WARNING");
            return stageDot(s.stage)+" "+stageName(s.stage);
        }
        if(aboveDanger)return "⚪ "+t("पुरानो reading • पछिल्लो मापन खतरा स्तर माथि थियो","STALE reading • last measurement was above the danger level");
        if(aboveWarning)return "⚪ "+t("पुरानो reading • पछिल्लो मापन चेतावनी स्तर माथि थियो","STALE reading • last measurement was above the warning level");
        return "⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading");
    } // V0911_NINDA_THRESHOLD_SAFE_DISPLAY

'''
if helper_anchor not in ui:
    raise SystemExit("showStation helper insertion anchor missing")
ui = ui.replace(helper_anchor, helper + helper_anchor, 1)

# Parser safety invariant: when a reading is fresh, numeric danger threshold wins
# over warning/normal. This is what Ninda's BIPAD-provided 122.50 danger threshold
# requires; threshold values are not swapped or invented.
if 'danger>0&&level>=danger' not in ui:
    raise SystemExit("fresh numeric danger threshold invariant missing")

UI.write_text(ui, encoding="utf-8")
RAIN.write_text(rain, encoding="utf-8")
FAST.write_text(fast, encoding="utf-8")
GRADLE.write_text(g, encoding="utf-8")

print("V0911_RIVER_2KM_EVENTS_LANGUAGE_NINDA_OK")
