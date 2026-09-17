from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8');m=m_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

def replace_between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start anchor missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end anchor missing')
    return text[:i]+replacement+text[j:]

# -----------------------------------------------------------------------------
# One display truth: BIPAD official catalog = total stations; BIPAD latest = source-online.
# Safety freshness remains separate (<=30 min) and is still used for flood alerts/river colours.
# This keeps a station green when the official latest endpoint publishes it, while an older
# observation can never trigger a live warning merely because the station is online.
# -----------------------------------------------------------------------------
loader=r'''    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{
        JSONArray catalog=new JSONArray(),latest=new JSONArray();
        try{catalog=trustedPages(BIPAD+"river-stations/?limit=2000",now);}catch(Exception ignored){}
        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}
        v849CatalogCount=catalog.length();v849LatestCount=latest.length(); // V0850_EXACT_SOURCE_COUNTS

        java.util.LinkedHashMap<String,JSONObject> metaByIndex=new java.util.LinkedHashMap<>();
        java.util.LinkedHashMap<String,JSONObject> metaByName=new java.util.LinkedHashMap<>();
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            if(!ix.isEmpty())metaByIndex.put(v846Key(ix),c);
            if(!nm.isEmpty())metaByName.put(v846Key(nm),c);
        }

        List<RiverStation> out=new ArrayList<>();java.util.HashSet<String> onlineKeys=new java.util.HashSet<>();
        for(int i=0;i<latest.length();i++){
            JSONObject live=latest.optJSONObject(i);if(live==null)continue;
            String ix=v846StationIndex(live),nm=v846StationName(live);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);
            JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject merged=v850MergeStationMeta(meta,live);
            try{merged.put("_floodsafeOnline",true);merged.put("_floodsafeSource","BIPAD latest");}catch(Exception ignored){}
            RiverStation s=parseStation(merged,now);if(s!=null){out.add(s);onlineKeys.add(key);}
        }
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);
            if(onlineKeys.contains(key))continue;
            JSONObject off=v850MergeStationMeta(c,null);
            try{off.put("_floodsafeOnline",false);off.put("_floodsafeCatalogOnly",true);off.put("_floodsafeSource","BIPAD catalog");}catch(Exception ignored){}
            RiverStation s=parseStation(off,now);if(s!=null)out.add(s);
        }

        // Only if BIPAD itself is unreachable: keep the app useful with the existing official proxy.
        // Proxy rows are never mixed into a healthy BIPAD catalog/latest result, so parity stays exact.
        if(out.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now));
                for(int i=0;i<rr.length();i++){
                    JSONObject r=rr.optJSONObject(i);if(r==null)continue;
                    try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","BIPAD/DHM proxy");}catch(Exception ignored){}
                    RiverStation s=parseStation(r,now);if(s!=null)out.add(s);
                }
                v849CatalogCount=out.size();v849LatestCount=out.size();
            }catch(Exception ignored){}
        }
        return out; // V0850_BIPAD_PARITY_LOADER
    }

    private static JSONObject v850MergeStationMeta(JSONObject meta,JSONObject live){
        JSONObject out=new JSONObject();
        try{if(meta!=null)out=new JSONObject(meta.toString());}catch(Exception ignored){}
        if(live!=null)try{java.util.Iterator<String> it=live.keys();while(it.hasNext()){String k=it.next();Object v=live.opt(k);if(v!=null)out.put(k,v);}}catch(Exception ignored){}
        return out;
    }

'''
a=replace_between(a,'    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{','    private static String v846StationIndex(',loader,'v0850 official loader')

