from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.70 is deliberately narrow:
# BIPAD's official river-station coordinates live in fields.point as GeoJSON
# {"type":"Point","coordinates":[lon,lat]}. Older parsing expected flat lat/lon,
# so valid catalog gauges (including Bishnumati) could disappear completely.
# Do not touch rain marker policy, notification cadence/radius, news, river geometry,
# source timestamps/values, or the v0.8.69 interaction logic.

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

# Robust official coordinate reader. Flat coordinates remain supported for proxy rows,
# but the canonical BIPAD fields.point GeoJSON is authoritative for catalog/latest rows.
coord=r'''    private static double[] v870OfficialCoord(JSONObject r){
        double la=Double.NaN,lo=Double.NaN;if(r==null)return new double[]{la,lo};
        JSONObject f=r.optJSONObject("fields");
        la=numDeep(r,f,"latitude","lat","stationLatitude","station_latitude","stationLat");
        lo=numDeep(r,f,"longitude","lon","lng","stationLongitude","station_longitude","stationLon");
        if(Double.isFinite(la)&&Double.isFinite(lo))return new double[]{la,lo};
        Object p=r.opt("point");if((p==null||p==JSONObject.NULL)&&f!=null)p=f.opt("point");
        try{
            JSONObject po=null;JSONArray ca=null;
            if(p instanceof JSONObject)po=(JSONObject)p;
            else if(p instanceof JSONArray)ca=(JSONArray)p;
            else if(p instanceof String){
                String s=((String)p).trim();
                if(s.startsWith("{"))po=new JSONObject(s);
                else if(s.startsWith("["))ca=new JSONArray(s);
                else{
                    java.util.regex.Matcher m=java.util.regex.Pattern.compile("(?i)POINT\\s*\\(\\s*([-+0-9.]+)\\s+([-+0-9.]+)\\s*\\)").matcher(s);
                    if(m.find()){lo=Double.parseDouble(m.group(1));la=Double.parseDouble(m.group(2));}
                }
            }
            if(po!=null){
                ca=po.optJSONArray("coordinates");
                if(ca==null){la=po.optDouble("lat",po.optDouble("latitude",Double.NaN));lo=po.optDouble("lon",po.optDouble("lng",po.optDouble("longitude",Double.NaN)));}
            }
            if(ca!=null&&ca.length()>=2){lo=ca.optDouble(0,Double.NaN);la=ca.optDouble(1,Double.NaN);}
        }catch(Exception ignored){}
        return new double[]{la,lo};
    } // V0870_BIPAD_POINT_COORDS
'''

parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=v870OfficialCoord(r);double la=c[0],lo=c[1];
        if(!Double.isFinite(la)||!Double.isFinite(lo)||!isNepal(la,lo))return null;
        double level=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level"),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold"),
               elevation=numDeep(r,f,"elevation","stationElevation","station_elevation","altitude");
        long at=trustedRowTime(r);
        boolean online=r.optBoolean("_floodsafeOnline",!r.optBoolean("_floodsafeCatalogOnly",false));
        boolean hasObservation=Double.isFinite(level)&&at>0L;
        boolean fresh=online&&hasObservation; // V0870_SOURCE_CURRENT_NO_AGE_GATE
        boolean datum=Double.isFinite(elevation)&&elevation>50&&Double.isFinite(level)&&Math.abs(level-elevation)<20&&
                ((Double.isFinite(warning)&&Math.abs(warning-elevation)<25)||(Double.isFinite(danger)&&Math.abs(danger-elevation)<25));
        if(datum){level-=elevation;if(Double.isFinite(warning))warning-=elevation;if(Double.isFinite(danger))danger-=elevation;}
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(hasObservation){
            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")||(Double.isFinite(danger)&&danger>0&&level>=danger)){stage="danger";rank=0;}
            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")||(Double.isFinite(warning)&&warning>0&&level>=warning)){stage="warning";rank=1;}
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else{stage="normal";rank=3;}
        }
        if(!online)rank=4;
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official river station";
        String district=v848DistrictName(la,lo,strDeep(r,f,"districtName","district_name","district"));
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);
    } // V0870_ALL_OFFICIAL_POINT_GAUGES
'''

sp=method_span(a,'parseStation')
if not sp:raise SystemExit('v0870 parseStation missing')
# Keep the new coordinate helper immediately before the parser, replacing only parser behavior.
a=a[:sp[0]]+coord+parse+a[sp[1]:]

# v0.8.69 already owns map/rain/notifications. Assert those contracts still exist.
for marker in ['V0869_NO_RAIN_ONLY_MAP_STATIONS','V0869_FULL_GAUGE_INVENTORY','V0869_ALL_77_DISTRICTS','V0869_GAUGE_WATER_AND_RAIN_DETAIL','V0869_IMMEDIATE_ALERT_CHECKS','V0869_START_MONITOR_SERVICE','V0869_TWO_HOUR_DIGEST']:
    if marker not in a and marker!='V0869_TWO_HOUR_DIGEST':raise SystemExit('v0870 prior activity contract missing: '+marker)
if 'main.postDelayed(this,10_000L);' not in a:raise SystemExit('v0870 10-second source poll changed')
if 'RIVER_FRESH_MS=Long.MAX_VALUE' not in a:raise SystemExit('v0870 no-age-gate source parity changed')

if 'versionCode 89' in g:g=g.replace('versionCode 89','versionCode 90',1)
elif 'versionCode 90' not in g:raise SystemExit('v0870 versionCode anchor missing')
if "versionName '0.8.69'" in g:g=g.replace("versionName '0.8.69'","versionName '0.8.70'",1)
elif "versionName '0.8.70'" not in g:raise SystemExit('v0870 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for x in ['V0870_BIPAD_POINT_COORDS','V0870_ALL_OFFICIAL_POINT_GAUGES','V0870_SOURCE_CURRENT_NO_AGE_GATE']:
    if x not in a:raise SystemExit('v0870 marker missing: '+x)
for x in ['versionCode 90',"versionName '0.8.70'"]:
    if x not in g:raise SystemExit('v0870 version marker missing: '+x)
print('FloodSafe v0.8.70 PASS: BIPAD fields.point GeoJSON coordinates restore the full official gauge inventory; v0.8.69 behavior untouched')
