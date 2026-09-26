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

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
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
    if not sp:raise SystemExit('v0897 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# v0.8.96 regression root cause: it ignored the official GeoJSON point field and
# therefore parsed the 284 catalog as zero visible RiverStation rows. Restore the
# proven official coordinate extractor. CURRENT now means present in the current
# BIPAD/DHM response, not a client-side 20-minute age guess.
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=v870OfficialCoord(r);double la=c[0],lo=c[1];
        if(!(Double.isFinite(la)&&Double.isFinite(lo)&&la>=26.2d&&la<=30.5d&&lo>=80.0d&&lo<=88.35d))return null;
        double level=v877ObservationLevel(r);
        double warning=numDeep(r,f,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel");
        double danger=numDeep(r,f,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=v877ObservationTime(r);
        boolean has=Double.isFinite(level);
        boolean matched=r.optBoolean("_floodsafeObservationMatched",false);
        boolean current=r.optBoolean("_floodsafeCurrentResponse",false)&&has;
        boolean online=(matched&&has)||current;
        boolean fresh=current; // V0897_BIPAD_CURRENT_NOT_LOCAL_20M
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(has){
            boolean belowWarning=raw.contains("BELOW WARNING")||raw.contains("BELOWWARNING");
            boolean officialNormal=belowWarning||raw.contains("NORMAL")||raw.contains("GREEN")||raw.contains("SAFE");
            boolean officialDanger=(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED");
            boolean officialWarning=(raw.contains("WARNING")&&!belowWarning)||raw.contains("ORANGE")||raw.contains("BELOW DANGER");
            boolean officialAlert=raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW");
            if(officialNormal){stage="normal";rank=3;}
            else if(officialDanger){stage="danger";rank=0;}
            else if(officialWarning){stage="warning";rank=1;}
            else if(officialAlert){stage="alert";rank=2;}
            else{
                boolean sane=Double.isFinite(warning)&&Double.isFinite(danger)&&warning>0d&&danger>warning;
                if(sane&&level>=danger){stage="danger";rank=0;}
                else if(sane&&level>=warning){stage="warning";rank=1;}
                else {stage="normal";rank=3;}
            }
        }
        String name=v846StationName(r);if(name.isEmpty())name=v877RiverName(r);if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district");
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw); // V0897_KEEP_ALL_284_POINT_STATIONS
    } // V0897_OFFICIAL_POINT_AND_CURRENT_TRUTH
'''
a=replace_method(a,'parseStation',parse)

# BIPAD uses waterLevelOn/water_level_on on river objects. Accept these explicitly,
# together with the prior trusted timestamp parser, so latest readings don't collapse to 0.
time=r'''    private long v877ObservationTime(JSONObject r){
        if(r==null)return 0L;long at=trustedRowTime(r);if(at>0L)return at;
        JSONObject f=r.optJSONObject("fields");String[] keys={"_measurementTime","_lastWaterLevelOn","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","updatedOn","updated_at"};
        for(String k:keys){Object v=r.opt(k);if((v==null||v==JSONObject.NULL)&&f!=null)v=f.opt(k);at=v897Time(v);if(at>0L)return at;}
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){at=trustedRowTime(o);if(at>0L)return at;JSONObject of=o.optJSONObject("fields");for(String q:keys){Object v=o.opt(q);if((v==null||v==JSONObject.NULL)&&of!=null)v=of.opt(q);at=v897Time(v);if(at>0L)return at;}}}
        return 0L;
    } // V0897_BIPAD_WATER_LEVEL_ON_TIME

    private long v897Time(Object v){
        if(v==null||v==JSONObject.NULL)return 0L;
        if(v instanceof Number){long n=((Number)v).longValue();return n>0L&&n<100000000000L?n*1000L:n;}
        String s=String.valueOf(v).trim();if(s.isEmpty()||"null".equalsIgnoreCase(s))return 0L;
        try{long n=Long.parseLong(s);return n>0L&&n<100000000000L?n*1000L:n;}catch(Exception ignored){}
        try{return java.time.Instant.parse(s).toEpochMilli();}catch(Exception ignored){}
        try{return java.time.OffsetDateTime.parse(s).toInstant().toEpochMilli();}catch(Exception ignored){}
        try{return java.time.LocalDateTime.parse(s.replace(' ','T')).atZone(java.time.ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();}catch(Exception ignored){}
        return 0L;
    } // V0897_BIPAD_TIME_PARSER
'''
a=replace_method(a,'v877ObservationTime',time)

# Mark rows that came from this exact official fetch as CURRENT. Cached rows remain
# latest/history only and can never inflate the BIPAD-current number.
a=a.replace('try{merged.put("_floodsafeObservationMatched",true);merged.put("_floodsafeOnline",true);}catch(Exception ignored){}',
            'try{merged.put("_floodsafeObservationMatched",true);merged.put("_floodsafeOnline",true);merged.put("_floodsafeCurrentResponse",true);}catch(Exception ignored){} // V0897_MARK_CURRENT_BIPAD_ROW')
a=a.replace('row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeSource","DHM realtime-stream");',
            'row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeCurrentResponse",true);row.put("_floodsafeSource","DHM realtime-stream"); // V0897_MARK_CURRENT_DHM_ROW')
# Any row coming from cache/process carry-over must explicitly lose CURRENT.
a=a.replace('row.put("_floodsafeSource","Last verified official observation cache");',
            'row.put("_floodsafeCurrentResponse",false);row.put("_floodsafeSource","Last verified official observation cache"); // V0897_CACHE_NOT_CURRENT')

# Mirror the primary BIPAD river feed count instead of deriving CURRENT from local age.
# trustedPages already follows pagination, so rows.length() is the source list we just fetched.
needle='JSONArray rows=trustedPages(BIPAD+path+"&_fs="+now,now);'
if needle not in a: raise SystemExit('v0897 BIPAD path loop anchor missing')
a=a.replace(needle,needle+'\n                if(path.startsWith("river/?"))v897BipadCurrentFeedCount=rows.length(); // V0897_MIRROR_BIPAD_CURRENT_COUNT',1)
field='    private volatile int v877FreshObservationCount=0,v877LatestObservationCount=0,v877NoObservationCount=0; // V0877_CLEAN_COVERAGE_FIELDS'
if field not in a: raise SystemExit('v0897 coverage field anchor missing')
a=a.replace(field,field+'\n    private volatile int v897BipadCurrentFeedCount=-1; // V0897_PRIMARY_BIPAD_CURRENT_COUNT',1)
a=a.replace('v877FreshObservationCount=freshCount;v877LatestObservationCount=latestCount;',
            'v877FreshObservationCount=v897BipadCurrentFeedCount>=0?v897BipadCurrentFeedCount:freshCount;v877LatestObservationCount=latestCount; // V0897_SOURCE_COUNT_NOT_20M',1)

# Remove the old <=20m wording from the active UI. The number is now direct current-feed count.
a=a.replace('LIVE (≤20m) ', 'BIPAD CURRENT ')
a=a.replace('LIVE (<=20m) ', 'BIPAD CURRENT ')
a=a.replace('LIVE '+ '"+v877FreshObservationCount', 'BIPAD CURRENT '+ '"+v877FreshObservationCount') if False else a

# Source monitor: direct BIPAD river endpoint, no proxy, and a sane 60-second observer.
# BIPAD itself normally advances readings on its own cadence; polling once a minute catches
# the next source change promptly without the old one-request-per-second hammering.
l=re.sub(r'private static final String RIVER_ENDPOINT="[^"]+";', 'private static final String RIVER_ENDPOINT=BIPAD+"river/?limit=5000"; // V0897_DIRECT_BIPAD_BACKGROUND', l, count=1)
l=l.replace('handler.postDelayed(this,1_000L); // V0872_ONE_SECOND_BACKGROUND_RECHECK', 'handler.postDelayed(this,60_000L); // V0897_BACKGROUND_BIPAD_OBSERVER')
l=l.replace('RIVER_ENDPOINT+"?_bg="', 'RIVER_ENDPOINT+"&_bg="')

# Field-test package identity.
g=re.sub(r'versionCode\s+116\b','versionCode 117',g,count=1)
g=g.replace("versionName '0.8.96'","versionName '0.8.97'",1)
if 'versionCode 117' not in g or "versionName '0.8.97'" not in g:raise SystemExit('v0897 version bump failed')

need=['V0897_OFFICIAL_POINT_AND_CURRENT_TRUTH','V0897_KEEP_ALL_284_POINT_STATIONS','V0897_BIPAD_CURRENT_NOT_LOCAL_20M','V0897_BIPAD_WATER_LEVEL_ON_TIME','V0897_MIRROR_BIPAD_CURRENT_COUNT','V0897_SOURCE_COUNT_NOT_20M','V0897_DIRECT_BIPAD_BACKGROUND','V0897_BACKGROUND_BIPAD_OBSERVER']
for x in need:
    if x not in a+l:raise SystemExit('missing '+x)
if 'LIVE (≤20m)' in a or 'LIVE (<=20m)' in a:raise SystemExit('old 20-minute UI wording survived')

a_path.write_text(a,encoding='utf-8')
l_path.write_text(l,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('v0.8.97 BIPAD mirror + 284 station point + current-count regression repair applied')
