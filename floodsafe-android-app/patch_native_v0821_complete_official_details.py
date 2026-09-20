from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
b_path=src/'FloodLiveGaugeMonitor.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
b=b_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def between(text,start,end,repl,label):
    i=text.find(start); j=text.find(end,i if i>=0 else 0)
    if i<0 or j<0: raise SystemExit(label+' anchors missing')
    return text[:i]+repl+text[j:]

# -----------------------------------------------------------------------------
# v0.8.21: preserve v0.8.20 Nepal-only clean map, but make the data behind a river
# tap complete and source-faithful. Quiet/stale official stations remain discoverable
# in details; ONLY current observations may colour river lines or trigger alerts.
# -----------------------------------------------------------------------------

# River catalogue + latest observation feed. Keep last official value/time on stale
# rows instead of erasing them. Current line/status semantics remain <=30 minutes.
parse_station=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[]c=officialCoord(r);double a=c[0],o=c[1];if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value"),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger"),
               discharge=numDeep(r,f,"_lastDischarge","discharge","currentDischarge","current_discharge","streamflow","flow","flowRate","flow_rate");
        long at=trustedRowTime(r);
        boolean current=Double.isFinite(level)&&at>0&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L;
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(current){
            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else if(raw.contains("BELOW WARNING")||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("GREEN")){stage="normal";rank=3;}
            else{stage="unknown";rank=4;}
        }
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");
        JSONObject station=r.optJSONObject("station");if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName");
        if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district"),
               stationId=strDeep(r,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),
               basin=strDeep(r,f,"basin","basin_name","basinName","riverBasin","river_basin");
        return new RiverStation(name,district,a,o,level,warning,danger,discharge,at,current,stage,rank,raw,stationId,basin);
    }

'''
a=between(a,'    private RiverStation parseStation(','    private void refreshRainStations(){',parse_station,'parseStation v0821')

# Rain: merge the full official catalogue with latest=true so Himalayan/quiet AWS
# stations stay available for nearest-station detail even between observations.
refresh_rain=r'''    private void refreshRainStations(){
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();
                JSONArray catalog=new JSONArray(),latest=new JSONArray();
                try{catalog=trustedPages(BIPAD+"rain-stations/?limit=2000",now);}catch(Exception ignored){}
                try{latest=trustedPages(BIPAD+"rain-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}
                JSONArray rr=mergeTrustedRiverRows(catalog,latest);
                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain-trimed/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}
                if(rr.length()==0){try{rr=rows(getJson(BIPAD+"rain/?limit=1000&_nativefull="+now));}catch(Exception ignored){}}
                List<RainStation> out=new ArrayList<>();
                for(int i=0;i<rr.length();i++){RainStation s=parseRainStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
                synchronized(rainStations){rainStations.clear();rainStations.addAll(out);} runOnUiThread(this::refreshRainUi);
            }catch(Exception ignored){runOnUiThread(this::refreshRainUi);}
        });
    }

