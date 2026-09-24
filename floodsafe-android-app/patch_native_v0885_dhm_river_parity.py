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

# v0.8.85: field-test correction based on the actual current DHM River Watch contract.
# Primary current readings come from DHM's own River Watch JSON response. The 20-minute
# number is no longer presented as an official rule. BIPAD remains metadata/fallback only.
# The map also renders DHM's own River_All.geojson so the overview is river-first.

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

# -----------------------------------------------------------------------------
# A) Native current-source helpers: small DHM JSON POST + bundled station-coordinate map.
# -----------------------------------------------------------------------------
if 'V0885_DHM_RIVERWATCH_PRIMARY_HELPERS' not in a:
    sp=method_span(a,'loadTrustedRiverStationsV862')
    if not sp:raise SystemExit('v0885 loader method missing')
    helpers=r'''    private String v885ReadAssetText(String path)throws Exception{
        try(java.io.InputStream in=getAssets().open(path);java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){
            byte[] buf=new byte[32768];int n;while((n=in.read(buf))>0)out.write(buf,0,n);
            return out.toString("UTF-8");
        }
    }
    private String v885PostDhmRiverWatch()throws Exception{
        java.net.HttpURLConnection c=(java.net.HttpURLConnection)new java.net.URL("https://dhm.gov.np/site/riverWatchTableViewData").openConnection();
        c.setConnectTimeout(18000);c.setReadTimeout(30000);c.setUseCaches(false);c.setDoOutput(true);c.setRequestMethod("POST");
        c.setRequestProperty("User-Agent","Mozilla/5.0 FloodSafeNepal/0.8.85");
        c.setRequestProperty("Accept","application/json,*/*");
        c.setRequestProperty("Content-Type","application/x-www-form-urlencoded; charset=UTF-8");
        c.setRequestProperty("X-Requested-With","XMLHttpRequest");
        c.setRequestProperty("Referer","https://www.dhm.gov.np/hydrology/river-watch");
        c.setRequestProperty("Cache-Control","no-cache");
        byte[] body="type=0&mapValue=all".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        try(java.io.OutputStream os=c.getOutputStream()){os.write(body);}
        int code=c.getResponseCode();java.io.InputStream in=code>=200&&code<300?c.getInputStream():c.getErrorStream();
        if(in==null)throw new java.io.IOException("DHM River Watch HTTP "+code);
        try(java.io.InputStream x=in;java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){
            byte[] buf=new byte[32768];int n;while((n=x.read(buf))>0)out.write(buf,0,n);
            String s=out.toString("UTF-8");if(code<200||code>=300)throw new java.io.IOException("DHM River Watch HTTP "+code);return s;
        }finally{c.disconnect();}
    }
    private static String v885RiverFromStationName(String name){
        if(name==null)return "";String x=name.trim();
        int p=x.toLowerCase(Locale.ROOT).indexOf(" at ");if(p>0)x=x.substring(0,p).trim();
        x=x.replaceAll("(?iu)\\s*\\([^)]*\\)\\s*$","").trim();return x;
    }
    private static String v885MetaKey(String s){return s==null?"":s.trim().toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}.]+","");}
    // V0885_DHM_RIVERWATCH_PRIMARY_HELPERS

'''
    a=a[:sp[0]]+helpers+a[sp[0]:]

# Dedicated current-source count for truthful UI.
if 'V0885_DHM_CURRENT_COUNT' not in a:
    anchor='private volatile int v877FreshObservationCount=0,v877LatestObservationCount=0,v877NoObservationCount=0;'
    p=a.find(anchor)
    if p<0:raise SystemExit('v0885 coverage field anchor missing')
    e=a.find('\n',p)
    a=a[:e+1]+'    private volatile int v885DhmCurrentCount=0; // V0885_DHM_CURRENT_COUNT\n'+a[e+1:]

