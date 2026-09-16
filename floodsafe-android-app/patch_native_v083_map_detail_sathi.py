from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path = src / 'FloodSafeNativeMapView.java'
activity_path = src / 'NativeFullActivity.java'
gradle_path = root / 'app/build.gradle'

if not map_path.is_file() or not activity_path.is_file():
    raise SystemExit('v0.8.3 native sources missing')

m = map_path.read_text(encoding='utf-8')

# Native text labels for Nepal districts and exact official station coordinates.
if 'import org.maplibre.android.style.layers.SymbolLayer;' not in m:
    m = m.replace('import org.maplibre.android.style.layers.LineLayer;\n',
                  'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.layers.SymbolLayer;\n', 1)
for imp in [
    'import static org.maplibre.android.style.layers.PropertyFactory.textAllowOverlap;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textColor;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textField;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textHaloColor;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textHaloWidth;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textSize;\n',
]:
    if imp not in m:
        anchor = 'import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\n'
        if anchor not in m:
            raise SystemExit('MapLibre PropertyFactory import anchor missing')
        m = m.replace(anchor, anchor + imp, 1)

field_anchor = '    private final List<RiverWay> rivers = new ArrayList<>();\n'
if 'private final List<NepalRing> nepalRings' not in m:
    if field_anchor not in m:
        raise SystemExit('River list field anchor missing')
    m = m.replace(field_anchor, field_anchor + '    private final List<NepalRing> nepalRings = new ArrayList<>();\n', 1)
if 'private String districtLabelsGeoJson' not in m:
    m = m.replace('    private String districtGeoJson = null;\n',
                  '    private String districtGeoJson = null;\n    private String districtLabelsGeoJson = null;\n', 1)

# Build an exact Nepal union from the 77 district polygons before river geometry.
district_anchor = '''            try {\n                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");\n            } catch (Exception ignored) {\n                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}\n            }\n            try {\n'''
if 'buildNepalRings(districtGeoJson);' not in m:
    if district_anchor not in m:
        raise SystemExit('District load anchor missing')
    m = m.replace(district_anchor, '''            try {\n                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");\n            } catch (Exception ignored) {\n                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}\n            }\n            if (districtGeoJson != null) {\n                try {\n                    buildNepalRings(districtGeoJson);\n                    districtLabelsGeoJson = makeDistrictLabelsGeoJson(districtGeoJson);\n                } catch (Exception ignored) {}\n            }\n            try {\n''', 1)

old_river = '''                        RiverWay rw = new RiverWay();\n                        rw.name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");\n                        rw.type = w.optString("type", "stream");\n                        for (int j = 0; j < pts.length(); j++) {\n                            JSONArray p = pts.optJSONArray(j);\n                            if (p == null || p.length() < 2) continue;\n                            double lo = p.optDouble(0, Double.NaN), la = p.optDouble(1, Double.NaN);\n                            if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo)) rw.points.add(new double[]{lo, la});\n                        }\n                        if (rw.points.size() >= 2) all.add(rw);\n'''
new_river = '''                        String riverName = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"), "नदी / खोला");\n                        String riverType = w.optString("type", "stream");\n                        List<double[]> segment = new ArrayList<>();\n                        for (int j = 0; j < pts.length(); j++) {\n                            JSONArray p = pts.optJSONArray(j);\n                            if (p == null || p.length() < 2) continue;\n                            double lo = p.optDouble(0, Double.NaN), la = p.optDouble(1, Double.NaN);\n                            boolean inside = Double.isFinite(la) && Double.isFinite(lo) && isInsideNepal(la, lo);\n                            if (inside) {\n                                segment.add(new double[]{lo, la});\n                            } else {\n                                addRiverSegment(all, riverName, riverType, segment);\n                                segment = new ArrayList<>();\n                            }\n                        }\n                        addRiverSegment(all, riverName, riverType, segment);\n'''
if old_river in m:
    m = m.replace(old_river, new_river, 1)
elif 'boolean inside = Double.isFinite(la) && Double.isFinite(lo) && isInsideNepal(la, lo);' not in m:
    raise SystemExit('River clipping anchor missing')

