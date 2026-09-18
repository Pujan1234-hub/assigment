from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.62 is data-pipeline only:
# - poll BIPAD latest + DHM realtime directly every existing foreground cycle
# - newest trustworthy official observation wins per station
# - catalog is metadata/history only and cannot overwrite a current observation
# - UI updates in place only when station data changes (no screen reload/flicker)
# - map/language/GPS/colours/weather/20-minute safety/2-km alert stay unchanged

loader=r'''    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        JSONArray catalog=new JSONArray(),bipadLatest=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=2000&_fs="+now,now);}catch(Exception ignored){}
        try{bipadLatest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000&_fs="+now,now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();v849LatestCount=bipadLatest.length();

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        java.util.LinkedHashMap<String,JSONObject> liveByKey=new java.util.LinkedHashMap<>();
        for(int i=0;i<bipadLatest.length();i++){
            JSONObject live=bipadLatest.optJSONObject(i);if(live==null)continue;
            String ix=v846StationIndex(live),nm=v846StationName(live),key=v862Key(ix,nm);if(key.isEmpty())continue;
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject merged=v862MetaOnly(meta,live);
            try{merged.put("_floodsafeOnline",true);merged.put("_floodsafeSource","BIPAD latest direct");}catch(Exception ignored){}
            liveByKey.put(key,merged);
        }

        // Restore direct DHM realtime union. v0.8.50 accidentally replaced this with BIPAD-only.
        String[] dhmUrls={
            "https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,
            "https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now
        };
        for(String url:dhmUrls){
            try{
                String html=getTextV846(url);long dhmAt=v846DhmUpdatedAt(html,0L);
                for(DhmLiveV846 d:v846ParseDhmRows(html)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    JSONObject meta=null;
                    if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));
                    if(meta==null)meta=metaByName.get(v846Key(d.name));
                    if(meta==null)continue;
                    JSONObject row=v862MetaOnly(meta,null);
                    row.put("stationIndex",d.index);row.put("stationName",d.name);row.put("districtName",d.district);
                    row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                    if(dhmAt>0)row.put("_measurementTime",java.time.Instant.ofEpochMilli(dhmAt).toString());
                    row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");
                    JSONObject f=row.optJSONObject("fields");
                    double warning=numDeep(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning");
                    double danger=numDeep(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger");
                    String status="";
                    if(Double.isFinite(danger)&&danger>0&&d.level>=danger)status="DANGER";
                    else if(Double.isFinite(warning)&&warning>0&&d.level>=warning)status="WARNING";
                    else if(Double.isFinite(warning)&&warning>0)status="BELOW WARNING LEVEL";
                    if(!status.isEmpty())row.put("_officialStatus",status);

                    String key=v862Key(d.index,d.name);if(key.isEmpty())continue;
                    JSONObject old=liveByKey.get(key);
                    long oldAt=old==null?0L:trustedRowTime(old),newAt=trustedRowTime(row);
                    JSONObject of=old==null?null:old.optJSONObject("fields");
                    double oldLevel=old==null?Double.NaN:numDeep(old,of,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");
                    if(old==null||(newAt>0&&(oldAt<=0||newAt>oldAt))||(newAt==oldAt&&!Double.isFinite(oldLevel)))liveByKey.put(key,row); // V0862_NEWEST_OFFICIAL_WINS
                }
            }catch(Exception ignored){}
        }

        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();
        for(java.util.Map.Entry<String,JSONObject> e:liveByKey.entrySet()){
            RiverStation s=parseStation(e.getValue(),now);if(s!=null){out.add(s);onlineKeys.add(e.getKey());}
        }

        // Catalog rows are history/offline only. They never overwrite liveByKey.
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c),key=v862Key(ix,nm);if(key.isEmpty()||onlineKeys.contains(key))continue;
            JSONObject off=new JSONObject(c.toString());
            try{off.put("_floodsafeOnline",false);off.put("_floodsafeCatalogOnly",true);off.put("_floodsafeSource","BIPAD catalog history");}catch(Exception ignored){}
            RiverStation s=parseStation(off,now);if(s!=null)out.add(s);
        }

        // Proxy is last resort only if BOTH direct official live paths produced nothing.
        if(liveByKey.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));out.clear();
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","official proxy fallback");}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);if(s!=null)out.add(s);
                }
                v849CatalogCount=out.size();v849LatestCount=out.size();
            }catch(Exception ignored){}
        }
        return out; // V0862_TRUE_REALTIME_BIPAD_DHM
    }

    private static String v862Key(String index,String name){
        if(index!=null&&!index.trim().isEmpty())return "i:"+v846Key(index);
        if(name!=null&&!name.trim().isEmpty())return "n:"+v846Key(name);
        return "";
    }

    private static JSONObject v862MetaOnly(JSONObject meta,JSONObject live){
        JSONObject out=new JSONObject();
        try{if(meta!=null)out=new JSONObject(meta.toString());}catch(Exception ignored){}
        v862StripObservation(out);
        if(live!=null)try{java.util.Iterator<String> it=live.keys();while(it.hasNext()){String k=it.next();Object v=live.opt(k);if(v!=null)out.put(k,v);}}catch(Exception ignored){}
        return out;
    } // V0862_CATALOG_METADATA_ONLY

    private static void v862StripObservation(JSONObject o){
        if(o==null)return;
        String[] keys={"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level"};
        for(String k:keys)o.remove(k);JSONObject f=o.optJSONObject("fields");if(f!=null)for(String k:keys)f.remove(k);
    }

'''

