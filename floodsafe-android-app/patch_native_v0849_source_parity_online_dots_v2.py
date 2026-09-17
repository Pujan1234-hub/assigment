from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8');m=m_path.read_text(encoding='utf-8');g=g_path.read_text(encoding='utf-8')

# Source counts.
field_anchor='    private String selectedDistrict=""; private Button districtPicker; private final java.util.HashMap<String,String> v848DistrictCache=new java.util.HashMap<>(); // V0848_DISTRICT_FIELDS'
if 'V0849_SOURCE_COUNTS' not in a:
    if field_anchor not in a: raise SystemExit('v0849 district field anchor')
    a=a.replace(field_anchor,field_anchor+'\n    private volatile int v849CatalogCount=0,v849LatestCount=0; // V0849_SOURCE_COUNTS',1)

ls=a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{');le=a.find('    private static String v846StationIndex(',ls)
if ls<0 or le<0: raise SystemExit('v0849 loader anchors')
loader=a[ls:le]
count_anchor='        try{latest=trustedPages(BIPAD+"river-stations/?latest=true&limit=2000",now);}catch(Exception ignored){}'
if 'V0849_CAPTURE_SOURCE_COUNTS' not in loader:
    if count_anchor not in loader: raise SystemExit('v0849 latest anchor')
    loader=loader.replace(count_anchor,count_anchor+'\n        v849CatalogCount=catalog.length();v849LatestCount=latest.length(); // V0849_CAPTURE_SOURCE_COUNTS',1)
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
    if old_loop not in loader: raise SystemExit('v0849 current loop anchor')
    loader=loader.replace(old_loop,new_loop,1)
a=a[:ls]+loader+a[le:]

if 'private static JSONObject v849MergeStationMeta' not in a:
    helper=r'''    private static JSONObject v849MergeStationMeta(JSONObject meta,JSONObject live){
        JSONObject out=meta==null?new JSONObject():cloneJson(meta);if(live==null)return out;
        try{JSONArray names=live.names();if(names!=null)for(int i=0;i<names.length();i++){String k=names.optString(i);Object v=live.opt(k);Object old=out.opt(k);if(v instanceof JSONObject&&old instanceof JSONObject)out.put(k,v849MergeStationMeta((JSONObject)old,(JSONObject)v));else out.put(k,v);}}catch(Exception ignored){}
        if(meta!=null)try{JSONObject mf=meta.optJSONObject("fields");double la=numDeep(meta,mf,"latitude","lat","stationLatitude","station_latitude"),lo=numDeep(meta,mf,"longitude","lon","lng","stationLongitude","station_longitude");if(Double.isFinite(la))out.put("latitude",la);if(Double.isFinite(lo))out.put("longitude",lo);}catch(Exception ignored){}
        return out;
    } // V0849_META_ENRICH

'''
    anchor='    private static String v846StationIndex('
    if anchor not in a: raise SystemExit('v0849 index anchor')
    a=a.replace(anchor,helper+anchor,1)

# List availability dot.
ss=a.find('    private View stationRow(RiverStation s)');se=a.find('    private void updateRisk(',ss)
if ss<0 or se<0: raise SystemExit('v0849 row anchors')
row=r'''    private static String v849AvailabilityDot(RiverStation s){return s!=null&&s.fresh?"🟢":"⚫";} // V0849_AVAILABILITY_DOT
    private View stationRow(RiverStation s){TextView v=text(v849AvailabilityDot(s)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(s.fresh?Color.rgb(239,252,244):Color.rgb(245,246,247),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;}
'''
a=a[:ss]+row+a[se:]

# Explicit source/app parity UI.
rs=a.find('    private void refreshRiverUi(){');re_=a.find('    private static String v849AvailabilityDot',rs)
if rs<0 or re_<0: raise SystemExit('v0849 UI anchors')
ui=a[rs:re_]
old='''        stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("अहिले उपलब्ध "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • current नभएको "+u,"Available now "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • no current "+u));'''
new='''        int sourceTotal=v849CatalogCount>0?v849CatalogCount:copy.size(),sourceLatest=v849LatestCount;
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("Official source "+sourceTotal+" • app "+copy.size()+" • 🟢 current "+f+" • ⚫ off/no-current "+u+" • BIPAD latest rows "+sourceLatest,"Official source "+sourceTotal+" • app "+copy.size()+" • 🟢 current "+f+" • ⚫ off/no-current "+u+" • BIPAD latest rows "+sourceLatest)); // V0849_PARITY_UI'''
if 'V0849_PARITY_UI' not in ui:
    if old not in ui: raise SystemExit('v0849 parity UI anchor')
    ui=ui.replace(old,new,1)
a=a[:rs]+ui+a[re_:]

# Robust map colour override: do not depend on whatever colours prior patches installed.
# Existing layer IDs are stable and refreshStationSources already groups fresh by stage and
# non-current as stale. We recolour every fresh station layer green, stale black. GPS stays blue.
if 'private void v849AvailabilityDotColours()' not in m:
    mh=r'''    private void v849AvailabilityDotColours(){
        if(!styleReady||style==null)return;
        try{CircleLayer x=style.getLayerAs("fs-stale-layer");if(x!=null)x.setProperties(circleColor("#111111"),circleOpacity(1.0f),circleRadius(4.8f));}catch(Exception ignored){}
        String[] ids={"fs-normal-layer","fs-alert-layer","fs-warning-layer","fs-danger-layer"};for(String id:ids)try{CircleLayer x=style.getLayerAs(id);if(x!=null)x.setProperties(circleColor("#16A34A"),circleOpacity(1.0f),circleRadius(4.8f));}catch(Exception ignored){}
    } // V0849_MAP_AVAILABILITY_COLOURS

'''
    anchor='    private void refreshUserSource()'
    if anchor not in m: raise SystemExit('v0849 refreshUserSource anchor')
    m=m.replace(anchor,mh+anchor,1)

# Call after station GeoJSON refresh.
fs=m.find('    private void refreshStationSources() {');fe=m.find('    private void v849AvailabilityDotColours()',fs)
if fs<0 or fe<0: raise SystemExit('v0849 refreshStationSources anchors')
block=m[fs:fe]
if 'v849AvailabilityDotColours(); // V0849_APPLY_DOT_COLOURS' not in block:
    close=block.rfind('    }')
    if close<0: raise SystemExit('v0849 refreshStationSources close')
    block=block[:close]+'        v849AvailabilityDotColours(); // V0849_APPLY_DOT_COLOURS\n'+block[close:]
    m=m[:fs]+block+m[fe:]
if 'circleColor("#0b7fd0")' not in m: raise SystemExit('v0849 GPS blue missing')

# Version.
g=g.replace('versionCode 68','versionCode 69',1).replace("versionName '0.8.48'","versionName '0.8.49'",1)
if 'versionCode 69' not in g or "versionName '0.8.49'" not in g: raise SystemExit('v0849 version bump')
for x in ['V0849_SOURCE_COUNTS','V0849_LATEST_WITH_CATALOG_META','V0849_META_ENRICH','V0849_AVAILABILITY_DOT','V0849_PARITY_UI']:
    if x not in a: raise SystemExit('activity marker '+x)
for x in ['V0849_MAP_AVAILABILITY_COLOURS','V0849_APPLY_DOT_COLOURS','V0848_FLOOD_COLOUR_PRIORITY']:
    if x not in m: raise SystemExit('map marker '+x)

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.49 source parity + green online + black offline + blue GPS PASS')
