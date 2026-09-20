from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path=src/'NativeFullActivity.java'
map_path=src/'FloodSafeNativeMapView.java'
monitor_path=src/'FloodLiveGaugeMonitor.java'
gradle_path=root/'app/build.gradle'
activity=activity_path.read_text(encoding='utf-8')
helper=map_path.read_text(encoding='utf-8')
monitor=monitor_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

def replace_between(text,start,end,replacement,label):
    a=text.find(start); b=text.find(end,a if a>=0 else 0)
    if a<0 or b<0: raise SystemExit(label+' anchor missing')
    return text[:a]+replacement+text[b:]

# Foreground map follows official changes quickly; the existing foreground service
# still performs the one-second non-overlapping background source recheck.
activity=activity.replace('main.postDelayed(this,60_000L);','main.postDelayed(this,5_000L);',1)
activity=activity.replace('main.postDelayed(livePoll,60_000L);','main.postDelayed(livePoll,5_000L);',1)

refresh_rivers=r'''    private void refreshRivers(){
        feedFresh.setText(t("Official BIPAD/DHM stations refresh हुँदैछ…","Refreshing official BIPAD/DHM stations…"));
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();
                java.util.LinkedHashMap<String,JSONObject> merged=new java.util.LinkedHashMap<>();
                // Full public station catalog first, then the latest/trimmed/live feeds
                // overwrite matching station fields. This keeps Himalayan/quiet stations
                // visible even when they do not have a fresh observation this minute.
                mergeOfficialRows(merged,safeRows(BIPAD+"river-stations/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"station-location/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"flood-station/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"streamflow/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"river-stations/?latest=true&limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"river-trimed/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"river/?limit=2000&_nativefull="+now));
                if(merged.isEmpty()){
                    try{mergeOfficialRows(merged,rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now)));}catch(Exception ignored){}
                }
                List<RiverStation> out=new ArrayList<>();
                for(JSONObject row:merged.values()){RiverStation s=parseStation(row,now);if(s!=null)out.add(s);}
                out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
                synchronized(stations){stations.clear();stations.addAll(out);} runOnUiThread(this::refreshRiverUi);
            }catch(Exception e){runOnUiThread(()->feedFresh.setText(t("Official river refresh हुन सकेन • cached/stale लाई live भनिएको छैन","Official river refresh failed • cached/stale data is not labelled live")));}
        });
    }
'''
activity=replace_between(activity,'    private void refreshRivers(){','    private RiverStation parseStation(',refresh_rivers,'refreshRivers')

refresh_rain=r'''    private void refreshRainStations(){
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();
                java.util.LinkedHashMap<String,JSONObject> merged=new java.util.LinkedHashMap<>();
                // rain-stations contains the nationwide official station/AWS catalogue
                // (including high-altitude AWS where BIPAD exposes them). Observation
                // feeds overwrite matching catalogue rows without deleting quiet stations.
                mergeOfficialRows(merged,safeRows(BIPAD+"rain-stations/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"rain-trimed/?limit=2000&_nativefull="+now));
                mergeOfficialRows(merged,safeRows(BIPAD+"rain/?limit=2000&_nativefull="+now));
                List<RainStation> out=new ArrayList<>();
                for(JSONObject row:merged.values()){RainStation s=parseRainStation(row,now);if(s!=null)out.add(s);}
                synchronized(rainStations){rainStations.clear();rainStations.addAll(out);} runOnUiThread(this::refreshRainUi);
            }catch(Exception ignored){runOnUiThread(this::refreshRainUi);}
        });
    }

'''
activity=replace_between(activity,'    private void refreshRainStations(){','    private RainStation parseRainStation(',refresh_rain,'refreshRainStations')

# Enrich river station metadata while preserving the existing official/fresh status rules.
old='return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank,raw);'
new='double discharge=numDeep(r,f,"discharge","currentDischarge","current_discharge","streamflow","flow","flowRate","flow_rate"); String stationId=strDeep(r,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),basin=strDeep(r,f,"basin","basin_name","basinName"); return new RiverStation(name,district,a,o,level,warning,danger,at,fresh,stage,rank,raw,stationId,basin,discharge);'
if old not in activity: raise SystemExit('river constructor call missing')
activity=activity.replace(old,new,1)

