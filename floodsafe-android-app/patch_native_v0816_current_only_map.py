from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path=src/'NativeFullActivity.java'
map_path=src/'FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'
activity=activity_path.read_text(encoding='utf-8')
helper=map_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

# v0.8.16: show official current truth, not the whole bundled OSM waterway mesh.
# Bundled geometry remains available for matching/tap context, but visually it is
# nearly hidden. Current official gauges and their matched river segments carry
# the source-derived colour. This also reduces visual clutter and GPU work.

# Fade the entire bundled background network to near-invisible context.
helper=helper.replace(
    'lineColor("#243f49"), lineWidth(3.2f), lineOpacity(0.24f)',
    'lineColor("#51646d"), lineWidth(0.80f), lineOpacity(0.025f)',1)
helper=helper.replace(
    'lineColor("#78909c"), lineWidth(1.45f), lineOpacity(0.42f)',
    'lineColor("#78909c"), lineWidth(0.65f), lineOpacity(0.055f)',1)
# Compatibility with any generated variant that retained the older cyan base.
helper=helper.replace(
    'lineColor("#00bde9"), lineWidth(7.4f), lineOpacity(0.58f)',
    'lineColor("#51646d"), lineWidth(0.80f), lineOpacity(0.025f)',1)
helper=helper.replace(
    'lineColor("#7ceeff"), lineWidth(2.65f), lineOpacity(1.0f)',
    'lineColor("#78909c"), lineWidth(0.65f), lineOpacity(0.055f)',1)

# Fresh official station dots remain visible; stale catalogue dots become almost
# invisible so they cannot be mistaken for live data.
helper=helper.replace(
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 2.5f, 0.42f);',
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 1.25f, 0.10f);',1)
helper=helper.replace(
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);',
    'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 1.25f, 0.10f);',1)
helper=helper.replace(
    'ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f);',
    'ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 3.6f, 0.96f);',1)

# Only CURRENT official gauges get station-name labels. Old/stale catalogue names
# no longer flood the national map.
all_pat=r'''    private static String stationGeoAll\(List<StationDot> list\) \{.*?\n    \}\n'''
all_new=r'''    private static String stationGeoAll(List<StationDot> list) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) { if(s!=null&&s.fresh) f.put(pointFeature(s.lon, s.lat, s.name)); }
            return new JSONObject().put("type", "FeatureCollection").put("features", f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    }
'''
helper,n=re.subn(all_pat,all_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('stationGeoAll current-only replacement failed')

# River labels from the huge OSM mesh are context, not source truth. Remove them
# from the default map; the official station labels still name the live locations.
labels_pat=r'''            if \(riverLabelsGeoJson != null && style.getSource\("fs-river-labels"\) == null\) \{.*?\n            \}\n'''
labels_new='''            // v0.8.16: generic OSM river-name mesh hidden by default; official current station labels are authoritative.\n'''
helper,n=re.subn(labels_pat,labels_new,helper,count=1,flags=re.S)
if n!=1 and 'generic OSM river-name mesh hidden by default' not in helper:
    raise SystemExit('river label block missing')

# Keep normal current river segments clearly visible in blue while severe stages
# retain the stronger source-colour treatment from v0.8.14.
helper=helper.replace('float coreWidth=normal?2.65f:(alert?3.2f:3.8f);',
                      'float coreWidth=normal?3.05f:(alert?3.45f:4.10f);',1)

# UI text explicitly describes what is and is not live.
activity=activity.replace(
    'mapSub.setText(t("Source status जस्तै: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER • Grey=stale/geometry","Source-exact status: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER • Grey=stale/geometry"));',
    'mapSub.setText(t("Current official source मात्र highlight: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER","Only current official source is highlighted: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER"));',1)

# Hint wording: current count is source readings; background geometry is not live.
activity=activity.replace(
    '"🌊 नदी current ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ वर्षा fresh "+mapRainFresh+" / "+mapRainTotal,',
    '"🌊 current official ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • बाकी geometry hidden • 🌧️ rain "+mapRainFresh+" / "+mapRainTotal,',1)
activity=activity.replace(
    '"🌊 river current ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain fresh "+mapRainFresh+" / "+mapRainTotal));',
    '"🌊 current official ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • background geometry hidden • 🌧️ rain "+mapRainFresh+" / "+mapRainTotal));',1)

# Version bump.
if "versionName '0.8.16'" not in gradle:
    gradle=gradle.replace('versionCode 35','versionCode 36',1)
    gradle=gradle.replace("versionName '0.8.15'","versionName '0.8.16'",1)
if 'versionCode 36' not in gradle or "versionName '0.8.16'" not in gradle:
    raise SystemExit('v0.8.16 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard truth/UX assertions.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for m in ['Only current official source is highlighted','background geometry hidden','sourceStatusLabel(RiverStation s)']:
    if m not in a: raise SystemExit('v0.8.16 activity marker missing: '+m)
for m in ['lineWidth(0.65f), lineOpacity(0.055f)','if(s!=null&&s.fresh)','generic OSM river-name mesh hidden by default','coreWidth=normal?3.05f']:
    if m not in h: raise SystemExit('v0.8.16 map marker missing: '+m)
if 'lineColor("#78909c"), lineWidth(1.45f), lineOpacity(0.42f)' in h:
    raise SystemExit('cluttered background river styling remained')
print('FloodSafe v0.8.16 current-official-only map + hidden background mesh PASS')
