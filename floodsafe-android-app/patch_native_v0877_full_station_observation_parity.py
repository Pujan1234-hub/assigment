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

# v0.8.77 repairs source parity without fabricating readings.
# The 284 official BIPAD river-station inventory remains the map inventory, while
# live/latest observations are joined from the documented river + river-trimed feeds
# (plus the already used hydrology feeds) by stable station id first, then station name.
# A station is never called OFF merely because a reading is stale or failed to join.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
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

# -----------------------------------------------------------------------------
# 1) Stable station identity. Older code preferred river_name before station_name,
# causing several gauges on the same river to collapse into one key.
# -----------------------------------------------------------------------------
sp=method_span(a,'v846StationIndex')
if not sp:raise SystemExit('v0877 v846StationIndex missing')
idx=r'''    private String v846StationIndex(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"stationIndex","station_index","stationSeriesId","station_series_id","stationId","station_id","gauge_id","gaugeId","code","stationCode","station_code");
        if(!x.isEmpty())return x;
        Object st=r.opt("station");if((st==null||st==JSONObject.NULL)&&f!=null)st=f.opt("station");
        try{
            if(st instanceof JSONObject){JSONObject s=(JSONObject)st;String y=strDeep(s,"index","id","stationIndex","station_index","stationId","station_id","code");if(!y.isEmpty())return y;}
            else if(st!=null&&st!=JSONObject.NULL){String y=String.valueOf(st).trim();if(!y.isEmpty()&&!"null".equalsIgnoreCase(y))return y;}
        }catch(Exception ignored){}
        return "";
    } // V0877_STABLE_STATION_ID
'''
a=a[:sp[0]]+idx+a[sp[1]:]

sp=method_span(a,'v846StationName')
if not sp:raise SystemExit('v0877 v846StationName missing')
name=r'''    private String v846StationName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"station_name","stationName","stationTitle","station_title","locationName","location_name");
        if(!x.isEmpty())return x;
        Object st=r.opt("station");if((st==null||st==JSONObject.NULL)&&f!=null)st=f.opt("station");
        try{if(st instanceof JSONObject){JSONObject s=(JSONObject)st;String y=strDeep(s,"station_name","stationName","name","title","location");if(!y.isEmpty())return y;}}catch(Exception ignored){}
        x=strDeep(r,f,"name","title","location");if(!x.isEmpty())return x;
        return strDeep(r,f,"river_name","riverName","river");
    } // V0877_STATION_NAME_BEFORE_RIVER
'''
a=a[:sp[0]]+name+a[sp[1]:]

# Extra helpers used only by v0.8.77 loader/detail.
helper_anchor='    private String v846StationName(JSONObject r){'
sp=method_span(a,'v846StationName')
if not sp:raise SystemExit('v0877 station name helper span missing after replace')
helpers=r'''
    private String v877RiverName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String x=strDeep(r,f,"river_name","riverName","river","stream_name","streamName","khola_name","kholaName");
        if(!x.isEmpty())return x;
        Object rv=r.opt("river");if((rv==null||rv==JSONObject.NULL)&&f!=null)rv=f.opt("river");
        try{if(rv instanceof JSONObject)return strDeep((JSONObject)rv,"name","title","river_name","riverName");}catch(Exception ignored){}
        return "";
    } // V0877_SEPARATE_RIVER_NAME

    private static double v877ObservationLevel(JSONObject r){
        if(r==null)return Double.NaN;JSONObject f=r.optJSONObject("fields");
        double v=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");
        if(Double.isFinite(v))return v;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){JSONObject of=o.optJSONObject("fields");v=numDeep(o,of,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");if(Double.isFinite(v))return v;}}
        return Double.NaN;
    } // V0877_NESTED_LEVEL_READER

    private String v877WaterbodyType(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        String kind=strDeep(r,f,"_floodsafeWaterbodyType","stationType","station_type","waterbodyType","waterbody_type","type","category");
        String hay=(v846StationName(r)+" "+v877RiverName(r)+" "+kind+" "+strDeep(r,f,"description","stationDescription","station_description")).toLowerCase(Locale.ROOT);
        if(hay.contains("glacial")||hay.contains("glof")||hay.contains("lake outlet")||hay.contains("outlet"))return "lake/outlet";
        if(hay.contains("lake")||hay.contains("reservoir")||hay.contains("dam")||hay.contains(" tal")||hay.startsWith("tal ")||hay.contains("ताल"))return "lake/reservoir";
        return kind;
    } // V0877_LAKE_OUTLET_METADATA

'''
a=a[:sp[1]]+helpers+a[sp[1]:]

