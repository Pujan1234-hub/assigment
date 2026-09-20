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

# v0.8.74 is a regression-only map repair on top of v0.8.73:
# - rainfall remains official detail/alert data, but is NOT a standalone map-dot layer
# - canonical 77 district names come from the bundled Nepal district GeoJSON, never numeric IDs
# - river flow/glow and risk geometry are drawn below the strict Nepal outside mask
# - camera target is constrained to Nepal bounds
# - v0.8.71/v0.8.72 one-second official source polling, popup refresh, source-exact values,
#   status colours, river taps and background monitoring remain untouched.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# 1) Restore the accepted river-only map. Rain is still refreshed every second and remains
# available inside gauge detail/alerts; only standalone rainfall dots are removed.
sp=method_span(a,'refreshRainUi')
if not sp:raise SystemExit('v0874 refreshRainUi missing')
a=a[:sp[0]]+r'''    private void refreshRainUi(){
        List<RainStation> copy;synchronized(rainStations){copy=new ArrayList<>(rainStations);}
        int current=0;for(RainStation s:copy)if(s!=null&&s.fresh&&s.at>0L)current++;
        mapRainFresh=current;mapRainTotal=copy.size();
        if(map!=null)map.setRainStations(new ArrayList<>()); // V0874_RAIN_DETAIL_ONLY_NO_MAP_DOTS
        updateMapHintCounts();
    }
'''+a[sp[1]:]

sp=method_span(m,'refreshRainSources')
if not sp:raise SystemExit('v0874 map refreshRainSources missing')
m=m[:sp[0]]+r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        String e=emptyFeatureCollection();
        setGeo("fs-rain-stale",e);setGeo("fs-rain-normal",e);setGeo("fs-rain-alert",e);setGeo("fs-rain-warning",e);setGeo("fs-rain-danger",e);
    } // V0874_HIDE_RAIN_ONLY_MAP_STATIONS
'''+m[sp[1]:]

# Rain points are no longer a map tap target. River gauge -> live source detail still includes
# the nearest official rainfall/AWS observation through the existing detail path.
sp=method_span(m,'onMapClick')
if not sp:raise SystemExit('v0874 map onMapClick missing')
m=m[:sp[0]]+r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;
        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);return true;}
        RiverWay r=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(r!=null){showRiver(r,p.getLatitude(),p.getLongitude());return true;}
        return false;
    } // V0874_RIVER_AND_GAUGE_TAPS_ONLY
'''+m[sp[1]:]

# 2) District IDs from BIPAD are metadata IDs, not display names. Always normalize every
# parsed station by coordinate through the exact bundled 77-district polygons.
sp=method_span(a,'parseStation')
if not sp:raise SystemExit('v0874 parseStation missing')
block=a[sp[0]:sp[1]]
if 'V0874_NORMALIZE_DISTRICT_NAME' not in block:
    pos=block.rfind('return new RiverStation')
    if pos<0:raise SystemExit('v0874 parseStation return missing')
    block=block[:pos]+'district=v848DistrictName(a,o,district); // V0874_NORMALIZE_DISTRICT_NAME\n        '+block[pos:]
    a=a[:sp[0]]+block+a[sp[1]:]

sp=method_span(a,'showDistrictPicker')
if not sp:raise SystemExit('v0874 showDistrictPicker missing')
a=a[:sp[0]]+r'''    private void showDistrictPicker(){
        java.util.TreeSet<String> names=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        try{
            JSONObject root=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=root.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i),p=f==null?null:f.optJSONObject("properties");String n=p==null?"":p.optString("nameEn","").trim();if(!n.isEmpty()&&!n.matches("\\d+"))names.add(n);}
        }catch(Exception ignored){}
        if(names.size()!=77){
            synchronized(stations){for(RiverStation s:stations){String n=s==null||s.district==null?"":s.district.trim();if(!n.isEmpty()&&!n.matches("\\d+"))names.add(n);}}
        }
        if(names.isEmpty()){new AlertDialog.Builder(this).setMessage(t("जिल्ला data refresh हुँदैछ।","District data is refreshing.")).setPositiveButton("OK",null).show();return;}
        String[] x=names.toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle(t("जिल्ला छान्नुहोस्","Choose district")).setItems(x,(d,w)->{selectedDistrict=x[w];districtPicker.setText(selectedDistrict+" ▾");refreshRiverUi();}).setNegativeButton(t("बन्द","Close"),null).show();
    } // V0874_CANONICAL_77_DISTRICT_NAMES
'''+a[sp[1]:]

