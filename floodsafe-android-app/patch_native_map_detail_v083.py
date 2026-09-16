from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
helper_path = src / 'FloodSafeNativeMapView.java'
activity_path = src / 'NativeFullActivity.java'
gradle_path = root / 'app/build.gradle'

helper = helper_path.read_text(encoding='utf-8')
activity = activity_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# --- MapLibre: labels, Nepal-only visual mask, exact station labels ---
if 'import org.maplibre.android.style.layers.SymbolLayer;' not in helper:
    helper = helper.replace('import org.maplibre.android.style.layers.LineLayer;\n',
                            'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.layers.SymbolLayer;\n')
for imp in [
    'import static org.maplibre.android.style.layers.PropertyFactory.textAllowOverlap;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textColor;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textField;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textHaloColor;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textHaloWidth;\n',
    'import static org.maplibre.android.style.layers.PropertyFactory.textSize;\n',
]:
    if imp not in helper:
        helper = helper.replace('import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\n',
                                'import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\n' + imp)

# Add glyph endpoint so native symbol labels render without WebView.
helper = helper.replace('"{\\\"version\\\":8,\\\"sources\\\":{" +',
                        '"{\\\"version\\\":8,\\\"glyphs\\\":\\\"https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf\\\",\\\"sources\\\":{" +')

if 'private String nepalMaskGeoJson = null;' not in helper:
    helper = helper.replace('private String districtGeoJson = null;\n    private String riversGeoJson = null;',
                            'private String districtGeoJson = null;\n    private String nepalMaskGeoJson = null;\n    private String riversGeoJson = null;')

# Build outside-Nepal polygon mask from the 77 district polygons.
load_anchor = '''            try {\n                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");\n            } catch (Exception ignored) {\n                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}\n            }\n            try {'''
load_new = '''            try {\n                districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson");\n            } catch (Exception ignored) {\n                try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {}\n            }\n            try { if (districtGeoJson != null) nepalMaskGeoJson = makeNepalOutsideMask(districtGeoJson); } catch (Exception ignored) {}\n            try {'''
if load_anchor in helper:
    helper = helper.replace(load_anchor, load_new, 1)

# Tighten river-point acceptance from the broad HARD_BOUNDS to Nepal's map bounds.
helper = helper.replace('private static boolean isNepalish(double la, double lo) { return la >= 25.4 && la <= 31.15 && lo >= 79.2 && lo <= 89.15; }',
                        'private static boolean isNepalish(double la, double lo) { return la >= NEPAL_MIN_LAT && la <= NEPAL_MAX_LAT && lo >= NEPAL_MIN_LON && lo <= NEPAL_MAX_LON; }')

# District names.
district_anchor = '''                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(\n                        lineColor("#e8fbff"), lineWidth(1.15f), lineOpacity(0.82f), lineJoin(LINE_JOIN_ROUND)));'''
district_new = district_anchor + '''\n                style.addLayer(new SymbolLayer("fs-district-labels", "fs-districts").withProperties(\n                        textField("{nameEn}"), textSize(10.5f), textColor("#ffffff"),\n                        textHaloColor("#173646"), textHaloWidth(1.6f), textAllowOverlap(false)));'''
if district_anchor in helper and 'fs-district-labels' not in helper:
    helper = helper.replace(district_anchor, district_new, 1)

# Dark outside-Nepal mask above river geometry so India/Tibet river effects do not visually leak.
river_anchor = '''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));\n            }'''
river_new = '''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#49dcff"), lineWidth(1.65f), lineOpacity(0.96f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));\n            }\n            if (nepalMaskGeoJson != null && style.getSource("fs-nepal-mask") == null) {\n                style.addSource(new GeoJsonSource("fs-nepal-mask", nepalMaskGeoJson));\n                style.addLayer(new FillLayer("fs-nepal-mask-layer", "fs-nepal-mask").withProperties(\n                        fillColor("#071720"), fillOpacity(0.88f)));\n            }'''
if river_anchor in helper and 'fs-nepal-mask-layer' not in helper:
    helper = helper.replace(river_anchor, river_new, 1)

# One source for station names at their official coordinates. Collision handling keeps the national view clean.
points_anchor = '''            ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f);'''
points_new = points_anchor + '''\n            if (style.getSource("fs-station-labels") == null) {\n                style.addSource(new GeoJsonSource("fs-station-labels", emptyFeatureCollection()));\n                style.addLayer(new SymbolLayer("fs-station-labels-layer", "fs-station-labels").withProperties(\n                        textField("{name}"), textSize(10.0f), textColor("#ffffff"),\n                        textHaloColor("#163846"), textHaloWidth(1.5f), textAllowOverlap(false)));\n            }'''
if points_anchor in helper and 'fs-station-labels-layer' not in helper:
    helper = helper.replace(points_anchor, points_new, 1)

refresh_anchor = '''        setGeo("fs-warning", stationGeo(snapshot, "warning"));\n        setGeo("fs-danger", stationGeo(snapshot, "danger"));'''
refresh_new = refresh_anchor + '''\n        setGeo("fs-station-labels", stationGeoAll(snapshot));'''
if refresh_anchor in helper and 'stationGeoAll(snapshot)' not in helper:
    helper = helper.replace(refresh_anchor, refresh_new, 1)

station_func_anchor = '''    private static String stationGeo(List<StationDot> list, String group) {'''
station_all = '''    private static String stationGeoAll(List<StationDot> list) {\n        try {\n            JSONArray f = new JSONArray();\n            for (StationDot s : list) f.put(pointFeature(s.lon, s.lat, s.name));\n            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();\n        } catch (Exception e) { return emptyFeatureCollection(); }\n    }\n\n'''
if station_func_anchor in helper and 'private static String stationGeoAll' not in helper:
    helper = helper.replace(station_func_anchor, station_all + station_func_anchor, 1)

