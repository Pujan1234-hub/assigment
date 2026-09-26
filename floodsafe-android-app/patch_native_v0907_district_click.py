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
    s2, n = re.subn(pattern, new, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, got {n}")
    s = s2

# UI-only state used to turn numeric BIPAD district ids into real district names
# from the bundled Nepal district polygons. River/map/data-source code is untouched.
replace_once(
    '    private long districtWeatherAt=0L;',
    '    private long districtWeatherAt=0L;\n    private JSONObject v0907DistrictGeometry;\n    private final java.util.Map<String,String> v0907DistrictNameCache=new java.util.HashMap<>();',
    'district display cache field'
)

# Remove the old show-all control. All district names remain visible; a district itself
# is now the control the user taps to open/close only that district's stations.
replace_once(
    'Button more=smallButton(t("सबै जिल्ला देखाउनुहोस्","Show all districts"));more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम जिल्ला देखाउनुहोस्","Show fewer districts"):t("सबै जिल्ला देखाउनुहोस्","Show all districts"));refreshRiverUi();});c.addView(more);return c;',
    'TextView districtHint=text(t("जिल्लाको नाममा थिचेर त्यस जिल्लाका नदी स्टेशन खोल्नुहोस्।","Tap a district name to open its river stations."),11,true,Color.rgb(88,118,140));districtHint.setPadding(0,dp(8),0,0);c.addView(districtHint);return c;',
    'district click hint'
)

accordion = r'''    private void renderDistrictStationGroups(List<RiverStation> source){
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
        for(java.util.Map.Entry<String,List<RiverStation>> e:groups.entrySet())nationalList.addView(districtGroupView(e.getKey(),e.getValue()));
        if(groups.isEmpty())nationalList.addView(empty(t("Official नदी स्टेशन data आउँदैछ…","Official river station data is loading…")));
    } // V0907_DISTRICT_NAMES_COLLAPSED

    private View districtGroupView(String district,List<RiverStation> rows){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(10),dp(8),dp(10),dp(8));
        String strongest="unknown";int best=99;
        for(RiverStation st:rows){if(st.rank<best){best=st.rank;strongest=st.stage;}}
        box.setBackground(round(stageBg(strongest),19,Color.rgb(207,226,237),1));

        LinearLayout body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setVisibility(View.GONE);
        for(RiverStation st:rows)body.addView(stationRow(st));

        TextView head=text("",16,true,Color.rgb(20,46,72));
        head.setPadding(dp(6),dp(8),dp(6),dp(8));
        Runnable updateHead=()->head.setText("📍 "+district+"  •  "+rows.size()+t(" स्टेशन"," stations")+(body.getVisibility()==View.VISIBLE?"   ▾":"   ▸"));
        updateHead.run();
        head.setOnClickListener(v->{boolean open=body.getVisibility()!=View.VISIBLE;body.setVisibility(open?View.VISIBLE:View.GONE);updateHead.run();});
        box.addView(head);box.addView(body);
        LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(10));box.setLayoutParams(p);return box;
    } // V0907_DISTRICT_CLICK_REVEALS_STATIONS

    private String districtLabel(RiverStation st){
        if(st==null)return t("जिल्ला नखुलेको","District unavailable");
        String raw=st.district==null?"":st.district.trim();
        if(!raw.isEmpty()&&!"null".equalsIgnoreCase(raw)&&!raw.matches("\\d+"))return raw;
        String cacheKey=(st.stationId==null?"":st.stationId)+"@"+String.format(Locale.US,"%.5f,%.5f",st.lat,st.lon);
        String cached=v0907DistrictNameCache.get(cacheKey);if(cached!=null)return cached;
        String resolved=v0907DistrictNameAt(st.lat,st.lon);
        if(resolved.isEmpty())resolved=t("जिल्ला नखुलेको","District unavailable");
        v0907DistrictNameCache.put(cacheKey,resolved);return resolved;
    }

    private String v0907DistrictNameAt(double lat,double lon){
        if(!Double.isFinite(lat)||!Double.isFinite(lon))return "";
        try{
            if(v0907DistrictGeometry==null){
                try{v0907DistrictGeometry=assetJson("floodsafe-nepal/v24/nepal-districts.geojson");}
                catch(Exception e){v0907DistrictGeometry=assetJson("floodsafe-nepal/v24/nepal-districts.json");}
            }
            JSONArray features=v0907DistrictGeometry.optJSONArray("features");if(features==null)return "";
            for(int i=0;i<features.length();i++){
                JSONObject f=features.optJSONObject(i);if(f==null)continue;
                JSONObject geo=f.optJSONObject("geometry");if(!v0907GeometryContains(geo,lon,lat))continue;
                JSONObject p=f.optJSONObject("properties");if(p==null)return "";
                String name=p.optString("nameEn","").trim();if(!name.isEmpty())return name;
            }
        }catch(Exception ignored){}
        return "";
    }

    private static boolean v0907GeometryContains(JSONObject geo,double lon,double lat){
        if(geo==null)return false;String type=geo.optString("type","");JSONArray c=geo.optJSONArray("coordinates");if(c==null)return false;
        if("Polygon".equals(type))return v0907PolygonContains(c,lon,lat);
        if("MultiPolygon".equals(type)){for(int i=0;i<c.length();i++){JSONArray poly=c.optJSONArray(i);if(v0907PolygonContains(poly,lon,lat))return true;}}
        return false;
    }

    private static boolean v0907PolygonContains(JSONArray rings,double lon,double lat){
        if(rings==null||rings.length()==0)return false;JSONArray outer=rings.optJSONArray(0);if(!v0907RingContains(outer,lon,lat))return false;
        for(int i=1;i<rings.length();i++)if(v0907RingContains(rings.optJSONArray(i),lon,lat))return false;
        return true;
    }

    private static boolean v0907RingContains(JSONArray ring,double lon,double lat){
        if(ring==null||ring.length()<3)return false;boolean inside=false;int j=ring.length()-1;
        for(int i=0;i<ring.length();j=i++){
            JSONArray pi=ring.optJSONArray(i),pj=ring.optJSONArray(j);if(pi==null||pj==null)continue;
            double xi=pi.optDouble(0,Double.NaN),yi=pi.optDouble(1,Double.NaN),xj=pj.optDouble(0,Double.NaN),yj=pj.optDouble(1,Double.NaN);
            if(!Double.isFinite(xi)||!Double.isFinite(yi)||!Double.isFinite(xj)||!Double.isFinite(yj))continue;
            boolean cross=((yi>lat)!=(yj>lat))&&(lon<(xj-xi)*(lat-yi)/(yj-yi)+xi);if(cross)inside=!inside;
        }
        return inside;
    }

    private String stationDisplayName(RiverStation st){
        if(st==null)return "";
        String rn=st.riverName==null?"":st.riverName.trim(),sn=st.name==null?"":st.name.trim();
        if(rn.isEmpty())return sn;if(sn.isEmpty())return rn;
        String a=rn.toLowerCase(Locale.ROOT),b=sn.toLowerCase(Locale.ROOT);return b.contains(a)?sn:rn+" — "+sn;
    }
'''

sub_once(
    r'    private void renderDistrictStationGroups\(List<RiverStation> source\)\{.*?    private String stationDisplayName\(RiverStation s\)\{.*?\n    \}\n',
    accordion,
    'district accordion methods'
)

if "versionCode 23" not in g or "versionName '0.9.06-district-196-rain'" not in g:
    raise SystemExit("v0.9.06 version markers missing")
g=g.replace("versionCode 23","versionCode 24",1)
g=g.replace("versionName '0.9.06-district-196-rain'","versionName '0.9.07-district-click'",1)

assert "V0907_DISTRICT_NAMES_COLLAPSED" in s
assert "V0907_DISTRICT_CLICK_REVEALS_STATIONS" in s
assert "FloodSafeNativeMapView" in s
assert "android.webkit.WebView" not in s
UI.write_text(s,encoding="utf-8")
GRADLE.write_text(g,encoding="utf-8")
print("V0907_DISTRICT_CLICK_UI_PATCH_OK")
