from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')

if 'V0902_BIPAD_TRUTH_DISTRICT_POPUP' in s:
    print('v0.9.02 activity truth/UI patch already applied')
    raise SystemExit(0)

def method_span(text,name):
    pat=re.compile(r'(?m)^\s*(?:@Override\s+)?(?:private|public|protected)?\s+(?:static\s+)?[^\n{;]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^\{]+)?\{')
    m=pat.search(text)
    if not m: return None
    op=text.find('{',m.start())
    depth=0; quote=None; esc=False
    for i in range(op,len(text)):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
        else:
            if ch in ('"',"'"): quote=ch
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return m.start(),i+1
    return None

def replace_method(text,name,block):
    sp=method_span(text,name)
    if not sp: raise SystemExit('Missing method '+name)
    return text[:sp[0]]+block+text[sp[1]:]

def insert_before(text,name,block,marker):
    if marker in text:return text
    sp=method_span(text,name)
    if not sp:raise SystemExit('Missing anchor '+name)
    return text[:sp[0]]+block+text[sp[0]:]

# Fields/state.
anchor='    private boolean showAllStations=false;\n'
if anchor not in s: raise SystemExit('state anchor missing')
s=s.replace(anchor,anchor+'''    private Button districtButton;\n    private String selectedDistrict="";\n    private int catalogCount=0,directBipadCount=0,latestReadingCount=0,currentReadingCount=0;\n    private boolean directBipadOk=false;\n    private String riverTruthSource="";\n    private static final long FOREGROUND_RIVER_REFRESH_MS=5L*60L*1000L;\n''',1)

# Foreground refresh only while visible; WorkManager remains the background cadence.
anchor='    @Override protected void onNewIntent(Intent i){super.onNewIntent(i);setIntent(i);consumeSathiIntent(i);}\n'
if anchor not in s: raise SystemExit('onNewIntent anchor missing')
s=s.replace(anchor,anchor+'''\n    private final Runnable foregroundRiverRefresh=new Runnable(){@Override public void run(){if(!isFinishing()){refreshRivers();main.postDelayed(this,FOREGROUND_RIVER_REFRESH_MS);}}};\n    @Override protected void onStart(){super.onStart();main.removeCallbacks(foregroundRiverRefresh);main.postDelayed(foregroundRiverRefresh,FOREGROUND_RIVER_REFRESH_MS);}\n    @Override protected void onStop(){main.removeCallbacks(foregroundRiverRefresh);super.onStop();}\n''',1)

national=r'''    private View nationalCard(){
        LinearLayout c=card();
        nationalTitle=text("",20,true,Color.rgb(16,39,70));
        nationalSub=text("",12,true,Color.rgb(100,130,151));
        nationalFresh=text("",12,true,Color.rgb(100,130,151));
        c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);
        districtButton=smallButton(t("🇳🇵 ७७ जिल्ला – Official River Stations","🇳🇵 77 Districts – Official River Stations"));
        districtButton.setOnClickListener(v->showDistrictSelector());
        c.addView(districtButton,lp(-1,dp(50),0,dp(10),0,dp(8)));
        nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);
        c.addView(nationalList,lp(-1,-2,0,dp(4),0,dp(8)));
        Button more=smallButton(t("सबै स्टेशन देखाउनुहोस्","Show all stations"));
        more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम देखाउनुहोस्","Show less"):t("सबै स्टेशन देखाउनुहोस्","Show all stations"));refreshRiverUi();});
        c.addView(more);return c;
    } // V0902_77_DISTRICT_SELECTOR
'''
s=replace_method(s,'nationalCard',national)

