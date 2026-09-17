from pathlib import Path
import re
root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=p.read_text(encoding='utf-8')

def between(s,a,b,r):
 i=s.find(a); j=s.find(b,i)
 if i<0 or j<0: raise SystemExit('anchor missing '+a)
 return s[:i]+r+s[j:]

# fields + district card placement
fa='    private boolean showAllStations=false;'
if 'V0848_DISTRICT_FIELDS' not in a:
 a=a.replace(fa,fa+'\n    private String selectedDistrict=""; private Button districtPicker; private final java.util.HashMap<String,String> v848DistrictCache=new java.util.HashMap<>(); // V0848_DISTRICT_FIELDS',1)
a=a.replace('content.addView(nationalCard());','content.addView(districtCard());',1)
if 'private View districtCard()' not in a:
 ui=r'''    private View districtCard(){LinearLayout c=card();nationalTitle=text(t("🏞️ जिल्ला अनुसार नदी अवस्था","🏞️ River status by district"),20,true,Color.rgb(16,39,70));nationalSub=text(t("जिल्ला छानेर official नदी स्टेशन हेर्नुहोस्।","Choose a district to see official river stations."),12,true,Color.rgb(100,130,151));nationalFresh=text("",12,true,Color.rgb(100,130,151));c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);districtPicker=smallButton(t("जिल्ला छान्नुहोस् ▾","Choose district ▾"));districtPicker.setOnClickListener(v->showDistrictPicker());c.addView(districtPicker,lp(-1,dp(50),0,dp(10),0,dp(8)));nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);c.addView(nationalList);return c;}
    private void showDistrictPicker(){java.util.TreeSet<String> n=new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);synchronized(stations){for(RiverStation s:stations)if(s.district!=null&&!s.district.isEmpty()&&!s.district.matches("\\d+"))n.add(s.district);}if(n.isEmpty()){new AlertDialog.Builder(this).setMessage(t("जिल्ला data refresh हुँदैछ।","District data is refreshing.")).setPositiveButton("OK",null).show();return;}String[] x=n.toArray(new String[0]);new AlertDialog.Builder(this).setTitle(t("जिल्ला छान्नुहोस्","Choose district")).setItems(x,(d,w)->{selectedDistrict=x[w];districtPicker.setText(selectedDistrict+" ▾");refreshRiverUi();}).setNegativeButton(t("बन्द","Close"),null).show();}

'''
 a=a.replace('    private LinearLayout humanCard()',ui+'    private LinearLayout humanCard()',1)