old='String basin=strDeep(r,f,"basin","basin_name"); return new RainStation(name,basin,a,o,mm,at,fresh,band,raw);'
new='String basin=strDeep(r,f,"basin","basin_name"),stationId=strDeep(r,f,"stationSeriesId","station_series_id","stationId","station_id","id"),district=strDeep(r,f,"districtName","district_name","district"); return new RainStation(name,basin,a,o,mm,at,fresh,band,raw,stationId,district);'
if old not in activity: raise SystemExit('rain constructor call missing')
activity=activity.replace(old,new,1)

merge_helpers=r'''    private JSONArray safeRows(String url){try{return rows(getJson(url));}catch(Exception ignored){return new JSONArray();}}
    private static String officialStationKey(JSONObject r){
        if(r==null)return"";JSONObject f=r.optJSONObject("fields");
        String id=strDeep(r,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id");
        if(!id.isEmpty())return"id:"+id;
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name","locationName","location_name").toLowerCase(Locale.ROOT).trim();
        double[] c=officialCoord(r);return"n:"+name+"@"+(Double.isFinite(c[0])?String.format(Locale.US,"%.5f,%.5f",c[0],c[1]):"");
    }
    private static JSONObject mergeOfficialJson(JSONObject base,JSONObject newer){
        if(base==null)return newer==null?new JSONObject():new JSONObject(newer.toString());
        JSONObject out=new JSONObject(base.toString());if(newer==null)return out;
        java.util.Iterator<String> it=newer.keys();while(it.hasNext()){String k=it.next();Object v=newer.opt(k);if("fields".equals(k)&&v instanceof JSONObject&&out.optJSONObject("fields")!=null){JSONObject f=new JSONObject(out.optJSONObject("fields").toString()),nf=(JSONObject)v;java.util.Iterator<String> fi=nf.keys();while(fi.hasNext()){String fk=fi.next();Object fv=nf.opt(fk);if(fv!=null&&fv!=JSONObject.NULL&&!String.valueOf(fv).isEmpty())try{f.put(fk,fv);}catch(Exception ignored){}}try{out.put("fields",f);}catch(Exception ignored){}}else if(v!=null&&v!=JSONObject.NULL&&!String.valueOf(v).isEmpty())try{out.put(k,v);}catch(Exception ignored){}}
        return out;
    }
    private static void mergeOfficialRows(java.util.LinkedHashMap<String,JSONObject> out,JSONArray rows){
        if(rows==null)return;for(int i=0;i<rows.length();i++){JSONObject r=rows.optJSONObject(i);if(r==null)continue;String k=officialStationKey(r);if(k.isEmpty())k="row:"+i+":"+r.toString().hashCode();JSONObject old=out.get(k);out.put(k,mergeOfficialJson(old,r));}
    }

'''
anchor='    private static double[] officialCoord(JSONObject r){'
if merge_helpers.strip() not in activity:
    if anchor not in activity: raise SystemExit('officialCoord anchor missing')
    activity=activity.replace(anchor,merge_helpers+anchor,1)

# Expand model metadata used by the native detail sheet.
activity=re.sub(r'private static final class RiverStation\{[^}]*\}',
'''private static final class RiverStation{final String name,district,stage,rawStatus,stationId,basin;final double lat,lon,level,warning,danger,discharge;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,String s,int r,String rs,String id,String b,double q){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=s;rank=r;rawStatus=rs;stationId=id;basin=b;discharge=q;}}''',activity,count=1)
activity=re.sub(r'private static final class RainStation\{[^}]*\}',
'''private static final class RainStation{final String name,basin,band,rawStatus,stationId,district;final double lat,lon,rainfall;final long at;final boolean fresh;RainStation(String n,String b,double a,double o,double mm,long tm,boolean f,String bd,String rs,String id,String di){name=n;basin=b;lat=a;lon=o;rainfall=mm;at=tm;fresh=f;band=bd;rawStatus=rs;stationId=id;district=di;}}''',activity,count=1)