# District-name layer: labels are generated from the actual district geometry centres.
district_layer_anchor = '''                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(\n                        lineColor("#e8fbff"), lineWidth(1.15f), lineOpacity(0.82f), lineJoin(LINE_JOIN_ROUND)));\n            }\n'''
if 'fs-district-labels-layer' not in m:
    if district_layer_anchor not in m:
        raise SystemExit('District layer anchor missing')
    m = m.replace(district_layer_anchor, district_layer_anchor + '''            if (districtLabelsGeoJson != null && style.getSource("fs-district-labels") == null) {\n                style.addSource(new GeoJsonSource("fs-district-labels", districtLabelsGeoJson));\n                SymbolLayer districtLabels = new SymbolLayer("fs-district-labels-layer", "fs-district-labels").withProperties(\n                        textField("{name}"), textSize(10.5f), textColor("#f4fdff"),\n                        textHaloColor("#183846"), textHaloWidth(1.4f), textAllowOverlap(false));\n                districtLabels.setMinZoom(5.15f);\n                style.addLayer(districtLabels);\n            }\n''', 1)

# Station labels appear when zooming in; dots remain at their exact feed lat/lon at every zoom.
station_anchor = '            ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f);\n'
if 'fs-station-labels-layer' not in m:
    if station_anchor not in m:
        raise SystemExit('Station source anchor missing')
    m = m.replace(station_anchor, station_anchor + '''            if (style.getSource("fs-station-labels") == null) {\n                style.addSource(new GeoJsonSource("fs-station-labels", emptyFeatureCollection()));\n                SymbolLayer stationLabels = new SymbolLayer("fs-station-labels-layer", "fs-station-labels").withProperties(\n                        textField("{name}"), textSize(10.0f), textColor("#ffffff"),\n                        textHaloColor("#26353d"), textHaloWidth(1.5f), textAllowOverlap(false));\n                stationLabels.setMinZoom(8.0f);\n                style.addLayer(stationLabels);\n            }\n''', 1)

refresh_anchor = '        setGeo("fs-danger", stationGeo(snapshot, "danger"));\n'
if 'setGeo("fs-station-labels", stationLabelsGeo(snapshot));' not in m:
    if refresh_anchor not in m:
        raise SystemExit('Station refresh anchor missing')
    m = m.replace(refresh_anchor, refresh_anchor + '        setGeo("fs-station-labels", stationLabelsGeo(snapshot));\n', 1)