'''
a=between(a,'    private void refreshRainStations(){','    private static double rainAverage(JSONObject r,int interval)',refresh_rain,'refreshRainStations v0821')

parse_rain=r'''    private RainStation parseRainStation(JSONObject r,long now){
        if(r==null)return null; JSONObject f=r.optJSONObject("fields"); double[] c=officialCoord(r); double a=c[0],o=c[1];
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double mm1=rainAverage(r,1),mm3=rainAverage(r,3),mm6=rainAverage(r,6),mm12=rainAverage(r,12),mm24=rainAverage(r,24);
        double mm=Double.isFinite(mm1)?mm1:numDeep(r,f,"_lastRainfall","lastRainfall","rainfall","rainFall","rain","rainfall24h","rainfall_24h","currentRainfall","lastValue","_lastValue","value");
        long at=parseTime(strDeep(r,f,"_measurementTime","_lastRainfallOn","rainfallOn","rainfall_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","date_time","timestamp","updatedOn","updated_at","time"));
        boolean fresh=at>0&&now-at<=90L*60L*1000L&&at-now<=5L*60_000L;
        String name=strDeep(r,f,"_stationName","stationName","station_name","title","name","locationName","location_name");
        JSONObject station=r.optJSONObject("station");if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName");if(name.isEmpty())name="Official rain/AWS station";
        String raw=strDeep(r,f,"status","status_name","_officialStatus","alertStatus","alert_status").toUpperCase(Locale.ROOT),band="stale";
        if(fresh){if(raw.contains("DANGER")||raw.contains("RED"))band="danger";else if(raw.contains("WARNING")||raw.contains("ORANGE"))band="warning";else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW"))band="alert";else band="normal";}
        String basin=strDeep(r,f,"basin","basin_name","riverBasin","river_basin"),
               stationId=strDeep(r,f,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"),
               district=strDeep(r,f,"districtName","district_name","district");
        return new RainStation(name,basin,district,stationId,a,o,mm,mm3,mm6,mm12,mm24,at,fresh,band,raw);
    }

'''
a=between(a,'    private RainStation parseRainStation(JSONObject r,long now){','    private void updateMapHintCounts()',parse_rain,'parseRainStation v0821')

# Stale readings must look stale everywhere in text even when source raw status says
# WARNING/DANGER from an older observation.
status_pat=r'''    private String sourceStatusLabel\(RiverStation s\)\{.*?\n    \}\n'''
status_new=r'''    private String sourceStatusLabel(RiverStation s){
        if(s==null)return "UNKNOWN";
        String raw=s.rawStatus==null?"":s.rawStatus.trim();
        if(!s.fresh)return raw.isEmpty()||"NO_CURRENT_OFFICIAL_READING".equals(raw)?"LATEST OFFICIAL • STALE":"LATEST OFFICIAL • STALE • "+raw;
        if(!raw.isEmpty()&&!"NO_CURRENT_OFFICIAL_READING".equals(raw))return raw;
        return "UNKNOWN";
    }
'''
a,n=re.subn(status_pat,status_new,a,count=1,flags=re.S)
if n!=1: raise SystemExit('sourceStatusLabel replacement failed')

# Models carry exact official metadata into the map detail dialog.
river_cls_pat=r'''    private static final class RiverStation\{.*?\}\n'''
river_cls=r'''    private static final class RiverStation{final String name,district,stage,rawStatus,stationId,basin;final double lat,lon,level,warning,danger,discharge;final long at;final boolean fresh;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,double q,long tm,boolean f,String s,int r,String rs,String id,String b){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;discharge=q;at=tm;fresh=f;stage=s;rank=r;rawStatus=rs;stationId=id;basin=b;}}
'''
a,n=re.subn(river_cls_pat,river_cls,a,count=1,flags=re.S)
if n!=1: raise SystemExit('RiverStation class replacement failed')
rain_cls_pat=r'''    private static final class RainStation\{.*?\}\n'''
rain_cls=r'''    private static final class RainStation{final String name,basin,district,stationId,band,rawStatus;final double lat,lon,rainfall,rain3,rain6,rain12,rain24;final long at;final boolean fresh;RainStation(String n,String b,String di,String id,double a,double o,double mm,double m3,double m6,double m12,double m24,long tm,boolean f,String bd,String rs){name=n;basin=b;district=di;stationId=id;lat=a;lon=o;rainfall=mm;rain3=m3;rain6=m6;rain12=m12;rain24=m24;at=tm;fresh=f;band=bd;rawStatus=rs;}}
'''
a,n=re.subn(rain_cls_pat,rain_cls,a,count=1,flags=re.S)
if n!=1: raise SystemExit('RainStation class replacement failed')

# Keep v0.8.20 clean map text but explain the hidden nearest rain/AWS river detail.
a=a.replace('rain stations are off-map','rain stations are off-map • river tap shows nearest official rain/AWS',1)
a=a.replace('rain station mapमा छैन','rain station mapमा छैन • नदी थिच्दा नजिकको official rain/AWS detail',1)

# -----------------------------------------------------------------------------
# Native map: no rain dots are re-enabled. River detail includes same-river gauge
# and nearest official rainfall/AWS from the already-fetched hidden rain catalogue.
# -----------------------------------------------------------------------------
show=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot direct=sameRiverGaugeFor(r,la,lo,true);
        StationDot sameAny=direct!=null?direct:sameRiverGaugeFor(r,la,lo,false);
        StringBuilder msg=new StringBuilder();
        StationDot g=direct!=null?direct:sameAny;
        if(g!=null){
            double d=km(la,lo,g.lat,g.lon);
            msg.append(direct!=null?"CURRENT same-river official gauge: ":"LATEST same-river official gauge • STALE: ").append(g.name).append(String.format(Locale.US," • %.1f km",d));
            if(g.stationId!=null&&!g.stationId.isEmpty())msg.append("\nStation ID: ").append(g.stationId);
            if(g.district!=null&&!g.district.isEmpty())msg.append("\nDistrict: ").append(g.district);
            if(g.basin!=null&&!g.basin.isEmpty())msg.append("\nBasin: ").append(g.basin);
            if(Double.isFinite(g.level))msg.append(String.format(Locale.US,"\nWater level: %.3f m",g.level));
            if(Double.isFinite(g.discharge))msg.append(String.format(Locale.US,"\nDischarge / streamflow: %.3f m³/s",g.discharge));
            if(Double.isFinite(g.warning))msg.append(String.format(Locale.US,"\nWarning level: %.3f m",g.warning));
            if(Double.isFinite(g.danger))msg.append(String.format(Locale.US,"\nDanger level: %.3f m",g.danger));
            msg.append("\nOfficial status: ").append(direct?(g.rawStatus==null||g.rawStatus.isEmpty()?g.stage.toUpperCase(Locale.ROOT):g.rawStatus):"STALE / NOT USED FOR LIVE COLOUR OR ALERT");
            msg.append("\nOfficial time: ").append(formatOfficialTime(g.at));
        }else{
            msg.append("यो नदी/खोलामा matching official gauge भेटिएन। अर्को नदीको gauge जोडिएको छैन र fake status बनाइएको छैन।");
        }
        RainDot rain=nearestRain(la,lo);
        if(rain!=null){
            double rd=km(la,lo,rain.lat,rain.lon);
            msg.append("\n\n🌧️ Nearest official rainfall/AWS: ").append(rain.name).append(String.format(Locale.US," • %.1f km",rd));
            if(rain.stationId!=null&&!rain.stationId.isEmpty())msg.append("\nRain station ID: ").append(rain.stationId);
            if(rain.district!=null&&!rain.district.isEmpty())msg.append("\nDistrict: ").append(rain.district);
            if(rain.basin!=null&&!rain.basin.isEmpty())msg.append("\nBasin: ").append(rain.basin);
            if(Double.isFinite(rain.rainfall))msg.append(String.format(Locale.US,"\nRain 1h: %.1f mm",rain.rainfall));
            if(Double.isFinite(rain.rain3))msg.append(String.format(Locale.US,"\nRain 3h: %.1f mm",rain.rain3));
            if(Double.isFinite(rain.rain6))msg.append(String.format(Locale.US,"\nRain 6h: %.1f mm",rain.rain6));
            if(Double.isFinite(rain.rain12))msg.append(String.format(Locale.US,"\nRain 12h: %.1f mm",rain.rain12));
            if(Double.isFinite(rain.rain24))msg.append(String.format(Locale.US,"\nRain 24h: %.1f mm",rain.rain24));
            msg.append("\nRain reading: ").append(rain.fresh?"CURRENT/LATEST":"LATEST OFFICIAL • STALE");
            msg.append("\nRain official time: ").append(formatOfficialTime(rain.at));
            if(rain.rawStatus!=null&&!rain.rawStatus.isEmpty())msg.append("\nRain source status: ").append(rain.rawStatus);
        }
        msg.append("\n\nSource: BIPAD/DHM official • River geometry: OpenStreetMap / FloodSafe bundled network");
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
m=between(m,'    private void showRiver(RiverWay r, double la, double lo) {','    private StationDot sameRiverGaugeFor(',show,'showRiver v0821')

# Enrich reflection copies.
read_station_anchor='s.warning = getDouble(c,o,"warning"); s.danger=getDouble(c,o,"danger"); s.at=getLong(c,o,"at",-1L);'
if read_station_anchor not in m: raise SystemExit('readStation field anchor missing')
m=m.replace(read_station_anchor,read_station_anchor+' s.stationId=getString(c,o,"stationId",""); s.basin=getString(c,o,"basin",""); s.district=getString(c,o,"district",""); s.discharge=getDouble(c,o,"discharge");',1)
read_rain_anchor='r.rainfall=getDouble(c,o,"rainfall");r.rain3=getDouble(c,o,"rain3");r.rain6=getDouble(c,o,"rain6");r.rain12=getDouble(c,o,"rain12");r.rain24=getDouble(c,o,"rain24");r.at=getLong(c,o,"at",-1L);return r;'
if read_rain_anchor not in m: raise SystemExit('readRain field anchor missing')
m=m.replace(read_rain_anchor,'r.rainfall=getDouble(c,o,"rainfall");r.rain3=getDouble(c,o,"rain3");r.rain6=getDouble(c,o,"rain6");r.rain12=getDouble(c,o,"rain12");r.rain24=getDouble(c,o,"rain24");r.at=getLong(c,o,"at",-1L);r.stationId=getString(c,o,"stationId","");r.district=getString(c,o,"district","");return r;',1)

# Add metadata fields without changing v0.8.20 map performance/state machinery.
m=m.replace('String name, stage, rawStatus;', 'String name, stage, rawStatus, stationId, basin, district;',1)
m=m.replace('double lat, lon, level, warning, danger;', 'double lat, lon, level, warning, danger, discharge;',1)
m=m.replace('String name,basin,band,rawStatus;', 'String name,basin,district,stationId,band,rawStatus;',1)
if 'stationId, basin, district' not in m or 'district,stationId,band' not in m: raise SystemExit('native metadata fields not applied')

# -----------------------------------------------------------------------------
# Notification repair only: warning/danger notification must be backed by a recent
# official observation. Radius/repeat/sound behavior stays untouched.
# -----------------------------------------------------------------------------
if 'ALERT_FRESH_MS=10L*60L*1000L' not in b:
    b=b.replace('private static final double MATERIAL_RISE_METRES=0.20d;','private static final double MATERIAL_RISE_METRES=0.20d;\n    private static final long ALERT_FRESH_MS=10L*60L*1000L;',1)
level_anchor='            double level=num(row,f,"_lastWaterLevel"'
if level_anchor not in b: raise SystemExit('alert level anchor missing')
if 'now-observedAt>ALERT_FRESH_MS' not in b:
    guard='            long observedAt=parseOfficialTime(str(row,f,"waterLevelOn","water_level_on","riverLevelOn","river_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","timestamp","time"));if(observedAt<=0L||now-observedAt>ALERT_FRESH_MS||observedAt-now>5L*60L*1000L)continue;\n'
    b=b.replace(level_anchor,guard+level_anchor,1)
if 'private static long parseOfficialTime(' not in b:
    method='''    private static long parseOfficialTime(String s){if(s==null||s.trim().isEmpty())return-1L;String x=s.trim();try{return java.time.Instant.parse(x).toEpochMilli();}catch(Exception ignored){}try{return java.time.OffsetDateTime.parse(x).toInstant().toEpochMilli();}catch(Exception ignored){}try{return java.time.LocalDateTime.parse(x.replace(" ","T")).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}return-1L;}\n'''
    b=b.replace('    private static JSONArray array(JSONObject root,String... keys){',method+'    private static JSONArray array(JSONObject root,String... keys){',1)

# Version 0.8.21 / Play release candidate.
if "versionName '0.8.21'" not in g:
    g=g.replace('versionCode 40','versionCode 41',1)
    g=g.replace("versionName '0.8.20'","versionName '0.8.21'",1)
if 'versionCode 41' not in g or "versionName '0.8.21'" not in g: raise SystemExit('v0.8.21 version bump failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');b_path.write_text(b,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard gates: user request + v0.8.20 clean-map constraints.
a2=a_path.read_text(encoding='utf-8');m2=m_path.read_text(encoding='utf-8');b2=b_path.read_text(encoding='utf-8')
for x in ['rain-stations/?limit=2000','rain-stations/?latest=true&limit=2000','LATEST OFFICIAL • STALE','stationId,basin','discharge']:
    if x not in a2: raise SystemExit('activity gate missing: '+x)
for x in ['Nearest official rainfall/AWS','CURRENT same-river official gauge','STALE / NOT USED FOR LIVE COLOUR OR ALERT','Discharge / streamflow','fs-nepal-outside-mask-layer']:
    if x not in m2: raise SystemExit('map gate missing: '+x)
if 'boolean rainShown=' in m2 or 'showRainMarkers=zoom>=8.0' in m2: raise SystemExit('v0.8.20 hidden rain-marker contract regressed')
for x in ['ALERT_FRESH_MS=10L*60L*1000L','now-observedAt>ALERT_FRESH_MS','RADIUS_KM=2d','handler.postDelayed(this,1_000L)']:
    if x not in b2: raise SystemExit('alert safety gate missing: '+x)
print('FloodSafe v0.8.21 complete official river + hidden rain/AWS detail + safe alerts PASS')