# -----------------------------------------------------------------------------
# 2) Final official loader. Keep catalog inventory separate from observation coverage.
# -----------------------------------------------------------------------------
sp=method_span(a,'loadTrustedRiverStationsV862')
if not sp:raise SystemExit('v0877 trusted loader missing')
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
        java.util.LinkedHashMap<String,JSONObject> supplement=new java.util.LinkedHashMap<>();
        String[] paths={
            "river/?limit=5000",
            "river-trimed/?limit=5000",
            "river-stations/?latest=true&limit=5000",
            "flood-station/?limit=5000",
            "streamflow/?limit=5000",
            "station-location/?limit=5000"
        };
        for(String path:paths){
            try{
                JSONArray rows=trustedPages(BIPAD+path+"&_fs="+now,now);
                for(int i=0;i<rows.length();i++){
                    JSONObject live=rows.optJSONObject(i);if(live==null)continue;
                    String ix=v846StationIndex(live),nm=v846StationName(live);
                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;
                    if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
                    if(meta==null)continue; // keep the official 284 river-station inventory canonical
                    String mix=v846StationIndex(meta),mn=v846StationName(meta),key=v862FinalKey(mix,mn);if(key.isEmpty())continue;
                    JSONObject merged=v862FinalMetaOnly(meta,live);
                    try{
                        merged.put("_floodsafeSource","BIPAD "+path);
                        String rn=v877RiverName(live);if(rn.isEmpty())rn=v877RiverName(meta);if(!rn.isEmpty())merged.put("_floodsafeRiverName",rn);
                        String wt=v877WaterbodyType(live);if(wt.isEmpty())wt=v877WaterbodyType(meta);if(!wt.isEmpty())merged.put("_floodsafeWaterbodyType",wt);
                    }catch(Exception ignored){}
                    supplement.put(key,merged);
                    double level=v877ObservationLevel(live);long at=trustedRowTime(live);
                    if(!Double.isFinite(level)||at<=0L)continue;
                    try{merged.put("_floodsafeOnline",true);merged.put("_floodsafeObservationMatched",true);}catch(Exception ignored){}
                    JSONObject old=newest.get(key);long oldAt=old==null?0L:trustedRowTime(old);
                    if(old==null||at>oldAt)newest.put(key,merged);
                }
            }catch(Exception ignored){}
        } // V0877_BIPAD_RIVER_AND_TRIMED_UNION

        // DHM direct realtime is retained as a second official source. It is joined to the
        // same catalog identity; it never creates a synthetic station.
        String[] dhmUrls={"https://dhm.gov.np/hydrology/realtime-stream?_fs="+now,"https://www.dhm.gov.np/hydrology/realtime-stream?_fs="+now};
        for(String url:dhmUrls){
            try{
                String html=getTextV846(url);long pageAt=v846DhmUpdatedAt(html,0L);
                for(DhmLiveV846 d:v846ParseDhmRows(html)){
                    if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                    JSONObject meta=null;if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));if(meta==null)meta=metaByName.get(v846Key(d.name));if(meta==null)continue;
                    String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));if(key.isEmpty())continue;
                    JSONObject row=v862FinalMetaOnly(meta,null);
                    row.put("stationIndex",v846StationIndex(meta));row.put("stationName",v846StationName(meta));if(!d.district.isEmpty())row.put("districtName",d.district);
                    row.put("waterLevel",d.level);if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                    if(pageAt>0)row.put("_measurementTime",java.time.Instant.ofEpochMilli(pageAt).toString());
                    row.put("_floodsafeOnline",true);row.put("_floodsafeObservationMatched",true);row.put("_floodsafeSource","DHM realtime-stream");
                    String rn=v877RiverName(meta);if(!rn.isEmpty())row.put("_floodsafeRiverName",rn);
                    String wt=v877WaterbodyType(meta);if(!wt.isEmpty())row.put("_floodsafeWaterbodyType",wt);
                    JSONObject old=newest.get(key);long oldAt=old==null?0L:trustedRowTime(old),newAt=trustedRowTime(row);
                    if(old==null||(newAt>0&&(oldAt<=0||newAt>oldAt)))newest.put(key,row);
                }
            }catch(Exception ignored){}
        } // V0877_DHM_STABLE_ID_JOIN

        List<RiverStation> out=new ArrayList<>();
        java.util.concurrent.ConcurrentHashMap<String,JSONObject> nextSourceRows=new java.util.concurrent.ConcurrentHashMap<>();
        int latest=0;
        for(int i=0;i<catalog.length();i++){
            JSONObject meta=catalog.optJSONObject(i);if(meta==null)continue;
            String key=v862FinalKey(v846StationIndex(meta),v846StationName(meta));
            JSONObject row=newest.get(key);
            if(row==null)row=supplement.get(key);
            if(row==null){
                row=new JSONObject(meta.toString());
                try{row.put("_floodsafeCatalogOnly",true);row.put("_floodsafeOnline",false);row.put("_floodsafeSource","BIPAD river-stations inventory");String rn=v877RiverName(meta);if(!rn.isEmpty())row.put("_floodsafeRiverName",rn);String wt=v877WaterbodyType(meta);if(!wt.isEmpty())row.put("_floodsafeWaterbodyType",wt);}catch(Exception ignored){}
            }else if(newest.get(key)==null){
                try{row.put("_floodsafeCatalogOnly",true);row.put("_floodsafeOnline",false);}catch(Exception ignored){}
            }
            RiverStation s=parseStation(row,now);if(s==null)continue;
            out.add(s);if(Double.isFinite(s.level)&&s.at>0L)latest++;
            try{String nm=v846StationName(row);if(!nm.isEmpty())nextSourceRows.put(v846Key(nm),new JSONObject(row.toString()));}catch(Exception ignored){}
        }
        v849LatestCount=latest;
        v871SourceRowsByName.clear();v871SourceRowsByName.putAll(nextSourceRows); // V0877_SOURCE_CACHE_TRUE_STATION_NAME
        return out;
    } // V0877_FULL_284_INVENTORY_MAX_OFFICIAL_OBSERVATIONS
