from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.49 goals
# 1) Exact source parity: BIPAD catalog total + BIPAD latest total are surfaced separately.
# 2) BIPAD latest rows are enriched with catalog metadata before parsing, so current rows
#    that omit coordinates are not accidentally shown as OFFLINE catalog-only stations.
# 3) Availability dots are independent of flood risk: ONLINE/FRESH=green, OFFLINE=black,
#    user's GPS dot=blue. River-line flood colours remain handled by v0.8.48.

# Runtime source counts.
field_anchor='    private String selectedDistrict=""; private Button districtPicker; private final java.util.HashMap<String,String> v848DistrictCache=new java.util.HashMap<>(); // V0848_DISTRICT_FIELDS'
if 'V0849_SOURCE_COUNTS' not in a:
    if field_anchor not in a: raise SystemExit('v0.8.49 district field anchor missing')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile int v849CatalogCount=0,v849LatestCount=0; // V0849_SOURCE_COUNTS',1)

# Capture exact source row counts after both requests complete.
ls=a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{')
le=a.find('    private static String v846StationIndex(',ls)
if ls<0 or le<0: raise SystemExit('v0.8.49 loader anchors missing')
loader=a[ls:le]
count_anchor='        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}'
if 'V0849_CAPTURE_SOURCE_COUNTS' not in loader:
    if count_anchor not in loader: raise SystemExit('v0.8.49 latest count anchor missing')
    loader=loader.replace(count_anchor,count_anchor+'\n        v849CatalogCount=catalog.length();v849LatestCount=latest.length(); // V0849_CAPTURE_SOURCE_COUNTS',1)

# Enrich every current BIPAD/DHM row with catalog metadata before parseStation().
# This fixes stations that are definitely in BIPAD latest but whose latest object does not
# repeat all station coordinates/metadata (e.g. Gaurighat/Kapan class of mismatches).
old_loop='''        List<RiverStation> out=new ArrayList<>(); java.util.HashSet<String> liveKeys=new java.util.HashSet<>();
        for(java.util.Map.Entry<String,JSONObject> e:current.entrySet()){RiverStation s=parseStation(e.getValue(),now);if(s!=null&&s.fresh){out.add(s);liveKeys.add(e.getKey());}} // V0848_ALL_OFFICIAL_STATIONS'''
new_loop='''        List<RiverStation> out=new ArrayList<>(); java.util.HashSet<String> liveKeys=new java.util.HashSet<>();
        for(java.util.Map.Entry<String,JSONObject> e:current.entrySet()){
            JSONObject live=e.getValue();String ix=v846StationIndex(live),nm=v846StationName(live);JSONObject meta=null;
            if(!ix.isEmpty())meta=metaByIndex.get(v846Key(ix));if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));
            JSONObject merged=v849MergeStationMeta(meta,live);RiverStation s=parseStation(merged,now);
            if(s!=null&&s.fresh){out.add(s);liveKeys.add(e.getKey());}
        } // V0849_LATEST_WITH_CATALOG_META'''
if 'V0849_LATEST_WITH_CATALOG_META' not in loader:
    if old_loop not in loader: raise SystemExit('v0.8.49 current loop anchor missing')
    loader=loader.replace(old_loop,new_loop,1)
a=a[:ls]+loader+a[le:]

# Recursive metadata+live merge. Live/current values always win; metadata supplies missing
# coordinates, district and thresholds only.
if 'private static JSONObject v849MergeStationMeta' not in a:
    helper=r'''    private static JSONObject v849MergeStationMeta(JSONObject meta,JSONObject live){
        JSONObject out=meta==null?new JSONObject():cloneJson(meta);if(live==null)return out;
        try{JSONArray names=live.names();if(names!=null)for(int i=0;i<names.length();i++){String k=names.optString(i);Object v=live.opt(k);Object old=out.opt(k);if(v instanceof JSONObject && old instanceof JSONObject)out.put(k,v849MergeStationMeta((JSONObject)old,(JSONObject)v));else out.put(k,v);}}catch(Exception ignored){}
        try{JSONObject mf=meta==null?null:meta.optJSONObject("fields");double la=numDeep(meta,mf,"latitude","lat","stationLatitude","station_latitude"),lo=numDeep(meta,mf,"longitude","lon","lng","stationLongitude","station_longitude");if(Double.isFinite(la))out.put("latitude",la);if(Double.isFinite(lo))out.put("longitude",lo);}catch(Exception ignored){}
        return out;
    } // V0849_META_ENRICH

'''
    anchor='    private static String v846StationIndex('
    if anchor not in a: raise SystemExit('v0.8.49 station index anchor missing')
    a=a.replace(anchor,helper+anchor,1)

# Green = current/fresh station, black = no current reading. Keep flood stage text and
# river-line risk colour separate so availability cannot be confused with danger status.
ss=a.find('    private View stationRow(RiverStation s)')
se=a.find('    private void updateRisk(',ss)
if ss<0 or se<0: raise SystemExit('v0.8.49 stationRow anchors missing')
row=r'''    private static String v849AvailabilityDot(RiverStation s){return s!=null&&s.fresh?"🟢":"⚫";} // V0849_AVAILABILITY_DOT
    private View stationRow(RiverStation s){TextView v=text(v849AvailabilityDot(s)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(s.fresh?Color.rgb(239,252,244):Color.rgb(245,246,247),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
'''
a=a[:ss]+row+a[se:]

# Make source parity visible instead of an ambiguous x/x count.
rs=a.find('    private void refreshRiverUi(){')
re_=a.find('    private static String v849AvailabilityDot',rs)
if rs<0 or re_<0: raise SystemExit('v0.8.49 refresh UI anchors missing')
ui=a[rs:re_]
old='''        stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("अहिले उपलब्ध "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • current नभएको "+u,"Available now "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • no current "+u));'''
new='''        int sourceTotal=v849CatalogCount>0?v849CatalogCount:copy.size(),sourceLatest=v849LatestCount;
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("Official source "+sourceTotal+" • app "+copy.size()+" • 🟢 current "+f+" • ⚫ off/no-current "+u+" • BIPAD latest rows "+sourceLatest,"Official source "+sourceTotal+" • app "+copy.size()+" • 🟢 current "+f+" • ⚫ off/no-current "+u+" • BIPAD latest rows "+sourceLatest)); // V0849_PARITY_UI'''
if 'V0849_PARITY_UI' not in ui:
    if old not in ui: raise SystemExit('v0.8.49 parity UI anchor missing')
    ui=ui.replace(old,new,1)
a=a[:rs]+ui+a[re_:]

# Map station dots: current station = green, offline/no-current = black.
# User/GPS source is already blue and remains blue. River risk overlays are untouched.
replacements={
'ensurePointSource("fs-stale", "fs-stale-layer", "#8e99a5", 4.0f, 0.92f);':'ensurePointSource("fs-stale", "fs-stale-layer", "#111111", 4.5f, 0.98f); // V0849_OFFLINE_BLACK',
'ensurePointSource("fs-normal", "fs-normal-layer", "#2d8cff", 4.4f, 0.98f);':'ensurePointSource("fs-normal", "fs-normal-layer", "#16a34a", 4.7f, 1f); // V0849_ONLINE_GREEN',
'ensurePointSource("fs-alert", "fs-alert-layer", "#ffc928", 5.0f, 1f);':'ensurePointSource("fs-alert", "fs-alert-layer", "#16a34a", 4.7f, 1f);',
'ensurePointSource("fs-warning", "fs-warning-layer", "#ff8a1f", 5.8f, 1f);':'ensurePointSource("fs-warning", "fs-warning-layer", "#16a34a", 4.7f, 1f);',
'ensurePointSource("fs-danger", "fs-danger-layer", "#f22f4b", 6.3f, 1f);':'ensurePointSource("fs-danger", "fs-danger-layer", "#16a34a", 4.7f, 1f);'
}
for oldm,newm in replacements.items():
    if oldm in m:m=m.replace(oldm,newm,1)
if 'V0849_ONLINE_GREEN' not in m or 'V0849_OFFLINE_BLACK' not in m: raise SystemExit('v0.8.49 map availability colour anchors missing')
if 'circleColor("#0b7fd0")' not in m: raise SystemExit('v0.8.49 GPS blue source missing')

# Version.
g=g.replace('versionCode 68','versionCode 69',1).replace("versionName '0.8.48'","versionName '0.8.49'",1)
if 'versionCode 69' not in g or "versionName '0.8.49'" not in g: raise SystemExit('v0.8.49 version bump failed')

for marker in ['V0849_SOURCE_COUNTS','V0849_CAPTURE_SOURCE_COUNTS','V0849_LATEST_WITH_CATALOG_META','V0849_META_ENRICH','V0849_AVAILABILITY_DOT','V0849_PARITY_UI']:
    if marker not in a: raise SystemExit('v0.8.49 activity marker missing: '+marker)
for marker in ['V0849_ONLINE_GREEN','V0849_OFFLINE_BLACK','V0848_FLOOD_COLOUR_PRIORITY']:
    if marker not in m: raise SystemExit('v0.8.49 map marker missing: '+marker)

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.49 source parity + green/black station availability + blue GPS PASS')
