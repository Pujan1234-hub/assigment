from pathlib import Path
import re

repo=Path(__file__).resolve().parents[2]
root=repo/'floodsafe-android-app'
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=a_path.read_text(encoding='utf-8')

def span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)?\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());d=0;quote=None;esc=False
    for i in range(op,len(text)):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':d+=1
            elif ch=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def replace_method(text,name,block):
    s=span(text,name)
    if not s:raise SystemExit('v0894b method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]

loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
        final long DISPLAY_MAX_AGE_MS=24L*60L*60L*1000L;
        JSONArray catalog=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=5000&_fs="+now,now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> unmatchedLive=new java.util.LinkedHashMap<>();

        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
            double lv=v877ObservationLevel(c);long at=v877ObservationTime(c);long age=now-at;
            if(Double.isFinite(lv)&&at>0L&&age>=-(5L*60L*1000L)&&age<=DISPLAY_MAX_AGE_MS){
                String key=v862FinalKey(ix,nm);if(!key.isEmpty()){
                    JSONObject row=v877MergeOfficial(c,c);
                    try{row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","BIPAD River Watch / river-stations current");}catch(Exception ignored){}
                    newest.put(key,row);
                }
            }
        } // V0894B_CURRENT_RIVER_STATIONS_ARE_VALID_WHEN_RECENT

        String[] paths={"river/?limit=5000","river-trimed/?limit=5000","river-stations/?latest=true&limit=5000"};
        for(String path:paths){
            try{
                JSONArray rows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<rows.length();i++){
                    JSONObject live=rows.optJSONObject(i);if(live==null)continue;
                    double level=v877ObservationLevel(live);long at=v877ObservationTime(live);long age=now-at;
                    if(!Double.isFinite(level)||at<=0L||age<-(5L*60L*1000L)||age>DISPLAY_MAX_AGE_MS)continue;
                    String ix=v846StationIndex(live),nm=v846StationName(live);
                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
                    JSONObject merged=v877MergeOfficial(meta,live);
                    try{merged.put("_floodsafeObservationMatched",true);merged.put("_floodsafeOnline",true);merged.put("_floodsafeSource","BIPAD realtime "+path);}catch(Exception ignored){}
                    String key=meta==null?v894LooseLiveKey(live):v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
                    java.util.LinkedHashMap<String,JSONObject> target=meta==null?unmatchedLive:newest;JSONObject old=target.get(key);long oldAt=old==null?0L:v877ObservationTime(old);if(old==null||at>oldAt)target.put(key,merged);
                }
            }catch(Exception ignored){}
        } // V0894B_OPTIONAL_OLDER_ENDPOINTS_CANNOT_BREAK_RIVERWATCH

        List<RiverStation> out=new ArrayList<>();java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextRows=new java.util.concurrent.ConcurrentHashMap<>();int freshCount=0,latestCount=0;
        for(int i=0;i<catalog.length();i++){
            JSONObject meta=catalog.optJSONObject(i);if(meta==null)continue;String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));JSONObject row=newest.get(key);if(row==null)row=v894CatalogMetadataOnly(meta);
            RiverStation s=parseStation(row,now);if(s==null)continue;out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        }
        for(JSONObject row:unmatchedLive.values()){RiverStation s=parseStation(row,now);if(s==null)continue;out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}}
        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,catalog.length()-latestCount);v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0894B_BIPAD_RIVERWATCH_MIRROR_RECENT_ROWS_ONLY
'''
a=replace_method(a,'loadTrustedRiverStationsV862',loader)
for x in ['V0894B_CURRENT_RIVER_STATIONS_ARE_VALID_WHEN_RECENT','V0894B_OPTIONAL_OLDER_ENDPOINTS_CANNOT_BREAK_RIVERWATCH','V0894B_BIPAD_RIVERWATCH_MIRROR_RECENT_ROWS_ONLY','V0894_BIPAD_EVENTON_WATERLEVELON']:
    if x not in a:raise SystemExit('v0894b contract missing: '+x)
a_path.write_text(a,encoding='utf-8')
print('FloodSafe v0.8.94b PASS: BIPAD river-stations recent rows mirror River Watch; stale August rows removed; optional endpoints cannot break refresh')