helper_anchor = '    private static String makeRiversGeoJson(List<RiverWay> ways) throws Exception {\n'
helpers = r'''    private void buildNepalRings(String raw) throws Exception {
        nepalRings.clear();
        JSONObject root = new JSONObject(raw);
        JSONArray features = root.optJSONArray("features");
        if (features == null) return;
        for (int i = 0; i < features.length(); i++) {
            JSONObject f = features.optJSONObject(i);
            JSONObject g = f == null ? null : f.optJSONObject("geometry");
            if (g == null) continue;
            String type = g.optString("type");
            JSONArray coords = g.optJSONArray("coordinates");
            if (coords == null) continue;
            if ("Polygon".equals(type)) {
                addOuterRing(coords.optJSONArray(0));
            } else if ("MultiPolygon".equals(type)) {
                for (int p = 0; p < coords.length(); p++) {
                    JSONArray poly = coords.optJSONArray(p);
                    if (poly != null) addOuterRing(poly.optJSONArray(0));
                }
            }
        }
    }

    private void addOuterRing(JSONArray ring) {
        if (ring == null || ring.length() < 3) return;
        NepalRing out = new NepalRing();
        for (int i = 0; i < ring.length(); i++) {
            JSONArray p = ring.optJSONArray(i);
            if (p == null || p.length() < 2) continue;
            double lo = p.optDouble(0, Double.NaN), la = p.optDouble(1, Double.NaN);
            if (!Double.isFinite(la) || !Double.isFinite(lo)) continue;
            out.points.add(new double[]{lo, la});
            out.minLon = Math.min(out.minLon, lo); out.maxLon = Math.max(out.maxLon, lo);
            out.minLat = Math.min(out.minLat, la); out.maxLat = Math.max(out.maxLat, la);
        }
        if (out.points.size() >= 3) nepalRings.add(out);
    }

    private boolean isInsideNepal(double la, double lo) {
        if (la < NEPAL_MIN_LAT || la > NEPAL_MAX_LAT || lo < NEPAL_MIN_LON || lo > NEPAL_MAX_LON) return false;
        if (nepalRings.isEmpty()) return true;
        for (NepalRing r : nepalRings) {
            if (lo < r.minLon || lo > r.maxLon || la < r.minLat || la > r.maxLat) continue;
            if (pointInRing(lo, la, r.points)) return true;
        }
        return false;
    }

    private static boolean pointInRing(double x, double y, List<double[]> ring) {
        boolean inside = false;
        for (int i = 0, j = ring.size() - 1; i < ring.size(); j = i++) {
            double[] a = ring.get(i), b = ring.get(j);
            boolean crosses = ((a[1] > y) != (b[1] > y)) &&
                    (x < (b[0] - a[0]) * (y - a[1]) / ((b[1] - a[1]) == 0 ? 1e-12 : (b[1] - a[1])) + a[0]);
            if (crosses) inside = !inside;
        }
        return inside;
    }

    private static void addRiverSegment(List<RiverWay> all, String name, String type, List<double[]> segment) {
        if (segment == null || segment.size() < 2) return;
        RiverWay rw = new RiverWay();
        rw.name = name; rw.type = type; rw.points.addAll(segment);
        all.add(rw);
    }

    private static String makeDistrictLabelsGeoJson(String raw) throws Exception {
        JSONObject root = new JSONObject(raw);
        JSONArray input = root.optJSONArray("features"), out = new JSONArray();
        if (input == null) return emptyFeatureCollection();
        for (int i = 0; i < input.length(); i++) {
            JSONObject f = input.optJSONObject(i);
            JSONObject g = f == null ? null : f.optJSONObject("geometry");
            JSONObject props = f == null ? null : f.optJSONObject("properties");
            if (g == null || props == null) continue;
            double[] c = geometryBoundsCenter(g);
            if (c == null) continue;
            String name = firstNonEmpty(props.optString("nameNe"), props.optString("name_en"), props.optString("nameEn"), props.optString("name"));
            out.put(pointFeature(c[0], c[1], name));
        }
        return new JSONObject().put("type", "FeatureCollection").put("features", out).toString();
    }

    private static double[] geometryBoundsCenter(JSONObject g) {
        JSONArray coords = g.optJSONArray("coordinates");
        if (coords == null) return null;
        double[] b = new double[]{Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.NEGATIVE_INFINITY};
        collectBounds(coords, b);
        if (!Double.isFinite(b[0]) || !Double.isFinite(b[1]) || !Double.isFinite(b[2]) || !Double.isFinite(b[3])) return null;
        return new double[]{(b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0};
    }

    private static void collectBounds(JSONArray a, double[] b) {
        if (a == null || a.length() == 0) return;
        Object first = a.opt(0);
        if (first instanceof Number && a.length() >= 2 && a.opt(1) instanceof Number) {
            double x = a.optDouble(0, Double.NaN), y = a.optDouble(1, Double.NaN);
            if (Double.isFinite(x) && Double.isFinite(y)) {
                b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y);
                b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y);
            }
            return;
        }
        for (int i = 0; i < a.length(); i++) collectBounds(a.optJSONArray(i), b);
    }

    private static String stationLabelsGeo(List<StationDot> list) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) f.put(pointFeature(s.lon, s.lat, s.name));
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }

'''
if 'private void buildNepalRings(String raw)' not in m:
    if helper_anchor not in m:
        raise SystemExit('GeoJSON helper anchor missing')
    m = m.replace(helper_anchor, helpers + helper_anchor, 1)

