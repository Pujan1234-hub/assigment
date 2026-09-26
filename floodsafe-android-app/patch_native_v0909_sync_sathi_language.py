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
        raise SystemExit(f"{label}: expected one match, got {n}")
    s = s.replace(old, new, 1)

# Keep a list of simple static bilingual labels so they can be updated in-place without recreating Activity/MapLibre.
pairs=[]
seen=set()
for m in re.finditer(r't\("((?:\\.|[^"\\])*)","((?:\\.|[^"\\])*)"\)', s):
    pair=(m.group(1),m.group(2))
    if pair not in seen:
        seen.add(pair);pairs.append(pair)

replace_once('import android.widget.Button;\n', 'import android.widget.Button;\nimport android.widget.EditText;\n', 'EditText import')
replace_once('    private Button v0908DistrictPicker;', '    private Button v0908DistrictPicker;\n    private boolean v0909SkipMapUpdateOnce=false;', 'language map-preserve flag')

# Language toggle must NOT recreate Activity; keep current map camera, style, location and already-fetched data.
replace_once(
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();recreate();});',
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();v0909SkipMapUpdateOnce=true;applyLanguage();v0909TranslateStaticTree(root);refreshRiverUi();updateWeatherLayerUi();}); // V0909_FAST_LANGUAGE_NO_RECREATE',
    'fast language toggle')

# refreshRiverUi still re-renders text/status, but language-only refresh must not rebuild map layers.
replace_once('        map.setStations(copy,lat,lon);', '        if(v0909SkipMapUpdateOnce)v0909SkipMapUpdateOnce=false;else map.setStations(copy,lat,lon); // V0909_LANGUAGE_PRESERVE_MAP', 'skip map once')

# Foreground BIPAD parity refresh. Initial load remains immediate via refreshAll(); this mirrors later 196->195 / 195->196 changes while open.
replace_once('main.post(clockTick);main.postDelayed(weatherRefreshTick,5L*60L*1000L);', 'main.post(clockTick);main.postDelayed(weatherRefreshTick,5L*60L*1000L);main.postDelayed(v0909RiverRefreshTick,60L*1000L);', 'start river parity tick')
clock_anchor='    private final Runnable clockTick='
if clock_anchor not in s: raise SystemExit('clock runnable anchor missing')
s=s.replace(clock_anchor, '    private final Runnable v0909RiverRefreshTick=new Runnable(){@Override public void run(){refreshRivers();main.postDelayed(this,60L*1000L);}}; // V0909_BIPAD_FOREGROUND_PARITY\n'+clock_anchor, 1)

# 77-district picker must come from Nepal district geometry, not only districts represented by the current station rows.
replace_once('            if(v0908DistrictPicker!=null)v0908DistrictPicker.setText(t("📍 जिल्ला छान्नुहोस् • ","📍 Choose district • ")+groups.size()+t(" जिल्ला"," districts"));', '            if(v0908DistrictPicker!=null)v0908DistrictPicker.setText(t("📍 जिल्ला छान्नुहोस् • ","📍 Choose district • ")+v0909AllDistrictNames().size()+t(" जिल्ला"," districts"));', 'district picker count')
replace_once('        if(!v0908SelectedDistrict.isEmpty()&&!groups.containsKey(v0908SelectedDistrict))v0908SelectedDistrict="";\n', '', 'keep selected empty-station district')
replace_once('        List<RiverStation> rows=groups.get(v0908SelectedDistrict);\n        if(rows==null||rows.isEmpty()){\n            v0908SelectedDistrict="";\n            nationalList.addView(empty(t("यस जिल्लामा official नदी स्टेशन भेटिएन।","No official river station was found in this district.")));\n            return;\n        }\n        if(v0908DistrictPicker!=null)v0908DistrictPicker.setText("📍 "+v0908SelectedDistrict+" • "+rows.size()+t(" स्टेशन"," stations")+"  ▾");\n        nationalList.addView(v0908DistrictDetailView(v0908SelectedDistrict,rows));', '        List<RiverStation> rows=groups.get(v0908SelectedDistrict);if(rows==null)rows=new ArrayList<>();\n        if(v0908DistrictPicker!=null)v0908DistrictPicker.setText("📍 "+v0908SelectedDistrict+" • "+rows.size()+t(" स्टेशन"," stations")+"  ▾");\n        if(rows.isEmpty()){nationalList.addView(empty(t("यस जिल्लामा अहिले BIPAD River Watch मा official नदी स्टेशन छैन।","This district currently has no official station in BIPAD River Watch.")));return;}\n        nationalList.addView(v0908DistrictDetailView(v0908SelectedDistrict,rows)); // V0909_EMPTY_DISTRICT_VISIBLE', 'empty district selection')
replace_once('        if(groups.isEmpty())return;\n        List<String> names=new ArrayList<>(groups.keySet());\n        String[] labels=new String[names.size()];\n        for(int i=0;i<names.size();i++){String n=names.get(i);labels[i]=n+" • "+groups.get(n).size()+t(" स्टेशन"," stations");}', '        List<String> names=v0909AllDistrictNames();if(names.isEmpty())names=new ArrayList<>(groups.keySet());\n        String[] labels=new String[names.size()];\n        for(int i=0;i<names.size();i++){String n=names.get(i);List<RiverStation> rr=groups.get(n);labels[i]=n+" • "+(rr==null?0:rr.size())+t(" स्टेशन"," stations");}', 'all 77 district dialog')

