from pathlib import Path
import re

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path = src / 'NativeFullActivity.java'
map_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'
activity = activity_path.read_text(encoding='utf-8')
helper = map_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

activity = activity.replace('JSONObject official=getJson(BIPAD+"river/?limit=1000&_nativefull="+now);','JSONObject official=getJson(BIPAD+"river-trimed/?limit=1000&_nativefull="+now);',1)
activity = activity.replace(
    'if(out.isEmpty()){\n                    JSONObject root=getJson(RIVER_ENDPOINT+"?_nativefull="+now); JSONArray rr=rows(root);',
    'if(out.isEmpty()){\n                    try{JSONObject raw=getJson(BIPAD+"river/?limit=1000&_nativefull="+now);JSONArray rawRows=rows(raw);for(int i=0;i<rawRows.length();i++){RiverStation s=parseStation(rawRows.optJSONObject(i),now);if(s!=null)out.add(s);}}catch(Exception ignored){}\n                }\n                if(out.isEmpty()){\n                    JSONObject root=getJson(RIVER_ENDPOINT+"?_nativefull="+now); JSONArray rr=rows(root);',1)
old_rain='try{rr=rows(getJson(BIPAD+"rain/?limit=1000&_nativefull="+now));}catch(Exception ignored){}\n                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain-trimed/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}'
new_rain='try{rr=rows(getJson(BIPAD+"rain-trimed/?limit=1000&_nativefull="+now));}catch(Exception ignored){}\n                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}'
if old_rain not in activity: raise SystemExit('v0.8.9 rain feed anchor missing')
activity=activity.replace(old_rain,new_rain,1)
activity=activity.replace('"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime","time"','"waterLevelOn","water_level_on","riverLevelOn","river_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","date_time","timestamp","_measurementTime","time"',1)
activity=activity.replace('"measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","createdOn","updatedOn","time"','"rainfallOn","rainfall_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","date_time","timestamp","createdOn","updatedOn","date","time"',1)
old_return='return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank);'
if old_return not in activity: raise SystemExit('RiverStation constructor call anchor missing')
activity=activity.replace(old_return,'return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank,raw);',1)
old_cls='private static final class RiverStation{final String name,district,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;}}'
new_cls='private static final class RiverStation{final String name,district,stage,rawStatus;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r,String rs){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;rawStatus=rs;}}'
if old_cls not in activity: raise SystemExit('RiverStation class anchor missing')
activity=activity.replace(old_cls,new_cls,1)

helper=helper.replace('lineColor("#22e7ff"), lineWidth(2.45f), lineOpacity(1.0f)','lineColor("#7f939c"), lineWidth(2.45f), lineOpacity(0.92f)',1)
flow_pat=r'ensurePointSource\("fs-flow-particles",\s*"fs-flow-particles-layer",\s*"#[0-9A-Fa-f]{6}",\s*[0-9.]+f,\s*[0-9.]+f\);'
helper,n=re.subn(flow_pat,'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#f4feff", 4.0f, 1.0f);',helper,count=1)
if n!=1: raise SystemExit('flow particle pattern missing')
helper=helper.replace('float glow=(float)(0.42+0.42*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(0.75f+0.45f*glow));','float glow=(float)(0.48+0.50*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(1.05f+0.80f*glow));',1)

status_install='''            ensureRiverStatusLayer("fs-river-normal-status","fs-river-normal-status-layer","#2d8cff");
            ensureRiverStatusLayer("fs-river-alert-status","fs-river-alert-status-layer","#ffc928");
            ensureRiverStatusLayer("fs-river-warning-status","fs-river-warning-status-layer","#ff8a1f");
            ensureRiverStatusLayer("fs-river-danger-status","fs-river-danger-status-layer","#f22f4b");
            refreshRiverStatusSources();
'''
flow_line='            ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#f4feff", 4.0f, 1.0f);'
if 'fs-river-danger-status-layer' not in helper:
    if flow_line not in helper: raise SystemExit('normalized flow particle anchor missing')
    helper=helper.replace(flow_line,status_install+flow_line,1)

