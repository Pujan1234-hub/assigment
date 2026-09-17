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

# v0.8.17: native map follows the proven web-map architecture:
# clean national major-river view, local nearby waterways, district labels,
# lightweight flowing-water animation, exact official gauge colours, and rain details.

# -----------------------------------------------------------------------------
# Activity: use the latest rain-station watch feed first; keep historical endpoints
# only as fallback. Map freshness is display-only and does not change emergency rules.
# -----------------------------------------------------------------------------
refresh_rain_pat=r'''    private void refreshRainStations\(\)\{.*?\n    \}\n\n    private RainStation parseRainStation'''
refresh_rain_new=r'''    private void refreshRainStations(){
        io.execute(()->{
            try{
                long now=System.currentTimeMillis(); JSONArray rr=new JSONArray();
                try{rr=rows(getJson(BIPAD+"rain-stations/?latest=true&limit=2000&_nativefull="+now));}catch(Exception ignored){}
                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain-trimed/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}
                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}
                List<RainStation> out=new ArrayList<>();
                for(int i=0;i<rr.length();i++){RainStation s=parseRainStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
                synchronized(rainStations){rainStations.clear();rainStations.addAll(out);} runOnUiThread(this::refreshRainUi);
            }catch(Exception ignored){runOnUiThread(this::refreshRainUi);}
        });
    }

    private RainStation parseRainStation'''
activity,n=re.subn(refresh_rain_pat,refresh_rain_new,activity,count=1,flags=re.S)
if n!=1: raise SystemExit('refreshRainStations block missing')

rain_parse_pat=r'''    private RainStation parseRainStation\(JSONObject r,long now\)\{.*?\n    \}\n\n    private void refreshRainUi'''
rain_parse_new=r'''    private RainStation parseRainStation(JSONObject r,long now){
        if(r==null)return null; JSONObject f=r.optJSONObject("fields"); double[] c=officialCoord(r); double a=c[0],o=c[1];
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double mm=numDeep(r,f,"_lastRainfall","lastRainfall","rainfall","rainFall","rain","rainfall24h","rainfall_24h","currentRainfall","lastValue","_lastValue","value");
        long at=parseTime(strDeep(r,f,"_measurementTime","_lastRainfallOn","rainfallOn","rainfall_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","updatedOn","updated_at","time"));
        // Rain gauges are often hourly; 90 minutes is a map-display freshness window only.
        boolean fresh=at>0&&now-at<=90L*60L*1000L&&at-now<=5*60_000L;
        String name=strDeep(r,f,"_stationName","stationName","station_name","title","name","locationName","location_name");
        JSONObject station=r.optJSONObject("station"); if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName"); if(name.isEmpty())name="Official rain station";
        String raw=strDeep(r,f,"status","status_name","_officialStatus").toUpperCase(Locale.ROOT), band="stale";
        if(fresh){
            if(raw.contains("DANGER")||raw.contains("RED"))band="danger";
            else if(raw.contains("WARNING")||raw.contains("ORANGE"))band="warning";
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW"))band="alert";
            else band="normal";
        }
        String basin=strDeep(r,f,"basin","basin_name","riverBasin","river_basin");
        return new RainStation(name,basin,a,o,mm,at,fresh,band,raw);
    }

    private void refreshRainUi'''
activity,n=re.subn(rain_parse_pat,rain_parse_new,activity,count=1,flags=re.S)
if n!=1: raise SystemExit('parseRainStation block missing')

# Cleaner wording: map is a live official gauge overlay on a geographic river network.
activity=activity.replace(
    'mapSub.setText(t("Current official source मात्र highlight: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER","Only current official source is highlighted: 🔵 BELOW WARNING/NORMAL • 🟡 ALERT • 🟠 WARNING • 🔴 DANGER"));',
    'mapSub.setText(t("जिल्ला + नदी network • 🔵 official gauge • 🟡 Alert • 🟠 Warning • 🔴 Danger","District + river network • 🔵 official gauge • 🟡 Alert • 🟠 Warning • 🔴 Danger"));',1)
activity=activity.replace('"🌊 current official ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • बाकी geometry hidden • 🌧️ rain "+mapRainFresh+" / "+mapRainTotal,',
                          '"🌊 current official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain latest "+mapRainFresh+" / "+mapRainTotal,',1)
activity=activity.replace('"🌊 current official ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • background geometry hidden • 🌧️ rain "+mapRainFresh+" / "+mapRainTotal));',
                          '"🌊 current official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain latest "+mapRainFresh+" / "+mapRainTotal));',1)