refresh=r'''    private void refreshRivers(){
        feedFresh.setText(t("Official BIPAD नदी अवस्था refresh हुँदैछ…","Refreshing official BIPAD river status…"));
        io.execute(()->{
            try{
                OfficialRiverData.Snapshot snap=OfficialRiverData.fetch();
                JSONArray rows=snap.rows;
                List<RiverStation> out=new ArrayList<>();
                long now=System.currentTimeMillis();
                int latest=0,current=0;
                for(int i=0;i<rows.length();i++){
                    RiverStation st=parseStation(rows.optJSONObject(i),now);
                    if(st==null)continue;
                    out.add(st);
                    if(st.at>0)latest++;
                    if(st.fresh)current++;
                }
                out.sort(Comparator.comparingInt((RiverStation st)->st.rank).thenComparingDouble(st->distanceKm(st.lat,st.lon)));
                synchronized(stations){stations.clear();stations.addAll(out);}
                catalogCount=snap.catalogCount>0?snap.catalogCount:out.size();
                directBipadCount=snap.directBipadCount;
                directBipadOk=snap.directBipadOk;
                latestReadingCount=latest;
                currentReadingCount=current;
                riverTruthSource=snap.source;
                android.util.Log.i("FloodSafeTruth","catalog="+catalogCount+" merged="+out.size()+" bipad_rows="+directBipadCount
                        +" latest_readings="+latestReadingCount+" current="+currentReadingCount+" source="+riverTruthSource);
                runOnUiThread(this::refreshRiverUi);
            }catch(Exception e){
                android.util.Log.e("FloodSafeTruth","river_refresh_failed",e);
                runOnUiThread(()->feedFresh.setText(t("River data refresh हुन सकेन • stale लाई live भनिएको छैन","River refresh failed • stale data is not live")));
            }
        });
    } // V0902_BIPAD_PRIMARY_MIRROR_BACKUP
'''
s=replace_method(s,'refreshRivers',refresh)

parse=r'''    private RiverStation parseStation(JSONObject r,long now){
        if(r==null)return null;
        double a=num(r,"latitude","lat","stationLatitude","station_latitude"),o=num(r,"longitude","lon","lng","stationLongitude","station_longitude");
        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;
        double level=num(r,"waterLevel","water_level","currentWaterLevel","current_water_level","currentLevel","current_level","level","value","_lastWaterLevel"),
                warning=num(r,"warningLevel","warning_level","warningThreshold","warning_threshold","_lastWarningLevel"),
                danger=num(r,"dangerLevel","danger_level","dangerThreshold","danger_threshold","_lastDangerLevel");
        long at=OfficialRiverData.observationTime(r);
        boolean fresh=OfficialRiverData.isCurrent(at,now);
        String stage=OfficialRiverData.stage(r,fresh);
        int rank=OfficialRiverData.rank(stage);
        String stationId=str(r,"stationSeriesId","station_series_id","stationId","station_id","stationIndex","station_index","seriesId","series_id","id");
        String riverName=str(r,"river_name","riverName","river");
        String name=str(r,"station_name","stationName","title","name");
        if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";
        String district=str(r,"districtName","district_name","district");
        String basin=str(r,"basinName","basin_name","basin");
        return new RiverStation(stationId,name,riverName,district,basin,a,o,level,warning,danger,at,fresh,stage,rank);
    } // V0902_OFFICIAL_STATUS_FIRST_OBSERVATION_TIME_ONLY
'''
s=replace_method(s,'parseStation',parse)

ui=r'''    private void refreshRiverUi(){
        if(nearList==null)return;
        List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        if(map!=null){map.setDistrictFilter(selectedDistrict);map.setStations(copy,lat,lon);}
        int d=0,w=0,a=0,n=0,stale=0;
        for(RiverStation st:copy){switch(st.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}}
        stationCount.setText(String.valueOf(catalogCount>0?catalogCount:copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        String parity=(directBipadOk?" • BIPAD rows "+directBipadCount:" • BIPAD direct unavailable, safe cache fallback");
        feedFresh.setText(t("Catalog "+(catalogCount>0?catalogCount:copy.size())+" • latest "+latestReadingCount+" • current "+currentReadingCount+"\n🟢 "+n+"  🟡 "+a+"  🟠 "+w+"  🔴 "+d+" • stale/no-current "+stale+parity,
                "Catalog "+(catalogCount>0?catalogCount:copy.size())+" • latest "+latestReadingCount+" • current "+currentReadingCount+"\n🟢 "+n+"  🟡 "+a+"  🟠 "+w+"  🔴 "+d+" • stale/no-current "+stale+parity));
        nationalFresh.setText(feedFresh.getText());
        updateRisk(copy);
        List<RiverStation> filtered=new ArrayList<>();
        for(RiverStation st:copy)if(selectedDistrict.isEmpty()||sameDistrict(selectedDistrict,st.district))filtered.add(st);
        nearList.removeAllViews();List<RiverStation> near=new ArrayList<>(filtered);near.sort(Comparator.comparingDouble(st->distanceKm(st.lat,st.lon)));
        int nearShown=Math.min(8,near.size());for(int i=0;i<nearShown;i++)nearList.addView(stationRow(near.get(i)));
        if(nearShown==0)nearList.addView(empty(selectedDistrict.isEmpty()?t("नेपालमा GPS location लिएपछि नजिकका station देखिन्छन्।","Nearby stations appear after a Nepal GPS location is available."):t("यो जिल्लामा official river station भेटिएन।","No official river station is listed for this district.")));
        nationalList.removeAllViews();int max=showAllStations?filtered.size():Math.min(24,filtered.size());for(int i=0;i<max;i++)nationalList.addView(stationRow(filtered.get(i)));
        if(max==0)nationalList.addView(empty(t("यो जिल्लामा station उपलब्ध छैन।","No station is available for this district.")));
        if(districtButton!=null)districtButton.setText(selectedDistrict.isEmpty()?t("🇳🇵 ७७ जिल्ला – सबै नेपाल","🇳🇵 77 Districts – All Nepal"):"📍 "+selectedDistrict+" • "+filtered.size()+" stations");
        android.util.Log.i("FloodSafeTruth","ui current normal="+n+" alert="+a+" warning="+w+" danger="+d+" stale="+stale+" selectedDistrict="+(selectedDistrict.isEmpty()?"ALL":selectedDistrict));
    } // V0902_COUNTERS_AND_DISTRICT_FILTER
'''
s=replace_method(s,'refreshRiverUi',ui)