# Native river click: exact same-river official gauge when available + nearest official rainfall/AWS.
show=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot direct=directGaugeFor(r,la,lo); StationDot near=nearestStation(la,lo); RainDot rain=nearestRain(la,lo);
        StationDot gauge=direct!=null?direct:near; StringBuilder msg=new StringBuilder();
        if(gauge!=null){double d=km(la,lo,gauge.lat,gauge.lon);msg.append(direct!=null?"यही नदीको official gauge: ":"नजिकको official hydrology station: ").append(gauge.name).append(String.format(Locale.US," • %.1f km",d));
            if(gauge.stationId!=null&&!gauge.stationId.isEmpty())msg.append("\nStation ID: ").append(gauge.stationId);
            if(gauge.basin!=null&&!gauge.basin.isEmpty())msg.append("\nBasin: ").append(gauge.basin);
            if(gauge.district!=null&&!gauge.district.isEmpty())msg.append("\nDistrict: ").append(gauge.district);
            if(Double.isFinite(gauge.level))msg.append(String.format(Locale.US,"\nWater level: %.3f m",gauge.level));
            if(Double.isFinite(gauge.discharge))msg.append(String.format(Locale.US,"\nDischarge / streamflow: %.3f m³/s",gauge.discharge));
            if(Double.isFinite(gauge.warning))msg.append(String.format(Locale.US,"\nWarning level: %.3f m",gauge.warning));
            if(Double.isFinite(gauge.danger))msg.append(String.format(Locale.US,"\nDanger level: %.3f m",gauge.danger));
            msg.append("\nOfficial status: ").append(gauge.fresh&&gauge.rawStatus!=null&&!gauge.rawStatus.isEmpty()?gauge.rawStatus:"LATEST OFFICIAL • STALE/NO CURRENT RISK");
            msg.append("\nOfficial time: ").append(formatOfficialTime(gauge.at));
        }else msg.append("यो नदी segmentसँग matching official hydrology station भेटिएन। Fake status बनाइएको छैन।");
        if(rain!=null){double rd=km(la,lo,rain.lat,rain.lon);msg.append("\n\n🌧️ Nearest official rainfall/AWS: ").append(rain.name).append(String.format(Locale.US," • %.1f km",rd));
            if(rain.stationId!=null&&!rain.stationId.isEmpty())msg.append("\nRain station ID: ").append(rain.stationId);
            if(rain.district!=null&&!rain.district.isEmpty())msg.append("\nDistrict: ").append(rain.district);
            if(rain.basin!=null&&!rain.basin.isEmpty())msg.append("\nBasin: ").append(rain.basin);
            if(Double.isFinite(rain.rainfall))msg.append(String.format(Locale.US,"\nRainfall: %.2f mm",rain.rainfall));
            msg.append("\nRain status: ").append(rain.fresh?rain.band.toUpperCase(Locale.ROOT):"LATEST OFFICIAL • STALE");
            msg.append("\nRain official time: ").append(formatOfficialTime(rain.at));}
        msg.append("\n\nSource: BIPAD/DHM official • River geometry: OpenStreetMap / FloodSafe bundled network");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
helper=replace_between(helper,'    private void showRiver(RiverWay r, double la, double lo) {','    private void startParticles() {',show,'native showRiver')

