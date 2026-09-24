from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.85: real-device official-source parity + river-map repair.
# Important separation:
# - what the MAP displays mirrors the latest official BIPAD/DHM-connected row and its official status
# - the existing stricter freshness gate remains untouched for automatic emergency alerts/push safety
# This removes the misleading user-facing <=20m rule without weakening alert safety.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0885 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# -----------------------------------------------------------------------------
# A) BIPAD river-stations is not metadata-only: it currently carries waterLevel,
#    waterLevelOn and status. Read those rows as first-class observations, then let
#    river/river-trimed/DHM replace them only when they have a newer source timestamp.
# -----------------------------------------------------------------------------
obs_time=r'''    private long v877ObservationTime(JSONObject r){
        if(r==null)return 0L;JSONObject f=r.optJSONObject("fields");
        String raw=strDeep(r,f,"_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","dataTime","data_time","timestamp","dateTime","datetime","modifiedOn","modified_on","updatedAt","updated_at");
        long at=parseTime(raw);if(at>0L)return at;
        at=trustedRowTime(r);if(at>0L)return at;
        String[] nested={"latest","data","reading","measurement","observation"};
        for(String k:nested){JSONObject o=r.optJSONObject(k);if(o!=null){
            JSONObject of=o.optJSONObject("fields");String x=strDeep(o,of,"_measurementTime","waterLevelOn","water_level_on","measuredOn","measured_on","measurementTime","measurement_time","observationTime","observation_time","observedAt","observed_at","timestamp","dateTime","datetime","modifiedOn","updatedAt");
            at=parseTime(x);if(at>0L)return at;at=trustedRowTime(o);if(at>0L)return at;
        }}
        return 0L;
    } // V0877_CLEAN_NESTED_TIME V0885_WATER_LEVEL_ON_TIME
'''
a=replace_method(a,'v877ObservationTime',obs_time)

sp=method_span(a,'loadTrustedRiverStationsV862')
if not sp:raise SystemExit('v0885 loader missing')
loader=a[sp[0]:sp[1]]
old='''        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();\n        java.util.LinkedHashMap<String,JSONObject> metadataMatch=new java.util.LinkedHashMap<>();'''
new='''        java.util.LinkedHashMap<String,JSONObject> newest=new java.util.LinkedHashMap<>();\n        java.util.LinkedHashMap<String,JSONObject> metadataMatch=new java.util.LinkedHashMap<>();\n        // BIPAD river-stations itself carries the current/latest DHM-connected observation.\n        for(int i=0;i<catalog.length();i++){\n            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;\n            String key=v862FinalKey(v846StationIndex(c),v846StationName(c));if(key.isEmpty())continue;\n            double level=v877ObservationLevel(c);long at=v877ObservationTime(c);\n            if(!Double.isFinite(level)||at<=0L)continue;\n            try{c.put("_floodsafeObservationMatched",true);c.put("_floodsafeOnline",true);c.put("_floodsafeSource","BIPAD river-stations / DHM-connected latest");String rn=v877RiverName(c);if(!rn.isEmpty())c.put("_floodsafeRiverName",rn);}catch(Exception ignored){}\n            newest.put(key,c);metadataMatch.put(key,c);\n        } // V0885_BIPAD_CATALOG_IS_LIVE_OBSERVATION'''
if old not in loader:raise SystemExit('v0885 loader newest anchor missing')
loader=loader.replace(old,new,1)
a=a[:sp[0]]+loader+a[sp[1]:]

# Primary UI mirrors official latest rows and source status. Do not expose an arbitrary
# global 20-minute rule as if it came from DHM/BIPAD.
hint=r'''    private void updateMapHintCounts(){
        if(mapHint==null)return;
        mapHint.setText(t("🌊 आधिकारिक catalog "+v849CatalogCount+" • latest official reading "+v877LatestObservationCount+" • reading नभएको "+v877NoObservationCount,
                          "🌊 official catalog "+v849CatalogCount+" • latest official reading "+v877LatestObservationCount+" • no matched reading "+v877NoObservationCount));
    } // V0885_OFFICIAL_LATEST_HEADER_NO_20M
'''
a=replace_method(a,'updateMapHintCounts',hint)

sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0885 refreshRiverUi missing')
ui=a[sp[0]:sp[1]]
ui=re.sub(r'feedFresh\.setText\(t\([^;]+?\);\s*// V0877_CLEAN_GAUGE_COVERAGE_UI',
          'feedFresh.setText(t("आधिकारिक latest: "+v877LatestObservationCount+" / "+v849CatalogCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+a+" 🔵 "+n+" • reading नभएको "+v877NoObservationCount, "Official latest: "+v877LatestObservationCount+" / "+v849CatalogCount+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+a+" 🔵 "+n+" • no matched reading "+v877NoObservationCount)); // V0885_OFFICIAL_LATEST_COUNTS',
          ui,count=1,flags=re.S)