helper = r'''    private List<String> v0909AllDistrictNames(){
        java.util.TreeSet<String> names=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        try{
            if(v0907DistrictGeometry==null){try{v0907DistrictGeometry=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");}catch(Exception e){v0907DistrictGeometry=assetJson("floodsafe-nepal/v24/nepal-districts.json");}}
            JSONArray fs=v0907DistrictGeometry.optJSONArray("features");
            if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i);JSONObject p=f==null?null:f.optJSONObject("properties");String n=p==null?"":p.optString("nameEn","").trim();if(!n.isEmpty())names.add(n);}
        }catch(Exception ignored){}
        return new ArrayList<>(names);
    } // V0909_ALL_77_DISTRICTS

'''
anchor='    private void v0908ShowDistrictPicker(){'
if anchor not in s: raise SystemExit('district picker method anchor missing')
s=s.replace(anchor, helper+anchor, 1)

# Restore typed SATHI interaction while keeping voice.
pattern=r'    private void showSathiDialog\(String initial\)\{.*?\}\n    private void startVoice'
new_sathi=r'''    private void showSathiDialog(String initial){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(8),dp(18),0);
        String intro=initial==null?t("मौसम, नदी, warning वा app status सोध्नुहोस्।","Ask about weather, rivers, warnings or app status."):t("तपाईं: ","You: ")+initial+"\n\nSATHI: "+answerSathi(initial);
        TextView answer=text(intro,14,false,Color.rgb(30,52,72));box.addView(answer);
        EditText input=new EditText(this);input.setHint(t("यहाँ प्रश्न लेख्नुहोस्…","Type your question here…"));input.setTextSize(14);input.setMinLines(2);input.setMaxLines(4);input.setPadding(dp(12),dp(10),dp(12),dp(10));input.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));box.addView(input,lp(-1,-2,0,dp(12),0,dp(8)));
        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
        Button ask=button(t("➤ सोध्नुहोस्","➤ Ask")),mic=button(t("🎙️ माइकबाट सोध्नुहोस्","🎙️ Ask by voice"));actions.addView(ask,new LinearLayout.LayoutParams(0,dp(52),1f));LinearLayout.LayoutParams mp=new LinearLayout.LayoutParams(0,dp(52),1f);mp.setMargins(dp(6),0,0,0);actions.addView(mic,mp);box.addView(actions);
        AlertDialog d=new AlertDialog.Builder(this).setTitle("🤖 SATHI").setView(box).setNegativeButton(t("बन्द","Close"),null).create();
        Runnable submit=()->{String q=input.getText().toString().trim();if(q.isEmpty())return;String a=answerSathi(q);answer.setText(t("तपाईं: ","You: ")+q+"\n\nSATHI: "+a);input.setText("");speak(a);};
        ask.setOnClickListener(v->submit.run());mic.setOnClickListener(v->startVoice(answer));d.show();
    } // V0909_SATHI_TEXT_AND_VOICE
    private void startVoice'''
s2,n=re.subn(pattern,lambda m:new_sathi,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'SATHI dialog replacement count={n}')
s=s2

# In-place translator for static TextViews/Buttons created during screen construction.
lines=[]
for ne,en in pairs:
    lines.append(f'            if(cur.equals("{ne}")||cur.equals("{en}")){{tv.setText(t("{ne}","{en}"));return;}}')
translator='''    private void v0909TranslateStaticTree(View v){\n        if(v==null)return;\n        if(v instanceof TextView){TextView tv=(TextView)v;String cur=String.valueOf(tv.getText());\n'''+"\n".join(lines)+'''\n        }\n        if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++)v0909TranslateStaticTree(g.getChildAt(i));}\n    } // V0909_IN_PLACE_LANGUAGE_TREE\n'''
t_anchor='    private String t(String ne,String en){return english?en:ne;}\n'
if t_anchor not in s: raise SystemExit('t() anchor missing')
s=s.replace(t_anchor,t_anchor+translator,1)

if "versionCode 25" not in g or "versionName '0.9.08-storm-events-compact-gauge'" not in g:
    raise SystemExit('v0.9.08 version marker missing')
g=g.replace('versionCode 25','versionCode 26',1)
g=g.replace("versionName '0.9.08-storm-events-compact-gauge'","versionName '0.9.09-live77-sathi-fastlang'",1)

for marker in ['V0909_FAST_LANGUAGE_NO_RECREATE','V0909_BIPAD_FOREGROUND_PARITY','V0909_ALL_77_DISTRICTS','V0909_SATHI_TEXT_AND_VOICE','V0909_IN_PLACE_LANGUAGE_TREE']:
    if marker not in s: raise SystemExit('missing marker '+marker)
if 'recreate();' in s: raise SystemExit('language recreate still present')
if 'android.webkit.WebView' in s: raise SystemExit('WebView introduced')
UI.write_text(s,encoding='utf-8');GRADLE.write_text(g,encoding='utf-8')
print('V0909_SYNC_SATHI_LANGUAGE_OK')
