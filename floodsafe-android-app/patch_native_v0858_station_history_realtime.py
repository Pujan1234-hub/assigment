from pathlib import Path
import re

root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=app/'NativeFullActivity.java'
m_path=app/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def replace_between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start anchor missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end anchor missing')
    return text[:i]+replacement+text[j:]

# v0.8.58: preserve old official readings for information, keep <=20m safety,
# reliable station detail taps, restore status colours, preserve 10s official polling.
parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;JSONObject f=r.optJSONObject("fields");
        double[] c=officialCoord(r);double la=c[0],lo=c[1];if(!Double.isFinite(la)||!Double.isFinite(lo)||!isNepal(la,lo))return null;
        double level=numDeep(r,f,"_lastWaterLevel","waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level"),
               warning=numDeep(r,f,"_lastWarningLevel","warningLevel","warning_level","warningThreshold","warning_threshold"),
               danger=numDeep(r,f,"_lastDangerLevel","dangerLevel","danger_level","dangerThreshold","danger_threshold"),
               elevation=numDeep(r,f,"elevation","stationElevation","station_elevation","altitude");
        long at=trustedRowTime(r);
        boolean online=r.optBoolean("_floodsafeOnline",!r.optBoolean("_floodsafeCatalogOnly",false));
        boolean hasObservation=Double.isFinite(level)&&at>0;
        boolean fresh=online&&hasObservation&&now-at<=20L*60L*1000L&&at-now<=5L*60L*1000L; // V0858_FRESH20_DISPLAY_OLD
        boolean datum=Double.isFinite(elevation)&&elevation>50&&Double.isFinite(level)&&Math.abs(level-elevation)<20 &&
                ((Double.isFinite(warning)&&Math.abs(warning-elevation)<25)||(Double.isFinite(danger)&&Math.abs(danger-elevation)<25));
        if(datum){level-=elevation;if(Double.isFinite(warning))warning-=elevation;if(Double.isFinite(danger))danger-=elevation;}
        String raw=strDeep(r,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level").toUpperCase(Locale.ROOT);
        String stage="unknown";int rank=4;
        if(hasObservation){
            if((raw.contains("DANGER")&&!raw.contains("BELOW DANGER"))||raw.contains("RED")||(Double.isFinite(danger)&&danger>0&&level>=danger)){stage="danger";rank=0;}
            else if((raw.contains("WARNING")&&!raw.contains("BELOW WARNING"))||raw.contains("ORANGE")||(Double.isFinite(warning)&&warning>0&&level>=warning)){stage="warning";rank=1;}
            else if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("RISING")||raw.contains("INCREASING")||raw.contains("YELLOW")){stage="alert";rank=2;}
            else{stage="normal";rank=3;}
        }
        if(!online){if(raw.isEmpty())raw="NOT IN LATEST SOURCE";rank=4;} // V0858_KEEP_LAST_OFFICIAL
        String name=strDeep(r,f,"river_name","riverName","station_name","stationName","title","name");if(name.isEmpty())name="Official river station";
        String district=v848DistrictName(la,lo,strDeep(r,f,"districtName","district_name","district"));
        return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);
    }

'''
a=replace_between(a,'    private RiverStation parseStation(JSONObject r,long now){','    private String v848DistrictName(',parse,'v0858 parseStation')

detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        boolean hasReading=Double.isFinite(s.level)&&s.at>0;
        StringBuilder b=new StringBuilder();
        b.append(s.fresh?v0857StatusDot(s):"⚪").append(" ").append(s.fresh?stageName(s.stage):t("पुरानो/अप्रत्यक्ष मापन","STALE / NOT LIVE"));
        b.append("\n").append(t("स्रोत अवस्था: ","Source status: ")).append(s.online?t("पछिल्लो स्रोतमा उपलब्ध","available in latest source"):t("पछिल्लो स्रोतमा उपलब्ध छैन","not in latest source"));
        if(hasReading){
            b.append("\n\n").append(t("अन्तिम आधिकारिक पानीको सतह: ","Last official water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
            b.append("\n").append(t("मापन समय: ","Measurement time: ")).append(v848Time(s.at));
            b.append("\n").append(t("कति अघि: ","Age: ")).append(v850Age(s.at));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
            if(!s.fresh)b.append("\n\n").append(t("⚪ यो पुरानो आधिकारिक मापन हो। २० मिनेटभन्दा पुरानो मापनलाई प्रत्यक्ष जोखिम/आपतकालीन चेतावनीका लागि प्रयोग गरिँदैन।","⚪ This is an older official reading. Readings older than 20 minutes are not used for live risk or emergency alerts."));
        }else b.append("\n\n").append(t("यो स्टेशनको पुरानो आधिकारिक मापन उपलब्ध छैन।","No previous official measurement is available for this station."));
        b.append("\n\n").append(t("स्रोत: BIPAD/DHM आधिकारिक नदी मापन","Source: official BIPAD/DHM river measurement"));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0858_STATION_DETAIL_LAST_READING

'''
a=replace_between(a,'    private void showStation(RiverStation s){','    private void refreshHuman()',detail,'v0858 showStation')

