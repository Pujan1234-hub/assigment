from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.46: source parity must mean BOTH official sources named by the app.
# Rebuilt after v0.8.45 inline-summary compile fix.
# BIPAD latest=true remains first-choice for exact status/time. DHM realtime-stream is
# merged as a second official live source so stations such as Dhobi Khola at Kapan are
# not shown offline merely because BIPAD's current snapshot omitted them.
# Catalog data is metadata only (coords/thresholds) and can never make a station visible.


def replace_between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start anchor missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end anchor missing')
    return text[:i]+replacement+text[j:]

loader=r'''    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        JSONArray catalog=new JSONArray(),latest=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=2000",now);}catch(Exception ignored){}
        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c);if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            String nm=v846StationName(c);if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        // Current rows only. Catalog is never inserted here by itself.
        java.util.LinkedHashMap<String,JSONObject> current=new java.util.LinkedHashMap<>();
        for(int i=0;i<latest.length();i++){
            JSONObject r=latest.optJSONObject(i);if(r==null)continue;
            try{r.put("_floodsafeLatestEndpoint",true);r.put("_floodsafeSource","BIPAD latest");}catch(Exception ignored){}
            String ix=v846StationIndex(r),nm=v846StationName(r);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);
            if(!key.endsWith(":"))current.put(key,r);
        }

        // DHM official current stream. Match to catalog only to recover coordinates and
        // official warning/danger thresholds; a catalog-only station is still invisible.
        try{
            String html=getTextV846("https://dhm.gov.np/hydrology/realtime-stream?_floodsafe="+now);
            long dhmAt=v846DhmUpdatedAt(html,now);
            for(DhmLiveV846 d:v846ParseDhmRows(html)){
                if(d==null||d.name.isEmpty()||!Double.isFinite(d.level))continue;
                JSONObject meta=null;
                if(!d.index.isEmpty())meta=metaByIndex.get(v846Key(d.index));
                if(meta==null)meta=metaByName.get(v846Key(d.name));
                if(meta==null)continue; // no trustworthy coordinates => cannot place on map

                JSONObject row=cloneJson(meta);
                row.put("stationIndex",d.index);
                row.put("stationName",d.name);
                row.put("districtName",d.district);
                row.put("waterLevel",d.level);
                if(Double.isFinite(d.discharge))row.put("discharge",d.discharge);
                row.put("_measurementTime",java.time.Instant.ofEpochMilli(dhmAt).toString());
                row.put("_floodsafeLatestEndpoint",true);
                row.put("_floodsafeSource","DHM realtime-stream");

                JSONObject f=row.optJSONObject("fields");
                double warning=numDeep(row,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning");
                double danger=numDeep(row,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger");
                String officialStatus="";
                if(Double.isFinite(danger)&&danger>0&&d.level>=danger)officialStatus="DANGER";
                else if(Double.isFinite(warning)&&warning>0&&d.level>=warning)officialStatus="WARNING";
                else if(Double.isFinite(warning)&&warning>0)officialStatus="BELOW WARNING LEVEL";
                if(!officialStatus.isEmpty())row.put("_officialStatus",officialStatus);

                String key=!d.index.isEmpty()?"i:"+v846Key(d.index):"n:"+v846Key(d.name);
                JSONObject existing=current.get(key);
                if(existing==null){current.put(key,row);}
                else{
                    // BIPAD status/time wins; DHM fills a numeric level if BIPAD left it blank.
                    JSONObject ef=existing.optJSONObject("fields");
                    double existingLevel=numDeep(existing,ef,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level");
                    if(!Double.isFinite(existingLevel)){
                        existing.put("waterLevel",d.level);
                        if(Double.isFinite(d.discharge))existing.put("discharge",d.discharge);
                    }
                }
            }
        }catch(Exception ignored){}

        List<RiverStation> out=new ArrayList<>();
        for(JSONObject r:current.values()){
            RiverStation s=parseStation(r,now);
            if(s!=null&&s.fresh)out.add(s); // V0846_BIPAD_DHM_CURRENT_UNION
        }

        // Last-resort proxy fallback only if both official direct sources failed.
        if(out.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now));
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeLatestEndpoint",true);r.put("_floodsafeSource","BIPAD/DHM proxy");}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);if(s!=null&&s.fresh)out.add(s);
                }
            }catch(Exception ignored){}
        }
        return out;
    }

    private static String v846StationIndex(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        return strDeep(r,f,"stationIndex","station_index","stationSeriesId","station_series_id","stationId","station_id");
    }
    private static String v846StationName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        return strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");
    }
    private static String v846Key(String s){
        if(s==null)return "";return s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","").trim();
    }

    private static final class DhmLiveV846{
        String index="",name="",district="";double level=Double.NaN,discharge=Double.NaN;
    }

    private static List<DhmLiveV846> v846ParseDhmRows(String html){
        List<DhmLiveV846> out=new ArrayList<>();if(html==null||html.isEmpty())return out;
        try{
            java.util.regex.Matcher rm=java.util.regex.Pattern.compile("(?is)<tr[^>]*>(.*?)</tr>").matcher(html);
            while(rm.find()){
                java.util.ArrayList<String> cells=new java.util.ArrayList<>();
                java.util.regex.Matcher cm=java.util.regex.Pattern.compile("(?is)<t[dh][^>]*>(.*?)</t[dh]>").matcher(rm.group(1));
                while(cm.find())cells.add(v846HtmlText(cm.group(1)));
                if(cells.size()<6)continue;
                String sn=cells.get(0);if(!sn.matches("\\d+"))continue;
                DhmLiveV846 d=new DhmLiveV846();
                d.index=cells.get(2).trim();d.name=cells.get(3).trim();d.district=cells.get(4).trim();
                d.level=v846Number(cells.get(5));if(cells.size()>6)d.discharge=v846Number(cells.get(6));
                if(!d.name.isEmpty()&&Double.isFinite(d.level))out.add(d);
            }
        }catch(Exception ignored){}
        return out;
    }

    private static String v846HtmlText(String s){
        if(s==null)return "";
        return s.replaceAll("(?is)<[^>]+>"," ")
                .replace("&nbsp;"," ").replace("&#160;"," ").replace("&amp;","&")
                .replace("&lt;","<").replace("&gt;",">").replace("&quot;","\"")
                .replaceAll("\\s+"," ").trim();
    }
    private static double v846Number(String s){
        if(s==null)return Double.NaN;java.util.regex.Matcher m=java.util.regex.Pattern.compile("[-+]?[0-9]+(?:\\.[0-9]+)?").matcher(s.replace(",",""));
        if(!m.find())return Double.NaN;try{return Double.parseDouble(m.group());}catch(Exception e){return Double.NaN;}
    }

    private static long v846DhmUpdatedAt(String html,long fallback){
        try{
            String t=v846HtmlText(html);
            java.util.regex.Matcher m=java.util.regex.Pattern.compile("(?i)Last\\s+updated\\s+on\\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)?,?\\s*([A-Za-z]{3})\\s+(\\d{1,2}),\\s*(\\d{4})\\s+(\\d{1,2}):(\\d{2})\\s*(AM|PM)?").matcher(t);
            if(!m.find())return fallback;
            String[] mons={"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};int mo=0;for(int i=0;i<mons.length;i++)if(mons[i].equalsIgnoreCase(m.group(1))){mo=i+1;break;}if(mo==0)return fallback;
            int day=Integer.parseInt(m.group(2)),year=Integer.parseInt(m.group(3)),hour=Integer.parseInt(m.group(4)),min=Integer.parseInt(m.group(5));String ap=m.group(6);
            if(hour<=12&&ap!=null){if("PM".equalsIgnoreCase(ap)&&hour<12)hour+=12;if("AM".equalsIgnoreCase(ap)&&hour==12)hour=0;}
            return java.time.ZonedDateTime.of(year,mo,day,hour,min,0,0,ZoneId.of("Asia/Kathmandu")).toInstant().toEpochMilli();
        }catch(Exception e){return fallback;}
    }

    private static String getTextV846(String u)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(15000);c.setReadTimeout(22000);c.setUseCaches(false);
        c.setRequestProperty("Accept","text/html,application/xhtml+xml");c.setRequestProperty("Cache-Control","no-cache, no-store");c.setRequestProperty("User-Agent","FloodSafeNepal/0.8.46 Android");
        int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);
        StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l).append('\n');}finally{c.disconnect();}
        return b.toString();
    }

'''
a=replace_between(a,'    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{','    private JSONArray trustedPages(',loader,'v0.8.46 official union loader')

