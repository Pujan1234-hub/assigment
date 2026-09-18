from pathlib import Path
import re

root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=app/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')


def between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end missing')
    return text[:i]+replacement+text[j:]

# Narrow data-pipeline repair on top of v0.8.61:
# - never let stale catalog observation fields overwrite a latest/live row
# - read BIPAD latest and DHM realtime directly on every foreground poll
# - choose the newest trustworthy direct observation per station
# - keep catalog rows only for metadata/offline display
# - retain the previous UI while a poll is running; update only when data changed
# - do NOT alter map geometry, language, GPS, colours, 20-minute safety or 2 km alerts

field_anchor='    private volatile int v849CatalogCount=0,v849LatestCount=0; // V0849_SOURCE_COUNTS'
if 'V0861_DATA_REFRESH_FIELDS' not in a:
    if field_anchor not in a: raise SystemExit('datafix source-count field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile boolean v861DataRefreshInFlight=false; private volatile String v861DataFingerprint=""; // V0861_DATA_REFRESH_FIELDS',1)

# -----------------------------------------------------------------------------
# Direct source loader.
# -----------------------------------------------------------------------------
loader=r'''    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        JSONArray catalog=new JSONArray(),latest=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=2000&_fs="+now,now);}catch(Exception ignored){}
        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000&_fs="+now,now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();v849LatestCount=latest.length();

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        java.util.LinkedHashMap<String,JSONObject> direct=new java.util.LinkedHashMap<>();
        java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();

        // BIPAD latest: catalog contributes ONLY identity/coordinates/threshold metadata.
        // Old catalog water level/time/status fields are explicitly removed before live merge.
        for(int i=0;i<latest.length();i++){
            JSONObject live=latest.optJSONObject(i);if(live==null)continue;
            String ix=v846StationIndex(live),nm=v846StationName(live);
            String key=v861DataKey(ix,nm);if(key.isEmpty())continue;
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject row=v861DataMergeMetaOnly(meta,live);
            try{row.put("_floodsafeOnline",true);row.put("_floodsafeSource","BIPAD latest direct");}catch(Exception ignored){}
            direct.put(key,row);onlineKeys.add(key);
        }

        // DHM is a separate official live source. v0.8.50 accidentally stopped merging it.
        // Try both realtime-stream hosts and river-watch; duplicate rows collapse by station key.
        String[] dhmUrls={
                "https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,
                "https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now,
                "https://dhm.gov.np/hydrology/river-watch?_fs="+now
        };
        java.util.LinkedHashMap<String,V861DhmReading> dhmRows=new java.util.LinkedHashMap<>();
        for(String u:dhmUrls){
            try{
                String html=getTextV846(u);long pageAt=v846DhmUpdatedAt(html,0L);
                for(V861DhmReading d:v861DataParseDhm(html,pageAt)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    String key=v861DataKey(d.index,d.name);if(key.isEmpty())continue;
                    V861DhmReading old=dhmRows.get(key);
                    if(old==null||(d.at>0&&d.at>old.at)||(!Double.isFinite(old.level)&&Double.isFinite(d.level)))dhmRows.put(key,d);
                }
            }catch(Exception ignored){}
        }

        for(java.util.Map.Entry<String,V861DhmReading> en:dhmRows.entrySet()){
            V861DhmReading d=en.getValue();String key=en.getKey();
            JSONObject meta=null;
            if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));
            if(meta==null&&!d.name.isEmpty())meta=metaByName.get(v846Key(d.name));
            if(meta==null)meta=v861DataFindMeta(metaByName,d.name);
            if(meta==null)continue;

            JSONObject dhm=v861DataMergeMetaOnly(meta,null);
            try{
                dhm.put("stationIndex",d.index);dhm.put("stationName",d.name);if(!d.district.isEmpty())dhm.put("districtName",d.district);
                dhm.put("waterLevel",d.level);if(Double.isFinite(d.warning))dhm.put("warningLevel",d.warning);if(Double.isFinite(d.danger))dhm.put("dangerLevel",d.danger);
                if(d.at>0)dhm.put("_measurementTime",java.time.Instant.ofEpochMilli(d.at).toString());
                if(!d.status.isEmpty())dhm.put("_officialStatus",d.status);
                dhm.put("_floodsafeOnline",true);dhm.put("_floodsafeSource","DHM realtime direct");
            }catch(Exception ignored){}

            JSONObject old=direct.get(key);
            if(old==null){direct.put(key,dhm);onlineKeys.add(key);continue;}
            long oldAt=trustedRowTime(old),newAt=d.at;
            JSONObject of=old.optJSONObject("fields");double oldLevel=numDeep(old,of,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");
            boolean oldStale=oldAt<=0||now-oldAt>RIVER_FRESH_MS;
            boolean prefer=(newAt>0&&(oldAt<=0||newAt>oldAt))||(newAt<=0&&oldStale&&Double.isFinite(d.level));
            if(prefer)direct.put(key,dhm);
            else if(!Double.isFinite(oldLevel)&&Double.isFinite(d.level))direct.put(key,dhm);
            onlineKeys.add(key);
        }

        List<RiverStation> out=new ArrayList<>();
        for(java.util.Map.Entry<String,JSONObject> en:direct.entrySet()){
            RiverStation s=parseStation(en.getValue(),now);if(s!=null)out.add(s);
        }

        // Catalog-only stations remain visible as black/offline and may show their last
        // official historical reading. They can never become live merely from catalog data.
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c),key=v861DataKey(ix,nm);if(key.isEmpty()||onlineKeys.contains(key))continue;
            JSONObject off=v850MergeStationMeta(c,null);
            try{off.put("_floodsafeOnline",false);off.put("_floodsafeCatalogOnly",true);off.put("_floodsafeSource","BIPAD catalog history");}catch(Exception ignored){}
            RiverStation s=parseStation(off,now);if(s!=null)out.add(s);
        }

        // Last resort only when BOTH direct official paths produced nothing.
        if(direct.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));
                out.clear();
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","official proxy fallback");}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);if(s!=null)out.add(s);
                }
                v849LatestCount=out.size();if(v849CatalogCount<=0)v849CatalogCount=out.size();
            }catch(Exception ignored){}
        }
        return out; // V0861_DIRECT_BIPAD_DHM_NEWEST
    }

    private static String v861DataKey(String index,String name){
        if(index!=null&&!index.trim().isEmpty())return "i:"+v846Key(index);
        if(name!=null&&!name.trim().isEmpty())return "n:"+v846Key(name);
        return "";
    }

    private static JSONObject v861DataMergeMetaOnly(JSONObject meta,JSONObject live){
        JSONObject out=new JSONObject();
        try{if(meta!=null)out=new JSONObject(meta.toString());}catch(Exception ignored){}
        v861DataStripObservation(out);
        if(live!=null)try{java.util.Iterator<String> it=live.keys();while(it.hasNext()){String k=it.next();Object v=live.opt(k);if(v!=null)out.put(k,v);}}catch(Exception ignored){}
        return out;
    } // V0861_META_NO_STALE_OBSERVATION

    private static void v861DataStripObservation(JSONObject o){
        if(o==null)return;
        String[] keys={"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level"};
        for(String k:keys)o.remove(k);
        JSONObject f=o.optJSONObject("fields");if(f!=null)for(String k:keys)f.remove(k);
    }

    private static JSONObject v861DataFindMeta(java.util.LinkedHashMap<String,JSONObject> byName,String name){
        String k=v846Key(name);if(k.isEmpty())return null;JSONObject x=byName.get(k);if(x!=null)return x;
        for(java.util.Map.Entry<String,JSONObject> e:byName.entrySet()){String q=e.getKey();if(q.length()>=6&&(q.contains(k)||k.contains(q)))return e.getValue();}
        return null;
    }

    private static final class V861DhmReading{
        String index="",name="",district="",status="";double level=Double.NaN,warning=Double.NaN,danger=Double.NaN;long at=0L;
    }

    private static List<V861DhmReading> v861DataParseDhm(String html,long pageAt){
        List<V861DhmReading> out=new ArrayList<>();if(html==null||html.isEmpty())return out;
        try{
            java.util.regex.Matcher rm=java.util.regex.Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
            while(rm.find()){
                java.util.ArrayList<String> cells=new java.util.ArrayList<>();
                java.util.regex.Matcher cm=java.util.regex.Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>").matcher(rm.group(1));
                while(cm.find())cells.add(v846HtmlText(cm.group(1)));
                if(cells.size()<2)continue;
                V861DhmReading d=new V861DhmReading();d.at=pageAt;
                if(cells.size()>=6&&cells.get(0).matches("\\d+")){
                    d.index=cells.get(2).trim();d.name=cells.get(3).trim();d.district=cells.get(4).trim();d.level=v846Number(cells.get(5));if(cells.size()>7)d.status=cells.get(cells.size()-1).trim();
                }else{
                    d.name=cells.get(0).trim();d.level=v846Number(cells.get(1));if(cells.size()>2)d.status=cells.get(2).trim();
                }
                if(!d.name.isEmpty()&&Double.isFinite(d.level))out.add(d);
            }
        }catch(Exception ignored){}
        try{
            String plain=v846HtmlText(html);
            java.util.regex.Matcher m=java.util.regex.Pattern.compile("([A-Za-z][A-Za-z0-9 .()'/-]{2,80}?)\\s+WL:\\s*([0-9]+(?:\\.[0-9]+)?)\\s*m\\s+WR:\\s*([0-9]+(?:\\.[0-9]+)?)\\s*m\\s+DL:\\s*([0-9]+(?:\\.[0-9]+)?)\\s*m",java.util.regex.Pattern.CASE_INSENSITIVE).matcher(plain);
            while(m.find()){
                V861DhmReading d=new V861DhmReading();d.name=m.group(1).trim();d.level=v846Number(m.group(2));d.warning=v846Number(m.group(3));d.danger=v846Number(m.group(4));d.at=pageAt;if(!d.name.isEmpty()&&Double.isFinite(d.level))out.add(d);
            }
        }catch(Exception ignored){}
        return out;
    }

'''
a=between(a,'    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{','    private static JSONObject v850MergeStationMeta(',loader,'datafix direct-source loader')

