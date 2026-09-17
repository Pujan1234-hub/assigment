from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.36: field request from real-device screenshot + reference video.
# MAP ONLY:
# - remove rain-station dots from the river map (rain data is still loaded and retained);
# - show the actual Nepal-wide OSM river/khola network as the video-style animated blue network;
# - tapping an actual river opens ONE simple card containing same-river official river status
#   plus the nearest official BIPAD/DHM rain reading, clearly labelled with distance;
# - never substitute another river gauge; 2 km alert/notification safety is untouched.

# 1) Rain data stays in memory but rain station markers are never painted on the river map.
rs=m.find('    private void refreshRainSources() {')
re_=m.find('    private void refreshUserSource() {',rs)
if rs<0 or re_<0:
    raise SystemExit('v0.8.36 refreshRainSources anchors missing')
rain_hidden=r'''    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        // RAIN_DATA_DETAIL_ONLY: rain stations are data for a river-detail card, not map dots.
        setGeo("fs-rain-stale", emptyFeatureCollection());
        setGeo("fs-rain-normal", emptyFeatureCollection());
        setGeo("fs-rain-alert", emptyFeatureCollection());
        setGeo("fs-rain-warning", emptyFeatureCollection());
        setGeo("fs-rain-danger", emptyFeatureCollection());
    }

'''
m=m[:rs]+rain_hidden+m[re_:]

# 2) River click only: actual river first, then an official river gauge if the user taps the gauge.
#    Rain stations are deliberately not clickable/visible as separate dots.
cs=m.find('    private boolean onMapClick(LatLng p) {')
ce=m.find('    private static boolean isSevereStage',cs)
if cs<0 or ce<0:
    raise SystemExit('v0.8.36 onMapClick anchors missing')
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.16,5.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}

        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.30,4.2/Math.pow(2.0,Math.max(0.0,zoom-6.0)));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        boolean stationShown=nearest!=null&&(zoom>=8.0||isSevereStage(nearest.stage));
        if(stationShown&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}
        return false;
    }

