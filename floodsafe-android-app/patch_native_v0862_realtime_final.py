from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# Final robust v0.8.62 data-only patch. It does not replace the legacy loader;
# it injects a uniquely named final loader and points refreshRivers() to it.
# This avoids all old patch-chain anchor/spacing conflicts.

field_anchor='    private volatile int v849CatalogCount=0,v849LatestCount=0; // V0849_SOURCE_COUNTS'
if 'V0862_FINAL_REFRESH_FIELDS' not in a:
    if field_anchor not in a:raise SystemExit('v0862 final source-count field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile boolean v862FinalRefreshInFlight=false; private volatile String v862FinalLastFingerprint=""; // V0862_FINAL_REFRESH_FIELDS',1)

loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
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

        java.util.LinkedHashMap<String,JSONObject> current=new java.util.LinkedHashMap<>();
        for(int i=0;i<bipadLatest.length();i++){
            JSONObject live=bipadLatest.optJSONObject(i);if(live==null)continue;
            String ix=v846StationIndex(live),nm=v846StationName(live),key=v862FinalKey(ix,nm);if(key.isEmpty())continue;
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject row=v862FinalMetaOnly(meta,live);
            try{row.put("_floodsafeOnline",true);row.put("_floodsafeSource","BIPAD latest direct");}catch(Exception ignored){}
            current.put(key,row);
        }

        // Direct official DHM live stream. Newer official timestamp wins over BIPAD.
        String[] dhmUrls={"https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,"https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now};
        for(String url:dhmUrls){
            try{
                String html=getTextV846(url);long pageAt=v846DhmUpdatedAt(html,0L);
                for(DhmLiveV846 d:v846ParseDhmRows(html)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    JSONObject meta=null;if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));if(meta==null)meta=metaByName.get(v846Key(d.name));if(meta==null)continue;
                    JSONObject row=v862FinalMetaOnly(meta,null);
                    row.put("stationIndex",d.index);row.put("stationName",d.name);if(!d.district.isEmpty())row.put("districtName",d.district);
                    row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                    if(pageAt>0)row.put("_measurementTime",java.time.Instant.ofEpochMilli(pageAt).toString());
                    row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");
                    JSONObject f=row.optJSONObject("fields");
                    double warning=numDeep(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning");
                    double danger=numDeep(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger");
                    String status="";if(Double.isFinite(danger)&&danger>0&&d.level>=danger)status="DANGER";else if(Double.isFinite(warning)&&warning>0&&d.level>=warning)status="WARNING";else if(Double.isFinite(warning)&&warning>0)status="BELOW WARNING LEVEL";if(!status.isEmpty())row.put("_officialStatus",status);

                    String key=v862FinalKey(d.index,d.name);if(key.isEmpty())continue;
                    JSONObject old=current.get(key);long oldAt=old==null?0L:trustedRowTime(old),newAt=trustedRowTime(row);
                    JSONObject of=old==null?null:old.optJSONObject("fields");double oldLevel=old==null?Double.NaN:numDeep(old,of,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");
                    if(old==null||(newAt>0&&(oldAt<=0||newAt>oldAt))||(newAt==oldAt&&!Double.isFinite(oldLevel)))current.put(key,row); // V0862_FINAL_NEWEST_OFFICIAL_WINS
                }
            }catch(Exception ignored){}
        }

        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();
        for(java.util.Map.Entry<String,JSONObject> e:current.entrySet()){RiverStation s=parseStation(e.getValue(),now);if(s!=null){out.add(s);onlineKeys.add(e.getKey());}}

        // Keep last official catalog reading for history only; never overwrite current.
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;String ix=v846StationIndex(c),nm=v846StationName(c),key=v862FinalKey(ix,nm);if(key.isEmpty()||onlineKeys.contains(key))continue;
            JSONObject off=new JSONObject(c.toString());try{off.put("_floodsafeOnline",false);off.put("_floodsafeCatalogOnly",true);off.put("_floodsafeSource","BIPAD catalog history");}catch(Exception ignored){}
            RiverStation s=parseStation(off,now);if(s!=null)out.add(s);
        }

        // Proxy only when neither direct live source returned a usable current row.
        if(current.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));out.clear();
                for(int i=0;i<rr.length();i++){JSONObject r=rr.optJSONObject(i);if(r==null)continue;try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","official proxy fallback");}catch(Exception ignored){}RiverStation s=parseStation(r,now);if(s!=null)out.add(s);}
                v849LatestCount=out.size();if(v849CatalogCount<=0)v849CatalogCount=out.size();
            }catch(Exception ignored){}
        }
        return out; // V0862_FINAL_TRUE_REALTIME_BIPAD_DHM
    }

    private static String v862FinalKey(String index,String name){if(index!=null&&!index.trim().isEmpty())return "i:"+v846Key(index);if(name!=null&&!name.trim().isEmpty())return "n:"+v846Key(name);return "";}

    private static JSONObject v862FinalMetaOnly(JSONObject meta,JSONObject live){
        JSONObject out=new JSONObject();try{if(meta!=null)out=new JSONObject(meta.toString());}catch(Exception ignored){}v862FinalStripObservation(out);
        if(live!=null)try{java.util.Iterator<String> it=live.keys();while(it.hasNext()){String k=it.next();Object v=live.opt(k);if(v!=null)out.put(k,v);}}catch(Exception ignored){}return out;
    } // V0862_FINAL_CATALOG_METADATA_ONLY

    private static void v862FinalStripObservation(JSONObject o){
        if(o==null)return;String[] keys={"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level"};
        for(String k:keys)o.remove(k);JSONObject f=o.optJSONObject("fields");if(f!=null)for(String k:keys)f.remove(k);
    }