# -----------------------------------------------------------------------------
# Map: clean web-style river network. We intentionally do NOT render thousands of
# local streams at once. National view keeps major/named context; local view keeps
# the nearest 64 routes, matching the old web map's nearby-water behavior.
# -----------------------------------------------------------------------------
# Restore a subtle cyan geographic network instead of near-invisible or all-live styling.
helper=helper.replace('lineColor("#51646d"), lineWidth(0.80f), lineOpacity(0.025f)',
                      'lineColor("#063d4a"), lineWidth(3.8f), lineOpacity(0.42f)',1)
helper=helper.replace('lineColor("#78909c"), lineWidth(0.65f), lineOpacity(0.055f)',
                      'lineColor("#6fe7f6"), lineWidth(1.25f), lineOpacity(0.74f)',1)
# Compatibility if the first replacement did not match a generated variant.
helper=helper.replace('lineColor("#243f49"), lineWidth(3.2f), lineOpacity(0.24f)',
                      'lineColor("#063d4a"), lineWidth(3.8f), lineOpacity(0.42f)',1)
helper=helper.replace('lineColor("#78909c"), lineWidth(1.45f), lineOpacity(0.42f)',
                      'lineColor("#6fe7f6"), lineWidth(1.25f), lineOpacity(0.74f)',1)

# Re-enable generic river labels only for the small visible set; collisions stay off.
install_anchor='''            // v0.8.16: generic OSM river-name mesh hidden by default; official current station labels are authoritative.\n'''
labels_block='''            if (riverLabelsGeoJson != null && style.getSource("fs-river-labels") == null) {\n                style.addSource(new GeoJsonSource("fs-river-labels", riverLabelsGeoJson));\n                style.addLayer(new SymbolLayer("fs-river-labels-layer", "fs-river-labels").withProperties(\n                        textField("{name}"), textSize(9.5f), textColor("#bcecf6"),\n                        textHaloColor("#102a34"), textHaloWidth(1.5f), textAllowOverlap(false)));\n            }\n'''
if install_anchor in helper:
    helper=helper.replace(install_anchor,labels_block,1)
elif 'fs-river-labels-layer' not in helper:
    raise SystemExit('v0.8.16 river label marker missing')

# Replace progressive loader with a clean, bounded visible-set loader.
start=helper.find('    private void refreshVisibleRiverTiles() {')
end=helper.find('    private List<RiverWay> readRiverTile(',start)
if start<0 or end<0: raise SystemExit('refreshVisibleRiverTiles anchors missing')
loader=r'''    private void refreshVisibleRiverTiles() {
        if (!styleReady || style == null || map == null || overviewRivers.isEmpty()) return;
        CameraPosition cp = map.getCameraPosition();
        LatLng center = cp.target;
        if(!cameraTargetInsideNepal(center)){map.animateCamera(CameraUpdateFactory.newLatLng(NEPAL_CENTER),250);return;}
        final double zoom=cp.zoom;
        final int cx=Math.max(0,Math.min(11,(int)Math.floor((center.getLongitude()-80.0)/0.7)));
        final int cy=Math.max(0,Math.min(7,(int)Math.floor((center.getLatitude()-26.2)/0.6)));
        final int radius=zoom<8.2?1:0;
        final String key=(zoom<7.0?"national":cx+":"+cy+":"+radius+":"+(int)(zoom*2));
        if(key.equals(lastRiverTileKey))return;
        lastRiverTileKey=key;final int generation=++riverTileGeneration;
        final double cla=center.getLatitude(),clo=center.getLongitude();
        io.execute(()->{
            try{
                List<RiverWay> chosen=new ArrayList<>();
                if(zoom<7.0){
                    // National: major/named only. 420 keeps the full-country shape clean.
                    int keep=Math.min(420,overviewRivers.size());
                    chosen.addAll(overviewRivers.subList(0,keep));
                }else{
                    JSONObject districts=districtGeoJson==null?null:new JSONObject(districtGeoJson);
                    List<RiverWay> candidates=new ArrayList<>();java.util.HashSet<String> seen=new java.util.HashSet<>();
                    for(int x=Math.max(0,cx-radius);x<=Math.min(11,cx+radius);x++)for(int y=Math.max(0,cy-radius);y<=Math.min(7,cy+radius);y++){
                        for(RiverWay r:readRiverTile(x,y,districts)){String k=riverKey(r);if(seen.add(k))candidates.add(r);}
                    }
                    // Include a few major routes so context never disappears.
                    for(int i=0;i<Math.min(180,overviewRivers.size());i++){RiverWay r=overviewRivers.get(i);String k=riverKey(r);if(seen.add(k))candidates.add(r);}
                    candidates.sort((a,b)->Double.compare(webVisibleScore(b,cla,clo),webVisibleScore(a,cla,clo)));
                    int keep=Math.min(64,candidates.size());chosen.addAll(candidates.subList(0,keep));
                }
                String geo=makeRiversGeoJson(chosen),labels=makeRiverLabelsGeoJson(chosen);
                main.post(()->{if(generation!=riverTileGeneration)return;rivers.clear();rivers.addAll(chosen);riversGeoJson=geo;riverLabelsGeoJson=labels;setGeo("fs-rivers",geo);setGeo("fs-river-labels",labels);});
            }catch(Exception ignored){}
        });
    }

    private static double webVisibleScore(RiverWay r,double la,double lo){
        if(r==null||r.points.size()<2)return -1e9;double best=Double.MAX_VALUE;int stride=Math.max(1,r.points.size()/80);
        for(int i=0;i<r.points.size();i+=stride){double[]p=r.points.get(i);best=Math.min(best,km(la,lo,p[1],p[0]));}
        return ("river".equalsIgnoreCase(r.type)?120:0)+(r.name==null||r.name.trim().isEmpty()?0:55)+Math.min(45,r.points.size())-best*5.0;
    }

'''
helper=helper[:start]+loader+helper[end:]