if 'V0885_OFFICIAL_LATEST_COUNTS' not in ui:raise SystemExit('v0885 feedFresh replacement failed')
a=a[:sp[0]]+ui+a[sp[1]:]

station_line=r'''    private String stationLine(RiverStation s){
        if(s==null)return "";boolean has=Double.isFinite(s.level)&&s.at>0L;
        if(!has)return t("आधिकारिक station • reading उपलब्ध छैन","Official station • no matched/available reading");
        String lev=v872ExactNumber(s.level)+" m",age=v850Age(s.at);double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        return stageName(s.stage)+" • "+lev+" • "+age+dist+" • "+t("आधिकारिक latest","OFFICIAL LATEST");
    } // V0885_STATION_ROW_OFFICIAL_LATEST
'''
a=replace_method(a,'stationLine',station_line)

a=a.replace('यो latest official reading हो; २० मिनेटभन्दा पुरानो भएकाले LIVE alert मा प्रयोग हुँदैन।','यो आधिकारिक source मा देखिएको पछिल्लो reading हो; source time र reading age देखाइएको छ।')
a=a.replace('This is the latest official reading; because it is older than 20 minutes it is not used for LIVE alerts.','This is the latest reading shown by the official source; source time and reading age are shown.')

# -----------------------------------------------------------------------------
# B) Full Nepal river network. Keep the exact viewport river tiles for tapping, but also
#    render the generated nationwide MultiLineString permanently underneath them so the
#    network never disappears at Nepal overview zoom.
# -----------------------------------------------------------------------------
field_anchor='    private String riversGeoJson = null;\n'
if 'V0885_NATIONAL_NETWORK_FIELD' not in m:
    if field_anchor not in m:raise SystemExit('v0885 river field anchor missing')
    m=m.replace(field_anchor,field_anchor+'    private String v885NationalRiverGeoJson = null; // V0885_NATIONAL_NETWORK_FIELD\n',1)

helpers=r'''    private void v885EnsureNationalRiverLayer(){
        if(!styleReady||style==null||v885NationalRiverGeoJson==null||v885NationalRiverGeoJson.trim().isEmpty())return;
        try{
            if(style.getSource("fs-rivers-national")==null)style.addSource(new GeoJsonSource("fs-rivers-national",v885NationalRiverGeoJson));
            if(style.getLayer("fs-rivers-national-glow")==null)style.addLayer(new LineLayer("fs-rivers-national-glow","fs-rivers-national").withProperties(
                    lineColor("#007fba"),lineWidth(5.2f),lineOpacity(0.62f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            if(style.getLayer("fs-rivers-national-core")==null)style.addLayer(new LineLayer("fs-rivers-national-core","fs-rivers-national").withProperties(
                    lineColor("#42d8ff"),lineWidth(2.15f),lineOpacity(0.98f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        }catch(Exception ignored){}
    } // V0885_ALWAYS_VISIBLE_NATIONAL_RIVER_NETWORK

'''
if 'V0885_ALWAYS_VISIBLE_NATIONAL_RIVER_NETWORK' not in m:
    sp=method_span(m,'loadBundledGeometry')
    if not sp:raise SystemExit('v0885 load geometry anchor missing')
    m=m[:sp[0]]+helpers+m[sp[0]:]

load=r'''    private void loadBundledGeometry() {
        io.execute(() -> {
            try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.geojson"); }
            catch (Exception ignored) { try { districtGeoJson = readAsset("floodsafe-nepal/v24/nepal-districts.json"); } catch (Exception ignored2) {} }
            try { v885NationalRiverGeoJson=readAsset("data/nepal-waterways-national-v0841.geojson"); } catch(Exception ignored) { v885NationalRiverGeoJson=null; }
            int gen=++v879RiverLoadGeneration;
            try {
                List<RiverWay> all=v879ReadRiverAsset("data/nepal-waterways-tiles/overview.json");
                main.post(()->{v885EnsureNationalRiverLayer();installGeoLayers();});
                v879ApplyRiverGeometry(all,"overview",gen);
            } catch (Exception ignored) {
                try {
                    List<RiverWay> all=v879ReadRiverAsset("data/nepal-waterways-snapshot.json");
                    main.post(()->{v885EnsureNationalRiverLayer();installGeoLayers();});
                    v879ApplyRiverGeometry(all,"snapshot-fallback",gen);
                } catch (Exception ignored2) { main.post(()->{v885EnsureNationalRiverLayer();installGeoLayers();}); }
            }
        });
    } // V0879_NO_GLOBAL_1400_TRUNCATION V0885_LOAD_NATIONAL_NETWORK
'''
m=replace_method(m,'loadBundledGeometry',load)