# Complete official inventory: current BIPAD/DHM rows stay live; catalog-only rows stay grey/no-current.
ls=a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{'); le=a.find('    private JSONArray trustedPages(',ls)
if ls<0 or le<0: raise SystemExit('loader anchors')
block=a[ls:le]
needle='''        List<RiverStation> out=new ArrayList<>();\n        for(JSONObject r:current.values()){\n            RiverStation s=parseStation(r,now);\n            if(s!=null&&s.fresh)out.add(s); // V0846_BIPAD_DHM_CURRENT_UNION\n        }'''
rep='''        List<RiverStation> out=new ArrayList<>(); java.util.HashSet<String> liveKeys=new java.util.HashSet<>();\n        for(java.util.Map.Entry<String,JSONObject> e:current.entrySet()){RiverStation s=parseStation(e.getValue(),now);if(s!=null&&s.fresh){out.add(s);liveKeys.add(e.getKey());}} // V0848_ALL_OFFICIAL_STATIONS'''
if needle in block:block=block.replace(needle,rep,1)
elif 'V0848_ALL_OFFICIAL_STATIONS' not in block: raise SystemExit('current union anchor')
# Insert catalog rows immediately before return out.
cat='''        for(int i=0;i<catalog.length();i++){JSONObject c=catalog.optJSONObject(i);if(c==null)continue;String ix=v846StationIndex(c),nm=v846StationName(c);String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);if(liveKeys.contains(key))continue;try{c.put("_floodsafeCatalogOnly",true);}catch(Exception ignored){}RiverStation s=parseStation(c,now);if(s!=null)out.add(s);}\n        out=v848DedupStations(out);\n'''
pos=block.rfind('        return out;')
if pos<0: raise SystemExit('loader return')
if '_floodsafeCatalogOnly' not in block:block=block[:pos]+cat+block[pos:]
a=a[:ls]+block+a[le:]
if 'v848DedupStations' not in a[a.find('    private JSONArray trustedPages(')-800:a.find('    private JSONArray trustedPages(')+100]:
 h='''    private static String v848Key(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","");}\n    private static List<RiverStation> v848DedupStations(List<RiverStation> in){java.util.LinkedHashMap<String,RiverStation> m=new java.util.LinkedHashMap<>();for(RiverStation s:in){String k=v848Key(s.name)+String.format(Locale.US,"|%.3f|%.3f",s.lat,s.lon);RiverStation o=m.get(k);if(o==null||(s.fresh&&!o.fresh))m.put(k,s);}return new ArrayList<>(m.values());}\n\n'''
 a=a.replace('    private JSONArray trustedPages(',h+'    private JSONArray trustedPages(',1)

# Resolve numeric district IDs from the bundled 77-district geometry.
if 'private String v848DistrictName' not in a:
 h=r'''    private String v848DistrictName(double la,double lo,String raw){String z=raw==null?"":raw.trim();if(!z.isEmpty()&&!z.matches("\\d+"))return z;String k=String.format(Locale.US,"%.4f,%.4f",la,lo);synchronized(v848DistrictCache){if(v848DistrictCache.containsKey(k))return v848DistrictCache.get(k);}String out="";try{JSONObject r=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");JSONArray fs=r.optJSONArray("features");if(fs!=null)for(int i=0;i<fs.length();i++){JSONObject f=fs.optJSONObject(i),g=f==null?null:f.optJSONObject("geometry");if(g!=null&&v848Inside(lo,la,g)){JSONObject pr=f.optJSONObject("properties");out=pr==null?"":pr.optString("nameEn","");if(!out.isEmpty())break;}}}catch(Exception ignored){}synchronized(v848DistrictCache){v848DistrictCache.put(k,out);}return out;}
    private static boolean v848Inside(double x,double y,JSONObject g){try{JSONArray c=g.optJSONArray("coordinates");if(c==null)return false;if("Polygon".equals(g.optString("type")))return v848Poly(x,y,c);if("MultiPolygon".equals(g.optString("type")))for(int i=0;i<c.length();i++)if(v848Poly(x,y,c.optJSONArray(i)))return true;}catch(Exception ignored){}return false;}
    private static boolean v848Poly(double x,double y,JSONArray p){if(p==null||p.length()==0)return false;JSONArray r=p.optJSONArray(0);if(r==null)return false;boolean in=false;for(int i=0,j=r.length()-1;i<r.length();j=i++){JSONArray a=r.optJSONArray(i),b=r.optJSONArray(j);if(a==null||b==null)continue;double xi=a.optDouble(0),yi=a.optDouble(1),xj=b.optDouble(0),yj=b.optDouble(1);if(((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/((yj-yi)==0?1e-12:(yj-yi))+xi))in=!in;}return in;}

'''
 a=a.replace('    private void refreshRainStations()',h+'    private void refreshRainStations()',1)
# district parser
ps=a.find('    private RiverStation parseStation('); pe=a.find('    private void refreshRainStations()',ps); b=a[ps:pe]
b,n=re.subn(r'String district=str\(r,"districtName","district_name","district"\);return new RiverStation','String district=v848DistrictName(a,o,str(r,"districtName","district_name","district"));return new RiverStation',b,count=1)
if n!=1 and 'v848DistrictName(a,o' not in b: raise SystemExit('district parse')
a=a[:ps]+b+a[pe:]

# district-scoped list instead of nationwide dump
ui=r'''    private void refreshRiverUi(){if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}copy.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));map.setStations(copy,lat,lon);int d=0,w=0,al=0,n=0,u=0,f=0;for(RiverStation s:copy){if(s.fresh)f++;switch(s.stage){case"danger":d++;break;case"warning":w++;break;case"alert":al++;break;case"normal":n++;break;default:u++;}}stationCount.setText(String.valueOf(copy.size()));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));feedFresh.setText(t("अहिले उपलब्ध "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • current नभएको "+u,"Available now "+f+" / "+copy.size()+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n+" • no current "+u));updateRisk(copy);nearList.removeAllViews();List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));if(nationalList!=null){nationalList.removeAllViews();if(selectedDistrict.isEmpty()){nationalFresh.setText(t("नेपालभरको ठूलो list हटाइएको छ — जिल्ला छान्नुहोस्।","Nationwide list removed — choose a district."));nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));}else{int total=0,cur=0;for(RiverStation s:copy)if(selectedDistrict.equalsIgnoreCase(s.district)){total++;if(s.fresh)cur++;nationalList.addView(stationRow(s));}nationalFresh.setText(selectedDistrict+": "+cur+" / "+total+" current");if(total==0)nationalList.addView(empty(t("Official river station भेटिएन।","No official river station found.")));}}}

'''
a=between(a,'    private void refreshRiverUi(){','    private View stationRow(',ui,'ui')
# no millions-of-minutes for catalog-only rows
s=a.find('    private String stationLine(RiverStation s)');e=a.find('    private void showStation(',s)
if s>=0 and e>s:a=a[:s]+'''    private String stationLine(RiverStation s){if(!s.fresh)return t("अहिले current reading छैन","NO CURRENT READING");String age=s.at>0?Math.max(0,(System.currentTimeMillis()-s.at)/60000)+" min ago":"time unknown";String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";double d=distanceKm(s.lat,s.lon);return stageName(s.stage)+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • %.1f km",d):"");}\n\n'''+a[e:]

for x in ['V0848_ALL_OFFICIAL_STATIONS','districtCard()','v848DistrictName','V0848_DISTRICT_FIELDS']:
 if x not in a: raise SystemExit('missing '+x)
p.write_text(a,encoding='utf-8')
print('v0.8.48 station inventory + district mode PASS')
