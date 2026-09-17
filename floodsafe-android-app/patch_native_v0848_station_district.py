from pathlib import Path
import re

root = Path(__file__).resolve().parent
p = root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a = p.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.8.48 station inventory + real district selector
# - keep every official station from the BIPAD station catalog on screen
# - current BIPAD/DHM observations win; catalog-only stations are grey/no-current
# - resolve numeric district ids to real 77-district names from bundled GeoJSON
# - replace the huge Nepal-wide station dump with a district picker
# -----------------------------------------------------------------------------

# UI fields.
field_anchor = '    private boolean showAllStations=false;'
if 'V0848_DISTRICT_FIELDS' not in a:
    if field_anchor not in a:
        raise SystemExit('v0.8.48 showAllStations field anchor missing')
    a = a.replace(field_anchor, field_anchor + '\n    private String selectedDistrict=""; private Button districtPicker; private final java.util.HashMap<String,String> v848DistrictCache=new java.util.HashMap<>(); // V0848_DISTRICT_FIELDS', 1)

# Swap the old nationwide card for a district card. Keep old nationalCard method harmlessly unused.
a = a.replace('content.addView(nationalCard());', 'content.addView(districtCard());', 1)

if 'private View districtCard()' not in a:
    district_ui = r'''    private View districtCard(){
        LinearLayout c=card();
        nationalTitle=text(t("🏞️ जिल्ला अनुसार नदी अवस्था","🏞️ River status by district"),20,true,Color.rgb(16,39,70));
        nationalSub=text(t("जिल्ला छानेर official नदी स्टेशन हेर्नुहोस्।","Choose a district to see official river stations."),12,true,Color.rgb(100,130,151));
        nationalFresh=text("",12,true,Color.rgb(100,130,151));
        c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);
        districtPicker=smallButton(t("जिल्ला छान्नुहोस् ▾","Choose district ▾"));
        districtPicker.setOnClickListener(v->showDistrictPicker());
        c.addView(districtPicker,lp(-1,dp(50),0,dp(10),0,dp(8)));
        nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);c.addView(nationalList);
        return c;
    }

    private void showDistrictPicker(){
        java.util.TreeSet<String> names=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        synchronized(stations){for(RiverStation s:stations){if(s.district!=null&&!s.district.trim().isEmpty()&&!s.district.trim().matches("\\d+"))names.add(s.district.trim());}}
        if(names.isEmpty()){new AlertDialog.Builder(this).setMessage(t("जिल्ला data refresh हुँदैछ।","District data is refreshing.")).setPositiveButton("OK",null).show();return;}
        String[] x=names.toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle(t("जिल्ला छान्नुहोस्","Choose district")).setItems(x,(d,w)->{selectedDistrict=x[w];districtPicker.setText(selectedDistrict+" ▾");refreshRiverUi();}).setNegativeButton(t("बन्द","Close"),null).show();
    }

'''
    anchor = '    private LinearLayout humanCard()'
    if anchor not in a:
        raise SystemExit('v0.8.48 humanCard anchor missing')
    a = a.replace(anchor, district_ui + anchor, 1)