line=r'''    private String stationLine(RiverStation s){
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—";
        double d=distanceKm(s.lat,s.lon);
        String distance=Double.isFinite(d)?String.format(Locale.US," • station %.1f km",d):"";
        if(s.fresh){
            long ageMs=s.at>0?Math.max(0,System.currentTimeMillis()-s.at):-1L;
            String age=ageMs<0?t("official time उपलब्ध छैन","official time unavailable"):
                    ageMs<60L*60L*1000L?(ageMs/60000L)+" min ago":(ageMs/(60L*60L*1000L))+" hr ago";
            return t("Current official reading","Current official reading")+" • "+lev+" • "+age+distance;
        }
        String stamp=s.at>0?officialTime(s.at):t("official date/time उपलब्ध छैन","official date/time unavailable");
        return t("Historical / last known reading","Historical / last known reading")+" • "+lev+" • "+stamp+distance;
    } // V0902_NO_CONTRADICTORY_STALE_AGE
'''
s=replace_method(s,'stationLine',line)

show=r'''    private void showStation(RiverStation s){
        StringBuilder b=new StringBuilder();
        b.append(s.fresh?stageDot(s.stage)+" "+stageName(s.stage)+" • CURRENT official":"⚪ "+t("Historical / last known reading","HISTORICAL / last known reading"));
        if(!s.stationId.isEmpty())b.append("\nStation ID: ").append(s.stationId);
        if(!s.riverName.isEmpty())b.append("\nRiver: ").append(s.riverName);
        if(!s.district.isEmpty())b.append("\nDistrict: ").append(s.district);
        if(!s.basin.isEmpty())b.append("\nBasin: ").append(s.basin);
        b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.2f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.2f m",s.danger));
        b.append("\nOfficial observation: ").append(s.at>0?officialTime(s.at):"—");
        if(!s.fresh)b.append("\n\n").append(t("यो historical reading warning colour वा alarm मा प्रयोग हुँदैन।","This historical reading is not used for warning colours or alarms."));
        String rainDetail=DhmRainMirror.detailFor(s.name,s.riverName,s.district,s.basin,s.lat,s.lon);
        b.append("\n\n").append(rainDetail!=null?rainDetail:t("No safely matched fresh official rainfall reading available.","No safely matched fresh official rainfall reading available."));
        b.append("\n\nSource: BIPAD / DHM");
        showScrollableDetail(s.name,b.toString());
    } // V0902_SCROLLABLE_STATION_DETAIL_RAIN
'''
s=replace_method(s,'showStation',show)