'''
a=a[:sp[0]]+loader+a[sp[1]:]

# -----------------------------------------------------------------------------
# 3) Parser uses station identity, not river identity. Freshness remains the v0.8.76
# safety rule, while latest-but-old rows remain inspectable.
# -----------------------------------------------------------------------------
sp=method_span(a,'parseStation')
if not sp:raise SystemExit('v0877 parseStation missing')
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=v870OfficialCoord(r);double la=c[0],lo=c[1];
        if(!Double.isFinite(la)||!Double.isFinite(lo)||!isNepal(la,lo))return null;
        double level=v877ObservationLevel(r),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold");
        long at=trustedRowTime(r);
        boolean hasObservation=Double.isFinite(level)&&at>0L;
        boolean matched=r.optBoolean("_floodsafeObservationMatched",hasObservation);
        boolean online=matched;
        boolean fresh=matched&&hasObservation&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L; // V0877_FRESH_ONLY_LIVE
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(hasObservation){
            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")||(Double.isFinite(danger)&&danger>0&&level>=danger)){stage="danger";rank=0;}
            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")||(Double.isFinite(warning)&&warning>0&&level>=warning)){stage="warning";rank=1;}
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else{stage="normal";rank=3;}
        }
        String name=v846StationName(r);if(name.isEmpty())name=v877RiverName(r);if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district");district=v848DistrictName(la,lo,district);
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);
    } // V0877_STATION_IDENTITY_PARSE
'''
a=a[:sp[0]]+parse+a[sp[1]:]

