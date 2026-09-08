package io.github.pujan1234hub.floodsafe.sathi;

import android.content.Context;
import android.content.SharedPreferences;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;
import org.json.JSONArray;
import org.json.JSONObject;

final class NativeDataAnswerer {
    private NativeDataAnswerer() {}

    private static final String RIVERS = "https://bipadportal.gov.np/api/v1/river-stations/?latest=true&limit=2000";

    static String answer(Context context, String question) {
        String q = norm(question);
        if (q.isBlank()) return "कृपया बाढी, नदी, खोला वा वर्षाबारे प्रश्न सोध्नुहोस्।";

        String k = knowledge(q);
        if (k != null) return k;

        if (isWeather(q)) return weather(context, q);
        return river(q);
    }

    private static boolean isWeather(String q) {
        return has(q, "पानी", "वर्षा", "rain", "pani", "barsha", "barsa", "कति बजे", "kati baje", "रोकिन", "rok", "मौसम", "weather");
    }

    private static String knowledge(String q) {
        if (has(q, "बाढी भनेको", "what is flood", "flood vaneko", "badi vaneko", "बाढी के हो"))
            return "बाढी भनेको नदी, खोला वा वर्षाको पानी सामान्य सीमाभन्दा बढेर बस्ती, खेत, सडक वा अन्य भूभागमा फैलिने अवस्था हो। नदीको जलस्तर, वर्षा, भू-आकृति र निकासको अवस्था अनुसार जोखिम फरक हुन्छ।";
        if (has(q, "किन आउ", "कारण", "cause", "kina aau", "kina auxa"))
            return "बाढीका मुख्य कारणमा धेरै वा लगातार वर्षा, नदीको बहाव अचानक बढ्नु, पहिरोले नदी थुनिनु, हिमताल वा बाँध फुट्नु, निकास बन्द हुनु र कमजोर भू-व्यवस्थापन पर्छन्। जोखिम हेर्दा स्थानीय आधिकारिक चेतावनीलाई प्राथमिकता दिनुहोस्।";
        if (has(q, "बाढी आए", "बाढी आयो", "के गर्ने", "k garne", "ke garne", "safe", "सुरक्षा", "bachne", "बच्ने"))
            return "⚠️ बाढीको जोखिम हुँदा नदी/खोला किनारबाट तुरुन्त टाढा जानुहोस्, तल्लो ठाउँ छोडेर उचाइतिर जानुहोस्, बिजुलीको मुख्य स्विच सुरक्षित रूपमा बन्द गर्न मिल्छ भने मात्र बन्द गर्नुहोस्, बगिरहेको पानीमा पैदल वा सवारी लिएर नछिर्नुहोस्, र स्थानीय प्रशासन/सुरक्षा निकायको निर्देशन पालना गर्नुहोस्।";
        if (has(q, "गाडी", "car", "bike", "सवारी", "drive"))
            return "🚗 बाढीको पानीले ढाकेको सडकमा गाडी नचलाउनुहोस्। पानीको गहिराइ र सडकको अवस्था आँखाले ठ्याक्कै थाहा हुँदैन, बहावले सवारी बगाउन सक्छ। सुरक्षित वैकल्पिक मार्ग वा आधिकारिक ट्राफिक निर्देशन प्रयोग गर्नुहोस्।";
        if (has(q, "बिजुली", "electric", "current", "करन्ट"))
            return "⚡ बाढीको पानी नजिक बिजुलीको तार, पोल, इनभर्टर, जनरेटर वा भिजेको स्विच नछुनुहोस्। पानी घरमा पस्दैछ र मुख्य स्विच सुरक्षित स्थानबाट बन्द गर्न सकिन्छ भने मात्र बन्द गर्नुहोस्। शंका भए विद्युत् निकाय वा आपतकालीन सेवाको सहायता लिनुहोस्।";
        if (has(q, "पिउने पानी", "drinking water", "खानेपानी", "पानी पिउ"))
            return "🥤 बाढीपछि दूषित पानी नपिउनुहोस्। सुरक्षित बोतलको पानी वा आधिकारिक रूपमा सुरक्षित भनिएको पानी प्रयोग गर्नुहोस्। आवश्यक परे पानी उमालेर प्रयोग गर्नुहोस् र खुला/दूषित खाद्य सामग्री नखानुहोस्।";
        if (has(q, "बच्चा", "बालबालिका", "child", "elder", "वृद्ध", "अपाङ्ग", "disabled"))
            return "👨‍👩‍👧 बाढीको जोखिममा बालबालिका, वृद्ध, गर्भवती, बिरामी र अपाङ्ग व्यक्तिलाई पहिला सुरक्षित उचाइतिर सार्नुहोस्। परिवारको भेट्ने स्थान र आपतकालीन सम्पर्क पहिले नै तय गर्नु राम्रो हुन्छ।";
        if (has(q, "पशु", "livestock", "गाई", "भैंसी", "बाख्रा"))
            return "🐄 पशुचौपायालाई सम्भव भएसम्म बाढी आउनुअघि उचाइ र सुरक्षित खुला स्थानतिर सार्नुहोस्। मान्छेको ज्यान जोखिममा पारेर पशु बचाउन बगिरहेको पानीमा नछिर्नुहोस्।";
        if (has(q, "warning", "चेतावनी तह", "danger level", "खतरा तह", "जलस्तर के"))
            return "नदीको ‘चेतावनी तह’ पुगेपछि सतर्कता बढाउनुपर्छ। ‘खतरा तह’ पुगे वा नाघेपछि जोखिम उच्च मानिन्छ र स्थानीय निकासी/सुरक्षा निर्देशन तुरुन्त पालना गर्नुपर्छ। SATHI ले उपलब्ध आधिकारिक BIPAD/DHM मापनबाट अहिलेको अवस्था बताउँछ।";
        return null;
    }

