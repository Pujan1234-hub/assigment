from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
l_path=src/'FloodLiveGaugeMonitor.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
l=l_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.77 CLEAN: one deterministic patch on top of the known-good v0.8.76 source.
# No runtime patch rewriting and no fabricated readings. The official catalog and the
# observation coverage are separate facts: inventory rows stay visible even when a
# matching fresh reading is unavailable.

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
    if not sp:raise SystemExit('v0877 clean method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

def replace_call_statement(block,anchor,new_stmt):
    p=block.find(anchor)
    if p<0:return block,False
    op=block.find('(',p)
    if op<0:return block,False
    depth=0;quote=None;esc=False;i=op
    while i<len(block):
        ch=block[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='(':depth+=1
            elif ch==')':
                depth-=1
                if depth==0:
                    j=i+1
                    while j<len(block) and block[j].isspace():j+=1
                    if j<len(block) and block[j]==';':j+=1
                    return block[:p]+new_stmt+block[j:],True
        i+=1
    return block,False

# -----------------------------------------------------------------------------
# 1) Stable station identity: station/index/code first; river name is NOT station id.
# -----------------------------------------------------------------------------
a=replace_method(a,'v846StationIndex',r'''    private String v846StationIndex(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"stationIndex","station_index","stationSeriesId","station_series_id","stationId","station_id","gaugeId","gauge_id","stationCode","station_code","code","index","id");
        if(!x.isEmpty())return x;
        Object st=r.opt("station");if((st==null||st==JSONObject.NULL)&&f!=null)st=f.opt("station");
        try{
            if(st instanceof JSONObject){JSONObject s=(JSONObject)st;String y=strDeep(s,s.optJSONObject("fields"),"stationIndex","station_index","stationId","station_id","stationCode","station_code","code","index","id");if(!y.isEmpty())return y;}
            if(st!=null&&st!=JSONObject.NULL){String y=String.valueOf(st).trim();if(!y.isEmpty()&&!"null".equalsIgnoreCase(y))return y;}
        }catch(Exception ignored){}
        return "";
    } // V0877_CLEAN_STABLE_STATION_ID
''')

a=replace_method(a,'v846StationName',r'''    private String v846StationName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"stationName","station_name","stationTitle","station_title","locationName","location_name");
        if(!x.isEmpty())return x;
        Object st=r.opt("station");if((st==null||st==JSONObject.NULL)&&f!=null)st=f.opt("station");
        try{if(st instanceof JSONObject){JSONObject s=(JSONObject)st;String y=strDeep(s,s.optJSONObject("fields"),"stationName","station_name","name","title","location");if(!y.isEmpty())return y;}}catch(Exception ignored){}
        x=strDeep(r,f,"name","title","location");
        return x;
    } // V0877_CLEAN_STATION_NAME_NOT_RIVER
''')

sp=method_span(a,'v846StationName')
if not sp:raise SystemExit('v0877 clean station helper span missing')
helpers=r'''

    private String v877RiverName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"_floodsafeRiverName","riverName","river_name","streamName","stream_name","kholaName","khola_name");
        if(!x.isEmpty())return x;
        Object rv=r.opt("river");if((rv==null||rv==JSONObject.NULL)&&f!=null)rv=f.opt("river");
        try{
            if(rv instanceof JSONObject)return strDeep((JSONObject)rv,((JSONObject)rv).optJSONObject("fields"),"name","title","riverName","river_name");
            if(rv!=null&&rv!=JSONObject.NULL){String y=String.valueOf(rv).trim();if(!y.isEmpty()&&!"null".equalsIgnoreCase(y))return y;}
        }catch(Exception ignored){}
        return "";
    } // V0877_CLEAN_SEPARATE_RIVER_NAME

    private double v877ObservationLevel(JSONObject r){
        if(r==null)return Double.NaN;JSONObject f=r.optJSONObject("fields");
        double v=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");
        if(Double.isFinite(v))return v;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){v=numDeep(o,o.optJSONObject("fields"),"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value");if(Double.isFinite(v))return v;}}
        return Double.NaN;
    } // V0877_CLEAN_NESTED_LEVEL

    private long v877ObservationTime(JSONObject r){
        if(r==null)return 0L;long at=trustedRowTime(r);if(at>0L)return at;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){at=trustedRowTime(o);if(at>0L)return at;}}
        return 0L;
    } // V0877_CLEAN_NESTED_TIME

    private String v877WaterbodyType(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String kind=strDeep(r,f,"_floodsafeWaterbodyType","stationType","station_type","waterbodyType","waterbody_type","type","category");
        String hay=(v846StationName(r)+" "+v877RiverName(r)+" "+kind+" "+strDeep(r,f,"description","stationDescription","station_description")).toLowerCase(Locale.ROOT);
        if(hay.contains("glacial")||hay.contains("glof")||hay.contains("lake outlet")||hay.contains("outlet"))return "lake/outlet";
        if(hay.contains("lake")||hay.contains("reservoir")||hay.contains("dam")||hay.contains(" tal")||hay.startsWith("tal ")||hay.contains("ताल"))return "lake/reservoir";
        return kind;
    } // V0877_CLEAN_LAKE_OUTLET_METADATA

    private JSONObject v877MergeOfficial(JSONObject meta,JSONObject live){
        try{
            JSONObject out=meta==null?new JSONObject():new JSONObject(meta.toString());
            if(live==null)return out;
            java.util.Iterator<String> it=live.keys();
            while(it.hasNext()){String k=it.next();if(!"fields".equals(k))out.put(k,live.opt(k));}
            JSONObject mf=out.optJSONObject("fields"),lf=live.optJSONObject("fields");
            if(lf!=null){JSONObject nf=mf==null?new JSONObject():new JSONObject(mf.toString());java.util.Iterator<String> fi=lf.keys();while(fi.hasNext()){String k=fi.next();nf.put(k,lf.opt(k));}out.put("fields",nf);}
            return out;
        }catch(Exception ignored){return meta==null?new JSONObject():meta;}
    } // V0877_CLEAN_REAL_OBSERVATION_MERGE
'''
a=a[:sp[1]]+helpers+a[sp[1]:]

# -----------------------------------------------------------------------------
# 2) One catalog + official observation union. All catalog rows are retained; readings
# are attached only when station identity matches. Metadata-only rows never become LIVE.
# -----------------------------------------------------------------------------
loader=r'''    private List<RiverStation> loadTrustedRiverStationsV862(long now)throws Exception{
        JSONArray catalog=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=5000&_fs="+now,now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();

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
        } // V0877_CLEAN_BIPAD_OBSERVATION_UNION

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
        } // V0877_CLEAN_DHM_JOIN

        List<RiverStation> out=new ArrayList<>();
        java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextRows=new java.util.concurrent.ConcurrentHashMap<>();
        int freshCount=0,latestCount=0;
        for(int i=0;i<catalog.length();i++){
            JSONObject meta=catalog.optJSONObject(i);if(meta==null)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));JSONObject row=newest.get(key);
            if(row==null)row=metadataMatch.get(key);
            if(row==null)row=v877MergeOfficial(meta,null);
            if(newest.get(key)==null){try{row.put("_floodsafeCatalogOnly",true);row.put("_floodsafeOnline",false);if(!row.has("_floodsafeSource"))row.put("_floodsafeSource","BIPAD river-stations inventory");}catch(Exception ignored){}}
            try{String rn=v877RiverName(row);if(rn.isEmpty())rn=v877RiverName(meta);if(!rn.isEmpty())row.put("_floodsafeRiverName",rn);String wt=v877WaterbodyType(row);if(wt.isEmpty())wt=v877WaterbodyType(meta);if(!wt.isEmpty())row.put("_floodsafeWaterbodyType",wt);}catch(Exception ignored){}
            RiverStation s=parseStation(row,now);if(s==null)continue;
            out.add(s);if(s.fresh)freshCount++;if(Double.isFinite(s.level)&&s.at>0L)latestCount++;
            try{String nm=v846StationName(row);if(!nm.isEmpty())nextRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        }
        v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;v877NoObservationCount=Math.max(0,catalog.length()-latestCount);
        v849LatestCount=latestCount;v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextRows);
        return out;
    } // V0877_CLEAN_FULL_INVENTORY_TRUTH
'''
a=replace_method(a,'loadTrustedRiverStationsV862',loader)

# Parser: only a real level+source-time pair is online/current; stale remains inspectable.
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=v870OfficialCoord(r);double la=c[0],lo=c[1];
        if(!Double.isFinite(la)||!Double.isFinite(lo)||!isNepal(la,lo))return null;
        double level=v877ObservationLevel(r),warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold");
        long at=v877ObservationTime(r);boolean has=Double.isFinite(level)&&at>0L;boolean matched=r.optBoolean("_floodsafeObservationMatched",has);boolean online=matched&&has;
        boolean fresh=online&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L; // V0877_CLEAN_FRESH_ONLY_LIVE
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(has){if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")||(Double.isFinite(danger)&&danger>0&&level>=danger)){stage="danger";rank=0;}else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")||(Double.isFinite(warning)&&warning>0&&level>=warning)){stage="warning";rank=1;}else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}else{stage="normal";rank=3;}}
        String name=v846StationName(r);if(name.isEmpty())name=v877RiverName(r);if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district");district=v848DistrictName(la,lo,district);
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);
    } // V0877_CLEAN_STATION_IDENTITY_PARSE
