from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')
if 'V0902_STATUS_FLOW_DISTRICT' in s:
    print('v0.9.02 map status/flow patch already applied');raise SystemExit(0)

def method_span(text,name):
    m=re.search(r'(?m)^\s*(?:private|public|protected)?\s+(?:static\s+)?[^\n{;]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^\{]+)?\{',text)
    if not m:return None
    op=text.find('{',m.start());depth=0;quote=None;esc=False
    for i in range(op,len(text)):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return m.start(),i+1
    return None

def replace_method(text,name,block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('missing '+name)
    return text[:sp[0]]+block+text[sp[1]:]

def insert_before(text,name,block,marker):
    if marker in text:return text
    sp=method_span(text,name)
    if not sp:raise SystemExit('missing anchor '+name)
    return text[:sp[0]]+block+text[sp[0]:]

# Imports for native scrollable map detail dialog.
s=s.replace('import android.widget.FrameLayout;','import android.widget.FrameLayout;\nimport android.widget.ScrollView;\nimport android.widget.TextView;',1)

anchor='    private volatile int monitoredSourceFeatureCount = 0;\n'
if anchor not in s:raise SystemExit('map field anchor missing')
s=s.replace(anchor,anchor+'''    private final java.util.IdentityHashMap<RiverWay,String> riverStatusBySegment = new java.util.IdentityHashMap<>();\n    private volatile String selectedDistrictFilter = "";\n''',1)

# Insert district navigation before zoomBy.
district=r'''    void setDistrictFilter(String district) {
        selectedDistrictFilter = district == null ? "" : district.trim();
        refreshStationSources();
    }

    void focusDistrict(String district) {
        if (map == null || districtGeoJson == null || district == null || district.trim().isEmpty()) { resetView(); return; }
        try {
            JSONObject root = new JSONObject(districtGeoJson);
            JSONArray fs = root.optJSONArray("features");
            if (fs == null) return;
            String wanted = districtKey(district);
            double[] b = {Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY};
            boolean found = false;
            for (int i=0;i<fs.length();i++) {
                JSONObject f=fs.optJSONObject(i), pr=f==null?null:f.optJSONObject("properties");
                if (pr==null || !wanted.equals(districtKey(pr.optString("nameEn","")))) continue;
                JSONObject g=f.optJSONObject("geometry"); if(g==null)continue;
                collectBounds(g.optJSONArray("coordinates"),b); found=Double.isFinite(b[0]); break;
            }
            if (!found) return;
            LatLngBounds bounds = new LatLngBounds.Builder().include(new LatLng(b[0],b[2])).include(new LatLng(b[1],b[3])).build();
            map.animateCamera(CameraUpdateFactory.newLatLngBounds(bounds, 52), 600);
            android.util.Log.i("FloodSafeDistrict","map_focus_district="+district);
        } catch(Exception e){android.util.Log.w("FloodSafeDistrict","district focus failed",e);}
    }

    private static void collectBounds(JSONArray a,double[] b){
        if(a==null)return;
        if(a.length()>=2 && a.opt(0) instanceof Number && a.opt(1) instanceof Number){
            double lo=a.optDouble(0,Double.NaN),la=a.optDouble(1,Double.NaN);
            if(Double.isFinite(la)&&Double.isFinite(lo)){b[0]=Math.min(b[0],la);b[1]=Math.max(b[1],la);b[2]=Math.min(b[2],lo);b[3]=Math.max(b[3],lo);}return;
        }
        for(int i=0;i<a.length();i++)collectBounds(a.optJSONArray(i),b);
    }
    private static String districtKey(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]","");}

'''
s=insert_before(s,'zoomBy',district,'map_focus_district=')

# Install status-colored flow point sources and green normal station dots.
old='            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#e3fdff", 2.35f, 0.92f);\n            ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);\n            ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f);'
new='''            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#bdf7ff", 2.35f, 0.94f);\n            ensurePointSource("fs-flow-alert", "fs-flow-alert-layer", "#ffd43b", 2.65f, 1f);\n            ensurePointSource("fs-flow-warning", "fs-flow-warning-layer", "#ff8a1f", 2.85f, 1f);\n            ensurePointSource("fs-flow-danger", "fs-flow-danger-layer", "#f22f4b", 3.05f, 1f);\n            ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);\n            ensurePointSource("fs-normal", "fs-normal-layer", "#27a65b", 4.6f, 0.99f);'''
if old not in s:raise SystemExit('point source color anchor missing')
s=s.replace(old,new,1)

station_sources=r'''    private void refreshStationSources() {
        if (!styleReady || style == null) return;
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        if (!selectedDistrictFilter.isEmpty()) {
            List<StationDot> filtered=new ArrayList<>();
            String wanted=districtKey(selectedDistrictFilter);
            for(StationDot st:snapshot)if(wanted.equals(districtKey(st.district)))filtered.add(st);
            snapshot=filtered;
        }
        setGeo("fs-stale", stationGeo(snapshot, "stale"));
        setGeo("fs-normal", stationGeo(snapshot, "normal"));
        setGeo("fs-alert", stationGeo(snapshot, "alert"));
        setGeo("fs-warning", stationGeo(snapshot, "warning"));
        setGeo("fs-danger", stationGeo(snapshot, "danger"));
        int stale=0,normal=0,alert=0,warning=0,danger=0;
        for(StationDot st:snapshot){String g=st.fresh?normalizeStage(st.stage):"stale";if("normal".equals(g))normal++;else if("alert".equals(g))alert++;else if("warning".equals(g))warning++;else if("danger".equals(g))danger++;else stale++;}
        android.util.Log.i("FloodSafeStationColor","station_sources normal_green="+normal+" alert_yellow="+alert+" warning_orange="+warning+" danger_red="+danger+" stale_grey="+stale);
    } // V0902_GREEN_NORMAL_STALE_GREY
'''
s=replace_method(s,'refreshStationSources',station_sources)

risk=r'''    private void refreshRiskRiverSources() {
        if (!styleReady || style == null) return;
        java.util.LinkedHashSet<RiverWay> alert = new java.util.LinkedHashSet<>();
        java.util.LinkedHashSet<RiverWay> warning = new java.util.LinkedHashSet<>();
        java.util.LinkedHashSet<RiverWay> danger = new java.util.LinkedHashSet<>();
        java.util.IdentityHashMap<RiverWay,String> status = new java.util.IdentityHashMap<>();
        synchronized(monitoredRivers){for(RiverWay r:monitoredRivers)status.put(r,"stale");}
        List<StationDot> snapshot;
        synchronized (stations) { snapshot = new ArrayList<>(stations); }
        for (StationDot st : snapshot) {
            List<RiverWay> linked=stationSegments(st); if(linked.isEmpty())continue;
            String group=st.fresh?normalizeStage(st.stage):"stale";
            for(RiverWay r:linked){String old=status.get(r);if(severity(group)>severity(old))status.put(r,group);}
        }
        for(java.util.Map.Entry<RiverWay,String> e:status.entrySet()){
            if("danger".equals(e.getValue()))danger.add(e.getKey());
            else if("warning".equals(e.getValue()))warning.add(e.getKey());
            else if("alert".equals(e.getValue()))alert.add(e.getKey());
        }
        synchronized(riverStatusBySegment){riverStatusBySegment.clear();riverStatusBySegment.putAll(status);}
        setGeo("fs-river-alert-risk", makeRiversGeoJsonSafe(new ArrayList<>(alert)));
        setGeo("fs-river-warning-risk", makeRiversGeoJsonSafe(new ArrayList<>(warning)));
        setGeo("fs-river-danger-risk", makeRiversGeoJsonSafe(new ArrayList<>(danger)));
        int normal=0,stale=0;for(String g:status.values()){if("normal".equals(g))normal++;else if("stale".equals(g))stale++;}
        android.util.Log.i("FloodSafeRiverColor","river_status_features normal_cyan="+normal+" alert_yellow="+alert.size()+" warning_orange="+warning.size()+" danger_red="+danger.size()+" stale_neutral="+stale);
    } // V0902_RIVER_COLOUR_FOLLOWS_STATION_STATUS
'''
s=replace_method(s,'refreshRiskRiverSources',risk)

# Insert severity helper before distance method.
helper=r'''    private static int severity(String s){
        if("danger".equals(s))return 4;if("warning".equals(s))return 3;if("alert".equals(s))return 2;if("normal".equals(s))return 1;return 0;
    }
    private String segmentStatus(RiverWay r){synchronized(riverStatusBySegment){String s=riverStatusBySegment.get(r);return s==null?"stale":s;}}

'''
s=insert_before(s,'distanceToMatchedRiverKm',helper,'private static int severity(')

show=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot gauge = bestGaugeForRiver(r, la, lo);
        StringBuilder msg = new StringBuilder();
        if (gauge != null) {
            double d = km(la, lo, gauge.lat, gauge.lon);
            msg.append("Same-river official gauge: ").append(gauge.name).append(String.format(Locale.US, " • %.1f km", d));
            if(!empty(gauge.district))msg.append("\nDistrict: ").append(gauge.district);
            if(!empty(gauge.basin))msg.append("\nBasin: ").append(gauge.basin);
            if (Double.isFinite(gauge.level)) msg.append(String.format(Locale.US, "\nWater level: %.2f m", gauge.level));
            if (gauge.at > 0L) msg.append("\nOfficial observation: ").append(java.time.Instant.ofEpochMilli(gauge.at).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
            if (gauge.fresh) msg.append("\nStatus: ").append(normalizeStage(gauge.stage).toUpperCase(Locale.ROOT)).append(" • CURRENT official");
            else msg.append("\nStatus: HISTORICAL / STALE • last known reading\nThis old reading is not used for warning colours or alerts.");
            String rain = DhmRainMirror.detailFor(gauge.name,gauge.riverName,gauge.district,gauge.basin,gauge.lat,gauge.lon);
            msg.append("\n\n").append(rain != null ? rain : "No safely matched fresh official rainfall reading available.");
        } else {
            msg.append("No safely matched same-river official gauge was found for this river geometry.\nNo safely matched fresh official rainfall reading available.");
        }
        msg.append("\n\nRiver geometry: bundled station-linked Nepal waterways");
        showScrollableDialog(r.name,msg.toString());
    } // V0902_SCROLLABLE_RIVER_DETAIL_RAIN
'''
s=replace_method(s,'showRiver',show)

scroll=r'''    private void showScrollableDialog(String title,String message){
        ScrollView sv=new ScrollView(getContext());int pad=dp(18);sv.setPadding(pad,dp(8),pad,dp(8));sv.setFillViewport(false);
        TextView body=new TextView(getContext());body.setText(message);body.setTextSize(14);body.setTextColor(Color.rgb(30,52,72));body.setSingleLine(false);body.setHorizontallyScrolling(false);body.setTextIsSelectable(true);
        sv.addView(body,new ScrollView.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.WRAP_CONTENT));
        int screenH=getResources().getDisplayMetrics().heightPixels,maxH=Math.min((int)(screenH*0.64f),dp(620));sv.setLayoutParams(new LayoutParams(LayoutParams.MATCH_PARENT,maxH));
        AlertDialog d=new AlertDialog.Builder(getContext()).setTitle(title).setView(sv).setPositiveButton("OK",null).create();
        d.setOnShowListener(x->android.util.Log.i("FloodSafeDialog","river_scroll_dialog_shown maxHeight="+maxH+" title="+title));d.show();
    }
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}

