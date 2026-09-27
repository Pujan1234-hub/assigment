from pathlib import Path
import re

P=Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodLiveGaugeMonitor.java')
s=P.read_text(encoding='utf-8')

for old,new in [
    ('import java.io.InputStreamReader;\n','import java.io.InputStream;\nimport java.io.InputStreamReader;\n'),
    ('import java.util.Locale;\n','import java.util.Locale;\nimport java.util.List;\n'),
    ('import java.util.concurrent.ExecutorService;\n','import java.time.Instant;\nimport java.time.LocalDateTime;\nimport java.time.OffsetDateTime;\nimport java.time.ZoneId;\nimport java.time.ZonedDateTime;\nimport java.time.format.DateTimeFormatter;\nimport java.util.concurrent.ExecutorService;\n')]:
    if new.split('\n')[0] not in s and old in s:s=s.replace(old,new,1)

anchor='    private volatile int lastRiverHash=0,lastRainHash=0,lastHydroHash=0;'
if anchor not in s: raise SystemExit('field anchor missing')
s=s.replace(anchor,anchor+'\n    private volatile List<RiverShape> alertRiverShapes; // V0911_FAST_ALERT_RIVER_GEOMETRY_CACHE',1)

pattern=r'    private void checkNearbyHazards\(JSONObject root\)\{.*?\n    \} // V0872_BACKGROUND_2KM_SOURCE_ALERTS\n\n    private boolean claim'
replacement=r'''    private void checkNearbyHazards(JSONObject root){
        if(root==null)return;
        SharedPreferences monitor=app.getSharedPreferences(RainAlertWorker.PREFS,Context.MODE_PRIVATE);
        if(!monitor.getBoolean("enabled",false)||!monitor.getBoolean("follow_device",false))return;
        if(Build.VERSION.SDK_INT>=33&&app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
        double homeLat=Double.longBitsToDouble(monitor.getLong("lat",Double.doubleToRawLongBits(Double.NaN)));
        double homeLon=Double.longBitsToDouble(monitor.getLong("lon",Double.doubleToRawLongBits(Double.NaN)));
        if(!insideNepal(homeLat,homeLon))return;
        JSONArray rows=array(root,"results","current","stations","data");if(rows==null)return;
        List<RiverShape> shapes=riverShapesForAlerts();if(shapes.isEmpty())return;
        long now=System.currentTimeMillis();int shown=0;
        for(int i=0;i<rows.length()&&shown<3;i++){
            JSONObject row=rows.optJSONObject(i);if(row==null)continue;JSONObject f=row.optJSONObject("fields");
            double[] p=coord(row,f);double la=p[0],lo=p[1];if(!insideNepal(la,lo))continue;
            double level=num(row,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");
            double warning=num(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold");
            double danger=num(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold");
            String raw=str(row,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
            String stage=stage(level,warning,danger,raw);if(!"warning".equals(stage)&&!"danger".equals(stage))continue;
            String measured=str(row,f,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime");
            long measuredAt=parseAlertTime(measured);if(measuredAt<=0L||now-measuredAt>10L*60L*1000L||measuredAt-now>5L*60L*1000L)continue;
            String id=str(row,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id");
            String stationName=str(row,f,"station_name","stationName","title","name");
            String riverName=str(row,f,"river_name","riverName","river");
            if(stationName.isEmpty())stationName=riverName.isEmpty()?"Official hydrology station":riverName;
            if(riverName.isEmpty())riverName=riverFromStationTitle(stationName);
            if(id.isEmpty())id=stationName+"@"+String.format(Locale.US,"%.5f,%.5f",la,lo);
            RiverShape affected=bestMatchedRiver(shapes,riverName,stationName,la,lo);if(affected==null)continue;
            double distance=distanceToRiverKm(homeLat,homeLon,affected);if(!Double.isFinite(distance)||distance>RADIUS_KM)continue;
            if(!claim(id,stage,level,now))continue;
            String display=affected.name==null||affected.name.isEmpty()?stationName:affected.name+" • "+stationName;
            notifyHazard(id,display,stage,distance,level);shown++;
        }
    } // V0911_FAST_ALERT_ACTUAL_RIVER_GEOMETRY V0911_FAST_ALERT_FRESH_ONLY

    private static final class RiverShape{String name,key;final List<double[]> points=new ArrayList<>();}
    private List<RiverShape> riverShapesForAlerts(){
        List<RiverShape> cached=alertRiverShapes;if(cached!=null)return cached;
        synchronized(this){cached=alertRiverShapes;if(cached!=null)return cached;List<RiverShape> out=new ArrayList<>();
            try{String raw;try{raw=readAlertAsset("data/nepal-waterways-tiles/overview.json");}catch(Exception e){raw=readAlertAsset("data/nepal-waterways-snapshot.json");}JSONObject root=new JSONObject(raw);JSONArray ways=root.optJSONArray("waterways");if(ways!=null)for(int i=0;i<ways.length();i++){JSONObject w=ways.optJSONObject(i);if(w==null)continue;JSONArray pts=w.optJSONArray("pts");if(pts==null||pts.length()<2)continue;String name=w.optString("name_en","");if(name.isEmpty())name=w.optString("name","");if(name.isEmpty())name=w.optString("name_ne","");String key=canonicalRiverName(name);if(key.isEmpty())continue;RiverShape shape=new RiverShape();shape.name=name;shape.key=key;for(int j=0;j<pts.length();j++){JSONArray a=pts.optJSONArray(j);if(a==null||a.length()<2)continue;double lo=a.optDouble(0,Double.NaN),la=a.optDouble(1,Double.NaN);if(Double.isFinite(la)&&Double.isFinite(lo)&&la>=25.4&&la<=31.15&&lo>=79.2&&lo<=89.15)shape.points.add(new double[]{lo,la});}if(shape.points.size()>=2)out.add(shape);}}
            catch(Exception ignored){}
            alertRiverShapes=out;return out;}
    }
    private String readAlertAsset(String path)throws Exception{try(InputStream in=app.getAssets().open(path);BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){StringBuilder b=new StringBuilder();String line;while((line=r.readLine())!=null)b.append(line);return b.toString();}}
    private static RiverShape bestMatchedRiver(List<RiverShape> shapes,String riverName,String stationName,double la,double lo){String wanted=canonicalRiverName(riverName);if(wanted.isEmpty())wanted=canonicalRiverName(riverFromStationTitle(stationName));if(wanted.isEmpty())return null;RiverShape best=null;double bd=Double.POSITIVE_INFINITY;for(RiverShape r:shapes){if(!sameRiverKey(wanted,r.key))continue;double d=distanceToRiverKm(la,lo,r);if(Double.isFinite(d)&&d<=8d&&d<bd){bd=d;best=r;}}return best;}
    private static boolean sameRiverKey(String a,String b){if(a==null||b==null||a.isEmpty()||b.isEmpty())return false;if(a.equals(b))return true;int min=Math.min(a.length(),b.length());return min>=5&&(a.contains(b)||b.contains(a));}
    private static String riverFromStationTitle(String v){if(v==null)return"";String z=v.trim();int at=z.toLowerCase(Locale.ROOT).indexOf(" at ");return at>0?z.substring(0,at):z;}
    private static String canonicalRiverName(String v){String z=riverFromStationTitle(v).toLowerCase(Locale.ROOT);z=z.replace("river","").replace("khola","").replace("nadi","").replace("nadhi","").replace("stream","").replace("नदी","").replace("खोला","");return z.replaceAll("[^a-z0-9\\p{L}]","");}
    private static double distanceToRiverKm(double lat,double lon,RiverShape r){if(r==null||r.points.size()<2)return Double.NaN;double best=Double.POSITIVE_INFINITY;for(int i=0;i<r.points.size()-1;i++){double[] a=r.points.get(i),b=r.points.get(i+1);best=Math.min(best,pointSegmentKm(lat,lon,a[1],a[0],b[1],b[0]));}return best;}
    private static double pointSegmentKm(double lat,double lon,double lat1,double lon1,double lat2,double lon2){double cos=Math.cos(Math.toRadians(lat));double x1=(lon1-lon)*111.320d*cos,y1=(lat1-lat)*110.574d,x2=(lon2-lon)*111.320d*cos,y2=(lat2-lat)*110.574d,dx=x2-x1,dy=y2-y1,len2=dx*dx+dy*dy,t=len2<=1e-12d?0d:-(x1*dx+y1*dy)/len2;t=Math.max(0d,Math.min(1d,t));double x=x1+t*dx,y=y1+t*dy;return Math.sqrt(x*x+y*y);}
    private static long parseAlertTime(String value){if(value==null||value.trim().isEmpty())return-1L;String z=value.trim();try{long n=Long.parseLong(z);return n<10_000_000_000L?n*1000L:n;}catch(Exception ignored){}try{return Instant.parse(z).toEpochMilli();}catch(Exception ignored){}try{return OffsetDateTime.parse(z).toInstant().toEpochMilli();}catch(Exception ignored){}try{return ZonedDateTime.parse(z).toInstant().toEpochMilli();}catch(Exception ignored){}try{return LocalDateTime.parse(z.replace(' ','T'),DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){return-1L;}}

    private boolean claim'''

s2,n=re.subn(pattern,lambda m:replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'fast alert method anchor expected once, got {n}')
s=s2
for marker in ['V0911_FAST_ALERT_ACTUAL_RIVER_GEOMETRY','V0911_FAST_ALERT_FRESH_ONLY','V0911_FAST_ALERT_RIVER_GEOMETRY_CACHE']:
    if marker not in s: raise SystemExit('missing '+marker)
if 'double distance=haversineKm(homeLat,homeLon,la,lo)' in s: raise SystemExit('old station-dot distance still present in fast alert path')
P.write_text(s,encoding='utf-8')
print('V0911_FAST_ALERT_GEOMETRY_OK')