# Inject DHM River Watch current rows into the proven v0.8.77 union, BEFORE output parsing.
sp=method_span(a,'loadTrustedRiverStationsV862')
if not sp:raise SystemExit('v0885 generated loader missing')
block=a[sp[0]:sp[1]]
if 'V0885_DHM_RIVERWATCH_PRIMARY' not in block:
    anchor='        List<RiverStation> out=new ArrayList<>();'
    if anchor not in block:raise SystemExit('v0885 loader output anchor missing')
    dhm=r'''        // DHM River Watch is the primary CURRENT source. This is the same response used by
        // the official River Watch table; BIPAD remains catalog/fallback metadata.
        int v885Current=0;
        try{
            JSONArray metaArr=new JSONArray(v885ReadAssetText("data/dhm-river-watch-stations-v0885.json"));
            java.util.LinkedHashMap<String,JSONObject> dhmMetaByIndex=new java.util.LinkedHashMap<>(),dhmMetaByName=new java.util.LinkedHashMap<>();
            for(int i=0;i<metaArr.length();i++){JSONObject x=metaArr.optJSONObject(i);if(x==null)continue;
                String ix=x.optString("stationIndex","").trim(),nm=x.optString("name","").trim();
                if(!ix.isEmpty())dhmMetaByIndex.put(v885MetaKey(ix),x);if(!nm.isEmpty())dhmMetaByName.put(v885MetaKey(nm),x);
            }
            JSONObject feed=new JSONObject(v885PostDhmRiverWatch());JSONArray rows=feed.optJSONArray("data");
            if("success".equalsIgnoreCase(feed.optString("status"))&&rows!=null){
                for(int i=0;i<rows.length();i++){
                    JSONObject live=rows.optJSONObject(i);if(live==null)continue;JSONObject wl=live.optJSONObject("waterLevel");
                    if(wl==null||!Double.isFinite(wl.optDouble("value",Double.NaN)))continue;
                    String ix=live.optString("stationIndex","").trim(),nm=live.optString("name","").trim();String when=wl.optString("datetime","").trim();
                    if(nm.isEmpty()||when.isEmpty())continue;
                    JSONObject dm=!ix.isEmpty()?dhmMetaByIndex.get(v885MetaKey(ix)):null;if(dm==null)dm=dhmMetaByName.get(v885MetaKey(nm));
                    JSONObject bm=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;if(bm==null)bm=metaByName.get(v846Key(nm));
                    JSONObject row=v877MergeOfficial(bm,null);
                    if(dm!=null){
                        double la=dm.optDouble("latitude",Double.NaN),lo=dm.optDouble("longitude",Double.NaN);
                        if(Double.isFinite(la)&&Double.isFinite(lo)){row.put("latitude",la);row.put("longitude",lo);row.put("point",new JSONArray().put(lo).put(la));}
                    }
                    if(!ix.isEmpty())row.put("stationIndex",ix);row.put("stationName",nm);
                    row.put("waterLevel",wl.optDouble("value"));row.put("_measurementTime",when);
                    row.put("warningLevel",live.opt("warning_level"));row.put("dangerLevel",live.opt("danger_level"));
                    row.put("status",live.optString("status",""));row.put("_officialStatus",live.optString("status",""));row.put("steady",live.optString("steady",""));
                    row.put("districtName",live.optString("district",dm==null?"":dm.optString("district","")));row.put("basin",live.optString("basin",dm==null?"":dm.optString("basin","")));
                    row.put("_floodsafeRiverName",v885RiverFromStationName(nm));row.put("_floodsafeSource","DHM River Watch");
                    row.put("_floodsafeObservationMatched",true);row.put("_floodsafeOnline",true);row.put("_floodsafeCurrentOfficial",true);
                    String key=v862FinalKey(ix,nm);if(key.isEmpty())continue;newest.put(key,row);metadataMatch.put(key,row);v885Current++;
                    // Ensure DHM stations absent from the BIPAD 284 inventory still reach the map.
                    boolean known=(!ix.isEmpty()&&metaByIndex.containsKey(v846Key(ix)))||metaByName.containsKey(v846Key(nm));
                    if(!known){catalog.put(row);if(!ix.isEmpty())metaByIndex.put(v846Key(ix),row);metaByName.put(v846Key(nm),row);}
                }
            }
        }catch(Exception ignored){}
        v885DhmCurrentCount=v885Current; // V0885_DHM_RIVERWATCH_PRIMARY

'''
    block=block.replace(anchor,dhm+anchor,1)
    a=a[:sp[0]]+block+a[sp[1]:]

# A row present in the CURRENT official DHM response is current official truth. The old
# <=20m gate remains only as a BIPAD fallback safety rule and is no longer claimed as DHM policy.
old='boolean fresh=online&&now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L; // V0877_CLEAN_FRESH_ONLY_LIVE'
new='boolean currentOfficial=r.optBoolean("_floodsafeCurrentOfficial",false);boolean fresh=online&&(currentOfficial||(now-at<=RIVER_FRESH_MS&&at-now<=5L*60L*1000L)); // V0877_CLEAN_FRESH_ONLY_LIVE V0885_DHM_CURRENT_OFFICIAL_TRUTH'
if old in a:a=a.replace(old,new,1)
elif 'V0885_DHM_CURRENT_OFFICIAL_TRUTH' not in a:raise SystemExit('v0885 fresh truth anchor missing')