'''
s=insert_before(s,'startParticles',scroll,'river_scroll_dialog_shown')

particles=r'''    private final Runnable particleTick = new Runnable() {
        @Override public void run() {
            if (!animationRunning || !styleReady || style == null) return;
            try {
                List<RiverWay> visible;synchronized (monitoredRivers) { visible = new ArrayList<>(monitoredRivers); }
                JSONArray normal=new JSONArray(),alert=new JSONArray(),warning=new JSONArray(),danger=new JSONArray();
                int n=visible.size();double phase=((System.currentTimeMillis()-particleStart)%5600L)/5600.0;
                for(int i=0;i<n;i++){
                    RiverWay r=visible.get(i);if(r.points.size()<2)continue;
                    double v=((phase+i*0.137)%1.0)*(r.points.size()-1);int ix=Math.min(r.points.size()-2,(int)Math.floor(v));double f=v-ix;
                    double[] aa=r.points.get(ix),bb=r.points.get(ix+1);double lo=aa[0]+(bb[0]-aa[0])*f,la=aa[1]+(bb[1]-aa[1])*f;
                    String g=segmentStatus(r);JSONObject point=pointFeature(lo,la,"flow");
                    if("danger".equals(g))danger.put(point);else if("warning".equals(g))warning.put(point);else if("alert".equals(g))alert.put(point);else normal.put(point);
                }
                setGeo("fs-flow-particles",featureCollection(normal));setGeo("fs-flow-alert",featureCollection(alert));setGeo("fs-flow-warning",featureCollection(warning));setGeo("fs-flow-danger",featureCollection(danger));
                double wave=0.5+0.5*Math.sin(System.currentTimeMillis()/520.0);pulseLine("fs-river-glow",5.8f,0.50f,wave);pulseLine("fs-rivers-layer",2.35f,0.99f,wave);
                pulseStatus("fs-river-alert-risk-layer",3.4f,wave);pulseStatus("fs-river-warning-risk-layer",4.0f,wave);pulseStatus("fs-river-danger-risk-layer",4.6f,wave);
                animationFrameCount++;
                if(animationFrameCount==1||animationFrameCount%30L==0L)android.util.Log.i("FloodSafeRiver","flow_frame="+animationFrameCount+" animated_station_features="+n+" source_features="+monitoredSourceFeatureCount+" normal_flow="+normal.length()+" alert_flow="+alert.length()+" warning_flow="+warning.length()+" danger_flow="+danger.length());
            }catch(Exception e){android.util.Log.w("FloodSafeRiver","status flow frame failed",e);}
            main.postDelayed(this,180L);
        }
    }; // V0902_STATUS_COLOURED_FLOW_GLOW