# -----------------------------------------------------------------------------
# 4) Honest counts/status. 284 = inventory; LIVE = <=20m; latest = any official matched
# reading. Missing/old data is not called OFF.
# -----------------------------------------------------------------------------
field_anchor='    private volatile boolean v862FinalRefreshInFlight=false; private volatile String v862FinalLastFingerprint=""; // V0862_FINAL_REFRESH_FIELDS'
if 'V0877_COVERAGE_FIELDS' not in a:
    if field_anchor not in a:raise SystemExit('v0877 coverage field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile int v877FreshObservationCount=0,v877LatestObservationCount=0,v877NoObservationCount=0; // V0877_COVERAGE_FIELDS',1)

sp=method_span(a,'refreshRivers')
if not sp:raise SystemExit('v0877 refreshRivers missing')
refresh=r'''    private void refreshRivers(){
        if(v862FinalRefreshInFlight)return;v862FinalRefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> out=loadTrustedRiverStationsV862(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.fresh?0:(Double.isFinite(s.level)&&s.at>0L?1:2)).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                int fresh=0,latest=0;for(RiverStation s:out){if(s.fresh)fresh++;if(Double.isFinite(s.level)&&s.at>0L)latest++;}
                v877FreshObservationCount=fresh;v877LatestObservationCount=latest;v877NoObservationCount=Math.max(0,out.size()-latest);
                v849CatalogCount=out.size();v849LatestCount=latest;
                String fp=v862FinalFingerprint(out)+"|"+fresh+"|"+latest+"|"+out.size();boolean changed=!fp.equals(v862FinalLastFingerprint);
                if(!out.isEmpty()&&changed){synchronized(stations){stations.clear();stations.addAll(out);}v862FinalLastFingerprint=fp;}
                runOnUiThread(()->{v862FinalRefreshInFlight=false;if(changed&&!out.isEmpty())refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v862FinalRefreshInFlight=false);}
        });
    } // V0877_INVENTORY_AND_OBSERVATION_COUNTS
'''
a=a[:sp[0]]+refresh+a[sp[1]:]

sp=method_span(a,'updateMapHintCounts')
if not sp:raise SystemExit('v0877 updateMapHintCounts missing')
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 आधिकारिक नदी gauge "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount,
                          "🌊 official river gauges "+mapRiverTotal+" • LIVE "+v877FreshObservationCount+" • latest reading "+v877LatestObservationCount+" • no matched reading "+v877NoObservationCount));
    } // V0877_HEADER_NO_FALSE_OFFLINE
