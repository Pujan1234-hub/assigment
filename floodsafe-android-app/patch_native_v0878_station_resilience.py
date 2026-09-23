from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.78 field-test hotfix: station inventory must never disappear just because an
# upstream catalogue request is empty/partial, and a previously verified official
# observation must not flicker to "no reading" on one transient refresh failure.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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

def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0878 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

anchor='    } // V0877_CLEAN_REAL_OBSERVATION_MERGE\n'
if anchor not in a:
    raise SystemExit('v0878 requires clean v0877 base')

helpers=r'''

    private JSONArray v878BundledStationCatalog(){
        try{
            JSONObject seed=assetJson("data/floodsafe-core.json");
            JSONArray rows=seed.optJSONArray("river_stations");
            if(rows==null)rows=seed.optJSONArray("riverStations");
            return rows==null?new JSONArray():rows;
        }catch(Exception ignored){return new JSONArray();}
    } // V0878_STATION_CATALOG_FALLBACK

    private JSONArray v878ReadLastGoodObservations(){
        try(BufferedReader r=new BufferedReader(new InputStreamReader(openFileInput("floodsafe-river-lastgood-v878.json"),StandardCharsets.UTF_8))){
            StringBuilder b=new StringBuilder();String line;while((line=r.readLine())!=null)b.append(line);
            return b.length()==0?new JSONArray():new JSONArray(b.toString());
        }catch(Exception ignored){return new JSONArray();}
    } // V0878_LAST_GOOD_OBSERVATION_CACHE

    private void v878WriteLastGoodObservations(java.util.Collection<JSONObject> rows){
        try{
            JSONArray out=new JSONArray();
            if(rows!=null)for(JSONObject r:rows){
                if(r==null)continue;double l=v877ObservationLevel(r);long at=v877ObservationTime(r);
                if(!Double.isFinite(l)||at<=0L)continue;
                out.put(new JSONObject(r.toString()));
            }
            try(java.io.OutputStreamWriter w=new java.io.OutputStreamWriter(openFileOutput("floodsafe-river-lastgood-v878.json",MODE_PRIVATE),StandardCharsets.UTF_8)){w.write(out.toString());}
        }catch(Exception ignored){}
    } // V0878_LAST_GOOD_OBSERVATION_PERSIST

    private JSONObject v878MetadataOnly(JSONObject src){
        try{
            JSONObject out=src==null?new JSONObject():new JSONObject(src.toString());
            String[] readingKeys={"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","_lastDischarge","discharge","currentDischarge","current_discharge","flow","flowRate","flow_rate","_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp"};
            for(String k:readingKeys)out.remove(k);
            JSONObject f=out.optJSONObject("fields");if(f!=null)for(String k:readingKeys)f.remove(k);
            out.put("_floodsafeObservationMatched",false);out.put("_floodsafeOnline",false);out.put("_floodsafeCatalogOnly",true);
            return out;
        }catch(Exception ignored){return new JSONObject();}
    } // V0878_METADATA_NEVER_LIVE
'''
a=a.replace(anchor,anchor+helpers,1)

loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
        JSONArray bundled=v878BundledStationCatalog();
        JSONArray liveCatalog=new JSONArray();
        try{liveCatalog=trustedPages(BIPAD+"river-stations/?limit=5000&_fs="+now,now);}catch(Exception ignored){}
        int bundledCount=bundled.length(),liveCount=liveCatalog.length();
        boolean liveLooksComplete=liveCount>0&&(bundledCount==0||liveCount>=Math.max(25,(int)Math.floor(bundledCount*0.70)));
        JSONArray catalog=liveLooksComplete?liveCatalog:(bundledCount>0?bundled:liveCatalog);
        if(catalog.length()==0)throw new IllegalStateException("No official station inventory available");
        v849CatalogCount=catalog.length(); // V0878_STATION_CATALOG_NEVER_EMPTY

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metadataMatch=new java.util.LinkedHashMap<>();

        // Seed from the last verified official observations. They remain inspectable with
        // their original source time, but freshness logic alone decides LIVE/current risk.
        JSONArray cached=v878ReadLastGoodObservations();
        for(int i=0;i<cached.length();i++){
            JSONObject old=cached.optJSONObject(i);if(old==null)continue;
            String ix=v846StationIndex(old),nm=v846StationName(old);
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;
            if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            if(meta==null)continue;
            double l=v877ObservationLevel(old);long at=v877ObservationTime(old);if(!Double.isFinite(l)||at<=0L)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
            JSONObject row=v877MergeOfficial(meta,old);try{row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","Last verified official observation cache");}catch(Exception ignored){}
            JSONObject prev=newest.get(key);if(prev==null||at>v877ObservationTime(prev))newest.put(key,row);
        } // V0878_NO_READING_FLICKER

        // Also seed from the current process' last-good rows so a single missing endpoint
        // response cannot erase a reading before disk cache catches up.
        for(JSONObject old:v871SourceRowsByName.values()){
            if(old==null)continue;String ix=v846StationIndex(old),nm=v846StationName(old);
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));if(meta==null)continue;
            double l=v877ObservationLevel(old);long at=v877ObservationTime(old);if(!Double.isFinite(l)||at<=0L)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;JSONObject row=v877MergeOfficial(meta,old);
            try{row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);}catch(Exception ignored){}
            JSONObject prev=newest.get(key);if(prev==null||at>v877ObservationTime(prev))newest.put(key,row);
        }

        String[] paths={"river/?limit=5000","river-trimed/?limit=5000","river-stations/?latest=true&limit=5000","flood-station/?limit=5000","streamflow/?limit=5000","station-location/?limit=5000"};
        for(String path:paths){
            try{
                JSONArray rows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<rows.length();i++){
                    JSONObject live=rows.optJSONObject(i);if(live==null)continue;
                    String ix=v846StationIndex(live),nm=v846StationName(live);
                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;
                    if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
                    if(meta==null)continue;
                    String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
                    JSONObject merged=v877MergeOfficial(meta,live);
                    try{
                        merged.put("_floodsafeSource","BIPAD "+path);
                        String rn=v877RiverName(live);if(rn.isEmpty())rn=v877RiverName(meta);if(!rn.isEmpty())merged.put("_floodsafeRiverName",rn);
                        String wt=v877WaterbodyType(live);if(wt.isEmpty())wt=v877WaterbodyType(meta);if(!wt.isEmpty())merged.put("_floodsafeWaterbodyType",wt);
                    }catch(Exception ignored){}
                    metadataMatch.put(key,merged);
                    double level=v877ObservationLevel(live);long at=v877ObservationTime(live);
                    if(!Double.isFinite(level)||at<=0L)continue;
                    try{merged.put("_floodsafeObservationMatched",true);merged.put("_floodsafeOnline",true);}catch(Exception ignored){}
                    JSONObject old=newest.get(key);long oldAt=old==null?0L:v877ObservationTime(old);
                    if(old==null||at>oldAt)newest.put(key,merged);
                }
            }catch(Exception ignored){}
        }

        String[] dhmUrls={"https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,"https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now};
        for(String url:dhmUrls){
            try{
                String html=getTextV846(url);long pageAt=v846DhmUpdatedAt(html,0L);
                for(DhmLiveV846 d:v846ParseDhmRows(html)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    JSONObject meta=null;if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));if(meta==null)meta=metaByName.get(v846Key(d.name));if(meta==null)continue;
                    String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
                    JSONObject row=v877MergeOfficial(meta,null);
                    row.put("stationIndex",v846StationIndex(meta));row.put("stationName",v846StationName(meta));if(!d.district.isEmpty())row.put("districtName",d.district);
                    row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                    if(pageAt>0)row.put("_measurementTime",java.time.Instant.ofEpochMilli(pageAt).toString());
                    row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");
                    String rn=v877RiverName(meta);if(!rn.isEmpty())row.put("_floodsafeRiverName",rn);String wt=v877WaterbodyType(meta);if(!wt.isEmpty())row.put("_floodsafeWaterbodyType",wt);
                    JSONObject old=newest.get(key);long oldAt=old==null?0L:v877ObservationTime(old),newAt=v877ObservationTime(row);
                    if(old==null||(newAt>0L&&(oldAt<=0L||newAt>oldAt)))newest.put(key,row);
                }
            }catch(Exception ignored){}
        }

        v878WriteLastGoodObservations(newest.values());

        List<RiverStation> out=new ArrayList<>();
        java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextRows=new java.util.concurrent.ConcurrentHashMap<>();
        int freshCount=0,latestCount=0;
        for(int i=0;i<catalog.length();i++){
            JSONObject meta=catalog.optJSONObject(i);if(meta==null)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));JSONObject row=newest.get(key);
            boolean hasVerified=row!=null;
            if(row==null){row=metadataMatch.get(key);if(row==null)row=meta;row=v878MetadataOnly(row);}
            if(!hasVerified){try{row.put("_floodsafeCatalogOnly",true);row.put("_floodsafeOnline",false);row.put("_floodsafeObservationMatched",false);if(!row.has("_floodsafeSource"))row.put("_floodsafeSource",liveLooksComplete?"BIPAD river-stations inventory":"Bundled last-known official station inventory");}catch(Exception ignored){}}
            try{String rn=v877RiverName(row);if(rn.isEmpty())rn=v877RiverName(meta);if(!rn.isEmpty())row.put("_floodsafeRiverName",rn);String wt=v877WaterbodyType(row);if(wt.isEmpty())wt=v877WaterbodyType(meta);if(!wt.isEmpty())row.put("_floodsafeWaterbodyType",wt);}catch(Exception ignored){}
            RiverStation s=parseStation(row,now);if(s==null)continue;
            out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;
            try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        }
        if(out.isEmpty())throw new IllegalStateException("Station inventory parsed to zero rows");
        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,catalog.length()-latestCount);
        v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0878_RESILIENT_STATION_REFRESH
'''
a=replace_method(a,'loadTrustedRiverStationsV862',loader)

# A reading is current/online only when a trusted source match explicitly set the flag.
old='boolean has=Double.isFinite(level)&&at>0L;boolean matched=r.optBoolean("_floodsafeObservationMatched",has);boolean online=matched&&has;'
new='boolean has=Double.isFinite(level)&&at>0L;boolean matched=r.optBoolean("_floodsafeObservationMatched",false);boolean online=matched&&has; // V0878_EXPLICIT_MATCH_REQUIRED'
if old not in a:raise SystemExit('v0878 parseStation match anchor missing')
a=a.replace(old,new,1)

# Do not reuse the v0.8.77 package version for a materially different government field-test APK.
g=re.sub(r'versionCode\s+97\b','versionCode 98',g,count=1)
g=g.replace("versionName '0.8.77'","versionName '0.8.78'",1)
if 'versionCode 98' not in g or "versionName '0.8.78'" not in g:raise SystemExit('v0878 version bump failed')

need=['V0878_STATION_CATALOG_FALLBACK','V0878_STATION_CATALOG_NEVER_EMPTY','V0878_LAST_GOOD_OBSERVATION_CACHE','V0878_LAST_GOOD_OBSERVATION_PERSIST','V0878_NO_READING_FLICKER','V0878_METADATA_NEVER_LIVE','V0878_EXPLICIT_MATCH_REQUIRED','V0878_RESILIENT_STATION_REFRESH']
for x in need:
    if x not in a:raise SystemExit('missing '+x)

a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.78 station resilience patch applied')