    private static String weather(Context context, String q) {
        SharedPreferences p = context.getSharedPreferences(WakeWordService.PREFS, Context.MODE_PRIVATE);
        if (!p.contains("monitor_lat") || !p.contains("monitor_lon")) {
            return "🌦️ वर्षाको समय बताउन पहिले FloodSafe Nepal खोल्नुहोस् र नेपालभित्र आफ्नो निगरानी स्थान छान्नुहोस्। त्यसपछि ‘Ye Sathi’ बाट पनि सोध्न सक्नुहुन्छ।";
        }
        double lat = Double.longBitsToDouble(p.getLong("monitor_lat", 0));
        double lon = Double.longBitsToDouble(p.getLong("monitor_lon", 0));
        String label = p.getString("monitor_label", "छानिएको क्षेत्र");
        try {
            String u = "https://api.open-meteo.com/v1/forecast?latitude=" + lat + "&longitude=" + lon
                    + "&current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m"
                    + "&hourly=precipitation,rain,showers&timezone=Asia%2FKathmandu&timeformat=unixtime&forecast_days=2";
            JSONObject j = getJson(u);
            JSONObject current = j.optJSONObject("current");
            double nowRain = current == null ? 0 : Math.max(current.optDouble("precipitation", 0), current.optDouble("rain", 0));
            JSONArray times = j.optJSONObject("hourly") == null ? null : j.optJSONObject("hourly").optJSONArray("time");
            JSONObject hourly = j.optJSONObject("hourly");
            JSONArray precipitation = hourly == null ? null : hourly.optJSONArray("precipitation");
            JSONArray rain = hourly == null ? null : hourly.optJSONArray("rain");
            JSONArray showers = hourly == null ? null : hourly.optJSONArray("showers");
            long now = System.currentTimeMillis();
            Long start = null, stop = null;
            boolean wet = nowRain >= 0.2;
            boolean sawWet = wet;
            if (times != null) {
                for (int i = 0; i < times.length(); i++) {
                    long t = times.optLong(i, 0) * 1000L;
                    if (t <= now) continue;
                    double amount = Math.max(valueAt(precipitation, i), Math.max(valueAt(rain, i), valueAt(showers, i)));
                    boolean w = amount >= 0.2;
                    if (w && !sawWet) {
                        start = t;
                        sawWet = true;
                    } else if (!w && sawWet) {
                        stop = t;
                        break;
                    }
                }
            }
            List<String> out = new ArrayList<>();
            out.add("🌦️ " + (label == null || label.isBlank() ? "छानिएको क्षेत्र" : label) + "को पूर्वानुमान अनुसार");
            if (wet) out.add("अहिले वर्षा देखिएको छ");
            else out.add("अहिले वर्षा देखिएको छैन");
            if (start != null) {
                long mins = Math.max(0, (start - now + 59999) / 60000);
                out.add("वर्षा करिब " + time(start) + " बाट सुरु हुने अनुमान छ (करिब " + mins + " मिनेटपछि)");
            } else if (!wet) out.add("हालको पूर्वानुमानमा नजिकै वर्षा सुरु हुने स्पष्ट समय छैन");
            if (stop != null) out.add("र करिब " + time(stop) + " तिर रोकिने अनुमान छ");
            else if (wet || start != null) out.add("रोकिने समय अहिले स्पष्ट छैन");
            out.add("यो मौसम पूर्वानुमान हो, पक्का स्थानीय मापन होइन।");
            return String.join("। ", out);
        } catch (Exception e) {
            return "🌦️ ताजा मौसम पूर्वानुमान अहिले पढ्न सकिएन। केही क्षणपछि फेरि सोध्नुहोस्।";
        }
    }