'''
a=a[:sp[0]]+hint+a[sp[1]:]

# refreshRiverUi still owns list/map painting; make its headline/count semantics explicit.
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0877 refreshRiverUi missing')
ui=a[sp[0]:sp[1]]
# Preserve risk/status counters as fresh-only, but headline says exactly what each number means.
ui=re.sub(r'feedFresh\.setText\(t\(.*?\);\s*// V0869_GAUGE_COUNT_UI',
'''feedFresh.setText(t("आधिकारिक नदी gauge "+sourceTotal+" • LIVE (≤20m) "+current+" • latest reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n,\n                "Official river gauges "+sourceTotal+" • LIVE (≤20m) "+current+" • latest reading "+v877LatestObservationCount+" • no matched reading "+v877NoObservationCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n)); // V0877_GAUGE_COVERAGE_UI''',ui,count=1,flags=re.S)
if 'V0877_GAUGE_COVERAGE_UI' not in ui:raise SystemExit('v0877 feedFresh headline anchor missing')
a=a[:sp[0]]+ui+a[sp[1]:]

# Compact row wording: unavailable != offline.
sp=method_span(a,'stationLine')
if sp:
    line=r'''    private String stationLine(RiverStation s){
        if(s==null)return "";boolean has=Double.isFinite(s.level)&&s.at>0L;
        if(!has)return t("आधिकारिक station • reading match भएन/उपलब्ध छैन","Official station • no matched/available reading");
        String lev=v872ExactNumber(s.level)+" m",age=v850Age(s.at);double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        if(!s.fresh)return t("अन्तिम आधिकारिक reading: ","Latest official reading: ")+lev+" • "+age+dist+" • "+t("LIVE होइन","NOT LIVE");
        return stageName(s.stage)+" • "+lev+" • "+age+dist;
    } // V0877_NO_FALSE_OFFLINE_ROW
'''
    a=a[:sp[0]]+line+a[sp[1]:]

# -----------------------------------------------------------------------------
# 5) Detail exposes station name + river/khola separately and lake/outlet metadata.
# -----------------------------------------------------------------------------
sp=method_span(a,'v871GaugeDetailText')
if not sp:raise SystemExit('v0877 gauge detail missing')
detail=r'''    private String v871GaugeDetailText(RiverStation s){
        if(s==null)return "";JSONObject row=v871SourceRowsByName.get(v846Key(s.name));JSONObject f=row==null?null:row.optJSONObject("fields");
        String idx=v846StationIndex(row),river=v877RiverName(row),basin=strDeep(row,f,"basinName","basin_name","basin","riverBasin","river_basin");
        String trend=strDeep(row,f,"trend","waterLevelTrend","water_level_trend","levelTrend","level_trend");
        String desc=strDeep(row,f,"description","stationDescription","station_description");
        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");
        String stationType=v877WaterbodyType(row);
        double discharge=numDeep(row,f,"discharge","currentDischarge","current_discharge","flow","streamFlow","stream_flow");
        double elevation=numDeep(row,f,"elevation","stationElevation","station_elevation","altitude");
        boolean has=Double.isFinite(s.level)&&s.at>0L;
        StringBuilder b=new StringBuilder();
        if(s.fresh)b.append(v849AvailabilityDot(s)).append(" ").append(t("ताजा आधिकारिक मापन • LIVE/current","Fresh official measurement • LIVE/current"));
        else if(has)b.append("⚪ ").append(t("अन्तिम आधिकारिक मापन उपलब्ध • पुरानो / LIVE होइन","Latest official measurement available • STALE / NOT LIVE"));
        else b.append("⚪ ").append(t("आधिकारिक station catalog मा छ • reading match/measurement उपलब्ध छैन","Official station is in the inventory • no matched/available measurement"));
        if(!idx.isEmpty())b.append("\n").append(t("Station ID: ","Station ID: ")).append(idx);
        if(!river.isEmpty())b.append("\n").append(t("नदी/खोला: ","River/stream: ")).append(river);
        if(!basin.isEmpty())b.append("\n").append(t("Basin: ","Basin: ")).append(basin);
        if(!stationType.isEmpty())b.append("\n").append(t("प्रकार: ","Type: ")).append(stationType);
        b.append("\n").append(t("जिल्ला: ","District: ")).append(s.district==null||s.district.isEmpty()?"—":s.district);
        b.append(String.format(Locale.US,"\n%s%.6f, %.6f",t("स्थान: ","Location: "),s.lat,s.lon));
        if(Double.isFinite(elevation))b.append("\n").append(t("Elevation: ","Elevation: ")).append(v872ExactNumber(elevation)).append(" m");
        if(!desc.isEmpty())b.append("\n").append(t("Description: ","Description: ")).append(desc);
        if(has){
            b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(v872ExactNumber(s.level)).append(" m");
            if(Double.isFinite(discharge))b.append("\n").append(t("Discharge / streamflow: ","Discharge / streamflow: ")).append(v872ExactNumber(discharge));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(v872ExactNumber(s.warning)).append(" m");
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(v872ExactNumber(s.danger)).append(" m");
            if(!trend.isEmpty())b.append("\n").append(t("Trend: ","Trend: ")).append(trend);
            b.append("\n").append(t("Official source time: ","Official source time: ")).append(v848Time(s.at));
            b.append("\n").append(t("Reading age: ","Reading age: ")).append(v850Age(s.at));
            if(!s.fresh)b.append("\n").append(t("यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।","This is the latest official reading; because it is older than 20 minutes it is not used for LIVE alerts."));
        }else b.append("\n\n").append(t("यस station का लागि अहिले जोडिएका official feeds बाट water-level + source-time pair match भएन। यसलाई OFF भनिएको छैन।","No water-level + source-time pair matched from the connected official feeds for this station. It is not labelled OFF."));
        if(!source.isEmpty())b.append("\n").append(t("Data source: ","Data source: ")).append(source);
        v869AppendRain(b,s);
        b.append("\n\n").append(t("↻ BIPAD river, river-trimed, river-stations, flood/streamflow/location र DHM source recheck हुन्छन्।","↻ BIPAD river, river-trimed, river-stations, flood/streamflow/location and DHM sources are rechecked."));
        return b.toString();
    } // V0877_FULL_STATION_RIVER_LAKE_DETAIL
'''
a=a[:sp[0]]+detail+a[sp[1]:]

# -----------------------------------------------------------------------------
# 6) Background monitor uses the same strongest documented BIPAD river observation feeds.
# -----------------------------------------------------------------------------
if 'V0877_BACKGROUND_RIVER_FEEDS' not in l:
    old='"flood-station/?limit=2000"'
    if old not in l:raise SystemExit('v0877 background hydro endpoint anchor missing')
    l=l.replace(old,'"river/?limit=5000","river-trimed/?limit=5000",'+old,1)
    l=l.replace('private static final String[] HYDRO_ENDPOINTS', '/* V0877_BACKGROUND_RIVER_FEEDS */\n    private static final String[] HYDRO_ENDPOINTS',1)

# Release identity.
if 'versionCode 96' in g:g=g.replace('versionCode 96','versionCode 97',1)
elif 'versionCode 97' not in g:raise SystemExit('v0877 versionCode anchor missing')
if "versionName '0.8.76'" in g:g=g.replace("versionName '0.8.76'","versionName '0.8.77'",1)
elif "versionName '0.8.77'" not in g:raise SystemExit('v0877 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');l_path.write_text(l,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0877_STABLE_STATION_ID','V0877_STATION_NAME_BEFORE_RIVER','V0877_SEPARATE_RIVER_NAME','V0877_BIPAD_RIVER_AND_TRIMED_UNION','river/?limit=5000','river-trimed/?limit=5000','V0877_FULL_284_INVENTORY_MAX_OFFICIAL_OBSERVATIONS','V0877_STATION_IDENTITY_PARSE','V0877_HEADER_NO_FALSE_OFFLINE','V0877_GAUGE_COVERAGE_UI','V0877_NO_FALSE_OFFLINE_ROW','V0877_FULL_STATION_RIVER_LAKE_DETAIL','V0877_LAKE_OUTLET_METADATA']:
    if x not in a:raise SystemExit('v0877 activity contract missing: '+x)
for x in ['V0877_BACKGROUND_RIVER_FEEDS','river/?limit=5000','river-trimed/?limit=5000']:
    if x not in l:raise SystemExit('v0877 monitor contract missing: '+x)
for x in ['versionCode 97',"versionName '0.8.77'"]:
    if x not in g:raise SystemExit('v0877 version contract missing: '+x)
print('FloodSafe v0.8.77 PASS: 284-station inventory + river/river-trimed observation union + stable station-id join + honest LIVE/latest/no-reading status + river/lake/outlet detail')