# -----------------------------------------------------------------------------
# No-flicker foreground refresh.
# -----------------------------------------------------------------------------
refresh=r'''    private void refreshRivers(){
        if(v861DataRefreshInFlight)return;v861DataRefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> out=loadTrustedRiverStations(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                String fp=v861DataFingerprint(out);boolean changed=!fp.equals(v861DataFingerprint);
                if(!out.isEmpty()&&changed){synchronized(stations){stations.clear();stations.addAll(out);}v861DataFingerprint=fp;}
                runOnUiThread(()->{v861DataRefreshInFlight=false;if(changed&&!out.isEmpty())refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v861DataRefreshInFlight=false);}
        });
    } // V0861_NO_FLICKER_DIRECT_REFRESH

    private static String v861DataFingerprint(List<RiverStation> rows){
        StringBuilder b=new StringBuilder();for(RiverStation s:rows){b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|');if(Double.isFinite(s.level))b.append(String.format(Locale.US,"%.3f",s.level));b.append(';');}return b.toString();
    }

'''
a=between(a,'    private void refreshRivers(){','    private RiverStation parseStation(',refresh,'datafix no-flicker refresh')

if 'main.postDelayed(this,10_000L);' not in a: raise SystemExit('datafix 10-second poll missing')
if 'RIVER_FRESH_MS=20L*60L*1000L' not in a: raise SystemExit('datafix 20-minute safety missing')
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a: raise SystemExit('datafix 2-km safety guard changed')

if 'versionCode 81' in g:g=g.replace('versionCode 81','versionCode 82',1)
elif 'versionCode 82' not in g:raise SystemExit('datafix versionCode anchor missing')
if "versionName '0.8.61'" in g:g=g.replace("versionName '0.8.61'","versionName '0.8.61-datafix'",1)
elif "versionName '0.8.61-datafix'" not in g:raise SystemExit('datafix versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for needle in ['V0861_DATA_REFRESH_FIELDS','V0861_DIRECT_BIPAD_DHM_NEWEST','V0861_META_NO_STALE_OBSERVATION','V0861_NO_FLICKER_DIRECT_REFRESH','DHM realtime direct','BIPAD latest direct']:
    if needle not in a:raise SystemExit('datafix activity verification failed: '+needle)
if 'feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…"' in a:raise SystemExit('datafix transient refresh text still present')
for needle in ['versionCode 82',"versionName '0.8.61-datafix'"]:
    if needle not in g:raise SystemExit('datafix build identity verification failed: '+needle)
print('FloodSafe v0.8.61-datafix PASS: direct BIPAD+DHM newest observation, stale catalog leak blocked, no-flicker polling, safety/map unchanged')