    private static String river(String q) {
        try {
            JSONObject j = getJson(RIVERS);
            JSONArray rows = rows(j);
            if (rows == null || rows.length() == 0) return "अहिले BIPAD/DHM को ताजा नदी मापन उपलब्ध छैन। पुरानो डेटा अनुमान गरेर देखाइएको छैन।";
            List<River> rivers = new ArrayList<>();
            for (int i = 0; i < rows.length(); i++) {
                JSONObject raw = rows.optJSONObject(i);
                if (raw == null) continue;
                JSONObject o = flatten(raw);
                River r = parseRiver(o);
                if (r != null) rivers.add(r);
            }
            String target = targetRiver(q);
            if (target != null) {
                River best = findTarget(rivers, target);
                if (best == null) return "त्यो नदी/खोलाको ताजा आधिकारिक स्टेशन मापन अहिले भेटिएन। नाम फरक स्टेशनमा दर्ता भएको हुन सक्छ।";
                return riverLine(best, true);
            }
            List<River> risk = new ArrayList<>();
            for (River r : rivers) if (r.stage >= 1) risk.add(r);
            Collections.sort(risk, (a, b) -> Integer.compare(b.stage, a.stage));
            if (risk.isEmpty()) return "अहिले उपलब्ध ताजा आधिकारिक नदी मापनमा चेतावनी वा खतरा तहमा पुगेको स्टेशन भेटिएन। नदी नजिक हुँदा स्थानीय अवस्था र आधिकारिक सूचनामा ध्यान दिनुहोस्।";
            StringBuilder b = new StringBuilder("अहिले जोखिम देखिएका नदी/खोला स्टेशन: ");
            int n = Math.min(5, risk.size());
            for (int i = 0; i < n; i++) {
                if (i > 0) b.append("; ");
                b.append(riverLine(risk.get(i), false));
            }
            if (risk.size() > n) b.append("। थप ").append(risk.size() - n).append(" स्टेशन पनि निगरानीमा छन्");
            return b.toString();
        } catch (Exception e) {
            return "अहिले आधिकारिक नदी डेटा पढ्न सकिएन। केही क्षणपछि फेरि सोध्नुहोस्।";
        }
    }

    private static String riverLine(River r, boolean detail) {
        String st = r.stage >= 2 ? "🔴 खतरा" : r.stage == 1 ? "🟠 चेतावनी" : "🟢 सामान्य";
        StringBuilder b = new StringBuilder(r.name).append(" — ").append(st);
        if (Double.isFinite(r.level)) b.append(", जलस्तर ").append(fmt(r.level)).append(" मिटर");
        if (detail && Double.isFinite(r.warning)) b.append(", चेतावनी तह ").append(fmt(r.warning)).append(" मिटर");
        if (detail && Double.isFinite(r.danger)) b.append(", खतरा तह ").append(fmt(r.danger)).append(" मिटर");
        if (detail && r.time != null && !r.time.isBlank()) b.append("। आधिकारिक मापन समय ").append(r.time);
        if (detail && r.stage >= 2) b.append("। नदी किनार र तल्लो क्षेत्रमा नजानुहोस् र स्थानीय निकासी निर्देशन पालना गर्नुहोस्");
        else if (detail && r.stage == 1) b.append("। सतर्क रहनुहोस् र सुरक्षित स्थानतिर सर्ने तयारी गर्नुहोस्");
        return b.toString();
    }

    private static River findTarget(List<River> rows, String target) {
        River best = null;
        int score = -1;
        for (River r : rows) {
            String n = norm(r.name);
            int s = n.contains(target) ? 100 : 0;
            if (s == 0) {
                for (String t : target.split(" ")) if (t.length() >= 3 && n.contains(t)) s += t.length();
            }
            if (s > score) { score = s; best = r; }
        }
        return score > 0 ? best : null;
    }