helpers=r'''    private String officialTime(long at){
        if(at<=0)return "—";
        try{return java.time.Instant.ofEpochMilli(at).atZone(java.time.ZoneId.of("Asia/Kathmandu")).format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss 'NPT'"));}
        catch(Exception e){return String.valueOf(at);}
    }

    private void showScrollableDetail(String title,String message){
        ScrollView sv=new ScrollView(this);sv.setFillViewport(false);sv.setClipToPadding(false);sv.setPadding(dp(18),dp(8),dp(18),dp(8));
        TextView body=text(message,14,false,Color.rgb(30,52,72));body.setTextIsSelectable(true);body.setSingleLine(false);body.setHorizontallyScrolling(false);body.setPadding(0,0,0,dp(8));
        sv.addView(body,new ScrollView.LayoutParams(-1,-2));
        int screenH=getResources().getDisplayMetrics().heightPixels;
        int maxH=Math.min((int)(screenH*0.64f),dp(620));
        sv.setLayoutParams(new LinearLayout.LayoutParams(-1,maxH));
        AlertDialog d=new AlertDialog.Builder(this).setTitle(title).setView(sv).setPositiveButton(t("ठीक छ","OK"),null).create();
        d.setOnShowListener(x->{if(d.getButton(AlertDialog.BUTTON_POSITIVE)!=null)d.getButton(AlertDialog.BUTTON_POSITIVE).setAllCaps(false);android.util.Log.i("FloodSafeDialog","scroll_dialog_shown maxHeight="+maxH+" title="+title);});
        d.show();
    } // V0902_RESPONSIVE_SCROLL_DIALOG

    private List<String> districtNames(){
        java.util.TreeSet<String> names=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        try{
            JSONObject root=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=root.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i),pr=f==null?null:f.optJSONObject("properties");if(pr==null)continue;String n=pr.optString("nameEn","").trim();if(!n.isEmpty())names.add(n);}
        }catch(Exception e){android.util.Log.e("FloodSafeDistrict","district inventory failed",e);}
        android.util.Log.i("FloodSafeDistrict","district_selector_count="+names.size());
        return new ArrayList<>(names);
    }

    private void showDistrictSelector(){
        List<String> districts=districtNames();
        String[] items=new String[districts.size()+1];items[0]=t("🇳🇵 सबै नेपाल","🇳🇵 All Nepal");for(int i=0;i<districts.size();i++)items[i+1]=districts.get(i);
        new AlertDialog.Builder(this).setTitle(t("७७ जिल्ला – Official River Stations","77 Districts – Official River Stations"))
                .setItems(items,(dialog,which)->{selectedDistrict=which==0?"":districts.get(which-1);if(map!=null){map.setDistrictFilter(selectedDistrict);if(selectedDistrict.isEmpty())map.resetView();else map.focusDistrict(selectedDistrict);}refreshRiverUi();})
                .setNegativeButton(t("बन्द","Close"),null).show();
    }

    private static boolean sameDistrict(String a,String b){
        if(a==null||b==null)return false;String x=a.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]","");String y=b.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\p{L}]","");return !x.isEmpty()&&x.equals(y);
    }

'''
s=insert_before(s,'refreshHuman',helpers,'V0902_RESPONSIVE_SCROLL_DIALOG')

# Apply language should keep selector label in sync.
old='newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));privacyTitle.setText'
new='if(districtButton!=null)districtButton.setText(selectedDistrict.isEmpty()?t("🇳🇵 ७७ जिल्ला – सबै नेपाल","🇳🇵 77 Districts – All Nepal"):"📍 "+selectedDistrict);newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));privacyTitle.setText'
if old not in s: raise SystemExit('language selector anchor missing')
s=s.replace(old,new,1)

# Normal/current station must be green; user GPS remains blue in MapView.
s=s.replace('case"normal":return Color.rgb(45,140,255);default:return Color.rgb(113,139,155);','case"normal":return Color.rgb(39,166,91);default:return Color.rgb(113,139,155);',1)
s=s.replace('case"normal":return"🔵";default:return"⚪";','case"normal":return"🟢";default:return"⚪";',1)

# RiverStation carries basin for safe rainfall matching.
old_re=r'    private static final class RiverStation\{[^\n]+\}\n'
m=re.search(old_re,s)
if not m: raise SystemExit('RiverStation class anchor missing')
new_class='''    private static final class RiverStation{final String stationId,name,riverName,district,basin,stage;final double lat,lon,level,warning,danger;final long at;final boolean fresh;final int rank;RiverStation(String id,String n,String rn,String di,String ba,double a,double o,double l,double w,double d,long tm,boolean f,String st,int r){stationId=id==null?"":id;name=n;riverName=rn==null?"":rn;district=di==null?"":di;basin=ba==null?"":ba;lat=a;lon=o;level=l;warning=w;danger=d;at=tm;fresh=f;stage=st;rank=r;}}\n'''
s=s[:m.start()]+new_class+s[m.end():]

# Marker used by source/runtime gates.
s=s.replace('/** V0899_STALE_CURRENT_SEMANTICS — Full native Android FloodSafe UI. No WebView is used. */','/** V0899_STALE_CURRENT_SEMANTICS — Full native Android FloodSafe UI. No WebView is used. */\n// V0902_BIPAD_TRUTH_DISTRICT_POPUP',1)

p.write_text(s,encoding='utf-8')
print('FloodSafe v0.9.02 activity patch PASS: BIPAD-first truth, green normals, district selector, scroll dialog, truthful nearby wording')