# Replace the existing loader regardless of spacing/format. If the v0.8.61 legacy patch
# did not leave one behind, insert this final loader before the known merge helper.
start=re.search(r'(?m)^\s*private\s+List<RiverStation>\s+loadTrustedRiverStations\s*\(\s*long\s+now\s*\)\s*throws\s+Exception\s*\{',a)
end_marker='    private static JSONObject v850MergeStationMeta('
end=a.find(end_marker,start.start() if start else 0)
if start and end>=0:
    a=a[:start.start()]+loader+a[end:]
elif end>=0:
    a=a[:end]+loader+a[end:]
else:
    raise SystemExit('v0862 loader insertion anchor missing')

# No-flicker in-place refresh, independent of the brittle v0.8.61 data patch.
field_anchor='    private volatile int v849CatalogCount=0,v849LatestCount=0; // V0849_SOURCE_COUNTS'
if 'V0862_REFRESH_FIELDS' not in a:
    if field_anchor not in a:raise SystemExit('v0862 source count field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile boolean v862RefreshInFlight=false; private volatile String v862Fingerprint=""; // V0862_REFRESH_FIELDS',1)

refresh=r'''    private void refreshRivers(){
        if(v862RefreshInFlight)return;v862RefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> out=loadTrustedRiverStations(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                String fp=v862Fingerprint(out);boolean changed=!fp.equals(v862Fingerprint);
                if(!out.isEmpty()&&changed){synchronized(stations){stations.clear();stations.addAll(out);}v862Fingerprint=fp;}
                runOnUiThread(()->{v862RefreshInFlight=false;if(changed&&!out.isEmpty())refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v862RefreshInFlight=false);}
        });
    } // V0862_NO_FLICKER_INPLACE_REFRESH

    private static String v862Fingerprint(List<RiverStation> rows){
        StringBuilder b=new StringBuilder();for(RiverStation s:rows){b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|');if(Double.isFinite(s.level))b.append(String.format(Locale.US,"%.3f",s.level));b.append(';');}return b.toString();
    }

'''
rs=re.search(r'(?m)^\s*private\s+void\s+refreshRivers\s*\(\s*\)\s*\{',a)
pe=re.search(r'(?m)^\s*private\s+RiverStation\s+parseStation\s*\(',a[rs.start():] if rs else '')
if not rs or not pe:raise SystemExit('v0862 refresh method anchors missing')
refresh_end=rs.start()+pe.start()
a=a[:rs.start()]+refresh+a[refresh_end:]

if 'main.postDelayed(this,10_000L);' not in a:raise SystemExit('v0862 10-second foreground poll missing')
if 'recreate();});' in a:raise SystemExit('v0862 crash/reload language recreate unexpectedly present')
if 'RIVER_FRESH_MS=20L*60L*1000L' not in a:raise SystemExit('v0862 20-minute safety changed')
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0862 2km safety changed')

if 'versionCode 81' in g:g=g.replace('versionCode 81','versionCode 82',1)
elif 'versionCode 82' not in g:raise SystemExit('v0862 versionCode anchor missing')
if "versionName '0.8.61'" in g:g=g.replace("versionName '0.8.61'","versionName '0.8.62'",1)
elif "versionName '0.8.62'" not in g:raise SystemExit('v0862 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for x in ['V0862_TRUE_REALTIME_BIPAD_DHM','V0862_NEWEST_OFFICIAL_WINS','V0862_CATALOG_METADATA_ONLY','V0862_NO_FLICKER_INPLACE_REFRESH','DHM realtime-stream','BIPAD latest direct','main.postDelayed(this,10_000L);','RIVER_FRESH_MS=20L*60L*1000L','V0861_FULL_LANGUAGE_APPLY','V0860_SOURCE_PARITY_DETAIL']:
    if x not in a:raise SystemExit('v0862 activity guard failed: '+x)
for x in ['versionCode 82',"versionName '0.8.62'"]:
    if x not in g:raise SystemExit('v0862 version guard failed: '+x)
print('FloodSafe v0.8.62 PASS: newest direct BIPAD+DHM observation wins; catalog metadata/history only; 10s no-flicker in-place refresh; UI/safety untouched')
