from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'

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
    if not sp:raise SystemExit('missing method '+name)
    return text[:sp[0]]+block+text[sp[1]:]

# ---- DHM rainfall safe matching ----
p=src/'DhmRainMirror.java';s=p.read_text(encoding='utf-8')
if 'V0902_RAIN_MATCH_TIERS' not in s:
    s=s.replace('private static final long DISPLAY_FRESH_MS = 30L * 60L * 1000L;','private static final long DISPLAY_FRESH_MS = 90L * 60L * 1000L;',1)
    detail=r'''    static String detailFor(String stationName, String riverName, String district, String basin, double lat, double lon) {
        long now=System.currentTimeMillis();
        if (ROWS.isEmpty() || savedAt <= 0L || now - savedAt > DISPLAY_FRESH_MS) {
            android.util.Log.i("FloodSafeRain","rain_match unavailable mirror_cache_stale_or_empty");
            return null;
        }
        long officialAt=parseOfficialTime(updated);
        if(officialAt>0L && (officialAt-now>5L*60L*1000L || now-officialAt>2L*60L*60L*1000L)){
            android.util.Log.i("FloodSafeRain","rain_match unavailable official_update_stale="+updated);
            return null;
        }
        String stationKey=key(stationName),riverKey=key(riverName),districtKey=key(district),basinKey=key(basin);
        RainRow best=null;double bestScore=Double.POSITIVE_INFINITY,bestDistance=Double.POSITIVE_INFINITY;String reason="";
        for(RainRow row:ROWS.values()){
            if(!Double.isFinite(row.lat)||!Double.isFinite(row.lon))continue;
            double distance=km(lat,lon,row.lat,row.lon);if(!Double.isFinite(distance))continue;
            String rk=key(row.name),rd=key(row.district),rb=key(row.basin);
            boolean strongStation=!stationKey.isEmpty()&&!rk.isEmpty()&&Math.min(stationKey.length(),rk.length())>=5&&(stationKey.contains(rk)||rk.contains(stationKey));
            boolean strongRiver=!riverKey.isEmpty()&&!rk.isEmpty()&&Math.min(riverKey.length(),rk.length())>=5&&(riverKey.contains(rk)||rk.contains(riverKey));
            boolean sameDistrict=!districtKey.isEmpty()&&districtKey.equals(rd);
            boolean sameBasin=!basinKey.isEmpty()&&basinKey.equals(rb);
            double score=Double.POSITIVE_INFINITY;String why="";
            if((strongStation||strongRiver)&&distance<=35d){score=distance;why="same station/river area";}
            else if(sameDistrict&&sameBasin&&distance<=35d){score=50d+distance;why="same district + basin";}
            else if(sameDistrict&&distance<=20d){score=100d+distance;why="same district + nearby";}
            else if(sameBasin&&distance<=15d){score=150d+distance;why="same basin + nearby";}
            else if(distance<=10d){score=200d+distance;why="nearest safe official station";}
            if(score<bestScore){best=row;bestScore=score;bestDistance=distance;reason=why;}
        }
        if(best==null){android.util.Log.i("FloodSafeRain","rain_match unavailable no_safe_match station="+stationName+" district="+district+" basin="+basin);return null;}
        StringBuilder b=new StringBuilder();
        b.append("🌧️ DHM rainfall — official\nRainfall station: ").append(best.name);
        b.append(String.format(Locale.US,"\nDistance: %.1f km",bestDistance));
        if(!best.district.isEmpty())b.append("\nDistrict: ").append(best.district);
        if(!best.basin.isEmpty())b.append("\nBasin: ").append(best.basin);
        b.append("\nMatch: ").append(reason)
                .append("\n1 hr rainfall: ").append(mm(best.h1))
                .append("\n3 hr rainfall: ").append(mm(best.h3))
                .append("\n6 hr rainfall: ").append(mm(best.h6))
                .append("\n12 hr rainfall: ").append(mm(best.h12))
                .append("\n24 hr rainfall: ").append(mm(best.h24));
        if(!best.status.isEmpty())b.append("\nStatus: ").append(best.status);
        b.append("\nOfficial rainfall update: ").append(updated.isEmpty()?"—":updated);
        b.append("\nSource: DHM Rainfall Watch Map");
        android.util.Log.i("FloodSafeRain","rain_match ok station="+stationName+" rainfall="+best.name+" km="+String.format(Locale.US,"%.1f",bestDistance)+" reason="+reason);
        return b.toString();
    } // V0902_RAIN_MATCH_TIERS
'''
    s=replace_method(s,'detailFor',detail)
    # Compatibility overload for any untouched call sites.
    insert='''\n    static String detailFor(String stationName,String district,double lat,double lon){return detailFor(stationName,"",district,"",lat,lon);}\n    private static long parseOfficialTime(String value){\n        if(value==null||value.trim().isEmpty())return-1L;String v=value.trim();\n        try{return java.time.Instant.parse(v).toEpochMilli();}catch(Exception ignored){}\n        try{return java.time.OffsetDateTime.parse(v).toInstant().toEpochMilli();}catch(Exception ignored){}\n        try{return java.time.LocalDateTime.parse(v.replace(' ','T'),java.time.format.DateTimeFormatter.ISO_LOCAL_DATE_TIME).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){return-1L;}\n    }\n'''
    idx=s.find('    private static String read(HttpURLConnection c)')
    if idx<0:raise SystemExit('DHM insert anchor missing')
    s=s[:idx]+insert+s[idx:]
    p.write_text(s,encoding='utf-8')

