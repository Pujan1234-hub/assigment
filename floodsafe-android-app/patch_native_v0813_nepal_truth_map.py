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

# -----------------------------------------------------------------------------
# v0.8.13: Nepal-only truth map.
# Static OSM/FloodSafe river geometry is NOT live data. Keep it muted. Only a
# river matched to a current official BIPAD/DHM gauge gets colour/glow/particles.
# Also make Nepal clipping strict enough that India-side geometry cannot bleed in.
# -----------------------------------------------------------------------------

# Tight Nepal camera envelope (the old generous box intentionally included large
# areas of India/China and made it too easy to pan away from Nepal).
helper=helper.replace(
    '.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();',
    '.include(new LatLng(26.30, 80.00))\n                        .include(new LatLng(30.50, 88.25)).build();',1)

# Keep only the longest contiguous Nepal segment of each river instead of the old
# first-to-last Nepal span which could retain a long excursion outside the border.
trim_pat=r'''    private static void trimRiverToNepal\(RiverWay r,JSONObject districtRoot\) \{.*?\n    \}\n\n'''
trim_new=r'''    private static void trimRiverToNepal(RiverWay r,JSONObject districtRoot) {
        if (r==null||r.points.size()<2||districtRoot==null) return;
        int bestStart=-1,bestLen=0,curStart=-1,curLen=0;
        for(int i=0;i<r.points.size();i++){
            double[] p=r.points.get(i);
            boolean inside=insideNepalSoft(p[0],p[1],districtRoot);
            if(inside){
                if(curStart<0){curStart=i;curLen=1;}else curLen++;
                if(curLen>bestLen){bestLen=curLen;bestStart=curStart;}
            }else{curStart=-1;curLen=0;}
        }
        if(bestStart<0||bestLen<2){r.points.clear();return;}
        if(bestStart==0&&bestLen==r.points.size())return;
        List<double[]> keep=new ArrayList<>(r.points.subList(bestStart,bestStart+bestLen));
        r.points.clear();r.points.addAll(keep);
    }

'''
helper,n=re.subn(trim_pat,trim_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('trimRiverToNepal block missing')
helper=helper.replace('final double e=0.035;','final double e=0.010;',1)

# Use an actual Nepal-ish bbox even before district polygon clipping is available.
helper=helper.replace(
    'private static boolean isNepalish(double la, double lo) { return la >= 25.4 && la <= 31.15 && lo >= 79.2 && lo <= 89.15; }',
    'private static boolean isNepalish(double la, double lo) { return la >= 26.30 && la <= 30.50 && lo >= 80.00 && lo <= 88.25; }',1)

# Static river network = context only, not realtime truth.
helper=helper.replace('lineColor("#00bde9"), lineWidth(7.4f), lineOpacity(0.58f)',
                      'lineColor("#243f49"), lineWidth(3.2f), lineOpacity(0.24f)',1)
helper=helper.replace('lineColor("#22e7ff"), lineWidth(2.70f), lineOpacity(0.98f)',
                      'lineColor("#78909c"), lineWidth(1.45f), lineOpacity(0.42f)',1)

# Never pulse the whole river network. Fresh official status overlays provide the
# live glow; particles are filtered below to the same current-gauge rivers.
helper=helper.replace(
    'float glow=(float)(0.68+0.32*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(1.45f+1.05f*glow));',
    'flowTrace.setProperties(lineOpacity(0.0f),lineWidth(0.1f));',1)

# Give current official status lines their own glow + bright core.
status_pat=r'''    private void ensureRiverStatusLayer\(String sourceId,String layerId,String color\) \{\n        if\(style==null\|\|style.getSource\(sourceId\)!=null\)return;\n        style.addSource\(new GeoJsonSource\(sourceId,emptyFeatureCollection\(\)\)\);\n        style.addLayer\(new LineLayer\(layerId,sourceId\)\.withProperties\(lineColor\(color\),lineWidth\(3\.55f\),lineOpacity\(1\.0f\),lineCap\(LINE_CAP_ROUND\),lineJoin\(LINE_JOIN_ROUND\)\)\);\n    \}\n'''
status_new='''    private void ensureRiverStatusLayer(String sourceId,String layerId,String color) {\n        if(style==null||style.getSource(sourceId)!=null)return;\n        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));\n        style.addLayer(new LineLayer(layerId+"-glow",sourceId).withProperties(lineColor(color),lineWidth(8.2f),lineOpacity(0.28f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(3.8f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));\n    }\n'''
helper,n=re.subn(status_pat,status_new,helper,count=1)
if n!=1: raise SystemExit('ensureRiverStatusLayer block missing')

# Animated beads only on rivers that can be matched to a CURRENT official gauge.
old_n='                int n = Math.min(180, rivers.size());'
flow_select='''                List<StationDot> flowStations=new ArrayList<>();\n                synchronized(stations){for(StationDot s:stations)if(s!=null&&s.fresh)flowStations.add(s);}\n                List<RiverWay> flowRivers=new ArrayList<>();\n                for(RiverWay rr:rivers)if(routeGaugeForSnapshot(rr,flowStations)!=null)flowRivers.add(rr);\n                int n = Math.min(80, flowRivers.size());'''
if old_n not in helper: raise SystemExit('v0.8.12 particle count anchor missing')
helper=helper.replace(old_n,flow_select,1)
helper=helper.replace('                    RiverWay r = rivers.get(i);','                    RiverWay r = flowRivers.get(i);',1)

# Refuse India-side camera targets using the actual 77-district polygon, not only
# a rectangular bbox. Reset to Nepal if the user pans fully outside the country.
if 'private boolean cameraTargetInsideNepal(' not in helper:
    anchor='    private void refreshVisibleRiverTiles() {'
    method=r'''    private boolean cameraTargetInsideNepal(LatLng center) {
        if(center==null)return false;
        if(districtGeoJson==null)return isNepalish(center.getLatitude(),center.getLongitude());
        try{return insideDistricts(center.getLongitude(),center.getLatitude(),new JSONObject(districtGeoJson));}
        catch(Exception e){return isNepalish(center.getLatitude(),center.getLongitude());}
    }

'''
    if anchor not in helper: raise SystemExit('refreshVisibleRiverTiles anchor missing')
    helper=helper.replace(anchor,method+anchor,1)
helper=helper.replace(
    '        LatLng center = cp.target;\n        if (zoom < 7.0) {',
    '        LatLng center = cp.target;\n        if(!cameraTargetInsideNepal(center)){map.animateCamera(CameraUpdateFactory.newLatLng(NEPAL_CENTER),250);return;}\n        if (zoom < 7.0) {',1)

# -----------------------------------------------------------------------------
# UI truth semantics: do not label the whole map LIVE. Show separate current
# river and fresh-rain counts so "0 fresh / 1000 total" cannot be misread as the
# river feed being dead or as every cyan river being live.
# -----------------------------------------------------------------------------
activity=activity.replace(
    'TextView live=badge(t("प्रत्यक्ष","LIVE"),Color.rgb(233,255,245),Color.rgb(18,128,90));',
    'TextView live=badge(t("आधिकारिक","OFFICIAL"),Color.rgb(237,247,252),Color.rgb(23,116,174));',1)

field_anchor='    private boolean showAllStations=false;'
if 'private int mapRiverCurrent=' not in activity:
    if field_anchor not in activity: raise SystemExit('showAllStations field anchor missing')
    activity=activity.replace(field_anchor,field_anchor+'\n    private int mapRiverCurrent=0,mapRiverTotal=0,mapRainFresh=0,mapRainTotal=0;',1)

hint_method=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 नदी आजको official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ वर्षा fresh "+mapRainFresh+" / "+mapRainTotal,
                          "🌊 river current today "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain fresh "+mapRainFresh+" / "+mapRainTotal));
    }

