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

# FloodSafe Nepal v0.8.80 field-test fix, based on the real-device v0.8.79 video:
# 1) river geometry follows the entire visible MapLibre viewport, not only the camera-centre tile;
# 2) tapping a named river can open the latest official SAME-RIVER gauge even when the
#    latest reading is stale (the station detail still labels stale as NOT LIVE);
# 3) unrelated nearby gauges are never borrowed. Matching is exact after a deliberately
#    small canonical alias set (Kosi/Koshi, Nakhu/Nakhhu/Nakkhu, generic river suffixes).
# Safety alert freshness, 2 km emergency radius, source values, station coordinates and
# station inventory are deliberately unchanged.

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
    if not sp:raise SystemExit('v0880 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# -----------------------------------------------------------------------------
# A) Carry the official river/stream name alongside each RiverStation. v0.8.77 already
# keeps this value separately in the trusted source row; this only exposes that existing
# metadata to the native map. No station name/coordinate/reading is changed.
# -----------------------------------------------------------------------------
if 'V0880_RIVER_NAME_FIELD' not in a:
    q=re.search(r'private\s+static\s+final\s+class\s+RiverStation\s*\{',a)
    if not q:raise SystemExit('v0880 RiverStation class missing')
    a=a[:q.end()]+' String riverName=""; /* V0880_RIVER_NAME_FIELD */ '+a[q.end():]

old_return='return new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);'
new_return='RiverStation out=new RiverStation(name,district,la,lo,level,warning,danger,at,fresh,online,stage,rank,raw);out.riverName=v877RiverName(r);return out; // V0880_PRESERVE_OFFICIAL_RIVER_NAME'
if 'V0880_PRESERVE_OFFICIAL_RIVER_NAME' not in a:
    if old_return not in a:raise SystemExit('v0880 clean parseStation return anchor missing')
    a=a.replace(old_return,new_return,1)

# -----------------------------------------------------------------------------
# B) Expose riverName on StationDot using the same reflection path as station name/level.
# -----------------------------------------------------------------------------
if 'V0880_STATION_DOT_RIVER_NAME' not in m:
    q=re.search(r'private\s+static\s+final\s+class\s+StationDot\s*\{',m)
    if not q:raise SystemExit('v0880 StationDot class missing')
    m=m[:q.end()]+' String riverName=""; /* V0880_STATION_DOT_RIVER_NAME */ '+m[q.end():]

if 'V0880_READ_OFFICIAL_RIVER_NAME' not in m:
    sp=method_span(m,'readStation')
    if not sp:raise SystemExit('v0880 readStation missing')
    block=m[sp[0]:sp[1]]
    mm=re.search(r'(s\.name\s*=\s*getString\(c\s*,\s*o\s*,\s*"name"[^;]*;)',block)
    if not mm:raise SystemExit('v0880 station-name reflection anchor missing')
    block=block[:mm.end()]+'\n            s.riverName=getString(c,o,"riverName",""); // V0880_READ_OFFICIAL_RIVER_NAME'+block[mm.end():]
    m=m[:sp[0]]+block+m[sp[1]:]

# -----------------------------------------------------------------------------
# C) Full visible-bounds river loading. Use all tiles intersecting the current viewport
# plus a small margin. This prevents the half/blank river strips seen when the screen
# crossed a centre-tile boundary. Loading/dedup remains asynchronous via v0.8.79.
# -----------------------------------------------------------------------------
viewport=r'''    private void v879RefreshRiverGeometryForCamera(){
        if(map==null)return;CameraPosition cp=map.getCameraPosition();if(cp==null||cp.target==null)return;
        final double zoom=cp.zoom;if(!isNepalish(cp.target.getLatitude(),cp.target.getLongitude()))return;
        if(zoom<7.35){v879QueueRiverAssets("overview",java.util.Collections.singletonList("data/nepal-waterways-tiles/overview.json"));return;}
        double west=cp.target.getLongitude(),east=west,south=cp.target.getLatitude(),north=south;
        try{
            org.maplibre.android.geometry.VisibleRegion vr=map.getProjection().getVisibleRegion();
            org.maplibre.android.geometry.LatLng[] corners=new org.maplibre.android.geometry.LatLng[]{vr.farLeft,vr.farRight,vr.nearLeft,vr.nearRight};
            west=Double.POSITIVE_INFINITY;east=Double.NEGATIVE_INFINITY;south=Double.POSITIVE_INFINITY;north=Double.NEGATIVE_INFINITY;
            for(org.maplibre.android.geometry.LatLng p:corners){if(p==null)continue;west=Math.min(west,p.getLongitude());east=Math.max(east,p.getLongitude());south=Math.min(south,p.getLatitude());north=Math.max(north,p.getLatitude());}
            if(!Double.isFinite(west)||!Double.isFinite(east)||!Double.isFinite(south)||!Double.isFinite(north))throw new IllegalStateException("visible bounds unavailable");
        }catch(Exception ignored){
            west=cp.target.getLongitude()-V879_TILE_STEP_LON*.7;east=cp.target.getLongitude()+V879_TILE_STEP_LON*.7;
            south=cp.target.getLatitude()-V879_TILE_STEP_LAT*.7;north=cp.target.getLatitude()+V879_TILE_STEP_LAT*.7;
        }
        west=Math.max(V879_TILE_MIN_LON,west);east=Math.min(V879_TILE_MIN_LON+V879_TILE_STEP_LON*V879_TILE_NX,east);
        south=Math.max(V879_TILE_MIN_LAT,south);north=Math.min(V879_TILE_MIN_LAT+V879_TILE_STEP_LAT*V879_TILE_NY,north);
        int x0=v879TileX(west),x1=v879TileX(east),y0=v879TileY(south),y1=v879TileY(north);
        int pad=zoom>=9.0?1:0;
        x0=Math.max(0,x0-pad);x1=Math.min(V879_TILE_NX-1,x1+pad);y0=Math.max(0,y0-pad);y1=Math.min(V879_TILE_NY-1,y1+pad);
        List<String> paths=new ArrayList<>();String dir=zoom<10.0?"data/nepal-waterways-tiles-regional/":"data/nepal-waterways-tiles/";
        for(int x=x0;x<=x1;x++)for(int y=y0;y<=y1;y++)paths.add(dir+x+"-"+y+".json");
        java.util.Collections.sort(paths);
        String tier=zoom<10.0?"regional":"exact";
        v879QueueRiverAssets("v880:"+tier+":"+x0+":"+x1+":"+y0+":"+y1,paths);
    } // V0880_VISIBLE_REGION_ALL_TILES V0880_NO_CENTER_ONLY_TILE_GAPS
'''
m=replace_method(m,'v879RefreshRiverGeometryForCamera',viewport)

# -----------------------------------------------------------------------------
# D) Strict same-river mapping. Named river taps require canonical river-name equality.
# No geometry-only fallback is allowed for named rivers. Latest official observations may
# be stale and still be inspectable; the existing station popup clearly marks them NOT LIVE.
# -----------------------------------------------------------------------------
sp=method_span(m,'v866RiverGauge')
if not sp:raise SystemExit('v0880 v866RiverGauge missing')
helpers=r'''    private static String v880CanonicalRiverName(String value){
        if(value==null)return "";
        String x=value.toLowerCase(Locale.ROOT).trim();
        x=x.replace("koshi","kosi").replace("nakhhu","nakhu").replace("nakkhu","nakhu");
        x=x.replace("sunkosi","sun kosi").replace("sunkoshi","sun kosi");
        x=x.replaceAll("[^\\p{L}\\p{N}]+"," ").trim();
        x=x.replaceAll("\\b(river|khola|nadi|stream)\\b"," ").replaceAll("\\s+"," ").trim();
        return x;
    } // V0880_CANONICAL_RIVER_ALIASES

    private StationDot v880SameRiverGauge(RiverWay r,double la,double lo){
        if(r==null||r.points==null||r.points.size()<2||!v863UsefulRiverName(r.name))return null;
        String rk=v880CanonicalRiverName(r.name);if(rk.isEmpty())return null;
        StationDot bestObserved=null,bestAny=null;double observedScore=Double.POSITIVE_INFINITY,anyScore=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null)continue;String sk=v880CanonicalRiverName(s.riverName);if(sk.isEmpty()||!rk.equals(sk))continue; // V0880_EXACT_SAME_RIVER_ONLY
            double routeD=v866PointToRiverKm(r,s.lat,s.lon);if(!Double.isFinite(routeD)||routeD>7.5)continue;
            double tapD=km(la,lo,s.lat,s.lon);if(!Double.isFinite(tapD)||tapD>45.0)continue;
            double score=routeD*9.0+tapD;
            if(score<anyScore){anyScore=score;bestAny=s;}
            if(Double.isFinite(s.level)&&s.at>0L){double obsScore=score-(s.fresh?0.35:0.0);if(obsScore<observedScore){observedScore=obsScore;bestObserved=s;}}
        }}
        return bestObserved!=null?bestObserved:bestAny;
    } // V0880_LATEST_OR_FRESH_SAME_RIVER_GAUGE
'''
m=m[:sp[0]]+helpers+m[sp[0]:]

show=r'''    private void showRiver(RiverWay r,double la,double lo){
        StationDot gauge=v880SameRiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        if(gauge!=null&&stationTapListener!=null){
            stationTapListener.onStationTap(gauge.original);
            return;
        } // V0880_RIVER_TAP_OPENS_SAME_RIVER_SOURCE_DETAIL
        StringBuilder msg=new StringBuilder();
        if(named)msg.append(englishUi?
                "No official gauge in the current catalog can be safely mapped to this named river segment.":
                "यो नाम भएको नदीको यही खण्डसँग सुरक्षित रूपमा मिल्ने आधिकारिक gauge हालको catalog मा भेटिएन।");
        else msg.append(englishUi?
                "This map segment has no usable river name, so FloodSafe will not guess a gauge.":
                "यो नक्सा खण्डमा प्रयोग गर्न मिल्ने नदी नाम छैन, त्यसैले FloodSafe ले gauge अनुमान गरेर जोड्दैन।");
        msg.append("\n\n").append(englishUi?
                "Only an official same-river name match is accepted. Tap a station dot to inspect that exact station.":
                "आधिकारिक same-river नाम मिलेको gauge मात्र स्वीकार हुन्छ। ठ्याक्कै station हेर्न station dot थिच्नुहोस्।");
        msg.append("\n\n").append(englishUi?
                "River geometry: OpenStreetMap / FloodSafe Nepal network":
                "नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString())
                .setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0880_SAFE_SAME_RIVER_DETAIL_WORDING
'''
m=replace_method(m,'showRiver',show)

# Release identity.
g=re.sub(r'versionCode\s+99\b','versionCode 100',g,count=1)
g=g.replace("versionName '0.8.79'","versionName '0.8.80'",1)
if 'versionCode 100' not in g or "versionName '0.8.80'" not in g:raise SystemExit('v0880 version bump failed')

need_a=['V0880_RIVER_NAME_FIELD','V0880_PRESERVE_OFFICIAL_RIVER_NAME','V0877_CLEAN_FULL_INVENTORY_TRUTH','V0877_CLEAN_FRESH_ONLY_LIVE']
for x in need_a:
    if x not in a:raise SystemExit('v0880 activity contract missing: '+x)
need_m=['V0880_STATION_DOT_RIVER_NAME','V0880_READ_OFFICIAL_RIVER_NAME','V0880_VISIBLE_REGION_ALL_TILES','V0880_NO_CENTER_ONLY_TILE_GAPS','V0880_CANONICAL_RIVER_ALIASES','V0880_EXACT_SAME_RIVER_ONLY','V0880_LATEST_OR_FRESH_SAME_RIVER_GAUGE','V0880_RIVER_TAP_OPENS_SAME_RIVER_SOURCE_DETAIL','V0880_SAFE_SAME_RIVER_DETAIL_WORDING','V0879_NO_GLOBAL_1400_TRUNCATION','V0875_TOUCH_PRIORITY']
for x in need_m:
    if x not in m:raise SystemExit('v0880 map contract missing: '+x)
if 'StationDot gauge=v866RiverGauge(r,la,lo);' in m:raise SystemExit('v0880 old fresh-only river tap matcher still active')
if 'if (all.size() > 1400)' in m:raise SystemExit('v0880 old global river truncation regressed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.80 PASS: full visible-region river tiles + strict same-river latest/fresh gauge detail; LIVE/2km safety unchanged')
