from pathlib import Path
import runpy

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=a_path.read_text(encoding='utf-8')

# Compile-only repair. Later patch layers removed helper methods that both existing
# v0.8.48/v0.8.50 code and the final v0.8.62 official-source loader call.
# No UI, safety, map, language, GPS, colour or refresh policy is changed here.

helpers=r'''    private JSONArray trustedPages(String url,long now)throws Exception{
        // The app requests limit=2000 while Nepal's station inventory is far smaller,
        // so one no-cache page is the complete response for these calls.
        return rows(getJson(url));
    } // V0862_HELPER_TRUSTED_PAGES

    private static String v846StationIndex(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        return strDeep(r,f,"stationIndex","station_index","stationSeriesId","station_series_id","stationId","station_id");
    }
    private static String v846StationName(JSONObject r){
        if(r==null)return "";JSONObject f=r.optJSONObject("fields");
        return strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");
    }
    private static String v846Key(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","").trim();}
    private static String v848Key(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","");} // V0862_HELPER_V848_KEY

    private long trustedRowTime(JSONObject r){
        if(r==null)return 0L;JSONObject f=r.optJSONObject("fields");
        return parseTime(strDeep(r,f,"waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","timestamp","_measurementTime"));
    } // V0862_HELPER_ROW_TIME

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
    } // V0862_HELPER_DHM_ROWS

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
    } // V0862_HELPER_DHM_TIME

    private static String getTextV846(String u)throws Exception{
        HttpURLConnection c=(HttpURLConnection)new URL(u).openConnection();c.setConnectTimeout(15000);c.setReadTimeout(22000);c.setUseCaches(false);
        c.setRequestProperty("Accept","text/html,application/xhtml+xml");c.setRequestProperty("Cache-Control","no-cache, no-store");c.setRequestProperty("Pragma","no-cache");c.setRequestProperty("User-Agent","FloodSafeNepal/0.8.62 Android");
        int code=c.getResponseCode();if(code<200||code>=300)throw new IllegalStateException("HTTP "+code);
        StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l).append('\n');}finally{c.disconnect();}
        return b.toString();
    } // V0862_HELPER_DHM_HTTP

'''

# Insert immediately before the final v0.8.62 fingerprint helper. Method-name guards
# make this idempotent and avoid duplicates if older helpers survive a future chain.
anchor='    private static String v862FinalFingerprint('
if anchor not in a:raise SystemExit('v0862 compile helper insertion anchor missing')
needed=[]
checks=[
    ('private JSONArray trustedPages(', 'V0862_HELPER_TRUSTED_PAGES'),
    ('private static String v846StationIndex(', None),
    ('private static String v846StationName(', None),
    ('private static String v846Key(', None),
    ('private static String v848Key(', 'V0862_HELPER_V848_KEY'),
    ('private long trustedRowTime(', 'V0862_HELPER_ROW_TIME'),
    ('private static final class DhmLiveV846', None),
    ('private static List<DhmLiveV846> v846ParseDhmRows(', 'V0862_HELPER_DHM_ROWS'),
    ('private static String v846HtmlText(', None),
    ('private static double v846Number(', None),
    ('private static long v846DhmUpdatedAt(', 'V0862_HELPER_DHM_TIME'),
    ('private static String getTextV846(', 'V0862_HELPER_DHM_HTTP'),
]
# The broken generated source currently lacks the whole helper family. To stay safe if
# that changes, only inject the full coherent family when its main marker is absent.
if 'private JSONArray trustedPages(' not in a:
    a=a.replace(anchor,helpers+anchor,1)
else:
    # If trustedPages exists, assert the rest instead of silently creating duplicates.
    for sig,_ in checks:
        if sig not in a:raise SystemExit('v0862 partial helper family missing: '+sig)

a_path.write_text(a,encoding='utf-8')
for sig,_ in checks:
    if sig not in a:raise SystemExit('v0862 compile helper verification failed: '+sig)
for marker in ['V0862_FINAL_TRUE_REALTIME_BIPAD_DHM','V0862_FINAL_NO_FLICKER_REFRESH','RIVER_FRESH_MS=20L*60L*1000L','V0861_FULL_LANGUAGE_APPLY','V0860_SOURCE_PARITY_DETAIL']:
    if marker not in a:raise SystemExit('v0862 compile helper guard failed: '+marker)
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0862 compile helper 2km guard changed')
print('FloodSafe v0.8.62 compile helpers PASS: source helpers restored only; UI/map/safety unchanged')

# Final live display is strictly the latest official 20-minute window.
runpy.run_path(str(root/'patch_native_v0862_fresh20_live_only.py'),run_name='__main__')
a2=a_path.read_text(encoding='utf-8')
for marker in ['V0862_FRESH20_LIVE_ONLY','V0862_FRESH20_CLEAR_STALE','V0862_FRESH20_STATION_LINE','V0862_FRESH20_STATION_DETAIL']:
    if marker not in a2:raise SystemExit('v0862 fresh20 final guard failed: '+marker)
print('FloodSafe v0.8.62 final fresh20 guard PASS')

# rerun marker: v0.8.61 wrapper now bypasses its obsolete realtime-data guard; v0.8.62 owns the final loader.