if 'main.postDelayed(this,10_000L);' not in a: raise SystemExit('v0858 official 10-second foreground poll missing')

colour=r'''    private void v849AvailabilityDotColours(){
        if(!styleReady||style==null)return;
        try{CircleLayer x=style.getLayerAs("fs-stale-layer");if(x!=null)x.setProperties(circleColor("#8e99a5"),circleOpacity(0.96f),circleRadius(5.2f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-normal-layer");if(x!=null)x.setProperties(circleColor("#2d8cff"),circleOpacity(1.0f),circleRadius(5.3f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-alert-layer");if(x!=null)x.setProperties(circleColor("#ffc928"),circleOpacity(1.0f),circleRadius(5.7f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-warning-layer");if(x!=null)x.setProperties(circleColor("#ff8a1f"),circleOpacity(1.0f),circleRadius(6.1f));}catch(Exception ignored){}
        try{CircleLayer x=style.getLayerAs("fs-danger-layer");if(x!=null)x.setProperties(circleColor("#f22f4b"),circleOpacity(1.0f),circleRadius(6.5f));}catch(Exception ignored){}
    } // V0858_STATUS_COLOURS_NO_GREEN_OVERRIDE

'''
m=replace_between(m,'    private void v849AvailabilityDotColours(){','    private void refreshUserSource()',colour,'v0858 status colours')

# Robustly replace whatever station-threshold expression prior map patches left behind.
pat=r'double\s+stationThreshold\s*=\s*[^;]+;'
repl='double stationThreshold = v0858StationTapRadiusKm(p.getLatitude(), zoom); // V0858_STATION_TAP_TARGET'
m,n=re.subn(pat,repl,m,count=1)
if n!=1 and 'V0858_STATION_TAP_TARGET' not in m: raise SystemExit('v0858 station tap threshold anchor missing')

if 'private static double v0858StationTapRadiusKm(' not in m:
    anchor='    private StationDot nearestStation(double la, double lo) {'
    helper=r'''    private static double v0858StationTapRadiusKm(double lat,double zoom){
        double kmPerPixel=156.54303392*Math.max(0.35,Math.cos(Math.toRadians(lat)))/Math.pow(2.0,zoom);
        return Math.max(0.25,Math.min(12.0,kmPerPixel*22.0));
    } // V0858_STATION_TAP_RADIUS

'''
    if anchor not in m: raise SystemExit('v0858 nearestStation anchor missing')
    m=m.replace(anchor,helper+anchor,1)

if 'versionCode 77' in g:g=g.replace('versionCode 77','versionCode 78',1)
elif 'versionCode 78' not in g:raise SystemExit('v0858 versionCode anchor missing')
if "versionName '0.8.57'" in g:g=g.replace("versionName '0.8.57'","versionName '0.8.58'",1)
elif "versionName '0.8.58'" not in g:raise SystemExit('v0858 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for needle in ['V0858_FRESH20_DISPLAY_OLD','V0858_KEEP_LAST_OFFICIAL','V0858_STATION_DETAIL_LAST_READING','main.postDelayed(this,10_000L);','RIVER_FRESH_MS=20L*60L*1000L','V0857_FLOATING_LANGUAGE','V0857_NEARBY_GPS_TRUTH']:
    if needle not in a:raise SystemExit('v0858 activity verification failed: '+needle)
for needle in ['V0858_STATUS_COLOURS_NO_GREEN_OVERRIDE','V0858_STATION_TAP_TARGET','V0858_STATION_TAP_RADIUS']:
    if needle not in m:raise SystemExit('v0858 map verification failed: '+needle)
for needle in ['versionCode 78',"versionName '0.8.58'"]:
    if needle not in g:raise SystemExit('v0858 version verification failed: '+needle)
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0858 2 km fresh-only emergency guard changed')
print('FloodSafe v0.8.58 PASS: last official reading detail + relative age + reliable station tap + 10s source poll; 20m/2km safety unchanged')
