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

# v0.8.14 goals:
# - source-faithful status colours
# - current map reading <=30 min (emergency safety remains stricter elsewhere)
# - one nearest matching river segment per current official gauge
# - no O(rivers*stations) work on the UI animation tick
# - normal blue static; alert yellow; warning orange pulse; danger red pulse
# - lighter national river geometry for smooth touch/drag

# -----------------------------------------------------------------------------
# Activity: map-current means recent official observation, not merely same date.
# Prefer official source status text before threshold fallback.
# -----------------------------------------------------------------------------
activity=activity.replace(
    'boolean current=Double.isFinite(level)&&sameNepalCalendarDay(at,now);',
    'boolean current=Double.isFinite(level)&&at>0&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L;',1)

old_stage='''        if(current){\n            if((Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}\n            else if((Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}\n            else if(raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}\n            else{stage="normal";rank=3;}\n        }else{'''
new_stage='''        if(current){\n            // Source status wins. Thresholds are only a fallback when the source did not publish a status.\n            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}\n            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}\n            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}\n            else if(raw.contains("BELOW WARNING")||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("GREEN")){stage="normal";rank=3;}\n            else if(Double.isFinite(danger)&&danger>0&&level>=danger){stage="danger";rank=0;}\n            else if(Double.isFinite(warning)&&warning>0&&level>=warning){stage="warning";rank=1;}\n            else{stage="normal";rank=3;}\n        }else{'''
if old_stage not in activity: raise SystemExit('v0.8.12 source status stage block missing')
activity=activity.replace(old_stage,new_stage,1)

activity=activity.replace(
    'mapSub.setText(t("Grey नदी = geometry मात्र • रङ/Glow = आजको official gauge status","Grey rivers = geometry only • colour/glow = current official gauge status"));',
    'mapSub.setText(t("Grey=geometry • 🔵 Normal • 🟡 Alert • 🟠 Warning • 🔴 Danger — official source अनुसार","Grey=geometry • 🔵 Normal • 🟡 Alert • 🟠 Warning • 🔴 Danger — official source status"));',1)
activity=activity.replace(
    '"🌊 नदी आजको official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ वर्षा fresh "+mapRainFresh+" / "+mapRainTotal,',
    '"🌊 नदी current ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ वर्षा fresh "+mapRainFresh+" / "+mapRainTotal,',1)
activity=activity.replace(
    '"🌊 river current today "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain fresh "+mapRainFresh+" / "+mapRainTotal));',
    '"🌊 river current ≤30m "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain fresh "+mapRainFresh+" / "+mapRainTotal));',1)

# -----------------------------------------------------------------------------
# Map: reduce base geometry at national/local zoom. Detailed local tile still loads
# after camera idle, so zooming in keeps the useful river network without drawing
# 6k+ overview ways all the time.
# -----------------------------------------------------------------------------
helper=helper.replace(
    'List<RiverWay> base = new ArrayList<>(overviewRivers);',
    'int overviewKeep=Math.min(1400,overviewRivers.size());\n            List<RiverWay> base = new ArrayList<>(overviewRivers.subList(0,overviewKeep));',1)
helper=helper.replace(
    'int baseCount = Math.min(overviewRivers.size(), z < 8.4 ? 3200 : 1400);',
    'int baseCount = Math.min(overviewRivers.size(), z < 8.4 ? 900 : 350);',1)
helper=helper.replace('if(++count>=900)break;','if(++count>=180)break;',1)