# ---- WorkManager emergency alert: same truth layer + river geometry ----
p=src/'RiverAlertWorker.java';s=p.read_text(encoding='utf-8')
if 'V0902_WORKER_OFFICIAL_TRUTH' not in s:
    # doWork uses BIPAD-first merged snapshot.
    s=s.replace('            JSONObject root = fetch();\n            JSONArray rows = root.optJSONArray("results");\n            if (rows == null) rows = root.optJSONArray("data");\n            if (rows == null) return Result.retry();',
                '            OfficialRiverData.Snapshot snapshot = OfficialRiverData.fetch();\n            JSONArray rows = snapshot.rows;\n            if (rows == null || rows.length()==0) return Result.retry();\n            android.util.Log.i("FloodSafeAlert","worker_rows="+rows.length()+" bipad_rows="+snapshot.directBipadCount+" source="+snapshot.source);',1)
    # hazard stage and freshness: official status first, observation timestamp only.
    start=s.find('        double level = firstNumber(row, "waterLevel"')
    end=s.find('        String stationId = firstString(row, "stationSeriesId"',start)
    if start<0 or end<0:raise SystemExit('worker hazard status block missing')
    new='''        double level = firstNumber(row, "waterLevel", "water_level", "currentWaterLevel",\n                "current_water_level", "currentLevel", "current_level", "level", "value", "_lastWaterLevel");\n        double warning = firstNumber(row, "warningLevel", "warning_level", "warningThreshold",\n                "warning_threshold", "_lastWarningLevel");\n        double danger = firstNumber(row, "dangerLevel", "danger_level", "dangerThreshold",\n                "danger_threshold", "_lastDangerLevel");\n        long measuredAt=OfficialRiverData.observationTime(row);\n        if(!OfficialRiverData.isCurrent(measuredAt,now))return null;\n        String stage=OfficialRiverData.stage(row,true);\n        if (!("warning".equals(stage) || "danger".equals(stage))) return null;\n\n'''
    s=s[:start]+new+s[end:]
    s=s.replace('            String name = firstNonEmpty(w.optString("name_ne"), w.optString("name"), w.optString("name_en"));','            String name = firstNonEmpty(w.optString("name_en"), w.optString("name"), w.optString("name_ne"));',1)
    s=s.replace('public final class RiverAlertWorker extends Worker {','public final class RiverAlertWorker extends Worker {\n    // V0902_WORKER_OFFICIAL_TRUTH',1)
    p.write_text(s,encoding='utf-8')

# ---- Remove impossible one-second background polling and unsafe point-only alerts ----
p=src/'FloodLiveGaugeMonitor.java';s=p.read_text(encoding='utf-8')
if 'V0902_REALISTIC_BACKGROUND_REFRESH' not in s:
    s=s.replace(' * One-second foreground-service rechecker for official BIPAD/DHM hydrology sources.\n * River, rainfall and the public hydrology/flood/streamflow station feeds are fetched\n * independently.  The one-second scheduler never overlaps a still-running request.',
                ' * Foreground-service cache rechecker for official BIPAD/DHM hydrology sources.\n * Network sources are checked on a realistic five-minute cadence without overlapping requests.\n * Emergency river notifications are delegated to RiverAlertWorker, which verifies freshness and\n * distance to affected river geometry (never station-point-only).',1)
    s=s.replace('final class FloodLiveGaugeMonitor {','final class FloodLiveGaugeMonitor {\n    // V0902_REALISTIC_BACKGROUND_REFRESH\n    private static final long SOURCE_REFRESH_MS=5L*60L*1000L;',1)
    s=s.replace('        handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK','        handler.postDelayed(this,SOURCE_REFRESH_MS); // V0902_FIVE_MINUTE_SOURCE_REFRESH',1)
    s=s.replace('        try{checkNearbyHazards(new JSONObject(body));}catch(Exception ignored){}','        // Notifications are intentionally not emitted here: RiverAlertWorker performs the verified geometry-distance safety gate.',1)
    s=s.replace('        // A flood/streamflow row with the same standard level/status fields is allowed\n        // to trigger the same verified 2 km warning/danger guard; metadata-only rows do nothing.\n        for(int i=0;i<feeds.length();i++)try{JSONObject item=feeds.optJSONObject(i);if(item!=null)checkNearbyHazards(item.optJSONObject("payload"));}catch(Exception ignored){}',
                '        // Cache only. Verified 2 km Warning/Danger notifications are handled by RiverAlertWorker.',1)
    p.write_text(s,encoding='utf-8')

p=src/'FloodMonitorService.java';s=p.read_text(encoding='utf-8')
if 'V0902_REALISTIC_SERVICE_REFRESH' not in s:
    s=s.replace(' * The service keeps device location fresh and runs the native one-second BIPAD/DHM\n * river/rain/hydrology rechecker while monitoring is enabled.',
                ' * The service keeps device location fresh and runs a realistic BIPAD/DHM\n * river/rain/hydrology cache refresh while monitoring is enabled.',1)
    s=s.replace('public final class FloodMonitorService extends Service implements LocationListener {','public final class FloodMonitorService extends Service implements LocationListener {\n    // V0902_REALISTIC_SERVICE_REFRESH',1)
    s=s.replace('liveHydrologyMonitor.start(); // V0872_START_ONE_SECOND_HYDRO V0872_START_1S_BACKGROUND_SOURCE','liveHydrologyMonitor.start(); // V0902_START_REALISTIC_HYDRO_CACHE_REFRESH',1)
    p.write_text(s,encoding='utf-8')

print('FloodSafe v0.9.02 rain/background patch PASS: tiered DHM match, BIPAD-first geometry alerts, five-minute source cache refresh')
