from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def between(text,start,end,repl,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end missing')
    return text[:i]+repl+text[j:]

# v0.8.62 narrowly restores the direct DHM realtime stream that v0.8.50's
# BIPAD-only loader accidentally replaced. Every foreground poll re-reads BOTH
# official sources, selects the newest measurement per station, and uses the
# proxy only if both direct sources fail. UI/map/safety/location logic is untouched.
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
            String ix=v846StationIndex(live),nm=v846StationName(live);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);if(key.endsWith(":"))continue;
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject merged=v850MergeStationMeta(meta,live);
            try{merged.put("_floodsafeOnline",true);merged.put("_floodsafeSource","BIPAD latest");}catch(Exception ignored){}
            liveByKey.put(key,merged);
        }

        try{
            String html=getTextV846("https://dhm.gov.np/hydrology/realtime-stream?_floodsafe="+now);
            long dhmAt=v846DhmUpdatedAt(html,now);
            for(DhmLiveV846 d:v846ParseDhmRows(html)){
                if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                JSONObject meta=null;
                if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));
                if(meta==null)meta=metaByName.get(v846Key(d.name));
                if(meta==null)continue;
                JSONObject row=v850MergeStationMeta(meta,null);
                row.put("stationIndex",d.index);row.put("stationName",d.name);row.put("districtName",d.district);
                row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                row.put("_measurementTime",java.time.Instant.ofEpochMilli(dhmAt).toString());
                row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");
                JSONObject f=row.optJSONObject("fields");
                double warning=numDeep(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning");
                double danger=numDeep(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger");
                String officialStatus="";
                if(Double.isFinite(danger)&&danger>0&&d.level>=danger)officialStatus="DANGER";
                else if(Double.isFinite(warning)&&warning>0&&d.level>=warning)officialStatus="WARNING";
                else if(Double.isFinite(warning)&&warning>0)officialStatus="BELOW WARNING LEVEL";
                if(!officialStatus.isEmpty())row.put("_officialStatus",officialStatus);

                String key=!d.index.isEmpty()?"i:"+v846Key(d.index):"n:"+v846Key(d.name);if(key.endsWith(":"))continue;
                JSONObject old=liveByKey.get(key);
                long oldAt=old==null?0L:trustedRowTime(old);
                long newAt=trustedRowTime(row);
                if(old==null||newAt>=oldAt)liveByKey.put(key,row); // V0862_NEWEST_OFFICIAL_WINS
            }
        }catch(Exception ignored){}

        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();
        for(java.util.Map.Entry<String,JSONObject> e:liveByKey.entrySet()){
            RiverStation s=parseStation(e.getValue(),now);if(s!=null){out.add(s);onlineKeys.add(e.getKey());}
        }

        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);if(onlineKeys.contains(key))continue;
            JSONObject off=v850MergeStationMeta(c,null);
            try{off.put("_floodsafeOnline",false);off.put("_floodsafeCatalogOnly",true);off.put("_floodsafeSource","BIPAD catalog/history");}catch(Exception ignored){}
            RiverStation s=parseStation(off,now);if(s!=null)out.add(s);
        }

        if(liveByKey.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));
                out.clear();
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","BIPAD/DHM proxy fallback");}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);if(s!=null)out.add(s);
                }
                v849CatalogCount=out.size();v849LatestCount=out.size();
            }catch(Exception ignored){}
        }
        return out; // V0862_TRUE_REALTIME_BIPAD_DHM
    }

'''
a=between(a,'    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{','    private static JSONObject v850MergeStationMeta(',loader,'v0862 loader')

if 'main.postDelayed(this,10_000L);' not in a: raise SystemExit('v0862 10-second foreground poll missing')
if 'recreate();});' in a: raise SystemExit('v0862 crash/reload language recreate unexpectedly present')

if 'versionCode 81' in g:g=g.replace('versionCode 81','versionCode 82',1)
elif 'versionCode 82' not in g:raise SystemExit('v0862 versionCode anchor missing')
if "versionName '0.8.61'" in g:g=g.replace("versionName '0.8.61'","versionName '0.8.62'",1)
elif "versionName '0.8.62'" not in g:raise SystemExit('v0862 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0862_TRUE_REALTIME_BIPAD_DHM','V0862_NEWEST_OFFICIAL_WINS','DHM realtime-stream','BIPAD latest','main.postDelayed(this,10_000L);','RIVER_FRESH_MS=20L*60L*1000L','V0861_FULL_LANGUAGE_APPLY','V0860_SOURCE_PARITY_DETAIL']:
    if x not in a:raise SystemExit('v0862 activity guard failed: '+x)
for x in ['versionCode 82',"versionName '0.8.62'"]:
    if x not in g:raise SystemExit('v0862 version guard failed: '+x)
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0862 2km safety changed')
print('FloodSafe v0.8.62 PASS: direct BIPAD + DHM polling, newest official value wins, 10s in-place refresh; UI/safety untouched')

# retrigger after v0.8.61 wrapper compatibility repair