'''
a=replace_method(a,'parseStation',parse)

field_anchor='    private volatile boolean v862FinalRefreshInFlight=false; private volatile String v862FinalLastFingerprint=""; // V0862_FINAL_REFRESH_FIELDS'
if 'V0877_CLEAN_COVERAGE_FIELDS' not in a:
    if field_anchor not in a:raise SystemExit('v0877 clean coverage field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile int v877FreshObservationCount=0,v877LatestObservationCount=0,v877NoObservationCount=0; // V0877_CLEAN_COVERAGE_FIELDS',1)

# Keep v0.8.76 refresh behavior, but show the catalog truth rather than false OFF counts.
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 आधिकारिक catalog "+v849CatalogCount+" • map मा "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount,
                          "🌊 official catalog "+v849CatalogCount+" • mapped "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • no matched reading "+v877NoObservationCount));
    } // V0877_CLEAN_NO_FALSE_OFFLINE_HEADER
'''
a=replace_method(a,'updateMapHintCounts',hint)

sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0877 clean refreshRiverUi missing')
ui=a[sp[0]:sp[1]]
stmt='feedFresh.setText(t("आधिकारिक catalog "+v849CatalogCount+" • LIVE (≤20m) "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n, "Official catalog "+v849CatalogCount+" • LIVE (≤20m) "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • no matched reading "+v877NoObservationCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n)); // V0877_CLEAN_GAUGE_COVERAGE_UI'
ui,ok=replace_call_statement(ui,'feedFresh.setText',stmt)
if not ok:raise SystemExit('v0877 clean feedFresh statement missing')
a=a[:sp[0]]+ui+a[sp[1]:]

