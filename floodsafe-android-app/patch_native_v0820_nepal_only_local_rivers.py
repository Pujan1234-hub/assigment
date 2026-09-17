from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.20 user-locked map behavior:
# - River/glow/particles/status are visually restricted to Nepal only.
# - Kathmandu/local zoom prioritizes actual nearby OSM waterways instead of far major routes.
# - No river-name labels on the map; zoomed map uses place/boundary reference labels instead.
# - No rain station dots or rain click targets on the river map. Rain data remains elsewhere in app.
# - Latest official BIPAD/DHM river gauge dots remain visible; river tap shows same-river official state.
# Emergency 2 km and 2-hour notification rules are unchanged.

# -----------------------------------------------------------------------------
# Base style: add a transparent Esri place/boundary label overlay only from zoom 7.
# This gives Kathmandu/local place names without putting river names on the map.
# -----------------------------------------------------------------------------
style_old='''    private static final String STYLE_JSON = "{\\"version\\":8,\\"sources\\":{" +
            "\\"satellite\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"maxzoom\\":19,\\"attribution\\":\\"Imagery © Esri\\"}," +
            "\\"terrain\\":{\\"type\\":\\"raster-dem\\",\\"tiles\\":[\\"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png\\"],\\"tileSize\\":256,\\"encoding\\":\\"terrarium\\",\\"minzoom\\":0,\\"maxzoom\\":15,\\"attribution\\":\\"Terrain © AWS Terrain Tiles\\"}}," +
            "\\"layers\\":[{\\"id\\":\\"satellite\\",\\"type\\":\\"raster\\",\\"source\\":\\"satellite\\"},{\\"id\\":\\"hillshade\\",\\"type\\":\\"hillshade\\",\\"source\\":\\"terrain\\",\\"paint\\":{\\"hillshade-exaggeration\\":0.30,\\"hillshade-shadow-color\\":\\"#14242c\\",\\"hillshade-highlight-color\\":\\"#f2fdff\\",\\"hillshade-accent-color\\":\\"#4f7f8e\\"}}]}";'''
style_new='''    private static final String STYLE_JSON = "{\\"version\\":8,\\"sources\\":{" +
            "\\"satellite\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"maxzoom\\":19,\\"attribution\\":\\"Imagery © Esri\\"}," +
            "\\"terrain\\":{\\"type\\":\\"raster-dem\\",\\"tiles\\":[\\"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png\\"],\\"tileSize\\":256,\\"encoding\\":\\"terrarium\\",\\"minzoom\\":0,\\"maxzoom\\":15,\\"attribution\\":\\"Terrain © AWS Terrain Tiles\\"}," +
            "\\"places\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"minzoom\\":7,\\"maxzoom\\":19,\\"attribution\\":\\"Places © Esri\\"}}," +
            "\\"layers\\":[{\\"id\\":\\"satellite\\",\\"type\\":\\"raster\\",\\"source\\":\\"satellite\\"},{\\"id\\":\\"hillshade\\",\\"type\\":\\"hillshade\\",\\"source\\":\\"terrain\\",\\"paint\\":{\\"hillshade-exaggeration\\":0.30,\\"hillshade-shadow-color\\":\\"#14242c\\",\\"hillshade-highlight-color\\":\\"#f2fdff\\",\\"hillshade-accent-color\\":\\"#4f7f8e\\"}},{\\"id\\":\\"places\\",\\"type\\":\\"raster\\",\\"source\\":\\"places\\",\\"minzoom\\":7,\\"paint\\":{\\"raster-opacity\\":0.94}}]}";'''
if style_old in m:
    m=m.replace(style_old,style_new,1)
elif '\\"places\\":{\\"type\\":\\"raster\\"' not in m:
    raise SystemExit('v0.8.20 base style anchor missing')

# -----------------------------------------------------------------------------
# Visible river set: local zoom must favour nearby real waterways (Kathmandu included).
# Keep only a little major-river context, then use more local routes as zoom increases.
# -----------------------------------------------------------------------------
m=m.replace('for(int i=0;i<Math.min(96,overviewRivers.size());i++)',
            'for(int i=0;i<Math.min(24,overviewRivers.size());i++)',1)