    private static String targetRiver(String q) {
        Map<String, String> m = new HashMap<>();
        m.put("कोशी", "koshi"); m.put("कोसी", "koshi"); m.put("koshi", "koshi"); m.put("kosi", "koshi");
        m.put("कर्णाली", "karnali"); m.put("karnali", "karnali");
        m.put("गण्डकी", "gandaki"); m.put("gandaki", "gandaki");
        m.put("नारायणी", "narayani"); m.put("narayani", "narayani");
        m.put("बागमती", "bagmati"); m.put("bagmati", "bagmati");
        m.put("राप्ती", "rapti"); m.put("rapti", "rapti");
        m.put("महाकाली", "mahakali"); m.put("mahakali", "mahakali");
        for (Map.Entry<String, String> e : m.entrySet()) if (q.contains(norm(e.getKey()))) return e.getValue();
        return null;
    }

    private static River parseRiver(JSONObject o) {
        String name = str(o, "river_name", "riverName", "station_name", "stationName", "title", "name");
        if (name == null || name.isBlank()) name = "अज्ञात नदी स्टेशन";
        double level = dbl(o, "_lastWaterLevel", "waterLevel", "water_level", "currentWaterLevel", "current_water_level", "currentLevel", "level", "value");
        double warning = dbl(o, "_lastWarningLevel", "warningLevel", "warning_level", "warningThreshold", "warning_threshold");
        double danger = dbl(o, "_lastDangerLevel", "dangerLevel", "danger_level", "dangerThreshold", "danger_threshold");
        String raw = str(o, "_officialStatus", "status", "status_name", "alertStatus", "alert_status", "riskLevel", "risk_level");
        int stage = 0;
        String s = raw == null ? "" : raw.toLowerCase(Locale.ROOT);
        if ((Double.isFinite(level) && Double.isFinite(danger) && danger > 0 && level >= danger) || s.contains("danger") || s.contains("red")) stage = 2;
        else if ((Double.isFinite(level) && Double.isFinite(warning) && warning > 0 && level >= warning) || s.contains("warning") || s.contains("orange")) stage = 1;
        String t = str(o, "_measurementTime", "waterLevelOn", "water_level_on", "measuredOn", "measured_on", "measurementTime", "measurement_time", "observationTime", "timestamp");
        return new River(name, level, warning, danger, stage, t);
    }

    private static JSONObject flatten(JSONObject raw) {
        JSONObject fields = raw.optJSONObject("fields");
        if (fields == null) return raw;
        JSONObject out = new JSONObject();
        for (String k : fields.keySet()) try { out.put(k, fields.get(k)); } catch (Exception ignored) {}
        for (String k : raw.keySet()) try { out.put(k, raw.get(k)); } catch (Exception ignored) {}
        return out;
    }

    private static JSONArray rows(JSONObject j) {
        JSONArray a = j.optJSONArray("results");
        if (a != null) return a;
        a = j.optJSONArray("data");
        if (a != null) return a;
        JSONObject d = j.optJSONObject("data");
        return d == null ? null : d.optJSONArray("results");
    }

    private static JSONObject getJson(String address) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(address).openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(15000);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("User-Agent", "FloodSafe-SATHI/1.0");
        try {
            int code = c.getResponseCode();
            if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code);
            StringBuilder b = new StringBuilder();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream()))) {
                for (String line; (line = r.readLine()) != null;) b.append(line);
            }
            return new JSONObject(b.toString());
        } finally { c.disconnect(); }
    }

    private static String str(JSONObject o, String... keys) {
        for (String k : keys) {
            Object v = o.opt(k);
            if (v != null && v != JSONObject.NULL && !String.valueOf(v).isBlank()) return String.valueOf(v);
        }
        return null;
    }

    private static double dbl(JSONObject o, String... keys) {
        for (String k : keys) {
            Object v = o.opt(k);
            if (v == null || v == JSONObject.NULL) continue;
            try { return Double.parseDouble(String.valueOf(v)); } catch (Exception ignored) {}
        }
        return Double.NaN;
    }

    private static double valueAt(JSONArray a, int i) {
        if (a == null || i < 0 || i >= a.length()) return 0;
        return a.optDouble(i, 0);
    }

    private static String fmt(double n) { return String.format(Locale.US, "%.2f", n); }

    private static String time(long ms) {
        SimpleDateFormat f = new SimpleDateFormat("HH:mm", Locale.US);
        f.setTimeZone(TimeZone.getTimeZone("Asia/Kathmandu"));
        return f.format(new Date(ms));
    }

    private static boolean has(String q, String... words) {
        for (String w : words) if (q.contains(norm(w))) return true;
        return false;
    }

    private static String norm(String s) {
        if (s == null) return "";
        return s.toLowerCase(Locale.ROOT).replaceAll("[\\p{Punct}]", " ").replaceAll("\\s+", " ").trim();
    }

    private record River(String name, double level, double warning, double danger, int stage, String time) {}
}