'''
parse_match=re.search(r'(?m)^\s*private\s+RiverStation\s+parseStation\s*\(',a)
if not parse_match:raise SystemExit('v0862 final parseStation insertion anchor missing')
a=a[:parse_match.start()]+loader+a[parse_match.start():]

# Replace only refreshRivers(), using brace matching, so no UI tree/activity reload occurs.
def method_span(text,name):
    m=re.search(r'(?m)^\s*private\s+void\s+'+re.escape(name)+r'\s*\(\s*\)\s*\{',text)
    if not m:return None
    op=text.find('{',m.start());depth=0;quote=None;esc=False
    i=op
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
                if depth==0:return (m.start(),i+1)
        i+=1
    return None

refresh=r'''    private void refreshRivers(){
        if(v862FinalRefreshInFlight)return;v862FinalRefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> out=loadTrustedRiverStationsV862(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                String fp=v862FinalFingerprint(out);boolean changed=!fp.equals(v862FinalLastFingerprint);
                if(!out.isEmpty()&&changed){synchronized(stations){stations.clear();stations.addAll(out);}v862FinalLastFingerprint=fp;}
                runOnUiThread(()->{v862FinalRefreshInFlight=false;if(changed&&!out.isEmpty())refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v862FinalRefreshInFlight=false);}
        });
    } // V0862_FINAL_NO_FLICKER_REFRESH
'''
span=method_span(a,'refreshRivers')
if not span:raise SystemExit('v0862 final refreshRivers anchor missing')
a=a[:span[0]]+refresh+a[span[1]:]

finger=r'''    private static String v862FinalFingerprint(List<RiverStation> rows){StringBuilder b=new StringBuilder();for(RiverStation s:rows){b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|');if(Double.isFinite(s.level))b.append(String.format(Locale.US,"%.3f",s.level));b.append(';');}return b.toString();} // V0862_FINAL_FINGERPRINT

'''
# place fingerprint immediately before our unique loader
anchor='    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{'
pos=a.find(anchor)
if pos<0:raise SystemExit('v0862 final loader missing after insertion')
a=a[:pos]+finger+a[pos:]

if 'main.postDelayed(this,10_000L);' not in a:raise SystemExit('v0862 final 10-second foreground poll missing')
if 'RIVER_FRESH_MS=20L*60L*1000L' not in a:raise SystemExit('v0862 final 20-minute safety changed')
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0862 final 2-km safety changed')
if 'recreate();});' in a:raise SystemExit('v0862 final crash/reload recreate returned')

if 'versionCode 81' in g:g=g.replace('versionCode 81','versionCode 82',1)
elif 'versionCode 82' not in g:raise SystemExit('v0862 final versionCode anchor missing')
if "versionName '0.8.61'" in g:g=g.replace("versionName '0.8.61'","versionName '0.8.62'",1)
elif "versionName '0.8.62'" not in g:raise SystemExit('v0862 final versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for x in ['V0862_FINAL_TRUE_REALTIME_BIPAD_DHM','V0862_FINAL_NEWEST_OFFICIAL_WINS','V0862_FINAL_CATALOG_METADATA_ONLY','V0862_FINAL_NO_FLICKER_REFRESH','DHM realtime-stream','BIPAD latest direct','V0861_FULL_LANGUAGE_APPLY','V0860_SOURCE_PARITY_DETAIL']:
    if x not in a:raise SystemExit('v0862 final activity guard failed: '+x)
for x in ['versionCode 82',"versionName '0.8.62'"]:
    if x not in g:raise SystemExit('v0862 final version guard failed: '+x)
print('FloodSafe v0.8.62 FINAL PASS: direct BIPAD+DHM newest official snapshot + 10s no-flicker in-place refresh; old reading history only; UI/safety untouched')