sp=method_span(a,'stationLine')
if sp:
    a=a[:sp[0]]+r'''    private String stationLine(RiverStation s){
        if(s==null)return "";boolean has=Double.isFinite(s.level)&&s.at>0L;
        if(!has)return t("आधिकारिक station • reading match/उपलब्ध छैन","Official station • no matched/available reading");
        String lev=v872ExactNumber(s.level)+" m",age=v850Age(s.at);double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        if(!s.fresh)return t("अन्तिम आधिकारिक reading: ","Latest official reading: ")+lev+" • "+age+dist+" • "+t("LIVE होइन","NOT LIVE");
        return stageName(s.stage)+" • "+lev+" • "+age+dist;
    } // V0877_CLEAN_NO_FALSE_OFFLINE_ROW
'''+a[sp[1]:]

# Full source detail: station and river names stay separate; lake/outlet metadata is shown.
detail=r'''    private String v871GaugeDetailText(RiverStation s){
        if(s==null)return "";JSONObject row=v871SourceRowsByName.get(v846Key(s.name));JSONObject f=row==null?null:row.optJSONObject("fields");
        String idx=v846StationIndex(row),river=v877RiverName(row),basin=strDeep(row,f,"basinName","basin_name","basin","riverBasin","river_basin"),trend=strDeep(row,f,"trend","waterLevelTrend","water_level_trend","levelTrend","level_trend"),desc=strDeep(row,f,"description","stationDescription","station_description"),source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source"),stationType=v877WaterbodyType(row);
        double discharge=numDeep(row,f,"discharge","currentDischarge","current_discharge","flow","streamFlow","stream_flow"),elevation=numDeep(row,f,"elevation","stationElevation","station_elevation","altitude");
        boolean has=Double.isFinite(s.level)&&s.at>0L;StringBuilder b=new StringBuilder();
        if(s.fresh)b.append(v849AvailabilityDot(s)).append(" ").append(t("ताजा आधिकारिक मापन • LIVE/current","Fresh official measurement • LIVE/current"));else if(has)b.append("⚪ ").append(t("अन्तिम आधिकारिक मापन • पुरानो / LIVE होइन","Latest official measurement • STALE / NOT LIVE"));else b.append("⚪ ").append(t("आधिकारिक station catalog मा छ • reading match/measurement छैन","Official station is in the catalog • no matched/available measurement"));
        if(!idx.isEmpty())b.append("\nStation ID: ").append(idx);if(!river.isEmpty())b.append("\n").append(t("नदी/खोला: ","River/stream: ")).append(river);if(!basin.isEmpty())b.append("\nBasin: ").append(basin);if(!stationType.isEmpty())b.append("\n").append(t("प्रकार: ","Type: ")).append(stationType);
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);b.append(String.format(Locale.US,"\n%s%.6f, %.6f",t("स्थान: ","Location: "),s.lat,s.lon));
        if(Double.isFinite(elevation))b.append("\nElevation: ").append(v872ExactNumber(elevation)).append(" m");if(!desc.isEmpty())b.append("\nDescription: ").append(desc);
        if(has){b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(v872ExactNumber(s.level)).append(" m");if(Double.isFinite(discharge))b.append("\n").append(t("Discharge / streamflow: ","Discharge / streamflow: ")).append(v872ExactNumber(discharge));if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(v872ExactNumber(s.warning)).append(" m");if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(v872ExactNumber(s.danger)).append(" m");if(!trend.isEmpty())b.append("\nTrend: ").append(trend);b.append("\n").append(t("Official source time: ","Official source time: ")).append(v848Time(s.at));b.append("\n").append(t("Reading age: ","Reading age: ")).append(v850Age(s.at));if(!s.fresh)b.append("\n").append(t("यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।","This is the latest official reading; because it is older than 20 minutes it is not used for LIVE alerts."));}else b.append("\n\n").append(t("जोडिएका official feeds बाट water-level + source-time pair match भएन। यसलाई OFF भनिएको छैन।","No water-level + source-time pair matched from the connected official feeds. It is not labelled OFF."));
        if(!source.isEmpty())b.append("\n").append(t("Data source: ","Data source: ")).append(source);v869AppendRain(b,s);return b.toString();
    } // V0877_CLEAN_FULL_STATION_RIVER_LAKE_DETAIL
'''
a=replace_method(a,'v871GaugeDetailText',detail)

