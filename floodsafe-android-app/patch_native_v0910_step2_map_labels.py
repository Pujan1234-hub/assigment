from pathlib import Path
import re

MAP = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java")
GRADLE = Path("floodsafe-android-app/app/build.gradle")
s = MAP.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f"{label}: expected one match, got {n}")
    s=s.replace(old,new,1)

once('import org.maplibre.android.style.layers.LineLayer;\n',
     'import org.maplibre.android.style.layers.LineLayer;\nimport org.maplibre.android.style.layers.SymbolLayer;\nimport org.maplibre.android.style.expressions.Expression;\n',
     'symbol imports')
once('import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\n',
     'import static org.maplibre.android.style.layers.PropertyFactory.lineWidth;\nimport static org.maplibre.android.style.layers.PropertyFactory.textAllowOverlap;\nimport static org.maplibre.android.style.layers.PropertyFactory.textColor;\nimport static org.maplibre.android.style.layers.PropertyFactory.textField;\nimport static org.maplibre.android.style.layers.PropertyFactory.textHaloColor;\nimport static org.maplibre.android.style.layers.PropertyFactory.textHaloWidth;\nimport static org.maplibre.android.style.layers.PropertyFactory.textSize;\n',
     'text property imports')

style_pattern=r'    private static final String STYLE_JSON = .*?;\n\n    private final MapView mapView;'
style_replacement='''    private static final String STYLE_JSON = "{\\"version\\":8,\\"sources\\":{" +
            "\\"satellite\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"maxzoom\\":19,\\"attribution\\":\\"Imagery © Esri\\"}," +
            "\\"terrain\\":{\\"type\\":\\"raster-dem\\",\\"tiles\\":[\\"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png\\"],\\"tileSize\\":256,\\"encoding\\":\\"terrarium\\",\\"minzoom\\":0,\\"maxzoom\\":15,\\"attribution\\":\\"Terrain © AWS Terrain Tiles\\"}," +
            "\\"reference-labels\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"minzoom\\":0,\\"maxzoom\\":19,\\"attribution\\":\\"Places © Esri\\"}}," +
            "\\"layers\\":[{\\"id\\":\\"satellite\\",\\"type\\":\\"raster\\",\\"source\\":\\"satellite\\"},{\\"id\\":\\"hillshade\\",\\"type\\":\\"hillshade\\",\\"source\\":\\"terrain\\",\\"paint\\":{\\"hillshade-exaggeration\\":0.30,\\"hillshade-shadow-color\\":\\"#14242c\\",\\"hillshade-highlight-color\\":\\"#f2fdff\\",\\"hillshade-accent-color\\":\\"#4f7f8e\\"}},{\\"id\\":\\"reference-labels\\",\\"type\\":\\"raster\\",\\"source\\":\\"reference-labels\\",\\"minzoom\\":6.0}]}"; // V0910_ZOOM_PLACE_REFERENCE_LABELS

    private final MapView mapView;'''
s2,n=re.subn(style_pattern,lambda m:style_replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f"style block anchor expected once, got {n}")
s=s2

anchor='''    private void installGeoLayers() {
        if (!styleReady || style == null) return;'''