m=m.replace('int keep=Math.min(48,candidates.size());chosen.addAll(candidates.subList(0,keep));',
            'int keep=Math.min(zoom>=10.0?160:(zoom>=8.0?120:72),candidates.size());chosen.addAll(candidates.subList(0,keep));',1)
m=m.replace('-best*5.0;','-best*18.0;',1)
if 'zoom>=10.0?160:(zoom>=8.0?120:72)' not in m:
    raise SystemExit('v0.8.20 local river density anchor missing')

# No river text labels at any zoom. River name appears only after the real river line is tapped.
label_pat=r'String geo=makeRiversGeoJson\(chosen\),labels=.*?;'
m,n=re.subn(label_pat,'String geo=makeRiversGeoJson(chosen),labels=emptyFeatureCollection();',m,count=1)
if n!=1: raise SystemExit('v0.8.20 river label publish anchor missing')

# -----------------------------------------------------------------------------
# Nepal-only visual mask. Same architecture as the proven web map: an outer polygon
# with the 77 district polygons as holes. It is installed after hydro/status layers,
# so no cyan line/glow/particle/status can remain visible in India/China.
# -----------------------------------------------------------------------------
mask_helper=r'''    private static String makeNepalOutsideMask(String districtJson) {
        try {
            JSONObject root=new JSONObject(districtJson);JSONArray holes=new JSONArray();
            JSONArray outer=new JSONArray();
            outer.put(new JSONArray().put(79.1).put(25.3));
            outer.put(new JSONArray().put(89.25).put(25.3));
            outer.put(new JSONArray().put(89.25).put(31.25));
            outer.put(new JSONArray().put(79.1).put(31.25));
            outer.put(new JSONArray().put(79.1).put(25.3));
            holes.put(outer);
            JSONArray fs=root.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){
                JSONObject f=fs.optJSONObject(i),geom=f==null?null:f.optJSONObject("geometry");if(geom==null)continue;
                String type=geom.optString("type","");JSONArray c=geom.optJSONArray("coordinates");if(c==null)continue;
                if("Polygon".equals(type)){
                    JSONArray ring=c.optJSONArray(0);if(ring!=null&&ring.length()>=4)holes.put(ring);
                }else if("MultiPolygon".equals(type)){
                    for(int j=0;j<c.length();j++){JSONArray poly=c.optJSONArray(j),ring=poly==null?null:poly.optJSONArray(0);if(ring!=null&&ring.length()>=4)holes.put(ring);}
                }
            }
            JSONObject geom=new JSONObject().put("type","Polygon").put("coordinates",holes);
            JSONObject feat=new JSONObject().put("type","Feature").put("properties",new JSONObject()).put("geometry",geom);
            return new JSONObject().put("type","FeatureCollection").put("features",new JSONArray().put(feat)).toString();
        } catch(Exception ignored) { return emptyFeatureCollection(); }
    }

'''
helper_anchor='    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {'
if 'makeNepalOutsideMask(String districtJson)' not in m:
    if helper_anchor not in m: raise SystemExit('v0.8.20 mask helper anchor missing')
    m=m.replace(helper_anchor,mask_helper+helper_anchor,1)

install_anchor='''            refreshStationSources();
            refreshUserSource();'''
mask_install='''            if (districtGeoJson != null && style.getSource("fs-nepal-outside-mask") == null) {
                String mask=makeNepalOutsideMask(districtGeoJson);
                style.addSource(new GeoJsonSource("fs-nepal-outside-mask", mask));
                style.addLayer(new FillLayer("fs-nepal-outside-mask-layer", "fs-nepal-outside-mask").withProperties(
                        fillColor("#071821"), fillOpacity(1.0f)));
            }
'''
if 'fs-nepal-outside-mask-layer' not in m:
    if install_anchor not in m: raise SystemExit('v0.8.20 install mask anchor missing')
    m=m.replace(install_anchor,mask_install+install_anchor,1)