# -----------------------------------------------------------------------------
# Official inventory: current rows + catalog metadata rows.
# Current rows are always preferred. Catalog never creates a fake live reading.
# -----------------------------------------------------------------------------
ls = a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{')
le = a.find('    private JSONArray trustedPages(', ls)
if ls < 0 or le < 0:
    raise SystemExit('v0.8.48 official loader anchors missing')
loader = a[ls:le]

old_current = '''        List<RiverStation> out=new ArrayList<>();\n        for(JSONObject r:current.values()){\n            RiverStation s=parseStation(r,now);\n            if(s!=null&&s.fresh)out.add(s); // V0846_BIPAD_DHM_CURRENT_UNION\n        }'''
new_current = '''        List<RiverStation> out=new ArrayList<>(); java.util.HashSet<String> liveKeys=new java.util.HashSet<>();\n        for(java.util.Map.Entry<String,JSONObject> e:current.entrySet()){RiverStation s=parseStation(e.getValue(),now);if(s!=null&&s.fresh){out.add(s);liveKeys.add(e.getKey());}} // V0848_ALL_OFFICIAL_STATIONS'''
if old_current in loader:
    loader = loader.replace(old_current, new_current, 1)
elif 'V0848_ALL_OFFICIAL_STATIONS' not in loader:
    raise SystemExit('v0.8.48 current-source union anchor missing')

# Add catalog-only stations after direct/proxy current-source handling, just before return.
if '_floodsafeCatalogOnly' not in loader:
    insert = r'''        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);
            if(liveKeys.contains(key))continue;
            try{c.put("_floodsafeCatalogOnly",true);}catch(Exception ignored){}
            RiverStation s=parseStation(c,now);if(s!=null)out.add(s);
        }
        out=v848DedupStations(out);
'''
    pos = loader.rfind('        return out;')
    if pos < 0:
        raise SystemExit('v0.8.48 loader return anchor missing')
    loader = loader[:pos] + insert + loader[pos:]
a = a[:ls] + loader + a[le:]

if 'private static List<RiverStation> v848DedupStations' not in a:
    helpers = r'''    private static String v848Key(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","");}
    private static List<RiverStation> v848DedupStations(List<RiverStation> in){
        java.util.LinkedHashMap<String,RiverStation> m=new java.util.LinkedHashMap<>();
        for(RiverStation s:in){String k=v848Key(s.name)+String.format(Locale.US,"|%.3f|%.3f",s.lat,s.lon);RiverStation old=m.get(k);if(old==null||(s.fresh&&!old.fresh))m.put(k,s);}
        return new ArrayList<>(m.values());
    }

'''
    anchor = '    private JSONArray trustedPages('
    if anchor not in a:
        raise SystemExit('v0.8.48 trustedPages anchor missing')
    a = a.replace(anchor, helpers + anchor, 1)

# -----------------------------------------------------------------------------
# District names: if source sends a numeric district id, derive name from exact bundled
# 77-district polygon. Cache coordinate -> district so the 10 s source poll stays cheap.
# -----------------------------------------------------------------------------
if 'private String v848DistrictName' not in a:
    district_helpers = r'''    private String v848DistrictName(double la,double lo,String raw){
        String z=raw==null?"":raw.trim();if(!z.isEmpty()&&!z.matches("\\d+"))return z;
        String key=String.format(Locale.US,"%.4f,%.4f",la,lo);
        synchronized(v848DistrictCache){if(v848DistrictCache.containsKey(key))return v848DistrictCache.get(key);}
        String out="";
        try{JSONObject root=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=root.optJSONArray("features");if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i),g=f==null?null:f.optJSONObject("geometry");if(g!=null&&v848Inside(lo,la,g)){JSONObject pr=f.optJSONObject("properties");out=pr==null?"":pr.optString("nameEn","");if(!out.isEmpty())break;}}}catch(Exception ignored){}
        synchronized(v848DistrictCache){v848DistrictCache.put(key,out);}return out;
    }
    private static boolean v848Inside(double x,double y,JSONObject g){try{JSONArray c=g.optJSONArray("coordinates");if(c==null)return false;if("Polygon".equals(g.optString("type")))return v848Poly(x,y,c);if("MultiPolygon".equals(g.optString("type")))for(int i=0;i<c.length();i++)if(v848Poly(x,y,c.optJSONArray(i)))return true;}catch(Exception ignored){}return false;}
    private static boolean v848Poly(double x,double y,JSONArray p){if(p==null||p.length()==0)return false;JSONArray r=p.optJSONArray(0);if(r==null)return false;boolean inside=false;for(int i=0,j=r.length()-1;i<r.length();j=i++){JSONArray aa=r.optJSONArray(i),bb=r.optJSONArray(j);if(aa==null||bb==null)continue;double xi=aa.optDouble(0),yi=aa.optDouble(1),xj=bb.optDouble(0),yj=bb.optDouble(1);if(((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/((yj-yi)==0?1e-12:(yj-yi))+xi))inside=!inside;}return inside;}

'''
    anchor = '    private void refreshRainStations()'
    if anchor not in a:
        raise SystemExit('v0.8.48 refreshRainStations anchor missing')
    a = a.replace(anchor, district_helpers + anchor, 1)

# Robust district parser patch: prior versions may use str(...) or strDeep(...).
ps = a.find('    private RiverStation parseStation(')
pe = a.find('    private void refreshRainStations()', ps)
if ps < 0 or pe < 0:
    raise SystemExit('v0.8.48 parseStation anchors missing')
parse_block = a[ps:pe]
if 'v848DistrictName(a,o,' not in parse_block:
    parse_block, n = re.subn(r'String\s+district\s*=\s*([^;]+);(?=\s*return\s+new\s+RiverStation)', r'String district=v848DistrictName(a,o,\1);', parse_block, count=1)
    if n != 1:
        raise SystemExit('v0.8.48 district parse assignment missing')
a = a[:ps] + parse_block + a[pe:]

# -----------------------------------------------------------------------------
# District-scoped display. Nearby card stays useful; nationwide dump is removed.
# -----------------------------------------------------------------------------
rs = a.find('    private void refreshRiverUi(){')
re_ = a.find('    private View stationRow(', rs)
if rs < 0 or re_ < 0:
    raise SystemExit('v0.8.48 refreshRiverUi anchors missing')
refresh_ui = r'''    private void refreshRiverUi(){
        if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        copy.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(copy,lat,lon);
        int d=0,w=0,al=0,n=0,u=0,f=0;for(RiverStation s:copy){if(s.fresh)f++;switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":al++;break;case"normal":n++;break;default:u++;}}
        stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("अहिले उपलब्ध "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • current नभएको "+u,"Available now "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • no current "+u));
        updateRisk(copy);
        nearList.removeAllViews();List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));if(near.isEmpty())nearList.addView(empty(t("Official station भेटिएन।","No official station found.")));
        if(nationalList!=null){nationalList.removeAllViews();if(selectedDistrict.isEmpty()){nationalFresh.setText(t("नेपालभरको ठूलो list हटाइएको छ — जिल्ला छान्नुहोस्।","Nationwide list removed — choose a district."));nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));}else{int total=0,current=0;for(RiverStation s:copy)if(selectedDistrict.equalsIgnoreCase(s.district)){total++;if(s.fresh)current++;nationalList.addView(stationRow(s));}nationalFresh.setText(selectedDistrict+": "+current+" / "+total+" current");if(total==0)nationalList.addView(empty(t("Official river station भेटिएन।","No official river station found.")));}}
    }

'''
a = a[:rs] + refresh_ui + a[re_:]

# Never print absurd million-minute ages for metadata-only stations.
ss = a.find('    private String stationLine(RiverStation s)')
se = a.find('    private void showStation(', ss)
if ss < 0 or se < 0:
    raise SystemExit('v0.8.48 stationLine anchors missing')
station_line = r'''    private String stationLine(RiverStation s){if(!s.fresh)return t("अहिले current reading छैन","NO CURRENT READING");String age=s.at>0?Math.max(0,(System.currentTimeMillis()-s.at)/60000)+" min ago":"time unknown";String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";double d=distanceKm(s.lat,s.lon);return stageName(s.stage)+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • %.1f km",d):"");}

'''
a = a[:ss] + station_line + a[se:]

for marker in ['V0848_ALL_OFFICIAL_STATIONS','private View districtCard()','v848DistrictName','V0848_DISTRICT_FIELDS','_floodsafeCatalogOnly']:
    if marker not in a:
        raise SystemExit('v0.8.48 marker missing: '+marker)

p.write_text(a,encoding='utf-8')
print('FloodSafe v0.8.48 complete station inventory + real district selector PASS')