helper=r'''    private static String districtLabelGeoJson(String raw) {
        try {
            JSONObject root=new JSONObject(raw);JSONArray features=root.optJSONArray("features");JSONArray labels=new JSONArray();
            if(features!=null)for(int i=0;i<features.length();i++){
                JSONObject f=features.optJSONObject(i);if(f==null)continue;JSONObject p=f.optJSONObject("properties");JSONObject geom=f.optJSONObject("geometry");
                String name=p==null?"":p.optString("nameEn","").trim();JSONArray coords=geom==null?null:geom.optJSONArray("coordinates");if(name.isEmpty()||coords==null)continue;
                double[] b={Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY};districtCoordBounds(coords,b);
                if(!Double.isFinite(b[0])||!Double.isFinite(b[1])||!Double.isFinite(b[2])||!Double.isFinite(b[3]))continue;
                double lat=(b[0]+b[1])/2d,lon=(b[2]+b[3])/2d;
                JSONObject point=new JSONObject().put("type","Point").put("coordinates",new JSONArray().put(lon).put(lat));
                labels.put(new JSONObject().put("type","Feature").put("geometry",point).put("properties",new JSONObject().put("name",name)));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",labels).toString();
        } catch(Exception e){return emptyFeatureCollection();}
    }
    private static void districtCoordBounds(Object node,double[] b){
        if(!(node instanceof JSONArray)||b==null||b.length<4)return;JSONArray a=(JSONArray)node;
        Object x=a.length()>0?a.opt(0):null,y=a.length()>1?a.opt(1):null;
        if(x instanceof Number&&y instanceof Number){double lon=((Number)x).doubleValue(),lat=((Number)y).doubleValue();if(Double.isFinite(lat)&&Double.isFinite(lon)){b[0]=Math.min(b[0],lat);b[1]=Math.max(b[1],lat);b[2]=Math.min(b[2],lon);b[3]=Math.max(b[3],lon);}return;}
        for(int i=0;i<a.length();i++)districtCoordBounds(a.opt(i),b);
    } // V0910_DISTRICT_LABEL_POINTS

    private void installGeoLayers() {
        if (!styleReady || style == null) return;'''
if anchor not in s: raise SystemExit('installGeoLayers anchor missing')
s=s.replace(anchor,helper,1)

old='''            if (districtGeoJson != null && style.getSource("fs-districts") == null) {
                style.addSource(new GeoJsonSource("fs-districts", districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill", "fs-districts").withProperties(
                        fillColor("#8deeff"), fillOpacity(0.06f)));
                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(
                        lineColor("#e8fbff"), lineWidth(1.05f), lineOpacity(0.74f), lineJoin(LINE_JOIN_ROUND)));
            }
            if (style.getSource("fs-rivers") == null) {'''
new='''            if (districtGeoJson != null && style.getSource("fs-districts") == null) {
                style.addSource(new GeoJsonSource("fs-districts", districtGeoJson));
                style.addLayer(new FillLayer("fs-district-fill", "fs-districts").withProperties(
                        fillColor("#8deeff"), fillOpacity(0.06f)));
                style.addLayer(new LineLayer("fs-district-lines", "fs-districts").withProperties(
                        lineColor("#e8fbff"), lineWidth(1.05f), lineOpacity(0.74f), lineJoin(LINE_JOIN_ROUND)));
            }
            if (districtGeoJson != null && style.getSource("fs-district-label-points") == null) {
                style.addSource(new GeoJsonSource("fs-district-label-points", districtLabelGeoJson(districtGeoJson)));
            }
            if (style.getSource("fs-district-label-points") != null && style.getLayer("fs-district-labels") == null) {
                style.addLayer(new SymbolLayer("fs-district-labels", "fs-district-label-points").withProperties(
                        textField(Expression.get("name")), textSize(11.0f), textColor("#ffffff"),
                        textHaloColor("#173642"), textHaloWidth(1.45f), textAllowOverlap(false)));
            } // V0910_DISTRICT_AND_PLACE_LABELS
            if (style.getSource("fs-rivers") == null) {'''
if s.count(old)!=1: raise SystemExit(f'district layer anchor expected once, got {s.count(old)}')
s=s.replace(old,new,1)

if "versionCode 26" not in g or "versionName '0.9.09-live77-sathi-fastlang'" not in g:
    raise SystemExit('v0.9.09 version marker missing')
g=g.replace('versionCode 26','versionCode 27',1)
g=g.replace("versionName '0.9.09-live77-sathi-fastlang'","versionName '0.9.10-sathi-chat-map-labels'",1)

for marker in ['V0910_ZOOM_PLACE_REFERENCE_LABELS','V0910_DISTRICT_LABEL_POINTS','V0910_DISTRICT_AND_PLACE_LABELS']:
    if marker not in s: raise SystemExit('missing marker '+marker)
if 'android.webkit.WebView' in s: raise SystemExit('WebView introduced')
MAP.write_text(s,encoding='utf-8');GRADLE.write_text(g,encoding='utf-8')
print('V0910_STEP2_MAP_LABELS_OK')