# Add ring model beside existing map data classes.
if 'private static final class NepalRing' not in m:
    class_anchor = '    private static final class RiverWay {'
    if class_anchor not in m:
        raise SystemExit('RiverWay class anchor missing')
    ring_class = '''    private static final class NepalRing {\n        final List<double[]> points = new ArrayList<>();\n        double minLon = Double.POSITIVE_INFINITY, minLat = Double.POSITIVE_INFINITY;\n        double maxLon = Double.NEGATIVE_INFINITY, maxLat = Double.NEGATIVE_INFINITY;\n    }\n\n'''
    m = m.replace(class_anchor, ring_class + class_anchor, 1)

for marker in [
    'buildNepalRings(districtGeoJson);',
    'isInsideNepal(la, lo)',
    'fs-district-labels-layer',
    'fs-station-labels-layer',
    'stationLabelsGeo(snapshot)',
]:
    if marker not in m:
        raise SystemExit('v0.8.3 map marker missing: ' + marker)
map_path.write_text(m, encoding='utf-8')

# Restore web-style SATHI interaction: typed question + Send plus voice.
a = activity_path.read_text(encoding='utf-8')
if 'import android.widget.EditText;' not in a:
    if 'import android.widget.Button;' not in a:
        raise SystemExit('EditText import anchor missing')
    a = a.replace('import android.widget.Button;\n', 'import android.widget.Button;\nimport android.widget.EditText;\n', 1)
start = a.find('    private void showSathiDialog(String initial){')
end = a.find('    private void startVoice(', start)
if start < 0 or end < 0:
    raise SystemExit('SATHI dialog method anchors missing')
new_sathi = '''    private void showSathiDialog(String initial){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(8),dp(18),0);
        TextView answer=text(initial==null?t("मौसम, नदी, warning वा app status सोध्नुहोस्।","Ask about weather, rivers, warnings or app status."):answerSathi(initial),14,false,Color.rgb(30,52,72));box.addView(answer);
        EditText input=new EditText(this);input.setHint(t("यहाँ प्रश्न लेख्नुहोस्…","Type your question here…"));input.setTextSize(15);input.setSingleLine(false);input.setMinLines(1);input.setMaxLines(4);input.setPadding(dp(12),dp(10),dp(12),dp(10));input.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));box.addView(input,lp(-1,-2,0,dp(12),0,0));
        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
        Button send=button(t("➤ पठाउनुहोस्","➤ Send"));Button mic=button(t("🎙️ आवाज","🎙️ Voice"));actions.addView(send,new LinearLayout.LayoutParams(0,dp(52),1f));LinearLayout.LayoutParams mp=new LinearLayout.LayoutParams(0,dp(52),1f);mp.setMargins(dp(8),0,0,0);actions.addView(mic,mp);box.addView(actions);
        AlertDialog d=new AlertDialog.Builder(this).setTitle("🤖 SATHI").setView(box).setNegativeButton(t("बन्द","Close"),null).create();
        send.setOnClickListener(v->{String q=input.getText()==null?"":input.getText().toString().trim();if(q.isEmpty())return;String ans=answerSathi(q);answer.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+ans);input.setText("");speak(ans);});
        mic.setOnClickListener(v->startVoice(answer));d.show();
    }
'''
a = a[:start] + new_sathi + a[end:]
if 'Type your question here' not in a or '➤ Send' not in a:
    raise SystemExit('Typed SATHI markers missing')
activity_path.write_text(a, encoding='utf-8')

# Bump the build produced after v0.8.2 patch.
g = gradle_path.read_text(encoding='utf-8')
g = g.replace('versionCode 22', 'versionCode 23', 1)
g = g.replace("versionName '0.8.2'", "versionName '0.8.3'", 1)
if 'versionCode 23' not in g or "versionName '0.8.3'" not in g:
    raise SystemExit('v0.8.3 version bump failed; v0.8.2 patch must run first')
gradle_path.write_text(g, encoding='utf-8')

print('FloodSafe v0.8.3 Nepal-clipped detailed native map + typed/voice SATHI patch PASS')