# Keep the source-parity summary accurate now that both official sources feed it.
if 'V0845_SOURCE_PARITY_SUMMARY' not in a: raise SystemExit('v0.8.46 v0.8.45 summary marker missing')
a=a.replace('BIPAD/DHM अहिले उपलब्ध: ','BIPAD + DHM अहिले उपलब्ध: ',1).replace('BIPAD/DHM available now: ','BIPAD + DHM available now: ',1)

# Version.
g=g.replace('versionCode 65','versionCode 66',1).replace("versionName '0.8.45'","versionName '0.8.46'",1)
if 'versionCode 66' not in g or "versionName '0.8.46'" not in g:raise SystemExit('v0.8.46 version bump failed')

for marker in ['V0846_BIPAD_DHM_CURRENT_UNION','DHM realtime-stream','v846ParseDhmRows','v846DhmUpdatedAt','getTextV846','V0845_SCREEN_SCALE_RIVER_TAP','bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))']:
    if marker not in a+'\n'+g and marker!='V0845_SCREEN_SCALE_RIVER_TAP':raise SystemExit('v0.8.46 marker missing: '+marker)
# map marker lives in map file; do not alter it here.

# Hard rule: catalog is metadata only; output is constructed from current map values.
block=a[a.find('    private List<RiverStation> loadTrustedRiverStations'):a.find('    private JSONArray trustedPages(')]
if 'current.values()' not in block or 'catalog' not in block or 's!=null&&s.fresh' not in block:raise SystemExit('v0.8.46 union safety check failed')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.46 BIPAD + DHM current-source union realtime PASS')