sp=method_span(m,'installGeoLayers')
if not sp:raise SystemExit('v0885 installGeoLayers missing')
block=m[sp[0]:sp[1]]
if 'V0885_INSTALL_NATIONAL_NETWORK' not in block:
    p=block.find('{')+1
    block=block[:p]+'\n        v885EnsureNationalRiverLayer(); // V0885_INSTALL_NATIONAL_NETWORK'+block[p:]
    m=m[:sp[0]]+block+m[sp[1]:]

# Latest official observation controls DISPLAY colour, while alert/push freshness is still
# governed by NativeFullActivity's existing safety gate.
station_geo=r'''    private static String stationGeo(List<StationDot> list, String group) {
        try {
            JSONArray f = new JSONArray();
            for (StationDot s : list) {
                boolean observed=s!=null&&Double.isFinite(s.level)&&s.v881At>0L;
                String g = observed ? normalizeStage(s.stage) : "stale";
                if (!group.equals(g)) continue;
                f.put(pointFeature(s.lon,s.lat,s.name));
            }
            return new JSONObject().put("type","FeatureCollection").put("features",f).toString();
        } catch (Exception e) { return emptyFeatureCollection(); }
    } // V0885_STATION_COLOUR_OFFICIAL_LATEST
'''
m=replace_method(m,'stationGeo',station_geo)

risk=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null||!v863UsefulRiverName(r.name))return null;
        String rk=v884CanonicalRiverName(r.name);if(rk.isEmpty())return null;
        StationDot best=null;double bestD=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!Double.isFinite(x.level)||x.v881At<=0L||!group.equals(normalizeStage(x.stage)))continue;
            String sk=v884CanonicalRiverName(x.riverName);
            if(sk.isEmpty()||!rk.equals(sk))continue;
            double d=v872GaugeToRiverKm(x,r);if(Double.isFinite(d)&&d<bestD){bestD=d;best=x;}
        }
        return bestD<=7.5?best:null;
    } // V0872_MATCHED_RIVER_GEOMETRY_ONLY V0885_OFFICIAL_LATEST_RIVER_COLOUR
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk)

colour=r'''    private static String v884MapColour(StationDot s){
        if(s==null||!Double.isFinite(s.level)||s.v881At<=0L)return "GREY / no official reading";
        String st=normalizeStage(s.stage);if("danger".equals(st))return "RED";if("warning".equals(st))return "ORANGE";if("alert".equals(st))return "YELLOW";return "BLUE";
    } // V0885_MAP_COLOUR_FOLLOWS_OFFICIAL_LATEST
'''
m=replace_method(m,'v884MapColour',colour)

sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0885 showRiver missing')
show=m[sp[0]:sp[1]]
show=show.replace('append(gauge.fresh?" • LIVE":" • NOT LIVE / LATEST OFFICIAL")','append(" • OFFICIAL LATEST")')
show=show.replace('if(!gauge.fresh)b.append("\\n\\n").append(englishUi?"This latest official reading is not treated as LIVE and does not colour the river as an active warning.":"यो पछिल्लो आधिकारिक reading LIVE मानिएको छैन र active warning रङमा नदी रंगिँदैन।");','')
if ' • OFFICIAL LATEST' not in show:raise SystemExit('v0885 river status wording anchor missing')
m=m[:sp[0]]+show+m[sp[1]:]

# Release identity.
g=re.sub(r'versionCode\s+104\b','versionCode 105',g,count=1)
g=g.replace("versionName '0.8.84'","versionName '0.8.85'",1)

for x in ['V0885_WATER_LEVEL_ON_TIME','V0885_BIPAD_CATALOG_IS_LIVE_OBSERVATION','V0885_OFFICIAL_LATEST_HEADER_NO_20M','V0885_OFFICIAL_LATEST_COUNTS','V0885_STATION_ROW_OFFICIAL_LATEST']:
    if x not in a:raise SystemExit('v0885 activity contract missing: '+x)
for x in ['V0885_NATIONAL_NETWORK_FIELD','V0885_ALWAYS_VISIBLE_NATIONAL_RIVER_NETWORK','V0885_LOAD_NATIONAL_NETWORK','V0885_INSTALL_NATIONAL_NETWORK','V0885_STATION_COLOUR_OFFICIAL_LATEST','V0885_OFFICIAL_LATEST_RIVER_COLOUR','V0885_MAP_COLOUR_FOLLOWS_OFFICIAL_LATEST']:
    if x not in m:raise SystemExit('v0885 map contract missing: '+x)
if 'LIVE (≤20m)' in a or 'LIVE (<=20m)' in a:raise SystemExit('v0885 user-facing 20m label still present')
if 'versionCode 105' not in g or "versionName '0.8.85'" not in g:raise SystemExit('v0885 version bump failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.85 PASS: BIPAD current river-stations observations + official-latest UI/status colours + always-visible full Nepal river network; emergency freshness gate untouched')