# -----------------------------------------------------------------------------
# River map is river + real river gauges only. Rain markers and rain tap targets are zero.
# Rain data is still fetched and available in the app's rainfall section/status summary.
# -----------------------------------------------------------------------------
click_start=m.find('    private boolean onMapClick(LatLng p) {')
click_end=m.find('    private static boolean isSevereStage',click_start)
if click_start<0 or click_end<0: raise SystemExit('v0.8.20 click anchors missing')
click_block=r'''    private boolean onMapClick(LatLng p) {
        StationDot nearest = nearestStation(p.getLatitude(), p.getLongitude());
        double zoom = map == null ? 6.0 : map.getCameraPosition().zoom;
        double stationThreshold = Math.max(0.45, 5.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        boolean stationShown=nearest!=null&&(zoom>=7.0||isSevereStage(nearest.stage));
        if (stationShown && sd <= stationThreshold) { if (stationTapListener != null) stationTapListener.onStationTap(nearest.original); return true; }
        RiverWay rw = nearestRiver(p.getLatitude(), p.getLongitude(), Math.max(0.20, 9.0 / Math.pow(2.0, Math.max(0.0, zoom - 6.0))));
        if (rw != null) { showRiver(rw, p.getLatitude(), p.getLongitude()); return true; }
        return false;
    }

'''
m=m[:click_start]+click_block+m[click_end:]

rain_start=m.find('    private void refreshRainSources() {')
rain_end=m.find('    private void refreshUserSource() {',rain_start)
if rain_start<0 or rain_end<0: raise SystemExit('v0.8.20 rain source anchors missing')
rain_block=r'''    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        String e=emptyFeatureCollection();
        setGeo("fs-rain-stale",e);setGeo("fs-rain-normal",e);setGeo("fs-rain-alert",e);setGeo("fs-rain-warning",e);setGeo("fs-rain-danger",e);
    }

'''
m=m[:rain_start]+rain_block+m[rain_end:]

# Keep the map text clean: no river-name text and no station-name text competing with place labels.
m=m.replace('setGeo("fs-station-labels", zoom>=7.6?stationGeoImportant(snapshot):emptyFeatureCollection());',
            'setGeo("fs-station-labels", emptyFeatureCollection());',1)

# User-facing subtitle: exact map contract.
a=a.replace(
    'mapSub.setText(t("जिल्ला + मुख्य नदी • नदी थिच्दा त्यही नदीको official gauge • zoom गर्दा local/rain detail","District + major rivers • river tap uses same-river official gauge • zoom for local/rain detail"));',
    'mapSub.setText(t("नेपालभित्र actual नदी flow • 🔵 latest official gauge • zoom गर्दा local नदी + ठाउँको नाम • rain station mapमा छैन","Actual Nepal-only river flow • 🔵 latest official gauges • zoom for local rivers + place names • rain stations are off-map"));',1)

# Version bump.
if "versionName '0.8.20'" not in g:
    g=g.replace('versionCode 39','versionCode 40',1)
    g=g.replace("versionName '0.8.19'","versionName '0.8.20'",1)
if 'versionCode 40' not in g or "versionName '0.8.20'" not in g:
    raise SystemExit('v0.8.20 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

# Hard gates.
a2=a_path.read_text(encoding='utf-8');m2=m_path.read_text(encoding='utf-8')
for marker in [
    'fs-nepal-outside-mask-layer','makeNepalOutsideMask(String districtJson)',
    'World_Boundaries_and_Places','String geo=makeRiversGeoJson(chosen),labels=emptyFeatureCollection();',
    'zoom>=10.0?160:(zoom>=8.0?120:72)','Math.min(24,overviewRivers.size())','-best*18.0;',
    'setGeo("fs-station-labels", emptyFeatureCollection())','setGeo("fs-rain-stale",e)',
    'sameRiverGaugeFor','lineColor("#22e7ff")','main.postDelayed(this,150L)']:
    if marker not in m2: raise SystemExit('v0.8.20 map marker missing: '+marker)
if 'boolean rainShown=' in m2: raise SystemExit('rain click target remained')
if 'makeRiverLabelsGeoJson(new ArrayList<>(chosen.subList' in m2: raise SystemExit('river labels remained')
if 'showRainMarkers=zoom>=8.0' in m2: raise SystemExit('rain markers remained')
if 'नेपालभित्र actual नदी flow' not in a2: raise SystemExit('v0.8.20 subtitle marker missing')
print('FloodSafe v0.8.20 Nepal-only local river live map PASS')