# GeoJSON outside mask: outer rectangle with each district outer ring as a hole.
mask_anchor = '''    private static String makeRiversGeoJson(List<RiverWay> ways) throws Exception {'''
mask_func = '''    private static String makeNepalOutsideMask(String districtJson) throws Exception {\n        JSONObject root = new JSONObject(districtJson);\n        JSONArray features = root.optJSONArray("features");\n        JSONArray rings = new JSONArray();\n        JSONArray outer = new JSONArray();\n        outer.put(new JSONArray().put(79.2).put(25.4));\n        outer.put(new JSONArray().put(89.15).put(25.4));\n        outer.put(new JSONArray().put(89.15).put(31.15));\n        outer.put(new JSONArray().put(79.2).put(31.15));\n        outer.put(new JSONArray().put(79.2).put(25.4));\n        rings.put(outer);\n        if (features != null) for (int i=0;i<features.length();i++) {\n            JSONObject g = features.optJSONObject(i); if (g == null) continue;\n            JSONObject geo = g.optJSONObject("geometry"); if (geo == null) continue;\n            JSONArray c = geo.optJSONArray("coordinates"); if (c == null) continue;\n            if ("Polygon".equals(geo.optString("type"))) { JSONArray r=c.optJSONArray(0); if (r!=null) rings.put(r); }\n            else if ("MultiPolygon".equals(geo.optString("type"))) for (int j=0;j<c.length();j++) { JSONArray p=c.optJSONArray(j); JSONArray r=p==null?null:p.optJSONArray(0); if(r!=null) rings.put(r); }\n        }\n        JSONObject geom = new JSONObject().put("type","Polygon").put("coordinates",rings);\n        JSONObject feature = new JSONObject().put("type","Feature").put("properties",new JSONObject()).put("geometry",geom);\n        return feature.toString();\n    }\n\n'''
if mask_anchor in helper and 'makeNepalOutsideMask' not in helper[helper.find(mask_anchor):]:
    helper = helper.replace(mask_anchor, mask_func + mask_anchor, 1)

helper_path.write_text(helper, encoding='utf-8')

# --- SATHI: restore typed question box + send, keep microphone ---
if 'import android.widget.EditText;' not in activity:
    activity = activity.replace('import android.widget.Button;\n', 'import android.widget.Button;\nimport android.widget.EditText;\n')
start = activity.find('    private void showSathiDialog(String initial){')
end = activity.find('    private void startVoice(TextView out)', start)
if start < 0 or end < 0:
    raise SystemExit('SATHI dialog anchors missing')
new_dialog = '''    private void showSathiDialog(String initial){\n        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(8),dp(18),0);\n        TextView answer=text(initial==null?t("मौसम, नदी, warning वा app status सोध्नुहोस्।","Ask about weather, rivers, warnings or app status."):answerSathi(initial),14,false,Color.rgb(30,52,72));\n        box.addView(answer);\n        EditText input=new EditText(this);input.setSingleLine(false);input.setMinLines(1);input.setMaxLines(3);input.setTextSize(15);input.setHint(t("यहाँ प्रश्न लेख्नुहोस्…","Type your question here…"));input.setPadding(dp(14),dp(10),dp(14),dp(10));input.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(190,218,232),1));box.addView(input,lp(-1,-2,0,dp(12),0,0));\n        Button send=button(t("➤ पठाउनुहोस्","➤ Send"));box.addView(send,lp(-1,dp(50),0,dp(8),0,0));\n        Button mic=button(t("🎙️ माइकबाट सोध्नुहोस्","🎙️ Ask by voice"));box.addView(mic,lp(-1,dp(52),0,dp(8),0,0));\n        AlertDialog d=new AlertDialog.Builder(this).setTitle("🤖 SATHI").setView(box).setNegativeButton(t("बन्द","Close"),null).create();\n        send.setOnClickListener(v->{String q=input.getText()==null?"":input.getText().toString().trim();if(q.isEmpty())return;String a=answerSathi(q);answer.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+a);input.setText("");});\n        mic.setOnClickListener(v->startVoice(answer));\n        d.show();\n    }\n'''
activity = activity[:start] + new_dialog + activity[end:]
activity_path.write_text(activity, encoding='utf-8')

# v0.8.3
if "versionName '0.8.3'" not in gradle:
    gradle = gradle.replace('versionCode 22', 'versionCode 23', 1)
    gradle = gradle.replace("versionName '0.8.2'", "versionName '0.8.3'", 1)
if 'versionCode 23' not in gradle or "versionName '0.8.3'" not in gradle:
    raise SystemExit('v0.8.3 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index = index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.2</span>', '<span class="badge green">v0.8.3</span>')
    index_path.write_text(index, encoding='utf-8')

# Required build markers.
final_helper = helper_path.read_text(encoding='utf-8')
final_activity = activity_path.read_text(encoding='utf-8')
for marker in ['fs-nepal-mask-layer','fs-district-labels','fs-station-labels-layer','stationGeoAll(snapshot)','makeNepalOutsideMask']:
    if marker not in final_helper: raise SystemExit('Map detail marker missing: '+marker)
for marker in ['EditText input=new EditText(this)','send.setOnClickListener','Type your question here']:
    if marker not in final_activity: raise SystemExit('SATHI typed input marker missing: '+marker)
print('FloodSafe v0.8.3 native detailed map + SATHI text input patch PASS')
