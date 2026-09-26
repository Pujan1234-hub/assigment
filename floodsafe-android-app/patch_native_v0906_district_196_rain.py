from pathlib import Path
import re

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
GRADLE = Path("floodsafe-android-app/app/build.gradle")
s = UI.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

def replace_once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {n}")
    s = s.replace(old, new, 1)

def sub_once(pattern, new, label):
    global s
    # Use a callable replacement so Java escape sequences such as "\\n" stay literal.
    s2, n = re.subn(pattern, lambda _m: new, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {n}")
    s = s2

replace_once(
    '        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o))return null;',
    '        if(!Double.isFinite(a)||!Double.isFinite(o)||!isNepal(a,o)){a=Double.NaN;o=Double.NaN;} // V0906_KEEP_UNMAPPABLE_OFFICIAL_ROW',
    'retain all official rows'
)

replace_once(
    'nationalTitle.setText(t("🌊 ७७ जिल्ला — सबै official नदी स्टेशन","🌊 77 districts — official river stations"));nationalSub.setText(t("Latest official reading; stale data लाई live खतरा मानिँदैन।","Latest official readings; stale data is not treated as a live threat."));',
    'nationalTitle.setText(t("🌊 जिल्ला अनुसार official नदी स्टेशन","🌊 Official river stations by district"));nationalSub.setText(t("जिल्लाको नामभित्र त्यही जिल्लाका खोला/नदी स्टेशन देखिन्छन्। पुरानो data लाई live खतरा मानिँदैन।","Open each district to see its river stations. Stale data is not treated as a live threat."));',
    'district title'
)

replace_once(
    'Button more=smallButton(t("सबै स्टेशन देखाउनुहोस्","Show all stations"));more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम देखाउनुहोस्","Show less"):t("सबै स्टेशन देखाउनुहोस्","Show all stations"));refreshRiverUi();});',
    'Button more=smallButton(t("सबै जिल्ला देखाउनुहोस्","Show all districts"));more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम जिल्ला देखाउनुहोस्","Show fewer districts"):t("सबै जिल्ला देखाउनुहोस्","Show all districts"));refreshRiverUi();});',
    'district more button'
)

grouped = r'''    private void refreshRiverUi(){
        if(nearList==null)return;
        List<RiverStation> copy;
        synchronized(stations){copy=new ArrayList<>(stations);}
        map.setStations(copy,lat,lon);
        int d=0,w=0,a=0,n=0,stale=0;
        for(RiverStation s:copy){switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}}
        stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("ताजा: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • पुरानो/अज्ञात "+stale,"Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale));
        nationalFresh.setText(feedFresh.getText());
        updateRisk(copy);
        nearList.removeAllViews();
        List<RiverStation> near=new ArrayList<>(copy);
        near.sort(Comparator.comparingDouble(this::stationDistanceForSort));
        int nearShown=0;
        for(RiverStation s:near){
            if(!Double.isFinite(stationDistanceForSort(s)))continue;
            nearList.addView(stationRow(s));
            if(++nearShown>=8)break;
        }
        if(nearShown==0)nearList.addView(empty(t("नेपालमा GPS location लिएपछि नजिकका station देखिन्छन्।","Nearby stations appear after a Nepal GPS location is available.")));
        renderDistrictStationGroups(copy);
    } // V0906_DISTRICT_GROUPED_STATIONS

    private double stationDistanceForSort(RiverStation s){
        if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))return Double.POSITIVE_INFINITY;
        double d=distanceKm(s.lat,s.lon);
        return Double.isFinite(d)?d:Double.POSITIVE_INFINITY;
    }

    private void renderDistrictStationGroups(List<RiverStation> source){
        nationalList.removeAllViews();
        List<RiverStation> ordered=new ArrayList<>(source);
        ordered.sort((x,y)->{
            int c=districtLabel(x).compareToIgnoreCase(districtLabel(y));
            if(c!=0)return c;
            c=Integer.compare(x.rank,y.rank);
            if(c!=0)return c;
            return stationDisplayName(x).compareToIgnoreCase(stationDisplayName(y));
        });
        java.util.LinkedHashMap<String,List<RiverStation>> groups=new java.util.LinkedHashMap<>();
        for(RiverStation s:ordered)groups.computeIfAbsent(districtLabel(s),k->new ArrayList<>()).add(s);
        int districtLimit=showAllStations?groups.size():Math.min(10,groups.size());
        int shown=0;
        for(java.util.Map.Entry<String,List<RiverStation>> e:groups.entrySet()){
            if(shown++>=districtLimit)break;
            nationalList.addView(districtGroupView(e.getKey(),e.getValue(),showAllStations));
        }
        if(groups.isEmpty())nationalList.addView(empty(t("Official नदी स्टेशन data आउँदैछ…","Official river station data is loading…")));
        else if(!showAllStations&&groups.size()>districtLimit){
            nationalList.addView(empty(t("अझ "+(groups.size()-districtLimit)+" जिल्ला तलको बटनबाट खोल्न सकिन्छ।","Use the button below to show "+(groups.size()-districtLimit)+" more districts.")));
        }
    }

    private View districtGroupView(String district,List<RiverStation> rows,boolean expanded){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(10),dp(9),dp(10),dp(6));
        String strongest="unknown";int best=99,d=0,w=0,a=0,n=0,stale=0;
        for(RiverStation s:rows){
            if(s.rank<best){best=s.rank;strongest=s.stage;}
            switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}
        }
        box.setBackground(round(stageBg(strongest),19,Color.rgb(207,226,237),1));
        String summary=stageDot(strongest)+"  "+district+"  •  "+rows.size()+t(" स्टेशन"," stations")
                +"   🔴"+d+" 🟠"+w+" 🟡"+a+" 🔵"+n+(stale>0?" ⚪"+stale:"");
        TextView head=text(summary,15,true,Color.rgb(20,46,72));head.setPadding(dp(4),dp(2),dp(4),dp(8));box.addView(head);
        int rowLimit=expanded?rows.size():Math.min(6,rows.size());
        for(int i=0;i<rowLimit;i++)box.addView(stationRow(rows.get(i)));
        if(rowLimit<rows.size()){
            TextView more=text(t("＋ यस जिल्लाका बाँकी "+(rows.size()-rowLimit)+" स्टेशन “सबै जिल्ला” खोलेपछि देखिन्छन्।","＋ "+(rows.size()-rowLimit)+" more stations in this district are shown in “Show all districts”."),11,true,Color.rgb(76,111,136));
            more.setPadding(dp(8),dp(3),dp(8),dp(5));box.addView(more);
        }
        LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(10));box.setLayoutParams(p);return box;
    }

    private String districtLabel(RiverStation s){
        String d=s==null?"":s.district;
        if(d!=null){d=d.trim();if(!d.isEmpty()&&!"null".equalsIgnoreCase(d))return d;}
        return t("जिल्ला नखुलेको","District unavailable");
    }

    private String stationDisplayName(RiverStation s){
        if(s==null)return "";
        String rn=s.riverName==null?"":s.riverName.trim(), sn=s.name==null?"":s.name.trim();
        if(rn.isEmpty())return sn;
        if(sn.isEmpty())return rn;
        String a=rn.toLowerCase(Locale.ROOT),b=sn.toLowerCase(Locale.ROOT);
        return b.contains(a)?sn:rn+" — "+sn;
    }

    private View stationRow(RiverStation s){TextView v=text(stageDot(s.stage)+"  "+stationDisplayName(s)+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(stageBg(s.stage),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
'''
sub_once(r'    private void refreshRiverUi\(\)\{.*?    private View stationRow\(RiverStation s\)\{.*?\n', grouped + '\n', 'district grouped river UI')

replace_once(
    'private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☀ सफा • ☁ खैरो/गाढा = बादल • 🌧 निलो = वर्षा","☀ clear • ☁ grey/dark = cloud • 🌧 blue = rain"):t("☁ मौसम तह बन्द","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));} // V0905_WEATHER_AREA_LEGEND',
    'private void updateWeatherLayerUi(){if(weatherLayerButton!=null)weatherLayerButton.setText(weatherOverlayEnabled?t("☁ तह बन्द","☁ Layer off"):t("☁ तह खोल","☁ Layer on"));if(weatherLayerStatus!=null)weatherLayerStatus.setText((weatherOverlayEnabled?t("☀ सफा • ☁ बादल क्षेत्र • 🌧 चलिरहेको वर्षा animation","☀ clear • ☁ cloud field • 🌧 animated rain"):t("☁ मौसम तह बन्द","☁ Weather layer OFF"))+(districtWeatherAt>0?" • "+weatherAge():""));} // V0906_ADVANCED_RAIN_LEGEND',
    'advanced rain legend'
)

if "versionCode 22" not in g or "versionName '0.9.05-bipad-latest-cloud-area'" not in g:
    raise SystemExit("v0.9.05 version markers missing")
g=g.replace("versionCode 22","versionCode 23",1)
g=g.replace("versionName '0.9.05-bipad-latest-cloud-area'","versionName '0.9.06-district-196-rain'",1)

assert "V0906_KEEP_UNMAPPABLE_OFFICIAL_ROW" in s
assert "V0906_DISTRICT_GROUPED_STATIONS" in s
assert "V0906_ADVANCED_RAIN_LEGEND" in s
assert "android.webkit.WebView" not in s
UI.write_text(s,encoding="utf-8")
GRADLE.write_text(g,encoding="utf-8")
print("V0906_DISTRICT_196_RAIN_PATCH_OK")