# Read the enriched fields reflectively without changing existing tap listener contracts.
needle='s.warning = getDouble(c,o,"warning"); s.danger=getDouble(c,o,"danger"); s.at=getLong(c,o,"at",-1L);'
if needle not in helper: raise SystemExit('readStation metadata anchor missing')
helper=helper.replace(needle,needle+' s.stationId=getString(c,o,"stationId",""); s.basin=getString(c,o,"basin",""); s.district=getString(c,o,"district",""); s.discharge=getDouble(c,o,"discharge");',1)
needle='r.rainfall=getDouble(c,o,"rainfall");r.at=getLong(c,o,"at",-1L);return r;'
if needle not in helper: raise SystemExit('readRain metadata anchor missing')
helper=helper.replace(needle,'r.rainfall=getDouble(c,o,"rainfall");r.at=getLong(c,o,"at",-1L);r.stationId=getString(c,o,"stationId","");r.basin=getString(c,o,"basin","");r.district=getString(c,o,"district","");return r;',1)
helper=re.sub(r'private static final class StationDot \{[^}]*\}',
'''private static final class StationDot {Object original; String name,stage,rawStatus,stationId,basin,district; double lat,lon,level,warning,danger,discharge; long at; boolean fresh;}''',helper,count=1)
helper=re.sub(r'private static final class RainDot\{[^}]*\}',
'''private static final class RainDot{String name,band,rawStatus,stationId,basin,district;double lat,lon,rainfall;long at;boolean fresh;}''',helper,count=1)

# Notification safety repair only: old code could notify from stale warning rows.
if 'private static final long ALERT_FRESH_MS' not in monitor:
    monitor=monitor.replace('private static final double MATERIAL_RISE_METRES=0.20d;','private static final double MATERIAL_RISE_METRES=0.20d;\n    private static final long ALERT_FRESH_MS=10L*60L*1000L;',1)
alert_anchor='double level=num(row,f,"_lastWaterLevel"'
pos=monitor.find(alert_anchor)
if pos<0: raise SystemExit('background alert level anchor missing')
insert='long observedAt=parseOfficialTime(str(row,f,"waterLevelOn","water_level_on","riverLevelOn","river_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","timestamp","time"));if(observedAt<=0L||now-observedAt>ALERT_FRESH_MS||observedAt-now>5L*60L*1000L)continue;\n            '
monitor=monitor[:pos]+insert+monitor[pos:]
parse_method='''    private static long parseOfficialTime(String s){if(s==null||s.trim().isEmpty())return-1L;String x=s.trim();try{return java.time.Instant.parse(x).toEpochMilli();}catch(Exception ignored){}try{return java.time.OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}try{return java.time.LocalDateTime.parse(x.replace(" ","T")).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}return-1L;}\n'''
if 'private static long parseOfficialTime(' not in monitor:
    monitor=monitor.replace('    private static JSONArray array(JSONObject root,String... keys){',parse_method+'    private static JSONArray array(JSONObject root,String... keys){',1)

# Version bump from latest native pipeline.
if "versionName '0.8.13'" not in gradle:
    gradle=gradle.replace('versionCode 32','versionCode 33',1)
    gradle=gradle.replace("versionName '0.8.12'","versionName '0.8.13'",1)
if 'versionCode 33' not in gradle or "versionName '0.8.13'" not in gradle: raise SystemExit('v0.8.13 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
monitor_path.write_text(monitor,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

# Hard gates for the requested official-data behavior.
a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8');m=monitor_path.read_text(encoding='utf-8')
for marker in ['river-stations/?limit=2000','river-stations/?latest=true&limit=2000','rain-stations/?limit=2000','flood-station/?limit=2000','streamflow/?limit=2000','station-location/?limit=2000','main.postDelayed(this,5_000L)','mergeOfficialRows','discharge','stationId']:
    if marker not in a: raise SystemExit('v0.8.13 activity marker missing: '+marker)
for marker in ['Nearest official rainfall/AWS','Station ID','Discharge / streamflow','LATEST OFFICIAL • STALE','stationId,basin,district']:
    if marker not in h: raise SystemExit('v0.8.13 map marker missing: '+marker)
for marker in ['ALERT_FRESH_MS=10L*60L*1000L','parseOfficialTime','now-observedAt>ALERT_FRESH_MS']:
    if marker not in m: raise SystemExit('v0.8.13 alert safety marker missing: '+marker)
print('FloodSafe v0.8.13 complete official station + safe realtime native map PASS')