# -----------------------------------------------------------------------------
# Parse official observation without confusing "online in source" with "fresh enough
# for safety". Absolute reduced-level stations are normalized by their official elevation
# so Kathmandu gauges show useful depth (e.g. 1340.534 at elevation 1340 -> 0.534 m).
# -----------------------------------------------------------------------------
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=officialCoord(r);double la=c[0],lo=c[1];if(!Double.isFinite(la)||!Double.isFinite(lo)||!isNepal(la,lo))return null;
        double level=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level"),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold"),
               elevation=numDeep(r,f,"elevation","stationElevation","station_elevation","altitude");
        long at=trustedRowTime(r);
        boolean online=r.optBoolean("_floodsafeOnline",!r.optBoolean("_floodsafeCatalogOnly",false));
        boolean hasObservation=online&&Double.isFinite(level)&&at>0;
        boolean fresh=hasObservation&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L; // V0850_ONLINE_SEPARATE_FRESH

        boolean datum=Double.isFinite(elevation)&&elevation>50&&Double.isFinite(level)&&Math.abs(level-elevation)<20 &&
                ((Double.isFinite(warning)&&Math.abs(warning-elevation)<25)||(Double.isFinite(danger)&&Math.abs(danger-elevation)<25));
        if(datum){level-=elevation;if(Double.isFinite(warning))warning-=elevation;if(Double.isFinite(danger))danger-=elevation;} // V0850_DATUM_NORMALIZED

        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(online&&hasObservation){
            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")){stage="danger";rank=0;}
            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")){stage="warning";rank=1;}
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else if(raw.contains("BELOW WARNING")||raw.contains("NORMAL")||raw.contains("BLUE")||raw.contains("GREEN")){stage="normal";rank=3;}
            else if(Double.isFinite(danger)&&danger>0&&level>=danger){stage="danger";rank=0;}
            else if(Double.isFinite(warning)&&warning>0&&level>=warning){stage="warning";rank=1;}
            else{stage="normal";rank=3;}
        }
        if(!online){level=Double.NaN;at=0L;raw="OFFLINE / NOT IN LATEST SOURCE";stage="unknown";rank=4;}
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official river station";
        String district=v848DistrictName(la,lo,strDeep(r,f,"districtName","district_name","district"));
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);
    }

'''
ps=a.find('    private RiverStation parseStation(')
pe=a.find('    private String v848DistrictName(',ps)
if ps<0 or pe<0: raise SystemExit('v0850 parse anchors')
a=a[:ps]+parse+a[pe:]

# RiverStation now carries source availability separately from safety freshness.
pat=r'    private static final class RiverStation\{[^\n]*\}\n'
newcls='    private static final class RiverStation{final String name,district,stage,rawStatus;final double lat,lon,level,warning,danger;final long at;final boolean fresh,online;final int rank;RiverStation(String n,String di,double a,double o,double l,double w,double d,long tm,boolean f,boolean on,String s,int r,String rs){name=n;district=di;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;online=on;stage=s;rank=r;rawStatus=rs;}}\n'
a,n=re.subn(pat,newcls,a,count=1)
if n!=1: raise SystemExit('v0850 RiverStation class anchor')

# -----------------------------------------------------------------------------
# Exact source/app parity UI and requested station dots: green=source online,
# black=not in latest feed. GPS is kept blue on the native map.
# -----------------------------------------------------------------------------
rs=a.find('    private void refreshRiverUi(){');re_=a.find('    private static String v849AvailabilityDot',rs)
if rs<0 or re_<0: raise SystemExit('v0850 refresh UI anchors')
refresh=r'''    private void refreshRiverUi(){
        if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        copy.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(copy,lat,lon);
        int online=0,recent=0,d=0,w=0,al=0,n=0;for(RiverStation s:copy){if(s.online)online++;if(s.fresh){recent++;if("danger".equals(s.stage))d++;else if("warning".equals(s.stage))w++;else if("alert".equals(s.stage))al++;else if("normal".equals(s.stage))n++;}}
        int sourceTotal=v849CatalogCount>0?v849CatalogCount:copy.size(),sourceLatest=v849LatestCount>0?v849LatestCount:online,offline=Math.max(0,sourceTotal-sourceLatest);
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("आधिकारिक स्टेशन "+sourceTotal+" • 🟢 स्रोतमा उपलब्ध "+sourceLatest+" • ⚫ उपलब्ध छैन "+offline+" • पछिल्लो ३० मिनेटका मापन "+recent,
                "Official stations "+sourceTotal+" • 🟢 available in current source "+sourceLatest+" • ⚫ not currently available "+offline+" • readings within 30 min "+recent)); // V0850_PARITY_UI
        updateRisk(copy);
        nearList.removeAllViews();List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));if(near.isEmpty())nearList.addView(empty(t("नजिकको आधिकारिक नदी मापन केन्द्र भेटिएन।","No nearby official river station was found.")));
        if(nationalList!=null){nationalList.removeAllViews();if(selectedDistrict.isEmpty()){nationalFresh.setText(t("जिल्ला छानेर त्यहाँका आधिकारिक मापन केन्द्र हेर्नुहोस्।","Choose a district to view its official river stations."));nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));}else{int total=0,on=0,fr=0;for(RiverStation s:copy)if(selectedDistrict.equalsIgnoreCase(s.district)){total++;if(s.online)on++;if(s.fresh)fr++;nationalList.addView(stationRow(s));}nationalFresh.setText(t(selectedDistrict+": जम्मा "+total+" • 🟢 उपलब्ध "+on+" • पछिल्लो ३० मिनेट "+fr,selectedDistrict+": total "+total+" • 🟢 available "+on+" • within 30 min "+fr));if(total==0)nationalList.addView(empty(t("आधिकारिक नदी मापन केन्द्र भेटिएन।","No official river station was found.")));}}
    }