method_anchor='    private void ensurePointSource(String sourceId, String layerId, String color, float radius, float opacity) {'
status_methods=r'''    private void ensureRiverStatusLayer(String sourceId,String layerId,String color) {
        if(style==null||style.getSource(sourceId)!=null)return;
        style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        style.addLayer(new LineLayer(layerId,sourceId).withProperties(lineColor(color),lineWidth(3.55f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    }

    private void refreshRiverStatusSources() {
        if(!styleReady||style==null)return;
        setGeo("fs-river-normal-status",riverStatusGeo("normal"));
        setGeo("fs-river-alert-status",riverStatusGeo("alert"));
        setGeo("fs-river-warning-status",riverStatusGeo("warning"));
        setGeo("fs-river-danger-status",riverStatusGeo("danger"));
    }

    private String riverStatusGeo(String wanted) {
        try{
            JSONArray features=new JSONArray();
            for(RiverWay r:rivers){
                if(r==null||r.points.size()<2)continue;
                StationDot g=routeGaugeFor(r);
                if(g==null||!g.fresh||!wanted.equals(normalizeStage(g.stage)))continue;
                JSONArray coords=new JSONArray();for(double[]p:r.points)coords.put(new JSONArray().put(p[0]).put(p[1]));
                JSONObject geom=new JSONObject().put("type","LineString").put("coordinates",coords);
                JSONObject props=new JSONObject().put("name",r.name).put("status",wanted).put("gauge",g.name);
                features.put(new JSONObject().put("type","Feature").put("geometry",geom).put("properties",props));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",features).toString();
        }catch(Exception e){return emptyFeatureCollection();}
    }

    private StationDot routeGaugeFor(RiverWay r){
        if(r==null||r.points.isEmpty())return null;
        double[] p=r.points.get(r.points.size()/2);
        return directGaugeFor(r,p[1],p[0]);
    }

'''
if 'private void ensureRiverStatusLayer(' not in helper:
    if method_anchor not in helper: raise SystemExit('ensurePointSource anchor missing')
    helper=helper.replace(method_anchor,status_methods+method_anchor,1)

danger_line='        setGeo("fs-danger", stationGeo(snapshot, "danger"));'
if danger_line not in helper: raise SystemExit('danger station source line missing')
helper=helper.replace(danger_line,danger_line+'\n        refreshRiverStatusSources();',1)
helper=helper.replace('setGeo("fs-river-labels", riverLabelsGeoJson);','setGeo("fs-river-labels", riverLabelsGeoJson); refreshRiverStatusSources();')
helper=helper.replace('setGeo("fs-river-labels", labels);','setGeo("fs-river-labels", labels); refreshRiverStatusSources();')

helper=helper.replace('s.stage = getString(c, o, "stage", "normal").toLowerCase(Locale.ROOT);','s.stage = getString(c, o, "stage", "normal").toLowerCase(Locale.ROOT);\n            s.rawStatus = getString(c, o, "rawStatus", s.stage);',1)
helper=helper.replace('Object original; String name, stage; double lat, lon, level; boolean fresh;','Object original; String name, stage, rawStatus; double lat, lon, level; boolean fresh;',1)
helper=helper.replace('msg.append("\\nStatus: ").append(direct.fresh?direct.stage.toUpperCase(Locale.ROOT):"STALE / UNKNOWN");','msg.append("\\nOfficial status: ").append(direct.fresh&&direct.rawStatus!=null&&!direct.rawStatus.isEmpty()?direct.rawStatus:"STALE / UNKNOWN");\n            msg.append("\\nMap colour: ").append(direct.fresh?direct.stage.toUpperCase(Locale.ROOT):"GREY / STALE");',1)

if "versionName '0.8.10'" not in gradle:
    gradle=gradle.replace('versionCode 29','versionCode 30',1)
    gradle=gradle.replace("versionName '0.8.9'","versionName '0.8.10'",1)
if 'versionCode 30' not in gradle or "versionName '0.8.10'" not in gradle: raise SystemExit('v0.8.10 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for marker in ['river-trimed/?limit=1000','rain-trimed/?limit=1000','river/?limit=1000','rain/?limit=1000','rawStatus=rs','rainfallOn','RIVER_FRESH_MS=10L*60L*1000L','RAIN_FRESH_MS=30L*60L*1000L']:
    if marker not in a: raise SystemExit('v0.8.10 activity marker missing: '+marker)
for marker in ['fs-river-normal-status-layer','fs-river-alert-status-layer','fs-river-warning-status-layer','fs-river-danger-status-layer','refreshRiverStatusSources','routeGaugeFor','lineColor("#7f939c")','"#f4feff", 4.0f, 1.0f']:
    if marker not in h: raise SystemExit('v0.8.10 map marker missing: '+marker)
print('FloodSafe v0.8.10 latest BIPAD/DHM feeds + live river colour overlays PASS')
