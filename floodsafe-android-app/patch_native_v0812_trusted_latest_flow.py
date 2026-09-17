from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path=src/'NativeFullActivity.java'
map_path=src/'FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'
activity=activity_path.read_text(encoding='utf-8')
helper=map_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

def replace_between(text,start,end,replacement,label):
    a=text.find(start)
    if a<0: raise SystemExit(label+' start anchor missing')
    b=text.find(end,a)
    if b<0: raise SystemExit(label+' end anchor missing')
    return text[:a]+replacement+text[b:]

trusted_refresh=r'''    private void refreshRivers(){
        feedFresh.setText(t("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…"));
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();
                List<RiverStation> out=loadTrustedRiverStations(now);
                out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
                synchronized(stations){stations.clear();stations.addAll(out);}
                runOnUiThread(this::refreshRiverUi);
            }catch(Exception e){
                runOnUiThread(()->feedFresh.setText(t("Official river refresh हुन सकेन • पुरानो data live देखाइएको छैन","Official river refresh failed • old data is not shown as live")));
            }
        });
    }

    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        JSONArray catalog=new JSONArray(),latest=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=2000",now);}catch(Exception ignored){}
        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}
        JSONArray merged=mergeTrustedRiverRows(catalog,latest);
        List<RiverStation> out=new ArrayList<>();
        for(int i=0;i<merged.length();i++){RiverStation s=parseStation(merged.optJSONObject(i),now);if(s!=null)out.add(s);}
        if(out.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now));
                for(int i=0;i<rr.length();i++){RiverStation s=parseStation(rr.optJSONObject(i),now);if(s!=null)out.add(s);}
            }catch(Exception ignored){}
        }
        return out;
    }

    private JSONArray trustedPages(String first,long now)throws Exception{
        JSONArray out=new JSONArray();String next=first;List<String>seen=new ArrayList<>();
        for(int page=0;page<24&&next!=null&&!next.isEmpty();page++){
            if(seen.contains(next))break;seen.add(next);
            String u=next+(next.contains("?")?"&":"?")+"_nativefull="+now+"_"+page;
            JSONObject j=getJson(u);JSONArray part=rows(j);
            for(int i=0;i<part.length();i++)out.put(part.opt(i));
            String n=j.optString("next","");
            if(n.isEmpty()){JSONObject d=j.optJSONObject("data");if(d!=null)n=d.optString("next","");}
            if(n.isEmpty()||part.length()==0)break;
            if(n.startsWith("http://")||n.startsWith("https://"))next=n;
            else if(n.startsWith("/"))next="https://bipadportal.gov.np"+n;
            else next=BIPAD+n.replaceFirst("^api/v1/","");
        }
        return out;
    }

    private JSONArray mergeTrustedRiverRows(JSONArray catalog,JSONArray latest){
        try{
            java.util.LinkedHashMap<String,JSONObject> latestById=new java.util.LinkedHashMap<>();
            for(int i=0;i<latest.length();i++){
                JSONObject r=latest.optJSONObject(i);if(r==null)continue;
                List<String>ids=trustedIds(r);long rt=trustedRowTime(r);
                for(String id:ids){JSONObject old=latestById.get(id);if(old==null||rt>=trustedRowTime(old))latestById.put(id,r);}
            }
            JSONArray out=new JSONArray();List<JSONObject>used=new ArrayList<>();
            for(int i=0;i<catalog.length();i++){
                JSONObject c=catalog.optJSONObject(i);if(c==null)continue;JSONObject live=null;
                for(String id:trustedIds(c)){if(latestById.containsKey(id)){live=latestById.get(id);break;}}
                JSONObject m=live==null?cloneJson(c):mergeJson(c,live);out.put(m);if(live!=null&&!used.contains(live))used.add(live);
            }
            for(int i=0;i<latest.length();i++){JSONObject r=latest.optJSONObject(i);if(r!=null&&!used.contains(r))out.put(r);}
            return out;
        }catch(Exception e){return latest.length()>0?latest:catalog;}
    }

    private static JSONObject cloneJson(JSONObject o)throws Exception{return o==null?new JSONObject():new JSONObject(o.toString());}
    private static JSONObject mergeJson(JSONObject base,JSONObject live)throws Exception{
        JSONObject m=cloneJson(base);
        java.util.Iterator<String>it=live.keys();while(it.hasNext()){String k=it.next();m.put(k,live.opt(k));}
        JSONObject bf=base.optJSONObject("fields"),lf=live.optJSONObject("fields");
        if(bf!=null||lf!=null){JSONObject f=bf==null?new JSONObject():cloneJson(bf);if(lf!=null){java.util.Iterator<String>fi=lf.keys();while(fi.hasNext()){String k=fi.next();f.put(k,lf.opt(k));}}m.put("fields",f);}
        return m;
    }

    private static List<String> trustedIds(JSONObject o){
        List<String>out=new ArrayList<>();if(o==null)return out;
        addTrustedIds(o,out);JSONObject f=o.optJSONObject("fields");addTrustedIds(f,out);
        addTrustedIds(o.optJSONObject("station"),out);addTrustedIds(o.optJSONObject("riverStation"),out);addTrustedIds(o.optJSONObject("river_station"),out);
        return out;
    }
    private static void addTrustedIds(JSONObject o,List<String>out){
        if(o==null)return;String[]ks={"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","id"};
        for(String k:ks){Object v=o.opt(k);if(v!=null&&v!=JSONObject.NULL){String s=String.valueOf(v).trim();if(!s.isEmpty()&&!out.contains(s))out.add(s);}}
    }
    private static long trustedRowTime(JSONObject r){
        if(r==null)return 0L;JSONObject f=r.optJSONObject("fields");
        return parseTime(strDeep(r,f,"_measurementTime","waterLevelOn","water_level_on","riverLevelOn","river_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","datetime","dateTime","date_time","timestamp"));
    }
    private static boolean sameNepalCalendarDay(long at,long now){
        if(at<=0||at-now>5L*60L*1000L)return false;
        java.util.TimeZone tz=java.util.TimeZone.getTimeZone("Asia/Kathmandu");
        java.util.Calendar a=java.util.Calendar.getInstance(tz),b=java.util.Calendar.getInstance(tz);
        a.setTimeInMillis(at);b.setTimeInMillis(now);
        return a.get(java.util.Calendar.ERA)==b.get(java.util.Calendar.ERA)&&a.get(java.util.Calendar.YEAR)==b.get(java.util.Calendar.YEAR)&&a.get(java.util.Calendar.DAY_OF_YEAR)==b.get(java.util.Calendar.DAY_OF_YEAR);
    }

'''
activity=replace_between(activity,'    private void refreshRivers(){','    private RiverStation parseStation(',trusted_refresh,'refreshRivers trusted runtime')