# Status truth: normal does NOT paint a thick river segment; its blue station dot is
# enough. Alert/Warning/Danger colour the matched segment like the old live web map.
status_pat=r'''    private void ensureRiverStatusLayer\(String sourceId,String layerId,String color\) \{.*?\n    \}\n'''
status_new=r'''    private void ensureRiverStatusLayer(String sourceId,String layerId,String color) {
        if(style==null||style.getSource(sourceId)!=null)return;
        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        boolean normal=layerId.contains("normal"),alert=layerId.contains("alert"),warning=layerId.contains("warning"),danger=layerId.contains("danger");
        float glowOpacity=normal?0.0f:(alert?0.18f:(warning?0.34f:0.42f));
        float glowWidth=normal?0.1f:(alert?5.2f:(warning?7.2f:9.0f));
        float coreWidth=normal?0.1f:(alert?2.55f:(warning?3.35f:4.0f));
        float coreOpacity=normal?0.0f:1.0f;
        style.addLayer(new LineLayer(layerId+"-glow",sourceId).withProperties(lineColor(color),lineWidth(glowWidth),lineOpacity(glowOpacity),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(coreWidth),lineOpacity(coreOpacity),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }
'''
helper,n=re.subn(status_pat,status_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('ensureRiverStatusLayer replacement failed')

# Restore the old web-map feel: lightweight moving beads on the currently visible
# river set only. No station/risk matching happens in this animation loop.
pt_start=helper.find('    private final Runnable particleTick = new Runnable() {')
pt_end=helper.find('    private StationDot readStation(Object o) {',pt_start)
if pt_start<0 or pt_end<0: raise SystemExit('particle tick anchors missing')
new_tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if(!animationRunning||!styleReady||style==null)return;
            try{
                List<RiverWay> visibleSnapshot=new ArrayList<>(rivers);
                JSONArray features=new JSONArray();int n=Math.min(30,visibleSnapshot.size());
                double phase=((System.currentTimeMillis()-particleStart)%6000L)/6000.0;
                for(int i=0;i<n;i++){
                    RiverWay r=visibleSnapshot.get(i);if(r==null||r.points.size()<2)continue;
                    double v=((phase+i*.173)%1.0)*(r.points.size()-1);int ix=Math.min(r.points.size()-2,(int)Math.floor(v));double f=v-ix;
                    double[]a=r.points.get(ix),b=r.points.get(ix+1);features.put(pointFeature(a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,"flow"));
                }
                setGeo("fs-flow-particles",new JSONObject().put("type","FeatureCollection").put("features",features).toString());
                try{LineLayer trace=style.getLayerAs("fs-river-flow-trace");if(trace!=null){double ph=(System.currentTimeMillis()%1800L)/1800.0;float op=(float)(0.22+0.22*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));trace.setProperties(lineOpacity(op),lineWidth(0.85f));}}catch(Exception ignored){}
                try{double ph=(System.currentTimeMillis()%1800L)/1800.0;float pulse=(float)(0.26+0.18*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));LineLayer w=style.getLayerAs("fs-river-warning-status-layer-glow"),d=style.getLayerAs("fs-river-danger-status-layer-glow");if(w!=null)w.setProperties(lineOpacity(pulse));if(d!=null)d.setProperties(lineOpacity(Math.min(.58f,pulse+.14f)));}catch(Exception ignored){}
            }catch(Exception ignored){}
            main.postDelayed(this,180L);
        }
    };