'''
# replace field Runnable block using method_span doesn't work; locate exact range from declaration to marker.
start=s.find('    private final Runnable particleTick = new Runnable() {')
end=s.find('    private StationDot readStation',start)
if start<0 or end<0:raise SystemExit('particleTick block missing')
s=s[:start]+particles+'\n'+s[end:]

pulse=r'''    private static String featureCollection(JSONArray f){try{return new JSONObject().put("type","FeatureCollection").put("features",f).toString();}catch(Exception e){return emptyFeatureCollection();}}
    private void pulseLine(String id,float baseWidth,float baseOpacity,double wave){try{LineLayer l=style.getLayerAs(id);if(l!=null)l.setProperties(lineWidth((float)(baseWidth+(id.contains("glow")?0.8:0.24)*wave)),lineOpacity((float)Math.min(1.0,baseOpacity+0.08*wave)));}catch(Exception ignored){}}
    private void pulseStatus(String id,float width,double wave){try{LineLayer core=style.getLayerAs(id);if(core!=null)core.setProperties(lineWidth((float)(width+0.30*wave)));LineLayer glow=style.getLayerAs(id+"-glow");if(glow!=null)glow.setProperties(lineWidth((float)(width+3.1+0.70*wave)),lineOpacity((float)(0.25+0.12*wave)));}catch(Exception ignored){}}

'''
s=insert_before(s,'readStation',pulse,'private void pulseStatus(')

# Basin bridge.
old='            s.district = getString(c, o, "district", "");\n            s.stationId = getString(c, o, "stationId", "");'
new='            s.district = getString(c, o, "district", "");\n            s.basin = getString(c, o, "basin", "");\n            s.stationId = getString(c, o, "stationId", "");'
if old not in s:raise SystemExit('station basin bridge anchor missing')
s=s.replace(old,new,1)
s=s.replace('Object original; String stationId, name, riverName, district, stage; double lat, lon, level; long at; boolean fresh;','Object original; String stationId, name, riverName, district, basin, stage; double lat, lon, level; long at; boolean fresh;',1)

# Marker.
s=s.replace('final class FloodSafeNativeMapView extends FrameLayout {','final class FloodSafeNativeMapView extends FrameLayout {\n    // V0902_STATUS_FLOW_DISTRICT',1)
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.9.02 map patch PASS: green current dots, status-matched river overlays, coloured flow/glow, district focus, scrollable river dialog')