'''
if 'private void updateMapHintCounts()' not in activity:
    rain_anchor='    private void refreshRainUi(){'
    if rain_anchor not in activity: raise SystemExit('refreshRainUi anchor missing')
    activity=activity.replace(rain_anchor,hint_method+rain_anchor,1)

activity=activity.replace(
    'stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));',
    'mapRiverCurrent=d+w+a+n;mapRiverTotal=copy.size();updateMapHintCounts();stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));',1)

old_rain_hint='''        int fresh=0;for(RainStation s:copy)if(s.fresh)fresh++;
        if(mapHint!=null)mapHint.setText(t("🌊 official नदी gauge • 🌧️ वर्षा स्टेशन "+fresh+" fresh / "+copy.size()+" total","🌊 official river gauges • 🌧️ rain stations "+fresh+" fresh / "+copy.size()+" total"));'''
new_rain_hint='''        int fresh=0;for(RainStation s:copy)if(s.fresh)fresh++;
        mapRainFresh=fresh;mapRainTotal=copy.size();updateMapHintCounts();'''
if old_rain_hint not in activity: raise SystemExit('misleading rain mapHint block missing')
activity=activity.replace(old_rain_hint,new_rain_hint,1)

# Explain colours correctly: geometry is context; only current official gauge
# matches are coloured/glowing.
activity=activity.replace(
    'mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, वर्षा, चेतावनी र official time हेर्नुहोस्।","Tap rivers/stations for water level, rainfall, warning and official time."));',
    'mapSub.setText(t("Grey नदी = geometry मात्र • रङ/Glow = आजको official gauge status","Grey rivers = geometry only • colour/glow = current official gauge status"));',1)

# Match the locked safety colour contract everywhere in the UI: Normal is blue,
# never green; stale/unknown is grey.
activity=activity.replace('case"normal":return Color.rgb(31,164,116);','case"normal":return Color.rgb(45,140,255);',1)
activity=activity.replace('case"normal":return Color.rgb(233,255,245);','case"normal":return Color.rgb(237,247,255);',1)
activity=activity.replace('case"normal":return"🟢";','case"normal":return"🔵";',1)

if "versionName '0.8.13'" not in gradle:
    gradle=gradle.replace('versionCode 32','versionCode 33',1)
    gradle=gradle.replace("versionName '0.8.12'","versionName '0.8.13'",1)
if 'versionCode 33' not in gradle or "versionName '0.8.13'" not in gradle: raise SystemExit('v0.8.13 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard safety/truth assertions.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for m in ['OFFICIAL','mapRiverCurrent','updateMapHintCounts','Grey rivers = geometry only','case"normal":return"🔵";']:
    if m not in a: raise SystemExit('v0.8.13 activity marker missing: '+m)
for m in ['lineColor("#78909c"), lineWidth(1.45f)','lineWidth(8.2f)','Math.min(80, flowRivers.size())','routeGaugeForSnapshot(rr,flowStations)','cameraTargetInsideNepal','bestStart','final double e=0.010']:
    if m not in h: raise SystemExit('v0.8.13 map marker missing: '+m)
if 'lineColor("#22e7ff"), lineWidth(2.70f)' in h: raise SystemExit('false bright all-river live styling remained')
if 'Math.min(180, rivers.size())' in h: raise SystemExit('all-river particle animation remained')
print('FloodSafe v0.8.13 Nepal-only truth map + fresh-gauge-only glow/flow PASS')