# Remove the misleading user-facing app cutoff label. The popup continues to show the exact
# official observation timestamp so the user can judge age directly.
a=a.replace('LIVE (≤20m)','DHM current')
if 'LIVE (≤20m)' in a:raise SystemExit('v0885 obsolete 20m UI label remained')

# -----------------------------------------------------------------------------
# B) River-first map: render DHM's official River_All.geojson in addition to detailed taps.
# -----------------------------------------------------------------------------
if 'V0885_DHM_OFFICIAL_RIVER_FIELD' not in m:
    anchor='    private final List<RiverWay> rivers ='
    p=m.find(anchor)
    if p<0:raise SystemExit('v0885 river field anchor missing')
    m=m[:p]+'    private volatile String v885DhmOfficialRivers=null; // V0885_DHM_OFFICIAL_RIVER_FIELD\n'+m[p:]

sp=method_span(m,'loadBundledGeometry')
if not sp:raise SystemExit('v0885 map loadBundledGeometry missing')
mb=m[sp[0]:sp[1]]
if 'V0885_LOAD_DHM_OFFICIAL_RIVERS' not in mb:
    anchor='            main.post(this::installGeoLayers);'
    if anchor not in mb:raise SystemExit('v0885 map load post anchor missing')
    ins='''            try{v885DhmOfficialRivers=readAsset("data/dhm-river-all-v0885.geojson");}catch(Exception ignored){} // V0885_LOAD_DHM_OFFICIAL_RIVERS\n'''
    mb=mb.replace(anchor,ins+anchor,1)
    m=m[:sp[0]]+mb+m[sp[1]:]

sp=method_span(m,'installGeoLayers')
if not sp:raise SystemExit('v0885 installGeoLayers missing')
mb=m[sp[0]:sp[1]]
if 'V0885_DHM_OFFICIAL_RIVER_NETWORK' not in mb:
    anchor='            if (riversGeoJson != null && style.getSource("fs-rivers") == null) {'
    if anchor not in mb:
        anchor='            if(riversGeoJson != null && style.getSource("fs-rivers") == null){'
    if anchor not in mb:raise SystemExit('v0885 fs-rivers install anchor missing')
    official=r'''            if(v885DhmOfficialRivers!=null&&style.getSource("fs-dhm-official-rivers")==null){
                style.addSource(new GeoJsonSource("fs-dhm-official-rivers",v885DhmOfficialRivers));
                style.addLayer(new LineLayer("fs-dhm-official-river-glow","fs-dhm-official-rivers").withProperties(
                        lineColor("#075b85"),lineWidth(5.2f),lineOpacity(0.62f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
                style.addLayer(new LineLayer("fs-dhm-official-river-core","fs-dhm-official-rivers").withProperties(
                        lineColor("#94cfff"),lineWidth(2.15f),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
            } // V0885_DHM_OFFICIAL_RIVER_NETWORK V0885_RIVER_FOCUS
'''
    mb=mb.replace(anchor,official+anchor,1)
    m=m[:sp[0]]+mb+m[sp[1]:]

# Release identity.
g=re.sub(r'versionCode\s+104\b','versionCode 105',g,count=1)
g=g.replace("versionName '0.8.84'","versionName '0.8.85'",1)

for x in ['V0885_DHM_RIVERWATCH_PRIMARY_HELPERS','V0885_DHM_CURRENT_COUNT','V0885_DHM_RIVERWATCH_PRIMARY','V0885_DHM_CURRENT_OFFICIAL_TRUTH']:
    if x not in a:raise SystemExit('v0885 activity contract missing: '+x)
for x in ['V0885_DHM_OFFICIAL_RIVER_FIELD','V0885_LOAD_DHM_OFFICIAL_RIVERS','V0885_DHM_OFFICIAL_RIVER_NETWORK','V0885_RIVER_FOCUS','V0884_STATUS_COLOUR_FLOW_GLOW','V0884_REAL_RIVER_DETAIL_TIME_SOURCE_THRESHOLDS']:
    if x not in m:raise SystemExit('v0885 map contract missing: '+x)
if 'versionCode 105' not in g or "versionName '0.8.85'" not in g:raise SystemExit('v0885 version failed')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.85 PASS: DHM River Watch current JSON primary + exact status/time + official DHM river network; BIPAD fallback retained')