trusted_parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[]c=officialCoord(r);double a=c[0],o=c[1];if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value"),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold","warning"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold","danger");
        long at=trustedRowTime(r);
        boolean current=Double.isFinite(level)&&sameNepalCalendarDay(at,now);
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(current){
            if((Double.isFinite(danger)&&danger>0&&level>=danger)||(raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((Double.isFinite(warning)&&warning>0&&level>=warning)||(raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if(raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else{stage="normal";rank=3;}
        }else{
            level=Double.NaN;at=0L;raw="NO_CURRENT_OFFICIAL_READING";stage="unknown";rank=4;
        }
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");
        JSONObject station=r.optJSONObject("station");if(name.isEmpty()&&station!=null)name=str(station,"name","title","stationName");
        if(name.isEmpty())name="Official river station";
        String district=strDeep(r,f,"districtName","district_name","district");
        return new RiverStation(name,district,a,o,level,warning,danger,at,current,stage,rank,raw);
    }

'''
activity=replace_between(activity,'    private RiverStation parseStation(','    private void refreshRainStations(){',trusted_parse,'trusted parseStation')

helper=helper.replace('lineColor("#7f939c"), lineWidth(2.45f), lineOpacity(0.92f)','lineColor("#22e7ff"), lineWidth(2.70f), lineOpacity(0.98f)',1)
helper=helper.replace('float glow=(float)(0.48+0.50*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(1.05f+0.80f*glow));','float glow=(float)(0.68+0.32*(0.5+0.5*Math.sin(ph*Math.PI*2.0)));flowTrace.setProperties(lineOpacity(glow),lineWidth(1.45f+1.05f*glow));',1)
helper=helper.replace('int n = Math.min(120, rivers.size());','int n = Math.min(180, rivers.size());',1)
helper=helper.replace('main.postDelayed(this, 280L);','main.postDelayed(this, 320L);',1)

helper=helper.replace('synchronized(stations){for(StationDot s:stations){String sk=riverNameKey(s.name);','synchronized(stations){for(StationDot s:stations){if(!s.fresh)continue;String sk=riverNameKey(s.name);',1)
near_anchor='    private StationDot directGaugeFor(RiverWay r,double la,double lo){'
near_method=r'''    private StationDot nearestFreshStation(double la,double lo){
        StationDot best=null;double d=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){if(s==null||!s.fresh)continue;double x=km(la,lo,s.lat,s.lon);if(x<d){d=x;best=s;}}}
        return best;
    }
'''
if 'private StationDot nearestFreshStation(' not in helper:
    if near_anchor not in helper: raise SystemExit('directGaugeFor anchor missing')
    helper=helper.replace(near_anchor,near_method+'\n'+near_anchor,1)
helper=helper.replace('StationDot near = nearestStation(la, lo);','StationDot near = nearestFreshStation(la, lo);',1)
helper=helper.replace('यो नदी/खोलामा direct official realtime gauge भेटिएन।','यो नदी/खोलाको आजको direct official reading भेटिएन।',1)
helper=helper.replace('नजिकको gauge reference मात्र: ','नजिकको आजको official gauge reference: ',1)

if "versionName '0.8.12'" not in gradle:
    gradle=gradle.replace('versionCode 31','versionCode 32',1)
    gradle=gradle.replace("versionName '0.8.11'","versionName '0.8.12'",1)
if 'versionCode 32' not in gradle or "versionName '0.8.12'" not in gradle: raise SystemExit('v0.8.12 version bump failed')

activity_path.write_text(activity,encoding='utf-8')
map_path.write_text(helper,encoding='utf-8')
gradle_path.write_text(gradle,encoding='utf-8')

a=activity_path.read_text(encoding='utf-8');h=map_path.read_text(encoding='utf-8')
for m in ['river-stations/?latest=true&limit=2000','mergeTrustedRiverRows','sameNepalCalendarDay','NO_CURRENT_OFFICIAL_READING','trustedPages','_measurementTime']:
    if m not in a: raise SystemExit('v0.8.12 activity marker missing: '+m)
for m in ['lineColor("#22e7ff"), lineWidth(2.70f)','Math.min(180, rivers.size())','nearestFreshStation','if(!s.fresh)continue','fs-river-danger-status-layer','riverStatusKick = this::rebuildRiverStatusAsync']:
    if m not in h: raise SystemExit('v0.8.12 map marker missing: '+m)
if 'StationDot near = nearestStation(la, lo);' in h: raise SystemExit('stale nearest river reference remained')
print('FloodSafe v0.8.12 trusted latest official river pipeline + visible flow/glow PASS')