'''
m=m[:cs]+click+m[ce:]

# 3) One simple river card = same-river BIPAD/DHM gauge + nearby official rain reading.
#    Rain is explicitly called "nearby" and carries distance, so it can never be mistaken
#    for a river gauge or a same-river measurement.
ss=m.find('    private void showRiver(RiverWay r')
se=m.find('    private StationDot sameRiverGaugeFor(',ss)
if ss<0 or se<0:
    raise SystemExit('v0.8.36 showRiver anchors missing')
show=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot current=sameRiverGaugeFor(r,la,lo,true);
        StationDot known=current!=null?current:sameRiverGaugeFor(r,la,lo,false);
        RainDot rain=nearestRain(la,lo);
        double rainKm=rain==null?Double.MAX_VALUE:km(la,lo,rain.lat,rain.lon);
        // Very distant rain data is not useful for a local river tap.
        if(rainKm>50.0)rain=null;

        String title=(r==null||r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name))?"नदी / खोला":r.name;
        StringBuilder x=new StringBuilder();
        x.append("नदी स्थिति\n");
        if(current!=null){
            x.append("स्टेशन: ").append(current.name);
            if(Double.isFinite(current.level))x.append(String.format(Locale.US,"\nपानीको तह: %.2f m",current.level));
            String source=current.rawStatus==null?"":current.rawStatus.trim();
            x.append("\nअवस्था: ").append(source.isEmpty()?current.stage.toUpperCase(Locale.ROOT):source);
            if(Double.isFinite(current.warning))x.append(String.format(Locale.US,"\nसतर्क तह: %.2f m",current.warning));
            if(Double.isFinite(current.danger))x.append(String.format(Locale.US,"\nखतरा तह: %.2f m",current.danger));
            x.append("\nसमय: ").append(formatOfficialTime(current.at));
        }else if(known!=null){
            x.append("स्टेशन: ").append(known.name)
             .append("\nअहिलेको नयाँ नदी reading उपलब्ध छैन।")
             .append("\nअवस्था: STALE / UNKNOWN");
        }else{
            x.append("यस नदी/खोलासँग matching official नदी स्टेशन छैन।")
             .append("\nअर्को नदीको gauge data यहाँ राखिएको छैन।");
        }

        x.append("\n\nवर्षा\n");
        if(rain!=null){
            x.append("नजिकको आधिकारिक स्टेशन: ").append(rain.name)
             .append(String.format(Locale.US," • %.1f km",rainKm));
            if(rain.basin!=null&&!rain.basin.trim().isEmpty())x.append("\nBasin: ").append(rain.basin);
            if(Double.isFinite(rain.rainfall))x.append(String.format(Locale.US,"\n1 घण्टा: %.1f mm",rain.rainfall));
            if(Double.isFinite(rain.rain3))x.append(String.format(Locale.US,"\n3 घण्टा: %.1f mm",rain.rain3));
            if(Double.isFinite(rain.rain6))x.append(String.format(Locale.US,"\n6 घण्टा: %.1f mm",rain.rain6));
            if(Double.isFinite(rain.rain12))x.append(String.format(Locale.US,"\n12 घण्टा: %.1f mm",rain.rain12));
            if(Double.isFinite(rain.rain24))x.append(String.format(Locale.US,"\n24 घण्टा: %.1f mm",rain.rain24));
            x.append("\nReading: ").append(rain.fresh?"LATEST":"STALE / OLD");
            x.append("\nसमय: ").append(formatOfficialTime(rain.at));
        }else{
            x.append("नजिकको आधिकारिक वर्षा reading उपलब्ध छैन।");
        }
        x.append("\n\nस्रोत: BIPAD / DHM official • River geometry: OpenStreetMap");

        if(stationTapListener!=null){stationTapListener.onStationTap(new RiverTapInfo("🌊 "+title,x.toString()));return;}
        new AlertDialog.Builder(getContext()).setTitle(title).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
m=m[:ss]+show+m[se:]

# 4) Match the GitHub reference video: crisp cyan/blue whole-network core with a soft blue pulse.
#    Keep risk-colour overlays source-driven; this base is geographic river/khola context only.
replacements=[
    ('lineColor("#22C8FF"), lineWidth(3.20f), lineOpacity(1.0f)',
     'lineColor("#1EC8FF"), lineWidth(2.35f), lineOpacity(1.0f)'),
    ('lineColor("#0D8DFF"), lineWidth(8.0f), lineOpacity(0.42f)',
     'lineColor("#078BFF"), lineWidth(5.6f), lineOpacity(0.34f)'),
    ('lineWidth((float)(6.8+2.4*wave))','lineWidth((float)(4.8+1.6*wave))'),
    ('lineWidth((float)(2.8+0.65*wave))','lineWidth((float)(2.05+0.45*wave))'),
]
for old,new in replacements:
    if old in m:m=m.replace(old,new,1)

# Compatibility if v0.8.35 styling string differs slightly after earlier patch ordering.
m=m.replace('lineColor("#22C8FF"), lineWidth(2.20f), lineOpacity(1.0f)',
            'lineColor("#1EC8FF"), lineWidth(2.35f), lineOpacity(1.0f)',1)
m=m.replace('lineColor("#0D8DFF"), lineWidth(5.6f), lineOpacity(0.34f)',
            'lineColor("#078BFF"), lineWidth(5.6f), lineOpacity(0.34f)',1)
m=m.replace('lineColor("#0D8DFF"),','lineColor("#078BFF"),')
m=m.replace('lineColor("#22C8FF"),','lineColor("#1EC8FF"),')

# Version bump only; no alert/notification/home/SATHI/navigation changes.
g=g.replace('versionCode 55','versionCode 56',1).replace("versionName '0.8.35'","versionName '0.8.36'",1)
if 'versionCode 56' not in g or "versionName '0.8.36'" not in g:
    raise SystemExit('v0.8.36 version bump failed')

# Hard gates.
for marker in [
    'RAIN_DATA_DETAIL_ONLY',
    'setGeo("fs-rain-normal", emptyFeatureCollection())',
    'RainDot rain=nearestRain(la,lo)',
    'नजिकको आधिकारिक स्टेशन:',
    '1 घण्टा:',
    '24 घण्टा:',
    'new RiverTapInfo("🌊 "+title',
    'sameRiverGaugeFor(r,la,lo,true)',
    'lineColor("#1EC8FF")',
    'lineColor("#078BFF")',
    'private void refreshVisibleRiverTiles(){',
    'v835ReadRiverTile',
    'setGeo("fs-rivers",geo)',
    'routeD<=0.75']:
    if marker not in m:raise SystemExit('v0.8.36 marker missing: '+marker)
if 'RainDot rain=nearestRain(p.getLatitude(),p.getLongitude())' in m:
    raise SystemExit('v0.8.36 separate rain map click remained')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.36 VIDEO blue Nepal rivers + combined river/rain detail PASS')