'''
helper=helper[:pt_start]+new_tick+helper[pt_end:]

# Make sure a visible flow-trace layer exists for the current geographic river set.
if 'fs-river-flow-trace' not in helper:
    core='''                style.addLayer(new LineLayer("fs-rivers-layer", "fs-rivers").withProperties(\n                        lineColor("#6fe7f6"), lineWidth(1.25f), lineOpacity(0.74f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
    trace=core+'''\n                style.addLayer(new LineLayer("fs-river-flow-trace", "fs-rivers").withProperties(\n                        lineColor("#d9fbff"), lineWidth(0.85f), lineOpacity(0.30f), lineCap(LINE_CAP_ROUND), lineJoin(LINE_JOIN_ROUND)));'''
    if core not in helper: raise SystemExit('river core layer anchor missing')
    helper=helper.replace(core,trace,1)

# Rain detail: include basin + latest/old wording. RainDot stores basin too.
helper=helper.replace('private void showRain(RainDot r){StringBuilder m=new StringBuilder();m.append("Official rain station");if(Double.isFinite(r.rainfall))m.append(String.format(Locale.US,"\\nवर्षा: %.1f mm",r.rainfall));m.append("\\nStatus: ").append(r.fresh?r.band.toUpperCase(Locale.ROOT):"STALE / UNKNOWN");m.append("\\nOfficial time: ").append(formatOfficialTime(r.at));if(r.rawStatus!=null&&!r.rawStatus.isEmpty())m.append("\\nBIPAD: ").append(r.rawStatus);new AlertDialog.Builder(getContext()).setTitle("🌧️ "+r.name).setMessage(m.toString()).setPositiveButton("ठीक छ",null).show();}',
'''private void showRain(RainDot r){StringBuilder m=new StringBuilder();m.append("BIPAD/DHM official rain station");if(r.basin!=null&&!r.basin.isEmpty())m.append("\\nBasin: ").append(r.basin);if(Double.isFinite(r.rainfall))m.append(String.format(Locale.US,"\\nRainfall: %.1f mm",r.rainfall));else m.append("\\nRainfall: —");m.append("\\nReading: ").append(r.fresh?"LATEST":"STALE / OLD");m.append("\\nOfficial time: ").append(formatOfficialTime(r.at));if(r.rawStatus!=null&&!r.rawStatus.isEmpty())m.append("\\nSource status: ").append(r.rawStatus);new AlertDialog.Builder(getContext()).setTitle("🌧️ "+r.name).setMessage(m.toString()).setPositiveButton("ठीक छ",null).show();}''',1)
helper=helper.replace('r.name=getString(c,o,"name","Official rain station");r.band=getString(c,o,"band","stale");',
                      'r.name=getString(c,o,"name","Official rain station");r.basin=getString(c,o,"basin","");r.band=getString(c,o,"band","stale");',1)
helper=helper.replace('private static final class RainDot { String name,band,rawStatus; double lat,lon,rainfall; long at; boolean fresh; }',
                      'private static final class RainDot { String name,basin,band,rawStatus; double lat,lon,rainfall; long at; boolean fresh; }',1)

# Keep current official station labels compact: only severe station labels at national
# view are needed; district labels remain the main labels. Hide generic station labels.
helper=helper.replace('setGeo("fs-station-labels", stationGeoAll(snapshot));','setGeo("fs-station-labels", emptyFeatureCollection());',1)

# Version bump.
if "versionName '0.8.17'" not in gradle:
    gradle=gradle.replace('versionCode 36','versionCode 37',1)
    gradle=gradle.replace("versionName '0.8.16'","versionName '0.8.17'",1)
if 'versionCode 37' not in gradle or "versionName '0.8.17'" not in gradle: raise SystemExit('v0.8.17 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard assertions.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for m in ['rain-stations/?latest=true','_lastRainfall','90L*60L*1000L','District + river network']:
    if m not in a: raise SystemExit('v0.8.17 activity marker missing: '+m)
for m in ['Math.min(420,overviewRivers.size())','Math.min(64,candidates.size())','webVisibleScore','Math.min(30,visibleSnapshot.size())','main.postDelayed(this,180L)','coreOpacity=normal?0.0f','fs-river-labels-layer','RainDot { String name,basin']:
    if m not in h: raise SystemExit('v0.8.17 map marker missing: '+m)
if 'routeGaugeForSnapshot(rr,flowStations)' in h: raise SystemExit('heavy station scan returned to animation loop')
print('FloodSafe v0.8.17 clean web-style native map + rain detail PASS')