# 3) Nepal-fixed camera target. The irregular national border is enforced visually by the
# strict outside mask; these bounds prevent panning the target away from Nepal.
m=m.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();',
            '.include(new LatLng(NEPAL_MIN_LAT, NEPAL_MIN_LON))\n                        .include(new LatLng(NEPAL_MAX_LAT, NEPAL_MAX_LON)).build(); // V0874_NEPAL_FIXED_CAMERA',1)

# 4) The outside mask was installed before later moving-glow/risk layers. Re-create those
# later layers BELOW the mask so no cyan/status river can paint across India/China.
sp=method_span(m,'ensureV847FlowLayers')
if not sp:raise SystemExit('v0874 ensureV847FlowLayers missing')
m=m[:sp[0]]+r'''    private void ensureV847FlowLayers(){
        if(!styleReady||style==null)return;
        try{
            if(style.getSource("fs-river-flow-anim")==null)style.addSource(new GeoJsonSource("fs-river-flow-anim",emptyFeatureCollection()));
            LineLayer halo=style.getLayerAs("fs-river-flow-anim-halo");
            if(halo==null){LineLayer x=new LineLayer("fs-river-flow-anim-halo","fs-river-flow-anim").withProperties(lineColor("#65E9FF"),lineWidth(7.2f),lineOpacity(0.52f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND));if(style.getLayer("fs-nepal-outside-mask-layer")!=null)style.addLayerBelow(x,"fs-nepal-outside-mask-layer");else style.addLayer(x);}
            LineLayer core=style.getLayerAs("fs-river-flow-anim-core");
            if(core==null){LineLayer x=new LineLayer("fs-river-flow-anim-core","fs-river-flow-anim").withProperties(lineColor("#F0FEFF"),lineWidth(2.15f),lineOpacity(0.96f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND));if(style.getLayer("fs-nepal-outside-mask-layer")!=null)style.addLayerBelow(x,"fs-nepal-outside-mask-layer");else style.addLayer(x);}
        }catch(Exception ignored){}
    } // V0874_FLOW_BELOW_NEPAL_MASK
'''+m[sp[1]:]

sp=method_span(m,'ensureRiskLineSource')
if not sp:raise SystemExit('v0874 ensureRiskLineSource missing')
m=m[:sp[0]]+r'''    private void ensureRiskLineSource(String sourceId,String layerId,String color,float width){
        if(style.getSource(sourceId)==null)style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        if(style.getLayer(layerId)==null){LineLayer x=new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(width),lineOpacity(0.96f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND));if(style.getLayer("fs-nepal-outside-mask-layer")!=null)style.addLayerBelow(x,"fs-nepal-outside-mask-layer");else style.addLayer(x);}
    } // V0874_RISK_BELOW_NEPAL_MASK
'''+m[sp[1]:]

# 5) Release identity only.
if 'versionCode 93' in g:g=g.replace('versionCode 93','versionCode 94',1)
elif 'versionCode 94' not in g:raise SystemExit('v0874 versionCode anchor missing')
if "versionName '0.8.73'" in g:g=g.replace("versionName '0.8.73'","versionName '0.8.74'",1)
elif "versionName '0.8.74'" not in g:raise SystemExit('v0874 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0874_RAIN_DETAIL_ONLY_NO_MAP_DOTS','V0874_NORMALIZE_DISTRICT_NAME','V0874_CANONICAL_77_DISTRICT_NAMES','V0871_ONE_SECOND_SOURCE_RECHECK','V0871_SOURCE_EXACT_DETAIL','V0871_OPEN_POPUP_LIVE_UPDATE']:
    if x not in a:raise SystemExit('v0874 activity contract missing: '+x)
for x in ['V0874_HIDE_RAIN_ONLY_MAP_STATIONS','V0874_RIVER_AND_GAUGE_TAPS_ONLY','V0874_FLOW_BELOW_NEPAL_MASK','V0874_RISK_BELOW_NEPAL_MASK','V0874_NEPAL_FIXED_CAMERA','V0872_REFRESH_RIVER_STATUS_COLOURS','V0847_MOVING_GLOW']:
    if x not in m:raise SystemExit('v0874 map contract missing: '+x)
if 'V0873_ALL_RAIN_STATIONS_VISIBLE' in m:raise SystemExit('v0874 rain-dot regression remained')
if 'versionCode 94' not in g or "versionName '0.8.74'" not in g:raise SystemExit('v0874 version failed')
print('FloodSafe v0.8.74 PASS: Nepal-fixed rivers/glow + canonical 77 districts + hidden rain dots; 1s official detail preserved')