'''
a=a[:rs]+refresh+a[re_:]

ss=a.find('    private static String v849AvailabilityDot');se=a.find('    private void updateRisk(',ss)
if ss<0 or se<0: raise SystemExit('v0850 row anchors')
row=r'''    private static String v849AvailabilityDot(RiverStation s){return s!=null&&s.online?"🟢":"⚫";} // V0850_AVAILABILITY_DOT
    private View stationRow(RiverStation s){TextView v=text(v849AvailabilityDot(s)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(s.online?Color.rgb(239,252,244):Color.rgb(245,246,247),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
'''
a=a[:ss]+row+a[se:]

us=a.find('    private void updateRisk(');ue=a.find('    private String stationLine(',us)
if us<0 or ue<0: raise SystemExit('v0850 updateRisk anchors')
risk=r'''    private void updateRisk(List<RiverStation> copy){
        RiverStation best=null;double bestD=Double.POSITIVE_INFINITY;for(RiverStation s:copy){if(!s.fresh)continue;double km=distanceKm(s.lat,s.lon);if(!Double.isFinite(km))continue;if(km<bestD){bestD=km;best=s;}}
        if(best==null){riskValue.setText("—");riskBadge.setText(t("हालको मापन छैन","NO RECENT READING"));riskText.setText(t("सुरक्षा जोखिमका लागि पछिल्लो ३० मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ।","Only official observations from the last 30 minutes are used for safety risk."));alarmBanner.setVisibility(View.GONE);return;}
        riskValue.setText(stageName(best.stage));riskBadge.setText(stageName(best.stage));riskText.setText(best.name+" • "+String.format(Locale.US,"%.1f km",bestD)+" • "+stationLine(best));int col=stageColor(best.stage);riskValue.setTextColor(col);riskBadge.setTextColor(col);
        boolean emergency=bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"));alarmBanner.setVisibility(emergency?View.VISIBLE:View.GONE);if(emergency){alarmTitle.setText(best.stage.equals("danger")?t("🚨 खतरा — २ किमिभित्र","🚨 DANGER — within 2 km"):t("⚠️ चेतावनी — २ किमिभित्र","⚠️ WARNING — within 2 km"));alarmText.setText(best.name+" • "+stationLine(best));}
    }

'''
a=a[:us]+risk+a[ue:]

ls=a.find('    private String stationLine(');le=a.find('    private static String mapDisplayStage(',ls)
if ls<0 or le<0: raise SystemExit('v0850 stationLine anchors')
line=r'''    private String v850Age(long at){if(at<=0)return t("समय उपलब्ध छैन","time unavailable");long min=Math.max(0,(System.currentTimeMillis()-at)/60000L);if(min<60)return t(min+" मिनेटअघि",min+" min ago");long h=min/60;if(h<48)return t(h+" घण्टाअघि",h+" h ago");long d=h/24;return t(d+" दिनअघि",d+" d ago");}
    private String stationLine(RiverStation s){if(!s.online)return t("अफलाइन • हालको मापन उपलब्ध छैन","Offline • no current observation");String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("सतह उपलब्ध छैन","level unavailable");String prefix=s.fresh?stageName(s.stage):t("स्रोतमा उपलब्ध पछिल्लो मापन","Latest source observation");return prefix+" • "+lev+" • "+v850Age(s.at);}

'''
a=a[:ls]+line+a[le:]
a=a.replace('private static String mapDisplayStage(RiverStation s){\n        if(s==null||!s.fresh)return "stale";','private static String mapDisplayStage(RiverStation s){\n        if(s==null||!s.online)return "offline";\n        if(!s.fresh)return "latest";',1)

# Fully localized station detail.
sh=a.find('    private void showStation(');eh=a.find('    private void refreshHuman()',sh)
if sh<0 or eh<0: raise SystemExit('v0850 station detail anchors')
detail=r'''    private void showStation(RiverStation s){
        StringBuilder b=new StringBuilder();b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("स्रोतमा उपलब्ध","Available in source"):t("अफलाइन","Offline"));
        if(s.online){b.append("\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage));b.append("\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));b.append("\n").append(t("आधिकारिक मापन: ","Official observation: ")).append(s.at>0?v848Time(s.at):"—");if(!s.fresh)b.append("\n").append(t("यो मापन ३० मिनेटभन्दा पुरानो भएकाले प्रत्यक्ष सुरक्षा चेतावनीका लागि प्रयोग हुँदैन।","This observation is older than 30 minutes, so it is not used for live safety alerts."));}else b.append("\n").append(t("यो आधिकारिक स्टेशन हाल BIPAD को पछिल्लो स्रोत सूचीमा छैन।","This official station is not currently present in BIPAD's latest source feed."));
        b.append("\n").append(t("स्रोत: BIPAD आधिकारिक नदी मापन केन्द्र","Source: BIPAD official river station feed"));new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    }

'''
a=a[:sh]+detail+a[eh:]

# -----------------------------------------------------------------------------
# SATHI: route every app-data question through one grounded engine. It can answer
# station, river, district, source counts, flood risk, GPS-nearby, rainfall and weather.
# It never invents missing current observations.
# -----------------------------------------------------------------------------
a=a.replace('ans=v848SathiAnswer(z);','ans=v850SathiAnswer(z);',1)
anchor='    private String v848SathiAnswer(String q)throws Exception{'
if anchor not in a: raise SystemExit('v0850 SATHI anchor')
sathi=r'''    private String v850SathiAnswer(String q)throws Exception{ // V0850_SATHI_ALL_DATA
        String x=q==null?"":q.trim().toLowerCase(Locale.ROOT);if(x.isEmpty())return t("प्रश्न लेख्नुहोस्।","Enter a question.");
        String district=v848FindDistrict(q);RiverStation station=v850BestStation(q);
        boolean weather=x.contains("weather")||x.contains("मौसम")||x.contains("temperature")||x.contains("temp")||x.contains("तापक्रम")||x.contains("rainfall")||x.contains("rain")||x.contains("वर्षा");
        if(weather){double[] p=v848Point(district);if(p==null)return t("जिल्ला वा स्थानको नामसहित सोध्नुहोस्, अथवा नेपालभित्र GPS स्थान दिनुहोस्।","Ask with a district/place name, or provide a GPS location inside Nepal.");return v850Weather(district,p[0],p[1]);}
        if(station!=null)return v850StationAnswer(station);
        if(!district.isEmpty())return v850DistrictAnswer(district);
        if(x.contains("how many")||x.contains("count")||x.contains("station")||x.contains("स्टेशन")||x.contains("कति")||x.contains("online")||x.contains("offline")||x.contains("source")||x.contains("स्रोत"))return v850SourceSummary();
        if(x.contains("near")||x.contains("nearest")||x.contains("नजिक")||x.contains("gps")||x.contains("location")||x.contains("स्थान"))return v850NearbyAnswer();
        if(x.contains("warning")||x.contains("danger")||x.contains("flood")||x.contains("alert")||x.contains("चेतावनी")||x.contains("खतरा")||x.contains("बाढी"))return v850HazardAnswer();
        if(x.contains("green")||x.contains("black")||x.contains("blue")||x.contains("dot")||x.contains("रङ")||x.contains("हरियो")||x.contains("कालो")||x.contains("निलो"))return t("🟢 हरियो बिन्दु = BIPAD को पछिल्लो स्रोतमा उपलब्ध स्टेशन। ⚫ कालो = आधिकारिक स्टेशन तर अहिले पछिल्लो स्रोतमा उपलब्ध छैन। 🔵 निलो = तपाईंको GPS स्थान। नदीको रङ भने बाढी अवस्थाअनुसार बदलिन्छ।","🟢 Green dot = station present in BIPAD's latest source. ⚫ Black = official station not currently present in the latest source. 🔵 Blue = your GPS location. River-line colours separately represent flood status.");
        return v850SourceSummary()+"\n\n"+t("मलाई जिल्ला, नदी/खोला, स्टेशन, पानीको सतह, बाढी अवस्था, वर्षा, तापक्रम, मौसम, GPS नजिकका केन्द्र वा स्रोतको अवस्था सोध्न सक्नुहुन्छ।","You can ask me about a district, river/khola, station, water level, flood status, rainfall, temperature, weather, nearby GPS stations, or source availability.");
    }
    private RiverStation v850BestStation(String q){String low=q==null?"":q.toLowerCase(Locale.ROOT),k=v848Key(q);RiverStation best=null;int bestScore=0;String[] stop={"river","khola","station","status","level","water","flood","warning","danger","what","tell","about","को","खोला","नदी","अवस्था","कति"};java.util.HashSet<String> sw=new java.util.HashSet<>();for(String z:stop)sw.add(z);synchronized(stations){for(RiverStation r:stations){String nk=v848Key(r.name);int score=(nk.length()>4&&k.contains(nk))?20:0;for(String tok:r.name.toLowerCase(Locale.ROOT).split("[^a-z0-9]+")){if(tok.length()<4||sw.contains(tok))continue;if(low.contains(tok))score+=3;}if(score>bestScore||(score==bestScore&&score>0&&best!=null&&r.online&&!best.online)){bestScore=score;best=r;}}}return bestScore>=3?best:null;}
    private String v850StationAnswer(RiverStation s){StringBuilder b=new StringBuilder(s.name);if(s.district!=null&&!s.district.isEmpty())b.append(" • ").append(s.district);if(!s.online){b.append("\n⚫ ").append(t("आधिकारिक स्टेशन हो, तर अहिले BIPAD को पछिल्लो स्रोतमा उपलब्ध छैन।","This is an official station, but it is not currently present in BIPAD's latest source feed."));return b.toString();}b.append("\n🟢 ").append(t("स्रोतमा उपलब्ध","Available in source"));b.append("\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage));if(Double.isFinite(s.level))b.append(" • ").append(String.format(Locale.US,"%.2f m",s.level));b.append(" • ").append(v850Age(s.at));if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));if(Double.isFinite(s.danger))b.append(" • ").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));if(!s.fresh)b.append("\n").append(t("मापन ३० मिनेटभन्दा पुरानो छ; प्रत्यक्ष सुरक्षा चेतावनीका लागि प्रयोग हुँदैन।","The observation is older than 30 minutes and is not used for live safety alerts."));return b.toString();}
    private String v850DistrictAnswer(String d){List<RiverStation> z=new ArrayList<>();synchronized(stations){for(RiverStation r:stations)if(d.equalsIgnoreCase(r.district))z.add(r);}z.sort(Comparator.comparingInt((RiverStation r)->r.online?0:1).thenComparing(r->r.name,String.CASE_INSENSITIVE_ORDER));int on=0,fr=0,da=0,wa=0;for(RiverStation r:z){if(r.online)on++;if(r.fresh){fr++;if("danger".equals(r.stage))da++;if("warning".equals(r.stage))wa++;}}StringBuilder b=new StringBuilder(d).append(t(": जम्मा ",": total ")).append(z.size()).append(t(" • स्रोतमा उपलब्ध "," • available ")).append(on).append(t(" • पछिल्लो ३० मिनेट "," • within 30 min ")).append(fr).append(" • 🔴 ").append(da).append(" • 🟠 ").append(wa);for(int i=0;i<Math.min(8,z.size());i++){RiverStation r=z.get(i);b.append("\n").append(v849AvailabilityDot(r)).append(" ").append(r.name).append(" — ").append(r.online?(Double.isFinite(r.level)?String.format(Locale.US,"%.2f m",r.level):t("मापन उपलब्ध छैन","observation unavailable")):t("अफलाइन","offline"));}return b.toString();}
    private String v850SourceSummary(){int total=v849CatalogCount,on=v849LatestCount;if(total<=0){synchronized(stations){total=stations.size();for(RiverStation r:stations)if(r.online)on++;}}return t("BIPAD आधिकारिक स्टेशन "+total+"। अहिले पछिल्लो स्रोतमा उपलब्ध "+on+"। उपलब्ध नभएका "+Math.max(0,total-on)+"। सुरक्षा चेतावनीका लागि ३० मिनेटभित्रको मापन मात्र प्रयोग हुन्छ।","BIPAD official stations: "+total+". Currently present in the latest source: "+on+". Not currently present: "+Math.max(0,total-on)+". Only observations within 30 minutes are used for safety alerts.");}
    private String v850NearbyAnswer(){if(!isNepal(lat,lon))return t("नेपालभित्रको GPS स्थान उपलब्ध भएपछि नजिकका केन्द्र बताउन सक्छु।","I can list nearby stations after a GPS location inside Nepal is available.");List<RiverStation> z; synchronized(stations){z=new ArrayList<>(stations);}z.sort(Comparator.comparingDouble(r->distanceKm(r.lat,r.lon)));StringBuilder b=new StringBuilder(t("तपाईंको GPS नजिकका केन्द्र:","Stations nearest to your GPS:"));for(int i=0;i<Math.min(5,z.size());i++){RiverStation r=z.get(i);b.append("\n").append(v849AvailabilityDot(r)).append(" ").append(r.name).append(String.format(Locale.US," • %.1f km",distanceKm(r.lat,r.lon)));}return b.toString();}
    private String v850HazardAnswer(){List<RiverStation> z=new ArrayList<>();synchronized(stations){for(RiverStation r:stations)if(r.fresh&&(r.stage.equals("warning")||r.stage.equals("danger")||r.stage.equals("alert")))z.add(r);}z.sort(Comparator.comparingInt(r->r.rank));if(z.isEmpty())return t("पछिल्लो ३० मिनेटका आधिकारिक मापनमा Alert/Warning/Danger स्टेशन भेटिएन।","No Alert/Warning/Danger station was found among official observations from the last 30 minutes.");StringBuilder b=new StringBuilder(t("हालका आधिकारिक जोखिम मापन:","Current official risk observations:"));for(int i=0;i<Math.min(10,z.size());i++){RiverStation r=z.get(i);b.append("\n• ").append(r.name).append(" — ").append(stageName(r.stage));if(Double.isFinite(r.level))b.append(String.format(Locale.US," %.2f m",r.level));}return b.toString();}
    private String v850Weather(String d,double la,double lo)throws Exception{String u=String.format(Locale.US,"https://api.open-meteo.com/v1/forecast?latitude=%.6f&longitude=%.6f&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=Asia%%2FKathmandu",la,lo);JSONObject j=getJson(u),c=j.getJSONObject("current");double te=c.optDouble("temperature_2m",Double.NaN),pr=c.optDouble("precipitation",Double.NaN),hu=c.optDouble("relative_humidity_2m",Double.NaN),wi=c.optDouble("wind_speed_10m",Double.NaN);String label=d==null||d.isEmpty()?t("हालको GPS स्थान","Current GPS location"):d;StringBuilder b=new StringBuilder(label);if(Double.isFinite(te))b.append(t("\nतापक्रम: ","\nTemperature: ")).append(String.format(Locale.US,"%.1f°C",te));if(Double.isFinite(pr))b.append(t("\nअहिलेको वर्षा: ","\nCurrent precipitation: ")).append(String.format(Locale.US,"%.1f mm",pr));if(Double.isFinite(hu))b.append(t("\nआर्द्रता: ","\nHumidity: ")).append(String.format(Locale.US,"%.0f%%",hu));if(Double.isFinite(wi))b.append(t("\nहावाको गति: ","\nWind speed: ")).append(String.format(Locale.US,"%.0f km/h",wi));RainStation rr=v848NearestRain(la,lo);if(rr!=null){b.append(t("\nनजिकको आधिकारिक वर्षा केन्द्र: ","\nNearest official rain station: ")).append(rr.name);if(Double.isFinite(rr.rainfall))b.append(t(" • १ घण्टा "," • 1 h ")).append(String.format(Locale.US,"%.1f mm",rr.rainfall));if(Double.isFinite(rr.rain3))b.append(t(" • ३ घण्टा "," • 3 h ")).append(String.format(Locale.US,"%.1f mm",rr.rain3));if(Double.isFinite(rr.rain24))b.append(t(" • २४ घण्टा "," • 24 h ")).append(String.format(Locale.US,"%.1f mm",rr.rain24));b.append(rr.fresh?t(" • हालको मापन"," • current observation"):t(" • पुरानो/अज्ञात मापन"," • stale/unknown observation"));}return b.toString();}

'''
a=a.replace(anchor,sathi+anchor,1)

# -----------------------------------------------------------------------------
# Clean language mode: English is English; Nepali mode uses Nepali UI wording instead
# of English/Nepali mixtures. Official names/acronyms (BIPAD/DHM/GPS) remain proper nouns.
# -----------------------------------------------------------------------------
als=a.find('    private void applyLanguage(){');ale=a.find('    private String t(String ne,String en)',als)
if als<0 or ale<0: raise SystemExit('v0850 language anchors')
lang=r'''    private void applyLanguage(){ // V0850_LANGUAGE_CLEAN
        brandSub.setText(t("नेपाल • नदी • बाढी • चौबीसै घण्टा चेतावनी","Nepal • rivers • floods • 24/7 alerts"));langBtn.setText(t("अङ्ग्रेजी","नेपाली"));
        weatherText.setText(currentWeather.isEmpty()?t("निगरानी स्थान छान्नुहोस्","Choose a monitoring location"):currentWeather);weatherSupport.setText(t("स्थानीय मौसम + BIPAD/DHM को आधिकारिक नदी अवस्था","Local weather + official BIPAD/DHM river status"));
        if(!Double.isFinite(lat)){place.setText(t("📍 नेपालमा निगरानी स्थान छान्नुहोस्","📍 Choose a monitoring location in Nepal"));rainTiming.setText(t("हालको स्थान पाएपछि आगामी वर्षाको समय देखाइन्छ।","Rain timing appears after your location is available."));}
        mapTitle.setText(t("🇳🇵 नेपालको नदी नक्सा","🇳🇵 Nepal river map"));mapSub.setText(t("नदीको रङ आधिकारिक बाढी अवस्थाअनुसार बदलिन्छ; स्टेशनको बिन्दु उपलब्धताअनुसार देखिन्छ।","River-line colours follow official flood status; station dots show source availability."));mapHint.setText(t("🟢 उपलब्ध स्टेशन • ⚫ उपलब्ध छैन • 🔵 तपाईंको GPS","🟢 available station • ⚫ unavailable station • 🔵 your GPS"));
        nearTitle.setText(t("🌊 नजिकका नदी मापन केन्द्र","🌊 Nearby river stations"));nearSub.setText(t("तपाईंको स्थान नजिकका आधिकारिक नदी मापन केन्द्र","Official river stations near your location"));
        nationalTitle.setText(t("🏞️ जिल्ला अनुसार नदी अवस्था","🏞️ River status by district"));nationalSub.setText(t("जिल्ला छानेर आधिकारिक नदी मापन केन्द्र हेर्नुहोस्।","Choose a district to view official river stations."));
        newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));newsSub.setText(t("विश्वसनीय स्रोतका नयाँ समाचार","Recent stories from trusted sources"));privacyTitle.setText(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety"));privacySub.setText(t("स्थान, माइक्रोफोन र चेतावनीसम्बन्धी विवरण कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used."));if(districtPicker!=null&&selectedDistrict.isEmpty())districtPicker.setText(t("जिल्ला छान्नुहोस् ▾","Choose district ▾"));updateOutsideNotice();
    }

'''
a=a[:als]+lang+a[ale:]

# A few high-visibility mixed strings outside applyLanguage.
a=a.replace('t("जिल्ला data refresh हुँदैछ।","District data is refreshing.")','t("जिल्लाको विवरण अद्यावधिक हुँदैछ।","District data is refreshing.")')
a=a.replace('t("Official station भेटिएन।","No official station found.")','t("आधिकारिक स्टेशन भेटिएन।","No official station found.")')
a=a.replace('t("Live data अहिले पढ्न सकिनँ। फेरि प्रयास गर्नुहोस्।","Could not read live data right now. Try again.")','t("प्रत्यक्ष विवरण अहिले पढ्न सकिनँ। फेरि प्रयास गर्नुहोस्।","Could not read live data right now. Try again.")')
a=a.replace('t("🔎 live data जाँच्दैछु…","🔎 Checking live data…")','t("🔎 प्रत्यक्ष विवरण जाँच्दैछु…","🔎 Checking live data…")')
a=a.replace('t("BIPAD official • पछिल्लो १० दिन • "+fi+" घटना","BIPAD official • last 10 days • "+fi+" incidents")','t("BIPAD आधिकारिक • पछिल्लो १० दिन • "+fi+" घटना","BIPAD official • last 10 days • "+fi+" incidents")')
a=a.replace('t("अनुमानित संख्या देखाइँदैन। Official loss records मात्र।","No estimated counts. Official loss records only.")','t("अनुमानित संख्या देखाइँदैन। आधिकारिक क्षति अभिलेख मात्र देखाइन्छ।","No estimated counts. Official loss records only.")')

# -----------------------------------------------------------------------------
# Native map dot semantics: source-online is green even if the latest observation is
# older than 30 min; source-offline is black; GPS remains the existing blue layer.
# River risk overlays still read the separate `fresh` field.
# -----------------------------------------------------------------------------
cs=m.find('    private static final class StationDot {');ce=m.find('    private static final class RiverWay',cs)
if cs<0 or ce<0: raise SystemExit('v0850 StationDot anchors')
block=m[cs:ce]
if 'boolean fresh, online;' not in block:
    block=block.replace('boolean fresh;','boolean fresh, online;')
    if 'boolean fresh, online;' not in block:raise SystemExit('v0850 StationDot bool field')
m=m[:cs]+block+m[ce:]
read='            s.fresh = getBoolean(c, o, "fresh", false);'
if 's.online = getBoolean(c, o, "online", s.fresh);' not in m:
    if read not in m:raise SystemExit('v0850 readStation fresh anchor')
    m=m.replace(read,read+'\n            s.online = getBoolean(c, o, "online", s.fresh);',1)
old='                String g = s.fresh ? normalizeStage(s.stage) : "stale";'
new='                String g = s.online ? "normal" : "stale"; // V0850_MAP_AVAILABILITY_GROUP'
if old in m:m=m.replace(old,new,1)
elif 'V0850_MAP_AVAILABILITY_GROUP' not in m:raise SystemExit('v0850 stationGeo group anchor')
# v0849 already forces normal/status dot layers green and stale black. Reassert exact colours.
m=m.replace('circleColor("#111111"),circleOpacity(1.0f),circleRadius(4.8f)','circleColor("#000000"),circleOpacity(1.0f),circleRadius(5.0f)',1)
m=m.replace('circleColor("#16A34A"),circleOpacity(1.0f),circleRadius(4.8f)','circleColor("#16A34A"),circleOpacity(1.0f),circleRadius(5.0f)',1)
if 'circleColor("#0b7fd0")' not in m:raise SystemExit('v0850 GPS blue layer missing')

# Version bump.
g=g.replace('versionCode 69','versionCode 70',1).replace("versionName '0.8.49'","versionName '0.8.50'",1)
if 'versionCode 70' not in g or "versionName '0.8.50'" not in g:raise SystemExit('v0850 version bump')

for x in ['V0850_EXACT_SOURCE_COUNTS','V0850_BIPAD_PARITY_LOADER','V0850_ONLINE_SEPARATE_FRESH','V0850_DATUM_NORMALIZED','V0850_PARITY_UI','V0850_AVAILABILITY_DOT','V0850_SATHI_ALL_DATA','V0850_LANGUAGE_CLEAN']:
    if x not in a:raise SystemExit('v0850 activity marker missing '+x)
for x in ['V0850_MAP_AVAILABILITY_GROUP','s.online = getBoolean(c, o, "online", s.fresh);','circleColor("#0b7fd0")','V0848_FLOOD_COLOUR_PRIORITY']:
    if x not in m:raise SystemExit('v0850 map marker missing '+x)

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.50 exact 284/latest parity + green/black/blue dots + grounded SATHI + clean language PASS')