# Background monitor gets the same extra official river feeds without removing the old set.
if 'V0877_CLEAN_BACKGROUND_RIVER_FEEDS' not in l:
    anchor='private static final String[] HYDRO_ENDPOINTS'
    p=l.find(anchor)
    if p<0:raise SystemExit('v0877 clean HYDRO_ENDPOINTS missing')
    l=l[:p]+'/* V0877_CLEAN_BACKGROUND_RIVER_FEEDS */\n    '+l[p:]
    old='"flood-station/?limit=2000"'
    if old in l:l=l.replace(old,'"river/?limit=5000","river-trimed/?limit=5000",'+old,1)

if 'versionCode 96' in g:g=g.replace('versionCode 96','versionCode 97',1)
elif 'versionCode 97' not in g:raise SystemExit('v0877 clean versionCode anchor missing')
if "versionName '0.8.76'" in g:g=g.replace("versionName '0.8.76'","versionName '0.8.77'",1)
elif "versionName '0.8.77'" not in g:raise SystemExit('v0877 clean versionName anchor missing')

a_path.write_text(a,encoding='utf-8');l_path.write_text(l,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0877_CLEAN_STABLE_STATION_ID','V0877_CLEAN_STATION_NAME_NOT_RIVER','V0877_CLEAN_REAL_OBSERVATION_MERGE','V0877_CLEAN_BIPAD_OBSERVATION_UNION','V0877_CLEAN_FULL_INVENTORY_TRUTH','V0877_CLEAN_FRESH_ONLY_LIVE','V0877_CLEAN_NO_FALSE_OFFLINE_HEADER','V0877_CLEAN_GAUGE_COVERAGE_UI','V0877_CLEAN_FULL_STATION_RIVER_LAKE_DETAIL']:
    if x not in a:raise SystemExit('v0877 clean activity contract missing: '+x)
for x in ['V0877_CLEAN_BACKGROUND_RIVER_FEEDS','river/?limit=5000','river-trimed/?limit=5000']:
    if x not in l:raise SystemExit('v0877 clean monitor contract missing: '+x)
for x in ['versionCode 97',"versionName '0.8.77'"]:
    if x not in g:raise SystemExit('v0877 clean version contract missing: '+x)
print('FloodSafe v0.8.77 CLEAN PASS: stable station identity + full catalog retained + real observation merge + honest LIVE/latest/no-reading + river/lake/outlet detail')