# Current status layers: normal has no glow; alert subtle; warning/danger stronger.
status_pat=r'''    private void ensureRiverStatusLayer\(String sourceId,String layerId,String color\) \{.*?\n    \}\n'''
status_new=r'''    private void ensureRiverStatusLayer(String sourceId,String layerId,String color) {
        if(style==null||style.getSource(sourceId)!=null)return;
        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        boolean normal=layerId.contains("normal"), alert=layerId.contains("alert");
        float glowOpacity=normal?0.0f:(alert?0.14f:0.28f);
        float glowWidth=normal?0.1f:(alert?6.0f:8.2f);
        float coreWidth=normal?2.65f:(alert?3.2f:3.8f);
        style.addLayer(new LineLayer(layerId+"-glow",sourceId).withProperties(lineColor(color),lineWidth(glowWidth),lineOpacity(glowOpacity),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(coreWidth),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }
'''
helper,n=re.subn(status_pat,status_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('v0.8.13 status layer method missing')

# Build at most one nearest matching river segment per current official gauge.
# This mirrors source stations instead of colouring every same-name river way.
start=helper.find('    private String[] buildRiverStatusGeo(List<RiverWay> riverSnapshot,List<StationDot> stationSnapshot) {')
end=helper.find('    private static String featureCollection(JSONArray features)',start)
if start<0 or end<0: raise SystemExit('async river status builder anchors missing')
new_builder=r'''    private String[] buildRiverStatusGeo(List<RiverWay> riverSnapshot,List<StationDot> stationSnapshot) {
        try{
            JSONArray normal=new JSONArray(),alert=new JSONArray(),warning=new JSONArray(),danger=new JSONArray();
            java.util.HashSet<String> used=new java.util.HashSet<>();
            for(StationDot g:stationSnapshot){
                if(g==null||!g.fresh)continue;
                RiverWay r=nearestMatchingRiverForGauge(g,riverSnapshot,used);
                if(r==null)continue;
                String stage=normalizeStage(g.stage);
                JSONArray target;
                if("danger".equals(stage))target=danger;
                else if("warning".equals(stage))target=warning;
                else if("alert".equals(stage))target=alert;
                else target=normal;
                JSONArray coords=localRiverSegment(r,g.lat,g.lon);
                if(coords.length()<2)continue;
                JSONObject geom=new JSONObject().put("type","LineString").put("coordinates",coords);
                JSONObject props=new JSONObject().put("name",r.name).put("status",stage).put("gauge",g.name);
                target.put(new JSONObject().put("type","Feature").put("geometry",geom).put("properties",props));
            }
            return new String[]{featureCollection(normal),featureCollection(alert),featureCollection(warning),featureCollection(danger)};
        }catch(Exception e){String empty=emptyFeatureCollection();return new String[]{empty,empty,empty,empty};}
    }

    private RiverWay nearestMatchingRiverForGauge(StationDot g,List<RiverWay> riverSnapshot,java.util.HashSet<String> used){
        String sk=riverNameKey(g.name);if(sk.length()<3)return null;
        RiverWay best=null;double bestKm=Double.MAX_VALUE;String bestId="";
        for(RiverWay r:riverSnapshot){
            if(r==null||r.points.size()<2)continue;
            String rk=riverNameKey(r.name);if(rk.length()<3)continue;
            boolean exact=rk.equals(sk);
            boolean related=exact||(rk.length()>=4&&sk.length()>=4&&(rk.contains(sk)||sk.contains(rk)));
            if(!related)continue;
            double d=riverDistanceToGauge(r,g.lat,g.lon);
            double limit=exact?8.0:3.5;
            String id=riverKey(r);
            if(d<=limit&&d<bestKm&&!used.contains(id)){bestKm=d;best=r;bestId=id;}
        }
        if(best!=null)used.add(bestId);
        return best;
    }

    private static double riverDistanceToGauge(RiverWay r,double la,double lo){
        double best=Double.MAX_VALUE;int stride=Math.max(1,r.points.size()/120);
        for(int i=0;i<r.points.size();i+=stride){double[]p=r.points.get(i);best=Math.min(best,km(la,lo,p[1],p[0]));}
        return best;
    }

    private static JSONArray localRiverSegment(RiverWay r,double la,double lo){
        JSONArray out=new JSONArray();if(r==null||r.points.size()<2)return out;
        int nearest=0;double best=Double.MAX_VALUE;
        for(int i=0;i<r.points.size();i++){double[]p=r.points.get(i);double d=km(la,lo,p[1],p[0]);if(d<best){best=d;nearest=i;}}
        int radius=Math.min(90,Math.max(24,r.points.size()/5));
        int a=Math.max(0,nearest-radius),b=Math.min(r.points.size()-1,nearest+radius);
        if(b-a<1){a=0;b=r.points.size()-1;}
        for(int i=a;i<=b;i++){double[]p=r.points.get(i);out.put(new JSONArray().put(p[0]).put(p[1]));}
        return out;
    }

'''
helper=helper[:start]+new_builder+helper[end:]

# Eliminate the expensive particle loop. Pulse only the already-built severe
# status glow layers. No river/station scanning happens on the main UI thread.
pt_start=helper.find('    private final Runnable particleTick = new Runnable() {')
pt_end=helper.find('    private StationDot readStation(Object o) {',pt_start)
if pt_start<0 or pt_end<0: raise SystemExit('particleTick anchors missing')
new_tick=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if (!animationRunning || !styleReady || style == null) return;
            try {
                double ph=(System.currentTimeMillis()%1800L)/1800.0;
                float pulse=(float)(0.20+0.24*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));
                LineLayer warningGlow=style.getLayerAs("fs-river-warning-status-layer-glow");
                LineLayer dangerGlow=style.getLayerAs("fs-river-danger-status-layer-glow");
                if(warningGlow!=null)warningGlow.setProperties(lineOpacity(pulse),lineWidth(7.4f+1.6f*pulse));
                if(dangerGlow!=null)dangerGlow.setProperties(lineOpacity(Math.min(0.56f,pulse+0.10f)),lineWidth(8.6f+2.0f*pulse));
                setGeo("fs-flow-particles",emptyFeatureCollection());
            } catch (Exception ignored) {}
            main.postDelayed(this, 650L);
        }
    };

'''
helper=helper[:pt_start]+new_tick+helper[pt_end:]

# Debounce status publish a little more so camera/tile updates never fight touch.
helper=helper.replace('main.postDelayed(riverStatusKick, 240L);','main.postDelayed(riverStatusKick, 420L);',1)

# Version bump.
if "versionName '0.8.14'" not in gradle:
    gradle=gradle.replace('versionCode 33','versionCode 34',1)
    gradle=gradle.replace("versionName '0.8.13'","versionName '0.8.14'",1)
if 'versionCode 34' not in gradle or "versionName '0.8.14'" not in gradle: raise SystemExit('v0.8.14 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard checks.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for m in ['now-at<=30L*60L*1000L','Source status wins','BELOW WARNING','current ≤30m','🔵 Normal']:
    if m not in a: raise SystemExit('v0.8.14 activity marker missing: '+m)
for m in ['overviewKeep=Math.min(1400','z < 8.4 ? 900 : 350','if(++count>=180)break','nearestMatchingRiverForGauge','localRiverSegment','main.postDelayed(this, 650L)','fs-river-warning-status-layer-glow','main.postDelayed(riverStatusKick, 420L)']:
    if m not in h: raise SystemExit('v0.8.14 map marker missing: '+m)
if 'routeGaugeForSnapshot(rr,flowStations)' in h: raise SystemExit('expensive per-frame river/station scan remained')
if 'Math.min(80, flowRivers.size())' in h: raise SystemExit('old per-frame flow river build remained')
print('FloodSafe v0.8.14 source-exact status + smooth severe-only glow PASS')
