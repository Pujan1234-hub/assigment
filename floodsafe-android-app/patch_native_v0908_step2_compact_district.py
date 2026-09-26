from pathlib import Path
import re

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
s = UI.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, got {n}")
    s = s.replace(old, new, 1)


def sub_once(pattern, new, label):
    global s
    s2, n = re.subn(pattern, lambda _m: new, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 regex match, got {n}")
    s = s2

replace_once(
    '    private JSONObject v0907DistrictGeometry;\n    private final java.util.Map<String,String> v0907DistrictNameCache=new java.util.HashMap<>();',
    '    private JSONObject v0907DistrictGeometry;\n    private final java.util.Map<String,String> v0907DistrictNameCache=new java.util.HashMap<>();\n    private String v0908SelectedDistrict="";\n    private Button v0908DistrictPicker;',
    'compact district state'
)

new_national = r'''    private View nationalCard(){
        LinearLayout c=card();
        nationalTitle=text("",20,true,Color.rgb(16,39,70));
        nationalSub=text("",12,true,Color.rgb(100,130,151));
        nationalFresh=text("",12,true,Color.rgb(100,130,151));
        c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);
        v0908DistrictPicker=smallButton(t("📍 जिल्ला छान्नुहोस्","📍 Choose district"));
        v0908DistrictPicker.setOnClickListener(v->v0908ShowDistrictPicker());
        c.addView(v0908DistrictPicker,lp(-1,dp(48),0,dp(9),0,0));
        nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);
        c.addView(nationalList,lp(-1,-2,0,dp(8),0,0));
        TextView districtHint=text(t("एउटा जिल्ला छान्दा त्यही जिल्लाका official नदी/खोला स्टेशन मात्र देखिन्छन्।","Choose one district to show only that district's official river stations."),11,true,Color.rgb(88,118,140));
        c.addView(districtHint);
        return c;
    } // V0908_COMPACT_DISTRICT_PICKER
'''
sub_once(r'    private View nationalCard\(\)\{.*?\n    private LinearLayout humanCard\(\)', new_national + '    private LinearLayout humanCard()', 'national card compact selector')

compact_methods = r'''    private void renderDistrictStationGroups(List<RiverStation> source){
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
        for(RiverStation st:ordered)groups.computeIfAbsent(districtLabel(st),k->new ArrayList<>()).add(st);

        if(!v0908SelectedDistrict.isEmpty()&&!groups.containsKey(v0908SelectedDistrict))v0908SelectedDistrict="";
        if(v0908SelectedDistrict.isEmpty()){
            if(v0908DistrictPicker!=null)v0908DistrictPicker.setText(t("📍 जिल्ला छान्नुहोस् • ","📍 Choose district • ")+groups.size()+t(" जिल्ला"," districts"));
            nationalList.addView(empty(t("माथिको जिल्ला बटन थिच्नुहोस् — लामो ७७-जिल्ला सूची अब यहाँ देखिँदैन।","Tap the district button above — the long district list is no longer shown here.")));
            return;
        }
        List<RiverStation> rows=groups.get(v0908SelectedDistrict);
        if(rows==null||rows.isEmpty()){
            v0908SelectedDistrict="";
            nationalList.addView(empty(t("यस जिल्लामा official नदी स्टेशन भेटिएन।","No official river station was found in this district.")));
            return;
        }
        if(v0908DistrictPicker!=null)v0908DistrictPicker.setText("📍 "+v0908SelectedDistrict+" • "+rows.size()+t(" स्टेशन"," stations")+"  ▾");
        nationalList.addView(v0908DistrictDetailView(v0908SelectedDistrict,rows));
    } // V0908_ONE_DISTRICT_ONLY

    private void v0908ShowDistrictPicker(){
        List<RiverStation> copy; synchronized(stations){copy=new ArrayList<>(stations);}
        java.util.TreeMap<String,List<RiverStation>> groups=new java.util.TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for(RiverStation st:copy)groups.computeIfAbsent(districtLabel(st),k->new ArrayList<>()).add(st);
        if(groups.isEmpty())return;
        List<String> names=new ArrayList<>(groups.keySet());
        String[] labels=new String[names.size()];
        for(int i=0;i<names.size();i++){String n=names.get(i);labels[i]=n+" • "+groups.get(n).size()+t(" स्टेशन"," stations");}
        new AlertDialog.Builder(this)
                .setTitle(t("जिल्ला छान्नुहोस्","Choose district"))
                .setItems(labels,(d,which)->{v0908SelectedDistrict=names.get(which);renderDistrictStationGroups(copy);})
                .setNegativeButton(t("बन्द","Close"),null)
                .show();
    }

    private View v0908DistrictDetailView(String district,List<RiverStation> rows){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(10),dp(9),dp(10),dp(8));
        String strongest="unknown";int best=99,d=0,w=0,a=0,n=0,stale=0;
        for(RiverStation st:rows){
            if(st.rank<best){best=st.rank;strongest=st.stage;}
            switch(st.stage){case"danger":d++;break;case"warning":w++;break;case"alert":a++;break;case"normal":n++;break;default:stale++;}
        }
        box.setBackground(round(stageBg(strongest),19,Color.rgb(207,226,237),1));
        String summary=stageDot(strongest)+"  "+district+"  •  "+rows.size()+t(" स्टेशन"," stations")
                +"   🔴"+d+" 🟠"+w+" 🟡"+a+" 🔵"+n+(stale>0?" ⚪"+stale:"");
        TextView head=text(summary,15,true,Color.rgb(20,46,72));head.setPadding(dp(5),dp(3),dp(5),dp(9));box.addView(head);
        for(RiverStation st:rows)box.addView(stationRow(st));
        return box;
    } // V0908_SELECTED_DISTRICT_DETAILS

'''
sub_once(r'    private void renderDistrictStationGroups\(List<RiverStation> source\)\{.*?(?=    private String districtLabel\(RiverStation st\))', compact_methods, 'replace long district accordion')

for marker in ["V0908_COMPACT_DISTRICT_PICKER","V0908_ONE_DISTRICT_ONLY","V0907_DISTRICT_NAMES_COLLAPSED"]:
    if marker not in s:
        raise SystemExit("missing marker: "+marker)
if 'android.webkit.WebView' in s:
    raise SystemExit('WebView introduced')
UI.write_text(s,encoding="utf-8")
print("V0908_STEP2_COMPACT_DISTRICT_OK")
